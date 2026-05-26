# backend/api/billing_routes.py
"""
Billing + Tier API (Feature 8).

Endpoints:
  GET  /billing/plans                      — list plan tiers and pricing
  GET  /billing/subscription               — current user subscription
  GET  /billing/usage                      — current month usage stats
  POST /billing/checkout/stripe            — create Stripe checkout session
  POST /billing/checkout/razorpay          — create Razorpay subscription
  POST /billing/webhook/stripe             — Stripe webhook receiver
  POST /billing/webhook/razorpay           — Razorpay webhook receiver
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from backend.api.auth       import verify_token
from backend.billing.billing_manager import (
    TIER_LIMITS,
    check_feature_access,
    create_razorpay_subscription,
    create_stripe_checkout,
    get_subscription,
    get_tier_limits,
    get_usage,
    handle_razorpay_webhook,
    handle_stripe_webhook,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/billing", tags=["billing"])


# ── Models ────────────────────────────────────────────────────────────────────

class StripeCheckoutRequest(BaseModel):
    plan_tier:   str = Field(..., pattern="^(pro|enterprise)$")
    success_url: str = Field(default="http://localhost:5173/billing/success")
    cancel_url:  str = Field(default="http://localhost:5173/billing/cancel")


class RazorpayCheckoutRequest(BaseModel):
    plan_tier: str = Field(..., pattern="^(pro|enterprise)$")
    phone:     str = Field(default="")


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get(
    "/plans",
    summary="List billing plans",
    response_model=dict,
)
async def list_plans():
    """Return all available plans with limits and pricing. Public endpoint."""
    plans = []
    for tier, limits in TIER_LIMITS.items():
        plans.append({
            "tier":       tier,
            "name":       {"free": "Free", "pro": "Pro", "enterprise": "Enterprise"}[tier],
            "price_inr":  limits["price_inr"],
            "price_usd":  limits["price_usd"],
            "limits": {
                "api_calls":  limits["api_calls"],
                "tokens":     limits["tokens"],
                "image_gens": limits["image_gens"],
                "audio_mins": limits["audio_mins"],
                "storage_mb": limits["storage_mb"],
            },
            "features": {
                "image_gen":     check_feature_access(tier, "image_gen"),
                "audio":         check_feature_access(tier, "audio"),
                "hitl":          check_feature_access(tier, "hitl"),
                "a2a":           check_feature_access(tier, "a2a"),
                "scheduler":     check_feature_access(tier, "scheduler"),
                "advanced_rag":  check_feature_access(tier, "advanced_rag"),
                "custom_agents": check_feature_access(tier, "custom_agents"),
            },
        })
    return {"plans": plans}


@router.get(
    "/subscription",
    summary="Get current subscription",
    response_model=dict,
)
async def current_subscription(token: dict = Depends(verify_token)):
    """Return the caller's active subscription and plan limits."""
    user_id   = token.get("sub", "anonymous")
    sub       = await get_subscription(user_id)
    plan      = sub.get("plan_tier", "free")
    limits    = get_tier_limits(plan)
    usage     = await get_usage(user_id)

    return {
        "user_id":    user_id,
        "plan_tier":  plan,
        "status":     sub.get("status", "active"),
        "provider":   sub.get("provider"),
        "limits":     limits,
        "usage":      usage,
        "period_end": str(sub.get("current_period_end", "")),
    }


@router.get(
    "/usage",
    summary="Current month usage",
    response_model=dict,
)
async def current_usage(token: dict = Depends(verify_token)):
    """Return caller's current month resource usage."""
    user_id = token.get("sub", "anonymous")
    plan    = token.get("plan_tier", "free")
    usage   = await get_usage(user_id)
    limits  = get_tier_limits(plan)

    return {
        "user_id": user_id,
        "month":   __import__("datetime").date.today().strftime("%Y-%m"),
        "usage":   usage,
        "limits":  limits,
        "percent": {
            k: (
                round(usage.get(k, 0) / limits[k] * 100, 1)
                if limits.get(k, 0) > 0 else 0
            )
            for k in ["api_calls", "tokens", "image_gens"]
        },
    }


@router.post(
    "/checkout/stripe",
    summary="Create Stripe checkout session",
    response_model=dict,
)
async def stripe_checkout(
    req:   StripeCheckoutRequest,
    token: dict = Depends(verify_token),
):
    user_id = token.get("sub", "anonymous")
    email   = token.get("email", "")

    try:
        url = await create_stripe_checkout(
            user_id=user_id,
            plan_tier=req.plan_tier,
            email=email,
            success_url=req.success_url,
            cancel_url=req.cancel_url,
        )
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {"checkout_url": url, "plan_tier": req.plan_tier}


@router.post(
    "/checkout/razorpay",
    summary="Create Razorpay subscription (INR)",
    response_model=dict,
)
async def razorpay_checkout(
    req:   RazorpayCheckoutRequest,
    token: dict = Depends(verify_token),
):
    user_id = token.get("sub", "anonymous")
    email   = token.get("email", "")

    try:
        result = await create_razorpay_subscription(
            user_id=user_id,
            plan_tier=req.plan_tier,
            email=email,
            phone=req.phone or None,
        )
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return result


@router.post(
    "/webhook/stripe",
    summary="Stripe webhook receiver",
    status_code=status.HTTP_200_OK,
)
async def stripe_webhook(request: Request):
    """
    Stripe sends payment events here.
    Verifies HMAC signature and updates subscription records.
    """
    payload    = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        result = await handle_stripe_webhook(payload, sig_header)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid Stripe webhook signature.")
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Billing service configuration error.")

    return result


@router.post(
    "/webhook/razorpay",
    summary="Razorpay webhook receiver",
    status_code=status.HTTP_200_OK,
)
async def razorpay_webhook(request: Request):
    """
    Razorpay sends subscription events here.
    Verifies HMAC signature and updates subscription records.
    """
    payload   = await request.json()
    signature = request.headers.get("x-razorpay-signature", "")

    try:
        result = await handle_razorpay_webhook(payload, signature)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid Razorpay webhook signature.")

    return result
