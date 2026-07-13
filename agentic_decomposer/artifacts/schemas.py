"""JSON Schema registry.

Loads every schema from ``SCHEMAS_DIR`` at import time, caches the parsed JSON,
and exposes name-based lookup. Schemas are addressed by short names
(``"run_config"``, ``"evidence_pack"``, …) rather than file paths so that
callers don't hard-code disk locations.
"""
from __future__ import annotations

import json
from functools import lru_cache
from typing import Final, Literal

from agentic_decomposer.paths import SCHEMAS_DIR


SchemaName = Literal[
    "run_config",
    "evidence_pack",
    "domain_model",
    "candidate_decomposition",
    "evaluation_report",
    "refinement_patch",
    "final_output",
]


_SCHEMA_FILES: Final[dict[str, str]] = {
    "run_config":              "run_config.schema.json",
    "evidence_pack":           "evidence_pack.schema.json",
    "domain_model":            "domain_model.schema.json",
    "candidate_decomposition": "candidate_decomposition.schema.json",
    "evaluation_report":       "evaluation_report.schema.json",
    "refinement_patch":        "refinement_patch.schema.json",
    "final_output":            "final_output.schema.json",
}


class SchemaRegistry:
    """Read-only registry of all framework JSON schemas."""

    def __init__(self) -> None:
        self._schemas: dict[str, dict] = {}
        for name, filename in _SCHEMA_FILES.items():
            path = SCHEMAS_DIR / filename
            if not path.is_file():
                raise FileNotFoundError(
                    f"Schema {name!r} not found at {path}. "
                    "Did Stage 1 of the MVP roadmap complete?"
                )
            with path.open(encoding="utf-8") as fh:
                self._schemas[name] = json.load(fh)

    def get(self, name: SchemaName) -> dict:
        try:
            return self._schemas[name]
        except KeyError as exc:
            raise KeyError(
                f"Unknown schema {name!r}. Known: {sorted(self._schemas)}"
            ) from exc

    def names(self) -> tuple[str, ...]:
        return tuple(self._schemas.keys())


@lru_cache(maxsize=1)
def get_registry() -> SchemaRegistry:
    """Return a process-wide SchemaRegistry singleton."""
    return SchemaRegistry()
