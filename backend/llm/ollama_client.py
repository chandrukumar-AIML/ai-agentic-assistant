import json
import logging
import httpx
from typing import AsyncGenerator
from backend.config import get_settings  # FIXED: wrong import path — was `config`, must be `backend.config`

logger = logging.getLogger(__name__)
settings = get_settings()

# Module-level singleton — generous read timeout for slow local hardware
_httpx_client = httpx.AsyncClient(
    timeout=httpx.Timeout(connect=10.0, read=300.0, write=30.0, pool=10.0)
)


class OllamaCallError(Exception):
    pass


async def ollama_chat(
    messages:    list[dict],
    temperature: float = 0.3,
    max_tokens:  int   = 1000,
    stream:      bool  = False,
    num_ctx:     int   = 512,   # smaller context = faster on CPU
) -> str | AsyncGenerator[str, None]:
    payload = {
        "model":    settings.ollama_model,
        "messages": messages,
        "stream":   stream,
        "options":  {
            "temperature":  temperature,
            "num_predict":  max_tokens,
            "num_ctx":      num_ctx,   # limits context window for speed
        },
    }

    try:
        if stream:
            return _stream_ollama(payload)
        else:
            response = await _httpx_client.post(
                f"{settings.ollama_base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]

    except httpx.HTTPError as e:
        raise OllamaCallError(f"Ollama HTTP error: {e}")
    except Exception as e:
        raise OllamaCallError(f"Ollama unexpected error: {e}")


async def _stream_ollama(payload: dict) -> AsyncGenerator[str, None]:
    """Async generator for Ollama streaming — call without await."""
    async with _httpx_client.stream(
        "POST",
        f"{settings.ollama_base_url}/api/chat",
        json={**payload, "stream": True},
    ) as response:
        response.raise_for_status()
        async for line in response.aiter_lines():
            if not line:
                continue
            try:
                chunk = json.loads(line)
                content = chunk.get("message", {}).get("content", "")
                if content:
                    yield content
                if chunk.get("done"):
                    break
            except json.JSONDecodeError:
                continue


async def ollama_health() -> bool:
    try:
        r = await _httpx_client.get(f"{settings.ollama_base_url}/api/tags")
        if r.status_code != 200:
            return False
        models = [m["name"] for m in r.json().get("models", [])]
        has_model = any(settings.ollama_model.split(":")[0] in m for m in models)
        if not has_model:
            logger.warning(f"Ollama running but model '{settings.ollama_model}' not found. Available: {models}")
        return True
    except Exception:
        return False