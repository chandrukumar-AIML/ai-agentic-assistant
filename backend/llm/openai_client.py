import logging
from typing import AsyncGenerator
from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError
from backend.config import get_settings  # FIXED: wrong import path — was `config`, must be `backend.config`

logger = logging.getLogger(__name__)
settings = get_settings()

# Module-level singleton — one HTTP connection pool for all calls
_openai_client = AsyncOpenAI(
    api_key=settings.openai_api_key,
    timeout=30.0,
    max_retries=0,  # retries handled by circuit breaker in router
)


class OpenAICallError(Exception):
    """Raised when the OpenAI call fails — router catches this."""
    pass


async def openai_chat(
    messages:    list[dict],
    temperature: float = 0.3,
    max_tokens:  int   = 1000,
    stream:      bool  = False,
) -> str | AsyncGenerator[str, None]:
    try:
        if stream:
            return _stream_openai(messages, temperature, max_tokens)
        else:
            response = await _openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content

    except RateLimitError as e:
        raise OpenAICallError(f"Rate limit: {e}")
    except APITimeoutError as e:
        raise OpenAICallError(f"Timeout: {e}")
    except APIError as e:
        raise OpenAICallError(f"API error: {e}")
    except Exception as e:
        raise OpenAICallError(f"Unexpected: {e}")


async def _stream_openai(
    messages:    list[dict],
    temperature: float,
    max_tokens:  int,
) -> AsyncGenerator[str, None]:
    """Async generator for streaming OpenAI responses."""
    try:
        # Correct SDK pattern: await create(), then iterate the stream object
        stream = await _openai_client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    except Exception as e:
        raise OpenAICallError(f"Stream failed: {e}")


async def openai_health_check() -> bool:
    try:
        await _openai_client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1,
        )
        return True
    except Exception:
        return False