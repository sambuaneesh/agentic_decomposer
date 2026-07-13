"""Decomposition Refiner agent.

Stage 7 of the MVP roadmap. The agent asks the LLM for a controlled
``refinement_patch.json`` and applies it deterministically with the patcher.
It does **not** ask the LLM to regenerate the whole decomposition.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from agentic_decomposer.agents.base import AgentResult, BaseAgent
from agentic_decomposer.artifacts.validators import validate
from agentic_decomposer.helpers import LLMOutputError, extract_json_object
from agentic_decomposer.llm.client import LLMClient, LLMConfig
from agentic_decomposer.paths import PROMPTS_DIR
from agentic_decomposer.refinement import apply_patch, parse_operation
from agentic_decomposer.runs import read_json, write_json


_PROMPT_FILE = PROMPTS_DIR / "refiner.md"


class DecompositionRefinerAgent(BaseAgent):
    name = "decomposition_refiner"

    def _run(
        self,
        candidate: dict | None = None,
        evaluation: dict | None = None,
        evidence_pack: dict | None = None,
        domain_model: dict | None = None,
        refinement_round: int = 1,
        **_: Any,
    ) -> AgentResult:
        if candidate is None:
            raise ValueError("DecompositionRefinerAgent requires candidate")
        if evaluation is None:
            raise ValueError("DecompositionRefinerAgent requires evaluation")
        if evidence_pack is None and self.layout.evidence_pack_path.is_file():
            evidence_pack = read_json(self.layout.evidence_pack_path)
        if domain_model is None and self.layout.domain_model_path.is_file():
            domain_model = read_json(self.layout.domain_model_path)
        evidence_pack = evidence_pack or {"classes": [], "components": [], "dependency_edges": []}
        domain_model = domain_model or {"business_capabilities": []}

        prompt = self._build_prompt(
            candidate=candidate,
            evaluation=evaluation,
            evidence=evidence_pack,
            domain=domain_model,
            refinement_round=refinement_round,
        )
        llm = LLMClient(LLMConfig(
            model=self.config.model,
            seed=self.config.seed,
            log_path=self.layout.llm_calls_log_path,
        ))
        response = llm.complete(
            system="You are a software-architecture refiner. Output strict JSON only.",
            user=prompt,
        )
        try:
            patch = extract_json_object(response.text)
        except LLMOutputError as exc:
            raise LLMOutputError(
                f"Refiner could not parse LLM output for {candidate.get('candidate_id')}.",
                getattr(exc, "raw", response.text),
            ) from exc

        patch = self._normalise_patch(
            patch=patch,
            candidate_id=str(candidate.get("candidate_id") or "CAND_001"),
            refinement_round=refinement_round,
        )
        validate(patch, "refinement_patch")
        operations = [parse_operation(op) for op in patch.get("operations", [])]
        outcome = apply_patch(candidate, operations)

        refined_candidate = outcome.candidate
        refined_candidate["candidate_id"] = (
            f"{candidate.get('candidate_id', 'CAND_001')}_REFINED_{refinement_round}"
        )
        refined_candidate["strategy"] = "refined"
        refined_candidate["parent_candidate_id"] = candidate.get("candidate_id")
        refined_candidate["refinement_round"] = refinement_round
        refined_candidate["rationale"] = patch.get("rationale") or refined_candidate.get("rationale", "")

        refined_doc = {
            "system": self.config.system,
            "candidates": [refined_candidate],
            "metadata": {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "model": self.config.model,
                "tokens_used": response.total_tokens or 0,
                "stub": False,
                "applied_operations": outcome.applied,
                "skipped_operations": outcome.skipped,
            },
        }
        validate(refined_doc, "candidate_decomposition")
        write_json(self.layout.refinement_patch_path, patch)
        write_json(self.layout.refined_candidate_path, refined_doc)
        return AgentResult(
            name=self.name,
            output={"patch": patch, "refined": refined_doc},
            output_path=str(self.layout.refined_candidate_path),
            tokens_used=response.total_tokens or 0,
            extras={"applied_operations": outcome.applied, "skipped_operations": outcome.skipped},
        )

    # ------------------------------------------------------------------
    def _build_prompt(
        self,
        *,
        candidate: dict,
        evaluation: dict,
        evidence: dict,
        domain: dict,
        refinement_round: int,
    ) -> str:
        template = _PROMPT_FILE.read_text(encoding="utf-8")
        return (
            template
            .replace("<<SYSTEM>>", self.config.system)
            .replace("<<CANDIDATE_JSON>>", json.dumps(candidate, indent=2))
            .replace("<<EVALUATION_JSON>>", json.dumps(evaluation, indent=2))
            .replace("<<CLASSES_BLOCK>>", _format_classes(evidence))
            .replace("<<COMPONENTS_BLOCK>>", _format_components(evidence))
            .replace("<<CAPABILITIES_BLOCK>>", _format_capabilities(domain))
            .replace("<<EDGES_BLOCK>>", _format_edges(evidence))
            .replace('"refinement_round": 1', f'"refinement_round": {refinement_round}')
        )

    # ------------------------------------------------------------------
    def _normalise_patch(self, *, patch: dict, candidate_id: str, refinement_round: int) -> dict:
        operations = patch.get("operations") or []
        if not operations:
            # The schema requires at least one operation. Use a harmless
            # responsibility reassignment as a no-op fallback if the LLM says
            # nothing needs changing.
            operations = [{
                "operation": "reassign_responsibility",
                "service": "__NOOP__",
                "responsibility": "No refinement operation proposed.",
                "from_service": None,
                "reason": "LLM produced no operations; placeholder for schema validity.",
            }]
        return {
            "candidate_id": candidate_id,
            "refinement_round": int(refinement_round),
            "operations": operations,
            "expected_metric_effect": patch.get("expected_metric_effect") or {"CiD": "unknown"},
            "rationale": str(patch.get("rationale") or "Refinement patch generated from evaluator diagnostics."),
            "metadata": {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "model": self.config.model,
                "tokens_used": None,
                "stub": False,
            },
        }


def _format_classes(ev: dict) -> str:
    return "\n".join(
        f"- {c.get('id', '')} | {c['name']} | {c.get('package', '')} | {','.join(c.get('stereotypes') or []) or '-'}"
        for c in ev.get("classes", [])
    ) or "(none)"


def _format_components(ev: dict) -> str:
    return "\n".join(
        f"- {c['id']} | {c['name']} | classes={', '.join(c.get('classes', [])[:30])}"
        for c in ev.get("components", [])
    ) or "(none)"


def _format_capabilities(dm: dict) -> str:
    rows = []
    for cap in dm.get("business_capabilities", []):
        cls = ", ".join(c["class"] for c in (cap.get("related_classes") or [])[:30])
        rows.append(f"- {cap['id']} | {cap['name']} | classes=[{cls}]")
    return "\n".join(rows) or "(none)"


def _format_edges(ev: dict) -> str:
    edges = sorted(ev.get("dependency_edges", []), key=lambda e: -int(e.get("weight", 1)))
    return "\n".join(
        f"- {e['id']} | {e['source']} --{e['type']}({e.get('weight', 1)})--> {e['target']}"
        for e in edges[:160]
    ) or "(none)"
