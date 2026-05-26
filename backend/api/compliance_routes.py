# backend/api/compliance_routes.py
"""
Guardian Compliance API routes.

Endpoints:
  GET  /compliance/frameworks          — list active compliance frameworks
  POST /compliance/check               — check text for compliance violations
  POST /compliance/phi-scan            — HIPAA PHI-only scan
  GET  /compliance/audit-log           — paginated audit events
  GET  /compliance/dashboard           — summary metrics for React dashboard
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.api.auth                    import verify_token
from backend.guardrails.compliance_checker import (
    get_framework_status,
    run_compliance_check,
)
from backend.guardrails.phi_detector     import detect_phi, phi_summary

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/compliance", tags=["compliance"])


# ── Request / Response models ─────────────────────────────────────────────────

class ComplianceCheckRequest(BaseModel):
    text:       str            = Field(..., min_length=1, max_length=50_000)
    frameworks: Optional[list[str]] = Field(
        default=None,
        description="Subset of [HIPAA, GDPR, SOC2, EU_AI_ACT]. Defaults to all.",
    )
    context:    Optional[dict] = Field(
        default=None,
        description="Runtime context: user_role, channel, consent_obtained, data_residency, …",
    )


class PHIScanRequest(BaseModel):
    text:           str  = Field(..., min_length=1, max_length=50_000)
    include_india:  bool = Field(default=True, description="Include ABHA/UHID India health IDs")
    mask_output:    bool = Field(default=True,  description="Return masked text in response")


class ComplianceCheckResponse(BaseModel):
    status:          str
    frameworks:      list[str]
    violations:      list[dict]
    risk_tier:       Optional[str]
    phi:             Optional[dict]
    recommendations: list[str]
    timestamp:       str
    latency_ms:      float


class PHIScanResponse(BaseModel):
    has_phi:      bool
    categories:   list[str]
    match_count:  int
    risk_level:   str
    hipaa_flags:  list[str]
    masked_text:  Optional[str]


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get(
    "/frameworks",
    summary="List active compliance frameworks",
    response_model=dict,
)
async def list_frameworks(
    _token: dict = Depends(verify_token),
):
    """Return all compliance frameworks, their rule counts, and enabled status."""
    return get_framework_status()


@router.post(
    "/check",
    summary="Run multi-framework compliance check",
    response_model=ComplianceCheckResponse,
    status_code=status.HTTP_200_OK,
)
async def compliance_check(
    req:    ComplianceCheckRequest,
    token:  dict = Depends(verify_token),
):
    """
    Run HIPAA / GDPR / SOC2 / EU AI Act compliance checks on the provided text.

    Returns verdict (APPROVE / WARN / REJECT / ESCALATE) and all violations found.
    """
    user_id    = token.get("sub", "anonymous")
    session_id = req.context.get("session_id", "") if req.context else ""

    # Merge user identity into context
    ctx = {
        "user_id":    user_id,
        "session_id": session_id,
        "user_role":  token.get("role", "user"),
        **(req.context or {}),
    }

    try:
        verdict = await run_compliance_check(
            text=req.text,
            context=ctx,
            frameworks=req.frameworks,
        )
    except Exception as e:
        logger.error("Compliance check error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Compliance check service temporarily unavailable.",
        )

    return ComplianceCheckResponse(**verdict.to_api_dict(), latency_ms=verdict.latency_ms)


@router.post(
    "/phi-scan",
    summary="HIPAA PHI scan only",
    response_model=PHIScanResponse,
    status_code=status.HTTP_200_OK,
)
async def phi_scan(
    req:   PHIScanRequest,
    token: dict = Depends(verify_token),
):
    """
    Scan text for HIPAA Protected Health Information (PHI) across all 18 Safe Harbor categories.

    The response NEVER includes the matched text — only category names and offsets.
    """
    try:
        result = detect_phi(
            text=req.text,
            include_india=req.include_india,
            mask_output=req.mask_output,
        )
    except Exception as e:
        logger.error("PHI scan error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PHI scan service temporarily unavailable.",
        )

    return PHIScanResponse(
        has_phi=result.has_phi,
        categories=result.categories,
        match_count=result.match_count,
        risk_level=result.risk_level,
        hipaa_flags=result.hipaa_flags,
        masked_text=result.masked_text if req.mask_output else None,
    )


@router.get(
    "/audit-log",
    summary="Retrieve compliance audit events",
    response_model=dict,
)
async def get_audit_log(
    limit:      int = Query(default=50,  ge=1,   le=500),
    offset:     int = Query(default=0,   ge=0),
    event_type: Optional[str] = Query(default=None),
    user_id_filter: Optional[str] = Query(default=None, alias="user_id"),
    token:      dict = Depends(verify_token),
):
    """
    Retrieve paginated compliance audit events.

    Admin-only: non-admin users may only retrieve their own events.
    """
    caller_id   = token.get("sub", "")
    caller_role = token.get("role", "user")

    # Non-admins can only see their own audit events
    if caller_role not in ("admin", "enterprise") and user_id_filter != caller_id:
        user_id_filter = caller_id

    # Clamp pagination
    limit  = max(1, min(limit, 500))
    offset = max(0, offset)

    try:
        from backend.prompts.registry import get_pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            filters: list[str] = ["1=1"]
            params:  list      = []
            param_n = 1

            if event_type:
                # event_type maps to 'action' in the audit_log schema
                filters.append(f"action = ${param_n}")
                params.append(event_type)
                param_n += 1

            if user_id_filter:
                # actor_id maps to user_id (stored as text via session)
                filters.append(f"session_id = ${param_n}")
                params.append(user_id_filter)
                param_n += 1

            where = " AND ".join(filters)
            rows  = await conn.fetch(
                f"""
                SELECT id, action, session_id, trace_id,
                       guardrail_type, guardrail_triggered, pii_detected,
                       metadata, timestamp
                FROM audit_log
                WHERE {where}
                ORDER BY timestamp DESC
                LIMIT ${param_n} OFFSET ${param_n + 1}
                """,
                *params, limit, offset,
            )

            total = await conn.fetchval(
                f"SELECT COUNT(*) FROM audit_log WHERE {where}",
                *params,
            )

        events = [
            {
                "id":            r["id"],
                "event_type":    r["action"],
                "actor_id":      r["session_id"],
                "resource_type": r["guardrail_type"] or "query",
                "action":        r["action"],
                "outcome":       "FLAGGED" if r["guardrail_triggered"] else "APPROVE",
                "metadata":      r["metadata"] if isinstance(r["metadata"], dict) else {},
                "created_at":    r["timestamp"].isoformat(),
            }
            for r in rows
        ]

        return {"total": total, "limit": limit, "offset": offset, "events": events}

    except Exception as e:
        logger.warning("Audit log DB query failed (returning empty): %s", e)
        return {
            "total":  0,
            "limit":  limit,
            "offset": offset,
            "events": [],
            "note":   "Audit database unavailable — events are logged locally.",
        }


@router.get(
    "/dashboard",
    summary="Compliance dashboard metrics",
    response_model=dict,
)
async def compliance_dashboard(
    token: dict = Depends(verify_token),
):
    """
    Summary metrics for the React compliance dashboard:
    - Total checks today / this week
    - Approve / Warn / Reject / Escalate counts
    - Top violation frameworks
    - PHI detection rate
    """
    try:
        from backend.prompts.registry import get_pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            # Today's guardrail counts
            rows = await conn.fetch(
                """
                SELECT
                    CASE WHEN guardrail_triggered THEN 'FLAGGED' ELSE 'APPROVE' END AS outcome,
                    COUNT(*) AS cnt
                FROM audit_log
                WHERE timestamp >= NOW() - INTERVAL '24 hours'
                GROUP BY guardrail_triggered
                """
            )
            today_counts = {r["outcome"]: r["cnt"] for r in rows}

            # This week
            total_week = await conn.fetchval(
                """
                SELECT COUNT(*) FROM audit_log
                WHERE timestamp >= NOW() - INTERVAL '7 days'
                """
            )

            # PHI detections today
            phi_today = await conn.fetchval(
                """
                SELECT COUNT(*) FROM audit_log
                WHERE pii_detected = true
                  AND timestamp >= NOW() - INTERVAL '24 hours'
                """
            )

        total_today = sum(today_counts.values())
        return {
            "today": {
                "total":    total_today,
                "approve":  today_counts.get("APPROVE", 0),
                "warn":     today_counts.get("WARN",    0),
                "reject":   today_counts.get("REJECT",  0),
                "escalate": today_counts.get("ESCALATE_TO_HUMAN", 0),
                "phi_detections": phi_today or 0,
            },
            "week": {
                "total": total_week or 0,
            },
            "frameworks": get_framework_status()["frameworks"],
            "timestamp":  datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.warning("Dashboard DB query failed: %s", e)
        return {
            "today":      {"total": 0, "approve": 0, "warn": 0, "reject": 0, "escalate": 0, "phi_detections": 0},
            "week":       {"total": 0},
            "frameworks": get_framework_status()["frameworks"],
            "timestamp":  datetime.now(timezone.utc).isoformat(),
            "note":       "Dashboard database unavailable.",
        }
