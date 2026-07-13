"""Stable ID minting for evidence and domain artifacts.

IDs use fixed prefixes so downstream agents can recognise the entity type from
the ID alone. The minter is per-run and per-prefix; it generates monotonically
increasing zero-padded suffixes so IDs sort lexically in the same order they
were minted.

Examples
--------
>>> minter = IdMinter()
>>> minter.next("component")
'C001'
>>> minter.next("api")
'API_001'
>>> minter.next("component")
'C002'
"""
from __future__ import annotations

from typing import Final


ID_PREFIXES: Final[dict[str, str]] = {
    "component":  "C",
    "api":        "API_",
    "technology": "T_",
    "scenario":   "S_",
    "class_node": "K_",
    "edge":       "E_",
    "capability": "BC",
    "candidate":  "CAND_",
}


class IdMinter:
    """Generate stable, zero-padded IDs per entity type within a single run."""

    def __init__(self, width: int = 3) -> None:
        if width < 1:
            raise ValueError(f"width must be >= 1, got {width}")
        self._width = width
        self._counters: dict[str, int] = {k: 0 for k in ID_PREFIXES}

    def next(self, kind: str) -> str:
        """Mint and return the next ID for ``kind``."""
        try:
            prefix = ID_PREFIXES[kind]
        except KeyError as exc:
            raise KeyError(
                f"Unknown id kind {kind!r}; known kinds: {sorted(ID_PREFIXES)}"
            ) from exc
        self._counters[kind] += 1
        suffix = str(self._counters[kind]).zfill(self._width)
        return f"{prefix}{suffix}"

    def snapshot(self) -> dict[str, int]:
        """Return a copy of current counters; useful for debugging."""
        return dict(self._counters)
