#!/usr/bin/env python
"""Run the MVP pipeline over all four benchmark systems.

Examples
--------
python agentic_decomposer/experiments/run_all_systems.py --model gpt-5
python agentic_decomposer/experiments/run_all_systems.py --model gpt-5 --dry-run
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FRAMEWORK_ROOT = ROOT / "agentic_decomposer"
SYSTEMS = ("demo", "jpetstore-6", "spring-petclinic", "PartsUnlimitedMRP")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run all four agentic MVP decompositions.")
    parser.add_argument("--model", default="gpt-5")
    parser.add_argument("--evidence-mode", default="llm", choices=["llm", "deterministic", "external"])
    parser.add_argument("--external-views-dir", default=None)
    parser.add_argument("--summarisation-strategy", default="80k_concat")
    parser.add_argument("--num-candidates", type=int, default=3)
    parser.add_argument("--max-refinement-rounds", type=int, default=1)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    ns = parse_args()
    exit_code = 0
    env = dict(os.environ)
    env["PYTHONPATH"] = str(FRAMEWORK_ROOT)
    for system in SYSTEMS:
        cmd = [
            sys.executable, "-m", "agentic_decomposer", "run",
            "--system", system,
            "--model", ns.model,
            "--evidence-mode", ns.evidence_mode,
            "--summarisation-strategy", ns.summarisation_strategy,
            "--num-candidates", str(ns.num_candidates),
            "--max-refinement-rounds", str(ns.max_refinement_rounds),
            "--seed", str(ns.seed),
        ]
        if ns.external_views_dir:
            cmd.extend(["--external-views-dir", ns.external_views_dir])
        if ns.dry_run:
            cmd.append("--dry-run")
        exit_code = subprocess.call(cmd, cwd=str(ROOT), env=env) or exit_code
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
