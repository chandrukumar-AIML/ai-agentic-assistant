# backend/mlops/canary.py
"""
Canary deployment manager.
Routes X% of traffic to new model version.
Monitors quality, auto-promotes or rolls back.
"""
import logging
import random
import json
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional

from backend.session.redis_client import get_redis

logger = logging.getLogger(__name__)

CANARY_KEY_PREFIX = "canary:"


@dataclass
class CanaryConfig:
    model_name:      str           # e.g. "ollama/llama3-finetuned"
    traffic_pct:     float         # 0.10 = 10% traffic
    started_at:      datetime
    min_queries:     int = 100     # queries before auto-decision
    promote_if_better_by: float = 0.05   # promote if TCR improves 5%
    status:          str = "running"     # running|promoted|rolled_back


async def start_canary(
    model_name:   str,
    traffic_pct:  float = 0.10,
    min_queries:  int   = 100,
) -> CanaryConfig:
    """
    Start a canary deployment.
    Writes config to Redis so all backend instances see it.
    """
    config = CanaryConfig(
        model_name=model_name,
        traffic_pct=traffic_pct,
        started_at=datetime.now(timezone.utc),
        min_queries=min_queries,
    )

    redis = await get_redis()
    await redis.set(
        f"{CANARY_KEY_PREFIX}active",
        json.dumps({
            "model_name":   config.model_name,
            "traffic_pct":  config.traffic_pct,
            "started_at":   config.started_at.isoformat(),
            "min_queries":  config.min_queries,
            "status":       config.status,
        }),
        ex=7 * 24 * 3600,   # 7 days TTL
    )

    # Reset counters
    await redis.delete(f"{CANARY_KEY_PREFIX}control_queries")
    await redis.delete(f"{CANARY_KEY_PREFIX}canary_queries")
    await redis.delete(f"{CANARY_KEY_PREFIX}control_score_sum")
    await redis.delete(f"{CANARY_KEY_PREFIX}canary_score_sum")

    logger.info(
        f"Canary started: model={model_name} "
        f"traffic={traffic_pct:.0%} min_queries={min_queries}"
    )
    return config


async def get_model_for_request() -> tuple[str, str]:
    """
    Decide which model to use for this request.

    Returns: (model_name, group) where group is "canary" or "control"
    """
    redis = await get_redis()
    raw   = await redis.get(f"{CANARY_KEY_PREFIX}active")

    if not raw:
        return "auto", "control"

    config = json.loads(raw)
    if config.get("status") != "running":
        return "auto", "control"

    if random.random() < config["traffic_pct"]:
        await redis.incr(f"{CANARY_KEY_PREFIX}canary_queries")
        return config["model_name"], "canary"
    else:
        await redis.incr(f"{CANARY_KEY_PREFIX}control_queries")
        return "auto", "control"


async def record_canary_result(
    group:            str,   # "canary" or "control"
    reflection_score: float,
):
    """Record quality score for canary analysis."""
    redis = await get_redis()
    if group == "canary":
        await redis.incrbyfloat(f"{CANARY_KEY_PREFIX}canary_score_sum", reflection_score)
    else:
        await redis.incrbyfloat(f"{CANARY_KEY_PREFIX}control_score_sum", reflection_score)


async def check_canary_decision() -> Optional[str]:
    """
    Check if canary has enough data to make a promotion decision.
    Returns: "promote", "rollback", or None (not enough data yet)
    """
    redis = await get_redis()
    raw   = await redis.get(f"{CANARY_KEY_PREFIX}active")
    if not raw:
        return None

    config = json.loads(raw)
    if config.get("status") != "running":
        return None

    canary_queries  = int(await redis.get(f"{CANARY_KEY_PREFIX}canary_queries")  or 0)
    control_queries = int(await redis.get(f"{CANARY_KEY_PREFIX}control_queries") or 0)
    min_queries     = config.get("min_queries", 100)

    if canary_queries < min_queries // 2 or control_queries < min_queries // 2:
        return None

    canary_score_sum  = float(await redis.get(f"{CANARY_KEY_PREFIX}canary_score_sum")  or 0)
    control_score_sum = float(await redis.get(f"{CANARY_KEY_PREFIX}control_score_sum") or 0)

    canary_avg  = canary_score_sum  / max(canary_queries, 1)
    control_avg = control_score_sum / max(control_queries, 1)
    improvement = canary_avg - control_avg

    promote_threshold = config.get("promote_if_better_by", 0.05)

    logger.info(
        f"Canary analysis: canary={canary_avg:.3f} control={control_avg:.3f} "
        f"improvement={improvement:+.3f} "
        f"(threshold={promote_threshold:+.3f})"
    )

    if improvement >= promote_threshold:
        decision = "promote"
    elif improvement <= -promote_threshold:
        decision = "rollback"
    else:
        return None   # Not decisive yet

    # Update status
    config["status"] = "promoted" if decision == "promote" else "rolled_back"
    await redis.set(
        f"{CANARY_KEY_PREFIX}active",
        json.dumps(config),
        ex=7 * 24 * 3600,
    )

    logger.info(
        f"Canary decision: {decision} "
        f"(canary={canary_avg:.3f} vs control={control_avg:.3f})"
    )
    return decision


async def get_canary_status() -> Optional[dict]:
    """Return current canary status for admin UI."""
    redis = await get_redis()
    raw   = await redis.get(f"{CANARY_KEY_PREFIX}active")
    if not raw:
        return None

    config          = json.loads(raw)
    canary_queries  = int(await redis.get(f"{CANARY_KEY_PREFIX}canary_queries")  or 0)
    control_queries = int(await redis.get(f"{CANARY_KEY_PREFIX}control_queries") or 0)
    canary_score    = float(await redis.get(f"{CANARY_KEY_PREFIX}canary_score_sum")  or 0)
    control_score   = float(await redis.get(f"{CANARY_KEY_PREFIX}control_score_sum") or 0)

    return {
        **config,
        "canary_queries":   canary_queries,
        "control_queries":  control_queries,
        "canary_avg_score": round(canary_score  / max(canary_queries, 1), 3),
        "control_avg_score":round(control_score / max(control_queries, 1), 3),
        "total_queries":    canary_queries + control_queries,
        "completion_pct":   round(
            min(canary_queries, control_queries) / max(config.get("min_queries", 100) // 2, 1) * 100, 1
        ),
    }


async def rollback_canary() -> bool:
    """Manually roll back the canary deployment."""
    redis = await get_redis()
    raw   = await redis.get(f"{CANARY_KEY_PREFIX}active")
    if not raw:
        return False

    config = json.loads(raw)
    config["status"] = "rolled_back"
    await redis.set(f"{CANARY_KEY_PREFIX}active", json.dumps(config), ex=86400)
    logger.info(f"Canary manually rolled back: {config['model_name']}")
    return True