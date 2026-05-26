# backend/verticals/sales/sales_agent.py
"""
AI Sales Assistant + Lead Qualifier (Feature 16).

Capabilities:
  1. Lead scoring 0–100 (BANT: Budget, Authority, Need, Timeline)
  2. HubSpot CRM integration — create/update contacts and deals
  3. Salesforce CRM integration — create Lead and Opportunity
  4. Clearbit enrichment — company/contact data from email domain
  5. AI-generated personalized outreach (GPT-4o-mini)
  6. Follow-up sequence scheduling (via existing task scheduler)
  7. Pipeline stage progression with HITL gate for high-value deals

Lead score interpretation:
  80-100 → HOT (immediate outreach, sales call)
  60-79  → WARM (nurture sequence, 3-day follow-up)
  40-59  → COOL (monthly newsletter, re-qualify in 30 days)
  0-39   → COLD (marketing automation only)
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from backend.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()


# ── Lead scoring (BANT model) ─────────────────────────────────────────────────

def score_lead(lead: dict) -> dict:
    """
    Score a lead 0–100 using BANT framework + firmographic signals.

    Input dict keys (all optional, scored by presence/value):
      budget_usd, has_budget, authority_level, has_need, timeline_days,
      company_size, industry, title, website, inbound_source,
      email_domain, phone, linkedin_url
    """
    score  = 0
    signals: list[str] = []

    # Budget (0–25 points)
    budget = lead.get("budget_usd", 0) or 0
    if budget >= 50000:
        score += 25; signals.append("Large budget (≥$50k)")
    elif budget >= 10000:
        score += 18; signals.append("Medium budget ($10k–$50k)")
    elif budget >= 1000:
        score += 10; signals.append("Small budget ($1k–$10k)")
    elif lead.get("has_budget"):
        score += 8;  signals.append("Has budget (unquantified)")

    # Authority (0–25 points)
    title = (lead.get("title") or "").lower()
    authority_level = lead.get("authority_level", "").lower()
    if any(kw in title for kw in ["ceo", "cto", "cfo", "coo", "founder", "owner", "vp", "president"]):
        score += 25; signals.append("C-level / VP authority")
    elif any(kw in title for kw in ["director", "head", "manager", "lead"]):
        score += 18; signals.append("Director / Manager level")
    elif authority_level in ("decision_maker", "high"):
        score += 20; signals.append("Confirmed decision maker")
    elif authority_level in ("influencer", "medium"):
        score += 12; signals.append("Influencer level")
    elif lead.get("has_authority"):
        score += 8

    # Need (0–25 points)
    need_score = 0
    if lead.get("has_need"):
        need_score += 15; signals.append("Confirmed need")
    if lead.get("pain_points"):
        need_score += 5;  signals.append("Pain points identified")
    if lead.get("current_solution"):
        need_score += 5;  signals.append("Has current solution (replacement opportunity)")
    score += min(25, need_score)

    # Timeline (0–25 points)
    timeline = lead.get("timeline_days", 365)
    if timeline and timeline <= 30:
        score += 25; signals.append("Immediate need (≤30 days)")
    elif timeline and timeline <= 90:
        score += 18; signals.append("Short timeline (≤90 days)")
    elif timeline and timeline <= 180:
        score += 10; signals.append("Medium timeline (≤6 months)")
    elif lead.get("has_timeline"):
        score += 5

    # Firmographic bonuses
    company_size = lead.get("company_size", 0) or 0
    if company_size >= 500:
        score += 5; signals.append("Enterprise company (500+ employees)")
    elif company_size >= 50:
        score += 3; signals.append("Mid-market company (50-499 employees)")

    if lead.get("inbound_source") in ("demo_request", "contact_sales", "trial"):
        score += 5; signals.append("Inbound high-intent source")

    if lead.get("website"):
        score += 2; signals.append("Has company website")

    if lead.get("linkedin_url"):
        score += 2; signals.append("LinkedIn profile available")

    # Cap at 100
    score = min(100, score)

    # Tier classification
    if score >= 80:
        tier = "HOT"
        next_action = "Immediate outreach — schedule discovery call within 24h"
    elif score >= 60:
        tier = "WARM"
        next_action = "Add to nurture sequence — follow up in 3 days"
    elif score >= 40:
        tier = "COOL"
        next_action = "Add to monthly newsletter — re-qualify in 30 days"
    else:
        tier = "COLD"
        next_action = "Add to marketing automation only"

    # Compute BANT sub-scores from accumulation order
    # Budget points: first block adds 0–25
    budget_pts = 0
    if budget >= 50000:              budget_pts = 25
    elif budget >= 10000:            budget_pts = 18
    elif budget >= 1000:             budget_pts = 10
    elif lead.get("has_budget"):     budget_pts = 8

    # Authority points
    auth_pts = 0
    if any(kw in title for kw in ["ceo","cto","cfo","coo","founder","owner","vp","president"]):
        auth_pts = 25
    elif any(kw in title for kw in ["director","head","manager","lead"]):
        auth_pts = 18
    elif authority_level in ("decision_maker","high"):  auth_pts = 20
    elif authority_level in ("influencer","medium"):    auth_pts = 12
    elif lead.get("has_authority"):                     auth_pts = 8

    # Need points
    need_pts = min(25, need_score)

    # Timeline points
    tl_pts = 0
    if timeline and timeline <= 30:       tl_pts = 25
    elif timeline and timeline <= 90:     tl_pts = 18
    elif timeline and timeline <= 180:    tl_pts = 10
    elif lead.get("has_timeline"):        tl_pts = 5

    return {
        "score":       score,
        "tier":        tier,
        "next_action": next_action,
        "signals":     signals,
        "bant": {
            "budget":    budget_pts,
            "authority": auth_pts,
            "need":      need_pts,
            "timeline":  tl_pts,
        },
        "scored_at": datetime.now(timezone.utc).isoformat(),
    }


# ── HubSpot CRM integration ───────────────────────────────────────────────────

async def create_hubspot_contact(
    email:      str,
    first_name: str = "",
    last_name:  str = "",
    company:    str = "",
    phone:      str = "",
    lead_score: int = 0,
) -> dict:
    """Create or update a HubSpot contact via HubSpot API v3."""
    api_key = settings.hubspot_api_key

    if not api_key:
        logger.info("HubSpot not configured — mock contact creation")
        return {
            "id":      "mock_hs_001",
            "email":   email,
            "status":  "mock",
            "note":    "Configure HUBSPOT_API_KEY for live CRM sync",
        }

    try:
        import httpx
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json",
        }
        payload = {
            "properties": {
                "email":      email,
                "firstname":  first_name,
                "lastname":   last_name,
                "company":    company,
                "phone":      phone,
                "hs_lead_status": "NEW",
                "hubspotscore": lead_score,
            }
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.hubapi.com/crm/v3/objects/contacts",
                headers=headers,
                json=payload,
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                return {"id": data.get("id"), "email": email, "status": "created"}
            elif resp.status_code == 409:
                # Contact exists — return existing
                return {"email": email, "status": "already_exists"}
            resp.raise_for_status()
    except Exception as e:
        logger.error("HubSpot contact creation failed: %s", e)
        return {"error": "HubSpot temporarily unavailable.", "email": email}


async def create_hubspot_deal(
    contact_id:  str,
    deal_name:   str,
    deal_stage:  str = "appointmentscheduled",
    amount:      float = 0.0,
    close_date:  Optional[str] = None,
) -> dict:
    """Create a HubSpot deal linked to a contact."""
    api_key = settings.hubspot_api_key
    if not api_key:
        return {"id": "mock_deal_001", "status": "mock", "deal_name": deal_name}

    try:
        import httpx
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "properties": {
                "dealname":  deal_name,
                "dealstage": deal_stage,
                "amount":    str(amount),
                "closedate": close_date or "",
            },
            "associations": [
                {
                    "to":   {"id": contact_id},
                    "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 3}],
                }
            ],
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.hubapi.com/crm/v3/objects/deals",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return {"id": data.get("id"), "deal_name": deal_name, "status": "created"}
    except Exception as e:
        logger.error("HubSpot deal creation failed: %s", e)
        return {"error": "Deal creation failed."}


# ── Salesforce CRM integration ────────────────────────────────────────────────

async def create_salesforce_lead(
    email:       str,
    first_name:  str = "",
    last_name:   str = "Unknown",
    company:     str = "",
    lead_source: str = "AI Assistant",
    lead_score:  int = 0,
) -> dict:
    """Create a Salesforce Lead via REST API."""
    sf_instance = settings.salesforce_instance_url
    sf_token    = settings.salesforce_access_token

    if not (sf_instance and sf_token):
        return {
            "id":     "mock_sf_001",
            "email":  email,
            "status": "mock",
            "note":   "Configure SALESFORCE_INSTANCE_URL + SALESFORCE_ACCESS_TOKEN",
        }

    try:
        import httpx
        headers = {
            "Authorization": f"Bearer {sf_token}",
            "Content-Type":  "application/json",
        }
        payload = {
            "LastName":    last_name or "Unknown",
            "FirstName":   first_name,
            "Company":     company or "Unknown",
            "Email":       email,
            "LeadSource":  lead_source,
            "Rating":      "Hot" if lead_score >= 80 else "Warm" if lead_score >= 60 else "Cold",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{sf_instance}/services/data/v58.0/sobjects/Lead/",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return {"id": data.get("id"), "email": email, "status": "created"}
    except Exception as e:
        logger.error("Salesforce Lead creation failed: %s", e)
        return {"error": "Salesforce temporarily unavailable."}


# ── Clearbit enrichment ───────────────────────────────────────────────────────

async def enrich_lead(email: str) -> dict:
    """
    Enrich lead data from Clearbit (company, job title, LinkedIn, etc.).
    Falls back to domain-based enrichment if Clearbit unavailable.
    """
    clearbit_key = settings.clearbit_api_key

    if not clearbit_key:
        # Domain-based mock enrichment
        domain = email.split("@")[-1] if "@" in email else ""
        company_hint = domain.split(".")[0].capitalize() if domain else ""
        return {
            "email":   email,
            "domain":  domain,
            "company": {"name": company_hint, "domain": domain},
            "person":  None,
            "mock":    True,
        }

    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"https://person.clearbit.com/v2/combined/find",
                params={"email": email},
                auth=(clearbit_key, ""),
            )
            if resp.status_code == 200:
                data = resp.json()
                person  = data.get("person", {})
                company = data.get("company", {})
                return {
                    "email":        email,
                    "name":         person.get("name", {}).get("fullName", ""),
                    "title":        person.get("employment", {}).get("title", ""),
                    "linkedin":     person.get("linkedin", {}).get("handle", ""),
                    "company": {
                        "name":        company.get("name", ""),
                        "domain":      company.get("domain", ""),
                        "size":        company.get("metrics", {}).get("employees", 0),
                        "industry":    company.get("category", {}).get("industry", ""),
                        "description": company.get("description", "")[:200],
                    },
                }
            return {"email": email, "error": "Enrichment unavailable.", "status": resp.status_code}
    except Exception as e:
        logger.warning("Clearbit enrichment failed (non-fatal): %s", e)
        return {"email": email, "error": "Enrichment service unavailable."}


# ── Outreach generation ───────────────────────────────────────────────────────

async def generate_outreach(
    lead:        dict,
    enrichment:  dict,
    tone:        str = "professional",
    product:     str = "our AI platform",
    language:    str = "en",
) -> str:
    """
    Generate a personalized outreach email for a lead using Ollama.
    Returns plain text email body only (subject included as first line).
    """
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL

    name    = enrichment.get("name") or lead.get("name") or "there"
    company = (enrichment.get("company") or {}).get("name") or lead.get("company") or "your company"
    title   = enrichment.get("title") or lead.get("title") or ""
    industry = (enrichment.get("company") or {}).get("industry") or ""
    score   = lead.get("lead_score", 50)

    system = (
        f"You are an expert B2B sales copywriter. "
        f"Write a {tone} cold outreach email in {language}. "
        f"Personalize for the recipient. "
        f"Keep it under 150 words. Focus on value, not features. "
        f"Include: Subject line (prefix 'Subject: '), greeting, 1-2 sentence hook, "
        f"value proposition, clear CTA. No excessive praise."
    )
    user = (
        f"Lead: {name} ({title}) at {company}"
        f"{f', industry: {industry}' if industry else ''}. "
        f"Lead score: {score}/100. Product: {product}. "
        f"Write the outreach email:"
    )

    try:
        result = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            model=OLLAMA_MODEL,
            max_tokens=300,
            temperature=0.7,
        )
        return result or ""
    except Exception as e:
        logger.error("Outreach generation failed: %s", e)
        return ""


# ── Main sales agent dispatcher ───────────────────────────────────────────────

async def sales_agent(
    action:      str,     # qualify | enrich | create_contact | generate_outreach | full_pipeline
    lead:        dict,
    crm:         str = "hubspot",   # hubspot | salesforce | none
    user_id:     str = "",
    session_id:  str = "",
    product:     str = "our AI platform",
    language:    str = "en",
) -> dict:
    """
    Main sales agent dispatcher.
    'full_pipeline' runs: enrich → score → create_contact → generate_outreach
    High-value deals (score >= 80, amount >= $50k) trigger HITL for human review.
    """
    result: dict = {"action": action, "timestamp": datetime.now(timezone.utc).isoformat()}

    email = lead.get("email", "")

    if action in ("qualify", "full_pipeline"):
        scored = score_lead(lead)
        lead["lead_score"]   = scored["score"]
        lead["lead_tier"]    = scored["tier"]
        result["score"]      = scored
        result["lead_score"] = scored["score"]
        result["lead_tier"]  = scored["tier"]

    if action in ("enrich", "full_pipeline") and email:
        enrichment         = await enrich_lead(email)
        result["enrichment"] = enrichment
        # Merge enrichment into lead
        if enrichment.get("company", {}).get("size"):
            lead["company_size"] = enrichment["company"]["size"]
        if enrichment.get("title"):
            lead["title"] = enrichment["title"]
        # Re-score with enriched data
        if action == "full_pipeline":
            scored = score_lead(lead)
            result["score"]      = scored
            result["lead_score"] = scored["score"]
    else:
        enrichment = {}

    if action in ("create_contact", "full_pipeline"):
        if crm == "hubspot":
            contact = await create_hubspot_contact(
                email=email,
                first_name=lead.get("first_name", ""),
                last_name=lead.get("last_name", ""),
                company=lead.get("company", ""),
                phone=lead.get("phone", ""),
                lead_score=lead.get("lead_score", 0),
            )
        elif crm == "salesforce":
            contact = await create_salesforce_lead(
                email=email,
                first_name=lead.get("first_name", ""),
                last_name=lead.get("last_name", "Unknown"),
                company=lead.get("company", ""),
                lead_score=lead.get("lead_score", 0),
            )
        else:
            contact = {"status": "no_crm", "email": email}
        result["crm_contact"] = contact

    if action in ("generate_outreach", "full_pipeline"):
        outreach = await generate_outreach(
            lead=lead,
            enrichment=enrichment,
            product=product,
            language=language,
        )
        result["outreach"] = outreach

    # HITL gate for hot leads with high deal value
    deal_amount = lead.get("budget_usd", 0) or 0
    lead_score  = result.get("lead_score", 0)
    if lead_score >= 80 and deal_amount >= 50000:
        try:
            from backend.hitl.hitl_manager import request_approval
            approval_id = await request_approval(
                action_type="high_value_lead_action",
                action_payload={
                    "email":        email,
                    "lead_score":   lead_score,
                    "deal_amount":  deal_amount,
                    "company":      lead.get("company", ""),
                },
                context_summary=(
                    f"High-value lead: {email} at {lead.get('company','')} "
                    f"(score {lead_score}, ${deal_amount:,.0f} budget) — "
                    f"review before outreach"
                ),
                user_id=user_id,
                session_id=session_id,
                expires_minutes=120,
            )
            result["hitl_required"]   = True
            result["hitl_approval_id"] = approval_id
            result["note"] = "High-value lead requires human review before outreach."
        except Exception as e:
            logger.warning("Sales HITL request failed (non-fatal): %s", e)

    return result
