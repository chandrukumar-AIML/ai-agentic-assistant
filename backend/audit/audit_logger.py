# backend/audit/audit_logger.py
"""
Audit log writer.
Every agent invocation, tool call, admin action, and guardrail trigger
is written to the audit_log PostgreSQL table.
Non-blocking — uses asyncio.create_task.
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from backend.prompts.registry import get_pool   # reuse asyncpg pool

logger = logging.getLogger(__name__)


async def _write_audit_entry(entry: dict):
    """Internal: write a single audit entry to PostgreSQL."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO audit_log (
                user_id, workspace_id, session_id, trace_id,
                action, tool_called, worker_agents,
                input_tokens, output_tokens, cost_usd, latency_ms,
                guardrail_triggered, guardrail_type, pii_detected,
                reflection_loops, model_used, error, metadata
            ) VALUES (
                $1, $2, $3, $4,
                $5, $6, $7,
                $8, $9, $10, $11,
                $12, $13, $14,
                $15, $16, $17, $18
            )
            """,
            entry.get("user_id"),
            entry.get("workspace_id"),
            entry.get("session_id"),
            entry.get("trace_id"),
            entry.get("action", "query"),
            entry.get("tool_called"),
            entry.get("worker_agents", []),
            entry.get("input_tokens", 0),
            entry.get("output_tokens", 0),
            entry.get("cost_usd", 0.0),
            entry.get("latency_ms", 0),
            entry.get("guardrail_triggered", False),
            entry.get("guardrail_type"),
            entry.get("pii_detected", False),
            entry.get("reflection_loops", 0),
            entry.get("model_used"),
            entry.get("error"),
            json.dumps(entry.get("metadata", {})),
        )


def log_agent_action(
    user_id:             str,
    workspace_id:        str,
    session_id:          str,
    trace_id:            str,
    action:              str,
    worker_agents:       list[str]   = None,
    tool_called:         str | None  = None,
    input_tokens:        int         = 0,
    output_tokens:       int         = 0,
    cost_usd:            float       = 0.0,
    latency_ms:          int         = 0,
    guardrail_triggered: bool        = False,
    guardrail_type:      str | None  = None,
    pii_detected:        bool        = False,
    reflection_loops:    int         = 0,
    model_used:          str | None  = None,
    error:               str | None  = None,
    metadata:            dict        = None,
):
    """
    Fire-and-forget audit log entry.
    Non-blocking — returns immediately, writes in background.
    """
    entry = {
        "user_id":             user_id,
        "workspace_id":        workspace_id,
        "session_id":          session_id,
        "trace_id":            trace_id,
        "action":              action,
        "worker_agents":       worker_agents or [],
        "tool_called":         tool_called,
        "input_tokens":        input_tokens,
        "output_tokens":       output_tokens,
        "cost_usd":            cost_usd,
        "latency_ms":          latency_ms,
        "guardrail_triggered": guardrail_triggered,
        "guardrail_type":      guardrail_type,
        "pii_detected":        pii_detected,
        "reflection_loops":    reflection_loops,
        "model_used":          model_used,
        "error":               error,
        "metadata":            metadata or {},
    }

    try:
        asyncio.create_task(_write_audit_entry(entry))
    except RuntimeError:
        # No event loop running (e.g. in tests) — log only
        logger.info(f"AUDIT: {json.dumps(entry, default=str)}")


async def get_audit_log(
    workspace_id: str,
    user_id:      str | None   = None,
    action:       str | None   = None,
    limit:        int          = 100,
    offset:       int          = 0,
) -> list[dict]:
    limit  = max(1, min(limit,  1000))   # FIXED: cap limit to prevent DoS via unbounded result set
    offset = max(0, min(offset, 100_000))  # FIXED: cap offset to prevent runaway queries
    """
    Query audit log for admin UI.
    Filtered by workspace — never cross-workspace.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        conditions = ["workspace_id = $1"]
        params     = [workspace_id]
        idx        = 2

        if user_id:
            conditions.append(f"user_id = ${idx}")
            params.append(user_id)
            idx += 1
        if action:
            conditions.append(f"action = ${idx}")
            params.append(action)
            idx += 1

        where = " AND ".join(conditions)
        rows  = await conn.fetch(
            f"""
            SELECT
                id, user_id, session_id, trace_id, timestamp,
                action, tool_called, worker_agents,
                input_tokens, output_tokens, cost_usd, latency_ms,
                guardrail_triggered, guardrail_type, pii_detected,
                reflection_loops, model_used, error
            FROM audit_log
            WHERE {where}
            ORDER BY timestamp DESC
            LIMIT ${idx} OFFSET ${idx+1}
            """,
            *params, limit, offset,
        )

    return [dict(row) for row in rows]


async def get_audit_summary(workspace_id: str, days: int = 7) -> dict:
    """Aggregate audit stats for the workspace dashboard."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                COUNT(*)                             AS total_queries,
                SUM(input_tokens + output_tokens)    AS total_tokens,
                SUM(cost_usd)                        AS total_cost_usd,
                AVG(latency_ms)                      AS avg_latency_ms,
                SUM(CASE WHEN guardrail_triggered THEN 1 ELSE 0 END) AS guardrail_count,
                SUM(CASE WHEN pii_detected THEN 1 ELSE 0 END)        AS pii_count,
                SUM(CASE WHEN error IS NOT NULL THEN 1 ELSE 0 END)    AS error_count
            FROM audit_log
            WHERE workspace_id = $1
              AND timestamp >= NOW() - ($2 * INTERVAL '1 day')
            """,  # FIXED: INTERVAL '$2 days' was not a real bind parameter — asyncpg would treat it as a literal string; use ($2 * INTERVAL '1 day') with a proper integer binding
            workspace_id, days,
        )

    return {
        "period_days":     days,
        "total_queries":   int(row["total_queries"] or 0),
        "total_tokens":    int(row["total_tokens"]  or 0),
        "total_cost_usd":  round(float(row["total_cost_usd"] or 0), 4),
        "avg_latency_ms":  round(float(row["avg_latency_ms"] or 0), 0),
        "guardrail_count": int(row["guardrail_count"] or 0),
        "pii_count":       int(row["pii_count"]       or 0),
        "error_count":     int(row["error_count"]     or 0),
    }