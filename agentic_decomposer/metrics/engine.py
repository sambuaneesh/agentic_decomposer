"""Subprocess wrapper for ``../src/metrics/scripts/evaluate_decomposition.py``.

Mirrors the conventions of
:mod:`scripts/calculate_metrics_paper_comparison.py` so the framework
produces numbers comparable to every existing baseline in
``results/`` and to the previous paper.

Behaviour when the metric engine is not available
-------------------------------------------------

If the engine path does not exist (e.g. running on a fresh Windows checkout
without a Linux mirror), :func:`run_metric_engine` returns an
:class:`EngineResult` with ``available=False`` and ``metrics`` populated with
``None`` for every key. The caller is expected to flag this as a non-fatal
"emit-only" run and continue.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from agentic_decomposer.paths import METRICS_DIR, METRICS_SCRIPT, REPO_TO_APP


METRIC_KEYS: Final[tuple[str, ...]] = (
    "MoJoFM", "CiD", "CMod", "BCP", "DI", "TC", "LC", "DTP", "num_services",
)


@dataclass
class EngineResult:
    """Outcome of one metric-engine invocation."""

    available: bool
    metrics: dict[str, float | None]
    engine_output_path: str | None = None
    raw_json: dict | None = None
    stderr_tail: str | None = None
    returncode: int | None = None
    warnings: list[str] = field(default_factory=list)


# ----------------------------------------------------------------------
# Environment / Java
# ----------------------------------------------------------------------

# Same convention as calculate_metrics_paper_comparison.py: prepend any Java
# JRE folder we know about. Users can override / extend via env var.
_DEFAULT_JAVA_HOMES: tuple[str, ...] = (
    "/home/stealthspectre/.local/jre/temurin-17-jre/bin",
    "/home/stealthspectre/.local/share/mise/installs/java/25.0.2/bin",
)


def _candidate_java_dirs() -> list[str]:
    env_override = os.environ.get("AGENTIC_DECOMPOSER_JAVA_HOMES")
    if env_override:
        sep = ";" if os.name == "nt" else ":"
        return [d.strip() for d in env_override.split(sep) if d.strip()]
    return list(_DEFAULT_JAVA_HOMES)


def _build_env() -> dict[str, str]:
    """Return the environment used to run the metric engine."""
    env = os.environ.copy()
    java_exe = "java.exe" if os.name == "nt" else "java"
    for jdir in _candidate_java_dirs():
        java_path = Path(jdir) / java_exe
        if java_path.is_file():
            path_sep = ";" if os.name == "nt" else ":"
            env["PATH"] = f"{jdir}{path_sep}{env.get('PATH', '')}"
            env.setdefault("JAVA_HOME", str(Path(jdir).parent))
            break
    return env


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------

def run_metric_engine(
    *,
    decomposition_path: Path,
    system: str,
    tool_name: str,
    mojo_timeout: int = 60,
) -> EngineResult:
    """Invoke ``evaluate_decomposition.py`` and parse its output.

    Parameters
    ----------
    decomposition_path:
        Path to a decomposition.json that follows the standard
        ``{"tool":{"decomposition":{...}}}`` shape.
    system:
        One of the four supported systems (codebase folder name).
    tool_name:
        Free-form identifier embedded in the engine's output filename.
        Allowed characters: letters, digits, ``.``, ``-``, ``_``.
    mojo_timeout:
        Timeout in seconds for the engine's internal MoJo Java subprocess.
    """
    if system not in REPO_TO_APP:
        raise ValueError(f"Unknown system {system!r}; expected one of {sorted(REPO_TO_APP)}")
    if not METRICS_SCRIPT.is_file():
        return EngineResult(
            available=False,
            metrics={k: None for k in METRIC_KEYS},
            warnings=[
                f"Metric engine not found at {METRICS_SCRIPT}. "
                "Emit-only mode: decomposition.json written but metrics are null."
            ],
        )
    if not decomposition_path.is_file():
        raise FileNotFoundError(f"decomposition.json not found at {decomposition_path}")

    safe_tool_name = re.sub(r"[^A-Za-z0-9_.\-]+", "-", tool_name)[:60] or "agentic"
    cmd = [
        sys.executable, str(METRICS_SCRIPT),
        "--application",        REPO_TO_APP[system],
        "--granularity",        "class",
        "--decomposition-file", str(decomposition_path),
        "--tool-name",          safe_tool_name,
        "--output-format",      "json",
        "--input-format",       "standard",
        "--mojo-timeout",       str(int(mojo_timeout)),
    ]
    env = _build_env()

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(METRICS_DIR),
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
    except FileNotFoundError as exc:
        return EngineResult(
            available=False,
            metrics={k: None for k in METRIC_KEYS},
            warnings=[
                f"Could not launch metric engine: {exc}. Is Python on PATH?"
            ],
            returncode=None,
        )

    stderr_tail = (proc.stderr or "")[-1500:]
    if proc.returncode != 0:
        return EngineResult(
            available=True,
            metrics={k: None for k in METRIC_KEYS},
            stderr_tail=stderr_tail,
            returncode=proc.returncode,
            warnings=[
                f"Metric engine exited with code {proc.returncode}. "
                "See stderr_tail for details."
            ],
        )

    stdout = (proc.stdout or "").strip()
    match = re.search(r"JSON written to (output/\S+)", stdout)
    output_path: Path | None = None
    if match:
        output_path = (METRICS_DIR / match.group(1)).resolve()

    raw_json: dict | None = None
    if output_path and output_path.is_file():
        try:
            raw_json = json.loads(output_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return EngineResult(
                available=True,
                metrics={k: None for k in METRIC_KEYS},
                engine_output_path=str(output_path),
                stderr_tail=f"{stderr_tail}\nJSON parse error: {exc}",
                returncode=proc.returncode,
                warnings=[f"Engine output file is not valid JSON: {output_path}"],
            )
    else:
        # Some versions of the engine print the JSON to stdout directly.
        try:
            raw_json = json.loads(stdout)
        except json.JSONDecodeError:
            return EngineResult(
                available=True,
                metrics={k: None for k in METRIC_KEYS},
                stderr_tail=stderr_tail,
                returncode=proc.returncode,
                warnings=[
                    "Could not find engine output JSON. Stdout did not match "
                    "'JSON written to output/...' and was not JSON itself."
                ],
            )

    metrics = extract_metrics(raw_json)
    return EngineResult(
        available=True,
        metrics=metrics,
        engine_output_path=str(output_path) if output_path else None,
        raw_json=raw_json,
        returncode=proc.returncode,
    )


# ----------------------------------------------------------------------
# Engine output → metric dict
# ----------------------------------------------------------------------

def _first_class_level_row(rows: list[dict] | None) -> dict:
    for row in rows or []:
        if row.get("Granularity") == "class_level":
            return row
    return rows[0] if rows else {}


def _round(value) -> float | None:
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if f == -1.0:  # engine sentinel for "not applicable"
        return None
    return round(f, 2)


def extract_metrics(engine_output: dict) -> dict[str, float | None]:
    """Pull the nine Wang metric values out of an engine JSON document.

    Mapping mirrors
    :func:`scripts.calculate_metrics_paper_comparison.extract_metrics`.
    """
    if not engine_output:
        return {k: None for k in METRIC_KEYS}
    turbomq = _first_class_level_row(engine_output.get("turbomq"))
    mojofm  = _first_class_level_row(engine_output.get("mojofm"))
    entropy = _first_class_level_row(engine_output.get("entropy"))
    stats   = _first_class_level_row(engine_output.get("statistics"))

    cid: float | None = None
    if "CDP" in turbomq and turbomq["CDP"] is not None:
        cid = _round(100 - float(turbomq["CDP"]))
    return {
        "MoJoFM":       _round(mojofm.get("Mojo")),
        "CiD":          cid,
        "CMod":         _round(turbomq.get("Static Structural")),
        "BCP":          _round(entropy.get("Sarah BCP")),
        "DI":           _round(entropy.get("Use Case Entropy")),
        "TC":           _round(turbomq.get("TurboMQ_contributors")),
        "LC":           _round(turbomq.get("TurboMQ_commits")),
        "DTP":          _round(entropy.get("Database Entropy")),
        "num_services": _round(stats.get("Actual Partition Count")),
    }
