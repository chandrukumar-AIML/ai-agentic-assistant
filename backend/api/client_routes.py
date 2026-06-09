"""
Client + entitlements routes (file-store backed, DB-free).

Endpoints:
  POST /auth/signup            — self-serve signup (role=user, free plan)
  GET  /auth/me                — current user's profile + allowed_tools
  GET  /tools/catalog          — full tool catalog + always-allowed list
  GET  /clients                — [admin] list all clients
  POST /clients/{email}/tools  — [admin] set a client's allowed tools
  POST /clients/{email}/plan   — [admin] set a client's plan tier
  POST /clients/{email}/active — [admin] activate/deactivate a client
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field

from backend.api.auth   import decode_token, create_access_token, limiter
from backend.auth.models import UserRole, PlanTier
from backend.config     import get_settings
from backend.auth       import user_store

logger   = logging.getLogger(__name__)
settings = get_settings()
router   = APIRouter(tags=["clients"])


# ── helpers ──────────────────────────────────────────────────────────────────

def _claims(request: Request) -> dict:
    """Decode the real bearer token; fall back to a dev admin in development."""
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        tok = auth.split(" ", 1)[1].strip()
        if tok:
            try:
                return decode_token(tok)
            except HTTPException:
                pass
    if settings.app_env == "development":
        return {"sub": "dev", "email": "admin@agentic.local", "role": "admin", "plan_tier": "enterprise"}
    raise HTTPException(401, "Authentication required")


def _require_admin(request: Request) -> dict:
    claims = _claims(request)
    if claims.get("role") != "admin":
        raise HTTPException(403, "Admin access required")
    return claims


def _profile_for(email: str, claims: dict) -> dict:
    """Return the store profile, or a synthetic admin profile for dev/unknown users."""
    rec = user_store.get_user(email)
    if rec:
        return user_store._public(rec)  # noqa: SLF001 — internal helper, same package intent
    # Unknown (e.g. dev token) → full-access admin so local dev keeps working
    return {
        "email": email,
        "full_name": email.split("@")[0].title(),
        "role": claims.get("role", "admin"),
        "plan_tier": claims.get("plan_tier", "enterprise"),
        "allowed_tools": list(user_store.ALL_TOOL_IDS),
        "is_active": True,
        "total_queries": 0,
        "daily_query_count": 0,
    }


# ── request models ─────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    email:     EmailStr
    password:  str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(default="", max_length=200)


class ToolsRequest(BaseModel):
    tools: list[str] = Field(default_factory=list)


class PlanRequest(BaseModel):
    plan_tier: str = Field(..., pattern="^(free|pro|enterprise)$")


class ActiveRequest(BaseModel):
    is_active: bool


# ── auth: signup + me ──────────────────────────────────────────────────────────

@router.post("/auth/signup", summary="Self-serve client signup")
@limiter.limit("5/minute")
async def signup(request: Request, body: SignupRequest):
    try:
        rec = user_store.create_user(
            email=body.email,
            password=body.password,
            full_name=body.full_name,
        )
    except ValueError as e:
        raise HTTPException(409, str(e))

    token = create_access_token(
        user_id        = rec["email"],
        email          = rec["email"],
        workspace_id   = "ws-default",
        workspace_slug = "default",
        role           = UserRole(rec["role"]),
        plan_tier      = PlanTier(rec["plan_tier"]),
    )
    return {
        "access_token": token.access_token,
        "token_type":   "bearer",
        "expires_in":   token.expires_in,
        "profile":      user_store._public(rec),  # noqa: SLF001
    }


@router.get("/auth/me", summary="Current user profile + tool entitlements")
async def me(request: Request):
    claims  = _claims(request)
    profile = _profile_for(claims.get("email", ""), claims)
    return {
        "profile":        profile,
        "always_allowed": user_store.ALWAYS_ALLOWED,
        "is_admin":       profile.get("role") == "admin",
        "demo_mode":      bool(getattr(settings, "demo_mode", False)),
    }


@router.get("/config", summary="Public runtime config (demo flag, env)")
async def public_config():
    """Public — lets the login screen show a demo banner before auth."""
    return {
        "demo_mode": bool(getattr(settings, "demo_mode", False)),
        "app_env":   settings.app_env,
    }


@router.get("/tools/catalog", summary="Full catalog of gateable tools")
async def tools_catalog(request: Request):
    _claims(request)  # require auth
    return {
        "catalog":        user_store.TOOL_CATALOG,
        "always_allowed": user_store.ALWAYS_ALLOWED,
    }


# ── Integration status — which real integrations are LIVE vs need API keys ──────
# Maps each external integration to the settings attribute(s) that activate it.
# Never exposes key VALUES — only whether they are configured (boolean).
_INTEGRATIONS: list[dict] = [
    {"id": "ollama",       "name": "Ollama (local LLM)",   "vertical": "Core LLM",     "unlocks": "On-prem LLM inference (llama3.2)",      "keys": [], "always_on": True},
    {"id": "openai",       "name": "OpenAI",               "vertical": "Core LLM",     "unlocks": "Cloud LLM fallback + GPT-4o vision",    "keys": ["openai_api_key"]},
    {"id": "agmarknet",    "name": "Agmarknet (data.gov.in)", "vertical": "AgriTech",  "unlocks": "Live mandi commodity prices",           "keys": [], "always_on": True},
    {"id": "openweather",  "name": "OpenWeatherMap",        "vertical": "AgriTech",     "unlocks": "5-day weather advisory for farms",      "keys": ["openweather_api_key"]},
    {"id": "indiankanoon", "name": "IndianKanoon",          "vertical": "Legal",        "unlocks": "Indian case-law search",                "keys": ["indiankanoon_api_key"]},
    {"id": "hubspot",      "name": "HubSpot CRM",           "vertical": "Sales",        "unlocks": "Sync contacts & deals to HubSpot",      "keys": ["hubspot_api_key"]},
    {"id": "salesforce",   "name": "Salesforce",            "vertical": "Sales",        "unlocks": "Push leads to Salesforce",              "keys": ["salesforce_access_token"]},
    {"id": "clearbit",     "name": "Clearbit",              "vertical": "Sales",        "unlocks": "Auto-enrich leads from email",          "keys": ["clearbit_api_key"]},
    {"id": "twitter",      "name": "Twitter / X",           "vertical": "Social Media", "unlocks": "Auto-publish posts to X",               "keys": ["twitter_api_key", "twitter_api_secret", "twitter_access_token", "twitter_access_token_secret"]},
    {"id": "linkedin",     "name": "LinkedIn",              "vertical": "Social Media", "unlocks": "Auto-publish posts to LinkedIn",        "keys": ["linkedin_author_urn"]},
    {"id": "buffer",       "name": "Buffer",                "vertical": "Social Media", "unlocks": "Schedule posts across channels",        "keys": ["buffer_access_token"]},
    {"id": "twilio",       "name": "Twilio",                "vertical": "Receptionist", "unlocks": "Inbound voice + WhatsApp handling",     "keys": ["twilio_account_sid", "twilio_auth_token"]},
    {"id": "calendly",     "name": "Calendly",              "vertical": "Receptionist", "unlocks": "Appointment booking links",             "keys": ["calendly_api_key"]},
    {"id": "sendgrid",     "name": "SendGrid",              "vertical": "Email Manager","unlocks": "Transactional email delivery",          "keys": ["sendgrid_api_key"]},
    {"id": "docusign",     "name": "DocuSign",              "vertical": "HR",           "unlocks": "E-sign dispatch for offer letters",     "keys": ["docusign_access_token"]},
    {"id": "razorpay",     "name": "Razorpay",              "vertical": "Billing",      "unlocks": "India checkout — UPI / cards / NetBanking", "keys": ["razorpay_key_id", "razorpay_key_secret"]},
    {"id": "stripe",       "name": "Stripe",                "vertical": "Billing",      "unlocks": "Global checkout — USD / EUR / GBP",     "keys": ["stripe_secret_key"]},
    {"id": "tavily",       "name": "Tavily",                "vertical": "Knowledge",    "unlocks": "Live web search for RAG",               "keys": ["tavily_api_key"]},
    {"id": "elevenlabs",   "name": "ElevenLabs",            "vertical": "Voice",        "unlocks": "Premium text-to-speech",                "keys": ["elevenlabs_api_key"]},
]


@router.get("/integrations/status", summary="Which real integrations are live vs need API keys")
async def integrations_status(request: Request):
    _claims(request)  # require auth
    out = []
    for it in _INTEGRATIONS:
        configured = it.get("always_on", False) or all(
            bool(getattr(settings, k, None)) for k in it["keys"]
        )
        out.append({
            "id":         it["id"],
            "name":       it["name"],
            "vertical":   it["vertical"],
            "unlocks":    it["unlocks"],
            "configured": configured,
            "always_on":  it.get("always_on", False),
            "env_vars":   [k.upper() for k in it["keys"]],
        })
    live = sum(1 for x in out if x["configured"])
    return {"integrations": out, "live": live, "total": len(out)}


# ── admin: client management ─────────────────────────────────────────────────

@router.get("/clients", summary="[admin] List all clients")
async def list_clients(request: Request):
    _require_admin(request)
    users = user_store.list_users()
    return {"clients": users, "total": len(users)}


@router.post("/clients/{email}/tools", summary="[admin] Set a client's allowed tools")
async def set_client_tools(email: str, body: ToolsRequest, request: Request):
    _require_admin(request)
    try:
        return {"updated": True, "client": user_store.set_tools(email, body.tools)}
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/clients/{email}/plan", summary="[admin] Set a client's plan tier")
async def set_client_plan(email: str, body: PlanRequest, request: Request):
    _require_admin(request)
    try:
        return {"updated": True, "client": user_store.set_plan(email, body.plan_tier)}
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/clients/{email}/active", summary="[admin] Activate/deactivate a client")
async def set_client_active(email: str, body: ActiveRequest, request: Request):
    _require_admin(request)
    try:
        return {"updated": True, "client": user_store.set_active(email, body.is_active)}
    except ValueError as e:
        raise HTTPException(404, str(e))
