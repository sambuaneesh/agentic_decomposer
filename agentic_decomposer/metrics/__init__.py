"""Metric and quality-gate utilities.

* :mod:`agentic_decomposer.metrics.engine` — subprocess wrapper that invokes
  ``../src/metrics/scripts/evaluate_decomposition.py`` and parses its JSON
  output into the shape used by ``evaluation_report.json``.
* :mod:`agentic_decomposer.metrics.quality_gate` — local, pure-Python checks
  that do not require Java / the metric engine.
* :mod:`agentic_decomposer.metrics.composite_score` — controller-internal
  ranking score (not published).
"""

from agentic_decomposer.metrics.engine import (
    METRIC_KEYS,
    EngineResult,
    extract_metrics,
    run_metric_engine,
)
from agentic_decomposer.metrics.quality_gate import (
    QualityGateResult,
    run_quality_gate,
)
from agentic_decomposer.metrics.composite_score import compute_composite_score

__all__ = [
    "METRIC_KEYS",
    "EngineResult",
    "extract_metrics",
    "run_metric_engine",
    "QualityGateResult",
    "run_quality_gate",
    "compute_composite_score",
]
