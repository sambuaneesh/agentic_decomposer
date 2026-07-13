"""Schema-validation helpers.

A thin wrapper over ``jsonschema`` that converts the library's stack-trace-style
errors into compact, human-readable messages and that always validates in
"collect all errors" mode so users see every problem in one pass.
"""
from __future__ import annotations

from typing import Iterable

import jsonschema
from jsonschema import Draft202012Validator

from agentic_decomposer.artifacts.schemas import SchemaName, get_registry


class ValidationError(Exception):
    """Raised when a JSON artifact does not satisfy its schema."""

    def __init__(self, schema_name: str, messages: list[str]) -> None:
        self.schema_name = schema_name
        self.messages = messages
        joined = "\n  - ".join(messages)
        super().__init__(f"Artifact failed {schema_name} validation:\n  - {joined}")


def _format_error(err: jsonschema.ValidationError) -> str:
    location = "/".join(str(p) for p in err.absolute_path) or "<root>"
    return f"[{location}] {err.message}"


def validate(payload: dict, schema_name: SchemaName) -> None:
    """Raise ``ValidationError`` if *payload* does not satisfy *schema_name*.

    Returns ``None`` on success. We do not return a normalised copy because
    the framework never relies on schema-applied defaults — all defaults are
    set explicitly in the producing agent.
    """
    schema = get_registry().get(schema_name)
    validator = Draft202012Validator(schema)
    errors: Iterable[jsonschema.ValidationError] = validator.iter_errors(payload)
    messages = [_format_error(e) for e in errors]
    if messages:
        raise ValidationError(schema_name, messages)
