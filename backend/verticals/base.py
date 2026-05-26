# backend/verticals/base.py
"""
Base interface for domain vertical agents.
Each vertical inherits this and implements its tool registry + routing.
"""
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from backend.llm.router import llm_router

logger = logging.getLogger(__name__)


@dataclass
class VerticalResult:
    vertical:    str
    content:     str
    sources:     list[str]      = field(default_factory=list)
    charts:      list[str]      = field(default_factory=list)  # base64 encoded
    attachments: list[dict]     = field(default_factory=list)  # {name, data, type}
    metadata:    dict[str, Any] = field(default_factory=dict)
    latency_ms:  float          = 0.0
    error:       str | None     = None


class BaseVerticalAgent(ABC):
    vertical_name: str = "base"
    description:   str = "Base vertical agent"

    @property
    @abstractmethod
    def system_prompt(self) -> str: ...

    @abstractmethod
    async def run(
        self,
        query:         str,
        context:       dict[str, Any],
        memory_context: str = "",
    ) -> VerticalResult: ...

    async def _call_llm(
        self,
        user_content:   str,
        system_content: str | None = None,
        temperature:    float = 0.2,
        max_tokens:     int   = 2000,
    ) -> str:
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