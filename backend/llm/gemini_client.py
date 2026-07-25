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

from openai import APIError, AsyncOpenAI

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
            max_retries=0,
        )
    return _client


async def gemini_chat(
    messages:    list[dict],
    temperature: float = 0.7,
    max_tokens:  int   = 2048,
    stream:      bool  = False,
    model:       str | None = None,
    action:      str = "",
) -> str:
    """Call Gemini Flash and return the text response."""
    import time

    from backend.llm.cost_tracker import LLMCallRecord, estimate_cost, log_llm_call

    use_model = model or settings.gemini_model
    client = _get_client()
    start = time.monotonic()
    try:
        resp = await client.chat.completions.create(
            model=use_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        usage = resp.usage
        in_tok  = usage.prompt_tokens     if usage else 0
        out_tok = usage.completion_tokens if usage else 0
        log_llm_call(LLMCallRecord(
            provider="gemini", model=use_model, action=action,
            input_tokens=in_tok, output_tokens=out_tok,
            latency_ms=round((time.monotonic() - start) * 1000, 1),
            cost_usd=estimate_cost(use_model, in_tok, out_tok),
        ))
        return resp.choices[0].message.content or ""
    except APIError as e:
        log_llm_call(LLMCallRecord(
            provider="gemini", model=use_model, action=action,
            latency_ms=round((time.monotonic() - start) * 1000, 1),
            error=str(e)[:120],
        ))
        raise GeminiCallError(f"Gemini API error: {e}") from e
    except Exception as e:
        raise GeminiCallError(f"Gemini call failed: {e}") from e


async def gemini_health() -> bool:
    """Returns True if Gemini API key is configured (avoids burning rate-limit quota on health checks)."""
    return bool(settings.gemini_api_key)
