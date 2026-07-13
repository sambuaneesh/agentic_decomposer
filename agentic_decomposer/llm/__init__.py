"""LLM client wrappers built on LiteLLM.

The framework uses one client interface (:func:`call_llm`) so that switching
provider/model is a single CLI flag away. Token counts and raw payloads are
logged to ``runs/<run_id>/logs/llm_calls.jsonl`` for cost audit and
reproducibility.
"""

from agentic_decomposer.llm.client import (
    LLMClient,
    LLMCallResult,
    LLMConfig,
)

__all__ = ["LLMClient", "LLMCallResult", "LLMConfig"]
