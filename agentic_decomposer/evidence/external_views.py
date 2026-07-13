"""Load pre-existing A1..A5 files from a user-provided directory.

Expected layout (documented in ``docs/evidence_modes.md``):

    <external-views-dir>/
      <system>/
        A1.md              free-form text or Mermaid diagram
        A2.json            list of {name, classes, type, responsibilities}
        A3.json            list of {method, path, handler_class, related_entities}
        A4.json            object {framework, database, build, container, ...}
        A5.md              free-form scenarios

Missing files are tolerated and the corresponding view is set to ``None`` /
empty.  The agent will never fall back to the LLM in external mode.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExternalViews:
    """Bundle of A1..A5 loaded from disk."""

    component_diagram: str | None
    components: list[dict]
    api_endpoints: list[dict]
    technology_map: dict
    dynamic_interactions: list[dict]
    loaded_files: dict[str, str]   # view name → relative path that was loaded


def load_external_views(root: Path, system: str) -> ExternalViews:
    """Load every available A1..A5 file under ``root/system/``."""
    base = root / system
    if not base.is_dir():
        raise FileNotFoundError(
            f"External views directory not found for system={system!r}: {base}"
        )

    loaded: dict[str, str] = {}

    a1 = base / "A1.md"
    component_diagram = a1.read_text(encoding="utf-8") if a1.is_file() else None
    if component_diagram is not None:
        loaded["A1"] = a1.name

    components = _load_json_list(base / "A2.json", loaded, key="A2")
    api_endpoints = _load_json_list(base / "A3.json", loaded, key="A3")

    a4 = base / "A4.json"
    if a4.is_file():
        with a4.open(encoding="utf-8") as fh:
            technology_map = json.load(fh)
        loaded["A4"] = a4.name
    else:
        technology_map = {}

    a5 = base / "A5.md"
    dynamic_interactions: list[dict] = []
    if a5.is_file():
        # MVP keeps A5 as a single free-text scenario block — the evidence
        # constructor turns it into one synthetic scenario record.
        text = a5.read_text(encoding="utf-8").strip()
        if text:
            dynamic_interactions = [{
                "scenario": "External A5 narrative",
                "sequence": [],
                "trigger": None,
                "narrative": text,
            }]
            loaded["A5"] = a5.name

    return ExternalViews(
        component_diagram=component_diagram,
        components=components,
        api_endpoints=api_endpoints,
        technology_map=technology_map or {},
        dynamic_interactions=dynamic_interactions,
        loaded_files=loaded,
    )


def _load_json_list(path: Path, loaded: dict[str, str], *, key: str) -> list[dict]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    loaded[key] = path.name
    if isinstance(data, dict) and "items" in data:
        data = data["items"]
    if not isinstance(data, list):
        raise ValueError(
            f"{path} must contain a JSON list (got {type(data).__name__})."
        )
    return data
