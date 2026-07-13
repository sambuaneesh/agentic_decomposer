"""
agentic_decomposer
==================

Multi-agent framework for monolith-to-microservices decomposition.

The framework is composed of a deterministic Process Controller plus six
specialised agents that communicate exclusively via JSON artifacts validated
against the schemas in ``../schemas/``.

See ``docs/architecture.md`` for the design and ``docs/usage.md`` for CLI
usage. No symbols are re-exported here on purpose — each module owns its
public surface explicitly to keep imports unambiguous.
"""

__version__ = "0.1.0"
