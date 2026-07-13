"""Robust JSON parsing helpers for LLM responses.

LLMs do not reliably return raw JSON. They often wrap it in markdown code fences
(```json … ```), prefix it with prose, or trail it with a friendly summary.
:func:`extract_json` accepts every common shape and returns the parsed object,
or raises ``LLMOutputError`` with a useful diagnostic.
"""
from __future__ import annotations

import json
import re
from typing import Any


class LLMOutputError(ValueError):
    """Raised when an LLM response cannot be parsed as JSON."""

    def __init__(self, message: str, raw: str) -> None:
        super().__init__(f"{message}\n--- raw response ---\n{raw[:2000]}\n--- end ---")
        self.raw = raw


_FENCE_RE = re.compile(r"```(?:json|JSON)?\s*([\s\S]*?)\s*```", re.MULTILINE)


def extract_json(text: str) -> Any:
    """Parse the first JSON object/array found in *text*.

    Strategy, in order:
      1. Try ``json.loads(text)`` directly.
      2. Extract the contents of the first ``` fenced block `` and parse it.
      3. Scan for the first ``{`` or ``[``, find the matching brace using
         a depth counter, parse that slice.

    Raises :class:`LLMOutputError` if none of these succeed.
    """
    if text is None:
        raise LLMOutputError("LLM response was None.", "")

    stripped = text.strip()
    if not stripped:
        raise LLMOutputError("LLM response was empty.", text)

    # 1) raw JSON
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # 2) fenced code block
    fence = _FENCE_RE.search(stripped)
    if fence:
        candidate = fence.group(1).strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # 3) balanced brace scan
    candidate = _slice_balanced(stripped)
    if candidate is not None:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    raise LLMOutputError("Could not parse JSON from LLM response.", text)


def _slice_balanced(text: str) -> str | None:
    """Return the substring from the first ``{`` or ``[`` to its matching close."""
    open_chars = "{["
    close_chars = "}]"
    pair = {"{": "}", "[": "]"}

    # find first opening brace
    start = -1
    opener = ""
    for i, ch in enumerate(text):
        if ch in open_chars:
            start = i
            opener = ch
            break
    if start < 0:
        return None

    closer = pair[opener]
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
            continue
        if ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


def extract_json_object(text: str) -> dict:
    """Like :func:`extract_json` but requires the parsed value to be a dict."""
    result = extract_json(text)
    if not isinstance(result, dict):
        raise LLMOutputError(
            f"Expected a JSON object, got {type(result).__name__}.", text,
        )
    return result
