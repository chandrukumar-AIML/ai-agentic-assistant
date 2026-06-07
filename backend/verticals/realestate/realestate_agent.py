"""
Real Estate Vertical — AI assistant for brokers, agencies, and property managers.

Actions:
  listing_generator — SEO-rich property listing copy across portals
  lease_agreement   — Draft a rental/lease agreement (India context)
  roi_calculator    — Investment ROI, rental yield, break-even analysis
  lead_qualify      — Qualify a buyer/seller/tenant lead with next steps
  market_cma        — Comparative Market Analysis & pricing recommendation
"""
from __future__ import annotations

import logging
import time

from backend.llm.router import llm_router

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a senior real-estate advisor and broker operating in the
Indian property market. You write persuasive, accurate, and compliant property
content and clear legal/financial documents. You understand RERA, stamp duty,
registration, rental norms, carpet vs built-up area, and Indian metro/tier-2
market dynamics. Legal drafts you produce are templates that must be reviewed by a
qualified lawyer before signing. Be specific, structured, and practical."""


async def _llm(prompt: str, max_tokens: int = 700) -> str:
    text, _ = await llm_router.complete(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.3,
        max_tokens=max_tokens,
    )
    return text


async def listing_generator(payload: dict) -> dict:
    prompt = f"""Write a compelling property listing.

Type: {payload.get('property_type', '2BHK Apartment')} | For: {payload.get('listing_for', 'Sale')}
Location: {payload.get('location', '')}
Area: {payload.get('area', '')} | Price: {payload.get('price', '')}
Key features: {payload.get('features', '')}
Amenities: {payload.get('amenities', '')}

Produce:
1. **Headline** (catchy, <70 chars)
2. **Portal listing copy** (99acres/MagicBricks style, 120-150 words, SEO keywords)
3. **Premium/luxury version** (emotional, lifestyle-focused)
4. **WhatsApp broadcast version** (short, emoji, CTA)
5. **15 SEO tags / search keywords**
6. **Suggested highlight bullets** (6 bullets)"""
    result = await _llm(prompt, 800)
    return {"action": "listing_generator", "result": result}


async def lease_agreement(payload: dict) -> dict:
    prompt = f"""Draft a rental/lease agreement TEMPLATE (India). Mark it clearly as a draft
for legal review.

Landlord: {payload.get('landlord', 'Owner Name')}
Tenant: {payload.get('tenant', 'Tenant Name')}
Property: {payload.get('property', '')}
Monthly rent: {payload.get('rent', '')} | Deposit: {payload.get('deposit', '')}
Lease term: {payload.get('term', '11 months')} | City/State: {payload.get('city', '')}

Include standard clauses: Parties, Property description, Term & renewal, Rent &
escalation, Security deposit & refund, Maintenance & utilities, Use restrictions,
Lock-in period, Notice period, Subletting, Repairs, Termination, Dispute
resolution & jurisdiction, Registration/stamp duty note, Signature & witness blocks.
End with a stamp-duty/registration guidance note for the given state."""
    result = await _llm(prompt, 1000)
    return {"action": "lease_agreement", "result": result}


async def roi_calculator(payload: dict) -> dict:
    prompt = f"""Perform a property investment analysis.

Purchase price: {payload.get('price', '')}
Down payment: {payload.get('down_payment', '')} | Loan rate: {payload.get('loan_rate', '8.5%')} | Tenure: {payload.get('tenure', '20 yrs')}
Expected monthly rent: {payload.get('rent', '')}
Annual appreciation est.: {payload.get('appreciation', '7%')}
Other costs (maintenance/tax): {payload.get('costs', '')}

Produce:
1. **EMI estimate** & total interest outgo
2. **Gross & net rental yield %**
3. **Cash-on-cash return**
4. **Break-even period**
5. **5-year & 10-year wealth projection** (appreciation + rent, table)
6. **Verdict**: good/average/poor investment with 3 reasons
7. **Key risks**"""
    result = await _llm(prompt, 800)
    return {"action": "roi_calculator", "result": result}


async def lead_qualify(payload: dict) -> dict:
    prompt = f"""Qualify this real-estate lead and recommend next actions.

Lead type: {payload.get('lead_type', 'Buyer')}
Requirement: {payload.get('requirement', '')}
Budget: {payload.get('budget', '')} | Timeline: {payload.get('timeline', '')}
Notes from call: {payload.get('notes', '')}

Produce:
1. **Lead score 0-100** (Budget / Authority / Need / Timeline breakdown)
2. **Hot / Warm / Cold** classification
3. **Best-fit inventory criteria** to match
4. **Next 3 actions** for the agent
5. **Suggested follow-up message** (WhatsApp tone)
6. **Objections likely + responses**"""
    result = await _llm(prompt, 600)
    return {"action": "lead_qualify", "result": result}


async def market_cma(payload: dict) -> dict:
    prompt = f"""Produce a Comparative Market Analysis (CMA) and pricing recommendation.

Subject property: {payload.get('property', '')}
Location/micro-market: {payload.get('location', '')}
Area: {payload.get('area', '')} | Condition/age: {payload.get('condition', '')}
Recent comparables (if provided): {payload.get('comparables', 'use general market knowledge')}

Produce:
1. **Micro-market overview** (demand, recent trend)
2. **Comparable pricing table** (₹/sqft range for the area)
3. **Recommended listing price** + justified range
4. **Pricing strategy** (aggressive vs market vs premium)
5. **Days-on-market estimate**
6. **Negotiation buffer recommendation**
7. **Factors that could move price ±10%**"""
    result = await _llm(prompt, 700)
    return {"action": "market_cma", "result": result}


async def realestate_agent(action: str, payload: dict, language: str = "en") -> dict:
    """Main Real Estate agent dispatcher."""
    action = (action or "").lower().strip()
    handlers = {
        "listing_generator": listing_generator,
        "lease_agreement":   lease_agreement,
        "roi_calculator":    roi_calculator,
        "lead_qualify":      lead_qualify,
        "market_cma":        market_cma,
    }
    handler = handlers.get(action)
    if not handler:
        return {"error": f"Unknown action '{action}'. Valid: {', '.join(handlers)}"}

    start  = time.monotonic()
    result = await handler(payload)
    result["latency_ms"] = round((time.monotonic() - start) * 1000)
    return result
