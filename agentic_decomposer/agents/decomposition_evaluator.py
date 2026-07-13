"""Decomposition Evaluator agent.

Stage 6 of the MVP roadmap. For each candidate in
``candidate_decompositions.json``:

1. Runs the local Quality Gate.
2. Writes a B0-compatible ``decomposition.json`` to a temp path under the run
   folder and invokes the external metric engine via
   :func:`agentic_decomposer.metrics.engine.run_metric_engine`.
3. Builds a candidate diagnostic list from the quality-gate report + raw metrics.
4. Computes a composite score and produces a recommendation.

The agent always writes a schema-valid ``evaluation_report.json``. If the
metric engine is not available (Java missing / running on Windows without the
Linux mirror), all metric fields are set to ``null`` and a warning is logged —
the framework still finishes the run and the decomposition file is usable.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agentic_decomposer.agents.base import AgentResult, BaseAgent
from agentic_decomposer.artifacts.validators import validate
from agentic_decomposer.metrics import (
    METRIC_KEYS,
    EngineResult,
    QualityGateResult,
    compute_composite_score,
    run_metric_engine,
    run_quality_gate,
)
from agentic_decomposer.paths import METRICS_SCRIPT
from agentic_decomposer.runs import read_json, write_json


_DIAGNOSTIC_THRESHOLDS = {
    "CiD": 50.0,
    "CMod": 50.0,
    "DI": 30.0,
    "BCP": 50.0,
    "TC": 25.0,
    "MoJoFM": 30.0,
}

# Map a low-metric diagnostic to a suggested refiner operation hint.
_DIAGNOSTIC_TO_HINT: dict[str, list[str]] = {
    "low_cyclic_independence":   ["remove_invalid_dependency", "merge_services"],
    "low_modularity":            ["move_class", "split_service"],
    "low_domain_independence":   ["move_class", "reassign_responsibility"],
    "low_business_context_purity": ["split_service", "move_class"],
    "low_team_alignment":        ["move_class"],
    "low_mojofm":                ["merge_services", "split_service"],
}


class DecompositionEvaluatorAgent(BaseAgent):
    name = "decomposition_evaluator"

    def _run(
        self,
        candidates: dict | None = None,
        evidence_pack: dict | None = None,
        domain_model: dict | None = None,
        output_path: Path | None = None,
        **_: Any,
    ) -> AgentResult:
        if candidates is None:
            candidates = read_json(self.layout.candidates_path)
        if evidence_pack is None and self.layout.evidence_pack_path.is_file():
            evidence_pack = read_json(self.layout.evidence_pack_path)
        if domain_model is None and self.layout.domain_model_path.is_file():
            domain_model = read_json(self.layout.domain_model_path)

        target_path = output_path or self.layout.evaluation_report_path

        candidate_results: list[dict] = []
        best_id: str = ""
        best_score: float | None = None
        any_engine_warning: list[str] = []
        engine_available = METRICS_SCRIPT.is_file()
        quality_gate_enabled = not self.config.ablation_flags.no_quality_gate

        for cand in candidates.get("candidates", []):
            cand_id = cand.get("candidate_id", "")
            quality = (
                run_quality_gate(
                    cand,
                    evidence_pack,
                    domain_model=domain_model,
                    allow_unassigned_classes=self.config.constraints.allow_unassigned_classes,
                    min_services=self.config.constraints.min_services,
                    max_services=self.config.constraints.max_services,
                )
                if quality_gate_enabled
                else _skipped_quality_gate_result()
            )

            # Write candidate as decomposition.json to a per-candidate temp path
            # so we can hand it to the engine.
            tmp_decomp = self._materialise_decomposition(cand, cand_id)
            engine = (
                run_metric_engine(
                    decomposition_path=tmp_decomp,
                    system=self.config.system,
                    tool_name=f"agentic-{self.config.run_id}-{cand_id}",
                )
                if engine_available
                else EngineResult(
                    available=False,
                    metrics={k: None for k in METRIC_KEYS},
                    warnings=[
                        f"Metric engine not found at {METRICS_SCRIPT}. "
                        "Emit-only mode for this run.",
                    ],
                )
            )
            any_engine_warning.extend(engine.warnings)

            composite = compute_composite_score(
                engine.metrics,
                self.config.objectives,
                quality if quality_gate_enabled else None,
            )
            diagnostics = self._build_diagnostics(quality, engine.metrics)
            recommendation = self._recommend(quality, diagnostics, composite)

            candidate_results.append({
                "candidate_id":         cand_id,
                "metrics":              engine.metrics,
                "quality_gates":        quality.to_dict(),
                "composite_score":      composite,
                "diagnostics":          diagnostics,
                "recommendation":       recommendation,
                "engine_output_path":   engine.engine_output_path,
            })

            if recommendation["status"] != "reject":
                if (best_score is None
                        or (composite is not None and composite > best_score)
                        or (composite is None and best_score is None and not best_id)):
                    best_id, best_score = cand_id, composite
        if not best_id and candidate_results:
            # Nothing passed the gate; pick the first by tie-break.
            best_id = candidate_results[0]["candidate_id"]

        payload = {
            "system": self.config.system,
            "candidate_results": candidate_results,
            "best_candidate_id": best_id,
            "metadata": {
                "evaluated_at_utc":   datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "metric_engine_used": engine_available and not any_engine_warning,
                "metric_engine_path": str(METRICS_SCRIPT),
                "quality_gate_enabled": quality_gate_enabled,
                "engine_warnings":    any_engine_warning,
                "stub": False,
            },
        }
        validate(payload, "evaluation_report")
        write_json(target_path, payload)

        # CSV ranking table for human inspection
        self._write_ranking_csv(candidate_results)

        return AgentResult(
            name=self.name, output=payload, output_path=str(target_path),
        )

    # ------------------------------------------------------------------
    def _materialise_decomposition(self, candidate: dict, cand_id: str) -> Path:
        services: dict = {}
        for svc in candidate.get("services", []):
            services[svc.get("name", "Unnamed")] = [
                {"id": (c["id"] if isinstance(c, dict) else str(c))}
                for c in svc.get("classes", [])
            ]
        decomp = {"tool": {"decomposition": services}}
        target = self.layout.evaluation_dir / f"_decomp_{cand_id}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(decomp, indent=2), encoding="utf-8")
        return target

    # ------------------------------------------------------------------
    def _build_diagnostics(
        self,
        quality: QualityGateResult,
        metrics: dict[str, float | None],
    ) -> list[dict]:
        diags: list[dict] = []
        if not quality.no_duplicate_classes:
            diags.append({
                "type": "duplicate_class",
                "message": f"{len(quality.duplicate_class_assignments)} classes assigned to multiple services.",
                "affected_classes": [d["class"] for d in quality.duplicate_class_assignments[:20]],
                "affected_services": sorted({
                    s for d in quality.duplicate_class_assignments for s in d["services"]
                })[:20],
            })
        if quality.missing_classes:
            diags.append({
                "type": "missing_class",
                "message": f"{len(quality.missing_classes)} classes in evidence_pack are not assigned to any service.",
                "affected_classes": quality.missing_classes[:30],
            })
        if not quality.no_empty_services:
            diags.append({
                "type": "tiny_service",
                "message": "One or more services are empty.",
            })
        if not quality.unique_service_names:
            diags.append({
                "type": "duplicate_service_name",
                "message": "One or more service names are duplicated.",
                "affected_services": quality.duplicate_service_names[:20],
            })
        if not quality.valid_class_names_only:
            diags.append({
                "type": "invalid_class_name",
                "message": "One or more class IDs are not simple class names.",
                "affected_classes": quality.invalid_class_names[:20],
            })
        if not quality.all_services_have_evidence_refs:
            diags.append({
                "type": "missing_evidence_ref",
                "message": "One or more services do not cite evidence_refs.",
                "affected_services": quality.services_missing_evidence_refs[:20],
            })
        if not quality.all_evidence_refs_valid:
            diags.append({
                "type": "invalid_evidence_ref",
                "message": "One or more services cite evidence_refs that do not exist in the current artifacts.",
                "affected_services": sorted({r["service"] for r in quality.invalid_evidence_refs})[:20],
            })
        if not quality.service_count_within_bounds:
            diags.append({
                "type": "service_count_out_of_bounds",
                "message": f"Candidate has {quality.service_count} services outside configured min/max bounds.",
            })
        if quality.cyclic_dependency_count > 0:
            diags.append({
                "type": "cyclic_dependency",
                "message": f"{quality.cyclic_dependency_count} cyclic service-dependency chain(s) detected.",
            })
        for metric, threshold in _DIAGNOSTIC_THRESHOLDS.items():
            value = metrics.get(metric)
            if value is None:
                continue
            if value < threshold:
                diag_type = {
                    "CiD":    "low_cyclic_independence",
                    "CMod":   "low_modularity",
                    "DI":     "low_domain_independence",
                    "BCP":    "low_business_context_purity",
                    "TC":     "low_team_alignment",
                    "MoJoFM": "low_mojofm",
                }[metric]
                diags.append({
                    "type": diag_type,
                    "message": f"{metric}={value:.2f} below threshold {threshold:.0f}",
                })
        return diags

    # ------------------------------------------------------------------
    def _recommend(
        self,
        quality: QualityGateResult,
        diagnostics: list[dict],
        composite: float | None,
    ) -> dict:
        hard_failures = [
            d for d in diagnostics
            if d["type"] in {
                "duplicate_class", "duplicate_service_name", "missing_class", "invalid_class_name",
                "tiny_service", "missing_evidence_ref", "invalid_evidence_ref",
                "service_count_out_of_bounds",
            }
        ]
        if hard_failures:
            return {
                "status": "reject",
                "priority_fixes": [d["message"] for d in hard_failures[:5]],
                "suggested_operations": ["move_class", "split_service", "merge_services"],
            }

        if diagnostics or not quality.passes:
            ops: list[str] = []
            for d in diagnostics:
                for hint in _DIAGNOSTIC_TO_HINT.get(d["type"], []):
                    if hint not in ops:
                        ops.append(hint)
            if not ops:
                ops = ["move_class"]
            return {
                "status": "refine",
                "priority_fixes": [d["message"] for d in diagnostics[:5]],
                "suggested_operations": ops,
            }
        return {
            "status": "accept",
            "priority_fixes": [],
            "suggested_operations": [],
        }

    # ------------------------------------------------------------------
    def _write_ranking_csv(self, candidate_results: list[dict]) -> None:
        import csv
        path = self.layout.candidate_ranking_csv
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(
                ["candidate_id", "composite_score", "status", *METRIC_KEYS]
            )
            for cr in candidate_results:
                writer.writerow([
                    cr.get("candidate_id", ""),
                    "" if cr.get("composite_score") is None else cr["composite_score"],
                    cr.get("recommendation", {}).get("status", ""),
                    *[("" if cr["metrics"].get(k) is None else cr["metrics"][k]) for k in METRIC_KEYS],
                ])


def _skipped_quality_gate_result() -> QualityGateResult:
    return QualityGateResult(
        all_classes_assigned=True,
        no_duplicate_classes=True,
        no_empty_services=True,
        unique_service_names=True,
        valid_class_names_only=True,
        no_self_dependencies=True,
        all_dependency_targets_exist=True,
        all_services_have_rationale_or_responsibility=True,
        all_services_have_evidence_refs=True,
        all_evidence_refs_valid=True,
        service_count_within_bounds=True,
        cyclic_dependency_count=0,
        orphan_class_count=0,
    )
