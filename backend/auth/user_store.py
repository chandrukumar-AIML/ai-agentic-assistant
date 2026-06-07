"""
Lightweight JSON-file-backed user + entitlements store.

Why a file store (not Postgres): the platform must run on minimal infra
(e.g. Render free tier) where DATABASE_URL may be absent. This store gives a
real, working multi-tenant auth + per-client tool-access layer with zero DB
dependency. When a Postgres connection is available the richer admin_routes.py
path can be used instead; the two are independent.

NOTE (durability): on ephemeral filesystems (Render free) this file resets on
redeploy. Set AAA_USER_STORE to a path on a mounted persistent disk for
durability, or migrate to Postgres for production at scale.

Each user record:
  email, password_hash, full_name, role, plan_tier, allowed_tools (list[str]),
  is_active, created_at, total_queries, daily_query_count, last_query_day
"""
from __future__ import annotations

import json
import os
import threading
from datetime import date, datetime, timezone
from pathlib import Path

from backend.api.auth import hash_password, verify_password

# ── Canonical tool catalog — ids MUST match frontend PageId values ──────────────
TOOL_CATALOG: list[dict] = [
    # AI Core
    {"id": "compliance", "label": "Guardian / Compliance", "category": "AI Core"},
    {"id": "hitl",       "label": "HITL Approvals",         "category": "AI Core"},
    {"id": "output",     "label": "Output Generator",       "category": "AI Core"},
    {"id": "ab-test",    "label": "A/B Testing",            "category": "AI Core"},
    {"id": "scheduler",  "label": "Task Scheduler",         "category": "AI Core"},
    # Verticals
    {"id": "agri",        "label": "AgriTech",        "category": "Verticals"},
    {"id": "legal",       "label": "Legal Research",  "category": "Verticals"},
    {"id": "cybersec",    "label": "Cybersecurity",   "category": "Verticals"},
    {"id": "receptionist","label": "Receptionist",    "category": "Verticals"},
    {"id": "form-reader", "label": "Form Reader",     "category": "Verticals"},
    {"id": "email",       "label": "Email Manager",   "category": "Verticals"},
    {"id": "sales",       "label": "Sales & CRM",     "category": "Verticals"},
    {"id": "accountant",  "label": "Accountant",      "category": "Verticals"},
    {"id": "hr",          "label": "HR Assistant",    "category": "Verticals"},
    {"id": "social",      "label": "Social Media",    "category": "Verticals"},
    {"id": "analyst",     "label": "Data Analyst",    "category": "Verticals"},
    {"id": "devops",      "label": "DevOps Engineer", "category": "Verticals"},
    {"id": "qa",          "label": "QA Engineer",     "category": "Verticals"},
    {"id": "project",     "label": "Project Manager", "category": "Verticals"},
    {"id": "code",        "label": "Code Assistant",  "category": "Verticals"},
    {"id": "ml",          "label": "ML Engineer",     "category": "Verticals"},
    {"id": "dba",         "label": "DBA",             "category": "Verticals"},
    {"id": "techlead",    "label": "Tech Lead",       "category": "Verticals"},
    {"id": "healthcare",  "label": "Healthcare",      "category": "Verticals"},
    {"id": "realestate",  "label": "Real Estate",     "category": "Verticals"},
    {"id": "edtech",      "label": "EdTech",          "category": "Verticals"},
    # Knowledge / integrations
    {"id": "knowledge-base", "label": "Knowledge Base", "category": "Settings"},
    {"id": "webhooks",       "label": "Webhooks",       "category": "Settings"},
]

ALL_TOOL_IDS: list[str] = [t["id"] for t in TOOL_CATALOG]

# Pages every authenticated user always sees (never gated)
ALWAYS_ALLOWED: list[str] = ["dashboard", "chat", "billing", "settings"]

# Default tool set for a brand-new free signup
DEFAULT_FREE_TOOLS: list[str] = ["agri", "legal", "code", "analyst", "knowledge-base"]

_STORE_PATH = Path(os.getenv("AAA_USER_STORE", "data/users.json"))
_lock = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _seed() -> dict:
    """Initial users created on first run."""
    return {
        "admin@agentic.local": {
            "email": "admin@agentic.local",
            "password_hash": hash_password("admin123"),
            "full_name": "Platform Admin",
            "role": "admin",
            "plan_tier": "enterprise",
            "allowed_tools": list(ALL_TOOL_IDS),
            "is_active": True,
            "created_at": _now(),
            "total_queries": 0,
            "daily_query_count": 0,
            "last_query_day": "",
        },
        "demo@agentic.local": {
            "email": "demo@agentic.local",
            "password_hash": hash_password("demo123"),
            "full_name": "Demo Client",
            "role": "user",
            "plan_tier": "free",
            "allowed_tools": list(DEFAULT_FREE_TOOLS),
            "is_active": True,
            "created_at": _now(),
            "total_queries": 0,
            "daily_query_count": 0,
            "last_query_day": "",
        },
    }


def _load() -> dict:
    if _STORE_PATH.exists():
        try:
            return json.loads(_STORE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    users = _seed()
    _save(users)
    return users


def _save(users: dict) -> None:
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = _STORE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(users, indent=2), encoding="utf-8")
    tmp.replace(_STORE_PATH)


def _public(rec: dict) -> dict:
    """Strip the password hash for API responses."""
    return {k: v for k, v in rec.items() if k != "password_hash"}


# ── Public API ──────────────────────────────────────────────────────────────

def get_user(email: str) -> dict | None:
    with _lock:
        return _load().get((email or "").lower().strip())


def authenticate(email: str, password: str) -> dict | None:
    rec = get_user(email)
    if not rec or not rec.get("is_active"):
        return None
    if not verify_password(password, rec["password_hash"]):
        return None
    return rec


def create_user(
    email: str,
    password: str,
    full_name: str = "",
    role: str = "user",
    plan_tier: str = "free",
    allowed_tools: list[str] | None = None,
) -> dict:
    email = (email or "").lower().strip()
    with _lock:
        users = _load()
        if email in users:
            raise ValueError("A user with this email already exists.")
        rec = {
            "email": email,
            "password_hash": hash_password(password),
            "full_name": full_name or email.split("@")[0].title(),
            "role": role,
            "plan_tier": plan_tier,
            "allowed_tools": allowed_tools if allowed_tools is not None else list(DEFAULT_FREE_TOOLS),
            "is_active": True,
            "created_at": _now(),
            "total_queries": 0,
            "daily_query_count": 0,
            "last_query_day": "",
        }
        users[email] = rec
        _save(users)
        return rec


def list_users() -> list[dict]:
    with _lock:
        return [_public(u) for u in _load().values()]


def set_tools(email: str, tools: list[str]) -> dict:
    email = (email or "").lower().strip()
    clean = [t for t in tools if t in ALL_TOOL_IDS]
    with _lock:
        users = _load()
        if email not in users:
            raise ValueError("User not found.")
        users[email]["allowed_tools"] = clean
        _save(users)
        return _public(users[email])


def set_plan(email: str, plan_tier: str) -> dict:
    email = (email or "").lower().strip()
    if plan_tier not in ("free", "pro", "enterprise"):
        raise ValueError("Invalid plan tier.")
    with _lock:
        users = _load()
        if email not in users:
            raise ValueError("User not found.")
        users[email]["plan_tier"] = plan_tier
        _save(users)
        return _public(users[email])


def set_active(email: str, is_active: bool) -> dict:
    email = (email or "").lower().strip()
    with _lock:
        users = _load()
        if email not in users:
            raise ValueError("User not found.")
        users[email]["is_active"] = is_active
        _save(users)
        return _public(users[email])


def record_usage(email: str) -> None:
    """Increment usage counters; resets the daily count when the day rolls over."""
    email = (email or "").lower().strip()
    today = date.today().isoformat()
    with _lock:
        users = _load()
        rec = users.get(email)
        if not rec:
            return
        if rec.get("last_query_day") != today:
            rec["daily_query_count"] = 0
            rec["last_query_day"] = today
        rec["daily_query_count"] += 1
        rec["total_queries"] = rec.get("total_queries", 0) + 1
        _save(users)
