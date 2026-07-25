"""
LLM Router — Groq → Gemini → Ollama fallback chain.
Used by AI Brain features in all three verticals.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


async def call_llm(prompt: str, system: str = "", action: str = "") -> str:
    """Try Groq → Gemini → Ollama in order; return first successful response."""
    for provider_fn in (_try_groq, _try_gemini, _try_ollama):
        try:
            result = await provider_fn(prompt, system, action)
            if result:
                return result
        except Exception as exc:
            logger.warning("LLM provider failed, trying next: %s", exc)
    return "Unable to process request at this time. Please try again."


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


async def _try_ollama(prompt: str, system: str, action: str) -> str:
    from backend.llm.ollama_openai import ollama_chat_completion
    return await ollama_chat_completion(
        messages=[{"role": "user", "content": prompt}],
        system=system,
        action=action,
    )
