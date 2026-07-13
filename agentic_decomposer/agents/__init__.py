"""Agent package.

Six specialised agents + the Process Controller. Every agent class extends
:class:`agentic_decomposer.agents.base.BaseAgent` and is invoked by the
controller exactly once per pipeline stage (the Refiner may be invoked
multiple times in iterative variants).

⚠️ The Domain Knowledge Extractor (``domain_extractor.py``) is a **temporary
placeholder** that has not been concretized. It is a bare single-LLM-call
scaffold wired to ``prompts/domain_extractor.md`` so the pipeline runs
end-to-end. The real domain modeling stage with richer evidence signals is
planned for V2. Treat this component as a placeholder.
"""

from agentic_decomposer.agents.base import BaseAgent, AgentResult

__all__ = ["BaseAgent", "AgentResult"]
