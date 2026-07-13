"""Apply a sequence of :class:`Operation` to a candidate decomposition.

Patching is deterministic and idempotent per operation: invalid moves are
skipped with a warning rather than raising, so a partially-broken refinement
patch never blocks the pipeline. The applier returns the new candidate dict
plus a list of skipped-operation messages for the audit trail.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field

from agentic_decomposer.refinement.operations import (
    AddDependency,
    MergeServices,
    MoveClass,
    Operation,
    ReassignResponsibility,
    RemoveInvalidDependency,
    RenameService,
    SplitService,
)


@dataclass
class PatchOutcome:
    """Result of applying a refinement patch."""

    candidate: dict
    skipped: list[str] = field(default_factory=list)
    applied: list[str] = field(default_factory=list)


def apply_patch(candidate: dict, operations: list[Operation]) -> PatchOutcome:
    """Return a deep copy of *candidate* with *operations* applied in order."""
    new_candidate = copy.deepcopy(candidate)
    services = new_candidate.setdefault("services", [])
    outcome = PatchOutcome(candidate=new_candidate)

    for op in operations:
        try:
            handler = _DISPATCH[op.operation]
        except KeyError:
            outcome.skipped.append(f"unknown_operation:{op.operation}")
            continue
        try:
            note = handler(services, op)
        except _SkipOperation as exc:
            outcome.skipped.append(f"{op.operation}:{exc}")
            continue
        outcome.applied.append(f"{op.operation}:{note}")

    new_candidate["services"] = services
    return outcome


# ----------------------------------------------------------------------
class _SkipOperation(RuntimeError):
    """Raised by an op handler to signal "skip silently with this message"."""


def _find_service(services: list[dict], name: str) -> dict:
    for svc in services:
        if svc.get("name") == name:
            return svc
    raise _SkipOperation(f"service_not_found:{name}")


def _class_id_set(svc: dict) -> set[str]:
    return {(c["id"] if isinstance(c, dict) else str(c)) for c in svc.get("classes", [])}


# ----------------------------------------------------------------------
def _handle_move_class(services: list[dict], op: MoveClass) -> str:
    src = _find_service(services, op.from_service)
    dst = _find_service(services, op.to_service)
    if op.class_ not in _class_id_set(src):
        raise _SkipOperation(f"class_not_in_source:{op.class_}@{op.from_service}")
    if op.class_ in _class_id_set(dst):
        # Already in destination — remove from source for hygiene.
        src["classes"] = [c for c in src["classes"]
                          if (c["id"] if isinstance(c, dict) else str(c)) != op.class_]
        return f"deduped:{op.class_}->{op.to_service}"
    src["classes"] = [c for c in src["classes"]
                      if (c["id"] if isinstance(c, dict) else str(c)) != op.class_]
    dst.setdefault("classes", []).append({"id": op.class_})
    return f"{op.class_}:{op.from_service}->{op.to_service}"


def _handle_split_service(services: list[dict], op: SplitService) -> str:
    src = _find_service(services, op.service)
    src_classes = _class_id_set(src)
    if not op.split_into:
        raise _SkipOperation("split_into_empty")

    # Validate every target class exists in the source service.
    new_services: list[dict] = []
    consumed: set[str] = set()
    for name, classes, responsibilities in op.split_into:
        usable = [c for c in classes if c in src_classes and c not in consumed]
        if not usable:
            continue
        new_services.append({
            "name": name,
            "classes": [{"id": c} for c in usable],
            "responsibilities": list(responsibilities) or [
                f"Split out from {op.service}.",
            ],
            "dependencies": [],
            "evidence_refs": list(src.get("evidence_refs") or []),
        })
        consumed.update(usable)

    if not new_services:
        raise _SkipOperation(f"no_valid_classes_in_split:{op.service}")

    # Anything left in the original stays in src; if everything was consumed,
    # drop the (now empty) src.
    src["classes"] = [c for c in src["classes"]
                      if (c["id"] if isinstance(c, dict) else str(c)) not in consumed]
    idx = services.index(src)
    if not src["classes"]:
        services.pop(idx)
        services[idx:idx] = new_services
    else:
        services[idx + 1:idx + 1] = new_services
    return f"{op.service}->{[s['name'] for s in new_services]}"


def _handle_merge_services(services: list[dict], op: MergeServices) -> str:
    target = _find_service(services, op.target_service)
    target_classes = _class_id_set(target)
    merged_names = []
    for name in op.source_services:
        if name == op.target_service:
            continue
        try:
            svc = _find_service(services, name)
        except _SkipOperation:
            continue
        for c in svc.get("classes", []):
            cid = c["id"] if isinstance(c, dict) else str(c)
            if cid not in target_classes:
                target.setdefault("classes", []).append({"id": cid})
                target_classes.add(cid)
        for r in svc.get("responsibilities", []):
            if r not in target.get("responsibilities", []):
                target.setdefault("responsibilities", []).append(r)
        for ref in svc.get("evidence_refs", []):
            if ref not in target.get("evidence_refs", []):
                target.setdefault("evidence_refs", []).append(ref)
        services.remove(svc)
        merged_names.append(name)
    if not merged_names:
        raise _SkipOperation("no_sources_merged")
    return f"{merged_names}->{op.target_service}"


def _handle_rename_service(services: list[dict], op: RenameService) -> str:
    if op.from_name == op.to_name:
        raise _SkipOperation("noop_rename")
    src = _find_service(services, op.from_name)
    if any(s.get("name") == op.to_name for s in services):
        raise _SkipOperation(f"target_name_conflict:{op.to_name}")
    src["name"] = op.to_name
    # rewrite dependency references pointing at the old name
    for svc in services:
        svc["dependencies"] = [op.to_name if d == op.from_name else d
                               for d in svc.get("dependencies", [])]
    return f"{op.from_name}->{op.to_name}"


def _handle_add_dependency(services: list[dict], op: AddDependency) -> str:
    if op.from_service == op.to_service:
        raise _SkipOperation("self_dependency")
    src = _find_service(services, op.from_service)
    _ = _find_service(services, op.to_service)  # validate target exists
    deps = src.setdefault("dependencies", [])
    if op.to_service in deps:
        raise _SkipOperation("already_present")
    deps.append(op.to_service)
    return f"{op.from_service}->{op.to_service}"


def _handle_remove_invalid_dependency(services: list[dict], op: RemoveInvalidDependency) -> str:
    src = _find_service(services, op.from_service)
    deps = src.get("dependencies", [])
    if op.to_service not in deps:
        raise _SkipOperation("not_present")
    src["dependencies"] = [d for d in deps if d != op.to_service]
    return f"{op.from_service}!->{op.to_service}"


def _handle_reassign_responsibility(services: list[dict], op: ReassignResponsibility) -> str:
    if op.from_service:
        try:
            src = _find_service(services, op.from_service)
            src["responsibilities"] = [
                r for r in src.get("responsibilities", []) if r != op.responsibility
            ]
        except _SkipOperation:
            pass
    dst = _find_service(services, op.service)
    if op.responsibility not in dst.get("responsibilities", []):
        dst.setdefault("responsibilities", []).append(op.responsibility)
    return f"{op.responsibility}->{op.service}"


_DISPATCH = {
    "move_class":                _handle_move_class,
    "split_service":             _handle_split_service,
    "merge_services":            _handle_merge_services,
    "rename_service":            _handle_rename_service,
    "add_dependency":            _handle_add_dependency,
    "remove_invalid_dependency": _handle_remove_invalid_dependency,
    "reassign_responsibility":   _handle_reassign_responsibility,
}
