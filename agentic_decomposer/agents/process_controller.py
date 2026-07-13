"""Process Controller.

Orchestrates the full pipeline for one run:

    Evidence → Domain → Generator → Evaluator(+QualityGate)
      → Refiner (≤N rounds) → Evaluator (re-score)
      → select best → final_output.json + decomposition.json

No agentic reasoning lives here — only sequencing, artifact handoff,
quality-gate-aware candidate selection, and final reporting.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agentic_decomposer import __version__
from agentic_decomposer.agents.decomposition_evaluator import DecompositionEvaluatorAgent
from agentic_decomposer.agents.decomposition_generator import DecompositionGeneratorAgent
from agentic_decomposer.agents.decomposition_refiner import DecompositionRefinerAgent
from agentic_decomposer.agents.domain_extractor import DomainExtractorAgent
from agentic_decomposer.agents.evidence_constructor import EvidenceConstructorAgent
from agentic_decomposer.agents.quality_gate import QualityGateAgent
from agentic_decomposer.artifacts.validators import validate
from agentic_decomposer.config import RunConfig
from agentic_decomposer.logger import attach_file_handler, detach_file_handler, get_logger
from agentic_decomposer.runs import RunLayout, make_layout, read_json, write_json


class ProcessController:
    """Top-level orchestrator. Construct with a frozen RunConfig, call ``run()``."""

    def __init__(self, config: RunConfig, runs_dir: Path | None = None) -> None:
        self.config = config
        self.layout: RunLayout = make_layout(config.run_id, runs_dir=runs_dir)
        self.logger = get_logger("agentic.controller")

    # ------------------------------------------------------------------
    def run(self) -> dict:
        """Execute the full pipeline. Returns the parsed ``final_output``."""
        self.layout.create()
        handler = attach_file_handler(self.logger, self.layout.controller_log_path)
        wall_start = time.perf_counter()
        total_tokens = 0
        stopping_reason = "no_refinement_requested"

        try:
            self.logger.info("controller.start run_id=%s system=%s model=%s evidence_mode=%s",
                             self.config.run_id, self.config.system,
                             self.config.model, self.config.evidence_mode)

            self._write_config()

            # ── Evidence ─────────────────────────────────────────────────
            evidence_result = EvidenceConstructorAgent(self.config, self.layout).run()
            total_tokens += evidence_result.tokens_used
            evidence_pack = evidence_result.output  # type: ignore[assignment]

            # ── Domain (skippable) ───────────────────────────────────────
            domain_result = DomainExtractorAgent(self.config, self.layout).run(
                evidence_pack=evidence_pack,
            )
            total_tokens += domain_result.tokens_used
            domain_model = domain_result.output  # type: ignore[assignment]

            # ── Generate candidates ──────────────────────────────────────
            gen_result = DecompositionGeneratorAgent(self.config, self.layout).run(
                evidence_pack=evidence_pack,
                domain_model=domain_model,
            )
            total_tokens += gen_result.tokens_used
            candidates_doc = gen_result.output  # type: ignore[assignment]

            # ── Evaluate all candidates ──────────────────────────────────
            eval_result = DecompositionEvaluatorAgent(self.config, self.layout).run(
                candidates=candidates_doc,
                evidence_pack=evidence_pack,
                domain_model=domain_model,
            )
            total_tokens += eval_result.tokens_used
            evaluation = eval_result.output  # type: ignore[assignment]

            # ── Quality gate on the controller-selected best candidate ──
            best_id = evaluation.get("best_candidate_id") or ""
            best_candidate = self._find_candidate(candidates_doc, best_id)
            QualityGateAgent(self.config, self.layout).run(
                candidate=best_candidate, evidence_pack=evidence_pack, domain_model=domain_model,
            )

            # ── Refiner loop (single round in MVP) ───────────────────────
            initial_best_candidate = best_candidate
            initial_best_report = self._candidate_result(evaluation, best_id)
            selected_candidate = initial_best_candidate
            selected_report = initial_best_report
            refined_candidate = None
            refined_report = None
            num_rounds_done = 0

            if (not self.config.ablation_flags.no_refiner
                    and self.config.max_refinement_rounds > 0
                    and best_candidate is not None):
                rounds = self.config.max_refinement_rounds
                current_candidate = best_candidate
                current_eval = initial_best_report
                for round_idx in range(1, rounds + 1):
                    ref_result = DecompositionRefinerAgent(self.config, self.layout).run(
                        candidate=current_candidate,
                        evaluation=current_eval,
                        evidence_pack=evidence_pack,
                        domain_model=domain_model,
                        refinement_round=round_idx,
                    )
                    total_tokens += ref_result.tokens_used

                    refined_doc = read_json(self.layout.refined_candidate_path)
                    refined_eval_result = DecompositionEvaluatorAgent(self.config, self.layout).run(
                        candidates=refined_doc,
                        evidence_pack=evidence_pack,
                        domain_model=domain_model,
                        output_path=self.layout.refined_evaluation_path,
                    )
                    total_tokens += refined_eval_result.tokens_used
                    refined_eval_doc = refined_eval_result.output  # type: ignore[assignment]
                    refined_candidate = refined_doc["candidates"][0]
                    refined_report = self._candidate_result(
                        refined_eval_doc, refined_candidate["candidate_id"],
                    )
                    num_rounds_done = round_idx

                    if not self._is_report_improvement(refined_report, selected_report):
                        stopping_reason = "no_metric_improvement"
                        break

                    selected_candidate = refined_candidate
                    selected_report = refined_report
                    current_candidate = refined_candidate
                    current_eval = refined_report

                if stopping_reason != "no_metric_improvement":
                    stopping_reason = "max_rounds_reached"
            else:
                stopping_reason = "no_refinement_requested"

            # ── Select final candidate ───────────────────────────────────
            self._write_final_output(
                selected=selected_candidate,
                selected_report=selected_report,
                baseline_report=None,
                initial_report=initial_best_report,
                refined_report=refined_report,
                total_tokens=total_tokens,
                total_runtime=time.perf_counter() - wall_start,
                num_rounds=num_rounds_done,
                stopping_reason=stopping_reason,
            )
            final = read_json(self.layout.final_output_path)
            self.logger.info("controller.done run_id=%s tokens=%d runtime=%.2fs",
                             self.config.run_id, total_tokens,
                             time.perf_counter() - wall_start)
            return final
        finally:
            detach_file_handler(self.logger, handler)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _write_config(self) -> None:
        payload = self.config.to_dict()
        validate(payload, "run_config")
        write_json(self.layout.run_config_path, payload)

    @staticmethod
    def _find_candidate(doc: dict | None, candidate_id: str) -> dict | None:
        if not doc:
            return None
        for c in doc.get("candidates", []):
            if c.get("candidate_id") == candidate_id:
                return c
        return None

    @staticmethod
    def _candidate_result(report: dict | None, candidate_id: str) -> dict | None:
        if not report:
            return None
        for cr in report.get("candidate_results", []):
            if cr.get("candidate_id") == candidate_id:
                return cr
        return None

    @staticmethod
    def _is_report_improvement(new_report: dict | None, old_report: dict | None) -> bool:
        if not new_report:
            return False
        if not old_report:
            return True

        new_status = (new_report.get("recommendation") or {}).get("status")
        old_status = (old_report.get("recommendation") or {}).get("status")
        status_rank = {"reject": 0, "refine": 1, "accept": 2}
        if status_rank.get(new_status, 0) < status_rank.get(old_status, 0):
            return False

        new_score = new_report.get("composite_score")
        old_score = old_report.get("composite_score")
        if new_score is None or old_score is None:
            return status_rank.get(new_status, 0) > status_rank.get(old_status, 0)
        if float(new_score) > float(old_score):
            return True
        return (
            float(new_score) == float(old_score)
            and status_rank.get(new_status, 0) > status_rank.get(old_status, 0)
        )

    # ------------------------------------------------------------------
    def _write_final_output(
        self,
        *,
        selected: dict | None,
        selected_report: dict | None,
        baseline_report: dict | None,
        initial_report: dict | None,
        refined_report: dict | None,
        total_tokens: int,
        total_runtime: float,
        num_rounds: int,
        stopping_reason: str,
    ) -> None:
        selected_id = (selected or {}).get("candidate_id", "")
        final_metrics = (selected_report or {}).get("metrics") or {}

        # ── B0-compatible decomposition.json ─────────────────────────────
        decomposition = self._to_baseline_shape(selected) if selected else {
            "tool": {"decomposition": {}}
        }
        write_json(self.layout.decomposition_path, decomposition)

        def _row(report: dict | None) -> dict | None:
            if not report:
                return None
            return {
                "candidate_id": report.get("candidate_id"),
                "metrics":      report.get("metrics") or {},
                "source":       "this_run",
            }

        payload = {
            "run_id":                     self.config.run_id,
            "system":                     self.config.system,
            "selected_candidate_id":      selected_id,
            "selected_decomposition_path":
                str(self.layout.decomposition_path.relative_to(self.layout.root.parent.parent)).replace("\\", "/"),
            "final_metrics":              final_metrics,
            "comparison": {
                "single_llm_baseline":  baseline_report,
                "agentic_initial_best": _row(initial_report),
                "agentic_refined":      _row(refined_report),
            },
            "migration_roadmap": [],
            "run_metadata": {
                "total_tokens":          int(total_tokens),
                "input_tokens":          None,
                "output_tokens":         None,
                "total_runtime_seconds": round(total_runtime, 3),
                "num_refinement_rounds": int(num_rounds),
                "model":                 self.config.model,
                "evidence_mode":         self.config.evidence_mode,
                "summarisation_strategy": self.config.summarisation_strategy,
                "ablation_flags": {
                    "no_domain_agent": self.config.ablation_flags.no_domain_agent,
                    "no_quality_gate": self.config.ablation_flags.no_quality_gate,
                    "no_refiner":      self.config.ablation_flags.no_refiner,
                },
                "stopping_reason":     stopping_reason,
                "framework_version":   __version__,
            },
        }
        validate(payload, "final_output")
        write_json(self.layout.final_output_path, payload)

    @staticmethod
    def _to_baseline_shape(candidate: dict) -> dict:
        """Convert a candidate into the existing ``decomposition.json`` shape."""
        services = {}
        for svc in candidate.get("services", []):
            name = svc.get("name", "Unnamed")
            class_ids = []
            for cls in svc.get("classes", []):
                cid = cls["id"] if isinstance(cls, dict) else str(cls)
                class_ids.append({"id": cid})
            services[name] = class_ids
        return {"tool": {"decomposition": services}}
