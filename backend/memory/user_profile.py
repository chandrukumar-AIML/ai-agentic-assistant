# backend/memory/user_profile.py
"""
Long-term User Profile Memory (Feature 3).

Stores per-user preferences and domain signals that auto-load at session start:
  - expertise_level:     beginner | intermediate | expert
  - communication_style: concise | detailed | bullet_points | conversational
  - domain_interests:    list of topic tags e.g. ["law", "finance", "code"]
  - language:            preferred language code (default: "en")
  - timezone:            IANA timezone string
  - custom_instructions: user-set system prompt addon

Profile is loaded once per session and injected into the system prompt.
It is incrementally updated by the memory_updater_node after each turn.

Storage: PostgreSQL (primary) + Redis cache (5-min TTL).
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from backend.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()

_CACHE_TTL = 300   # 5 minutes


# ── Schema ────────────────────────────────────────────────────────────────────

DEFAULT_PROFILE = {
    "expertise_level":     "intermediate",
    "communication_style": "detailed",
    "domain_interests":    [],
    "language":            "en",
    "timezone":            "UTC",
    "custom_instructions": "",
    "interaction_count":   0,
    "last_seen":           None,
}


# ── Cache helpers ─────────────────────────────────────────────────────────────

def _cache_key(user_id: str) -> str:
    return f"user_profile:{user_id}"


async def _get_cached(user_id: str) -> Optional[dict]:
    try:
        from backend.session.redis_client import get_redis
        redis = await get_redis()
        raw   = await redis.get(_cache_key(user_id))
        return json.loads(raw) if raw else None
    except Exception:
        return None


async def _set_cached(user_id: str, profile: dict) -> None:
    try:
        from backend.session.redis_client import get_redis
        redis = await get_redis()
        await redis.setex(_cache_key(user_id), _CACHE_TTL, json.dumps(profile))
    except Exception:
        pass


async def _invalidate_cache(user_id: str) -> None:
    try:
        from backend.session.redis_client import get_redis
        redis = await get_redis()
        await redis.delete(_cache_key(user_id))
    except Exception:
        pass


# ── DB operations ────────────────────────────────────────────────────────────

async def _get_pool():
    from backend.prompts.registry import get_pool
    return await get_pool()


async def get_user_profile(user_id: str) -> dict:
    """
    Load user profile from Redis cache → PostgreSQL → default.

    Always returns a complete profile dict (never raises).
    """
    # 1. Check cache
    cached = await _get_cached(user_id)
    if cached:
        return cached

    # 2. Query DB
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT profile_data FROM user_profiles WHERE user_id = $1",
                user_id,
            )
        if row:
            profile = {**DEFAULT_PROFILE, **json.loads(row["profile_data"])}
            await _set_cached(user_id, profile)
            return profile
    except Exception as e:
        logger.warning("user_profile DB read failed (using default): %s", e)

    # 3. Return default (new user)
    return dict(DEFAULT_PROFILE)


async def save_user_profile(user_id: str, updates: dict) -> dict:
    """
    Merge updates into existing profile and persist.

    Returns the updated profile.
    """
    current = await get_user_profile(user_id)
    updated = {**current, **updates, "last_seen": datetime.now(timezone.utc).isoformat()}

    # Increment interaction count if this is a turn update
    if "interaction_count" not in updates:
        updated["interaction_count"] = current.get("interaction_count", 0) + 1

    # Merge domain_interests (union, capped at 20)
    if "domain_interests" in updates:
        existing  = set(current.get("domain_interests", []))
        new_items = set(updates["domain_interests"])
        merged    = list(existing | new_items)[:20]
        updated["domain_interests"] = merged

    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO user_profiles (user_id, profile_data, updated_at)
                VALUES ($1, $2::jsonb, NOW())
                ON CONFLICT (user_id) DO UPDATE
                SET profile_data = $2::jsonb, updated_at = NOW()
                """,
                user_id,
                json.dumps(updated),
            )
    except Exception as e:
        logger.error("user_profile DB write failed: %s", e)

    # Update cache
    await _set_cached(user_id, updated)
    logger.info("User profile updated for %s — expertise: %s, interests: %s",
                user_id, updated.get("expertise_level"), updated.get("domain_interests"))

    return updated


async def delete_user_profile(user_id: str) -> bool:
    """Delete user profile (GDPR right to erasure)."""
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM user_profiles WHERE user_id = $1", user_id,
            )
        await _invalidate_cache(user_id)
        deleted = result != "DELETE 0"
        logger.info("User profile deleted for %s: %s", user_id, deleted)
        return deleted
    except Exception as e:
        logger.error("user_profile delete failed: %s", e)
        return False


# ── System prompt injection ───────────────────────────────────────────────────

def build_profile_system_prompt(profile: dict) -> str:
    """
    Return a system prompt addon that injects user preferences.
    This is prepended to the planner's system prompt at session start.
    """
    expertise  = profile.get("expertise_level", "intermediate")
    style      = profile.get("communication_style", "detailed")
    interests  = profile.get("domain_interests", [])
    language   = profile.get("language", "en")
    custom     = profile.get("custom_instructions", "").strip()
    count      = profile.get("interaction_count", 0)

    expertise_guidance = {
        "beginner":     "Use simple language, avoid jargon, explain every concept from scratch.",
        "intermediate": "Assume general knowledge. Explain domain-specific terms briefly.",
        "expert":       "Use technical vocabulary freely. Skip basic explanations. Be precise.",
    }.get(expertise, "")

    style_guidance = {
        "concise":         "Keep responses brief — key points only, max 3-4 sentences.",
        "detailed":        "Provide thorough explanations with context and examples.",
        "bullet_points":   "Format responses as bullet points and numbered lists.",
        "conversational":  "Use a warm, conversational tone. Vary sentence structure.",
    }.get(style, "")

    interest_str = ", ".join(interests[:10]) if interests else "general topics"
    lang_note    = f"Respond in language: {language}." if language != "en" else ""

    parts = [
        f"## User Profile (interaction #{count + 1})",
        f"- Expertise: {expertise} — {expertise_guidance}",
        f"- Style: {style} — {style_guidance}",
        f"- Interests: {interest_str}",
    ]
    if lang_note:
        parts.append(f"- {lang_note}")
    if custom:
        parts.append(f"- Custom instructions: {custom}")

    return "\n".join(parts)


# ── LangGraph: profile updater signal ────────────────────────────────────────

async def infer_profile_updates(
    user_query:   str,
    ai_response:  str,
    current:      dict,
) -> dict:
    """
    Infer profile field updates from a completed conversation turn.
    Uses simple heuristics — no LLM call needed, keeps latency near-zero.

    Returns dict of fields to update (empty dict if nothing changed).
    """
    updates: dict = {}

    # Expertise level inference from vocabulary
    expert_signals   = ["API", "asymptotic", "Byzantine", "eigenvector", "polymorphism",
                        "sharding", "replication", "idempotent", "ACID", "CAP theorem"]
    beginner_signals = ["what is", "explain to me", "I don't understand", "how do I",
                        "for dummies", "simple explanation", "ELI5"]

    query_lower = user_query.lower()
    expert_hits   = sum(1 for s in expert_signals  if s.lower() in query_lower)
    beginner_hits = sum(1 for s in beginner_signals if s        in query_lower)

    current_expertise = current.get("expertise_level", "intermediate")
    if expert_hits >= 2 and current_expertise == "intermediate":
        updates["expertise_level"] = "expert"
    elif beginner_hits >= 2 and current_expertise == "intermediate":
        updates["expertise_level"] = "beginner"

    # Domain interest inference
    domain_keywords = {
        "law":       ["legal", "court", "IPC", "contract", "lawsuit", "attorney", "judge"],
        "finance":   ["stock", "portfolio", "P&L", "EBITDA", "investment", "dividend"],
        "code":      ["function", "class", "bug", "debug", "deploy", "git", "algorithm"],
        "health":    ["patient", "diagnosis", "medication", "clinical", "symptoms"],
        "agri":      ["crop", "soil", "fertilizer", "mandi", "sowing", "harvest"],
        "hr":        ["hiring", "resume", "interview", "onboarding", "payroll", "candidate"],
        "sales":     ["lead", "CRM", "prospect", "pipeline", "quota", "close"],
        "marketing": ["campaign", "SEO", "CTR", "funnel", "conversion", "brand"],
    }

    existing_interests = set(current.get("domain_interests", []))
    new_interests      = set()
    for domain, signals in domain_keywords.items():
        if any(s in query_lower for s in signals):
            new_interests.add(domain)

    added = new_interests - existing_interests
    if added:
        updates["domain_interests"] = list(existing_interests | new_interests)[:20]

    return updates
