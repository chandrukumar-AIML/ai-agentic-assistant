"""
LLM Router — Groq → Gemini → OpenAI → Ollama fallback chain.
Used by AI Brain features in all three verticals.
"""
from __future__ import annotations

import hashlib
import logging
import time

logger = logging.getLogger(__name__)

# ── Simple in-process LLM response cache ─────────────────────────────────────
# Prevents re-calling the provider for identical (prompt, system) pairs within TTL.
_CACHE: dict[str, tuple[str, float]] = {}
_CACHE_TTL   = 300   # seconds
_CACHE_MAX   = 500   # max entries before oldest are evicted


def _cache_key(prompt: str, system: str) -> str:
    return hashlib.sha256(f"{system}|||{prompt}".encode()).hexdigest()


def _cache_get(key: str) -> str | None:
    entry = _CACHE.get(key)
    if entry and (time.monotonic() - entry[1]) < _CACHE_TTL:
        return entry[0]
    _CACHE.pop(key, None)
    return None


def _cache_set(key: str, value: str) -> None:
    if len(_CACHE) >= _CACHE_MAX:
        oldest = next(iter(_CACHE))
        _CACHE.pop(oldest, None)
    _CACHE[key] = (value, time.monotonic())


async def call_llm(prompt: str, system: str = "", action: str = "") -> str:
    """Try Groq → Gemini → OpenAI → Ollama in order; return first successful response."""
    key = _cache_key(prompt, system)
    cached = _cache_get(key)
    if cached:
        logger.debug("LLM cache hit for action=%s", action)
        return cached

    for provider_fn, provider_name in (
        (_try_groq,   "groq"),
        (_try_gemini, "gemini"),
        (_try_openai, "openai"),
        (_try_ollama, "ollama"),
    ):
        try:
            result = await provider_fn(prompt, system, action)
            if result:
                _cache_set(key, result)
                _record_llm(provider_name, action, "ok")
                return result
        except Exception as exc:
            logger.warning("LLM provider %s failed, trying next: %s", provider_name, exc)
            _record_llm(provider_name, action, "error")

    return "Unable to process request at this time. Please try again."


def _record_llm(provider: str, action: str, status: str) -> None:
    try:
        from backend.api.metrics import llm_calls_total
        llm_calls_total.labels(provider=provider, action=action, status=status).inc()
    except Exception:
        pass


async def _try_groq(prompt: str, system: str, action: str) -> str:
    from backend.llm.groq_client import groq_chat
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    return await groq_chat(msgs, action=action)


async def _try_gemini(prompt: str, system: str, action: str) -> str:
    from backend.llm.gemini_client import gemini_chat
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    return await gemini_chat(msgs, action=action)


async def _try_openai(prompt: str, system: str, action: str) -> str:
    from openai import AsyncOpenAI

    from backend.config import get_settings
    settings = get_settings()
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY not set")
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    resp = await client.chat.completions.create(
        model=settings.openai_model,
        messages=msgs,
        temperature=0.7,
    )
    return resp.choices[0].message.content or ""


async def _try_ollama(prompt: str, system: str, action: str) -> str:
    from backend.llm.ollama_openai import ollama_chat_completion
    return await ollama_chat_completion(
        messages=[{"role": "user", "content": prompt}],
        system=system,
        action=action,
    )
