# backend/auth/rate_limiter.py
"""
Per-tier rate limiting using Redis.
Tracks daily query count per user and per workspace.
Resets at midnight UTC.
"""
import logging
from datetime import datetime, timezone, timedelta

from backend.auth.models    import PlanTier, RATE_LIMITS
from backend.session.redis_client import get_redis

logger = logging.getLogger(__name__)


def _daily_reset_seconds() -> int:
    """Seconds until next midnight UTC — used as Redis TTL."""
    now     = datetime.now(timezone.utc)
    midnight = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return int((midnight - now).total_seconds())


async def check_rate_limit(
    user_id:      str,
    workspace_id: str,
    plan_tier:    PlanTier,
) -> tuple[bool, int, int]:
    """
    Check if user is within their daily rate limit.

    Returns:
        (allowed: bool, current_count: int, limit: int)
    """
    redis  = await get_redis()
    limit  = RATE_LIMITS[plan_tier]
    ttl    = _daily_reset_seconds()

    # Per-user counter key
    key    = f"ratelimit:user:{user_id}:{datetime.now(timezone.utc).strftime('%Y%m%d')}"

    # Atomic increment + set TTL on first access
    current = await redis.incr(key)
    if current == 1:
        await redis.expire(key, ttl)

    allowed = current <= limit

    if not allowed:
        logger.warning(
            f"Rate limit exceeded: user={user_id} "
            f"tier={plan_tier} count={current}/{limit}"
        )

    return allowed, int(current), limit


async def get_usage_stats(user_id: str) -> dict:
    """Return current usage stats for a user."""
    redis   = await get_redis()
    key     = f"ratelimit:user:{user_id}:{datetime.now(timezone.utc).strftime('%Y%m%d')}"
    current = await redis.get(key)
    return {
        "today":     int(current or 0),
        "reset_at":  (
            datetime.now(timezone.utc) + timedelta(seconds=_daily_reset_seconds())
        ).isoformat(),
    }


async def reset_user_limit(user_id: str):
    """Admin action: reset a specific user's daily counter."""
    redis = await get_redis()
    key   = f"ratelimit:user:{user_id}:{datetime.now(timezone.utc).strftime('%Y%m%d')}"
    await redis.delete(key)
    logger.info(f"Rate limit reset for user: {user_id}")