# backend/llm/gemini_client.py
"""
Gemini Flash client using Google's OpenAI-compatible endpoint.

Gemini exposes /v1beta/openai/ which is fully compatible with the OpenAI SDK,
so we reuse AsyncOpenAI — zero extra dependencies needed.

Usage:
    from backend.llm.gemini_client import gemini_chat, gemini_health, GeminiCallError
"""
from __future__ import annotations

import logging
from typing import Optional

from openai import AsyncOpenAI, APIError

from backend.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

_client: Optional[AsyncOpenAI] = None


class GeminiCallError(Exception):
    pass


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        if not settings.gemini_api_key:
            raise GeminiCallError("GEMINI_API_KEY not configured")
        _client = AsyncOpenAI(
            base_url=GEMINI_BASE_URL,
            api_key=settings.gemini_api_key,
            timeout=60.0,
            max_retries=2,
        )
    return _client


async def gemini_chat(
    messages:    list[dict],
    temperature: float = 0.7,
    max_tokens:  int   = 2048,
    stream:      bool  = False,
    model:       str | None = None,
) -> str:
    """Call Gemini Flash and return the text response."""
    use_model = model or settings.gemini_model
    client = _get_client()
    try:
        resp = await client.chat.completions.create(
            model=use_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""
    except APIError as e:
        raise GeminiCallError(f"Gemini API error: {e}") from e
    except Exception as e:
        raise GeminiCallError(f"Gemini call failed: {e}") from e


async def gemini_health() -> bool:
    """Quick health check — returns True if Gemini API key is set and reachable."""
    if not settings.gemini_api_key:
        return False
    try:
        result = await gemini_chat(
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5,
        )
        return bool(result)
    except Exception:
        return False
