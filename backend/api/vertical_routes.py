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


# ═══════════════════════════════════════════════════════════════════════════════
# QA ENGINEER VERTICAL
# ═══════════════════════════════════════════════════════════════════════════════

class QARequest(BaseModel):
    action:  str  = Field(..., description="generate_tests|analyze_bug|test_plan|review_quality|acceptance_criteria")
    payload: dict = Field(default_factory=dict)
    language: str = Field(default="en")


@router.post("/qa/action", summary="AI QA Engineer — test generation, bug analysis, test plans")
async def qa_action(req: QARequest, token: dict = Depends(verify_token)):
    """
    QA automation: generate test cases, analyze bug reports, create test plans,
    review code quality, and write Gherkin acceptance criteria.
    """
    from backend.verticals.qa.qa_agent import qa_agent
    return await qa_agent(action=req.action, payload=req.payload, language=req.language)


# ═══════════════════════════════════════════════════════════════════════════════
# PROJECT MANAGER / SCRUM VERTICAL
# ═══════════════════════════════════════════════════════════════════════════════

class PMRequest(BaseModel):
    action:  str  = Field(..., description="user_story|sprint_plan|retrospective|roadmap|estimation")
    payload: dict = Field(default_factory=dict)
    language: str = Field(default="en")


@router.post("/pm/action", summary="AI Project Manager — user stories, sprint plans, roadmaps")
async def pm_action(req: PMRequest, token: dict = Depends(verify_token)):
    """
    Agile project management: generate user stories, create sprint backlogs,
    facilitate retrospectives, build product roadmaps, and estimate story points.
    """
    from backend.verticals.pm.pm_agent import pm_agent
    return await pm_agent(action=req.action, payload=req.payload, language=req.language)


# ═══════════════════════════════════════════════════════════════════════════════
# CODE ASSISTANT VERTICAL (exposes existing CodeAgent)
# ═══════════════════════════════════════════════════════════════════════════════

class CodeRequest(BaseModel):
    action:   str = Field(..., description="generate|debug|review|test|explain")
    code:     str = Field(default="", max_length=20_000)
    prompt:   str = Field(default="", max_length=2000)
    language: str = Field(default="python", description="python|javascript|typescript|go|java|sql")


@router.post("/code/action", summary="AI Code Assistant — generate, debug, review, test")
async def code_action(req: CodeRequest, token: dict = Depends(verify_token)):
    """
    Code assistance: generate code from description, debug existing code,
    review for quality/security, write unit tests, or explain complex logic.
    """
    from backend.agent.code_agent import CodeAgent

    # Build natural language query that CodeAgent's intent detector understands
    lang = req.language
    code_block = f"\n```{lang}\n{req.code}\n```" if req.code.strip() else ""

    if req.action == "generate":
        query = req.prompt or "Generate Python code"
    elif req.action == "debug":
        query = f"Debug and fix this {lang} code:{code_block}\n{req.prompt}"
    elif req.action == "review":
        query = f"Review this {lang} code:{code_block}\n{req.prompt}"
    elif req.action == "test":
        query = f"Write pytest unit tests for this {lang} code:{code_block}\n{req.prompt}"
    elif req.action == "explain":
        query = f"Explain this {lang} code:{code_block}\n{req.prompt}"
    else:
        query = f"{req.prompt}{code_block}"

    agent  = CodeAgent()
    result = await agent.run(query=query, context={}, memory_context="")
    return {
        "action":     req.action,
        "content":    result.content,
        "metadata":   result.metadata,
        "latency_ms": result.latency_ms,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ML ENGINEER VERTICAL
# ═══════════════════════════════════════════════════════════════════════════════

class MLRequest(BaseModel):
    action:  str  = Field(..., description="experiment_design|model_eval|feature_engineering|drift_analysis|training_plan|prompt_eval")
    payload: dict = Field(default_factory=dict)
    language: str = Field(default="en")


@router.post("/ml/action", summary="AI ML Engineer — experiments, model eval, feature engineering, drift")
async def ml_action(req: MLRequest, token: dict = Depends(verify_token)):
    """
    ML engineering: design experiments, evaluate models, engineer features,
    detect drift, plan training runs, and evaluate LLM prompts.
    """
    from backend.verticals.ml.ml_agent import ml_agent
    return await ml_agent(action=req.action, payload=req.payload, language=req.language)


# ═══════════════════════════════════════════════════════════════════════════════
# DBA VERTICAL
# ═══════════════════════════════════════════════════════════════════════════════

class DBARequest(BaseModel):
    action:  str  = Field(..., description="optimize_query|design_schema|index_recommend|migration_script|health_analysis|query_explain")
    payload: dict = Field(default_factory=dict)
    language: str = Field(default="en")


@router.post("/dba/action", summary="AI DBA — query optimization, schema design, migrations, health")
async def dba_action(req: DBARequest, token: dict = Depends(verify_token)):
    """
    Database administration: optimize slow queries, design schemas, recommend indexes,
    generate safe migration scripts, analyze database health, and explain query plans.
    """
    from backend.verticals.dba.dba_agent import dba_agent
    return await dba_agent(action=req.action, payload=req.payload, language=req.language)


# ═══════════════════════════════════════════════════════════════════════════════
# TECH LEAD / ARCHITECT VERTICAL
# ═══════════════════════════════════════════════════════════════════════════════

class TechLeadRequest(BaseModel):
    action:  str  = Field(..., description="adr|tech_debt|api_design|arch_review|perf_analysis|tech_radar")
    payload: dict = Field(default_factory=dict)
    language: str = Field(default="en")


@router.post("/techlead/action", summary="AI Tech Lead — ADRs, tech debt, API design, architecture review")
async def techlead_action(req: TechLeadRequest, token: dict = Depends(verify_token)):
    """
    Technical leadership: write Architecture Decision Records, analyze tech debt,
    design REST APIs with OpenAPI spec, review architecture, analyze performance,
    and generate technology radar assessments.
    """
    from backend.verticals.techlead.techlead_agent import techlead_agent
    return await techlead_agent(action=req.action, payload=req.payload, language=req.language)


# ═══════════════════════════════════════════════════════════════════════════════
# ENHANCEMENT ROUTES — Bring all roles to 100%
# Inline LLM calls to avoid modifying existing agent files.
# ═══════════════════════════════════════════════════════════════════════════════

class EnhanceRequest(BaseModel):
    action:  str  = Field(..., min_length=1)
    payload: dict = Field(default_factory=dict)
    language: str = Field(default="en")


async def _llm(system: str, prompt: str, max_tokens: int = 700) -> str:
    from backend.llm.router import llm_router
    text, _ = await llm_router.complete(
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=max_tokens,
    )
    return text


@router.post("/devops/iac", summary="DevOps IaC Generator — Dockerfile, K8s, Terraform, GH Actions")
async def devops_iac(req: EnhanceRequest, token: dict = Depends(verify_token)):
    p = req.payload
    iac_type = p.get("iac_type", "dockerfile")
    desc     = p.get("description", "web service")
    stack    = p.get("tech_stack", "Python/FastAPI")
    port     = p.get("port", "8000")
    env_vars = p.get("env_vars", "")
    sys = "You are a senior DevOps engineer with deep expertise in containers, Kubernetes, Terraform, and GitHub Actions. Generate production-ready, security-hardened IaC."
    if iac_type == "dockerfile":
        prompt = f"Generate a production-ready multi-stage Dockerfile for a {stack} app.\nDescription: {desc}\nPort: {port}\nEnv vars needed: {env_vars}\nRequirements: non-root user, minimal image, health check, optimized layer caching, .dockerignore hints."
    elif iac_type == "k8s":
        prompt = f"Generate complete Kubernetes manifests for: {desc}\nStack: {stack}\nPort: {port}\nInclude: Deployment, Service, HPA, PodDisruptionBudget, ConfigMap. Use resource limits, readiness/liveness probes, rolling update strategy."
    elif iac_type == "terraform":
        prompt = f"Generate a Terraform module for: {desc}\nStack: {stack}\nInclude: main.tf, variables.tf, outputs.tf\nBest practices: remote state, provider pinning, tagging strategy, meaningful outputs."
    elif iac_type == "github_actions":
        prompt = f"Generate a complete GitHub Actions CI/CD workflow for: {desc}\nStack: {stack}\nInclude: lint, test, build, Docker push, deploy to staging, manual approval gate for production. Use caching and matrix strategy."
    else:
        prompt = f"Generate IaC ({iac_type}) for: {desc}\nStack: {stack}"
    result = await _llm(sys, prompt, 900)
    return {"iac_type": iac_type, "output": result}


@router.post("/cybersec/owasp", summary="OWASP Top 10 review + security policy + pen test report")
async def cybersec_owasp(req: EnhanceRequest, token: dict = Depends(verify_token)):
    p = req.payload
    sys = "You are a senior application security engineer (OWASP, NIST, ISO 27001). You write thorough security reviews and professional security documentation."
    if req.action == "owasp_review":
        code = p.get("code", "")
        lang = p.get("language", "python")
        prompt = f"Perform an OWASP Top 10 security review of this {lang} code:\n\n```{lang}\n{code[:3000]}\n```\n\nFor each OWASP category: PASS/FAIL/N/A with line references for failures. Then list findings with severity (Critical/High/Medium/Low) and remediation code snippets."
    elif req.action == "security_policy":
        prompt = f"Write a comprehensive Information Security Policy for {p.get('company','Our Company')} ({p.get('industry','SaaS')}).\nScope: {p.get('scope','web application')}\nInclude: Password policy, Access control, Data classification, Incident response, Acceptable use, Third-party vendors, Compliance. Format as numbered sections."
    elif req.action == "pentest_report":
        prompt = f"Generate a professional penetration test report for: {p.get('target','Web Application')}\nScope: {p.get('scope','')}\nFindings: {p.get('findings','')}\nInclude: Executive Summary, Methodology, Risk Matrix, Findings table (Vuln/Severity/CVSS/Evidence/Remediation), Remediation Roadmap."
    else:
        prompt = str(p)
    result = await _llm(sys, prompt, 900)
    return {"action": req.action, "result": result}


@router.post("/sales/enhance", summary="Sales email sequences + meeting prep briefs")
async def sales_enhance(req: EnhanceRequest, token: dict = Depends(verify_token)):
    p = req.payload
    sys = "You are an expert B2B sales strategist with 15+ years in SaaS and enterprise sales. You write compelling, personalized sales communications that convert."
    if req.action == "email_sequence":
        prompt = f"Create a 5-email {p.get('sequence_type','cold outreach')} sequence for {p.get('prospect_name','the prospect')} at {p.get('company','their company')}.\nProduct: {p.get('product','our AI platform')}\nPain point: {p.get('pain_point','operational inefficiency')}\nFormat each email: Subject, Preview text, Body, CTA, Timing (Day X). Personalized, concise, progressively more direct."
    elif req.action == "meeting_prep":
        prompt = f"Create a comprehensive meeting prep brief for a {p.get('deal_stage','discovery')} call with {p.get('company','the prospect')}.\nAttendees: {p.get('attendees','decision maker, technical lead')}\nProduct: {p.get('product','our platform')}\nInclude: Research checklist, SPIN questions, Anticipated objections + responses, Demo flow, Next steps script."
    else:
        prompt = str(p)
    result = await _llm(sys, prompt, 800)
    return {"action": req.action, "result": result}


@router.post("/hr/enhance", summary="HR performance reviews + employee handbook generator")
async def hr_enhance(req: EnhanceRequest, token: dict = Depends(verify_token)):
    p = req.payload
    sys = "You are a senior HR professional specializing in performance management and organizational development. You write fair, legally compliant HR documentation."
    if req.action == "performance_review":
        prompt = f"Write a comprehensive performance review for:\nEmployee: {p.get('employee_name','Employee')} | Role: {p.get('role','Software Engineer')} | Period: {p.get('review_period','Q4 2025')} | Rating: {p.get('overall_rating','Meets Expectations')}\nAchievements: {p.get('achievements','')}\nDevelopment areas: {p.get('improvement_areas','')}\nInclude: Performance summary, Goal achievement, Competency ratings (1-5) for 6 competencies, 3 SMART development goals, Manager narrative."
    elif req.action == "employee_handbook":
        prompt = f"Create a comprehensive employee handbook for {p.get('company','Our Company')} ({p.get('industry','Technology')}).\nTopics: {p.get('topics','leave policy, code of conduct, remote work')}\nInclude formal sections: Welcome, Company values, Employment policies, Code of conduct, Leave & benefits, Performance management, Grievance procedure, IT & security, Acknowledgement page."
    else:
        prompt = str(p)
    result = await _llm(sys, prompt, 800)
    return {"action": req.action, "result": result}


@router.post("/accountant/enhance", summary="P&L analysis + budget forecasting")
async def accountant_enhance(req: EnhanceRequest, token: dict = Depends(verify_token)):
    p = req.payload
    sys = "You are a senior CPA/CA specializing in financial analysis, management accounting, and strategic financial planning. Provide actionable financial insights."
    if req.action == "pl_analysis":
        prompt = f"Perform a comprehensive P&L analysis for a {p.get('business_type','SaaS')} business — {p.get('period','FY 2025')}.\nRevenue: {p.get('revenue_data','')}\nExpenses: {p.get('expense_data','')}\nProvide: Executive Summary, Gross margin, EBITDA, Expense breakdown, Key ratios vs industry benchmarks, 3 recommendations to improve profitability."
    elif req.action == "budget_forecast":
        prompt = f"Create a detailed budget forecast for {p.get('department','Engineering')} — {p.get('forecast_period','FY 2026')}.\nCurrent spend: {p.get('current_spend','')}\nGoals: {p.get('goals','')}\nGrowth rate: {p.get('growth_rate','20%')}\nInclude: Budget by category, Monthly phasing, Bear/Base/Bull scenarios, ROI projections, Approval recommendation."
    else:
        prompt = str(p)
    result = await _llm(sys, prompt, 800)
    return {"action": req.action, "result": result}


@router.post("/legal/enhance", summary="Contract review + NDA generator")
async def legal_enhance(req: EnhanceRequest, token: dict = Depends(verify_token)):
    p = req.payload
    sys = "You are a senior corporate lawyer specializing in commercial contracts. Provide clear legal analysis with practical recommendations. Note: AI guidance only — always consult a qualified attorney for actual legal matters."
    if req.action == "contract_review":
        prompt = f"Review this {p.get('contract_type','service agreement')} from {p.get('reviewing_party','our company')}'s perspective:\n\n{p.get('contract_text','')[:3000]}\n\nProvide: Executive summary, Key terms table (Term/Position/Risk), Red flags with clause references, Missing clauses, Negotiation leverage points, Recommended redlines with alternative language."
    elif req.action == "nda_generator":
        prompt = f"Draft a comprehensive {p.get('nda_type','mutual')} NDA between:\nParty 1: {p.get('party1','Company A')}\nParty 2: {p.get('party2','Company B')}\nPurpose: {p.get('purpose','business discussions')}\nDuration: {p.get('duration','2 years')}\nGoverning law: {p.get('jurisdiction','India — Karnataka')}\nInclude: Recitals, Definition of Confidential Information, Obligations, Permitted disclosures, Return/destruction clause, Remedies, Term, Dispute resolution, Signature blocks."
    else:
        prompt = str(p)
    result = await _llm(sys, prompt, 1000)
    return {"action": req.action, "result": result}


@router.post("/social/enhance", summary="SEO audit + campaign brief")
async def social_enhance(req: EnhanceRequest, token: dict = Depends(verify_token)):
    p = req.payload
    sys = "You are a senior digital marketing strategist specializing in SEO, content marketing, and integrated campaign management. Deliver data-driven strategies with measurable outcomes."
    if req.action == "seo_audit":
        prompt = f"Perform a comprehensive SEO audit for: {p.get('url','the website')}\nTarget keywords: {p.get('target_keywords','')}\nCompetitors: {p.get('competitors','')}\nPage content: {p.get('page_content','')[:800]}\nProvide: Technical SEO checklist (20 items PASS/FAIL), On-page score, Content gaps, Keyword opportunities, Backlink strategy, Core Web Vitals recommendations, Meta tag templates, 30-60-90 day roadmap."
    elif req.action == "campaign_brief":
        prompt = f"Create a comprehensive marketing campaign brief:\nProduct: {p.get('product','our product')}\nAudience: {p.get('target_audience','B2B decision makers')}\nBudget: {p.get('budget','₹5,00,000')}\nTimeline: {p.get('timeline','3 months')}\nChannels: {p.get('channels','LinkedIn, Google, Email')}\nGoal: {p.get('goal','generate leads')}\nInclude: Campaign theme + tagline, 3 audience personas, Messaging hierarchy, Channel budget allocation %, 4-week content calendar, KPIs + targets, A/B test plan, Creative brief."
    else:
        prompt = str(p)
    result = await _llm(sys, prompt, 800)
    return {"action": req.action, "result": result}


@router.post("/receptionist/enhance", summary="FAQ builder + SLA policy + escalation matrix")
async def receptionist_enhance(req: EnhanceRequest, token: dict = Depends(verify_token)):
    p = req.payload
    sys = "You are a senior customer success and support operations expert. You design support systems, documentation, and escalation frameworks that maximize customer satisfaction."
    if req.action == "faq_builder":
        prompt = f"Create a comprehensive FAQ document for {p.get('business_name','Our Company')} ({p.get('service_type','SaaS platform')}).\nCommon questions: {p.get('common_questions','')}\nGenerate 20 FAQs in categories: Getting Started, Account & Billing, Features & Usage, Troubleshooting, Integrations, Security & Privacy, Policies. Each FAQ: Question, concise answer (2-4 sentences)."
    elif req.action == "sla_policy":
        prompt = f"Create a comprehensive SLA policy for {p.get('company','Our Company')} ({p.get('service_type','B2B SaaS')}).\nSupport tiers: {p.get('support_tiers','free, pro, enterprise')}\nInclude: Response time SLAs by tier and severity, Resolution targets, Uptime guarantee, Maintenance windows, Escalation triggers, Credit policy, Support channels per tier, Business hours definition."
    elif req.action == "escalation_matrix":
        prompt = f"Design a support escalation matrix for {p.get('company','Our Company')}.\nTeam size: {p.get('team_size','10')} agents\nLevels: {p.get('escalation_levels','L1, L2 Technical, L3 Engineering, Management')}\nCreate: Escalation decision tree, RACI matrix per level, Escalation triggers by issue type, Communication templates, VIP customer handling, SLA clock management."
    else:
        prompt = str(p)
    result = await _llm(sys, prompt, 800)
    return {"action": req.action, "result": result}


@router.post("/analyst/enhance", summary="Data storytelling + anomaly detection analysis")
async def analyst_enhance(req: EnhanceRequest, token: dict = Depends(verify_token)):
    p = req.payload
    sys = "You are a senior data scientist and analytics strategist. You transform data insights into compelling narratives and design rigorous anomaly detection frameworks."
    if req.action == "data_story":
        prompt = f"Create a data storytelling narrative for {p.get('audience','executive leadership')} in {p.get('format','board presentation')} format.\nContext: {p.get('business_context','')}\nKey insights: {p.get('key_insights','')}\nStructure: Hook, Context, Data journey, Key finding, Implication, Recommendation, Call to action. Include chart title recommendations and executive summary (3 bullet points)."
    elif req.action == "anomaly_detection":
        prompt = f"Perform anomaly detection analysis for metric: {p.get('metric_name','API response time')}\nData: {p.get('data_points','')}\nExpected range: {p.get('expected_range','')}\nContext: {p.get('business_context','')}\nProvide: Statistical analysis, Anomaly identification, Root cause hypotheses (3 ranked), Impact assessment, Detection methodology recommendation, Alert threshold recommendations."
    else:
        prompt = str(p)
    result = await _llm(sys, prompt, 800)
    return {"action": req.action, "result": result}


@router.post("/agri/enhance", summary="Yield prediction + market intelligence")
async def agri_enhance(req: EnhanceRequest, token: dict = Depends(verify_token)):
    p = req.payload
    sys = "You are an agricultural scientist and agribusiness analyst with expertise in crop science, precision agriculture, and agricultural market intelligence."
    if req.action == "yield_prediction":
        prompt = f"Yield prediction and optimization for:\nCrop: {p.get('crop','tomato')} | Location: {p.get('location','Tamil Nadu')} | Area: {p.get('acreage','2 acres')} | Season: {p.get('season','Kharif')}\nSoil: {p.get('soil_type','red loamy')} | Rainfall: {p.get('rainfall_mm','600')}mm\nProvide: Expected yield (pessimistic/realistic/optimistic), Input optimization (fertilizer NPK schedule, irrigation), Pest risk calendar, Revenue calculation at MSP, Break-even analysis."
    elif req.action == "market_intelligence":
        prompt = f"Market intelligence for {p.get('commodity','tomato')} in {p.get('region','Tamil Nadu')}.\nCurrent price: {p.get('current_price','')}\nProvide: Price trend analysis (seasonal), Price drivers, Surplus/deficit assessment, Best selling time, Top 5 mandis + price ranges, Export opportunity, Value-added product opportunities, 3-month price outlook."
    else:
        prompt = str(p)
    result = await _llm(sys, prompt, 800)
    return {"action": req.action, "result": result, "language": req.language}


@router.post("/techlead/enhance", summary="Vendor evaluation + build-vs-buy analysis")
async def techlead_enhance(req: EnhanceRequest, token: dict = Depends(verify_token)):
    p = req.payload
    sys = "You are a principal engineer and technology strategist with 15+ years evaluating enterprise software, build-vs-buy decisions, and vendor management at scale."
    if req.action == "vendor_eval":
        prompt = f"Comprehensive vendor evaluation for: {p.get('vendor_name','Vendor')} ({p.get('category','platform')})\nBudget: {p.get('annual_budget','$50,000')}\nRequirements: {p.get('requirements','')}\nAlternatives: {p.get('alternatives','')}\nProvide: Vendor scorecard (10 criteria, 1-5), Feature gap analysis, TCO (3-year), Integration complexity, Vendor risk, Build-vs-buy recommendation, Contract negotiation points, Implementation timeline."
    elif req.action == "build_vs_buy":
        prompt = f"Build-vs-buy analysis for: {p.get('feature','authentication system')}\nTeam: {p.get('team_size','5')} engineers | Timeline: {p.get('timeline','3 months')}\nVendor options: {p.get('vendor_options','Auth0, Cognito, Okta')}\nProvide: Build cost estimate, Buy TCO (3-year), Opportunity cost, Risk matrix, Core-vs-context assessment, Recommendation with 5 reasons, Implementation roadmap."
    else:
        prompt = str(p)
    result = await _llm(sys, prompt, 800)
    return {"action": req.action, "result": result}


# ═══════════════════════════════════════════════════════════════════════════════
# NEW VERTICALS — Healthcare, Real Estate, EdTech
# ═══════════════════════════════════════════════════════════════════════════════

class VerticalActionRequest(BaseModel):
    action:  str  = Field(..., min_length=1)
    payload: dict = Field(default_factory=dict)
    language: str = Field(default="en")


@router.post("/healthcare/action", summary="AI Healthcare Assistant — intake, reports, Rx notes, claims, triage")
async def healthcare_action(req: VerticalActionRequest, token: dict = Depends(verify_token)):
    """
    Clinical documentation support: patient intake, report summary, prescription
    notes, insurance claim drafting, symptom triage. Decision-support only.
    """
    from backend.verticals.healthcare.healthcare_agent import healthcare_agent
    return await healthcare_agent(action=req.action, payload=req.payload, language=req.language)


@router.post("/realestate/action", summary="AI Real Estate — listings, leases, ROI, lead qualify, CMA")
async def realestate_action(req: VerticalActionRequest, token: dict = Depends(verify_token)):
    """
    Real estate workflows: listing copy, lease agreement drafts, investment ROI,
    lead qualification, comparative market analysis.
    """
    from backend.verticals.realestate.realestate_agent import realestate_agent
    return await realestate_agent(action=req.action, payload=req.payload, language=req.language)


@router.post("/edtech/action", summary="AI EdTech — course outlines, quizzes, lesson plans, reports, doubts")
async def edtech_action(req: VerticalActionRequest, token: dict = Depends(verify_token)):
    """
    Education workflows: course outlines, quiz generation, lesson plans,
    student progress reports, doubt solving.
    """
    from backend.verticals.edtech.edtech_agent import edtech_agent
    return await edtech_agent(action=req.action, payload=req.payload, language=req.language)


@router.post("/social/pro", summary="Social Media Pro — repurpose, competitor audit, ads, influencer, crisis, YT, email, reels, report, SEO cluster")
async def social_pro(req: SocialRequest, token: dict = Depends(verify_token)):
    """
    10 enterprise-depth social media features:
    repurpose | competitor_audit | ad_copy | influencer_brief | crisis_response |
    youtube_script | email_sequence | reel_script | monthly_report | keyword_cluster
    """
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
