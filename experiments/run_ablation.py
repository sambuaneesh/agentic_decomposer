#!/usr/bin/env python
"""Run the RQ2 ablation grid.

Core comparison variants:
- A1_gen_only: one candidate, no refinement; evaluator scores after generation
- A2_eval_select: three candidates, evaluator selects best, no refinement
- A3_refined: three candidates, evaluator selects best, one refinement round

Component ablation variants:
- A_no_domain: skips Domain Agent
- A_no_qg: skips Quality Gate effects
- A_1cand_refined: one generator candidate with refinement enabled

This script does **not** re-run the old single-shot baseline. It only records
where B0 should be loaded from so the result CSV can be joined with existing
baseline metrics later.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FRAMEWORK_ROOT = ROOT / "agentic_decomposer"
RESULTS_DIR = FRAMEWORK_ROOT / "experiments" / "results_ablation"
SYSTEMS = ("demo", "jpetstore-6", "spring-petclinic", "PartsUnlimitedMRP")
if str(FRAMEWORK_ROOT) not in sys.path:
    sys.path.insert(0, str(FRAMEWORK_ROOT))

from agentic_decomposer.metrics import METRIC_KEYS, run_metric_engine  # noqa: E402


@dataclass(frozen=True)
class Variant:
    name: str
    flags: tuple[str, ...]


VARIANTS = (
    Variant("A1_gen_only", ("--num-candidates", "1", "--no-refiner", "--max-refinement-rounds", "0")),
    Variant("A2_eval_select", ("--no-refiner", "--max-refinement-rounds", "0")),
    Variant("A3_refined", ()),
    Variant("A_no_domain", ("--no-domain-agent",)),
    Variant("A_no_qg", ("--no-quality-gate",)),
    Variant("A_1cand_refined", ("--num-candidates", "1")),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run agentic decomposition ablations.")
    parser.add_argument("--system", default="jpetstore-6",
                        choices=[*SYSTEMS, "all"])
    parser.add_argument("--model", default="gpt-5")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--evidence-mode", default="llm", choices=["llm", "deterministic", "external"])
    parser.add_argument("--external-views-dir", default=None)
    parser.add_argument("--summarisation-strategy", default="80k_concat")
    parser.add_argument("--b0-agent", default="codex",
                        help="Agent family folder used as B0 reference, e.g. codex or claude-code.")
    parser.add_argument("--b0-baseline", default="baseline-1")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    ns = parse_args()
    systems = SYSTEMS if ns.system == "all" else (ns.system,)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    csv_path = RESULTS_DIR / f"ablation_{ns.system}_{_model_slug(ns.model)}_{stamp}.csv"

    rows: list[dict] = []
    exit_code = 0
    for system in systems:
        rows.append(_b0_row(system, ns))
        for run_idx in range(1, ns.runs + 1):
            for variant in VARIANTS:
                code, row = _run_variant(system, ns, variant, run_idx)
                rows.append(row)
                exit_code = code or exit_code

    _write_rows(csv_path, rows)
    print(f"Wrote {csv_path}")
    return exit_code


def _run_variant(system: str, ns: argparse.Namespace, variant: Variant, run_idx: int) -> tuple[int, dict]:
    seed = run_idx
    cmd = [
        sys.executable, "-m", "agentic_decomposer", "run",
        "--system", system,
        "--model", ns.model,
        "--evidence-mode", ns.evidence_mode,
        "--summarisation-strategy", ns.summarisation_strategy,
        "--runs-dir", str(FRAMEWORK_ROOT / "runs" / variant.name),
        "--seed", str(seed),
    ]
    if ns.external_views_dir:
        cmd.extend(["--external-views-dir", ns.external_views_dir])
    cmd.extend(variant.flags)
    if ns.dry_run:
        cmd.append("--dry-run")

    env = dict(os.environ)
    env["PYTHONPATH"] = str(FRAMEWORK_ROOT)
    code = subprocess.call(cmd, cwd=str(ROOT), env=env)

    run_id = _run_id(system, ns.model, ns.summarisation_strategy, seed)
    final_path = FRAMEWORK_ROOT / "runs" / variant.name / run_id / "06_final" / "final_output.json"
    row = {
        "system": system,
        "variant": variant.name,
        "run": run_idx,
        "status": "ok" if code == 0 else "failed",
        "run_id": run_id,
        "final_output": _rel(final_path),
        "model": ns.model,
        "evidence_mode": ns.evidence_mode,
        "summarisation_strategy": ns.summarisation_strategy,
    }
    row.update({k: "" for k in METRIC_KEYS})
    if final_path.is_file():
        try:
            final = json.loads(final_path.read_text(encoding="utf-8"))
            for key, value in (final.get("final_metrics") or {}).items():
                if key in METRIC_KEYS:
                    row[key] = "" if value is None else value
        except json.JSONDecodeError:
            row["status"] = "bad_final_json"
    return code, row


def _b0_row(system: str, ns: argparse.Namespace) -> dict:
    decomp_path = ROOT / "results" / ns.b0_agent / ns.b0_baseline / system / "decomposition.json"
    row = {
        "system": system,
        "variant": "B0_single_shot",
        "run": 0,
        "status": "available" if decomp_path.is_file() else "missing",
        "run_id": "",
        "final_output": _rel(decomp_path),
        "model": ns.b0_agent,
        "evidence_mode": "baseline",
        "summarisation_strategy": ns.b0_baseline,
    }
    row.update({k: "" for k in METRIC_KEYS})
    if decomp_path.is_file() and not ns.dry_run:
        engine = run_metric_engine(
            decomposition_path=decomp_path,
            system=system,
            tool_name=f"b0-{ns.b0_agent}-{ns.b0_baseline}-{system}",
        )
        row["status"] = "scored" if engine.available else "metric_engine_unavailable"
        for key, value in engine.metrics.items():
            if key in METRIC_KEYS:
                row[key] = "" if value is None else value
    return row


def _write_rows(path: Path, rows: list[dict]) -> None:
    fieldnames = [
        "system", "variant", "run", "status", "run_id", "final_output",
        "model", "evidence_mode", "summarisation_strategy", *METRIC_KEYS,
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _model_slug(model: str) -> str:
    import re
    return re.sub(r"[^A-Za-z0-9]+", "", model).lower() or "model"


def _strategy_slug(strategy: str) -> str:
    return strategy.replace("_", "")


def _run_id(system: str, model: str, strategy: str, seed: int) -> str:
    return f"{system}_{_model_slug(model)}_{_strategy_slug(strategy)}_seed{seed}"


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
