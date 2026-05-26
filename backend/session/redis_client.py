"""
Redis session client — async, connection-pooled.

Exported API:
  get_redis()               → AsyncRedis (singleton)
  close_redis()             → graceful shutdown (called from lifespan)
  get_session(session_id)   → dict | None
  save_session(session_id, data, ttl_seconds)
  delete_session(session_id)
"""
import asyncio  # FIXED: added for async lock used in thread-safe get_redis()
import json
import logging
from typing import Any

import redis.asyncio as aioredis
from backend.config import get_settings  # FIXED: wrong import path — was `config`, must be `backend.config`

logger   = logging.getLogger(__name__)
settings = get_settings()

_redis: aioredis.Redis | None = None

_SESSION_TTL = 60 * 60 * 24  # 24 hours default
_redis_lock: asyncio.Lock | None = None  # FIXED: async lock for race-free lazy init


def _get_lock() -> asyncio.Lock:
    """Return (or create) the module-level async lock. Safe to call before the event loop starts."""
    global _redis_lock
    if _redis_lock is None:
        _redis_lock = asyncio.Lock()  # FIXED: created lazily so it binds to the running event loop
    return _redis_lock


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is not None:
        return _redis
    async with _get_lock():  # FIXED: prevents concurrent coroutines from creating multiple Redis connections
        if _redis is None:  # FIXED: double-checked locking after acquiring the lock
            _redis = aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            logger.info(f"Redis client connected: {settings.redis_url}")
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
        logger.info("Redis connection closed")


async def get_session(session_id: str) -> dict[str, Any] | None:
    """Return the session dict, or None if it doesn't exist."""
    try:
        r = await get_redis()
        raw = await r.get(f"session:{session_id}")
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as e:
        logger.error(f"Redis get_session failed for {session_id}: {e}")
        return None


async def save_session(
    session_id: str,
    data: dict[str, Any],
    ttl_seconds: int = _SESSION_TTL,
) -> None:
    """Persist session data with a TTL (default 24 h)."""
    try:
        r = await get_redis()
        await r.setex(
            f"session:{session_id}",
            ttl_seconds,
            json.dumps(data, default=str),
        )
    except Exception as e:
        logger.error(f"Redis save_session failed for {session_id}: {e}")


async def delete_session(session_id: str) -> None:
    """Remove a session from Redis."""
    try:
        r = await get_redis()
        await r.delete(f"session:{session_id}")
    except Exception as e:
        logger.error(f"Redis delete_session failed for {session_id}: {e}")
