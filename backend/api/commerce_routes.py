# backend/api/commerce_routes.py
"""
Agentic Commerce API (Feature 5).

ALL irreversible actions require HITL approval before execution.
Guardian compliance check runs on every request.

Endpoints:
  POST /commerce/schedule        — Calendly meeting link
  POST /commerce/sms             — Twilio SMS
  POST /commerce/whatsapp        — Twilio WhatsApp
  POST /commerce/call            — Twilio voice call
  POST /commerce/sign            — DocuSign envelope
  POST /commerce/payment-link    — Stripe payment link
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.api.auth import verify_token
from backend.billing.billing_manager import check_feature_access
from backend.commerce.commerce_agent import (
    create_payment_link,
    make_voice_call,
    schedule_calendly_meeting,
    send_docusign_envelope,
    send_sms,
    send_whatsapp,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/commerce", tags=["commerce"])


async def _guardian_and_hitl(
    text:        str,
    action_type: str,
    payload:     dict,
    user_id:     str,
    session_id:  str,
    plan_tier:   str,
    require_hitl: bool = True,
) -> Optional[str]:
    """
    Run Guardian check + HITL pre-flight.
    Returns None on approval, error string on rejection.
    Returns approval_id string when HITL is pending.
    """
    # Feature gate
    if not check_feature_access(plan_tier, "hitl"):
        return "PRO or ENTERPRISE plan required for commerce actions."

    # Guardian compliance
    try:
        from backend.agent.compliance_agent import guardian_check_input
        verdict, _ = await guardian_check_input(text, user_id, session_id)
        if verdict == "REJECT":
            return "Commerce action blocked by compliance Guardian."
        if verdict == "ESCALATE_TO_HUMAN":
            require_hitl = True
    except Exception as e:
        logger.warning("Guardian check failed (non-fatal): %s", e)

    # HITL approval
    if require_hitl:
        from backend.hitl.hitl_manager import request_approval
        approval_id = await request_approval(
            action_type=action_type,
            action_payload=payload,
            context_summary=text,
            user_id=user_id,
            session_id=session_id,
        )
        return f"HITL_PENDING:{approval_id}"

    return None   # Approved


def _is_hitl_pending(result: Optional[str]) -> bool:
    return bool(result and result.startswith("HITL_PENDING:"))


def _hitl_response(result: str) -> dict:
    approval_id = result.split(":", 1)[1]
    return {
        "status":      "pending_approval",
        "approval_id": approval_id,
        "message":     "This action requires human approval. You'll be notified once reviewed.",
    }


# ── Routes ────────────────────────────────────────────────────────────────────

class ScheduleRequest(BaseModel):
    event_type_uri: str  = Field(..., min_length=1)
    invitee_email:  str  = Field(..., min_length=5)
    invitee_name:   str  = Field(..., min_length=1)
    note:           str  = Field(default="")
    session_id:     str  = Field(default="")


@router.post("/schedule", summary="Schedule Calendly meeting (HITL required)")
async def schedule_meeting(req: ScheduleRequest, token: dict = Depends(verify_token)):
    user_id   = token.get("sub", "anonymous")
    plan_tier = token.get("plan_tier", "free")

    gate = await _guardian_and_hitl(
        f"Schedule meeting with {req.invitee_email}", "calendly_schedule",
        req.model_dump(), user_id, req.session_id, plan_tier,
    )
    if gate and not _is_hitl_pending(gate):
        raise HTTPException(status_code=403, detail=gate)
    if _is_hitl_pending(gate):
        return _hitl_response(gate)

    result = await schedule_calendly_meeting(
        req.event_type_uri, req.invitee_email, req.invitee_name, req.note,
    )
    return result


class SMSRequest(BaseModel):
    to_number:  str = Field(..., min_length=5, max_length=20)
    message:    str = Field(..., min_length=1, max_length=1600)
    session_id: str = Field(default="")


@router.post("/sms", summary="Send SMS via Twilio (HITL required)")
async def send_sms_endpoint(req: SMSRequest, token: dict = Depends(verify_token)):
    user_id   = token.get("sub", "anonymous")
    plan_tier = token.get("plan_tier", "free")

    gate = await _guardian_and_hitl(
        f"Send SMS to {req.to_number}: {req.message[:100]}", "twilio_sms",
        req.model_dump(), user_id, req.session_id, plan_tier,
    )
    if gate and not _is_hitl_pending(gate):
        raise HTTPException(status_code=403, detail=gate)
    if _is_hitl_pending(gate):
        return _hitl_response(gate)

    return await send_sms(req.to_number, req.message)


class WhatsAppRequest(BaseModel):
    to_number:  str = Field(..., min_length=5, max_length=20)
    message:    str = Field(..., min_length=1, max_length=4096)
    session_id: str = Field(default="")


@router.post("/whatsapp", summary="Send WhatsApp message (HITL required)")
async def send_wa_endpoint(req: WhatsAppRequest, token: dict = Depends(verify_token)):
    user_id   = token.get("sub", "anonymous")
    plan_tier = token.get("plan_tier", "free")

    gate = await _guardian_and_hitl(
        f"Send WhatsApp to {req.to_number}: {req.message[:100]}", "twilio_whatsapp",
        req.model_dump(), user_id, req.session_id, plan_tier,
    )
    if gate and not _is_hitl_pending(gate):
        raise HTTPException(status_code=403, detail=gate)
    if _is_hitl_pending(gate):
        return _hitl_response(gate)

    return await send_whatsapp(req.to_number, req.message)


class VoiceRequest(BaseModel):
    to_number:    str = Field(..., min_length=5, max_length=20)
    twiml_or_url: str = Field(..., min_length=1)
    session_id:   str = Field(default="")


@router.post("/call", summary="Make voice call via Twilio (HITL required)")
async def voice_call_endpoint(req: VoiceRequest, token: dict = Depends(verify_token)):
    user_id   = token.get("sub", "anonymous")
    plan_tier = token.get("plan_tier", "free")

    gate = await _guardian_and_hitl(
        f"Voice call to {req.to_number}", "twilio_voice_call",
        req.model_dump(), user_id, req.session_id, plan_tier,
    )
    if gate and not _is_hitl_pending(gate):
        raise HTTPException(status_code=403, detail=gate)
    if _is_hitl_pending(gate):
        return _hitl_response(gate)

    return await make_voice_call(req.to_number, req.twiml_or_url)


class SignRequest(BaseModel):
    signer_email:  str = Field(..., min_length=5)
    signer_name:   str = Field(..., min_length=1)
    document_b64:  str = Field(..., min_length=10,
                                description="Base64-encoded PDF document")
    document_name: str = Field(default="Agreement.pdf")
    email_subject: str = Field(default="Please sign this document")
    session_id:    str = Field(default="")


@router.post("/sign", summary="Send DocuSign envelope (HITL required)")
async def docusign_endpoint(req: SignRequest, token: dict = Depends(verify_token)):
    user_id   = token.get("sub", "anonymous")
    plan_tier = token.get("plan_tier", "free")

    gate = await _guardian_and_hitl(
        f"DocuSign envelope to {req.signer_email}: {req.email_subject}", "docusign_envelope",
        {k: v for k, v in req.model_dump().items() if k != "document_b64"},
        user_id, req.session_id, plan_tier,
    )
    if gate and not _is_hitl_pending(gate):
        raise HTTPException(status_code=403, detail=gate)
    if _is_hitl_pending(gate):
        return _hitl_response(gate)

    return await send_docusign_envelope(
        req.signer_email, req.signer_name,
        req.document_b64, req.document_name, req.email_subject,
    )


class PaymentLinkRequest(BaseModel):
    amount_cents:   int  = Field(..., ge=100, description="Amount in smallest currency unit")
    currency:       str  = Field(default="inr", max_length=3)
    description:    str  = Field(default="AI Agent Service", max_length=200)
    customer_email: Optional[str] = Field(default=None)
    session_id:     str  = Field(default="")


@router.post("/payment-link", summary="Create Stripe payment link (HITL required)")
async def payment_link_endpoint(req: PaymentLinkRequest, token: dict = Depends(verify_token)):
    user_id   = token.get("sub", "anonymous")
    plan_tier = token.get("plan_tier", "free")

    gate = await _guardian_and_hitl(
        f"Payment request: {req.amount_cents/100:.2f} {req.currency.upper()} — {req.description}",
        "stripe_payment_link", req.model_dump(), user_id, req.session_id, plan_tier,
    )
    if gate and not _is_hitl_pending(gate):
        raise HTTPException(status_code=403, detail=gate)
    if _is_hitl_pending(gate):
        return _hitl_response(gate)

    return await create_payment_link(
        req.amount_cents, req.currency, req.description, req.customer_email,
    )
