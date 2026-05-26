# backend/agent/compliance_agent.py
"""
Guardian Compliance Agent — wraps every agent node with pre/post compliance checks.

Architecture:
  1. Pre-check:   run compliance rules on user input BEFORE the agent runs
  2. Post-check:  scan agent output for PHI leak / hallucination before streaming
  3. Verdict:     APPROVE → pass through | WARN → proceed + flag |
                  REJECT → block + explain | ESCALATE → HITL queue

Verdict is written to the PostgreSQL audit_log table and surfaced to the
React frontend via the `guardInputFlag` / `guardOutputFlag` fields in the
WebSocket `done` event.

All checks are async and non-blocking unless verdict is REJECT/ESCALATE.
LangSmith trace and MLflow are attached to every check run.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Optional

from backend.guardrails.compliance_checker import (
    ComplianceStatus,
    ComplianceVerdict,
    run_compliance_check,
)
from backend.guardrails.phi_detector import detect_phi, phi_summary
from backend.guardrails.guard_engine import check_input, check_output_response
from backend.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()


# ── Verdict constants surfaced to frontend ────────────────────────────────────
class GuardianVerdict(str):
    APPROVE          = "APPROVE"
    WARN             = "WARN"
    REJECT           = "REJECT"
    ESCALATE_TO_HUMAN = "ESCALATE_TO_HUMAN"


# ── Audit trail writer ────────────────────────────────────────────────────────

async def _write_compliance_audit(
    event_type:     str,
    verdict:        str,
    user_id:        str,
    session_id:     str,
    framework:      str,
    violations:     list[dict],
    latency_ms:     float,
    extra:          Optional[dict] = None,
) -> None:
    """
    Write compliance event to PostgreSQL audit_log table.
    Falls back to structured log if DB unavailable.
    """
    record = {
        "event_type":   event_type,       # guardian_input_check | guardian_output_check
        "verdict":      verdict,
        "user_id":      user_id,
        "session_id":   session_id,
        "framework":    framework,
        "violations":   violations,
        "latency_ms":   round(latency_ms, 2),
        "timestamp":    datetime.now(timezone.utc).isoformat(),
        **(extra or {}),
    }

    try:
        from backend.prompts.registry import get_pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO audit_log
                    (event_type, actor_id, resource_type, resource_id,
                     action, outcome, metadata, ip_address, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
                """,
                event_type,
                user_id,
                "compliance_check",
                session_id,
                f"guardian_{event_type}",
                verdict,
                json.dumps(record),
                extra.get("ip_address", "") if extra else "",
            )
    except Exception as e:
        # Non-fatal — log structured event instead
        logger.info("COMPLIANCE_AUDIT: %s", json.dumps(record))
        if settings.app_env != "development":
            logger.warning("Audit DB write failed: %s", e)


# ── LangSmith trace helper ────────────────────────────────────────────────────

def _trace_compliance(
    run_name:   str,
    inputs:     dict,
    outputs:    dict,
    latency_ms: float,
    tags:       list[str],
) -> None:
    """Attach compliance check run to LangSmith trace (non-blocking)."""
    try:
        from langsmith import Client as LangSmithClient
        if not getattr(settings, "langsmith_api_key", None):
            return
        client = LangSmithClient(api_key=settings.langsmith_api_key)
        client.create_run(
            name=run_name,
            run_type="chain",
            inputs=inputs,
            outputs=outputs,
            tags=["guardian", "compliance"] + tags,
            extra={"latency_ms": latency_ms},
        )
    except Exception:
        pass   # Tracing is observability — never crash the agent


# ── Core Guardian check functions ─────────────────────────────────────────────

async def guardian_check_input(
    text:       str,
    user_id:    str,
    session_id: str,
    context:    Optional[dict] = None,
) -> tuple[str, ComplianceVerdict]:
    """
    Run Guardian pre-flight check on user input.

    Returns:
        (verdict_str, ComplianceVerdict)
        verdict_str ∈ {APPROVE, WARN, REJECT, ESCALATE_TO_HUMAN}
    """
    start = time.monotonic()
    ctx   = {
        "user_id":               user_id,
        "session_id":            session_id,
        "audit_trail_enabled":   True,
        "human_oversight_enabled": True,
        "ai_disclosure":         True,
        **(context or {}),
    }

    # Run all 4 frameworks in parallel
    compliance_task  = run_compliance_check(text, ctx)
    guard_input_task = check_input(text, user_id, session_id=session_id)

    compliance_result, guard_result = await asyncio.gather(
        compliance_task, guard_input_task,
        return_exceptions=True,
    )

    # Handle exceptions from individual tasks
    if isinstance(compliance_result, Exception):
        logger.error("Compliance check failed: %s", compliance_result)
        compliance_result = None
    if isinstance(guard_result, Exception):
        logger.error("Guard engine check failed: %s", guard_result)
        guard_result = None

    latency_ms = (time.monotonic() - start) * 1000

    # Determine combined verdict
    verdict = GuardianVerdict.APPROVE
    violations_dicts: list[dict] = []

    if compliance_result:
        if compliance_result.status == ComplianceStatus.REJECT:
            verdict = GuardianVerdict.REJECT
        elif compliance_result.status == ComplianceStatus.ESCALATE:
            verdict = GuardianVerdict.ESCALATE_TO_HUMAN
        elif compliance_result.status == ComplianceStatus.WARN and verdict == GuardianVerdict.APPROVE:
            verdict = GuardianVerdict.WARN

        violations_dicts = [
            {
                "framework":   v.framework,
                "rule_id":     v.rule_id,
                "severity":    v.severity,
                "description": v.description,
            }
            for v in compliance_result.violations
        ]

    # Guard engine can also hard-block (injection detected)
    if guard_result and not guard_result.passed and verdict not in (GuardianVerdict.REJECT,):
        verdict = GuardianVerdict.REJECT
        violations_dicts.append({
            "framework":   "GUARD_ENGINE",
            "rule_id":     "INJECTION_DETECTED",
            "severity":    "CRITICAL",
            "description": guard_result.block_reason or "Prompt injection detected",
        })

    # Async audit write (fire-and-forget)
    asyncio.create_task(_write_compliance_audit(
        event_type="guardian_input_check",
        verdict=verdict,
        user_id=user_id,
        session_id=session_id,
        framework="ALL",
        violations=violations_dicts,
        latency_ms=latency_ms,
        extra={
            "phi_detected": compliance_result.phi_summary if compliance_result else None,
            "risk_tier":    compliance_result.risk_tier   if compliance_result else None,
        },
    ))

    # LangSmith trace (fire-and-forget)
    _trace_compliance(
        run_name="guardian_input_check",
        inputs={"text_len": len(text), "user_id": user_id},
        outputs={"verdict": verdict, "violations": len(violations_dicts)},
        latency_ms=latency_ms,
        tags=[verdict.lower()],
    )

    logger.info(
        "Guardian INPUT check — verdict: %s, violations: %d, %.1fms",
        verdict, len(violations_dicts), latency_ms,
    )

    return verdict, compliance_result  # type: ignore[return-value]


async def guardian_check_output(
    response:   str,
    user_id:    str,
    session_id: str,
    tool_results: Optional[list[dict]] = None,
) -> tuple[str, dict]:
    """
    Run Guardian post-flight check on agent output before streaming.

    Returns:
        (verdict_str, summary_dict)
        verdict_str ∈ {APPROVE, WARN, REJECT}
    """
    start = time.monotonic()

    # Check output with existing guard engine
    output_result = await check_output_response(
        response=response,
        tool_results=tool_results,
        user_id=user_id,
        session_id=session_id,
    )

    # Additional PHI scan on response
    phi_result = detect_phi(response)

    latency_ms = (time.monotonic() - start) * 1000

    verdict = GuardianVerdict.APPROVE
    if not output_result.passed:
        verdict = GuardianVerdict.REJECT
    elif phi_result.has_phi:
        verdict = GuardianVerdict.WARN   # PHI leaked into response — warn

    summary = {
        "verdict":          verdict,
        "hallucination":    output_result.hallucination_flag,
        "pii_in_response":  output_result.pii_in_response,
        "phi_in_response":  phi_result.has_phi,
        "phi_categories":   phi_result.categories,
        "latency_ms":       round(latency_ms, 2),
    }

    # Async audit write
    asyncio.create_task(_write_compliance_audit(
        event_type="guardian_output_check",
        verdict=verdict,
        user_id=user_id,
        session_id=session_id,
        framework="OUTPUT",
        violations=[],
        latency_ms=latency_ms,
        extra=summary,
    ))

    logger.info(
        "Guardian OUTPUT check — verdict: %s, phi: %s, halluc: %s, %.1fms",
        verdict, phi_result.has_phi, output_result.hallucination_flag, latency_ms,
    )

    return verdict, summary


# ── LangGraph node wrapper ────────────────────────────────────────────────────

async def guardian_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    LangGraph node — run Guardian checks and update state.

    Plugs into the graph as:
        graph.add_node("guardian", guardian_node)
        graph.add_edge(START, "guardian")
        graph.add_conditional_edges("guardian", route_guardian)

    State mutations:
        guard_input_flag:  verdict string
        guard_output_flag: post-check verdict string (empty until output phase)
        error:             rejection reason (if REJECT)
    """
    user_query = state.get("user_query", "")
    user_id    = state.get("user_id",    "anonymous")
    session_id = state.get("session_id", "")

    ctx = {
        "user_role":              state.get("user_role",              "user"),
        "channel":                state.get("channel",                "wss"),
        "human_oversight_enabled": True,
        "ai_disclosure":           True,
        "audit_trail_enabled":     True,
    }

    verdict, compliance_result = await guardian_check_input(
        text=user_query,
        user_id=user_id,
        session_id=session_id,
        context=ctx,
    )

    updates: dict[str, Any] = {
        "guard_input_flag": verdict,
    }

    if verdict == GuardianVerdict.REJECT:
        rejection_msg = "Request blocked by Guardian Agent due to compliance violation."
        if compliance_result and compliance_result.violations:
            top = compliance_result.violations[0]
            rejection_msg = (
                f"Compliance violation ({top.framework} {top.rule_id}): {top.description}"
            )
        updates["error"]        = rejection_msg
        updates["final_answer"] = rejection_msg

    elif verdict == GuardianVerdict.ESCALATE_TO_HUMAN:
        updates["error"] = (
            "This request has been escalated to a human reviewer for compliance approval."
        )

    return updates


def route_guardian(state: dict[str, Any]) -> str:
    """
    Conditional edge after guardian_node.

    Returns next node name:
      "supervisor"   → approved/warned → continue normally
      "end_blocked"  → rejected → terminal error state
      "hitl_queue"   → escalated → human review queue
    """
    flag = state.get("guard_input_flag", GuardianVerdict.APPROVE)

    if flag == GuardianVerdict.REJECT:
        return "end_blocked"
    if flag == GuardianVerdict.ESCALATE_TO_HUMAN:
        return "hitl_queue"
    return "supervisor"   # APPROVE or WARN → continue


# ── Decorator for protecting individual agent functions ───────────────────────

def requires_guardian(frameworks: Optional[list[str]] = None):
    """
    Decorator: wrap an async agent function with Guardian pre-check.

    Usage:
        @requires_guardian(frameworks=["HIPAA", "GDPR"])
        async def my_agent_fn(state):
            ...

    If the check rejects, the function returns early with an error state.
    """
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        async def wrapper(state: dict[str, Any], *args, **kwargs) -> dict[str, Any]:
            user_query = state.get("user_query", "")
            user_id    = state.get("user_id",    "anonymous")
            session_id = state.get("session_id", "")

            verdict, _ = await guardian_check_input(
                text=user_query,
                user_id=user_id,
                session_id=session_id,
                context={"frameworks": frameworks} if frameworks else None,
            )

            if verdict in (GuardianVerdict.REJECT, GuardianVerdict.ESCALATE_TO_HUMAN):
                return {
                    **state,
                    "guard_input_flag": verdict,
                    "error": f"Guardian blocked request: {verdict}",
                    "final_answer": "Request blocked by compliance Guardian.",
                }

            result = await fn(state, *args, **kwargs)

            # Post-check on output
            final_answer = result.get("final_answer") or ""
            if final_answer:
                out_verdict, out_summary = await guardian_check_output(
                    response=final_answer,
                    user_id=user_id,
                    session_id=session_id,
                )
                result["guard_output_flag"] = out_verdict
                if out_verdict == GuardianVerdict.REJECT:
                    result["final_answer"] = (
                        "Response blocked by Guardian Agent due to output compliance violation."
                    )

            return result
        return wrapper
    return decorator
