"""Thin LiteLLM wrapper with token counting and JSONL logging."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LLMConfig:
    """Per-run LLM configuration."""

    model: str
    temperature: float = 0.2
    max_tokens: int | None = None
    seed: int | None = None
    # When set, every prompt+response pair is appended to this JSONL file.
    log_path: Path | None = None


@dataclass(frozen=True)
class LLMCallResult:
    text: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    latency_ms: int
    raw_response: dict | None = None


class LLMClient:
    """Stateless wrapper around ``litellm.completion``.

    Reasons not to call ``litellm.completion`` directly from agents:

    1. We want consistent JSONL logging of every call.
    2. We want consistent extraction of text + token counts across providers.
    3. We want a single seam to inject test doubles when running offline.

    The client is intentionally simple — no retries or rate-limit handling yet.
    Those will live in ``llm/retry.py`` once we hit a real production need.
    """

    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    # ------------------------------------------------------------------
    def complete(self, *, system: str, user: str, response_format: dict | None = None) -> LLMCallResult:
        """Run a single completion. Returns the assistant text + token usage."""
        # Local import keeps ``litellm`` an optional dependency for code paths
        # that never call the LLM (e.g. deterministic evidence mode).
        import litellm  # noqa: WPS433 (deliberate local import)

        messages = [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ]
        kwargs: dict[str, Any] = {
            "model":       self.config.model,
            "messages":    messages,
            "temperature": self.config.temperature,
        }
        if self.config.max_tokens is not None:
            kwargs["max_tokens"] = self.config.max_tokens
        if self.config.seed is not None:
            kwargs["seed"] = self.config.seed
        if response_format is not None:
            kwargs["response_format"] = response_format

        started = time.perf_counter()
        response = litellm.completion(**kwargs)
        elapsed_ms = int((time.perf_counter() - started) * 1000)

        text, usage = _extract_text_and_usage(response)
        result = LLMCallResult(
            text=text,
            model=self.config.model,
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
            total_tokens=usage.get("total_tokens"),
            latency_ms=elapsed_ms,
            raw_response=_safe_dump(response),
        )

        self._log_call(system=system, user=user, result=result)
        return result

    # ------------------------------------------------------------------
    def _log_call(self, *, system: str, user: str, result: LLMCallResult) -> None:
        if self.config.log_path is None:
            return
        record = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "model":         result.model,
            "input_tokens":  result.input_tokens,
            "output_tokens": result.output_tokens,
            "total_tokens":  result.total_tokens,
            "latency_ms":    result.latency_ms,
            "system_prompt": system,
            "user_prompt":   user,
            "response_text": result.text,
        }
        self.config.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.config.log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _safe_dump(obj: Any) -> dict | None:
    """Best-effort conversion of a LiteLLM response to a plain dict."""
    try:
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "dict"):
            return obj.dict()
        if isinstance(obj, dict):
            return obj
    except Exception:
        return None
    return None


def _extract_text_and_usage(response: Any) -> tuple[str, dict]:
    """Extract the assistant text + usage dict from a LiteLLM ChatCompletion."""
    # LiteLLM normalises to the OpenAI shape regardless of provider.
    try:
        choice = response.choices[0]
        text = choice.message.content if hasattr(choice, "message") else choice["message"]["content"]
    except Exception:
        text = ""
    try:
        usage = response.usage
        usage_dict = {
            "prompt_tokens":     getattr(usage, "prompt_tokens", None),
            "completion_tokens": getattr(usage, "completion_tokens", None),
            "total_tokens":      getattr(usage, "total_tokens", None),
        }
    except Exception:
        usage_dict = {}
    return (text or ""), usage_dict


def disable_litellm_telemetry() -> None:
    """Tell LiteLLM not to phone home; call once at framework startup."""
    os.environ.setdefault("LITELLM_LOG", "ERROR")
    os.environ.setdefault("LITELLM_TELEMETRY", "False")
