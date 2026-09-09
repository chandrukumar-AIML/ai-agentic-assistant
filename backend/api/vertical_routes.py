"""Vertical agent REST routes — Social Media, CA Accounting, Customer Support."""
from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from backend.api.auth import verify_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/verticals", tags=["verticals"])


def _save_bg(user_id: str, vertical: str, action: str, label: str, result: dict) -> None:
    """Fire-and-forget history save — never blocks the response."""
    if result.get("error"):
        return
    try:
        from backend.db import history as hist
        hist.save(user_id=user_id, vertical=vertical, action=action, input_label=label, output=result)
    except Exception as exc:
        logger.debug("History save skipped: %s", exc)


# ── Social Media ──────────────────────────────────────────────────────────────

class SocialRequest(BaseModel):
    action:   str  = Field(..., description="generate|post|schedule|hashtags|calendar|image")
    platform: str  = Field(default="linkedin", description="twitter|linkedin|instagram|all")
    payload:  dict = Field(default_factory=dict)
    language: str  = Field(default="en")


@router.post("/social/action", summary="AI Social Media Manager")
async def social_action(req: SocialRequest, token: dict = Depends(verify_token)):
    from backend.verticals.social_media.agent import social_agent
    user_id = token.get("sub", "")
    result = await social_agent(
        action=req.action,
        platform=req.platform,
        payload=req.payload,
        user_id=user_id,
        session_id="",
        language=req.language,
    )
    label = req.payload.get("topic") or req.payload.get("brand_name") or req.action
    asyncio.get_event_loop().call_soon(
        lambda: _save_bg(user_id, "social", req.action, str(label)[:120], result)
    )
    return result


# ── CA Accounting ─────────────────────────────────────────────────────────────

class CARequest(BaseModel):
    action:   str  = Field(..., description="gst_query|client_email|deadlines|tds_calc|invoice|audit_checklist|reconciliation|itr_advice|ca_social_post|client_query")
    payload:  dict = Field(default_factory=dict)
    language: str  = Field(default="en")


@router.post("/ca/action", summary="AI CA / Accounting Agent")
async def ca_action(req: CARequest, token: dict = Depends(verify_token)):
    from backend.verticals.ca_accounting.agent import ca_agent
    user_id = token.get("sub", "")
    result = await ca_agent(
        action=req.action,
        payload=req.payload,
        language=req.language,
    )
    label = req.payload.get("query") or req.payload.get("client_name") or req.action
    asyncio.get_event_loop().call_soon(
        lambda: _save_bg(user_id, "ca", req.action, str(label)[:120], result)
    )
    return result


# ── Customer Support ──────────────────────────────────────────────────────────

class CSRequest(BaseModel):
    action:   str  = Field(..., description="faq_bot|qualify_lead|draft_whatsapp|analyze_sentiment|handle_complaint|summarize_ticket|response_template|weekly_report|kb_answer")
    payload:  dict = Field(default_factory=dict)
    language: str  = Field(default="en")


@router.post("/cs/action", summary="AI Customer Support Agent")
async def cs_action(req: CSRequest, token: dict = Depends(verify_token)):
    from backend.verticals.customer_support.agent import cs_agent
    user_id = token.get("sub", "")
    result = await cs_agent(
        action=req.action,
        payload=req.payload,
        language=req.language,
    )
    label = req.payload.get("question") or req.payload.get("customer_message") or req.action
    asyncio.get_event_loop().call_soon(
        lambda: _save_bg(user_id, "cs", req.action, str(label)[:120], result)
    )
    return result
