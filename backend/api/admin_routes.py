# backend/api/admin_routes.py
"""
Admin-only routes: user management, workspace management, audit log viewer.
All routes require Permission.MANAGE_USERS (admin role).
"""
from fastapi import APIRouter, Depends, HTTPException
from backend.auth.rbac      import require_permission, Permission, extract_claims
from backend.auth.models    import UserCreateRequest, WorkspaceCreateRequest, UserRole, PlanTier, JWTClaims
from backend.auth.workspace import (
    create_workspace, get_workspace_by_slug,
    create_user, list_workspace_users, get_user_by_id,
)
from backend.audit.audit_logger import get_audit_log, get_audit_summary

router = APIRouter(prefix="/admin", tags=["admin"])

require_admin = require_permission(Permission.MANAGE_USERS)


# ── Workspace management ─────────────────────────────────────────────────────

@router.post("/workspaces")
async def create_workspace_endpoint(
    body:   WorkspaceCreateRequest,
    claims: JWTClaims = Depends(require_admin),
):
    ws = await create_workspace(
        name=body.name,
        slug=body.slug,
        plan_tier=body.plan_tier,
    )
    return {
        "created":          True,
        "workspace_id":     str(ws.id),
        "slug":             ws.slug,
        "chroma_collection": ws.chroma_collection,
        "mem0_namespace":   ws.mem0_namespace,
    }


@router.get("/workspaces/{slug}")
async def get_workspace_endpoint(
    slug:   str,
    claims: JWTClaims = Depends(require_admin),
):
    ws = await get_workspace_by_slug(slug)
    if not ws:
        raise HTTPException(404, "Workspace not found")
    return ws.dict()


# ── User management ─────────────────────────────────────────────────────────

@router.post("/users")
async def create_user_endpoint(
    body:   UserCreateRequest,
    claims: JWTClaims = Depends(require_admin),
):
    # Admin creates users in their own workspace unless specified
    workspace_id = body.workspace_id or claims.workspace_id
    user = await create_user(
        email=body.email,
        workspace_id=workspace_id,
        role=body.role,
        full_name=body.full_name,
        password=body.password,
    )
    return {
        "created":      True,
        "user_id":      str(user.id),
        "email":        user.email,
        "role":         user.role,
        "workspace_id": str(user.workspace_id),
    }


@router.get("/users")
async def list_users_endpoint(claims: JWTClaims = Depends(require_admin)):
    try:
        users = await list_workspace_users(claims.workspace_id)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("DB unavailable for admin/users: %s", e)
        return {"users": [], "total": 0, "unavailable": True}
    return {
        "users": [
            {
                "id":          str(u.id),
                "email":       u.email,
                "full_name":   u.full_name,
                "role":        u.role,
                "is_active":   u.is_active,
                "created_at":  u.created_at.isoformat(),
                "daily_queries": u.daily_query_count,
            }
            for u in users
        ],
        "total": len(users),
    }


@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role:    UserRole,
    claims:  JWTClaims = Depends(require_admin),
):
    from backend.prompts.registry import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET role = $1 WHERE id = $2",
            role.value, user_id,
        )
    return {"updated": True, "user_id": user_id, "role": role}


@router.patch("/users/{user_id}/tools")
async def update_user_tools(
    user_id: str,
    body:    dict,
    claims:  JWTClaims = Depends(require_admin),
):
    """Update which agents/tools a user can access. body = {"allowed_tools": ["social","ca-accounting"]}"""
    tools = body.get("allowed_tools", [])
    import json
    from backend.prompts.registry import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET allowed_tools = $1 WHERE id = $2",
            json.dumps(tools), user_id,
        )
    return {"updated": True, "user_id": user_id, "allowed_tools": tools}


@router.get("/usage")
async def get_workspace_usage(
    days:   int = 30,
    claims: JWTClaims = Depends(require_admin),
):
    """Workspace-level usage summary for admin dashboard."""
    from backend.prompts.registry import get_pool
    import json
    pool = await get_pool()
    workspace_id = claims.get("workspace_id", "")
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    tool_called,
                    COUNT(*) as calls,
                    SUM(input_tokens + output_tokens) as tokens,
                    SUM(cost_usd) as cost,
                    AVG(latency_ms) as avg_latency,
                    SUM(CASE WHEN error IS NOT NULL THEN 1 ELSE 0 END) as errors
                FROM audit_log
                WHERE workspace_id = $1
                  AND timestamp >= NOW() - ($2 * INTERVAL '1 day')
                GROUP BY tool_called
                ORDER BY calls DESC
                """,
                workspace_id, days,
            )
            total = await conn.fetchrow(
                """
                SELECT COUNT(*) as total_calls,
                       SUM(input_tokens + output_tokens) as total_tokens,
                       SUM(cost_usd) as total_cost,
                       COUNT(DISTINCT user_id) as active_users
                FROM audit_log
                WHERE workspace_id = $1
                  AND timestamp >= NOW() - ($2 * INTERVAL '1 day')
                """,
                workspace_id, days,
            )
        return {
            "period_days": days,
            "total_calls":   int(total["total_calls"] or 0),
            "total_tokens":  int(total["total_tokens"] or 0),
            "total_cost_usd": round(float(total["total_cost"] or 0), 4),
            "active_users":  int(total["active_users"] or 0),
            "by_agent": [
                {
                    "agent": r["tool_called"] or "unknown",
                    "calls": int(r["calls"]),
                    "tokens": int(r["tokens"] or 0),
                    "cost": round(float(r["cost"] or 0), 4),
                    "avg_latency_ms": round(float(r["avg_latency"] or 0)),
                    "errors": int(r["errors"]),
                }
                for r in rows
            ],
        }
    except Exception as e:
        return {
            "period_days": days, "total_calls": 0, "total_tokens": 0,
            "total_cost_usd": 0, "active_users": 0, "by_agent": [],
            "demo_mode": True, "note": str(e),
        }


@router.delete("/users/{user_id}")
async def deactivate_user(
    user_id: str,
    claims:  JWTClaims = Depends(require_admin),
):
    from backend.prompts.registry import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET is_active = false WHERE id = $1",
            user_id,
        )
    return {"deactivated": True, "user_id": user_id}


# ── Audit log ────────────────────────────────────────────────────────────────

@router.get("/audit")
async def get_audit_log_endpoint(
    user_id: str | None = None,
    action:  str | None = None,
    limit:   int        = 100,
    offset:  int        = 0,
    claims:  JWTClaims  = Depends(require_admin),
):
    """Paginated audit log for this workspace."""
    try:
        entries = await get_audit_log(
            workspace_id=claims.workspace_id,
            user_id=user_id,
            action=action,
            limit=min(limit, 500),
            offset=offset,
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("DB unavailable for audit-log: %s", e)
        return {"entries": [], "count": 0, "unavailable": True}
    return {"entries": entries, "count": len(entries)}


@router.get("/audit/summary")
async def get_audit_summary_endpoint(
    days:   int       = 7,
    claims: JWTClaims = Depends(require_admin),
):
    summary = await get_audit_summary(
        workspace_id=claims.workspace_id,
        days=days,
    )
    return summary


# ── Auth endpoints ────────────────────────────────────────────────────────────

@router.post("/token")
async def get_token(email: str, password: str):
    """
    Login endpoint — returns JWT with full workspace claims.
    Validates email/password against users table.
    """
    from backend.auth.workspace import get_pool
    from backend.api.auth       import verify_password, create_access_token
    from backend.auth.workspace import get_workspace_by_slug

    pool = await get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            """
            SELECT u.*, w.slug as ws_slug, w.plan_tier as ws_plan
            FROM users u
            JOIN workspaces w ON u.workspace_id = w.id
            WHERE u.email = $1 AND u.is_active = true
            """,
            email,
        )

    if not user or not user["hashed_password"]:
        raise HTTPException(401, "Invalid credentials")

    if not verify_password(password, user["hashed_password"]):
        raise HTTPException(401, "Invalid credentials")

    token = create_access_token(
        user_id=str(user["id"]),
        email=user["email"],
        workspace_id=str(user["workspace_id"]),
        workspace_slug=user["ws_slug"],
        role=UserRole(user["role"]),
        plan_tier=PlanTier(user["ws_plan"]),
    )
    return token


# ── Workspace domain whitelist management ─────────────────────────────────────

@router.get("/workspaces/{slug}/domains")
async def list_workspace_domains(
    slug:   str,
    claims: JWTClaims = Depends(require_admin),
):
    """List all allowed domains for a workspace."""
    from backend.prompts.registry import get_pool
    try:
        pool = await get_pool()
        rows = await pool.fetch(
            """
            SELECT id, domain, added_by, note, is_active, created_at
            FROM   workspace_domains
            WHERE  workspace_slug = $1
            ORDER  BY domain
            """,
            slug,
        )
        return {
            "workspace_slug": slug,
            "domains": [dict(r) for r in rows],
            "total": len(rows),
        }
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("workspace_domains fetch failed: %s", exc)
        return {"workspace_slug": slug, "domains": [], "total": 0, "unavailable": True}


@router.post("/workspaces/{slug}/domains")
async def add_workspace_domain(
    slug:   str,
    domain: str,
    note:   str    = "",
    claims: JWTClaims = Depends(require_admin),
):
    """Add a domain to the workspace whitelist."""
    from backend.prompts.registry import get_pool
    from backend.browser.domain_whitelist import invalidate_cache, ALWAYS_ALLOWED, ALWAYS_BLOCKED

    domain = domain.lower().strip().lstrip("*.")
    if not domain or len(domain) < 3:
        raise HTTPException(400, "Invalid domain")
    if domain in ALWAYS_BLOCKED:
        raise HTTPException(400, "Cannot whitelist a globally-blocked domain")

    try:
        pool = await get_pool()
        await pool.execute(
            """
            INSERT INTO workspace_domains (workspace_slug, domain, added_by, note)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (workspace_slug, domain) DO UPDATE
              SET is_active = true, note = EXCLUDED.note
            """,
            slug, domain, claims.email, note,
        )
        invalidate_cache(slug)
        return {"added": True, "workspace_slug": slug, "domain": domain}
    except Exception as exc:
        raise HTTPException(500, f"Failed to add domain: {exc}")


@router.delete("/workspaces/{slug}/domains/{domain}")
async def remove_workspace_domain(
    slug:   str,
    domain: str,
    claims: JWTClaims = Depends(require_admin),
):
    """Deactivate a domain from the workspace whitelist."""
    from backend.prompts.registry import get_pool
    from backend.browser.domain_whitelist import invalidate_cache

    try:
        pool = await get_pool()
        result = await pool.execute(
            """
            UPDATE workspace_domains
            SET    is_active = false
            WHERE  workspace_slug = $1 AND domain = $2
            """,
            slug, domain.lower().strip(),
        )
        invalidate_cache(slug)
        removed = result != "UPDATE 0"
        return {"removed": removed, "workspace_slug": slug, "domain": domain}
    except Exception as exc:
        raise HTTPException(500, f"Failed to remove domain: {exc}")