"""Structured logging for the framework.

Each run gets its own log subfolder under ``runs/<run_id>/logs/`` containing:

- ``controller.log``  — overall orchestration timeline
- ``agent_<name>.log`` — one file per agent invocation
- ``llm_calls.jsonl`` — every LLM request/response with token counts

The console handler uses ``rich`` for readable colour output; file handlers
write plain text so log files diff cleanly across runs.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Iterator

from rich.logging import RichHandler


_CONFIGURED = False
_DEFAULT_FORMAT = "%(asctime)s | %(name)-32s | %(levelname)-7s | %(message)s"
_DEFAULT_DATEFMT = "%Y-%m-%dT%H:%M:%S"


def configure_root(level: int = logging.INFO) -> None:
    """Install the rich console handler on the root logger (idempotent)."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    root = logging.getLogger()
    root.setLevel(level)
    handler = RichHandler(
        rich_tracebacks=True,
        markup=False,
        show_path=False,
        show_time=True,
        log_time_format="[%X]",
    )
    handler.setLevel(level)
    root.addHandler(handler)
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a logger, ensuring the root handler is configured."""
    configure_root()
    return logging.getLogger(name)


def attach_file_handler(logger: logging.Logger, path: Path, level: int = logging.DEBUG) -> logging.Handler:
    """Add a plain-text file handler to *logger* writing to *path*.

    Returns the handler so callers can detach it cleanly when the agent
    finishes (use ``detach_file_handler`` for symmetry).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(_DEFAULT_FORMAT, datefmt=_DEFAULT_DATEFMT))
    logger.addHandler(handler)
    return handler


def detach_file_handler(logger: logging.Logger, handler: logging.Handler) -> None:
    """Remove *handler* from *logger* and close it. Safe to call twice."""
    try:
        logger.removeHandler(handler)
    finally:
        try:
            handler.close()
        except Exception:
            pass


def iter_all_loggers() -> Iterator[logging.Logger]:
    """Yield every logger created via ``get_logger`` for diagnostics."""
    manager = logging.getLogger().manager
    for name in list(manager.loggerDict.keys()):
        yield logging.getLogger(name)
