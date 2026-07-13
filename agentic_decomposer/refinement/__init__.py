"""Refinement subpackage.

The Refiner agent calls the LLM, parses a :class:`RefinementPatch`, and
applies it deterministically via :func:`apply_patch`. Operations are typed
dataclasses so we can validate them statically before mutating the candidate.
"""

from agentic_decomposer.refinement.operations import (
    AddDependency,
    MergeServices,
    MoveClass,
    Operation,
    ReassignResponsibility,
    RemoveInvalidDependency,
    RenameService,
    SplitService,
    parse_operation,
)
from agentic_decomposer.refinement.patcher import apply_patch

__all__ = [
    "AddDependency",
    "MergeServices",
    "MoveClass",
    "Operation",
    "ReassignResponsibility",
    "RemoveInvalidDependency",
    "RenameService",
    "SplitService",
    "apply_patch",
    "parse_operation",
]
