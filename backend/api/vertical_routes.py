"""Vertical agent REST routes — Social Media, CA Accounting, Customer Support."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from backend.api.auth import verify_token

router = APIRouter(prefix="/verticals", tags=["verticals"])


# ── Social Media ──────────────────────────────────────────────────────────────

class SocialRequest(BaseModel):
    action:   str  = Field(..., description="generate|post|schedule|hashtags|calendar|image")
    platform: str  = Field(default="linkedin", description="twitter|linkedin|instagram|all")
    payload:  dict = Field(default_factory=dict)
    language: str  = Field(default="en")


@router.post("/social/action", summary="AI Social Media Manager")
async def social_action(req: SocialRequest, token: dict = Depends(verify_token)):
    from backend.verticals.social_media.agent import social_agent
    return await social_agent(
        action=req.action,
        platform=req.platform,
        payload=req.payload,
        user_id=token.get("sub", ""),
        session_id="",
        language=req.language,
    )


# ── CA Accounting ─────────────────────────────────────────────────────────────

class CARequest(BaseModel):
    action:   str  = Field(..., description="gst_query|client_email|deadlines|tds_calc|invoice|audit_checklist|reconciliation|itr_advice|ca_social_post|client_query")
    payload:  dict = Field(default_factory=dict)
    language: str  = Field(default="en")


@router.post("/ca/action", summary="AI CA / Accounting Agent")
async def ca_action(req: CARequest, token: dict = Depends(verify_token)):
    from backend.verticals.ca_accounting.agent import ca_agent
    return await ca_agent(
        action=req.action,
        payload=req.payload,
        language=req.language,
    )


# ── Customer Support ──────────────────────────────────────────────────────────

class CSRequest(BaseModel):
    action:   str  = Field(..., description="faq_bot|qualify_lead|draft_whatsapp|analyze_sentiment|handle_complaint|summarize_ticket|response_template|weekly_report|kb_answer")
    payload:  dict = Field(default_factory=dict)
    language: str  = Field(default="en")


@router.post("/cs/action", summary="AI Customer Support Agent")
async def cs_action(req: CSRequest, token: dict = Depends(verify_token)):
    from backend.verticals.customer_support.agent import cs_agent
    return await cs_agent(
        action=req.action,
        payload=req.payload,
        language=req.language,
    )
