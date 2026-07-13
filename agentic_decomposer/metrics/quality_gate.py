"""Local structural quality gate.

Runs pure-Python checks against a single candidate decomposition. None of
these checks require the external metric engine. They cover the structural
constraints documented in ``docs/schemas.md``:

- every class is assigned
- no class is assigned to more than one service
- no service is empty
- service names are unique
- every class name is a "simple" name (no dots)
- no self-dependency
- every dependency target exists in the candidate
- every service has at least one responsibility or a non-empty rationale
- every service cites at least one evidence/domain reference
- cited evidence/domain references exist in the current artifacts
- service count obeys configured min/max bounds
- count of cyclic service dependencies (warning, not blocking)
- orphan-class count (classes in evidence_pack that the candidate forgot)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import networkx as nx


_SIMPLE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*$")


@dataclass
class QualityGateResult:
    """Outcome of one quality-gate pass over a candidate."""

    all_classes_assigned: bool
    no_duplicate_classes: bool
    no_empty_services: bool
    unique_service_names: bool
    valid_class_names_only: bool
    no_self_dependencies: bool
    all_dependency_targets_exist: bool
    all_services_have_rationale_or_responsibility: bool
    all_services_have_evidence_refs: bool
    all_evidence_refs_valid: bool
    service_count_within_bounds: bool
    cyclic_dependency_count: int
    orphan_class_count: int
    service_count: int = 0
    duplicate_service_names: list[str] = field(default_factory=list)
    duplicate_class_assignments: list[dict] = field(default_factory=list)
    missing_classes: list[str] = field(default_factory=list)
    invalid_class_names: list[str] = field(default_factory=list)
    services_missing_evidence_refs: list[str] = field(default_factory=list)
    invalid_evidence_refs: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "all_classes_assigned":            self.all_classes_assigned,
            "no_duplicate_classes":            self.no_duplicate_classes,
            "no_empty_services":               self.no_empty_services,
            "unique_service_names":            self.unique_service_names,
            "valid_class_names_only":          self.valid_class_names_only,
            "no_self_dependencies":            self.no_self_dependencies,
            "all_dependency_targets_exist":    self.all_dependency_targets_exist,
            "all_services_have_rationale_or_responsibility":
                self.all_services_have_rationale_or_responsibility,
            "all_services_have_evidence_refs": self.all_services_have_evidence_refs,
            "all_evidence_refs_valid":        self.all_evidence_refs_valid,
            "service_count_within_bounds":     self.service_count_within_bounds,
            "cyclic_dependency_count":         self.cyclic_dependency_count,
            "orphan_class_count":              self.orphan_class_count,
            "service_count":                   self.service_count,
            "duplicate_service_names":         list(self.duplicate_service_names),
            "duplicate_class_assignments":     list(self.duplicate_class_assignments),
            "missing_classes":                 list(self.missing_classes),
            "invalid_class_names":             list(self.invalid_class_names),
            "services_missing_evidence_refs":  list(self.services_missing_evidence_refs),
            "invalid_evidence_refs":           list(self.invalid_evidence_refs),
        }

    @property
    def passes(self) -> bool:
        """True when every blocking check passes (cycles + orphans are warnings only)."""
        return all([
            self.all_classes_assigned,
            self.no_duplicate_classes,
            self.no_empty_services,
            self.unique_service_names,
            self.valid_class_names_only,
            self.no_self_dependencies,
            self.all_dependency_targets_exist,
            self.all_services_have_rationale_or_responsibility,
            self.all_services_have_evidence_refs,
            self.all_evidence_refs_valid,
            self.service_count_within_bounds,
        ])


# ----------------------------------------------------------------------
def run_quality_gate(
    candidate: dict,
    evidence_pack: dict | None,
    *,
    domain_model: dict | None = None,
    allow_unassigned_classes: bool = False,
    min_services: int | None = None,
    max_services: int | None = None,
) -> QualityGateResult:
    """Evaluate a candidate against the framework's structural rules."""
    services = candidate.get("services", [])
    known_classes = {c["name"] for c in (evidence_pack or {}).get("classes", [])}

    # ── Collect per-class assignments ─────────────────────────────────
    class_to_services: dict[str, list[str]] = {}
    for svc in services:
        name = svc.get("name", "")
        for cls in svc.get("classes", []):
            cid = cls["id"] if isinstance(cls, dict) else str(cls)
            class_to_services.setdefault(cid, []).append(name)

    duplicates = [
        {"class": cls, "services": svcs}
        for cls, svcs in class_to_services.items()
        if len(svcs) > 1
    ]

    invalid_names = [
        cls for cls in class_to_services.keys()
        if not _SIMPLE_NAME_RE.match(cls or "")
    ]

    empty_services = [s for s in services if not s.get("classes")]
    service_name_counts: dict[str, int] = {}
    for svc in services:
        service_name = svc.get("name", "") or "<unnamed>"
        service_name_counts[service_name] = service_name_counts.get(service_name, 0) + 1
    duplicate_service_names = sorted(
        name for name, count in service_name_counts.items() if count > 1
    )

    # ── Class assignment coverage vs evidence pack ────────────────────
    assigned = set(class_to_services.keys())
    missing = sorted(known_classes - assigned) if known_classes else []
    extra = sorted(assigned - known_classes) if known_classes else []
    all_assigned = (not missing) or allow_unassigned_classes

    # ── Service-dependency hygiene ────────────────────────────────────
    service_names = {s.get("name", "") for s in services}
    self_dep = False
    bad_targets = False
    for svc in services:
        name = svc.get("name", "")
        for dep in svc.get("dependencies", []):
            if dep == name:
                self_dep = True
            if dep not in service_names:
                bad_targets = True

    # ── Cycle count ───────────────────────────────────────────────────
    graph = nx.DiGraph()
    graph.add_nodes_from(service_names)
    for svc in services:
        name = svc.get("name", "")
        for dep in svc.get("dependencies", []):
            if dep in service_names and dep != name:
                graph.add_edge(name, dep)
    try:
        cycles = list(nx.simple_cycles(graph))
    except nx.NetworkXNoCycle:
        cycles = []
    cycle_count = len(cycles)

    # ── Responsibility coverage ───────────────────────────────────────
    rationale = (candidate.get("rationale") or "").strip()
    services_have_rationale = all(
        (svc.get("responsibilities") and any(r.strip() for r in svc["responsibilities"]))
        or bool(rationale)
        for svc in services
    )

    missing_refs = [
        svc.get("name", "") or "<unnamed>"
        for svc in services
        if not svc.get("evidence_refs")
    ]

    known_refs = _known_reference_ids(evidence_pack, domain_model)
    invalid_refs: list[dict] = []
    if known_refs:
        for svc in services:
            service_name = svc.get("name", "") or "<unnamed>"
            for ref in svc.get("evidence_refs") or []:
                if ref not in known_refs:
                    invalid_refs.append({"service": service_name, "ref": str(ref)})

    service_count = len(services)
    lower_ok = True if min_services is None else service_count >= min_services
    upper_ok = True if max_services is None else service_count <= max_services

    return QualityGateResult(
        all_classes_assigned=all_assigned,
        no_duplicate_classes=not duplicates,
        no_empty_services=not empty_services,
        unique_service_names=not duplicate_service_names,
        valid_class_names_only=not invalid_names,
        no_self_dependencies=not self_dep,
        all_dependency_targets_exist=not bad_targets,
        all_services_have_rationale_or_responsibility=services_have_rationale,
        all_services_have_evidence_refs=not missing_refs,
        all_evidence_refs_valid=not invalid_refs,
        service_count_within_bounds=lower_ok and upper_ok,
        cyclic_dependency_count=cycle_count,
        orphan_class_count=len(extra),
        service_count=service_count,
        duplicate_service_names=duplicate_service_names,
        duplicate_class_assignments=duplicates,
        missing_classes=missing,
        invalid_class_names=invalid_names,
        services_missing_evidence_refs=missing_refs,
        invalid_evidence_refs=invalid_refs,
    )


def _known_reference_ids(evidence_pack: dict | None, domain_model: dict | None) -> set[str]:
    refs: set[str] = set()
    evidence_pack = evidence_pack or {}
    for key in ("classes", "components", "api_endpoints", "dependency_edges", "dynamic_interactions"):
        for item in evidence_pack.get(key, []) or []:
            if isinstance(item, dict) and item.get("id"):
                refs.add(str(item["id"]))
    for cap in (domain_model or {}).get("business_capabilities", []) or []:
        if isinstance(cap, dict) and cap.get("id"):
            refs.add(str(cap["id"]))
    return refs
