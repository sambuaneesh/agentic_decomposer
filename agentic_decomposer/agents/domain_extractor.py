"""Domain Knowledge Extractor agent.

Stage 4 of the MVP roadmap. Calls the LLM with the evidence pack as
machine-readable context and asks it to infer business capabilities,
bounded-context hypotheses, and a class→capability matrix.

When the ``--no-domain-agent`` ablation flag is active this agent writes an
empty-but-schema-valid ``domain_model.json`` so downstream consumers do not
need to special-case the missing artifact.
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone
from typing import Any

from agentic_decomposer.agents.base import AgentResult, BaseAgent
from agentic_decomposer.artifacts.validators import validate
from agentic_decomposer.helpers import LLMOutputError, extract_json_object
from agentic_decomposer.llm.client import LLMClient, LLMConfig
from agentic_decomposer.paths import PROMPTS_DIR
from agentic_decomposer.runs import write_json


_PROMPT_FILE = PROMPTS_DIR / "domain_extractor.md"

# Allowed evidence labels (in addition to ID-style references like C001, API_003).
_LITERAL_EVIDENCE_LABELS = frozenset({
    "class name", "package name", "entity name", "scenario",
})

_ID_PREFIXES = ("BC", "C", "API_", "K_", "E_", "S_", "T_")


class DomainExtractorAgent(BaseAgent):
    name = "domain_extractor"

    def _run(self, evidence_pack: dict | None = None, **_: Any) -> AgentResult:
        if self.config.ablation_flags.no_domain_agent:
            payload = self._empty_payload(ablation=True, stub=False)
            validate(payload, "domain_model")
            write_json(self.layout.domain_model_path, payload)
            self._write_matrix_csv([])
            self.logger.info("domain_extractor skipped (--no-domain-agent); empty model written.")
            return AgentResult(name=self.name, output=payload,
                               output_path=str(self.layout.domain_model_path))

        if not evidence_pack:
            raise ValueError("DomainExtractorAgent requires evidence_pack in kwargs")

        prompt = self._build_prompt(evidence_pack)
        llm = LLMClient(LLMConfig(
            model=self.config.model,
            seed=self.config.seed,
            log_path=self.layout.llm_calls_log_path,
        ))
        result = llm.complete(
            system="You are a domain modeller. Output strict JSON only.",
            user=prompt,
        )

        try:
            raw_model = extract_json_object(result.text)
        except LLMOutputError as exc:
            raise LLMOutputError(
                f"Domain Extractor could not parse LLM output for {self.config.system}.",
                getattr(exc, "raw", result.text),
            ) from exc

        normalised = self._normalise(raw_model, evidence_pack)
        normalised["metadata"] = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "model": self.config.model,
            "tokens_used": result.total_tokens or 0,
            "ablation_no_domain_agent": False,
            "stub": False,
        }
        validate(normalised, "domain_model")
        write_json(self.layout.domain_model_path, normalised)
        self._write_matrix_csv(normalised["class_capability_matrix"])
        return AgentResult(
            name=self.name, output=normalised,
            output_path=str(self.layout.domain_model_path),
            tokens_used=result.total_tokens or 0,
        )

    # ------------------------------------------------------------------
    def _empty_payload(self, *, ablation: bool, stub: bool) -> dict:
        return {
            "system": self.config.system,
            "business_capabilities": [],
            "bounded_context_hypotheses": [],
            "class_capability_matrix": [],
            "metadata": {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "model": None,
                "tokens_used": 0,
                "ablation_no_domain_agent": ablation,
                "stub": stub,
            },
        }

    # ------------------------------------------------------------------
    def _build_prompt(self, evidence: dict) -> str:
        template = _PROMPT_FILE.read_text(encoding="utf-8")

        def _format_components() -> str:
            rows = []
            for c in evidence.get("components", []):
                rows.append(
                    f"- {c['id']} | {c['name']} | type={c.get('type')} | "
                    f"classes={', '.join(c.get('classes', [])[:25])}"
                )
            return "\n".join(rows) or "(none)"

        def _format_endpoints() -> str:
            rows = []
            for ep in evidence.get("api_endpoints", [])[:80]:
                rows.append(f"- {ep['id']} | {ep['method']} {ep['path']} → {ep['handler_class']}")
            return "\n".join(rows) or "(none)"

        def _format_entities() -> str:
            rows = []
            for e in evidence.get("persistence_entities", []):
                rows.append(
                    f"- {e['entity']} | repo={e.get('repository')} | "
                    f"tables={', '.join(e.get('tables') or [])}"
                )
            return "\n".join(rows) or "(none)"

        def _format_classes() -> str:
            rows = []
            for c in evidence.get("classes", []):
                stereotypes = ",".join(c.get("stereotypes") or []) or "-"
                rows.append(
                    f"- {c['id']} | {c['name']} | {c.get('package', '')} | {stereotypes}"
                )
            return "\n".join(rows)

        return (
            template
            .replace("<<SYSTEM>>", self.config.system)
            .replace("<<NUM_CLASSES>>", str(len(evidence.get("classes", []))))
            .replace("<<NUM_COMPONENTS>>", str(len(evidence.get("components", []))))
            .replace("<<NUM_ENDPOINTS>>", str(len(evidence.get("api_endpoints", []))))
            .replace("<<NUM_ENTITIES>>", str(len(evidence.get("persistence_entities", []))))
            .replace("<<TECHNOLOGY>>",
                     ", ".join(f"{k}={v}" for k, v in (evidence.get("technology_map") or {}).items() if v))
            .replace("<<COMPONENTS_BLOCK>>", _format_components())
            .replace("<<ENDPOINTS_BLOCK>>", _format_endpoints())
            .replace("<<ENTITIES_BLOCK>>", _format_entities())
            .replace("<<CLASSES_BLOCK>>", _format_classes())
            .replace("<<SOURCE_SUMMARY>>", (evidence.get("source_summary") or "(none)")[:8000])
        )

    # ------------------------------------------------------------------
    def _normalise(self, raw: dict, evidence: dict) -> dict:
        known_classes = {c["name"] for c in evidence.get("classes", [])}

        capabilities: list[dict] = []
        seen_ids: set[str] = set()
        for idx, cap in enumerate(raw.get("business_capabilities") or [], start=1):
            cap_id = cap.get("id") or f"BC{idx:03d}"
            if not cap_id.startswith("BC"):
                cap_id = f"BC{idx:03d}"
            if cap_id in seen_ids:
                cap_id = f"BC{idx:03d}"
            seen_ids.add(cap_id)

            related = []
            for rc in cap.get("related_classes") or []:
                cls = _simple(rc.get("class"))
                if cls not in known_classes:
                    continue
                confidence = _clip01(rc.get("confidence"))
                evidence_refs = [
                    e for e in (rc.get("evidence") or [])
                    if isinstance(e, str) and (
                        e in _LITERAL_EVIDENCE_LABELS
                        or any(e.startswith(p) for p in _ID_PREFIXES)
                    )
                ]
                related.append({
                    "class": cls,
                    "confidence": confidence,
                    "evidence": evidence_refs,
                })
            if not related:
                continue
            capabilities.append({
                "id": cap_id,
                "name": str(cap.get("name") or f"Capability {idx}"),
                "description": str(cap.get("description") or ""),
                "related_terms": list(cap.get("related_terms") or []),
                "related_classes": related,
            })

        contexts: list[dict] = []
        for ctx in raw.get("bounded_context_hypotheses") or []:
            classes = [_simple(c) for c in (ctx.get("classes") or []) if _simple(c) in known_classes]
            if not classes:
                continue
            cap_refs = [
                ref for ref in (ctx.get("related_capability_ids") or [])
                if isinstance(ref, str) and ref.startswith("BC")
            ]
            contexts.append({
                "name": str(ctx.get("name") or "Context"),
                "classes": classes,
                "rationale": str(ctx.get("rationale") or ""),
                "related_capability_ids": cap_refs,
            })

        # Build the flat matrix: prefer LLM-provided rows, but enforce one row per class.
        seen_classes: set[str] = set()
        matrix: list[dict] = []
        for row in raw.get("class_capability_matrix") or []:
            cls = _simple(row.get("class"))
            cap_id = str(row.get("capability_id") or "")
            if cls in seen_classes or cls not in known_classes:
                continue
            if not cap_id.startswith("BC"):
                continue
            matrix.append({
                "class": cls,
                "capability_id": cap_id,
                "capability_name": row.get("capability_name"),
                "confidence": _clip01(row.get("confidence")),
            })
            seen_classes.add(cls)

        # Fall back to the per-capability `related_classes` to fill missing rows.
        cap_index = {c["id"]: c for c in capabilities}
        for cap in capabilities:
            for rc in cap["related_classes"]:
                if rc["class"] in seen_classes:
                    continue
                matrix.append({
                    "class": rc["class"],
                    "capability_id": cap["id"],
                    "capability_name": cap["name"],
                    "confidence": rc["confidence"],
                })
                seen_classes.add(rc["class"])

        return {
            "system": self.config.system,
            "business_capabilities": capabilities,
            "bounded_context_hypotheses": contexts,
            "class_capability_matrix": matrix,
        }

    # ------------------------------------------------------------------
    def _write_matrix_csv(self, matrix: list[dict]) -> None:
        path = self.layout.class_capability_csv
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["class", "capability_id", "capability_name", "confidence"])
            for row in matrix:
                writer.writerow([
                    row.get("class", ""),
                    row.get("capability_id", ""),
                    row.get("capability_name", "") or "",
                    row.get("confidence", "") if row.get("confidence") is not None else "",
                ])


def _simple(name: object) -> str:
    if isinstance(name, dict):
        return str(name.get("id") or name.get("name") or "").rsplit(".", 1)[-1]
    return str(name or "").rsplit(".", 1)[-1]


def _clip01(value: object) -> float:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return 0.5
    if v < 0.0:
        return 0.0
    if v > 1.0:
        return 1.0
    return v
