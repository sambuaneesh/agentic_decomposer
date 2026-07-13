"""Quality Gate agent.

Stage 6 of the MVP roadmap. Thin wrapper around
:func:`agentic_decomposer.metrics.quality_gate.run_quality_gate` that writes a
standalone ``quality_gate_report.json`` for the controller-selected best
candidate.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from agentic_decomposer.agents.base import AgentResult, BaseAgent
from agentic_decomposer.metrics import run_quality_gate
from agentic_decomposer.runs import read_json, write_json


class QualityGateAgent(BaseAgent):
    name = "quality_gate"

    def _run(
        self,
        candidate: dict | None = None,
        evidence_pack: dict | None = None,
        domain_model: dict | None = None,
        **_: Any,
    ) -> AgentResult:
        if self.config.ablation_flags.no_quality_gate:
            report = {
                "skipped": True,
                "checked_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
            write_json(self.layout.quality_gate_report_path, report)
            self.logger.info("quality_gate skipped (--no-quality-gate).")
            return AgentResult(
                name=self.name, output=report,
                output_path=str(self.layout.quality_gate_report_path),
            )

        if candidate is None:
            self.logger.warning(
                "quality_gate invoked without a candidate; writing an empty report."
            )
            report = {
                "skipped": False,
                "passed": False,
                "reason": "No candidate provided.",
                "checked_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
            write_json(self.layout.quality_gate_report_path, report)
            return AgentResult(
                name=self.name, output=report,
                output_path=str(self.layout.quality_gate_report_path),
            )

        if domain_model is None and self.layout.domain_model_path.is_file():
            domain_model = read_json(self.layout.domain_model_path)

        qg = run_quality_gate(
            candidate,
            evidence_pack,
            domain_model=domain_model,
            allow_unassigned_classes=self.config.constraints.allow_unassigned_classes,
            min_services=self.config.constraints.min_services,
            max_services=self.config.constraints.max_services,
        )
        report = {
            "checked_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "candidate_id":   candidate.get("candidate_id"),
            "passed":         qg.passes,
            **qg.to_dict(),
        }
        write_json(self.layout.quality_gate_report_path, report)
        return AgentResult(
            name=self.name, output=report,
            output_path=str(self.layout.quality_gate_report_path),
        )
