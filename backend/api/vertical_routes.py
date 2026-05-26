# backend/api/vertical_routes.py
"""
Domain Vertical REST API routes — Features 9–13, 14.

Endpoints:
  POST /verticals/agri/query             — AgriTech agent
  POST /verticals/agri/diagnose          — Crop disease (image)
  GET  /verticals/agri/mandi-prices      — Mandi price lookup
  GET  /verticals/agri/weather           — Weather advisory
  GET  /verticals/agri/schemes           — Govt scheme search

  POST /verticals/legal/query            — Indian Legal Research
  POST /verticals/legal/case-search      — IndianKanoon search

  POST /verticals/cybersec/analyze-logs  — Log anomaly detection
  GET  /verticals/cybersec/cve-search    — NVD CVE lookup
  POST /verticals/cybersec/full-scan     — Full scan (log + CVE + report)

  POST /verticals/receptionist/chat      — Web widget chat
  POST /verticals/receptionist/voice     — Twilio voice webhook
  POST /verticals/receptionist/whatsapp  — WhatsApp message handler
  GET  /verticals/receptionist/widget    — Embeddable JS snippet

  POST /verticals/forms/extract          — AI Form Reader: single image (Feature 14)
  POST /verticals/forms/extract-multi    — AI Form Reader: multi-page
  POST /verticals/forms/validate         — Validate India identifiers (no image needed)
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field

from backend.api.auth import verify_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/verticals", tags=["verticals"])


# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE 9 — AgriTech
# ═══════════════════════════════════════════════════════════════════════════════

class AgriQueryRequest(BaseModel):
    query:    str           = Field(..., min_length=1, max_length=2000)
    language: str           = Field(default="en", max_length=5)
    district: Optional[str] = Field(default=None)
    state:    str           = Field(default="Tamil Nadu")


class AgriDiagnoseRequest(BaseModel):
    image_b64: str           = Field(..., min_length=10)
    crop_name: str           = Field(default="")
    language:  str           = Field(default="en")


@router.post("/agri/query", summary="AgriTech advisory (Feature 9)")
async def agri_query(req: AgriQueryRequest, token: dict = Depends(verify_token)):
    from backend.verticals.agri.agri_agent import agri_agent
    return await agri_agent(req.query, req.language, req.district, req.state)


@router.post("/agri/diagnose", summary="Crop disease diagnosis from photo")
async def agri_diagnose(req: AgriDiagnoseRequest, token: dict = Depends(verify_token)):
    plan = token.get("plan_tier", "free")
    if plan == "free":
        raise HTTPException(status_code=402, detail="Crop disease diagnosis requires PRO plan.")
    from backend.verticals.agri.agri_agent import diagnose_crop_disease
    return await diagnose_crop_disease(req.image_b64, req.crop_name, req.language)


@router.get("/agri/mandi-prices", summary="Mandi price lookup")
async def agri_mandi(
    commodity: str = Query(..., min_length=1),
    state:     str = Query(default="Tamil Nadu"),
    district:  Optional[str] = Query(default=None),
    token:     dict = Depends(verify_token),
):
    from backend.verticals.agri.agri_agent import get_mandi_prices
    return await get_mandi_prices(commodity, state, district)


@router.get("/agri/weather", summary="Weather advisory for farmers")
async def agri_weather(
    district: str = Query(..., min_length=1),
    state:    str = Query(default="Tamil Nadu"),
    language: str = Query(default="en"),
    token:    dict = Depends(verify_token),
):
    from backend.verticals.agri.agri_agent import get_weather_advisory
    return await get_weather_advisory(district, state, language)


@router.get("/agri/schemes", summary="Government agricultural schemes")
async def agri_schemes(
    query:    str = Query(..., min_length=1),
    language: str = Query(default="en"),
    token:    dict = Depends(verify_token),
):
    from backend.verticals.agri.agri_agent import get_govt_schemes
    return {"schemes": get_govt_schemes(query, language)}


# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE 10 — Indian Legal Research
# ═══════════════════════════════════════════════════════════════════════════════

class LegalQueryRequest(BaseModel):
    query:    str = Field(..., min_length=1, max_length=2000)
    language: str = Field(default="en")


class CaseSearchRequest(BaseModel):
    query:       str = Field(..., min_length=1, max_length=500)
    doc_types:   str = Field(default="judgments")
    max_results: int = Field(default=5, ge=1, le=20)


@router.post("/legal/query", summary="Indian Legal Research agent (Feature 10)")
async def legal_query(req: LegalQueryRequest, token: dict = Depends(verify_token)):
    from backend.verticals.legal.legal_agent import legal_agent
    return await legal_agent(req.query, req.language)


@router.post("/legal/case-search", summary="Search IndianKanoon for cases")
async def legal_case_search(req: CaseSearchRequest, token: dict = Depends(verify_token)):
    from backend.verticals.legal.legal_agent import search_indiankanoon
    cases = await search_indiankanoon(req.query, req.doc_types, req.max_results)
    return {"cases": cases, "count": len(cases)}


# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE 11 — Cybersecurity Monitoring
# ═══════════════════════════════════════════════════════════════════════════════

class LogAnalysisRequest(BaseModel):
    log_text:        str  = Field(..., min_length=1, max_length=100_000)
    generate_report: bool = Field(default=False)


class CVESearchRequest(BaseModel):
    keyword:  str           = Field(..., min_length=1, max_length=200)
    severity: Optional[str] = Field(default=None, pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    limit:    int           = Field(default=10, ge=1, le=20)


class FullScanRequest(BaseModel):
    log_text:    str           = Field(..., min_length=1, max_length=100_000)
    cve_keyword: Optional[str] = Field(default=None)
    query:       str           = Field(default="Security analysis")


@router.post("/cybersec/analyze-logs", summary="Log anomaly detection (Feature 11)")
async def analyze_logs_endpoint(req: LogAnalysisRequest, token: dict = Depends(verify_token)):
    plan = token.get("plan_tier", "free")
    if plan == "free":
        raise HTTPException(status_code=402, detail="Cybersecurity monitoring requires PRO plan.")
    from backend.verticals.cybersec.cybersec_agent import analyze_logs, generate_incident_report
    import base64

    analysis = analyze_logs(req.log_text)
    result   = {"analysis": analysis}

    if req.generate_report and analysis["findings"]:
        try:
            pdf = await generate_incident_report(
                title=f"Incident Report — {analysis['risk_level']}",
                findings=analysis["findings"],
                log_lines=analysis["lines_analyzed"],
                risk_level=analysis["risk_level"],
            )
            result["report_b64"]     = base64.b64encode(pdf).decode()
            result["report_size_kb"] = round(len(pdf) / 1024, 1)
        except Exception as e:
            result["report_error"] = "PDF generation unavailable."
    return result


@router.get("/cybersec/cve-search", summary="NVD CVE vulnerability search")
async def cve_search(
    keyword:  str = Query(..., min_length=1),
    severity: Optional[str] = Query(default=None),
    limit:    int = Query(default=10, ge=1, le=20),
    token:    dict = Depends(verify_token),
):
    from backend.verticals.cybersec.cybersec_agent import search_nvd_cve
    cves = await search_nvd_cve(keyword, severity, limit)
    return {"cves": cves, "count": len(cves)}


@router.post("/cybersec/full-scan", summary="Full security scan: logs + CVE + report")
async def full_security_scan(req: FullScanRequest, token: dict = Depends(verify_token)):
    plan = token.get("plan_tier", "free")
    if plan == "free":
        raise HTTPException(status_code=402, detail="Full security scan requires PRO plan.")
    from backend.verticals.cybersec.cybersec_agent import cybersec_agent
    return await cybersec_agent(req.query, req.log_text, req.cve_keyword, generate_report=True)


# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE 13 — AI Receptionist
# ═══════════════════════════════════════════════════════════════════════════════

class ReceptionistChatRequest(BaseModel):
    message:    str           = Field(..., min_length=1, max_length=1000)
    channel:    str           = Field(default="web")
    session_id: str           = Field(default="")
    user_name:  Optional[str] = Field(default=None)


@router.post("/receptionist/chat", summary="AI Receptionist chat endpoint (Feature 13)")
async def receptionist_chat(req: ReceptionistChatRequest):
    """Public endpoint — no auth required for web widget embeds."""
    from backend.verticals.receptionist.receptionist_agent import handle_receptionist_message
    return await handle_receptionist_message(
        req.message, req.channel, req.session_id, req.user_name,
    )


@router.post("/receptionist/voice", summary="Twilio voice webhook (TwiML response)")
async def receptionist_voice(request: Request):
    """
    Twilio calls this when inbound call received.
    Returns TwiML XML.
    """
    from backend.verticals.receptionist.receptionist_agent import build_inbound_twiml
    form_data = await request.form()
    lang      = "en"  # Could detect from Twilio metadata
    twiml     = build_inbound_twiml(lang)
    return Response(content=twiml, media_type="text/xml")


@router.post("/receptionist/voice-response", summary="Twilio voice response handler")
async def receptionist_voice_response(request: Request):
    """Handle gathered speech from Twilio voice call."""
    from backend.verticals.receptionist.receptionist_agent import (
        handle_receptionist_message, build_voice_twiml,
    )
    form_data   = await request.form()
    speech_text = form_data.get("SpeechResult", "")
    if not speech_text:
        twiml = build_voice_twiml("I didn't catch that. Could you please repeat?")
        return Response(content=twiml, media_type="text/xml")

    result = await handle_receptionist_message(speech_text, channel="voice")
    twiml  = build_voice_twiml(result["response"], result["language"])
    return Response(content=twiml, media_type="text/xml")


@router.post("/receptionist/whatsapp", summary="WhatsApp message handler (Twilio webhook)")
async def receptionist_whatsapp(request: Request):
    """Twilio calls this for inbound WhatsApp messages. Returns TwiML."""
    from backend.verticals.receptionist.receptionist_agent import handle_receptionist_message
    form_data  = await request.form()
    body       = form_data.get("Body", "")
    from_num   = form_data.get("From", "")
    profile    = form_data.get("ProfileName", "")

    if not body:
        return Response(content="<?xml version='1.0' encoding='UTF-8'?><Response></Response>",
                        media_type="text/xml")

    result   = await handle_receptionist_message(body, channel="whatsapp", user_name=profile)
    response = result["response"]

    # For WhatsApp, reply via Twilio API (not TwiML)
    try:
        from backend.commerce.commerce_agent import send_whatsapp
        await send_whatsapp(from_num, response)
    except Exception as e:
        logger.error("WhatsApp reply failed: %s", e)

    return Response(
        content="<?xml version='1.0' encoding='UTF-8'?><Response></Response>",
        media_type="text/xml",
    )


@router.get(
    "/receptionist/widget",
    summary="Get embeddable JS widget code",
    response_class=HTMLResponse,
)
async def receptionist_widget(
    theme_color: str = Query(default="#534AB7"),
    greeting:    str = Query(default="Hi! How can I help you today?"),
    token:       dict = Depends(verify_token),
):
    """Return the HTML/JS snippet to embed in customer websites."""
    from backend.verticals.receptionist.receptionist_agent import get_widget_embed_code
    from backend.config import get_settings
    cfg  = get_settings()
    code = get_widget_embed_code(
        api_url=getattr(cfg, "backend_url", "http://localhost:8000"),
        theme_color=theme_color,
        greeting=greeting,
    )
    return HTMLResponse(content=f"<pre>{code}</pre>")


# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE 14 — AI Form Reader + Data Extractor
# ═══════════════════════════════════════════════════════════════════════════════

class FormExtractRequest(BaseModel):
    image_b64:    str           = Field(..., min_length=10,
                                        description="Base64-encoded JPEG/PNG of the form")
    form_hint:    Optional[str] = Field(default=None,
                                        description="pan_card|aadhaar_card|gstin_reg|invoice|kyc|generic")
    redact_pii:   bool          = Field(default=False)
    export_excel: bool          = Field(default=False)
    language:     str           = Field(default="en")


class FormMultiPageRequest(BaseModel):
    images_b64:   list[str]     = Field(..., min_length=1, max_length=20)
    form_hint:    Optional[str] = Field(default=None)
    redact_pii:   bool          = Field(default=False)
    export_excel: bool          = Field(default=False)


class ValidateRequest(BaseModel):
    pan:     Optional[str] = Field(default=None)
    gstin:   Optional[str] = Field(default=None)
    aadhaar: Optional[str] = Field(default=None)
    mobile:  Optional[str] = Field(default=None)
    pincode: Optional[str] = Field(default=None)
    ifsc:    Optional[str] = Field(default=None)


@router.post("/forms/extract", summary="Extract structured data from form image (Feature 14)")
async def form_extract(req: FormExtractRequest, token: dict = Depends(verify_token)):
    """
    GPT-4o Vision form extraction.
    Validates PAN, Aadhaar, GSTIN, mobile, pincode automatically.
    PRO plan required.
    """
    plan = token.get("plan_tier", "free")
    if plan == "free":
        raise HTTPException(
            status_code=402,
            detail="AI Form Reader requires PRO plan.",
        )
    from backend.verticals.form_reader.form_agent import form_reader_agent
    return await form_reader_agent(
        images_b64=[req.image_b64],
        form_hint=req.form_hint,
        redact_pii=req.redact_pii,
        export_excel=req.export_excel,
        language=req.language,
    )


@router.post("/forms/extract-multi", summary="Multi-page form extraction")
async def form_extract_multi(req: FormMultiPageRequest, token: dict = Depends(verify_token)):
    """
    Process multi-page forms (e.g., scanned PDFs split into JPEG pages).
    Merges fields by highest confidence value. PRO plan required.
    """
    plan = token.get("plan_tier", "free")
    if plan == "free":
        raise HTTPException(status_code=402, detail="AI Form Reader requires PRO plan.")
    from backend.verticals.form_reader.form_agent import form_reader_agent
    return await form_reader_agent(
        images_b64=req.images_b64,
        form_hint=req.form_hint,
        redact_pii=req.redact_pii,
        export_excel=req.export_excel,
    )


@router.post("/forms/validate", summary="Validate India identifiers (PAN/Aadhaar/GSTIN/etc.)")
async def form_validate(req: ValidateRequest, token: dict = Depends(verify_token)):
    """
    Validate Indian identity numbers without a form image.
    Aadhaar response always masks the number — only last 4 digits returned.
    """
    from backend.verticals.form_reader.form_agent import (
        validate_pan, validate_gstin, validate_aadhaar,
        validate_mobile_in, validate_pincode_in, validate_ifsc,
    )
    result: dict = {}
    if req.pan:     result["pan"]     = validate_pan(req.pan)
    if req.gstin:   result["gstin"]   = validate_gstin(req.gstin)
    if req.aadhaar: result["aadhaar"] = validate_aadhaar(req.aadhaar)
    if req.mobile:  result["mobile"]  = validate_mobile_in(req.mobile)
    if req.pincode: result["pincode"] = validate_pincode_in(req.pincode)
    if req.ifsc:    result["ifsc"]    = validate_ifsc(req.ifsc)

    if not result:
        raise HTTPException(status_code=400, detail="Provide at least one field to validate.")

    # Cross-validate GSTIN vs PAN if both provided
    if "gstin" in result and "pan" in result:
        if result["gstin"].get("valid") and result["pan"].get("valid"):
            result["gstin_pan_match"] = (
                result["gstin"].get("embedded_pan") == result["pan"].get("pan")
            )
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE 15 — AI Email Manager
# ═══════════════════════════════════════════════════════════════════════════════

class EmailActionRequest(BaseModel):
    action:       str           = Field(..., description="list|read|draft|send|summarize|search")
    provider:     str           = Field(default="gmail", description="gmail|outlook")
    access_token: str           = Field(..., min_length=10)
    message_id:   Optional[str] = Field(default=None)
    query:        str           = Field(default="is:unread")
    draft_params: Optional[dict] = Field(default=None)
    send_params:  Optional[dict] = Field(default=None)
    max_results:  int           = Field(default=20, ge=1, le=50)
    language:     str           = Field(default="en")


@router.post("/email/action", summary="AI Email Manager (Feature 15)")
async def email_action(req: EmailActionRequest, token: dict = Depends(verify_token)):
    """
    Execute email management action. 'send' always routes through HITL.
    Requires PRO plan.
    """
    plan = token.get("plan_tier", "free")
    if plan == "free":
        raise HTTPException(status_code=402, detail="AI Email Manager requires PRO plan.")
    from backend.verticals.email_manager.email_agent import email_agent
    return await email_agent(
        action=req.action,
        provider=req.provider,
        access_token=req.access_token,
        user_id=token.get("sub", ""),
        session_id="",
        message_id=req.message_id,
        query=req.query,
        draft_params=req.draft_params,
        send_params=req.send_params,
        max_results=req.max_results,
        language=req.language,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE 16 — AI Sales Assistant + Lead Qualifier
# ═══════════════════════════════════════════════════════════════════════════════

class SalesActionRequest(BaseModel):
    action:  str  = Field(..., description="qualify|enrich|create_contact|generate_outreach|full_pipeline")
    lead:    dict = Field(..., description="Lead data dict")
    crm:     str  = Field(default="hubspot", description="hubspot|salesforce|none")
    product: str  = Field(default="our AI platform")
    language: str = Field(default="en")


@router.post("/sales/action", summary="AI Sales Assistant + Lead Qualifier (Feature 16)")
async def sales_action(req: SalesActionRequest, token: dict = Depends(verify_token)):
    """
    Lead qualification, enrichment, CRM sync, and outreach generation.
    High-value leads (score >= 80, budget >= $50k) auto-trigger HITL review.
    """
    from backend.verticals.sales.sales_agent import sales_agent
    return await sales_agent(
        action=req.action,
        lead=req.lead,
        crm=req.crm,
        user_id=token.get("sub", ""),
        session_id="",
        product=req.product,
        language=req.language,
    )


@router.post("/sales/score", summary="Quick lead scoring (BANT model)")
async def sales_score(
    lead:  dict = Body(..., description="Lead data fields (budget_usd, title, company_size, etc.)"),
    token: dict = Depends(verify_token),
):
    """Score a lead 0-100 using BANT framework. No external API calls."""
    from backend.verticals.sales.sales_agent import score_lead
    return score_lead(lead)


# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE 17 — AI Accountant Assistant
# ═══════════════════════════════════════════════════════════════════════════════

class AccountantRequest(BaseModel):
    action:  str  = Field(..., description="gst_calc|tds_calc|hsn_lookup|gstr1|gstr3b|invoice|query")
    payload: dict = Field(default_factory=dict)
    language: str = Field(default="en")


@router.post("/accountant/action", summary="AI Accountant (GST/TDS/GSTR) — Feature 17")
async def accountant_action(req: AccountantRequest, token: dict = Depends(verify_token)):
    """
    India GST calculation, TDS computation, GSTR-1/3B generation, tax invoice PDF.
    """
    from backend.verticals.accountant.accountant_agent import accountant_agent
    return await accountant_agent(req.action, req.payload, req.language)


@router.get("/accountant/hsn/{hsn_code}", summary="HSN/SAC code lookup")
async def hsn_lookup(hsn_code: str, token: dict = Depends(verify_token)):
    from backend.verticals.accountant.accountant_agent import lookup_hsn
    return lookup_hsn(hsn_code)


@router.get("/accountant/tds-sections", summary="List all TDS sections")
async def tds_sections(token: dict = Depends(verify_token)):
    from backend.verticals.accountant.accountant_agent import _TDS_SECTIONS
    return {
        "sections": {
            k: {
                "description":  v["description"],
                "threshold":    v.get("threshold"),
                "rate_others":  v.get("rate_others"),
            }
            for k, v in _TDS_SECTIONS.items()
        }
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE 18 — AI HR Assistant
# ═══════════════════════════════════════════════════════════════════════════════

class HRRequest(BaseModel):
    action:  str  = Field(..., description="screen|generate_jd|offer_letter|onboarding|bgv|qa")
    payload: dict = Field(default_factory=dict)
    language: str = Field(default="en")


@router.post("/hr/action", summary="AI HR Assistant — full hiring pipeline (Feature 18)")
async def hr_action(req: HRRequest, token: dict = Depends(verify_token)):
    """
    Resume screening, JD generation, offer letter PDF (HITL before e-sign),
    onboarding checklist, BGV checklist, HR Q&A.
    """
    from backend.verticals.hr.hr_agent import hr_agent
    return await hr_agent(
        action=req.action,
        payload=req.payload,
        user_id=token.get("sub", ""),
        session_id="",
        language=req.language,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE 19 — AI Social Media Manager
# ═══════════════════════════════════════════════════════════════════════════════

class SocialRequest(BaseModel):
    action:   str  = Field(..., description="generate|post|schedule|hashtags|calendar|image")
    platform: str  = Field(default="linkedin", description="twitter|linkedin|instagram|all")
    payload:  dict = Field(default_factory=dict)
    language: str  = Field(default="en")


@router.post("/social/action", summary="AI Social Media Manager (Feature 19)")
async def social_action(req: SocialRequest, token: dict = Depends(verify_token)):
    """
    Generate platform-optimized posts, DALL-E 3 visuals, Buffer scheduling,
    hashtag research, and content calendar planning.
    Post/schedule actions require PRO plan.
    """
    if req.action in ("post", "schedule") and token.get("plan_tier", "free") == "free":
        raise HTTPException(status_code=402, detail="Social posting requires PRO plan.")
    from backend.verticals.social_media.social_agent import social_agent
    return await social_agent(
        action=req.action,
        platform=req.platform,
        payload=req.payload,
        user_id=token.get("sub", ""),
        session_id="",
        language=req.language,
    )


@router.post("/social/generate-all", summary="Generate posts for all platforms at once")
async def social_generate_all(
    topic:     str = Query(..., min_length=3),
    tone:      str = Query(default="professional"),
    brand:     str = Query(default=""),
    language:  str = Query(default="en"),
    token:     dict = Depends(verify_token),
):
    """
    Generate Twitter + LinkedIn + Instagram posts for a topic in one call.
    No external API calls — pure content generation.
    """
    from backend.verticals.social_media.social_agent import generate_post
    import asyncio

    twitter, linkedin, instagram = await asyncio.gather(
        generate_post(topic, "twitter",   tone, True, brand, language),
        generate_post(topic, "linkedin",  tone, True, brand, language),
        generate_post(topic, "instagram", tone, True, brand, language),
    )
    return {
        "topic":     topic,
        "twitter":   twitter,
        "linkedin":  linkedin,
        "instagram": instagram,
    }
