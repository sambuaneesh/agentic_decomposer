"""Base agent contract."""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from agentic_decomposer.config import RunConfig
from agentic_decomposer.logger import attach_file_handler, detach_file_handler, get_logger
from agentic_decomposer.runs import RunLayout


@dataclass
class AgentResult:
    """Lightweight wrapper around an agent's primary output."""

    name: str
    output: dict | list | None
    output_path: str | None = None
    tokens_used: int = 0
    runtime_seconds: float = 0.0
    extras: dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Common base for every agent in the framework.

    Concrete agents implement :meth:`_run`. The public :meth:`run` method
    handles per-agent logging, timing, and error containment so the controller
    sees a consistent interface for every step.
    """

    #: Short stable name used for log files and result keys. Override per subclass.
    name: str = "agent"

    def __init__(self, config: RunConfig, layout: RunLayout) -> None:
        self.config = config
        self.layout = layout
        self.logger = get_logger(f"agentic.{self.name}")

    # ------------------------------------------------------------------
    def run(self, **kwargs: Any) -> AgentResult:
        log_path = self.layout.agent_log_path(self.name)
        handler = attach_file_handler(self.logger, log_path)
        started = time.perf_counter()
        try:
            self.logger.info("agent.start name=%s run_id=%s", self.name, self.config.run_id)
            result = self._run(**kwargs)
            result.runtime_seconds = time.perf_counter() - started
            self.logger.info(
                "agent.done  name=%s runtime=%.2fs tokens=%d",
                self.name, result.runtime_seconds, result.tokens_used,
            )
            return result
        except Exception:
            self.logger.exception("agent.fail name=%s", self.name)
            raise
        finally:
            detach_file_handler(self.logger, handler)

    # ------------------------------------------------------------------
    @abstractmethod
    def _run(self, **kwargs: Any) -> AgentResult:
        """Perform this agent's work; return its primary output as an AgentResult."""
        raise NotImplementedError
