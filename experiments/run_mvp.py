#!/usr/bin/env python
"""Run the MVP pipeline for one system.

This is a thin Python wrapper around the public CLI. It exists so experiment
commands can be versioned and cited from the paper without embedding long CLI
strings in shell scripts.

Examples
--------
python agentic_decomposer/experiments/run_mvp.py --system jpetstore-6 --model gpt-5
python agentic_decomposer/experiments/run_mvp.py --system demo --model gpt-5 --dry-run
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FRAMEWORK_ROOT = ROOT / "agentic_decomposer"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one agentic MVP decomposition.")
    parser.add_argument("--system", default="jpetstore-6",
                        choices=["demo", "jpetstore-6", "spring-petclinic", "PartsUnlimitedMRP"])
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
    cmd = [
        sys.executable, "-m", "agentic_decomposer", "run",
        "--system", ns.system,
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

    env = dict(os.environ)
    env["PYTHONPATH"] = str(FRAMEWORK_ROOT)
    return subprocess.call(cmd, cwd=str(ROOT), env=env)


if __name__ == "__main__":
    raise SystemExit(main())
