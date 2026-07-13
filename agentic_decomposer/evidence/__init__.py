"""Architectural evidence builders.

The Evidence Constructor agent composes its output from this subpackage. Three
modes are supported and documented in ``docs/evidence_modes.md``:

- :mod:`agentic_decomposer.evidence.llm_views`           — A1..A5 via LLM
- :mod:`agentic_decomposer.evidence.deterministic_views` — A2/A3/A4 via static parsing
- :mod:`agentic_decomposer.evidence.external_views`      — A1..A5 from disk

A6 is always built from
:mod:`agentic_decomposer.evidence.dependency_graph_loader` (which reads the
existing ``graph-artifacts/<system>-class-dependency.json`` files).
"""

from agentic_decomposer.evidence.source_walker import (
    SourceWalker,
    SourceFile,
    walk_codebase,
)
from agentic_decomposer.evidence.dependency_graph_loader import (
    load_dependency_graph,
    DependencyGraphData,
)

__all__ = [
    "SourceWalker",
    "SourceFile",
    "walk_codebase",
    "load_dependency_graph",
    "DependencyGraphData",
]
