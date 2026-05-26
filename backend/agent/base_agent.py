# backend/agents/base_agent.py
"""
Base class for all worker agents.
Each worker has: a name, system prompt, allowed tools, and a run() method.
"""
import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from backend.llm.router import llm_router

logger = logging.getLogger(__name__)


@dataclass
class WorkerResult:
    worker_name: str
    content:     str
    sources:     list[str]      = field(default_factory=list)
    confidence:  float          = 0.8
    metadata:    dict[str, Any] = field(default_factory=dict)
    latency_ms:  float          = 0.0
    error:       str | None     = None


class BaseWorkerAgent(ABC):
    """
    All worker agents inherit from this.
    Each implements: system_prompt, tools_description, run()
    """
    name:        str = "base_worker"
    description: str = "Base worker"

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """The worker's specialised system prompt."""
        ...

    @abstractmethod
    async def run(
        self,
        query:          str,
        context:        dict[str, Any],
        memory_context: str = "",
    ) -> WorkerResult:
        """Execute the worker's task. Must return a WorkerResult."""
        ...

    async def _call_llm(
        self,
        user_content:   str,
        system_content: str | None = None,
        temperature:    float = 0.3,
        max_tokens:     int   = 1500,
    ) -> str:
        """Shared LLM call through the router (circuit breaker included)."""
        messages = []
        if system_content:
            messages.append({"role": "system", "content": system_content})
        messages.append({"role": "user", "content": user_content})

        response, _ = await llm_router.complete(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response if isinstance(response, str) else ""

    def _timed(self) -> float:
        return time.monotonic()