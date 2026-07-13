"""Command-line interface for the framework.

Usage examples (see ``docs/usage.md`` for the full list):

    python -m agentic_decomposer run --system jpetstore-6 --model gpt-5
    python -m agentic_decomposer run --system all --model gpt-5
    python -m agentic_decomposer run --config configs/mvp_jpetstore.yaml
    python -m agentic_decomposer run --system demo --dry-run
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

from agentic_decomposer.agents.process_controller import ProcessController
from agentic_decomposer.config import RunConfig, build_run_config
from agentic_decomposer.logger import get_logger
from agentic_decomposer.paths import FRAMEWORK_ROOT, RUNS_DIR, SYSTEMS


_DEFAULT_MODEL = "gpt-5"


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="agentic_decomposer",
        description="Multi-agent monolith-to-microservices decomposition framework.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Run the full pipeline.")
    run.add_argument("--system",  default=None,
                     choices=[*SYSTEMS, "all"],
                     help="Codebase to decompose, or 'all'. Optional when --config has system.")
    run.add_argument("--model",   default=None,
                     help="LiteLLM model string (e.g. gpt-5, anthropic/claude-sonnet-4-20250514).")
    run.add_argument("--evidence-mode", default=None,
                     choices=["llm", "deterministic", "external"])
    run.add_argument("--external-views-dir", default=None,
                     help="Required when --evidence-mode=external.")
    run.add_argument("--summarisation-strategy", default=None,
                     choices=["30k_concat", "30k_aggregate",
                              "50k_concat", "50k_aggregate",
                              "80k_concat", "80k_aggregate",
                              "hierarchical"])
    run.add_argument("--num-candidates", type=int, default=None, choices=range(1, 11),
                     metavar="N (1-10)")
    run.add_argument("--max-refinement-rounds", type=int, default=None, choices=range(0, 6),
                     metavar="N (0-5)")
    run.add_argument("--seed", type=int, default=None)

    run.add_argument("--no-domain-agent", action="store_true", default=None, help="Ablation flag.")
    run.add_argument("--no-quality-gate", action="store_true", default=None, help="Ablation flag.")
    run.add_argument("--no-refiner",      action="store_true", default=None, help="Ablation flag.")

    run.add_argument("--config", type=Path, default=None,
                     help="Optional YAML config file; CLI flags override values in the file.")
    run.add_argument("--runs-dir", type=Path, default=RUNS_DIR,
                     help="Directory under which per-run folders are created (default: agentic_decomposer/runs/).")
    run.add_argument("--dry-run", action="store_true",
                     help="Validate config + create run folder, then exit without invoking agents.")

    return parser.parse_args(argv)


def _resolve_config_path(path: Path | None) -> Path | None:
    if path is None:
        return None
    if path.is_file():
        return path
    framework_relative = FRAMEWORK_ROOT / path
    if framework_relative.is_file():
        return framework_relative
    config_name = FRAMEWORK_ROOT / "configs" / path.name
    if config_name.is_file():
        return config_name
    return path


def _system_from_config(path: Path | None) -> str | None:
    if path is None or not path.is_file():
        return None
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        return None
    value = data.get("system")
    return str(value) if value else None


def _cli_value(ns: argparse.Namespace, attr: str, default: Any) -> Any:
    value = getattr(ns, attr)
    if value is None and ns.config is None:
        return default
    return value


def _build_config_for_system(system: str, ns: argparse.Namespace) -> RunConfig:
    no_refiner = ns.no_refiner if ns.no_refiner is not None else None
    max_rounds = _cli_value(ns, "max_refinement_rounds", 1)
    if no_refiner:
        max_rounds = 0
    ablation_flags = {
        key: value for key, value in {
            "no_domain_agent": ns.no_domain_agent,
            "no_quality_gate": ns.no_quality_gate,
            "no_refiner":      ns.no_refiner,
        }.items() if value is not None
    }
    return build_run_config(
        system=system,
        model=_cli_value(ns, "model", _DEFAULT_MODEL),
        evidence_mode=_cli_value(ns, "evidence_mode", "llm"),
        summarisation_strategy=_cli_value(ns, "summarisation_strategy", "80k_concat"),
        num_candidates=_cli_value(ns, "num_candidates", 3),
        max_refinement_rounds=max_rounds,
        seed=_cli_value(ns, "seed", 1),
        external_views_dir=ns.external_views_dir,
        ablation_flags=ablation_flags or None,
        config_file=ns.config,
    )


def _run_one(ns: argparse.Namespace, system: str) -> int:
    logger = get_logger("agentic.cli")
    cfg = _build_config_for_system(system, ns)
    logger.info("cli.run system=%s run_id=%s dry_run=%s", system, cfg.run_id, ns.dry_run)
    controller = ProcessController(cfg, runs_dir=ns.runs_dir)
    if ns.dry_run:
        controller.layout.create()
        from agentic_decomposer.runs import write_json
        write_json(controller.layout.run_config_path, cfg.to_dict())
        logger.info("cli.dry_run_done run_id=%s folder=%s",
                    cfg.run_id, controller.layout.root)
        return 0
    controller.run()
    return 0


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv if argv is not None else sys.argv[1:])
    ns.config = _resolve_config_path(ns.config)
    logger = get_logger("agentic.cli")
    if ns.command != "run":
        logger.error("Unsupported command %s", ns.command)
        return 2

    selected_system = ns.system or _system_from_config(ns.config)
    if not selected_system:
        logger.error("--system is required unless --config contains a system field")
        return 2
    if selected_system not in (*SYSTEMS, "all"):
        logger.error("Unknown system %s; expected one of %s or all", selected_system, SYSTEMS)
        return 2

    systems = list(SYSTEMS) if selected_system == "all" else [selected_system]
    exit_code = 0
    for system in systems:
        try:
            exit_code = _run_one(ns, system) or exit_code
        except Exception:
            logger.exception("Run failed for system=%s", system)
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
