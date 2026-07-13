"""Typed operation dataclasses + parser.

Every operation mirrors a ``oneOf`` branch in
``schemas/refinement_patch.schema.json``. The parser turns a raw dict into a
typed dataclass and raises ``ValueError`` if the shape is wrong.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class MoveClass:
    class_: str
    from_service: str
    to_service: str
    reason: str

    operation: str = "move_class"


@dataclass(frozen=True)
class SplitService:
    service: str
    split_into: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...]
    # split_into = ((new_name, (classes...), (responsibilities...)), ...)
    reason: str

    operation: str = "split_service"


@dataclass(frozen=True)
class MergeServices:
    source_services: tuple[str, ...]
    target_service: str
    reason: str

    operation: str = "merge_services"


@dataclass(frozen=True)
class RenameService:
    from_name: str
    to_name: str
    reason: str

    operation: str = "rename_service"


@dataclass(frozen=True)
class AddDependency:
    from_service: str
    to_service: str
    reason: str

    operation: str = "add_dependency"


@dataclass(frozen=True)
class RemoveInvalidDependency:
    from_service: str
    to_service: str
    reason: str

    operation: str = "remove_invalid_dependency"


@dataclass(frozen=True)
class ReassignResponsibility:
    service: str
    responsibility: str
    from_service: str | None
    reason: str

    operation: str = "reassign_responsibility"


Operation = Union[
    MoveClass, SplitService, MergeServices, RenameService,
    AddDependency, RemoveInvalidDependency, ReassignResponsibility,
]


def parse_operation(raw: dict) -> Operation:
    """Convert a dict from ``refinement_patch.json`` into a typed op."""
    if not isinstance(raw, dict) or "operation" not in raw:
        raise ValueError(f"Operation dict missing 'operation' key: {raw}")
    op_type = raw["operation"]
    reason = str(raw.get("reason") or "")
    if op_type == "move_class":
        return MoveClass(
            class_=str(raw["class"]),
            from_service=str(raw["from_service"]),
            to_service=str(raw["to_service"]),
            reason=reason,
        )
    if op_type == "split_service":
        split = []
        for part in raw.get("split_into") or []:
            split.append((
                str(part.get("name") or "NewService"),
                tuple(str(c) for c in (part.get("classes") or [])),
                tuple(str(r) for r in (part.get("responsibilities") or [])),
            ))
        return SplitService(service=str(raw["service"]),
                            split_into=tuple(split),
                            reason=reason)
    if op_type == "merge_services":
        return MergeServices(
            source_services=tuple(str(s) for s in raw.get("source_services") or []),
            target_service=str(raw["target_service"]),
            reason=reason,
        )
    if op_type == "rename_service":
        return RenameService(
            from_name=str(raw["from_name"]),
            to_name=str(raw["to_name"]),
            reason=reason,
        )
    if op_type == "add_dependency":
        return AddDependency(
            from_service=str(raw["from_service"]),
            to_service=str(raw["to_service"]),
            reason=reason,
        )
    if op_type == "remove_invalid_dependency":
        return RemoveInvalidDependency(
            from_service=str(raw["from_service"]),
            to_service=str(raw["to_service"]),
            reason=reason,
        )
    if op_type == "reassign_responsibility":
        return ReassignResponsibility(
            service=str(raw["service"]),
            responsibility=str(raw["responsibility"]),
            from_service=(str(raw["from_service"]) if raw.get("from_service") else None),
            reason=reason,
        )
    raise ValueError(f"Unknown operation type {op_type!r}")
