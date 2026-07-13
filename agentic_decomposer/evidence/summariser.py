"""Seven summarisation strategies for Phase-1 source ingestion.

Strategies match those used in the previous paper:

| Strategy        | What it does                                                       |
| --------------- | ------------------------------------------------------------------ |
| ``30k_concat``  | Concatenate Java sources, truncate to ~30k tokens (no LLM call).   |
| ``50k_concat``  | Same, ~50k tokens.                                                 |
| ``80k_concat``  | Same, ~80k tokens.                                                 |
| ``30k_aggregate`` | Chunk to ~30k token windows, summarise each via LLM, join.       |
| ``50k_aggregate`` | Same, ~50k tokens per window.                                    |
| ``80k_aggregate`` | Same, ~80k tokens per window.                                    |
| ``hierarchical``  | Two-level summarisation: per-file summary → cluster-level rollup.|

The ``concat`` strategies do not call the LLM at all and run on any machine
without API keys. The ``aggregate`` / ``hierarchical`` strategies require a
configured :class:`~agentic_decomposer.llm.client.LLMClient`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from agentic_decomposer.evidence.source_walker import SourceFile
from agentic_decomposer.llm.client import LLMClient


# Approximate tokens per character. Real tokenisation varies by model; this
# heuristic is calibrated to match tiktoken on Java-heavy text within ±15%.
_CHARS_PER_TOKEN = 4

# Token budgets for the three families.
_BUDGETS: dict[str, int] = {
    "30k": 30_000,
    "50k": 50_000,
    "80k": 80_000,
}


def _budget(strategy: str) -> int:
    for key, value in _BUDGETS.items():
        if strategy.startswith(key):
            return value
    return 80_000  # hierarchical defaults to the largest single-pass budget


@dataclass
class SummariserConfig:
    """Per-run summarisation configuration."""

    strategy: str
    llm: LLMClient | None = None  # required for *_aggregate and hierarchical

    @property
    def needs_llm(self) -> bool:
        return self.strategy.endswith("_aggregate") or self.strategy == "hierarchical"


# ----------------------------------------------------------------------
# Strategy implementations
# ----------------------------------------------------------------------

def _concat_files(files: list[SourceFile], budget_tokens: int) -> str:
    """Concatenate file contents, truncating to fit ``budget_tokens`` tokens."""
    budget_chars = budget_tokens * _CHARS_PER_TOKEN
    chunks: list[str] = []
    total = 0
    for sf in files:
        header = f"\n\n// ─── {sf.path.as_posix()} ───\n"
        body = sf.text
        block = header + body
        if total + len(block) > budget_chars:
            # take whatever remains, then stop
            remaining = budget_chars - total
            if remaining > len(header):
                chunks.append(header)
                chunks.append(body[: remaining - len(header)])
            break
        chunks.append(block)
        total += len(block)
    return "".join(chunks).lstrip()


def _chunk_for_aggregation(files: list[SourceFile], chunk_tokens: int) -> list[str]:
    """Split files into chunks of approximately ``chunk_tokens`` tokens each."""
    chunk_chars = chunk_tokens * _CHARS_PER_TOKEN
    chunks: list[str] = []
    current: list[str] = []
    current_size = 0
    for sf in files:
        block = f"\n\n// ─── {sf.path.as_posix()} ───\n{sf.text}"
        if current and current_size + len(block) > chunk_chars:
            chunks.append("".join(current).lstrip())
            current, current_size = [], 0
        current.append(block)
        current_size += len(block)
    if current:
        chunks.append("".join(current).lstrip())
    return chunks


_AGGREGATE_SYSTEM_PROMPT = (
    "You are summarising part of a monolithic Java codebase to help a "
    "downstream architectural-decomposition agent understand structure and "
    "responsibilities. Focus on: package layout, key classes and their roles, "
    "important APIs, persistence/database touchpoints, and noteworthy "
    "third-party libraries. Do not invent details that are not present in "
    "the provided source."
)


def _summarise_chunks(chunks: list[str], llm: LLMClient) -> list[str]:
    """Call the LLM once per chunk and return the per-chunk summaries."""
    summaries: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        user = (
            f"Summarise CHUNK {i}/{len(chunks)} of the codebase below. "
            "Limit your output to roughly 600 words. Use concise bullet "
            "points where possible.\n\n```java\n"
            f"{chunk}\n```"
        )
        result = llm.complete(system=_AGGREGATE_SYSTEM_PROMPT, user=user)
        summaries.append(result.text.strip())
    return summaries


def _aggregate(files: list[SourceFile], cfg: SummariserConfig) -> str:
    if cfg.llm is None:
        raise ValueError(f"Strategy {cfg.strategy!r} requires an LLM client.")
    budget = _budget(cfg.strategy)
    chunks = _chunk_for_aggregation(files, chunk_tokens=budget)
    summaries = _summarise_chunks(chunks, cfg.llm)
    return "\n\n".join(
        f"### Chunk {i + 1}\n{summary}" for i, summary in enumerate(summaries)
    )


_HIERARCHICAL_FILE_SYSTEM_PROMPT = (
    "You are summarising a single Java file as a one-paragraph blurb about "
    "the class(es) inside, their main responsibilities, and any notable "
    "collaborators. Be concise; do not exceed 120 words."
)

_HIERARCHICAL_ROLLUP_SYSTEM_PROMPT = (
    "You are merging per-file summaries of a Java codebase into one cohesive "
    "architectural overview. Preserve names of important classes, packages, "
    "and APIs. Aim for ~1500 words."
)


def _hierarchical(files: list[SourceFile], cfg: SummariserConfig) -> str:
    if cfg.llm is None:
        raise ValueError("Hierarchical strategy requires an LLM client.")
    per_file_summaries: list[str] = []
    for sf in files:
        user = (
            f"File path: {sf.path.as_posix()}\n"
            f"Package: {sf.package or '(default)'}\n\n"
            f"```java\n{sf.text}\n```"
        )
        result = cfg.llm.complete(
            system=_HIERARCHICAL_FILE_SYSTEM_PROMPT, user=user,
        )
        per_file_summaries.append(f"- `{sf.path.name}` ({sf.package}): {result.text.strip()}")

    rollup_input = "\n".join(per_file_summaries)
    rollup = cfg.llm.complete(
        system=_HIERARCHICAL_ROLLUP_SYSTEM_PROMPT,
        user=f"Per-file summaries follow. Produce the merged overview.\n\n{rollup_input}",
    )
    return rollup.text.strip()


_STRATEGIES: dict[str, Callable[[list[SourceFile], SummariserConfig], str]] = {
    "30k_concat": lambda files, cfg: _concat_files(files, _budget(cfg.strategy)),
    "50k_concat": lambda files, cfg: _concat_files(files, _budget(cfg.strategy)),
    "80k_concat": lambda files, cfg: _concat_files(files, _budget(cfg.strategy)),
    "30k_aggregate": _aggregate,
    "50k_aggregate": _aggregate,
    "80k_aggregate": _aggregate,
    "hierarchical":  _hierarchical,
}


# ----------------------------------------------------------------------
def summarise_codebase(files: list[SourceFile], cfg: SummariserConfig) -> str:
    """Produce a single repository-level summary string per *cfg.strategy*."""
    try:
        func = _STRATEGIES[cfg.strategy]
    except KeyError as exc:
        raise ValueError(f"Unknown summarisation strategy {cfg.strategy!r}") from exc
    return func(files, cfg)
