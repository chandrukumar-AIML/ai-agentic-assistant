# backend/cost/cache.py
"""
Semantic query cache using Redis.
Identical queries (same hash) return cached responses — zero LLM cost.
Uses content hash (not embedding similarity) for exact match caching.
"""
import hashlib
import json
import logging
import time
from typing import Optional

from backend.session.redis_client import get_redis

logger = logging.getLogger(__name__)

# Cache settings
CACHE_TTL_SECONDS  = 3600   # 1 hour
CACHE_MAX_SIZE_KB  = 50     # skip caching responses > 50KB
CACHE_KEY_PREFIX   = "llm_cache:"

# Stats counters
_cache_hits   = 0
_cache_misses = 0
_cost_saved   = 0.0


def _make_cache_key(
    query:          str,
    model:          str,
    temperature:    float,
    system_prompt:  str = "",
) -> str:
    """
    Generate a deterministic cache key.
    Includes model + temperature so different configs don't share cache.
    """
    content = f"{model}:{temperature}:{system_prompt[:100]}:{query}"
    h       = hashlib.sha256(content.encode()).hexdigest()
    return f"{CACHE_KEY_PREFIX}{h}"


async def get_cached_response(
    query:         str,
    model:         str,
    temperature:   float  = 0.3,
    system_prompt: str    = "",
) -> Optional[dict]:
    """
    Check Redis for a cached response.
    Returns cached dict or None on miss.

    Cached dict structure:
    {
        "response":       str,
        "model":          str,
        "input_tokens":   int,
        "output_tokens":  int,
        "cached_at":      float,
        "cache_hit":      True,
    }
    """
    global _cache_misses, _cache_hits

    # Only cache deterministic calls (temperature = 0)
    if temperature > 0.1:
        return None

    redis = await get_redis()
    key   = _make_cache_key(query, model, temperature, system_prompt)

    try:
        raw = await redis.get(key)
        if raw:
            data          = json.loads(raw)
            data["cache_hit"] = True
            _cache_hits  += 1
            logger.debug(f"Cache HIT: {key[:20]}... (saved {data.get('cost_usd', 0):.5f} USD)")
            return data
    except Exception as e:
        logger.warning(f"Cache read failed: {e}")

    _cache_misses += 1
    return None


async def cache_response(
    query:         str,
    response:      str,
    model:         str,
    input_tokens:  int,
    output_tokens: int,
    cost_usd:      float,
    temperature:   float = 0.0,
    system_prompt: str   = "",
) -> bool:
    """
    Store a response in Redis cache.
    Returns True if cached successfully.
    """
    global _cost_saved

    # Don't cache non-deterministic or huge responses
    if temperature > 0.1:
        return False
    if len(response) > CACHE_MAX_SIZE_KB * 1024:
        logger.debug("Response too large to cache")
        return False

    redis   = await get_redis()
    key     = _make_cache_key(query, model, temperature, system_prompt)
    payload = json.dumps({
        "response":      response,
        "model":         model,
        "input_tokens":  input_tokens,
        "output_tokens": output_tokens,
        "cost_usd":      cost_usd,
        "cached_at":     time.time(),
        "query_preview": query[:100],
    })

    try:
        await redis.setex(key, CACHE_TTL_SECONDS, payload)
        _cost_saved += cost_usd
        logger.debug(f"Cached response: {key[:20]}... (cost={cost_usd:.5f} USD)")
        return True
    except Exception as e:
        logger.warning(f"Cache write failed: {e}")
        return False


async def invalidate_cache(pattern: str = "*") -> int:
    """Clear cache entries matching a pattern. Returns count deleted."""
    redis = await get_redis()
    keys  = await redis.keys(f"{CACHE_KEY_PREFIX}{pattern}")
    if keys:
        await redis.delete(*keys)
    logger.info(f"Cache invalidated: {len(keys)} entries deleted")
    return len(keys)


def get_cache_stats() -> dict:
    """Return current cache performance statistics."""
    total   = _cache_hits + _cache_misses
    hit_rate = _cache_hits / total if total > 0 else 0.0
    return {
        "hits":       _cache_hits,
        "misses":     _cache_misses,
        "hit_rate":   round(hit_rate, 4),
        "cost_saved": round(_cost_saved, 4),
        "ttl_seconds": CACHE_TTL_SECONDS,
    }