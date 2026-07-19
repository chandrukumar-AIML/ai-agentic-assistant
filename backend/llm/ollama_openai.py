# backend/llm/ollama_openai.py
"""
Central Ollama client using OpenAI-compatible API.
Ollama exposes /v1/chat/completions at http://localhost:11434/v1
Use this instead of AsyncOpenAI(api_key=...) everywhere.

Usage:
    from backend.llm.ollama_openai import get_ollama_client, ollama_chat_completion, OLLAMA_MODEL

    client = get_ollama_client()
    resp = await client.chat.completions.create(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": "Hello"}],
        temperature=0.7,
    )
    text = resp.choices[0].message.content
"""
from __future__ import annotations

import logging
from typing import Optional

from openai import AsyncOpenAI

from backend.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()

# Primary model to use — llama3.2 for general, deepseek-coder for code tasks
OLLAMA_MODEL      = "llama3.2"
OLLAMA_CODE_MODEL = "deepseek-coder"
OLLAMA_BASE_URL   = "http://localhost:11434/v1"
OLLAMA_API_KEY    = "ollama"   # Ollama ignores this but openai-sdk requires a non-empty key


def get_ollama_client() -> AsyncOpenAI:
    """Return a reusable AsyncOpenAI client pointed at local Ollama."""
    return AsyncOpenAI(
        base_url=OLLAMA_BASE_URL,
        api_key=OLLAMA_API_KEY,
        timeout=120.0,          # Ollama can be slow on CPU
        max_retries=0,          # Don't retry — surface errors immediately
    )


# Singleton client (lazy)
_client: Optional[AsyncOpenAI] = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = get_ollama_client()
    return _client


async def ollama_chat_completion(
    messages:    list[dict],
    model:       str   = OLLAMA_MODEL,
    temperature: float = 0.7,
    max_tokens:  int   = 1024,
    system:      Optional[str] = None,
) -> str:
    """
    Simple wrapper — returns the text content string directly.
    Handles errors gracefully, returns empty string on failure.
    """
    cfg = get_settings()

    # DEMO MODE: instant canned response, no LLM call.
    if getattr(cfg, "demo_mode", False):
        try:
            from backend.llm.demo_responder import demo_complete
            msgs = ([{"role": "system", "content": system}] if system else []) + list(messages)
            return demo_complete(msgs)[0]
        except Exception:
            pass

    if system and (not messages or messages[0].get("role") != "system"):
        messages = [{"role": "system", "content": system}] + list(messages)

    # GEMINI-FIRST (production): when GEMINI_API_KEY is set, use Gemini Flash.
    if cfg.gemini_api_key:
        try:
            from backend.llm.gemini_client import gemini_chat
            return await gemini_chat(messages, temperature=temperature, max_tokens=max_tokens)
        except Exception as e:
            logger.warning("Gemini failed, falling back to Ollama: %s", e)

    # LOCAL DEV: use Ollama.
    client = get_client()
    try:
        resp = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        logger.error("Ollama completion failed (model=%s): %s", model, e)
        return ""


async def ollama_health() -> bool:
    """Quick health check — returns True if Ollama responds."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=3.0) as c:
            r = await c.get("http://localhost:11434/")
            return r.status_code == 200
    except Exception:
        return False
