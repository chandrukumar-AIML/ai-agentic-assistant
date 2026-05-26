# backend/billing/billing_manager.py
"""
Stripe / Razorpay Billing + Tier Enforcement (Feature 8).

Plans:
  FREE       — 100 API calls/month, 50k tokens, no images/audio
  PRO        — ₹999/month, 5k calls, 2M tokens, 50 images, 60min audio
  ENTERPRISE — Custom / unlimited (manual/Stripe)

Stripe handles international payments.
Razorpay handles Indian payments (INR ₹999/month).

Usage enforcement is checked in-process via Redis counter (fast path)
and synced to PostgreSQL daily.
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime, timezone
from typing import Optional

from backend.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()


# ── Tier definitions ──────────────────────────────────────────────────────────

TIER_LIMITS = {
    "free": {
        "api_calls":   100,
        "tokens":      50_000,
        "image_gens":  0,
        "audio_mins":  0.0,
        "storage_mb":  100.0,
        "price_inr":   0,
        "price_usd":   0,
    },
    "pro": {
        "api_calls":   5_000,
        "tokens":      2_000_000,
        "image_gens":  50,
        "audio_mins":  60.0,
        "storage_mb":  5_000.0,
        "price_inr":   999,
        "price_usd":   12,
        "stripe_price_id":   getattr(settings, "stripe_pro_price_id",  "price_pro_monthly"),
        "razorpay_plan_id":  getattr(settings, "razorpay_pro_plan_id", "plan_pro_monthly"),
    },
    "enterprise": {
        "api_calls":   -1,    # unlimited
        "tokens":      -1,
        "image_gens":  -1,
        "audio_mins":  -1.0,
        "storage_mb":  -1.0,
        "price_inr":   -1,    # custom
        "price_usd":   -1,
    },
}

TIER_ORDER = {"free": 0, "pro": 1, "enterprise": 2}


def get_tier_limits(plan_tier: str) -> dict:
    return TIER_LIMITS.get(plan_tier, TIER_LIMITS["free"])


def check_feature_access(plan_tier: str, feature: str) -> bool:
    """
    Quick boolean check for feature gate.
    feature ∈ {"image_gen", "audio", "hitl", "a2a", "scheduler",
               "advanced_rag", "custom_agents", "white_label"}
    """
    feature_tiers = {
        "image_gen":     {"pro", "enterprise"},
        "audio":         {"pro", "enterprise"},
        "hitl":          {"pro", "enterprise"},
        "a2a":           {"enterprise"},
        "scheduler":     {"pro", "enterprise"},
        "advanced_rag":  {"pro", "enterprise"},
        "custom_agents": {"enterprise"},
        "white_label":   {"enterprise"},
    }
    allowed = feature_tiers.get(feature, {"free", "pro", "enterprise"})
    return plan_tier in allowed


# ── Redis usage counters (fast path) ────────────────────────────────────────

def _usage_key(user_id: str, metric: str) -> str:
    month = date.today().strftime("%Y-%m")
    return f"usage:{user_id}:{month}:{metric}"


async def increment_usage(user_id: str, metric: str, amount: int = 1) -> int:
    """
    Increment a usage counter in Redis. Returns new total.
    metric ∈ {api_calls, tokens, image_gens, audio_mins}
    """
    try:
        from backend.session.redis_client import get_redis
        redis  = await get_redis()
        key    = _usage_key(user_id, metric)
        new_val = await redis.incrby(key, amount)
        # Expire at end of month + 2 days buffer
        import calendar
        today  = date.today()
        days   = calendar.monthrange(today.year, today.month)[1] - today.day + 2
        await redis.expire(key, days * 86400)
        return new_val
    except Exception as e:
        logger.debug("increment_usage Redis error (non-fatal): %s", e)
        return 0


async def get_usage(user_id: str) -> dict:
    """Get current month usage from Redis."""
    metrics = ["api_calls", "tokens", "image_gens", "audio_mins"]
    usage   = {}
    try:
        from backend.session.redis_client import get_redis
        redis = await get_redis()
        for metric in metrics:
            raw = await redis.get(_usage_key(user_id, metric))
            usage[metric] = int(raw or 0)
    except Exception:
        usage = {m: 0 for m in metrics}
    return usage


async def check_limit(user_id: str, plan_tier: str, metric: str) -> bool:
    """
    Returns True if user is within their plan limit for the metric.
    Returns False if limit exceeded.
    """
    limits = get_tier_limits(plan_tier)
    cap    = limits.get(metric, 0)
    if cap == -1:
        return True   # unlimited

    usage  = await get_usage(user_id)
    return usage.get(metric, 0) < cap


# ── Stripe checkout ──────────────────────────────────────────────────────────

async def create_stripe_checkout(
    user_id:    str,
    plan_tier:  str,
    email:      str,
    success_url: str,
    cancel_url:  str,
) -> str:
    """
    Create a Stripe Checkout session for plan upgrade.
    Returns the checkout URL.
    """
    stripe_key = getattr(settings, "stripe_secret_key", None)
    if not stripe_key:
        raise RuntimeError("STRIPE_SECRET_KEY not configured")

    try:
        import stripe
        stripe.api_key = stripe_key

        price_id = TIER_LIMITS.get(plan_tier, {}).get("stripe_price_id", "")
        if not price_id:
            raise ValueError(f"No Stripe price configured for tier: {plan_tier}")

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            customer_email=email,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url,
            metadata={"user_id": user_id, "plan_tier": plan_tier},
        )
        logger.info("Stripe checkout created for user %s → %s", user_id, plan_tier)
        return session.url
    except Exception as e:
        logger.error("Stripe checkout failed: %s", e)
        raise RuntimeError(f"Stripe checkout creation failed: {e}") from e


# ── Razorpay subscription ────────────────────────────────────────────────────

async def create_razorpay_subscription(
    user_id:   str,
    plan_tier: str,
    email:     str,
    phone:     Optional[str] = None,
) -> dict:
    """
    Create a Razorpay subscription for Indian customers.
    Returns dict with subscription_id and payment_link.
    """
    rp_key    = getattr(settings, "razorpay_key_id",     None)
    rp_secret = getattr(settings, "razorpay_key_secret", None)
    if not rp_key or not rp_secret:
        raise RuntimeError("RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET not configured")

    try:
        import razorpay
        client  = razorpay.Client(auth=(rp_key, rp_secret))
        plan_id = TIER_LIMITS.get(plan_tier, {}).get("razorpay_plan_id", "")
        if not plan_id:
            raise ValueError(f"No Razorpay plan configured for tier: {plan_tier}")

        sub = client.subscription.create({
            "plan_id":       plan_id,
            "customer_notify": 1,
            "quantity":      1,
            "total_count":   12,   # 12 monthly billing cycles
            "notes":         {"user_id": user_id, "plan_tier": plan_tier},
        })
        logger.info("Razorpay subscription created for user %s → %s", user_id, plan_tier)
        return {
            "subscription_id": sub["id"],
            "short_url":       sub.get("short_url", ""),
            "plan_tier":       plan_tier,
            "amount_inr":      TIER_LIMITS[plan_tier]["price_inr"],
        }
    except Exception as e:
        logger.error("Razorpay subscription failed: %s", e)
        raise RuntimeError(f"Razorpay subscription creation failed: {e}") from e


# ── Webhook handlers ─────────────────────────────────────────────────────────

async def handle_stripe_webhook(payload: bytes, sig_header: str) -> dict:
    """
    Verify and process Stripe webhook events.
    Updates billing_subscriptions table on payment events.
    """
    webhook_secret = getattr(settings, "stripe_webhook_secret", None)
    if not webhook_secret:
        raise RuntimeError("STRIPE_WEBHOOK_SECRET not configured")

    try:
        import stripe
        stripe.api_key = getattr(settings, "stripe_secret_key", "")
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except Exception as e:
        raise ValueError(f"Stripe webhook verification failed: {e}") from e

    event_type = event["type"]
    data       = event["data"]["object"]

    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:

            if event_type == "checkout.session.completed":
                user_id   = data.get("metadata", {}).get("user_id", "")
                plan_tier = data.get("metadata", {}).get("plan_tier", "pro")
                sub_id    = data.get("subscription", "")
                cust_id   = data.get("customer", "")

                await conn.execute(
                    """
                    INSERT INTO billing_subscriptions
                        (user_id, plan_tier, provider, provider_sub_id, provider_cust_id, status)
                    VALUES ($1, $2, 'stripe', $3, $4, 'active')
                    ON CONFLICT (user_id) DO UPDATE
                    SET plan_tier=EXCLUDED.plan_tier, provider_sub_id=EXCLUDED.provider_sub_id,
                        provider_cust_id=EXCLUDED.provider_cust_id, status='active', updated_at=NOW()
                    """,
                    user_id, plan_tier, sub_id, cust_id,
                )
                logger.info("Stripe: upgraded user %s to %s", user_id, plan_tier)

            elif event_type in ("customer.subscription.deleted", "customer.subscription.paused"):
                sub_id = data.get("id", "")
                await conn.execute(
                    """
                    UPDATE billing_subscriptions
                    SET plan_tier='free', status='cancelled', updated_at=NOW()
                    WHERE provider_sub_id=$1
                    """,
                    sub_id,
                )
                logger.info("Stripe: subscription %s cancelled/paused → downgraded to free", sub_id)

    except Exception as e:
        logger.error("Stripe webhook DB update failed: %s", e)

    return {"status": "processed", "event_type": event_type}


async def handle_razorpay_webhook(payload: dict, signature: str) -> dict:
    """Verify and process Razorpay webhook events."""
    rp_secret = getattr(settings, "razorpay_key_secret", None)
    if not rp_secret:
        raise RuntimeError("RAZORPAY_KEY_SECRET not configured")

    try:
        import razorpay
        razorpay.utility.verify_webhook_signature(
            json.dumps(payload), signature, rp_secret
        )
    except Exception as e:
        raise ValueError(f"Razorpay webhook verification failed: {e}") from e

    event = payload.get("event", "")
    sub   = payload.get("payload", {}).get("subscription", {}).get("entity", {})
    notes = sub.get("notes", {})
    user_id   = notes.get("user_id", "")
    plan_tier = notes.get("plan_tier", "pro")

    if event == "subscription.activated":
        try:
            pool = await _get_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO billing_subscriptions
                        (user_id, plan_tier, provider, provider_sub_id, status)
                    VALUES ($1, $2, 'razorpay', $3, 'active')
                    ON CONFLICT (user_id) DO UPDATE
                    SET plan_tier=EXCLUDED.plan_tier, provider_sub_id=EXCLUDED.provider_sub_id,
                        status='active', updated_at=NOW()
                    """,
                    user_id, plan_tier, sub.get("id", ""),
                )
            logger.info("Razorpay: activated %s for user %s", plan_tier, user_id)
        except Exception as e:
            logger.error("Razorpay webhook DB update failed: %s", e)

    return {"status": "processed", "event": event}


async def get_subscription(user_id: str) -> dict:
    """Get current subscription for a user."""
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT plan_tier, status, provider, current_period_end FROM billing_subscriptions WHERE user_id=$1",
                user_id,
            )
        if row:
            return dict(row)
    except Exception as e:
        logger.debug("get_subscription DB error: %s", e)
    return {"plan_tier": "free", "status": "active", "provider": None, "current_period_end": None}


async def _get_pool():
    from backend.prompts.registry import get_pool
    return await get_pool()
