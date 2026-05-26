# backend/hitl/hitl_manager.py
"""
Human-in-the-Loop (HITL) Manager.

Flow:
  1. Agent reaches an irreversible action (email send, payment, booking)
  2. Calls request_approval() → creates DB record, sends notifications, returns approval_id
  3. Agent node returns → LangGraph interrupt() suspends the graph thread
  4. Reviewer approves/rejects via /api/hitl/{approval_id}/decision
  5. approve_action() / reject_action() writes verdict to DB
  6. Graph thread resumed via LangGraph update_state() + invoke()
  7. Expired (>30 min pending) approvals are auto-rejected by the expiry sweeper

All state is in PostgreSQL so restarts are safe.
The LangGraph checkpoint is referenced by thread_id + checkpoint_id.
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from backend.config import get_settings
from backend.hitl.notification_service import send_hitl_notifications

logger   = logging.getLogger(__name__)
settings = get_settings()

TIMEOUT_MINUTES = 30


# ── DB helpers ────────────────────────────────────────────────────────────────

async def _get_pool():
    from backend.prompts.registry import get_pool
    return await get_pool()


# ── Core HITL operations ──────────────────────────────────────────────────────

async def request_approval(
    action_type:     str,
    action_payload:  dict[str, Any],
    context_summary: str,
    user_id:         str,
    session_id:      str,
    workspace_id:    str = "00000000-0000-0000-0000-000000000001",
    thread_id:       Optional[str] = None,
    checkpoint_id:   Optional[str] = None,
    reviewer_email:  Optional[str] = None,
) -> str:
    """
    Create a pending HITL approval request.

    Returns:
        approval_id (UUID string) — stored and returned to the LangGraph node.

    Side-effects:
        - Writes to hitl_approvals table
        - Fires email + Slack + in-app notifications (fire-and-forget)
    """
    approval_id = str(uuid.uuid4())
    expires_at  = datetime.now(timezone.utc) + timedelta(minutes=TIMEOUT_MINUTES)

    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO hitl_approvals
                    (approval_id, user_id, session_id, workspace_id,
                     action_type, action_payload, context_summary,
                     expires_at, thread_id, checkpoint_id)
                VALUES ($1::uuid, $2, $3, $4, $5, $6::jsonb, $7, $8, $9, $10)
                """,
                approval_id,
                user_id,
                session_id,
                workspace_id,
                action_type,
                json.dumps(action_payload),
                context_summary,
                expires_at,
                thread_id,
                checkpoint_id,
            )
    except Exception as e:
        logger.error("hitl_approvals insert failed: %s", e)
        raise RuntimeError(f"HITL approval queue unavailable: {e}") from e

    logger.info(
        "HITL approval requested — id: %s, action: %s, user: %s, expires: %s",
        approval_id, action_type, user_id, expires_at.isoformat(),
    )

    # Fire notifications asynchronously — never await so approval creation is instant
    asyncio.create_task(send_hitl_notifications(
        approval_id=approval_id,
        action_type=action_type,
        context_summary=context_summary,
        user_id=user_id,
        session_id=session_id,
        reviewer_email=reviewer_email,
        expires_at=expires_at,
    ))

    return approval_id


async def get_approval(approval_id: str) -> Optional[dict]:
    """Fetch a single approval record by UUID."""
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT approval_id, user_id, session_id, action_type,
                       action_payload, context_summary, status,
                       reviewer_id, reviewer_note, decided_at,
                       expires_at, created_at, thread_id, checkpoint_id
                FROM hitl_approvals
                WHERE approval_id = $1::uuid
                """,
                approval_id,
            )
        if not row:
            return None
        return dict(row)
    except Exception as e:
        logger.error("get_approval failed for %s: %s", approval_id, e)
        return None


async def list_pending(
    workspace_id: str,
    limit:  int = 50,
    offset: int = 0,
) -> list[dict]:
    """List pending approval requests for a workspace (reviewer dashboard)."""
    limit  = max(1, min(limit, 200))
    offset = max(0, offset)
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT approval_id, user_id, session_id, action_type,
                       context_summary, status, expires_at, created_at
                FROM hitl_approvals
                WHERE workspace_id = $1
                  AND status = 'pending'
                  AND expires_at > NOW()
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
                """,
                workspace_id, limit, offset,
            )
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error("list_pending failed: %s", e)
        return []


async def decide_approval(
    approval_id: str,
    decision:    str,              # "approved" | "rejected"
    reviewer_id: str,
    reviewer_note: str = "",
) -> dict:
    """
    Record a reviewer's approve/reject decision.

    Returns:
        {"success": bool, "thread_id": str, "checkpoint_id": str, "action_payload": dict}
        Caller should resume the LangGraph thread using thread_id + checkpoint_id.
    """
    if decision not in ("approved", "rejected"):
        raise ValueError(f"Invalid decision: {decision!r} — must be 'approved' or 'rejected'")

    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            # Atomic: only update if still pending and not expired
            row = await conn.fetchrow(
                """
                UPDATE hitl_approvals
                SET status        = $1,
                    reviewer_id   = $2,
                    reviewer_note = $3,
                    decided_at    = NOW()
                WHERE approval_id = $4::uuid
                  AND status      = 'pending'
                  AND expires_at  > NOW()
                RETURNING approval_id, thread_id, checkpoint_id,
                          action_payload, session_id, user_id
                """,
                decision, reviewer_id, reviewer_note, approval_id,
            )
    except Exception as e:
        logger.error("decide_approval failed for %s: %s", approval_id, e)
        return {"success": False, "error": "Database error during decision recording."}

    if not row:
        # Either not found, already decided, or expired
        record = await get_approval(approval_id)
        if not record:
            return {"success": False, "error": "Approval not found."}
        if record["status"] != "pending":
            return {"success": False, "error": f"Already {record['status']}."}
        return {"success": False, "error": "Approval has expired."}

    logger.info(
        "HITL decision — id: %s, decision: %s, reviewer: %s",
        approval_id, decision, reviewer_id,
    )

    # Notify user of decision via in-app WebSocket
    asyncio.create_task(_notify_decision(
        session_id=row["session_id"],
        approval_id=approval_id,
        decision=decision,
        reviewer_note=reviewer_note,
    ))

    return {
        "success":        True,
        "approval_id":    approval_id,
        "decision":       decision,
        "thread_id":      row["thread_id"],
        "checkpoint_id":  row["checkpoint_id"],
        "action_payload": json.loads(row["action_payload"]) if row["action_payload"] else {},
        "session_id":     row["session_id"],
    }


async def _notify_decision(
    session_id:   str,
    approval_id:  str,
    decision:     str,
    reviewer_note: str,
) -> None:
    """Push decision result to user's WebSocket session."""
    try:
        from backend.session.redis_client import get_redis
        redis   = await get_redis()
        message = json.dumps({
            "type":          "hitl_decision",
            "approval_id":   approval_id,
            "decision":      decision,
            "reviewer_note": reviewer_note,
            "message":       (
                f"✅ Action approved by reviewer."
                if decision == "approved"
                else f"❌ Action rejected: {reviewer_note or 'No reason provided.'}"
            ),
        })
        await redis.publish(f"hitl:{session_id}", message)
    except Exception as e:
        logger.warning("HITL decision notify failed (non-fatal): %s", e)


# ── LangGraph integration ─────────────────────────────────────────────────────

async def hitl_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    LangGraph node for HITL.

    Placed in graph BEFORE irreversible action nodes.
    Creates approval request, then LangGraph interrupt() suspends execution.

    The node checks if an approval decision already exists in state (resume path).
    If approved → return state unchanged.
    If rejected → set error + final_answer.
    If not yet decided → interrupt() with pending approval_id.
    """
    from langgraph.types import interrupt

    approval_id   = state.get("hitl_approval_id")
    hitl_decision = state.get("hitl_decision")

    # ── Resume path: decision already made ───────────────────────────────────
    if hitl_decision == "approved":
        logger.info("HITL resume — approved for approval %s", approval_id)
        return {"hitl_approval_id": approval_id, "hitl_decision": "approved"}

    if hitl_decision == "rejected":
        note = state.get("hitl_reviewer_note", "No reason provided.")
        return {
            "hitl_approval_id": approval_id,
            "hitl_decision":    "rejected",
            "error":            f"Action rejected by reviewer: {note}",
            "final_answer":     f"❌ Your request was rejected by a human reviewer. Reason: {note}",
        }

    # ── First-time path: create approval request ──────────────────────────────
    action_type     = state.get("hitl_action_type",     "agent_action")
    action_payload  = state.get("hitl_action_payload",  {})
    context_summary = state.get("hitl_context_summary", state.get("user_query", ""))
    user_id         = state.get("user_id",              "anonymous")
    session_id      = state.get("session_id",           "")

    new_approval_id = await request_approval(
        action_type=action_type,
        action_payload=action_payload,
        context_summary=context_summary,
        user_id=user_id,
        session_id=session_id,
        thread_id=state.get("thread_id"),
    )

    # interrupt() suspends LangGraph — value is returned to the caller
    interrupt({
        "hitl_approval_id":   new_approval_id,
        "action_type":        action_type,
        "context_summary":    context_summary,
        "message":            (
            f"⏳ Action '{action_type}' requires human approval. "
            f"Approval ID: {new_approval_id}. "
            f"You will be notified when a reviewer responds (timeout: {TIMEOUT_MINUTES} min)."
        ),
    })

    # Unreachable — interrupt() suspends execution
    return {"hitl_approval_id": new_approval_id}  # pragma: no cover


def route_hitl(state: dict[str, Any]) -> str:
    """
    Conditional edge after hitl_node.
    Called on resume — routes based on reviewer decision.
    """
    decision = state.get("hitl_decision", "")
    if decision == "approved":
        return state.get("hitl_next_node", "action_executor")
    return "end_rejected"


# ── Expiry sweeper ────────────────────────────────────────────────────────────

async def expire_stale_approvals() -> int:
    """
    Background task: auto-reject approvals past their expiry time.
    Run every 5 minutes via APScheduler (Feature 4).

    Returns count of expired records.
    """
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                UPDATE hitl_approvals
                SET status       = 'expired',
                    reviewer_note = 'Auto-rejected: approval timeout exceeded',
                    decided_at   = NOW()
                WHERE status    = 'pending'
                  AND expires_at < NOW()
                RETURNING approval_id, session_id
                """
            )

        if rows:
            logger.info("HITL expiry sweeper — expired %d approvals", len(rows))
            # Notify affected sessions
            for row in rows:
                asyncio.create_task(_notify_decision(
                    session_id=row["session_id"],
                    approval_id=str(row["approval_id"]),
                    decision="rejected",
                    reviewer_note="Auto-rejected: approval timed out after 30 minutes.",
                ))

        return len(rows)

    except Exception as e:
        logger.error("expire_stale_approvals failed: %s", e)
        return 0
