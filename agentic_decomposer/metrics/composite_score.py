"""Composite ranking score used internally by the Process Controller.

This score is **not** published. It is used only to pick the "best" candidate
when several pass the quality gate with similar Wang metrics. The objective
weights are read from :class:`agentic_decomposer.config.RunConfig.objectives`.
"""
from __future__ import annotations

from agentic_decomposer.config import Objectives
from agentic_decomposer.metrics.quality_gate import QualityGateResult


# Mapping from objective key → list of (metric_key, weight_inside_objective).
# Each Wang metric is normalised to [0,1] before weighting (we divide by 100
# for percentage-style metrics; num_services is not used in the composite).
_METRIC_TO_OBJECTIVE: dict[str, list[tuple[str, float]]] = {
    "structural_modularity": [("CMod", 1.0)],
    "domain_alignment":      [("BCP", 0.5), ("DI", 0.5)],
    "cyclic_independence":   [("CiD", 1.0)],
    "migration_feasibility": [("MoJoFM", 0.5), ("TC", 0.25), ("LC", 0.25)],
}


def _normalise(metric_key: str, value: float | None) -> float | None:
    if value is None:
        return None
    # All metrics except num_services are percentages on [0,100].
    if metric_key == "num_services":
        return None
    return max(0.0, min(value / 100.0, 1.0))


def compute_composite_score(
    metrics: dict[str, float | None],
    objectives: Objectives,
    quality_gate: QualityGateResult | None = None,
) -> float | None:
    """Return a scalar in roughly [0, 1] (higher is better).

    Returns ``None`` when no metric values are available (e.g. metric engine
    unreachable). When ``quality_gate`` is supplied and the gate fails, the
    score is multiplied by 0.5 so failing candidates rank below passing ones.
    """
    weight_total = 0.0
    score = 0.0
    contributed = False

    obj_weights = {
        "structural_modularity": objectives.structural_modularity,
        "domain_alignment":      objectives.domain_alignment,
        "cyclic_independence":   objectives.cyclic_independence,
        "migration_feasibility": objectives.migration_feasibility,
    }

    for objective, weight in obj_weights.items():
        sub_total = 0.0
        sub_weight_used = 0.0
        for metric_key, inner_weight in _METRIC_TO_OBJECTIVE[objective]:
            normalised = _normalise(metric_key, metrics.get(metric_key))
            if normalised is None:
                continue
            sub_total      += inner_weight * normalised
            sub_weight_used += inner_weight
        if sub_weight_used > 0:
            score        += weight * (sub_total / sub_weight_used)
            weight_total += weight
            contributed = True

    if not contributed or weight_total == 0:
        return None

    base = score / weight_total
    if quality_gate is not None and not quality_gate.passes:
        base *= 0.5
    return round(base, 4)
