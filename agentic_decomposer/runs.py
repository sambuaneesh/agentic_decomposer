"""Run-folder layout.

Encapsulates the canonical directory structure under ``runs/<run_id>/`` so
every agent writes to the same place without hard-coding strings.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agentic_decomposer.paths import RUNS_DIR


@dataclass(frozen=True)
class RunLayout:
    """Resolved paths for one run."""

    run_id: str
    root: Path

    # Folder accessors -------------------------------------------------------
    @property
    def config_dir(self) -> Path:      return self.root / "00_config"
    @property
    def evidence_dir(self) -> Path:    return self.root / "01_evidence"
    @property
    def domain_dir(self) -> Path:      return self.root / "02_domain"
    @property
    def candidates_dir(self) -> Path:  return self.root / "03_candidates"
    @property
    def evaluation_dir(self) -> Path:  return self.root / "04_evaluation"
    @property
    def refinement_dir(self) -> Path:  return self.root / "05_refinement"
    @property
    def final_dir(self) -> Path:       return self.root / "06_final"
    @property
    def logs_dir(self) -> Path:        return self.root / "logs"

    # Canonical file paths ---------------------------------------------------
    @property
    def run_config_path(self) -> Path:           return self.config_dir / "run_config.json"
    @property
    def evidence_pack_path(self) -> Path:        return self.evidence_dir / "evidence_pack.json"
    @property
    def domain_model_path(self) -> Path:         return self.domain_dir / "domain_model.json"
    @property
    def class_capability_csv(self) -> Path:      return self.domain_dir / "class_capability_matrix.csv"
    @property
    def candidates_path(self) -> Path:           return self.candidates_dir / "candidate_decompositions.json"
    @property
    def candidates_validation_path(self) -> Path:return self.candidates_dir / "schema_validation.json"
    @property
    def evaluation_report_path(self) -> Path:    return self.evaluation_dir / "evaluation_report.json"
    @property
    def quality_gate_report_path(self) -> Path:  return self.evaluation_dir / "quality_gate_report.json"
    @property
    def candidate_ranking_csv(self) -> Path:     return self.evaluation_dir / "candidate_ranking.csv"
    @property
    def refinement_patch_path(self) -> Path:     return self.refinement_dir / "refinement_patch.json"
    @property
    def refined_candidate_path(self) -> Path:    return self.refinement_dir / "refined_candidate.json"
    @property
    def refined_evaluation_path(self) -> Path:   return self.refinement_dir / "refined_evaluation_report.json"
    @property
    def final_output_path(self) -> Path:         return self.final_dir / "final_output.json"
    @property
    def decomposition_path(self) -> Path:        return self.final_dir / "decomposition.json"
    @property
    def llm_calls_log_path(self) -> Path:        return self.logs_dir / "llm_calls.jsonl"
    @property
    def controller_log_path(self) -> Path:       return self.logs_dir / "controller.log"

    # Helpers ---------------------------------------------------------------
    def create(self) -> None:
        """Create every subdirectory. Idempotent."""
        for folder in (
            self.config_dir, self.evidence_dir, self.domain_dir,
            self.candidates_dir, self.evaluation_dir, self.refinement_dir,
            self.final_dir, self.logs_dir,
        ):
            folder.mkdir(parents=True, exist_ok=True)

    def agent_log_path(self, agent_name: str) -> Path:
        safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in agent_name)
        return self.logs_dir / f"agent_{safe}.log"


def make_layout(run_id: str, runs_dir: Path | None = None) -> RunLayout:
    """Return a :class:`RunLayout` rooted at ``runs_dir / run_id`` (default ``RUNS_DIR``)."""
    root = (runs_dir or RUNS_DIR) / run_id
    return RunLayout(run_id=run_id, root=root)


def write_json(path: Path, payload: Any) -> None:
    """Write *payload* as pretty-printed UTF-8 JSON; create parent dirs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False, sort_keys=False)
        fh.write("\n")


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)
