# backend/api/hitl_routes.py
"""
HITL (Human-in-the-Loop) Approval REST API.

Endpoints:
  POST /hitl/request                       — create approval request (agent-facing)
  GET  /hitl/pending                       — list pending approvals (reviewer dashboard)
  GET  /hitl/{approval_id}                 — get single approval detail
  POST /hitl/{approval_id}/decision        — approve or reject
  GET  /hitl/history                       — paginated decision history
  POST /hitl/expire-sweep                  — admin: manually trigger expiry sweep
"""
from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.api.auth      import verify_token
from backend.hitl.hitl_manager import (
    decide_approval,
    expire_stale_approvals,
    get_approval,
    list_pending,
    request_approval,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/hitl", tags=["hitl"])


# ── Request / Response models ─────────────────────────────────────────────────

class ApprovalRequest(BaseModel):
    action_type:     str  = Field(..., min_length=1, max_length=100)
    action_payload:  dict = Field(default_factory=dict)
    context_summary: str  = Field(..., min_length=1, max_length=2000)
    session_id:      str  = Field(default="")
    reviewer_email:  Optional[str] = Field(default=None)


class DecisionRequest(BaseModel):
    decision:     str = Field(..., pattern="^(approved|rejected)$")
    reviewer_note: str = Field(default="", max_length=1000)


class ApprovalResponse(BaseModel):
    approval_id:     str
    action_type:     str
    context_summary: str
    status:          str
    expires_at:      str
    created_at:      str
    reviewer_id:     Optional[str]
    reviewer_note:   Optional[str]
    decided_at:      Optional[str]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _serialize_approval(row: dict) -> dict:
    """Convert DB row to API-safe dict (timestamps → ISO strings)."""
    return {
        "approval_id":     str(row.get("approval_id", "")),
        "action_type":     row.get("action_type", ""),
        "context_summary": row.get("context_summary", ""),
        "status":          row.get("status", ""),
        "expires_at":      row["expires_at"].isoformat() if row.get("expires_at") else None,
        "created_at":      row["created_at"].isoformat() if row.get("created_at") else None,
        "reviewer_id":     row.get("reviewer_id"),
        "reviewer_note":   row.get("reviewer_note"),
        "decided_at":      row["decided_at"].isoformat() if row.get("decided_at") else None,
        "session_id":      row.get("session_id"),
        "user_id":         row.get("user_id"),
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post(
    "/request",
    summary="Create HITL approval request",
    status_code=status.HTTP_201_CREATED,
    response_model=dict,
)
async def create_approval_request(
    req:   ApprovalRequest,
    token: dict = Depends(verify_token),
):
    """
    Called by agent nodes before executing irreversible actions.
    Returns approval_id to embed in LangGraph interrupt() payload.
    """
    user_id      = token.get("sub", "anonymous")
    workspace_id = token.get("workspace_id", "00000000-0000-0000-0000-000000000001")

    try:
        approval_id = await request_approval(
            action_type=req.action_type,
            action_payload=req.action_payload,
            context_summary=req.context_summary,
            user_id=user_id,
            session_id=req.session_id,
            workspace_id=workspace_id,
            reviewer_email=req.reviewer_email,
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="HITL approval queue temporarily unavailable.",
        )

    return {
        "approval_id": approval_id,
        "status":      "pending",
        "message":     (
            "Approval request created. Notifications sent. "
            "The action will auto-reject after 30 minutes if no decision is made."
        ),
    }


@router.get(
    "/pending",
    summary="List pending HITL approvals",
    response_model=dict,
)
async def get_pending_approvals(
    limit:  int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0,  ge=0),
    token:  dict = Depends(verify_token),
):
    """
    Reviewer dashboard: list all pending approvals in this workspace.
    Requires admin or reviewer role.
    """
    caller_role  = token.get("role", "user")
    workspace_id = token.get("workspace_id", "00000000-0000-0000-0000-000000000001")

    if caller_role not in ("admin", "reviewer", "enterprise"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reviewer or admin role required to view pending approvals.",
        )

    rows = await list_pending(workspace_id, limit=limit, offset=offset)
    return {
        "total":  len(rows),
        "limit":  limit,
        "offset": offset,
        "approvals": [_serialize_approval(r) for r in rows],
    }


@router.get(
    "/history",
    summary="HITL decision history",
    response_model=dict,
)
async def get_history(
    limit:   int = Query(default=50, ge=1, le=200),
    offset:  int = Query(default=0,  ge=0),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    token:   dict = Depends(verify_token),
):
    """Paginated history of all HITL decisions (admin only)."""
    caller_role  = token.get("role", "user")
    workspace_id = token.get("workspace_id", "00000000-0000-0000-0000-000000000001")

    if caller_role not in ("admin", "enterprise"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required for HITL history.",
        )

    limit  = max(1, min(limit, 200))
    offset = max(0, offset)

    try:
        from backend.prompts.registry import get_pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            cond   = "WHERE workspace_id = $1"
            params: list = [workspace_id]
            if status_filter:
                cond += " AND status = $2"
                params.append(status_filter)

            rows = await conn.fetch(
                f"""
                SELECT approval_id, user_id, session_id, action_type,
                       context_summary, status, reviewer_id, reviewer_note,
                       decided_at, expires_at, created_at
                FROM hitl_approvals
                {cond}
                ORDER BY created_at DESC
                LIMIT {limit} OFFSET {offset}
                """,
                *params,
            )
            total = await conn.fetchval(
                f"SELECT COUNT(*) FROM hitl_approvals {cond}", *params,
            )

        return {
            "total":     total,
            "limit":     limit,
            "offset":    offset,
            "approvals": [_serialize_approval(dict(r)) for r in rows],
        }
    except Exception as e:
        logger.error("HITL history query failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve HITL history.",
        )


@router.get(
    "/{approval_id}",
    summary="Get HITL approval detail",
    response_model=dict,
)
async def get_approval_detail(
    approval_id: str,
    token: dict = Depends(verify_token),
):
    """
    Fetch a single approval record.
    Users may only view their own approvals; reviewers/admins may view any.
    """
    # Validate UUID format
    try:
        UUID(approval_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid approval ID format.")

    record = await get_approval(approval_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found.")

    caller_id   = token.get("sub", "")
    caller_role = token.get("role", "user")

    if caller_role not in ("admin", "reviewer", "enterprise") and record.get("user_id") != caller_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You may only view your own approval requests.",
        )

    return _serialize_approval(record)


@router.post(
    "/{approval_id}/decision",
    summary="Approve or reject a HITL request",
    response_model=dict,
)
async def post_decision(
    approval_id: str,
    req:         DecisionRequest,
    token:       dict = Depends(verify_token),
):
    """
    Record a reviewer decision (approved | rejected).

    On success, the associated LangGraph thread is resumed via Redis pub/sub.
    The agent then continues (if approved) or surfaces a rejection message (if rejected).
    """
    # Validate UUID
    try:
        UUID(approval_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid approval ID.")

    caller_id   = token.get("sub", "anonymous")
    caller_role = token.get("role", "user")

    if caller_role not in ("admin", "reviewer", "enterprise"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reviewer or admin role required to approve/reject actions.",
        )

    try:
        result = await decide_approval(
            approval_id=approval_id,
            decision=req.decision,
            reviewer_id=caller_id,
            reviewer_note=req.reviewer_note,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=result.get("error", "Decision could not be recorded."),
        )

    return {
        "approval_id":  approval_id,
        "decision":     req.decision,
        "reviewer_id":  caller_id,
        "message":      (
            f"✅ Action approved and agent resumed."
            if req.decision == "approved"
            else f"❌ Action rejected. Agent has been notified."
        ),
        "thread_id":    result.get("thread_id"),
    }


@router.post(
    "/expire-sweep",
    summary="Manually trigger HITL expiry sweep (admin)",
    response_model=dict,
)
async def manual_expire_sweep(
    token: dict = Depends(verify_token),
):
    """Admin endpoint: immediately expire all timed-out pending approvals."""
    if token.get("role") not in ("admin", "enterprise"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required.",
        )

    expired_count = await expire_stale_approvals()
    return {"expired": expired_count, "message": f"Swept {expired_count} expired approval(s)."}
