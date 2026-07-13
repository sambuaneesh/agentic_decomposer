"""Load the static class-dependency graph (A6) from ``graph-artifacts/``.

The graph files have the shape produced by an external static analyser:

    {
      "metadata": {...},
      "classes": {
        "<fully.qualified.ClassName>": {
          "methods":  [...],
          "fields":   [...],
          "relationships": {
            "USED_BY":   {"<other.fqn>": weight, ...},
            "CALLS":     {"<other.fqn>": weight, ...},
            "USES":      {...},
            "CREATES":   {...},
            "EXTENDS":   {...},
            "IMPLEMENTS":{...}
          }
        },
        ...
      }
    }

``USED_BY`` is the inverse of ``USES``. To avoid double-counting we only keep
outgoing edges (CALLS, USES, CREATES, EXTENDS, IMPLEMENTS).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from agentic_decomposer.paths import dependency_graph_path


# Outgoing relationship keys we keep (and what we map them to in evidence_pack).
_OUTGOING_EDGE_TYPES: tuple[str, ...] = (
    "CALLS", "USES", "CREATES", "EXTENDS", "IMPLEMENTS",
)


@dataclass
class ClassNode:
    """One class entry from the dependency graph."""

    fqn: str
    simple_name: str
    package: str
    methods: list[dict] = field(default_factory=list)
    fields:  list[dict] = field(default_factory=list)


@dataclass
class DependencyEdge:
    """One outgoing relationship between two classes."""

    source_fqn: str
    target_fqn: str
    type: str
    weight: int

    @property
    def source_simple(self) -> str:
        return _simple(self.source_fqn)

    @property
    def target_simple(self) -> str:
        return _simple(self.target_fqn)


@dataclass
class DependencyGraphData:
    """Parsed dependency graph, exposed in convenient shapes for downstream use."""

    system: str
    classes: list[ClassNode]
    edges:   list[DependencyEdge]
    metadata: dict

    @property
    def fqns(self) -> list[str]:
        return [c.fqn for c in self.classes]

    @property
    def simple_names(self) -> list[str]:
        return [c.simple_name for c in self.classes]


# ----------------------------------------------------------------------
def load_dependency_graph(system: str, path: Path | None = None) -> DependencyGraphData:
    """Load and normalise the dependency graph for *system*.

    Parameters
    ----------
    system:
        One of the four supported systems (``demo``, ``jpetstore-6``,
        ``spring-petclinic``, ``PartsUnlimitedMRP``).
    path:
        Optional explicit path; defaults to
        ``graph-artifacts/<system>-class-dependency.json``.
    """
    graph_path = path or dependency_graph_path(system)
    if not graph_path.is_file():
        raise FileNotFoundError(
            f"Dependency graph not found for system={system!r} at {graph_path}"
        )
    with graph_path.open(encoding="utf-8") as fh:
        raw = json.load(fh)

    raw_classes: dict = raw.get("classes", {}) or {}
    classes = [
        ClassNode(
            fqn=fqn,
            simple_name=_simple(fqn),
            package=_pkg(fqn),
            methods=info.get("methods", []) or [],
            fields=info.get("fields", []) or [],
        )
        for fqn, info in raw_classes.items()
    ]
    classes.sort(key=lambda c: c.fqn)

    edges: list[DependencyEdge] = []
    for fqn, info in raw_classes.items():
        relationships = info.get("relationships", {}) or {}
        for edge_type in _OUTGOING_EDGE_TYPES:
            targets = relationships.get(edge_type, {}) or {}
            for target_fqn, weight in targets.items():
                try:
                    weight_int = int(weight)
                except (TypeError, ValueError):
                    weight_int = 1
                edges.append(DependencyEdge(
                    source_fqn=fqn,
                    target_fqn=target_fqn,
                    type=edge_type,
                    weight=max(1, weight_int),
                ))

    return DependencyGraphData(
        system=system,
        classes=classes,
        edges=edges,
        metadata=raw.get("metadata", {}) or {},
    )


# ----------------------------------------------------------------------
def _simple(fqn: str) -> str:
    """Return the simple class name (last dot-separated segment)."""
    return fqn.rsplit(".", 1)[-1] if fqn else fqn


def _pkg(fqn: str) -> str:
    """Return everything before the simple class name."""
    parts = fqn.rsplit(".", 1)
    return parts[0] if len(parts) == 2 else ""
