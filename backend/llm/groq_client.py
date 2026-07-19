# backend/llm/groq_client.py
"""
Groq client using OpenAI-compatible API.
Free tier: 6000 req/day, 30 RPM — no card needed.
Get key: https://console.groq.com
"""
from __future__ import annotations

import logging
from typing import Optional

from openai import AsyncOpenAI, APIError

from backend.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()

GROQ_BASE_URL = "https://api.groq.com/openai/v1"

_client: Optional[AsyncOpenAI] = None


class GroqCallError(Exception):
    pass


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        if not settings.groq_api_key:
            raise GroqCallError("GROQ_API_KEY not configured")
        _client = AsyncOpenAI(
            base_url=GROQ_BASE_URL,
            api_key=settings.groq_api_key,
            timeout=30.0,
            max_retries=0,
        )
    return _client


async def groq_chat(
    messages:    list[dict],
    temperature: float = 0.7,
    max_tokens:  int   = 2048,
    model:       str | None = None,
) -> str:
    use_model = model or settings.groq_model
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
        raise GroqCallError(f"Groq API error: {e}") from e
    except Exception as e:
        raise GroqCallError(f"Groq call failed: {e}") from e


async def groq_health() -> bool:
    return bool(settings.groq_api_key)
