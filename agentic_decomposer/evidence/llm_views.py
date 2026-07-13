"""LLM-driven generation of architectural views A1..A5.

The LLM is asked, in a single call, to return a JSON object that the Evidence
Constructor can splice straight into ``evidence_pack.json``. The prompt
template lives in ``prompts/evidence_views.md`` so it can be edited without a
code change.

The response is parsed with :func:`agentic_decomposer.helpers.extract_json_object`
which tolerates code fences and surrounding prose.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agentic_decomposer.helpers import LLMOutputError, extract_json_object
from agentic_decomposer.llm.client import LLMClient
from agentic_decomposer.paths import PROMPTS_DIR


_PROMPT_FILE = PROMPTS_DIR / "evidence_views.md"


@dataclass
class LLMViews:
    """Bundle returned by :func:`generate_llm_views`."""

    component_diagram: str | None
    components: list[dict]
    api_endpoints: list[dict]
    technology_map: dict
    dynamic_interactions: list[dict]
    persistence_entities: list[dict]
    tokens_used: int


def _load_prompt() -> str:
    if not _PROMPT_FILE.is_file():
        raise FileNotFoundError(
            f"Evidence-views prompt not found at {_PROMPT_FILE}. "
            "Stage 3 of the MVP roadmap installs it."
        )
    return _PROMPT_FILE.read_text(encoding="utf-8")


def generate_llm_views(
    *,
    system: str,
    summary: str,
    known_classes: list[str],
    llm: LLMClient,
) -> LLMViews:
    """Ask the LLM to produce A1..A5 + persistence entities for *system*."""
    prompt_template = _load_prompt()
    user = (
        prompt_template
        .replace("<<SYSTEM>>", system)
        .replace("<<KNOWN_CLASSES>>", _format_class_list(known_classes))
        .replace("<<SOURCE_SUMMARY>>", summary or "(no summary provided)")
    )
    result = llm.complete(
        system="You produce strict JSON describing the architectural views of a "
               "monolithic Java codebase. Do not include prose outside JSON.",
        user=user,
    )
    try:
        payload = extract_json_object(result.text)
    except LLMOutputError as exc:
        raise LLMOutputError(
            f"Evidence Constructor (LLM mode) failed to parse views for {system}.",
            getattr(exc, "raw", result.text),
        ) from exc

    return LLMViews(
        component_diagram=payload.get("component_diagram"),
        components=_as_list(payload.get("components")),
        api_endpoints=_as_list(payload.get("api_endpoints")),
        technology_map=payload.get("technology_map") or {},
        dynamic_interactions=_as_list(payload.get("dynamic_interactions")),
        persistence_entities=_as_list(payload.get("persistence_entities")),
        tokens_used=result.total_tokens or 0,
    )


def _format_class_list(names: list[str]) -> str:
    if not names:
        return "(no class list available)"
    if len(names) <= 200:
        return "\n".join(f"- {name}" for name in names)
    head = "\n".join(f"- {name}" for name in names[:200])
    return f"{head}\n... ({len(names) - 200} more classes omitted)"


def _as_list(x) -> list:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]
