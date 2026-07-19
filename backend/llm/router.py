"""
LLM Router with circuit breaker pattern.

Usage in any node:
    from backend.llm.router import llm_router
    response, model = await llm_router.complete(messages, temperature=0.3)
"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import AsyncGenerator

from backend.llm.openai_client  import openai_chat, openai_health_check, OpenAICallError
from backend.llm.ollama_client  import ollama_chat, ollama_health, OllamaCallError
from backend.llm.gemini_client  import gemini_chat, gemini_health, GeminiCallError
from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CircuitState(str, Enum):
    CLOSED    = "closed"
    OPEN      = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    failure_threshold:   int   = 3
    success_threshold:   int   = 2
    cooldown_seconds:    float = 30.0

    state:             CircuitState = CircuitState.CLOSED
    failure_count:     int          = 0
    success_count:     int          = 0
    last_failure_time: float        = 0.0
    total_fallbacks:   int          = 0

    # Lock created lazily in __post_init__ to avoid event-loop binding at import time
    _lock: asyncio.Lock = field(default=None, init=False)

    def __post_init__(self):
        self._lock = asyncio.Lock()

    def record_success(self):
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                logger.info("Circuit breaker: HALF_OPEN → CLOSED")
                self.state = CircuitState.CLOSED
                self.success_count = 0

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.monotonic()
        self.success_count = 0

        if self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                logger.warning(f"Circuit breaker: CLOSED → OPEN ({self.failure_count} failures)")
                self.state = CircuitState.OPEN
                self.total_fallbacks += 1
        elif self.state == CircuitState.HALF_OPEN:
            logger.warning("Circuit breaker: HALF_OPEN → OPEN")
            self.state = CircuitState.OPEN

    def should_attempt_primary(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            elapsed = time.monotonic() - self.last_failure_time
            if elapsed >= self.cooldown_seconds:
                logger.info(f"Circuit breaker: OPEN → HALF_OPEN (cooldown elapsed: {elapsed:.1f}s)")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                return True
        if self.state == CircuitState.HALF_OPEN:
            return True
        return False

    def get_status(self) -> dict:
        return {
            "state":           self.state.value,
            "failure_count":   self.failure_count,
            "total_fallbacks": self.total_fallbacks,
            "cooldown_remaining": max(
                0.0,
                self.cooldown_seconds - (time.monotonic() - self.last_failure_time)
            ) if self.state == CircuitState.OPEN else 0.0,
        }


class LLMRouter:
    def __init__(self):
        self.circuit = CircuitBreaker()

    async def complete(
        self,
        messages:    list[dict],
        temperature: float = 0.3,
        max_tokens:  int   = 1000,
        stream:      bool  = False,
        force_model: str | None = None,
    ) -> tuple[str | AsyncGenerator, str]:
        # DEMO MODE: instant canned responses, no Ollama/OpenAI call (zero cost).
        if getattr(settings, "demo_mode", False) and not stream:
            from backend.llm.demo_responder import demo_complete
            return demo_complete(messages)

        if force_model == "gemini":
            return await self._call_gemini(messages, temperature, max_tokens, stream)
        if force_model == "ollama":
            return await self._call_ollama(messages, temperature, max_tokens, stream)
        if force_model == "openai":
            return await self._call_openai(messages, temperature, max_tokens, stream)

        # GEMINI-FIRST (production): when GEMINI_API_KEY is set, use Gemini Flash.
        # OLLAMA-FIRST (local dev): when no Gemini key, use local Ollama.
        if settings.gemini_api_key:
            return await self._call_gemini(messages, temperature, max_tokens, stream)
        return await self._call_ollama(messages, temperature, max_tokens, stream)

    async def _call_gemini(self, messages, temperature, max_tokens, stream) -> tuple:
        try:
            result = await gemini_chat(messages, temperature, max_tokens, stream)
            return result, settings.gemini_model
        except GeminiCallError as e:
            logger.warning(f"Gemini failed: {e} — falling back to Ollama")
            return await self._call_ollama(messages, temperature, max_tokens, stream)

    async def _call_openai(self, messages, temperature, max_tokens, stream) -> tuple:
        result = await openai_chat(messages, temperature, max_tokens, stream)
        return result, "gpt-4o"

    async def _call_ollama(self, messages, temperature, max_tokens, stream) -> tuple:
        try:
            result = await ollama_chat(messages, temperature, max_tokens, stream=stream)
            return result, f"ollama/{settings.ollama_model}"
        except OllamaCallError as e:
            logger.warning(f"Ollama failed: {e}")
            return (
                "LLM unavailable — set GEMINI_API_KEY for production or run: ollama serve",
                "none"
            )

    async def health(self) -> dict:
        gemini_ok, ollama_ok, openai_ok = await asyncio.gather(
            gemini_health(),
            ollama_health(),
            openai_health_check(),
        )
        active = settings.gemini_model if settings.gemini_api_key else f"ollama/{settings.ollama_model}"
        return {
            "gemini_healthy": gemini_ok,
            "ollama_healthy": ollama_ok,
            "openai_healthy": openai_ok,
            "circuit":        self.circuit.get_status(),
            "active_model":   active,
        }

    def reset(self):
        self.circuit = CircuitBreaker()
        logger.info("Circuit breaker manually reset to CLOSED")


# Module-level singleton — import this everywhere
llm_router = LLMRouter()