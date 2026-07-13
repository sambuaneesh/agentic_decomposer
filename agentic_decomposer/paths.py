"""Workspace path resolution.

The framework lives at ``<workspace_root>/agentic_decomposer/agentic_decomposer/paths.py``.
We compute everything relative to this file so the same code runs on Windows
(``C:\\Users\\...\\Stuff\\agentic-experiments``) and Linux without changes,
as long as the surrounding folder structure is preserved:

    <shared parent>/
    ├── agentic-experiments/        ← AGENTIC_ROOT
    │   ├── codebases/
    │   ├── graph-artifacts/
    │   ├── prompts/                ← BASELINE_PROMPTS_DIR
    │   ├── results/                ← BASELINE_RESULTS_DIR (existing CLI-agent baselines)
    │   ├── scripts/
    │   └── agentic_decomposer/     ← FRAMEWORK_ROOT
    │       ├── schemas/            ← SCHEMAS_DIR
    │       ├── prompts/            ← PROMPTS_DIR
    │       ├── configs/            ← CONFIGS_DIR
    │       └── runs/               ← RUNS_DIR (output)
    └── src/
        └── metrics/scripts/        ← METRICS_DIR
            └── evaluate_decomposition.py
"""
from __future__ import annotations

from pathlib import Path
from typing import Final

# This file: <FRAMEWORK_ROOT>/agentic_decomposer/paths.py
_THIS_FILE = Path(__file__).resolve()

PACKAGE_DIR:    Final[Path] = _THIS_FILE.parent                 # agentic_decomposer/agentic_decomposer
FRAMEWORK_ROOT: Final[Path] = PACKAGE_DIR.parent                # agentic_decomposer
AGENTIC_ROOT:   Final[Path] = FRAMEWORK_ROOT.parent             # agentic-experiments
WORKSPACE_PARENT: Final[Path] = AGENTIC_ROOT.parent             # the shared parent

# Inputs that live in the wider agentic-experiments repo
CODEBASES_DIR:        Final[Path] = AGENTIC_ROOT / "codebases"
GRAPH_ARTIFACTS_DIR:  Final[Path] = AGENTIC_ROOT / "graph-artifacts"
BASELINE_PROMPTS_DIR: Final[Path] = AGENTIC_ROOT / "prompts"
BASELINE_RESULTS_DIR: Final[Path] = AGENTIC_ROOT / "results"
AGENTIC_SCRIPTS_DIR:  Final[Path] = AGENTIC_ROOT / "scripts"

# Inputs/outputs that live inside this framework
SCHEMAS_DIR: Final[Path] = FRAMEWORK_ROOT / "schemas"
PROMPTS_DIR: Final[Path] = FRAMEWORK_ROOT / "prompts"
CONFIGS_DIR: Final[Path] = FRAMEWORK_ROOT / "configs"
RUNS_DIR:    Final[Path] = FRAMEWORK_ROOT / "runs"
DOCS_DIR:    Final[Path] = FRAMEWORK_ROOT / "docs"

# External metric engine. Same convention as
# scripts/calculate_metrics_paper_comparison.py::METRICS_DIR.
METRICS_DIR:    Final[Path] = WORKSPACE_PARENT / "src" / "metrics" / "scripts"
METRICS_SCRIPT: Final[Path] = METRICS_DIR / "evaluate_decomposition.py"


# Codebase folder name → metric-engine application name. Identical to the
# REPO_TO_APP mapping in calculate_metrics_paper_comparison.py.
REPO_TO_APP: Final[dict[str, str]] = {
    "demo":              "demo",
    "jpetstore-6":       "jpetstore",
    "spring-petclinic":  "spring-petclinic",
    "PartsUnlimitedMRP": "partsunlimited",
}

SYSTEMS: Final[tuple[str, ...]] = tuple(REPO_TO_APP.keys())


def codebase_path(system: str) -> Path:
    """Return the absolute path to the pinned codebase for *system*."""
    if system not in REPO_TO_APP:
        raise ValueError(f"Unknown system {system!r}; expected one of {SYSTEMS}")
    return CODEBASES_DIR / system


def dependency_graph_path(system: str) -> Path:
    """Return the absolute path to the static class dependency graph (A6)."""
    if system not in REPO_TO_APP:
        raise ValueError(f"Unknown system {system!r}; expected one of {SYSTEMS}")
    return GRAPH_ARTIFACTS_DIR / f"{system}-class-dependency.json"


def metrics_app_name(system: str) -> str:
    """Return the metric-engine application name for *system*."""
    try:
        return REPO_TO_APP[system]
    except KeyError as exc:
        raise ValueError(f"Unknown system {system!r}; expected one of {SYSTEMS}") from exc


def relative_to_agentic(path: Path) -> str:
    """Return *path* as a forward-slash, agentic-root-relative string.

    Useful for embedding paths in manifests and CSVs so they remain portable
    between Windows and Linux checkouts.
    """
    abs_path = path.resolve()
    try:
        rel = abs_path.relative_to(AGENTIC_ROOT)
    except ValueError:
        # Outside agentic-experiments: try workspace-parent-relative instead.
        try:
            rel = abs_path.relative_to(WORKSPACE_PARENT)
            return rel.as_posix()
        except ValueError:
            return abs_path.as_posix()
    return f"agentic-experiments/{rel.as_posix()}"
