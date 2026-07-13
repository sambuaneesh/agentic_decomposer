"""Agent package.

Six specialised agents + the Process Controller. Every agent class extends
:class:`agentic_decomposer.agents.base.BaseAgent` and is invoked by the
controller exactly once per pipeline stage (the Refiner may be invoked
multiple times in iterative variants).

This package currently exposes **stub implementations** that produce
schema-valid placeholder JSON so the end-to-end pipeline runs while the real
agent logic is filled in (Stages 3–7 of the MVP roadmap).
"""

from agentic_decomposer.agents.base import BaseAgent, AgentResult

__all__ = ["BaseAgent", "AgentResult"]
