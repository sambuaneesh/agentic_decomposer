"""RunConfig loader.

A typed ``RunConfig`` is the single source of truth for everything an agent
needs to know about its enclosing run. It is built from a YAML config file
and/or CLI flags, validated against ``run_config.schema.json``, then frozen
and written to ``runs/<run_id>/00_config/run_config.json``.

The dataclass mirrors the JSON shape one-to-one so that ``to_dict()`` round-trips
through ``validate(payload, "run_config")``.
"""
from __future__ import annotations

import dataclasses
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from agentic_decomposer import __version__
from agentic_decomposer.artifacts.validators import validate
from agentic_decomposer.paths import (
    REPO_TO_APP,
    SYSTEMS,
    codebase_path,
    relative_to_agentic,
)


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

_DEFAULT_OBJECTIVES = {
    "structural_modularity": 0.30,
    "domain_alignment":      0.30,
    "cyclic_independence":   0.20,
    "migration_feasibility": 0.20,
}

_DEFAULT_CONSTRAINTS = {
    "each_class_assigned_once": True,
    "allow_unassigned_classes": False,
    "max_services":             None,
    "min_services":             2,
}

_DEFAULT_ABLATION_FLAGS = {
    "no_domain_agent": False,
    "no_quality_gate": False,
    "no_refiner":      False,
}


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Objectives:
    structural_modularity: float = _DEFAULT_OBJECTIVES["structural_modularity"]
    domain_alignment:      float = _DEFAULT_OBJECTIVES["domain_alignment"]
    cyclic_independence:   float = _DEFAULT_OBJECTIVES["cyclic_independence"]
    migration_feasibility: float = _DEFAULT_OBJECTIVES["migration_feasibility"]


@dataclass(frozen=True)
class Constraints:
    each_class_assigned_once: bool = _DEFAULT_CONSTRAINTS["each_class_assigned_once"]
    allow_unassigned_classes: bool = _DEFAULT_CONSTRAINTS["allow_unassigned_classes"]
    max_services:             int | None = _DEFAULT_CONSTRAINTS["max_services"]
    min_services:             int = _DEFAULT_CONSTRAINTS["min_services"]


@dataclass(frozen=True)
class AblationFlags:
    no_domain_agent: bool = _DEFAULT_ABLATION_FLAGS["no_domain_agent"]
    no_quality_gate: bool = _DEFAULT_ABLATION_FLAGS["no_quality_gate"]
    no_refiner:      bool = _DEFAULT_ABLATION_FLAGS["no_refiner"]


@dataclass(frozen=True)
class RunConfig:
    run_id: str
    system: str
    metrics_app: str
    repo_path: str
    model: str
    evidence_mode: str
    summarisation_strategy: str
    num_candidates: int
    max_refinement_rounds: int
    objectives: Objectives
    constraints: Constraints
    ablation_flags: AblationFlags
    seed: int
    commit_sha: str | None = None
    external_views_dir: str | None = None
    created_at_utc: str = ""
    framework_version: str = __version__

    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        # Empty optional fields stay as None — schema allows them.
        return d


# ---------------------------------------------------------------------------
# Loader / builder
# ---------------------------------------------------------------------------

def _slugify_model(model: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "", model).lower() or "model"


def _slugify_strategy(strategy: str) -> str:
    return strategy.replace("_", "")


def build_run_id(system: str, model: str, strategy: str, seed: int) -> str:
    return f"{system}_{_slugify_model(model)}_{_slugify_strategy(strategy)}_seed{seed}"


def _load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"Config file {path} must be a YAML mapping, got {type(data).__name__}")
    return data


def _merge(base: dict, override: dict) -> dict:
    """Shallow merge: override wins; nested dicts are merged one level deep."""
    out = dict(base)
    for k, v in override.items():
        if v is None:
            continue
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = {**out[k], **v}
        else:
            out[k] = v
    return out


def build_run_config(
    *,
    system: str,
    model: str,
    evidence_mode: str,
    summarisation_strategy: str,
    num_candidates: int,
    max_refinement_rounds: int,
    seed: int,
    external_views_dir: str | None = None,
    commit_sha: str | None = None,
    objectives: dict | None = None,
    constraints: dict | None = None,
    ablation_flags: dict | None = None,
    config_file: Path | None = None,
) -> RunConfig:
    """Build a RunConfig from CLI args, optionally merged with a YAML config.

    CLI args win over the YAML file. The result is validated against
    ``run_config.schema.json`` before it is returned, so any subsequent
    serialisation is guaranteed to round-trip.
    """
    file_data: dict[str, Any] = {}
    if config_file is not None:
        file_data = _load_yaml(config_file)

    # Build a single dict view so we can apply the file first, then CLI overrides.
    cli_view: dict[str, Any] = {
        "system": system,
        "model": model,
        "evidence_mode": evidence_mode,
        "summarisation_strategy": summarisation_strategy,
        "num_candidates": num_candidates,
        "max_refinement_rounds": max_refinement_rounds,
        "seed": seed,
        "external_views_dir": external_views_dir,
        "commit_sha": commit_sha,
        "objectives": objectives,
        "constraints": constraints,
        "ablation_flags": ablation_flags,
    }
    merged = _merge(file_data, cli_view)

    # Validate the required fields are now non-None.
    for key in ("system", "model", "evidence_mode", "summarisation_strategy",
                "num_candidates", "max_refinement_rounds", "seed"):
        if merged.get(key) is None:
            raise ValueError(f"RunConfig field {key!r} is required (set via CLI flag or config file)")

    sys_name = merged["system"]
    if sys_name not in REPO_TO_APP:
        raise ValueError(f"Unknown system {sys_name!r}; expected one of {SYSTEMS}")

    obj_kwargs = {**_DEFAULT_OBJECTIVES, **(merged.get("objectives") or {})}
    con_kwargs = {**_DEFAULT_CONSTRAINTS, **(merged.get("constraints") or {})}
    abl_kwargs = {**_DEFAULT_ABLATION_FLAGS, **(merged.get("ablation_flags") or {})}

    if merged["evidence_mode"] == "external" and not merged.get("external_views_dir"):
        raise ValueError("evidence_mode='external' requires --external-views-dir")

    run_id = merged.get("run_id") or build_run_id(
        sys_name, merged["model"], merged["summarisation_strategy"], int(merged["seed"])
    )

    config = RunConfig(
        run_id=run_id,
        system=sys_name,
        metrics_app=REPO_TO_APP[sys_name],
        repo_path=relative_to_agentic(codebase_path(sys_name)),
        model=merged["model"],
        evidence_mode=merged["evidence_mode"],
        summarisation_strategy=merged["summarisation_strategy"],
        num_candidates=int(merged["num_candidates"]),
        max_refinement_rounds=int(merged["max_refinement_rounds"]),
        objectives=Objectives(**obj_kwargs),
        constraints=Constraints(**con_kwargs),
        ablation_flags=AblationFlags(**abl_kwargs),
        seed=int(merged["seed"]),
        commit_sha=merged.get("commit_sha"),
        external_views_dir=merged.get("external_views_dir"),
        created_at_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        framework_version=__version__,
    )

    # Round-trip through the schema to catch any drift between dataclass and JSON.
    validate(config.to_dict(), "run_config")
    return config


def load_run_config_json(path: Path) -> RunConfig:
    """Load a previously frozen ``run_config.json`` back into a RunConfig."""
    import json
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    validate(data, "run_config")
    return RunConfig(
        run_id=data["run_id"],
        system=data["system"],
        metrics_app=data["metrics_app"],
        repo_path=data["repo_path"],
        model=data["model"],
        evidence_mode=data["evidence_mode"],
        summarisation_strategy=data["summarisation_strategy"],
        num_candidates=data["num_candidates"],
        max_refinement_rounds=data["max_refinement_rounds"],
        objectives=Objectives(**data["objectives"]),
        constraints=Constraints(**data["constraints"]),
        ablation_flags=AblationFlags(**data["ablation_flags"]),
        seed=data["seed"],
        commit_sha=data.get("commit_sha"),
        external_views_dir=data.get("external_views_dir"),
        created_at_utc=data.get("created_at_utc", ""),
        framework_version=data.get("framework_version", __version__),
    )
