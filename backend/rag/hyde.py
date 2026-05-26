# backend/rag/hyde.py — HyDE via Ollama (no OpenAI)
import logging
from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL

logger = logging.getLogger(__name__)

HYDE_PROMPT = """\
Write a concise, factual passage (3-5 sentences) that directly answers the
following question. Write it as if it were an excerpt from a reference document,
not as a conversational reply. Do not say "According to..." — just state the facts.

Question: {query}
"""


async def generate_hypothetical_document(query: str) -> str:
    """
    Generate a hypothetical answer document for HyDE retrieval using Ollama.
    Falls back to the raw query if Ollama fails.
    """
    try:
        result = await ollama_chat_completion(
            messages=[{"role": "user", "content": HYDE_PROMPT.format(query=query)}],
            model=OLLAMA_MODEL,
            temperature=0.1,
            max_tokens=200,
        )
        if result:
            result = result.strip()
            logger.debug("HyDE generated: %s...", result[:100])
            return result
    except Exception as e:
        logger.warning("HyDE generation failed, using raw query: %s", e)
    return query   # fallback — embed the raw query
