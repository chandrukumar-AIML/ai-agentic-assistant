# backend/verticals/ca_accounting/ca_agent.py
"""
AI CA / Accounting Agent — India-focused.

Capabilities:
  1. GST Query Bot       — answer any GST/HSN/rate question
  2. Client Email Drafter — plain-English emails to explain tax notices/filings
  3. Deadline Tracker    — GST/ITR/TDS/MCA deadline calendar
  4. TDS Calculator      — section-wise TDS with rates Finance Act 2025
  5. Invoice Drafter     — GST-compliant invoice content generator
  6. Audit Checklist     — generate audit prep checklist from client profile
  7. GST Reconciliation  — explain GSTR-2B mismatches, suggest resolution
  8. ITR Advisor         — ITR form selector + deduction optimizer
  9. CA Post Generator   — social media posts for CA firms (India-specific)
 10. Client Query Bot    — answer common client questions about tax/compliance
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


# ── GST rate table (common HSN/SAC) ──────────────────────────────────────────

_GST_RATES: dict[str, dict] = {
    "0%":  ["basic food grains", "milk", "eggs", "fresh vegetables", "fresh fruits", "education services", "healthcare services", "books"],
    "5%":  ["coffee", "tea", "edible oil", "sugar", "packed food", "economy hotels", "transport services", "life insurance"],
    "12%": ["computers", "processed food", "mobile phones", "business class hotels", "construction services"],
    "18%": ["IT services", "software", "professional services", "banking", "telecom", "restaurants", "CA services", "legal services", "rent of commercial property"],
    "28%": ["luxury cars", "tobacco", "pan masala", "aerated drinks", "casino", "high-end hotels"],
}

_TDS_SECTIONS: dict[str, dict] = {
    "194C": {"name": "Contractor/Subcontractor", "individual": 1.0, "company": 2.0, "threshold": 30000, "annual": 100000},
    "194J": {"name": "Professional/Technical Services", "individual": 10.0, "company": 10.0, "threshold": 30000, "annual": None},
    "194I": {"name": "Rent", "individual": 10.0, "company": 10.0, "threshold": 240000, "annual": None},
    "194H": {"name": "Commission/Brokerage", "individual": 5.0, "company": 5.0, "threshold": 15000, "annual": None},
    "192":  {"name": "Salary", "individual": "slab", "company": None, "threshold": 250000, "annual": None},
    "194A": {"name": "Interest (other than bank)", "individual": 10.0, "company": 10.0, "threshold": 5000, "annual": None},
    "194B": {"name": "Lottery/Winnings", "individual": 30.0, "company": 30.0, "threshold": 10000, "annual": None},
    "194Q": {"name": "Purchase of goods", "individual": 0.1, "company": 0.1, "threshold": 5000000, "annual": None},
    "194R": {"name": "Benefits/Perquisites", "individual": 10.0, "company": 10.0, "threshold": 20000, "annual": None},
}

_GST_DEADLINES = [
    {"form": "GSTR-1", "due": "11th of next month", "who": "All registered taxpayers with turnover > ₹1.5 Cr", "type": "monthly"},
    {"form": "GSTR-1 (Quarterly)", "due": "13th after quarter end", "who": "Taxpayers with turnover < ₹1.5 Cr (QRMP)", "type": "quarterly"},
    {"form": "GSTR-3B", "due": "20th of next month", "who": "All regular taxpayers", "type": "monthly"},
    {"form": "GSTR-9 (Annual)", "due": "31st December", "who": "All regular taxpayers (FY return)", "type": "annual"},
    {"form": "GSTR-9C", "due": "31st December", "who": "Taxpayers with turnover > ₹5 Cr (reconciliation)", "type": "annual"},
    {"form": "ITC-04", "due": "25th of month after quarter", "who": "Manufacturers sending goods for job work", "type": "quarterly"},
]

_ITR_FORMS = {
    "ITR-1 (Sahaj)": "Salaried individuals, pension, one house property, other income < ₹5000. Total income < ₹50 lakh.",
    "ITR-2": "Individuals/HUF with capital gains, foreign income, more than one house property. No business income.",
    "ITR-3": "Individuals/HUF with business or professional income (proprietorship).",
    "ITR-4 (Sugam)": "Presumptive income: business u/s 44AD, professional u/s 44ADA, transport u/s 44AE.",
    "ITR-5": "Firms, LLPs, AOPs, BOIs.",
    "ITR-6": "Companies (other than u/s 11 exemption).",
    "ITR-7": "Trusts, political parties, universities, institutions.",
}


# ── 1. GST Query Bot ──────────────────────────────────────────────────────────

async def answer_gst_query(
    query: str,
    context: str = "",
    language: str = "en",
) -> dict:
    """Answer any GST/HSN/rate/compliance question using AI."""
    from backend.llm.ollama_openai import ollama_chat_completion

    system = (
        "You are an expert Chartered Accountant with 15 years of India GST experience. "
        "You know the CGST Act 2017, IGST Act, GST rules, circulars, and recent notifications. "
        "Give accurate, practical answers. When in doubt, advise consulting GSTN portal or a CA. "
        f"Language: {language}. "
        "Format your response clearly with sections if needed."
    )
    user = f"GST Query: {query}"
    if context:
        user += f"\n\nAdditional context: {context}"

    try:
        answer = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            max_tokens=800,
            temperature=0.3,
        )
        return {
            "action":   "gst_query",
            "query":    query,
            "answer":   answer,
            "language": language,
        }
    except Exception as e:
        logger.error("GST query failed: %s", e)
        return {"error": f"GST query failed: {e}", "query": query}


# ── 2. Client Email Drafter ──────────────────────────────────────────────────

async def draft_client_email(
    email_type:    str,   # gst_notice | tds_notice | demand | refund | compliance_reminder | filing_done | audit_start
    client_name:   str,
    firm_name:     str,
    details:       str,
    amount:        str = "",
    deadline:      str = "",
    language:      str = "en",
) -> dict:
    """Draft professional plain-English client communication for tax matters."""
    from backend.llm.ollama_openai import ollama_chat_completion

    email_templates = {
        "gst_notice":          "GST department notice received — explain what it means and what action client needs to take",
        "tds_notice":          "TDS mismatch/demand notice — explain TDS default and resolution steps",
        "demand":              "Tax demand notice — explain demand amount, reason, and options (pay/appeal/rectification)",
        "refund":              "GST/income tax refund status update — explain timeline and next steps",
        "compliance_reminder": "Upcoming compliance deadline reminder — urgent but not alarming",
        "filing_done":         "Confirmation that filing is complete — give them peace of mind with details",
        "audit_start":         "Audit notice / assessment — prepare client, explain process, request documents",
        "advisory":            "General tax advisory or planning suggestion for the client",
    }
    email_context = email_templates.get(email_type, email_type)

    system = (
        "You are a CA writing professional emails to clients. "
        "Your clients are business owners who don't understand tax jargon. "
        "Write in clear, plain English (or the requested language). "
        "Be empathetic, not alarming. Explain what it means in simple terms. "
        "Include: what happened, what it means for them, what action is needed, and what you (the CA) will do. "
        f"Language: {language}. Firm name: {firm_name}."
    )
    user = (
        f"Email type: {email_context}\n"
        f"Client name: {client_name}\n"
        f"Details: {details}\n"
        f"{'Amount: ' + amount if amount else ''}\n"
        f"{'Deadline: ' + deadline if deadline else ''}\n\n"
        "Write the complete email (Subject + Body). Use [CLIENT NAME] and [FIRM NAME] as placeholders where appropriate."
    )

    try:
        email = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            max_tokens=700,
            temperature=0.4,
        )
        return {
            "action":     "client_email",
            "email_type": email_type,
            "client":     client_name,
            "email":      email,
        }
    except Exception as e:
        logger.error("Client email draft failed: %s", e)
        return {"error": f"Email draft failed: {e}"}


# ── 3. Deadline Tracker ───────────────────────────────────────────────────────

async def get_compliance_deadlines(
    month:       int = 0,
    year:        int = 0,
    taxpayer_type: str = "regular",  # regular | composition | qrmp
    state:       str = "",
) -> dict:
    """Return GST/ITR/TDS/MCA deadlines for the given month."""
    today = date.today()
    m = month or today.month
    y = year  or today.year

    month_name = datetime(y, m, 1).strftime("%B %Y")

    deadlines = []

    # GST deadlines
    if taxpayer_type in ("regular", "qrmp"):
        deadlines.append({"date": f"{m:02d}/11/{y}", "form": "GSTR-1", "description": "Outward supply return", "category": "GST", "priority": "high"})
        deadlines.append({"date": f"{m:02d}/20/{y}", "form": "GSTR-3B", "description": "Monthly summary return + tax payment", "category": "GST", "priority": "high"})

    if taxpayer_type == "composition":
        deadlines.append({"date": f"{m:02d}/18/{y}", "form": "CMP-08", "description": "Composition scheme quarterly payment", "category": "GST", "priority": "high"})

    # TDS deadlines
    deadlines.append({"date": f"{m:02d}/07/{y}", "form": "TDS Payment", "description": "Deposit TDS deducted in previous month", "category": "TDS", "priority": "high"})
    if m in (7, 10, 1):  # quarter end months + 1
        deadlines.append({"date": f"{m:02d}/31/{y}", "form": "TDS Return (24Q/26Q)", "description": "Quarterly TDS return filing", "category": "TDS", "priority": "high"})

    # ITR
    if m == 7:
        deadlines.append({"date": f"07/31/{y}", "form": "ITR Filing", "description": "Income Tax Return — individuals (non-audit)", "category": "ITR", "priority": "critical"})
    if m == 9:
        deadlines.append({"date": f"09/30/{y}", "form": "Tax Audit Report (3CD)", "description": "Tax audit report submission", "category": "Audit", "priority": "critical"})
        deadlines.append({"date": f"10/31/{y}", "form": "ITR Filing (Audit cases)", "description": "ITR for audit-required taxpayers", "category": "ITR", "priority": "high"})

    # Advance tax
    if m == 6:
        deadlines.append({"date": f"06/15/{y}", "form": "Advance Tax", "description": "1st installment — 15% of advance tax liability", "category": "Income Tax", "priority": "medium"})
    if m == 9:
        deadlines.append({"date": f"09/15/{y}", "form": "Advance Tax", "description": "2nd installment — 45% cumulative", "category": "Income Tax", "priority": "medium"})
    if m == 12:
        deadlines.append({"date": f"12/15/{y}", "form": "Advance Tax", "description": "3rd installment — 75% cumulative", "category": "Income Tax", "priority": "medium"})
    if m == 3:
        deadlines.append({"date": f"03/15/{y}", "form": "Advance Tax", "description": "4th installment — 100%", "category": "Income Tax", "priority": "high"})

    # MCA
    if m == 9:
        deadlines.append({"date": f"09/30/{y}", "form": "AOC-4", "description": "Financial statements filing with MCA (companies)", "category": "MCA", "priority": "medium"})
    if m == 10:
        deadlines.append({"date": f"10/31/{y}", "form": "MGT-7", "description": "Annual return filing with MCA", "category": "MCA", "priority": "medium"})

    return {
        "action":   "deadlines",
        "month":    month_name,
        "taxpayer": taxpayer_type,
        "count":    len(deadlines),
        "deadlines": sorted(deadlines, key=lambda d: d["date"]),
    }


# ── 4. TDS Calculator ─────────────────────────────────────────────────────────

async def calculate_tds(
    section:      str,    # 194C | 194J | 194I | 194H | etc.
    amount:       float,
    pan_available: bool = True,
    payee_type:   str = "individual",  # individual | company
) -> dict:
    """Calculate TDS amount for a given section and payment amount."""
    section = section.upper()
    if section not in _TDS_SECTIONS:
        return {
            "error":    f"Section {section} not in database. Supported: {list(_TDS_SECTIONS.keys())}",
            "section":  section,
        }

    sec = _TDS_SECTIONS[section]
    threshold = sec["threshold"]

    if amount < threshold:
        return {
            "action":    "tds_calc",
            "section":   section,
            "name":      sec["name"],
            "amount":    amount,
            "threshold": threshold,
            "tds":       0.0,
            "note":      f"No TDS — payment ₹{amount:,.2f} is below threshold ₹{threshold:,}",
        }

    rate_key = payee_type if payee_type in ("individual", "company") else "individual"
    rate = sec.get(rate_key, sec.get("individual", 0))

    if rate == "slab":
        return {
            "action":  "tds_calc",
            "section": section,
            "name":    sec["name"],
            "note":    "Salary TDS (Sec 192) is calculated per income-tax slab — use the salary TDS calculator.",
        }

    if not pan_available:
        rate = max(rate * 2, 20.0)  # 20% or twice the rate, whichever higher

    tds_amount = round(amount * rate / 100, 2)
    net_payment = round(amount - tds_amount, 2)

    return {
        "action":       "tds_calc",
        "section":      section,
        "name":         sec["name"],
        "gross_amount": amount,
        "tds_rate":     rate,
        "tds_amount":   tds_amount,
        "net_payment":  net_payment,
        "pan_available": pan_available,
        "payee_type":   payee_type,
        "due_date":     "7th of next month (or 30th April for March deductions)",
        "challan":      "ITNS 281 — select minor head based on payee type",
    }


# ── 5. Invoice Drafter ────────────────────────────────────────────────────────

async def draft_invoice(
    seller_name:   str,
    seller_gstin:  str,
    buyer_name:    str,
    buyer_gstin:   str = "",
    items:         list[dict] = None,   # [{desc, qty, rate, hsn_sac, gst_rate}]
    invoice_date:  str = "",
    place_of_supply: str = "",
    seller_state:  str = "",
    notes:         str = "",
) -> dict:
    """Generate GST-compliant invoice details with tax calculations."""
    today_str = invoice_date or date.today().strftime("%d/%m/%Y")
    items = items or []

    if not items:
        return {"error": "No line items provided. Add at least one item."}

    is_interstate = bool(
        seller_state and place_of_supply and
        seller_state.lower().strip() != place_of_supply.lower().strip()
    )

    line_items = []
    subtotal = 0.0
    total_cgst = 0.0
    total_sgst = 0.0
    total_igst = 0.0

    for item in items:
        qty       = float(item.get("qty", 1))
        rate      = float(item.get("rate", 0))
        gst_rate  = float(item.get("gst_rate", 18))
        taxable   = round(qty * rate, 2)
        subtotal += taxable

        if is_interstate:
            igst = round(taxable * gst_rate / 100, 2)
            total_igst += igst
            line_items.append({**item, "taxable": taxable, "igst": igst, "cgst": 0, "sgst": 0})
        else:
            cgst = round(taxable * gst_rate / 200, 2)
            sgst = cgst
            total_cgst += cgst
            total_sgst += sgst
            line_items.append({**item, "taxable": taxable, "cgst": cgst, "sgst": sgst, "igst": 0})

    total_tax   = round(total_cgst + total_sgst + total_igst, 2)
    grand_total = round(subtotal + total_tax, 2)

    # Amount in words (simple)
    def amount_words(n: float) -> str:
        try:
            import math
            n_int = int(n)
            if n_int >= 10_00_000:
                return f"Rupees {n_int / 10_00_000:.2f} Lakh only"
            if n_int >= 1000:
                return f"Rupees {n_int:,} only"
            return f"Rupees {n_int} only"
        except Exception:
            return f"Rupees {n:.2f} only"

    return {
        "action":          "invoice",
        "invoice_date":    today_str,
        "seller":          {"name": seller_name, "gstin": seller_gstin},
        "buyer":           {"name": buyer_name, "gstin": buyer_gstin},
        "place_of_supply": place_of_supply,
        "tax_type":        "IGST" if is_interstate else "CGST+SGST",
        "line_items":      line_items,
        "subtotal":        round(subtotal, 2),
        "total_cgst":      round(total_cgst, 2),
        "total_sgst":      round(total_sgst, 2),
        "total_igst":      round(total_igst, 2),
        "total_tax":       total_tax,
        "grand_total":     grand_total,
        "amount_in_words": amount_words(grand_total),
        "notes":           notes,
        "compliance_note": "This invoice is computer generated. Signature may not be required as per GST Rules.",
    }


# ── 6. Audit Checklist Generator ─────────────────────────────────────────────

async def generate_audit_checklist(
    client_name:    str,
    business_type:  str,   # proprietorship | partnership | pvt_ltd | llp | trust
    turnover_cr:    float,
    industry:       str,
    audit_type:     str = "tax_audit",  # tax_audit | statutory_audit | gst_audit | internal_audit
    fy:             str = "",
    language:       str = "en",
) -> dict:
    """Generate a comprehensive audit checklist for the given client profile."""
    from backend.llm.ollama_openai import ollama_chat_completion

    today = date.today()
    fy = fy or (f"{today.year-1}-{str(today.year)[2:]}" if today.month < 4 else f"{today.year}-{str(today.year+1)[2:]}")

    system = (
        "You are a senior Chartered Accountant with audit experience. "
        "Generate a comprehensive, actionable audit checklist. "
        "Be specific to the client's business type and industry. "
        f"Language: {language}."
    )
    prompt = (
        f"Client: {client_name}\n"
        f"Business type: {business_type}\n"
        f"Turnover: ₹{turnover_cr} Crores\n"
        f"Industry: {industry}\n"
        f"Audit type: {audit_type}\n"
        f"Financial year: {fy}\n\n"
        "Generate a detailed audit checklist organized by category:\n"
        "1. DOCUMENTS TO COLLECT FROM CLIENT (list each document)\n"
        "2. BOOKS OF ACCOUNTS verification points\n"
        "3. GST COMPLIANCE checks\n"
        "4. TDS COMPLIANCE checks\n"
        "5. INCOME TAX provisions to verify\n"
        "6. INDUSTRY-SPECIFIC checks (based on their sector)\n"
        "7. RED FLAGS to watch for in this type of business\n"
        "8. MANAGEMENT REPRESENTATION points\n"
        "9. REPORTING / DISCLOSURE requirements\n\n"
        "For each item, mark priority: [CRITICAL] [HIGH] [MEDIUM]"
    )

    try:
        checklist = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
            max_tokens=1200,
            temperature=0.3,
        )
        return {
            "action":       "audit_checklist",
            "client":       client_name,
            "audit_type":   audit_type,
            "fy":           fy,
            "turnover":     turnover_cr,
            "checklist":    checklist,
        }
    except Exception as e:
        logger.error("Audit checklist failed: %s", e)
        return {"error": f"Checklist generation failed: {e}"}


# ── 7. GST Reconciliation Advisor ────────────────────────────────────────────

async def advise_gst_reconciliation(
    mismatch_type:  str,   # gstr2b_mismatch | itc_reversal | output_mismatch | excess_credit
    mismatch_amount: str,
    client_name:    str,
    description:    str,
    language:       str = "en",
) -> dict:
    """Explain GST reconciliation issues and suggest step-by-step resolution."""
    from backend.llm.ollama_openai import ollama_chat_completion

    mismatch_context = {
        "gstr2b_mismatch":  "GSTR-2B shows different ITC than books — supplier hasn't filed or filed wrong amount",
        "itc_reversal":     "ITC reversal required — non-business use, exempt supplies, or Rule 42/43 reversal",
        "output_mismatch":  "Output tax liability differs between GSTR-1 and GSTR-3B",
        "excess_credit":    "ITC claimed is more than eligible — risk of demand notice",
        "late_filing":      "GSTR-1 filed late — impact on recipients claiming ITC",
        "amendment":        "Amendment required in previous month's return",
    }
    context = mismatch_context.get(mismatch_type, mismatch_type)

    system = (
        "You are a GST expert CA. Give step-by-step practical resolution advice for reconciliation issues. "
        "Be specific about which forms to use, which portals to check, and what entries to pass. "
        f"Language: {language}."
    )
    prompt = (
        f"Client: {client_name}\n"
        f"Issue type: {context}\n"
        f"Mismatch amount: {mismatch_amount}\n"
        f"Description: {description}\n\n"
        "Provide:\n"
        "1. ROOT CAUSE — why this happens typically\n"
        "2. IMMEDIATE ACTION — what to check first on GSTN portal\n"
        "3. STEP-BY-STEP RESOLUTION — exact steps with form names\n"
        "4. JOURNAL ENTRY — accounting entry to pass in books\n"
        "5. RISK ASSESSMENT — penalty/interest exposure if unresolved\n"
        "6. PREVENTION — how to avoid this next month"
    )

    try:
        advice = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
            max_tokens=900,
            temperature=0.3,
        )
        return {
            "action":         "reconciliation",
            "mismatch_type":  mismatch_type,
            "client":         client_name,
            "amount":         mismatch_amount,
            "resolution":     advice,
        }
    except Exception as e:
        logger.error("GST reconciliation advice failed: %s", e)
        return {"error": f"Reconciliation advice failed: {e}"}


# ── 8. ITR Advisor ────────────────────────────────────────────────────────────

async def advise_itr(
    income_sources:  list[str],   # salary | business | capital_gains | rental | other
    gross_income:    float,
    taxpayer_type:   str = "individual",  # individual | huf | firm | company
    age:             int = 35,
    has_80c:         bool = True,
    has_hra:         bool = False,
    has_home_loan:   bool = False,
    language:        str = "en",
) -> dict:
    """Recommend ITR form and deduction optimization strategy."""
    from backend.llm.ollama_openai import ollama_chat_completion

    sources_str = ", ".join(income_sources)

    # Determine ITR form
    if taxpayer_type == "individual":
        if "business" in income_sources or "professional" in income_sources:
            itr_form = "ITR-3"
            itr_reason = "Business/professional income requires ITR-3"
        elif "capital_gains" in income_sources:
            itr_form = "ITR-2"
            itr_reason = "Capital gains income not eligible for ITR-1"
        elif gross_income <= 5000000:
            itr_form = "ITR-1 (Sahaj)"
            itr_reason = "Salaried individual with income up to ₹50 lakh — simplest form"
        else:
            itr_form = "ITR-2"
            itr_reason = "Income exceeds ₹50 lakh or multiple house properties"
    elif taxpayer_type in ("firm", "llp"):
        itr_form = "ITR-5"
        itr_reason = "Firms and LLPs must use ITR-5"
    else:
        itr_form = "ITR-6"
        itr_reason = "Companies use ITR-6"

    system = (
        "You are a tax planning expert CA in India. "
        "Give practical, legal deduction optimization advice. "
        "Always mention the section numbers and limits. "
        f"Language: {language}."
    )
    prompt = (
        f"Taxpayer type: {taxpayer_type}, Age: {age}\n"
        f"Income sources: {sources_str}\n"
        f"Gross income: ₹{gross_income:,.0f}\n"
        f"80C investments done: {'Yes' if has_80c else 'No'}\n"
        f"HRA claim: {'Yes' if has_hra else 'No'}\n"
        f"Home loan: {'Yes' if has_home_loan else 'No'}\n\n"
        "Provide:\n"
        "1. RECOMMENDED ITR FORM with reason\n"
        "2. DEDUCTION CHECKLIST — all deductions they can claim (with section + limit)\n"
        "3. MISSED DEDUCTIONS — commonly missed ones for their profile\n"
        "4. TAX REGIME COMPARISON — Old vs New regime (which saves more)\n"
        "5. ADVANCE TAX CHECK — do they need to pay advance tax?\n"
        "6. DOCUMENTS REQUIRED — checklist for ITR filing\n"
        "7. ESTIMATED TAX SAVING — with all deductions applied"
    )

    try:
        advice = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
            max_tokens=1000,
            temperature=0.3,
        )
        return {
            "action":         "itr_advice",
            "itr_form":       itr_form,
            "itr_reason":     itr_reason,
            "taxpayer":       taxpayer_type,
            "income_sources": income_sources,
            "gross_income":   gross_income,
            "advice":         advice,
        }
    except Exception as e:
        logger.error("ITR advice failed: %s", e)
        return {"error": f"ITR advice failed: {e}"}


# ── 9. CA Social Media Post Generator ────────────────────────────────────────

async def generate_ca_social_post(
    topic:      str,  # gst_tip | deadline_reminder | budget_update | tax_saving | myth_bust | success_story
    platform:   str = "linkedin",
    firm_name:  str = "",
    language:   str = "en",
) -> dict:
    """Generate India-specific social media posts for CA firms."""
    from backend.llm.ollama_openai import ollama_chat_completion

    ca_post_contexts = {
        "gst_tip":          "Practical GST tip for small business owners",
        "deadline_reminder": "Upcoming tax/GST deadline reminder (friendly, not scary)",
        "budget_update":    "Union Budget impact for Indian businesses and individuals",
        "tax_saving":       "Legal tax saving strategies for individuals/businesses",
        "myth_bust":        "Bust a common tax myth or misconception",
        "success_story":    "Client success / tax saved / compliance achieved (anonymized)",
        "itr_tip":          "ITR filing tip or FAQ answer",
        "new_rule":         "New GST/income tax rule or notification update",
    }
    ctx = ca_post_contexts.get(topic, topic)

    system = (
        f"You are a CA firm's social media manager. Write engaging, educational social media posts for {platform}. "
        "The audience is Indian business owners, SMBs, and working professionals. "
        "Make tax/compliance content approachable, not scary. Use simple language. "
        f"Firm: {firm_name or 'our CA firm'}. Language: {language}."
    )
    prompt = (
        f"Post topic: {ctx}\n"
        f"Platform: {platform}\n\n"
        "Write a {platform} post that:\n"
        "- Opens with a hook that stops the scroll\n"
        "- Gives 1-3 actionable takeaways\n"
        "- Uses simple language (no jargon)\n"
        "- Ends with a CTA (comment, DM, or follow)\n"
        "- Includes 3-5 relevant hashtags\n"
        "- Tamil or Hindi version if language requested\n"
        "Keep it under 300 words for LinkedIn, 280 chars for Twitter."
    )

    try:
        post = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
            max_tokens=500,
            temperature=0.7,
        )
        return {
            "action":   "ca_social_post",
            "topic":    topic,
            "platform": platform,
            "post":     post,
        }
    except Exception as e:
        logger.error("CA social post failed: %s", e)
        return {"error": f"Post generation failed: {e}"}


# ── 10. Client Query Bot ──────────────────────────────────────────────────────

async def answer_client_query(
    query:      str,
    client_profile: str = "",  # brief description of client's business
    language:   str = "en",
) -> dict:
    """Answer common client questions about GST, TDS, ITR, invoices in plain language."""
    from backend.llm.ollama_openai import ollama_chat_completion

    system = (
        "You are a CA's assistant answering client queries in simple, plain language. "
        "The client is a business owner who doesn't know tax jargon. "
        "Explain things simply like you're talking to a friend. "
        "If a question needs professional CA judgment, say so and suggest scheduling a call. "
        f"Language: {language}. "
        f"{'Client profile: ' + client_profile if client_profile else ''}"
    )

    try:
        answer = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": f"Client question: {query}"},
            ],
            max_tokens=600,
            temperature=0.4,
        )
        return {
            "action":   "client_query",
            "query":    query,
            "answer":   answer,
            "language": language,
        }
    except Exception as e:
        logger.error("Client query bot failed: %s", e)
        return {"error": f"Query bot failed: {e}"}


# ── Compliance Calendar — Visual deadline tracker ─────────────────────────────

GST_DEADLINES = {
    1:  [("GSTR-3B", "20-Jan", "Monthly filers"), ("GSTR-1", "11-Jan", "Monthly filers"), ("TDS Q3 advance", "15-Jan", "All deductors")],
    2:  [("GSTR-3B", "20-Feb", "Monthly filers"), ("GSTR-1", "11-Feb", "Monthly filers")],
    3:  [("GSTR-3B", "20-Mar", "Monthly filers"), ("GSTR-1", "11-Mar", "Monthly filers"), ("Advance Tax Q4", "15-Mar", "All taxpayers"), ("TDS Q3 return", "31-Mar", "All deductors")],
    4:  [("GSTR-3B", "20-Apr", "Monthly filers"), ("GSTR-1", "11-Apr", "Monthly filers"), ("TDS Q4 advance", "15-Apr", "All deductors"), ("ITR FY deadline (extended)", "31-Jul", "Individuals")],
    5:  [("GSTR-3B", "20-May", "Monthly filers"), ("GSTR-1", "11-May", "Monthly filers")],
    6:  [("GSTR-3B", "20-Jun", "Monthly filers"), ("GSTR-1", "11-Jun", "Monthly filers"), ("Advance Tax Q1", "15-Jun", "All taxpayers")],
    7:  [("GSTR-3B", "20-Jul", "Monthly filers"), ("GSTR-1", "11-Jul", "Monthly filers"), ("ITR Filing Deadline", "31-Jul", "Individuals/HUF"), ("TDS Q1 return", "31-Jul", "All deductors")],
    8:  [("GSTR-3B", "20-Aug", "Monthly filers"), ("GSTR-1", "11-Aug", "Monthly filers")],
    9:  [("GSTR-3B", "20-Sep", "Monthly filers"), ("GSTR-1", "11-Sep", "Monthly filers"), ("Advance Tax Q2", "15-Sep", "All taxpayers"), ("GSTR-9 Annual", "31-Dec", "Regular taxpayers")],
    10: [("GSTR-3B", "20-Oct", "Monthly filers"), ("GSTR-1", "11-Oct", "Monthly filers"), ("TDS Q2 return", "31-Oct", "All deductors"), ("ITR Audit deadline", "30-Sep", "Audit cases")],
    11: [("GSTR-3B", "20-Nov", "Monthly filers"), ("GSTR-1", "11-Nov", "Monthly filers")],
    12: [("GSTR-3B", "20-Dec", "Monthly filers"), ("GSTR-1", "11-Dec", "Monthly filers"), ("Advance Tax Q3", "15-Dec", "All taxpayers"), ("GSTR-9 Annual", "31-Dec", "Regular taxpayers"), ("TDS Q3 return", "31-Jan-next", "All deductors")],
}

async def get_compliance_calendar(
    months:        list,   # [1, 2, 3] — month numbers
    taxpayer_type: str = "regular",   # regular | composition | quarterly
    include_tds:   bool = True,
    include_itr:   bool = True,
    firm_name:     str = "",
    language:      str = "en",
) -> dict:
    """Return structured compliance deadline calendar for selected months."""
    import datetime

    all_deadlines = []
    for m in months:
        month_items = GST_DEADLINES.get(m, [])
        month_name = datetime.date(2024, m, 1).strftime("%B")
        for form, date, who in month_items:
            if not include_tds and "TDS" in form:
                continue
            if not include_itr and "ITR" in form:
                continue
            urgency = "high" if any(k in form for k in ["3B", "ITR", "Advance Tax"]) else "medium"
            all_deadlines.append({
                "month": month_name,
                "month_num": m,
                "form": form,
                "due_date": date,
                "applicable_to": who,
                "urgency": urgency,
                "penalty": _deadline_penalty(form),
            })

    summary = {
        "total_deadlines": len(all_deadlines),
        "high_priority": sum(1 for d in all_deadlines if d["urgency"] == "high"),
        "months_covered": [datetime.date(2024, m, 1).strftime("%B") for m in months],
        "firm": firm_name,
    }
    return {"action": "compliance_calendar", "calendar": all_deadlines, "summary": summary}


def _deadline_penalty(form: str) -> str:
    if "3B" in form: return "₹50/day late fee + 18% interest on tax"
    if "GSTR-1" in form: return "₹50/day (nil return: ₹20/day)"
    if "TDS" in form: return "₹200/day + 1.5%/month interest"
    if "ITR" in form: return "₹5,000 late fee (₹1,000 if income < ₹5L)"
    if "Advance Tax" in form: return "1% interest/month u/s 234B & 234C"
    if "GSTR-9" in form: return "₹200/day (max 0.25% of turnover)"
    return "As per applicable section"


# ── Tally XML → AI GST Reconciliation ────────────────────────────────────────

async def analyze_tally_export(
    tally_data:    str,    # raw Tally XML or CSV text pasted by user
    analysis_type: str = "gst_reconciliation",  # gst_reconciliation | tds_summary | profit_loss | outstanding
    firm_name:     str = "",
    fy:            str = "",
    language:      str = "en",
) -> dict:
    """Parse Tally XML/CSV export and generate GST reconciliation or financial summary."""
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL
    import json

    TYPE_DESC = {
        "gst_reconciliation": "GST reconciliation — compare GSTR-1/3B with books, find mismatches",
        "tds_summary":        "TDS deduction summary — section-wise breakdown, verify 26AS",
        "profit_loss":        "P&L analysis — revenue, expenses, gross profit, net profit, ratios",
        "outstanding":        "Outstanding debtors/creditors — aging analysis, overdue alerts",
    }

    system = (
        f"You are a Chartered Accountant specializing in Tally ERP analysis for Indian businesses. "
        f"Task: {TYPE_DESC.get(analysis_type, analysis_type)}. Language: {language}. "
        "Parse the provided Tally export data and generate a structured CA-grade analysis."
    )
    data_preview = tally_data[:3000] if len(tally_data) > 3000 else tally_data
    prompt = (
        f"Firm: {firm_name or 'Client'} | FY: {fy or 'current'}\n"
        f"Analysis requested: {analysis_type}\n\n"
        f"Tally Export Data:\n{data_preview}\n\n"
        "Generate a structured analysis:\n"
        "1. DATA SUMMARY — what was detected (transaction count, date range, totals)\n"
        "2. KEY FINDINGS — 5 most important observations\n"
        "3. MISMATCHES / ISSUES — discrepancies, missing entries, errors\n"
        "4. RISK FLAGS — items requiring immediate CA attention (with ₹ amounts)\n"
        "5. RECOMMENDATIONS — specific actions to take before GST filing\n"
        "6. READY-TO-FILE STATUS — yes/no with reason\n\n"
        "Output as JSON: {data_summary, key_findings, mismatches, risk_flags, recommendations, ready_to_file, ready_reason}"
    )
    try:
        raw = await ollama_chat_completion(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            model=OLLAMA_MODEL, max_tokens=1000, temperature=0.3,
        )
        import re
        try:
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            data = json.loads(match.group()) if match else {}
        except Exception:
            data = {}
        return {
            "action": "tally_analysis",
            "analysis_type": analysis_type,
            "firm": firm_name,
            **data,
            "raw": raw if not data else None,
        }
    except Exception as e:
        logger.error("Tally analysis failed: %s", e)
        return {"error": "Tally analysis failed.", "detail": str(e)}


# ── Main dispatcher ───────────────────────────────────────────────────────────

async def ca_agent(
    action:  str,
    payload: dict,
    language: str = "en",
) -> dict:
    """Main CA Agent dispatcher."""

    if action == "gst_query":
        return await answer_gst_query(
            query=payload.get("query", ""),
            context=payload.get("context", ""),
            language=language,
        )

    elif action == "client_email":
        return await draft_client_email(
            email_type=payload.get("email_type", "advisory"),
            client_name=payload.get("client_name", ""),
            firm_name=payload.get("firm_name", ""),
            details=payload.get("details", ""),
            amount=payload.get("amount", ""),
            deadline=payload.get("deadline", ""),
            language=language,
        )

    elif action == "deadlines":
        return await get_compliance_deadlines(
            month=int(payload.get("month", 0)),
            year=int(payload.get("year", 0)),
            taxpayer_type=payload.get("taxpayer_type", "regular"),
            state=payload.get("state", ""),
        )

    elif action == "tds_calc":
        return await calculate_tds(
            section=payload.get("section", "194J"),
            amount=float(payload.get("amount", 0)),
            pan_available=bool(payload.get("pan_available", True)),
            payee_type=payload.get("payee_type", "individual"),
        )

    elif action == "invoice":
        return await draft_invoice(
            seller_name=payload.get("seller_name", ""),
            seller_gstin=payload.get("seller_gstin", ""),
            buyer_name=payload.get("buyer_name", ""),
            buyer_gstin=payload.get("buyer_gstin", ""),
            items=payload.get("items", []),
            invoice_date=payload.get("invoice_date", ""),
            place_of_supply=payload.get("place_of_supply", ""),
            seller_state=payload.get("seller_state", ""),
            notes=payload.get("notes", ""),
        )

    elif action == "audit_checklist":
        return await generate_audit_checklist(
            client_name=payload.get("client_name", ""),
            business_type=payload.get("business_type", "proprietorship"),
            turnover_cr=float(payload.get("turnover_cr", 1.0)),
            industry=payload.get("industry", ""),
            audit_type=payload.get("audit_type", "tax_audit"),
            fy=payload.get("fy", ""),
            language=language,
        )

    elif action == "reconciliation":
        return await advise_gst_reconciliation(
            mismatch_type=payload.get("mismatch_type", "gstr2b_mismatch"),
            mismatch_amount=payload.get("mismatch_amount", ""),
            client_name=payload.get("client_name", ""),
            description=payload.get("description", ""),
            language=language,
        )

    elif action == "itr_advice":
        return await advise_itr(
            income_sources=payload.get("income_sources", ["salary"]),
            gross_income=float(payload.get("gross_income", 500000)),
            taxpayer_type=payload.get("taxpayer_type", "individual"),
            age=int(payload.get("age", 35)),
            has_80c=bool(payload.get("has_80c", True)),
            has_hra=bool(payload.get("has_hra", False)),
            has_home_loan=bool(payload.get("has_home_loan", False)),
            language=language,
        )

    elif action == "ca_social_post":
        return await generate_ca_social_post(
            topic=payload.get("topic", "gst_tip"),
            platform=payload.get("platform", "linkedin"),
            firm_name=payload.get("firm_name", ""),
            language=language,
        )

    elif action == "client_query":
        return await answer_client_query(
            query=payload.get("query", ""),
            client_profile=payload.get("client_profile", ""),
            language=language,
        )

    elif action == "compliance_calendar":
        return await get_compliance_calendar(
            months=payload.get("months", []),
            taxpayer_type=payload.get("taxpayer_type", "regular"),
            include_tds=bool(payload.get("include_tds", True)),
            include_itr=bool(payload.get("include_itr", True)),
            firm_name=payload.get("firm_name", ""),
            language=language,
        )

    elif action == "tally_analysis":
        return await analyze_tally_export(
            tally_data=payload.get("tally_data", ""),
            analysis_type=payload.get("analysis_type", "gst_reconciliation"),
            firm_name=payload.get("firm_name", ""),
            fy=payload.get("fy", ""),
            language=language,
        )

    elif action == "generate_invoice":
        return await generate_gst_invoice(
            seller=payload.get("seller", {}),
            buyer=payload.get("buyer", {}),
            items=payload.get("items", []),
            invoice_no=payload.get("invoice_no", ""),
            invoice_date=payload.get("invoice_date", ""),
            payment_terms=payload.get("payment_terms", ""),
            notes=payload.get("notes", ""),
            language=language,
        )

    elif action == "mca_roc_calendar":
        return generate_mca_roc_calendar(
            company_name=payload.get("company_name", ""),
            entity_type=payload.get("entity_type", "private_limited"),
            fy_end_month=payload.get("fy_end_month", "March"),
            has_msme_vendors=payload.get("has_msme_vendors", False),
            has_deposits=payload.get("has_deposits", False),
            is_newly_incorporated=payload.get("is_newly_incorporated", False),
            language=language,
        )

    elif action == "directors_report":
        return generate_directors_report(
            company_name=payload.get("company_name", ""),
            cin=payload.get("cin", ""),
            fy_start=payload.get("fy_start", ""),
            fy_end=payload.get("fy_end", ""),
            revenue=payload.get("revenue", 0),
            profit_before_tax=payload.get("profit_before_tax", 0),
            profit_after_tax=payload.get("profit_after_tax", 0),
            dividend_declared=payload.get("dividend_declared", False),
            dividend_per_share=payload.get("dividend_per_share", 0),
            directors=payload.get("directors", []),
            new_directors=payload.get("new_directors", []),
            resigned_directors=payload.get("resigned_directors", []),
            auditor_status=payload.get("auditor_status", "no_qualification"),
            csr_applicable=payload.get("csr_applicable", False),
            csr_amount_spent=payload.get("csr_amount_spent", 0),
            foreign_exchange_earnings=payload.get("foreign_exchange_earnings", 0),
            foreign_exchange_outgo=payload.get("foreign_exchange_outgo", 0),
            language=language,
        )

    elif action == "startup_guide":
        return generate_startup_registration_guide(
            startup_name=payload.get("startup_name", ""),
            entity_type=payload.get("entity_type", "private_limited"),
            industry_sector=payload.get("industry_sector", ""),
            state=payload.get("state", "Tamil Nadu"),
            founders_count=payload.get("founders_count", 2),
            language=language,
        )

    elif action == "partnership_deed":
        return generate_partnership_deed(
            firm_name=payload.get("firm_name", ""),
            business_nature=payload.get("business_nature", ""),
            registered_address=payload.get("registered_address", ""),
            commencement_date=payload.get("commencement_date", ""),
            duration=payload.get("duration", "at_will"),
            partners=payload.get("partners", []),
            profit_loss_ratio=payload.get("profit_loss_ratio", ""),
            bank_name=payload.get("bank_name", ""),
            language=language,
        )
    elif action == "advance_tax":
        return generate_advance_tax(
            taxpayer_name=payload.get("taxpayer_name", ""),
            taxpayer_type=payload.get("taxpayer_type", "individual"),
            financial_year=payload.get("financial_year", "2025-26"),
            estimated_income=float(payload.get("estimated_income", 0)),
            tds_deducted=float(payload.get("tds_deducted", 0)),
            regime=payload.get("regime", "new"),
            business_income=float(payload.get("business_income", 0)),
            salary_income=float(payload.get("salary_income", 0)),
            capital_gains_stcg=float(payload.get("capital_gains_stcg", 0)),
            capital_gains_ltcg=float(payload.get("capital_gains_ltcg", 0)),
            other_income=float(payload.get("other_income", 0)),
            deductions_80c=float(payload.get("deductions_80c", 0)),
            language=language,
        )
    elif action == "balance_sheet":
        return generate_balance_sheet(
            company_name=payload.get("company_name", ""),
            period=payload.get("period", ""),
            industry=payload.get("industry", "services"),
            land_building=float(payload.get("land_building", 0)),
            plant_machinery=float(payload.get("plant_machinery", 0)),
            furniture=float(payload.get("furniture", 0)),
            vehicles=float(payload.get("vehicles", 0)),
            intangibles=float(payload.get("intangibles", 0)),
            cash=float(payload.get("cash", 0)),
            bank=float(payload.get("bank", 0)),
            debtors=float(payload.get("debtors", 0)),
            inventory=float(payload.get("inventory", 0)),
            loans_advances=float(payload.get("loans_advances", 0)),
            other_current=float(payload.get("other_current", 0)),
            share_capital=float(payload.get("share_capital", 0)),
            reserves_surplus=float(payload.get("reserves_surplus", 0)),
            long_term_loans=float(payload.get("long_term_loans", 0)),
            deferred_tax=float(payload.get("deferred_tax", 0)),
            creditors=float(payload.get("creditors", 0)),
            short_term_loans=float(payload.get("short_term_loans", 0)),
            provisions=float(payload.get("provisions", 0)),
            other_current_liab=float(payload.get("other_current_liab", 0)),
            language=language,
        )
    elif action == "form_16":
        return generate_form16(
            employee_name=payload.get("employee_name", ""),
            employee_pan=payload.get("employee_pan", ""),
            employee_designation=payload.get("employee_designation", ""),
            employer_name=payload.get("employer_name", ""),
            employer_tan=payload.get("employer_tan", ""),
            employer_pan=payload.get("employer_pan", ""),
            employer_address=payload.get("employer_address", ""),
            financial_year=payload.get("financial_year", "2024-25"),
            assessment_year=payload.get("assessment_year", "2025-26"),
            gross_salary=payload.get("gross_salary", 0),
            basic_salary=payload.get("basic_salary", 0),
            hra_received=payload.get("hra_received", 0),
            hra_exemption=payload.get("hra_exemption", 0),
            lta=payload.get("lta", 0),
            other_allowances=payload.get("other_allowances", 0),
            standard_deduction=payload.get("standard_deduction", 50000),
            professional_tax=payload.get("professional_tax", 0),
            deduction_80c=payload.get("deduction_80c", 0),
            deduction_80d=payload.get("deduction_80d", 0),
            deduction_80ccd=payload.get("deduction_80ccd", 0),
            other_deductions=payload.get("other_deductions", 0),
            tds_q1=payload.get("tds_q1", 0),
            tds_q2=payload.get("tds_q2", 0),
            tds_q3=payload.get("tds_q3", 0),
            tds_q4=payload.get("tds_q4", 0),
        )

    elif action == "client_compliance_status":
        import datetime
        today = datetime.date.today()
        return generate_client_compliance_status(
            client_name=payload.get("client_name", ""),
            pan=payload.get("pan", ""),
            gstin=payload.get("gstin", ""),
            business_type=payload.get("business_type", "proprietorship"),
            filing_type=payload.get("filing_type", "monthly"),
            state=payload.get("state", "Karnataka"),
            turnover_lakh=payload.get("turnover_lakh", 0),
            has_employees=payload.get("has_employees", False),
            is_audit_case=payload.get("is_audit_case", False),
            current_month=today.month,
            current_year=today.year,
        )

    elif action == "salary_slip":
        return generate_salary_slip(
            employee_name=payload.get("employee_name", ""),
            employee_id=payload.get("employee_id", ""),
            designation=payload.get("designation", ""),
            department=payload.get("department", ""),
            company_name=payload.get("company_name", ""),
            month_year=payload.get("month_year", ""),
            ctc_annual=payload.get("ctc_annual", 0),
            basic_pct=payload.get("basic_pct", 40),
            hra_pct=payload.get("hra_pct", 20),
            city_tier=payload.get("city_tier", "metro"),
            pf_applicable=payload.get("pf_applicable", True),
            pt_state=payload.get("pt_state", "karnataka"),
            bonus=payload.get("bonus", 0),
            advance_deduction=payload.get("advance_deduction", 0),
            lop_days=payload.get("lop_days", 0),
            working_days=payload.get("working_days", 26),
        )

    elif action == "itr_checklist":
        return generate_itr_checklist(
            taxpayer_name=payload.get("taxpayer_name", ""),
            pan=payload.get("pan", ""),
            assessment_year=payload.get("assessment_year", "2025-26"),
            income_sources=payload.get("income_sources", []),
            has_foreign_income=payload.get("has_foreign_income", False),
            has_crypto=payload.get("has_crypto", False),
            has_home_loan=payload.get("has_home_loan", False),
            deductions=payload.get("deductions", []),
            taxpayer_type=payload.get("taxpayer_type", "individual"),
        )

    elif action == "depreciation_calc":
        return generate_depreciation_calc(
            asset_name=payload.get("asset_name", ""),
            asset_category=payload.get("asset_category", "plant_machinery"),
            cost=payload.get("cost", 0),
            purchase_date=payload.get("purchase_date", ""),
            useful_life_years=payload.get("useful_life_years", 5),
            salvage_value=payload.get("salvage_value", 0),
            method=payload.get("method", "slm"),
            financial_year_start=payload.get("financial_year_start", 2024),
        )

    elif action == "gst_invoice":
        return generate_gst_invoice(
            seller_name=payload.get("seller_name", ""),
            seller_gstin=payload.get("seller_gstin", ""),
            seller_address=payload.get("seller_address", ""),
            seller_state=payload.get("seller_state", "karnataka"),
            buyer_name=payload.get("buyer_name", ""),
            buyer_gstin=payload.get("buyer_gstin", ""),
            buyer_address=payload.get("buyer_address", ""),
            buyer_state=payload.get("buyer_state", "karnataka"),
            invoice_number=payload.get("invoice_number", ""),
            invoice_date=payload.get("invoice_date", ""),
            items=payload.get("items", []),
            reverse_charge=payload.get("reverse_charge", False),
            payment_terms=payload.get("payment_terms", "30 days"),
            notes=payload.get("notes", ""),
        )

    elif action == "client_proposal":
        return generate_client_proposal(
            firm_name=payload.get("firm_name", ""),
            client_name=payload.get("client_name", ""),
            client_industry=payload.get("client_industry", ""),
            client_turnover=payload.get("client_turnover", ""),
            services=payload.get("services", []),
            fee_type=payload.get("fee_type", "monthly_retainer"),
            engagement_start=payload.get("engagement_start", ""),
            ca_name=payload.get("ca_name", ""),
        )

    elif action == "tds_compliance_tracker":
        return generate_tds_compliance_tracker(
            company_name=payload.get("company_name", ""),
            month=int(payload.get("month", 0) or 0),
            year=int(payload.get("year", 0) or 0),
            deductions=payload.get("deductions", []),
            pan_verified=bool(payload.get("pan_verified", True)),
        )

    elif action == "msme_loan_eligibility":
        return calculate_msme_loan_eligibility(
            company_name=payload.get("company_name", ""),
            business_type=payload.get("business_type", "manufacturing"),
            annual_turnover=float(payload.get("annual_turnover", 0) or 0),
            plant_machinery_value=float(payload.get("plant_machinery_value", 0) or 0),
            years_in_business=int(payload.get("years_in_business", 1) or 1),
            loan_purpose=payload.get("loan_purpose", "working_capital"),
            loan_amount_requested=float(payload.get("loan_amount_requested", 0) or 0),
            existing_loans=float(payload.get("existing_loans", 0) or 0),
            monthly_revenue=float(payload.get("monthly_revenue", 0) or 0),
            gst_registered=bool(payload.get("gst_registered", True)),
        )

    elif action == "pl_statement":
        return generate_pl_statement(
            company_name=payload.get("company_name", ""),
            period=payload.get("period", ""),
            revenue_items=payload.get("revenue_items", []),
            cogs_items=payload.get("cogs_items", []),
            opex_items=payload.get("opex_items", []),
            other_income=float(payload.get("other_income", 0) or 0),
            tax_rate=float(payload.get("tax_rate", 25) or 25),
            industry=payload.get("industry", "general"),
            prev_period_revenue=float(payload.get("prev_period_revenue", 0) or 0),
            prev_period_profit=float(payload.get("prev_period_profit", 0) or 0),
        )

    elif action == "overdue_collector":
        return generate_overdue_collection(
            company_name=payload.get("company_name", ""),
            invoices=payload.get("invoices", []),
            contact_name=payload.get("contact_name", ""),
            sender_name=payload.get("sender_name", ""),
            payment_terms=payload.get("payment_terms", "Net 30"),
            late_fee_pct=float(payload.get("late_fee_pct", 2) or 2),
        )

    elif action == "cash_flow_forecast":
        return calculate_cash_flow_forecast(
            company_name=payload.get("company_name", ""),
            monthly_revenue=float(payload.get("monthly_revenue", 0) or 0),
            revenue_growth=float(payload.get("revenue_growth", 5) or 5),
            fixed_expenses=float(payload.get("fixed_expenses", 0) or 0),
            variable_expense_pct=float(payload.get("variable_expense_pct", 30) or 30),
            opening_cash=float(payload.get("opening_cash", 0) or 0),
            one_time_inflows=payload.get("one_time_inflows", []),
            one_time_outflows=payload.get("one_time_outflows", []),
            industry=payload.get("industry", "general"),
        )

    elif action == "business_valuation":
        return calculate_business_valuation(
            revenue=float(payload.get("revenue", 0) or 0),
            ebitda=float(payload.get("ebitda", 0) or 0),
            net_profit=float(payload.get("net_profit", 0) or 0),
            industry=payload.get("industry", "technology"),
            stage=payload.get("stage", "growth"),
            growth_rate=float(payload.get("growth_rate", 20) or 20),
            assets=float(payload.get("assets", 0) or 0),
            liabilities=float(payload.get("liabilities", 0) or 0),
            language=language,
        )

    elif action == "gst_notice_reply":
        return await draft_gst_notice_reply(
            notice_type=payload.get("notice_type", ""),
            notice_ref=payload.get("notice_ref", ""),
            gstin=payload.get("gstin", ""),
            taxpayer_name=payload.get("taxpayer_name", ""),
            notice_details=payload.get("notice_details", ""),
            reply_points=payload.get("reply_points", ""),
            language=language,
        )

    elif action == "payroll":
        return calculate_payroll(
            employees=payload.get("employees", []),
            company_name=payload.get("company_name", ""),
            month=payload.get("month", ""),
            language=language,
        )

    elif action == "tax_planning":
        return await optimize_tax_planning(
            income_details=payload.get("income_details", {}),
            investments=payload.get("investments", {}),
            expenses=payload.get("expenses", {}),
            taxpayer_type=payload.get("taxpayer_type", "individual"),
            age=int(payload.get("age", 30)),
            regime=payload.get("regime", "old"),
            language=language,
        )

    elif action == "gstr_filing_prep":
        return await prepare_gstr_filing(
            sales_data=payload.get("sales_data", []),
            purchase_data=payload.get("purchase_data", []),
            return_type=payload.get("return_type", "gstr3b"),
            firm_name=payload.get("firm_name", ""),
            gstin=payload.get("gstin", ""),
            period=payload.get("period", ""),
            language=language,
        )

    return {"error": f"Unknown CA action: {action}"}


# ── GST Invoice Generator (Round 4) ──────────────────────────────────────────

GST_RATES = [0, 5, 12, 18, 28]


def _calculate_gst(amount: float, gst_rate: float, supply_type: str = "intra") -> dict:
    """Calculate CGST/SGST (intra-state) or IGST (inter-state)."""
    gst_amount = round(amount * gst_rate / 100, 2)
    if supply_type == "inter":
        return {"igst": gst_amount, "cgst": 0.0, "sgst": 0.0, "total_gst": gst_amount}
    half = round(gst_amount / 2, 2)
    return {"igst": 0.0, "cgst": half, "sgst": gst_amount - half, "total_gst": gst_amount}


async def generate_gst_invoice(
    seller:        dict,
    buyer:         dict,
    items:         list[dict],
    invoice_no:    str = "",
    invoice_date:  str = "",
    payment_terms: str = "Due on receipt",
    notes:         str = "",
    language:      str = "en",
) -> dict:
    """
    Generate a GST-compliant invoice with line-item tax breakdown.
    seller/buyer: {name, gstin, address, state}
    items: [{description, hsn, qty, unit, rate, gst_rate}]
    """
    from datetime import datetime, timezone
    import uuid

    inv_no   = invoice_no  or f"INV-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
    inv_date = invoice_date or datetime.now(timezone.utc).strftime("%d/%m/%Y")

    # Determine supply type from states
    seller_state = (seller.get("state") or "").strip().lower()
    buyer_state  = (buyer.get("state")  or "").strip().lower()
    supply_type  = "inter" if seller_state and buyer_state and seller_state != buyer_state else "intra"

    line_items = []
    subtotal = 0.0
    total_cgst = total_sgst = total_igst = 0.0

    for item in items:
        qty      = float(item.get("qty", 1))
        rate     = float(item.get("rate", 0))
        gst_rate = float(item.get("gst_rate", 18))
        taxable  = round(qty * rate, 2)
        tax      = _calculate_gst(taxable, gst_rate, supply_type)
        total_amount = round(taxable + tax["total_gst"], 2)

        subtotal   += taxable
        total_cgst += tax["cgst"]
        total_sgst += tax["sgst"]
        total_igst += tax["igst"]

        line_items.append({
            "description": item.get("description", ""),
            "hsn":         item.get("hsn", ""),
            "qty":         qty,
            "unit":        item.get("unit", "Nos"),
            "rate":        rate,
            "taxable":     taxable,
            "gst_rate":    gst_rate,
            **tax,
            "total_amount": total_amount,
        })

    subtotal    = round(subtotal, 2)
    total_cgst  = round(total_cgst, 2)
    total_sgst  = round(total_sgst, 2)
    total_igst  = round(total_igst, 2)
    grand_total = round(subtotal + total_cgst + total_sgst + total_igst, 2)

    # Round off
    rounded_total = round(grand_total)
    round_off     = round(rounded_total - grand_total, 2)

    # Amount in words (simple)
    def _amount_words(n: int) -> str:
        ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
                "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
                "Seventeen", "Eighteen", "Nineteen"]
        tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
        if n == 0: return "Zero"
        if n < 20: return ones[n]
        if n < 100: return tens[n // 10] + ("" if n % 10 == 0 else " " + ones[n % 10])
        if n < 1000: return ones[n // 100] + " Hundred" + ("" if n % 100 == 0 else " " + _amount_words(n % 100))
        if n < 100000: return _amount_words(n // 1000) + " Thousand" + ("" if n % 1000 == 0 else " " + _amount_words(n % 1000))
        if n < 10000000: return _amount_words(n // 100000) + " Lakh" + ("" if n % 100000 == 0 else " " + _amount_words(n % 100000))
        return _amount_words(n // 10000000) + " Crore" + ("" if n % 10000000 == 0 else " " + _amount_words(n % 10000000))

    amount_words = _amount_words(rounded_total) + " Rupees Only"

    return {
        "action": "generate_invoice",
        "invoice_no":     inv_no,
        "invoice_date":   inv_date,
        "payment_terms":  payment_terms,
        "supply_type":    supply_type,
        "seller":         seller,
        "buyer":          buyer,
        "line_items":     line_items,
        "subtotal":       subtotal,
        "total_cgst":     total_cgst,
        "total_sgst":     total_sgst,
        "total_igst":     total_igst,
        "total_gst":      round(total_cgst + total_sgst + total_igst, 2),
        "round_off":      round_off,
        "grand_total":    rounded_total,
        "amount_in_words": amount_words,
        "notes":          notes,
        "gst_compliant":  True,
    }


# ── GSTR Filing Prep (Round 5) ────────────────────────────────────────────────

def _sum_by_rate(rows: list[dict], amount_key: str = "taxable_value") -> dict:
    """Group sales/purchase rows by GST rate, sum taxable + taxes."""
    buckets: dict = {}
    for r in rows:
        rate = float(r.get("gst_rate", 18))
        taxable = float(r.get("taxable_value", 0) or r.get("taxable", 0))
        cgst  = float(r.get("cgst", 0))
        sgst  = float(r.get("sgst", 0))
        igst  = float(r.get("igst", 0))
        if rate not in buckets:
            buckets[rate] = {"gst_rate": rate, "taxable": 0.0, "cgst": 0.0, "sgst": 0.0, "igst": 0.0, "total_tax": 0.0}
        buckets[rate]["taxable"] += taxable
        buckets[rate]["cgst"]    += cgst
        buckets[rate]["sgst"]    += sgst
        buckets[rate]["igst"]    += igst
        # Auto-calculate if taxes not provided
        if cgst == 0 and sgst == 0 and igst == 0:
            half_tax = round(taxable * rate / 200, 2)
            buckets[rate]["cgst"] += half_tax
            buckets[rate]["sgst"] += half_tax
        buckets[rate]["total_tax"] = round(buckets[rate]["cgst"] + buckets[rate]["sgst"] + buckets[rate]["igst"], 2)
    for b in buckets.values():
        b["taxable"]    = round(b["taxable"], 2)
        b["cgst"]       = round(b["cgst"], 2)
        b["sgst"]       = round(b["sgst"], 2)
        b["igst"]       = round(b["igst"], 2)
    return dict(sorted(buckets.items()))


async def prepare_gstr_filing(
    sales_data:    list[dict],
    purchase_data: list[dict],
    return_type:   str = "gstr3b",
    firm_name:     str = "",
    gstin:         str = "",
    period:        str = "",
    language:      str = "en",
) -> dict:
    """
    Prepare GSTR-1 or GSTR-3B filing summary from sales/purchase line data.
    sales_data:    [{taxable_value, gst_rate, cgst, sgst, igst, supply_type, b2b/b2c, hsn}]
    purchase_data: [{taxable_value, gst_rate, cgst, sgst, igst, vendor_gstin}]
    """
    from datetime import datetime, timezone

    period = period or datetime.now(timezone.utc).strftime("%b %Y")

    # ── Sales summary ──
    sales_by_rate    = _sum_by_rate(sales_data)
    total_taxable    = round(sum(b["taxable"]   for b in sales_by_rate.values()), 2)
    total_cgst_out   = round(sum(b["cgst"]      for b in sales_by_rate.values()), 2)
    total_sgst_out   = round(sum(b["sgst"]      for b in sales_by_rate.values()), 2)
    total_igst_out   = round(sum(b["igst"]      for b in sales_by_rate.values()), 2)
    total_output_tax = round(total_cgst_out + total_sgst_out + total_igst_out, 2)

    # ── ITC (Input Tax Credit) from purchases ──
    purchase_by_rate = _sum_by_rate(purchase_data)
    itc_cgst   = round(sum(b["cgst"]  for b in purchase_by_rate.values()), 2)
    itc_sgst   = round(sum(b["sgst"]  for b in purchase_by_rate.values()), 2)
    itc_igst   = round(sum(b["igst"]  for b in purchase_by_rate.values()), 2)
    total_itc  = round(itc_cgst + itc_sgst + itc_igst, 2)

    # ── Net tax liability ──
    net_cgst    = round(max(total_cgst_out - itc_cgst, 0), 2)
    net_sgst    = round(max(total_sgst_out - itc_sgst, 0), 2)
    net_igst    = round(max(total_igst_out - itc_igst, 0), 2)
    net_payable = round(net_cgst + net_sgst + net_igst, 2)

    itc_excess_cgst = round(max(itc_cgst - total_cgst_out, 0), 2)
    itc_excess_sgst = round(max(itc_sgst - total_sgst_out, 0), 2)
    itc_excess_igst = round(max(itc_igst - total_igst_out, 0), 2)
    total_itc_carryforward = round(itc_excess_cgst + itc_excess_sgst + itc_excess_igst, 2)

    # ── Filing checklist ──
    checklist = [
        {"item": "Sales invoices reconciled with books",       "status": "pending"},
        {"item": "Purchase invoices matched with GSTR-2B",     "status": "pending"},
        {"item": "HSN summary verified (if turnover > ₹5 Cr)", "status": "pending" if total_taxable > 500_0000 else "na"},
        {"item": "Reverse Charge Mechanism (RCM) checked",     "status": "pending"},
        {"item": "ITC reversal for ineligible credits",        "status": "pending"},
        {"item": "E-invoicing compliance (if applicable)",     "status": "pending" if total_taxable > 500_0000 else "na"},
        {"item": "Late fees / interest calculated if filing past due date", "status": "pending"},
        {"item": "Bank payment challan ready",                 "status": "ready" if net_payable == 0 else "pending"},
    ]

    gstr1_summary = None
    if return_type in ("gstr1", "both"):
        b2b = [r for r in sales_data if (r.get("supply_type") == "b2b" or r.get("gstin"))]
        b2c = [r for r in sales_data if r not in b2b]
        gstr1_summary = {
            "b2b_invoices": len(b2b),
            "b2c_invoices": len(b2c),
            "b2b_taxable":  round(sum(float(r.get("taxable_value", 0)) for r in b2b), 2),
            "b2c_taxable":  round(sum(float(r.get("taxable_value", 0)) for r in b2c), 2),
            "hsn_summary":  list(sales_by_rate.values()),
        }

    return {
        "action":          "gstr_filing_prep",
        "return_type":     return_type.upper(),
        "firm_name":       firm_name,
        "gstin":           gstin,
        "period":          period,
        "sales_summary": {
            "total_invoices":   len(sales_data),
            "total_taxable":    total_taxable,
            "total_cgst":       total_cgst_out,
            "total_sgst":       total_sgst_out,
            "total_igst":       total_igst_out,
            "total_output_tax": total_output_tax,
            "by_rate":          list(sales_by_rate.values()),
        },
        "purchase_summary": {
            "total_invoices": len(purchase_data),
            "itc_cgst":       itc_cgst,
            "itc_sgst":       itc_sgst,
            "itc_igst":       itc_igst,
            "total_itc":      total_itc,
            "by_rate":        list(purchase_by_rate.values()),
        },
        "tax_liability": {
            "output_tax":          total_output_tax,
            "total_itc":           total_itc,
            "net_cgst_payable":    net_cgst,
            "net_sgst_payable":    net_sgst,
            "net_igst_payable":    net_igst,
            "total_net_payable":   net_payable,
            "itc_carryforward":    total_itc_carryforward,
            "refund_eligible":     total_itc_carryforward > 0,
        },
        "gstr1_summary":   gstr1_summary,
        "filing_checklist": checklist,
        "ready_to_file":   net_payable >= 0 and len(sales_data) > 0,
    }


# ── Tax Planning Optimizer (Round 6) ─────────────────────────────────────────

_INSTRUMENTS = [
    {"name": "ELSS Mutual Funds",         "section": "80C",           "returns": "12-15%",   "lock_in": "3 years",      "risk": "High",        "best_for": "Investors with 3+ year horizon"},
    {"name": "PPF (Public Provident Fund)","section": "80C",           "returns": "7.1%",     "lock_in": "15 years",     "risk": "None",        "best_for": "Long-term risk-free savings"},
    {"name": "NPS Tier 1",                 "section": "80C+80CCD(1B)", "returns": "8-10%",    "lock_in": "Till retire",  "risk": "Low-Medium",  "best_for": "Extra Rs.50,000 deduction"},
    {"name": "Health Insurance",           "section": "80D",           "returns": "Protection","lock_in": "Annual",       "risk": "None",        "best_for": "Everyone — medical + tax"},
    {"name": "5-Year Bank FD",             "section": "80C",           "returns": "6.5-7.5%", "lock_in": "5 years",      "risk": "None",        "best_for": "Conservative investors"},
    {"name": "Sukanya Samriddhi Yojana",   "section": "80C",           "returns": "8.2%",     "lock_in": "21 years",     "risk": "None",        "best_for": "Parents of girl child"},
]


async def optimize_tax_planning(
    income_details: dict,
    investments:    dict,
    expenses:       dict,
    taxpayer_type:  str = "individual",
    age:            int = 30,
    regime:         str = "old",
    language:       str = "en",
) -> dict:
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL

    gross = (
        float(income_details.get("gross_salary",   0) or 0) +
        float(income_details.get("other_income",   0) or 0) +
        float(income_details.get("rental_income",  0) or 0) +
        float(income_details.get("business_income",0) or 0)
    )
    std_deduction  = 75000 if income_details.get("gross_salary", 0) else 0
    cur_80c        = min(float(investments.get("c80", 0) or 0), 150000)
    cur_nps        = min(float(investments.get("nps", 0) or 0), 50000)
    cur_80d        = min(float(investments.get("health_insurance", 0) or 0), 50000 if age >= 60 else 25000)
    cur_hl_int     = min(float(investments.get("home_loan_interest", 0) or 0), 200000)
    cur_donations  = float(investments.get("donations", 0) or 0)
    cur_edu_loan   = float(expenses.get("education_loan_interest", 0) or 0)

    total_ded = std_deduction + cur_80c + cur_nps + cur_80d + cur_hl_int + cur_donations + cur_edu_loan
    gap_80c = max(150000 - float(investments.get("c80", 0) or 0), 0)
    gap_nps = max(50000  - float(investments.get("nps", 0) or 0), 0)
    gap_80d = max((50000 if age >= 60 else 25000) - float(investments.get("health_insurance", 0) or 0), 0)

    taxable_now = max(gross - total_ded, 0)
    taxable_opt = max(gross - total_ded - gap_80c - gap_nps - gap_80d, 0)

    def _tax(income: float) -> float:
        exemption = 300000 if age >= 60 else 250000
        if income <= exemption:
            return 0.0
        tax, remaining = 0.0, income - exemption
        for slab, rate in [(300000, .05), (300000, .10), (300000, .15), (300000, .20), (300000, .25), (float("inf"), .30)]:
            if remaining <= 0:
                break
            chunk = min(remaining, slab)
            tax += chunk * rate
            remaining -= chunk
        return round(tax * 1.04, 0)

    tax_now  = _tax(taxable_now)
    tax_opt  = _tax(taxable_opt)
    saving   = round(tax_now - tax_opt, 0)

    recs = []
    if gap_80c > 0:
        recs.append({"section": "80C", "priority": "High",
            "action": f"Invest Rs.{gap_80c:,.0f} more to max out 80C (Rs.1.5L limit)",
            "saving": round(gap_80c * 0.30, 0),
            "instruments": ["ELSS — best returns + 3yr lock-in", "PPF — safe + 15yr", "NPS Tier 1"]})
    if gap_nps > 0:
        recs.append({"section": "80CCD(1B)", "priority": "High",
            "action": f"Invest Rs.{gap_nps:,.0f} in NPS for extra deduction beyond 80C",
            "saving": round(gap_nps * 0.30, 0),
            "instruments": ["NPS Tier 1 via PFRDA-registered fund manager"]})
    if gap_80d > 0:
        recs.append({"section": "80D", "priority": "High" if gap_80d > 10000 else "Medium",
            "action": f"Get health insurance to claim Rs.{gap_80d:,.0f} more under 80D",
            "saving": round(gap_80d * 0.30, 0),
            "instruments": ["Family floater plan", "Add parents policy for extra Rs.25K-50K"]})
    if not investments.get("home_loan_interest"):
        recs.append({"section": "24(b)+80C", "priority": "Medium",
            "action": "Home loan interest (up to Rs.2L) + principal (80C) both deductible",
            "saving": "Up to Rs.75,000/yr", "instruments": ["Home loan from bank/HFC"]})

    try:
        narrative = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": f"Senior CA giving tax advice. Language: {language}. Be specific and encouraging."},
                {"role": "user",   "content": f"Income Rs.{gross:,.0f}, age {age}, {regime.upper()} regime. Current tax Rs.{tax_now:,.0f}, after optimization Rs.{tax_opt:,.0f}, saving Rs.{saving:,.0f}. Write 3 sentences of personalized advice."},
            ],
            model=OLLAMA_MODEL, max_tokens=250,
        )
    except Exception:
        narrative = f"With a gross income of Rs.{gross:,.0f}, you can save approximately Rs.{saving:,.0f} in taxes this year by fully using available deductions. Start with ELSS for 80C (3-year lock-in, market returns), then add NPS for the extra Rs.50,000 deduction under 80CCD(1B). A health insurance policy will also save tax under 80D while protecting your family."

    return {
        "action":             "tax_planning",
        "taxpayer_type":      taxpayer_type,
        "age":                age,
        "regime":             regime,
        "gross_income":       gross,
        "current_deductions": round(total_ded, 0),
        "taxable_current":    round(taxable_now, 0),
        "taxable_optimized":  round(taxable_opt, 0),
        "tax_current":        tax_now,
        "tax_optimized":      tax_opt,
        "potential_saving":   saving,
        "effective_rate":     round(tax_now / gross * 100, 1) if gross else 0,
        "optimized_rate":     round(tax_opt / gross * 100, 1) if gross else 0,
        "deduction_gaps":     {"80C": round(gap_80c, 0), "NPS": round(gap_nps, 0), "80D": round(gap_80d, 0)},
        "recommendations":    recs,
        "instruments":        _INSTRUMENTS,
        "narrative":          narrative,
    }


# ── Payroll & Salary Processor (Round 7) ──────────────────────────────────────

_PT_SLABS = {
    "karnataka": [(14999, 0), (99999, 200), (float("inf"), 200)],
    "maharashtra": [(7500, 0), (10000, 175), (float("inf"), 200)],
    "tamil_nadu": [(float("inf"), 0)],
    "default": [(float("inf"), 200)],
}


def _calc_pt(gross: float, state: str = "default") -> float:
    slabs = _PT_SLABS.get(state.lower().replace(" ", "_"), _PT_SLABS["default"])
    for limit, amt in slabs:
        if gross <= limit:
            return float(amt)
    return 200.0


def _calc_tds_salary(taxable_annual: float, age: int = 30) -> float:
    exemption = 300000 if age >= 60 else 250000
    if taxable_annual <= exemption:
        return 0.0
    remaining = taxable_annual - exemption
    tax = 0.0
    for slab, rate in [(300000, .05), (300000, .10), (300000, .15), (300000, .20), (300000, .25), (float("inf"), .30)]:
        if remaining <= 0:
            break
        chunk = min(remaining, slab)
        tax += chunk * rate
        remaining -= chunk
    return round(tax * 1.04 / 12, 0)


def calculate_payroll(
    employees: list,
    company_name: str = "",
    month: str = "",
    language: str = "en",
) -> dict:
    if not employees:
        employees = [
            {"name": "Arjun Kumar", "emp_id": "E001", "designation": "Software Engineer", "gross_salary": 85000, "pf_applicable": True, "esi_applicable": False, "age": 28, "state": "karnataka", "lop_days": 0},
            {"name": "Priya Sharma", "emp_id": "E002", "designation": "Marketing Manager",  "gross_salary": 55000, "pf_applicable": True, "esi_applicable": True,  "age": 32, "state": "karnataka", "lop_days": 1},
            {"name": "Ravi Patel",   "emp_id": "E003", "designation": "Support Executive",   "gross_salary": 22000, "pf_applicable": True, "esi_applicable": True,  "age": 25, "state": "maharashtra","lop_days": 0},
        ]

    payslips = []
    total_gross = total_net = total_pf_emp = total_pf_er = total_esi_emp = total_esi_er = total_tds = total_pt = 0.0

    for e in employees:
        gross     = float(e.get("gross_salary", 0) or 0)
        lop_days  = int(e.get("lop_days", 0) or 0)
        age       = int(e.get("age", 30) or 30)
        state     = e.get("state", "default")
        pf_ok     = bool(e.get("pf_applicable", True))
        esi_ok    = bool(e.get("esi_applicable", False)) and gross <= 21000

        # LOP deduction (assume 26 working days)
        lop_ded   = round(gross / 26 * lop_days, 0)
        gross_act = gross - lop_ded

        # PF: 12% employee + 12% employer on basic (assume basic = 50% of gross, capped at 15,000)
        basic     = min(gross_act * 0.5, 15000) if pf_ok else 0
        pf_emp    = round(basic * 0.12, 0) if pf_ok else 0
        pf_er     = round(basic * 0.12, 0) if pf_ok else 0

        # ESI: 0.75% employee + 3.25% employer
        esi_emp   = round(gross_act * 0.0075, 0) if esi_ok else 0
        esi_er    = round(gross_act * 0.0325, 0) if esi_ok else 0

        # Professional Tax
        pt        = _calc_pt(gross_act, state)

        # TDS on salary (simplified: annualise, apply slab, /12)
        tds_annual_gross = gross_act * 12
        std_ded   = min(75000, tds_annual_gross)
        tds       = _calc_tds_salary(max(tds_annual_gross - std_ded - pf_emp * 12, 0), age)

        deductions = pf_emp + esi_emp + pt + tds + lop_ded
        net        = round(gross_act - pf_emp - esi_emp - pt - tds, 0)

        total_gross  += gross_act; total_net    += net
        total_pf_emp += pf_emp;   total_pf_er  += pf_er
        total_esi_emp+= esi_emp;  total_esi_er += esi_er
        total_tds    += tds;      total_pt     += pt

        payslips.append({
            "name":         e.get("name", ""),
            "emp_id":       e.get("emp_id", ""),
            "designation":  e.get("designation", ""),
            "gross_salary": gross,
            "lop_days":     lop_days,
            "lop_deduction":lop_ded,
            "gross_actual": gross_act,
            "basic":        basic,
            "pf_employee":  pf_emp,
            "pf_employer":  pf_er,
            "esi_employee": esi_emp,
            "esi_employer": esi_er,
            "professional_tax": pt,
            "tds":          tds,
            "total_deductions": round(deductions, 0),
            "net_salary":   net,
            "ctc_monthly":  round(gross + pf_er + esi_er, 0),
        })

    employer_liability = round(total_gross + total_pf_er + total_esi_er, 0)

    return {
        "action":            "payroll",
        "company_name":      company_name,
        "month":             month,
        "employee_count":    len(payslips),
        "payslips":          payslips,
        "summary": {
            "total_gross":      round(total_gross, 0),
            "total_net":        round(total_net, 0),
            "total_pf_employee":round(total_pf_emp, 0),
            "total_pf_employer":round(total_pf_er, 0),
            "total_esi_employee":round(total_esi_emp, 0),
            "total_esi_employer":round(total_esi_er, 0),
            "total_tds":        round(total_tds, 0),
            "total_pt":         round(total_pt, 0),
            "total_deductions": round(total_gross - total_net, 0),
            "employer_liability": employer_liability,
        },
        "compliance_reminders": [
            "PF challan due: 15th of next month via EPFO unified portal",
            "ESI challan due: 15th of next month via ESIC portal",
            "TDS (Form 24Q) due: quarterly — 31st July, 31st Oct, 31st Jan, 15th May",
            "PT due: as per state schedule (monthly/annual)",
        ],
    }


# ── Business Valuation Calculator (Round 9) ───────────────────────────────────

_INDUSTRY_MULTIPLES: dict[str, dict] = {
    "technology":     {"revenue": (4, 8),  "ebitda": (15, 25), "pe": (25, 45)},
    "saas":           {"revenue": (6, 12), "ebitda": (20, 35), "pe": (30, 60)},
    "ecommerce":      {"revenue": (1, 3),  "ebitda": (8, 14),  "pe": (15, 25)},
    "manufacturing":  {"revenue": (0.5,1.5),"ebitda":(5, 10),  "pe": (10, 18)},
    "retail":         {"revenue": (0.5,1.5),"ebitda":(5, 8),   "pe": (10, 15)},
    "healthcare":     {"revenue": (2, 4),  "ebitda": (10, 18), "pe": (18, 28)},
    "fintech":        {"revenue": (5, 10), "ebitda": (18, 30), "pe": (28, 50)},
    "education":      {"revenue": (2, 5),  "ebitda": (8, 15),  "pe": (15, 25)},
    "real_estate":    {"revenue": (2, 4),  "ebitda": (10, 16), "pe": (12, 20)},
    "consulting":     {"revenue": (1, 2),  "ebitda": (5, 10),  "pe": (10, 15)},
    "default":        {"revenue": (2, 4),  "ebitda": (8, 14),  "pe": (15, 22)},
}

_STAGE_DISCOUNT = {"pre_revenue": 0.4, "early": 0.6, "growth": 0.8, "mature": 1.0, "late": 1.0}


def calculate_business_valuation(
    revenue: float,
    ebitda: float,
    net_profit: float,
    industry: str = "technology",
    stage: str = "growth",
    growth_rate: float = 20.0,
    assets: float = 0.0,
    liabilities: float = 0.0,
    language: str = "en",
) -> dict:
    ind_key = industry.lower().replace(" ", "_").replace("-", "_")
    mult = _INDUSTRY_MULTIPLES.get(ind_key, _INDUSTRY_MULTIPLES["default"])
    disc = _STAGE_DISCOUNT.get(stage, 0.8)
    growth_premium = 1 + max(0, (growth_rate - 15) / 100)

    def _range(low_m: float, high_m: float, base: float) -> tuple[float, float]:
        return (round(base * low_m * disc * growth_premium, 0),
                round(base * high_m * disc * growth_premium, 0))

    valuations: dict[str, dict] = {}

    if revenue > 0:
        lo, hi = _range(*mult["revenue"], revenue)
        valuations["revenue_multiple"] = {
            "method": "Revenue Multiple",
            "low": lo, "high": hi, "midpoint": round((lo + hi) / 2, 0),
            "multiple_used": f"{mult['revenue'][0]}x – {mult['revenue'][1]}x revenue",
            "note": "Common for high-growth startups with strong top-line",
        }

    if ebitda > 0:
        lo, hi = _range(*mult["ebitda"], ebitda)
        valuations["ebitda_multiple"] = {
            "method": "EBITDA Multiple",
            "low": lo, "high": hi, "midpoint": round((lo + hi) / 2, 0),
            "multiple_used": f"{mult['ebitda'][0]}x – {mult['ebitda'][1]}x EBITDA",
            "note": "Standard for profitable businesses seeking PE/strategic acquisition",
        }

    if net_profit > 0:
        lo, hi = _range(*mult["pe"], net_profit)
        valuations["pe_multiple"] = {
            "method": "P/E Multiple",
            "low": lo, "high": hi, "midpoint": round((lo + hi) / 2, 0),
            "multiple_used": f"{mult['pe'][0]}x – {mult['pe'][1]}x PAT",
            "note": "Used by public market investors and listed company comparables",
        }

    net_assets = assets - liabilities
    if net_assets > 0:
        valuations["asset_based"] = {
            "method": "Net Asset Value",
            "low": round(net_assets * 0.8, 0), "high": round(net_assets * 1.2, 0),
            "midpoint": round(net_assets, 0),
            "multiple_used": "Book value ± 20%",
            "note": "Floor valuation — asset-heavy or distressed businesses",
        }

    midpoints = [v["midpoint"] for v in valuations.values() if v["midpoint"] > 0]
    blended = round(sum(midpoints) / len(midpoints), 0) if midpoints else 0
    overall_low  = round(min(v["low"]  for v in valuations.values()), 0) if valuations else 0
    overall_high = round(max(v["high"] for v in valuations.values()), 0) if valuations else 0

    ebitda_margin = round(ebitda / revenue * 100, 1) if revenue else 0
    pat_margin    = round(net_profit / revenue * 100, 1) if revenue else 0

    def _cr(n: float) -> str:
        if n >= 10_000_000:
            return f"₹{n/10_000_000:.1f} Cr"
        elif n >= 100_000:
            return f"₹{n/100_000:.1f} L"
        return f"₹{n:,.0f}"

    return {
        "action":          "business_valuation",
        "industry":        industry,
        "stage":           stage,
        "growth_rate":     growth_rate,
        "inputs": {
            "revenue": revenue, "ebitda": ebitda,
            "net_profit": net_profit, "assets": assets, "liabilities": liabilities,
        },
        "financials": {
            "ebitda_margin": ebitda_margin,
            "pat_margin":    pat_margin,
            "net_assets":    net_assets,
        },
        "valuations":        valuations,
        "blended_valuation": blended,
        "range": {"low": overall_low, "high": overall_high},
        "formatted": {
            "blended": _cr(blended),
            "low":     _cr(overall_low),
            "high":    _cr(overall_high),
        },
        "stage_discount":    disc,
        "growth_premium":    round(growth_premium, 2),
        "recommendations": [
            f"Blended valuation: {_cr(blended)} (range: {_cr(overall_low)} – {_cr(overall_high)})",
            f"For fundraising, use revenue multiple ({_cr(valuations.get('revenue_multiple',{}).get('midpoint',0))}) if pre-profit.",
            f"EBITDA margin of {ebitda_margin}% — {'healthy' if ebitda_margin >= 20 else 'improve margins before fundraising'} for {industry}.",
            "Consider getting a formal valuation report from a SEBI-registered Category I Merchant Banker for DPIIT/funding purposes.",
        ] if valuations else ["Enter financial figures to see valuation"],
    }


# ── GST Notice Reply Drafter (Round 8) ────────────────────────────────────────

_NOTICE_TEMPLATES = {
    "gst_scrutiny": {
        "section": "Section 61 of CGST Act, 2017",
        "subject": "Reply to Notice for Scrutiny of Returns",
        "opening": "We are in receipt of your notice dated {date} regarding scrutiny of our GST returns for the period {period}. We wish to submit our reply as follows:",
        "legal_ref": ["Section 61 CGST Act 2017", "Rule 99 CGST Rules 2017"],
    },
    "gst_demand": {
        "section": "Section 73/74 of CGST Act, 2017",
        "subject": "Reply to Show Cause Notice / Demand Notice",
        "opening": "We have received the Show Cause Notice / Demand Notice and wish to submit our detailed reply on the allegations / demands raised therein:",
        "legal_ref": ["Section 73 CGST Act 2017", "Section 74 CGST Act 2017", "Rule 142 CGST Rules 2017"],
    },
    "itc_mismatch": {
        "section": "Section 16 of CGST Act, 2017",
        "subject": "Reply to Notice for ITC Mismatch (GSTR-2A/2B vs GSTR-3B)",
        "opening": "This is in reference to your notice regarding Input Tax Credit mismatch between GSTR-2B and our GSTR-3B filings. We submit the following clarification:",
        "legal_ref": ["Section 16 CGST Act 2017", "Rule 36 CGST Rules 2017", "Circular 183/15/2022-GST"],
    },
    "ewaybill": {
        "section": "Rule 138 of CGST Rules, 2017",
        "subject": "Reply to Notice for E-Way Bill Non-Compliance",
        "opening": "We acknowledge receipt of the notice pertaining to E-Way Bill related observations and submit the following explanation:",
        "legal_ref": ["Rule 138 CGST Rules 2017", "Section 129 CGST Act 2017"],
    },
    "annual_return": {
        "section": "Section 44 of CGST Act, 2017",
        "subject": "Reply to Notice Regarding GSTR-9 Annual Return",
        "opening": "We have received your notice regarding discrepancies observed in our Annual Return GSTR-9. We wish to provide the following clarification:",
        "legal_ref": ["Section 44 CGST Act 2017", "Rule 80 CGST Rules 2017"],
    },
    "tds_demand": {
        "section": "Section 200A of Income Tax Act, 1961",
        "subject": "Reply to TDS Demand Notice u/s 200A",
        "opening": "We have received the demand notice under Section 200A and wish to submit our reply with supporting details:",
        "legal_ref": ["Section 200A Income Tax Act 1961", "Section 154 Income Tax Act 1961"],
    },
}


async def draft_gst_notice_reply(
    notice_type: str,
    notice_ref: str = "",
    gstin: str = "",
    taxpayer_name: str = "",
    notice_details: str = "",
    reply_points: str = "",
    language: str = "en",
) -> dict:
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL

    template = _NOTICE_TEMPLATES.get(notice_type, _NOTICE_TEMPLATES["gst_scrutiny"])
    today = date.today().strftime("%d/%m/%Y")

    header = f"""To,
The Proper Officer,
GST Department

Subject: {template['subject']}
Reference Notice No.: {notice_ref or '[NOTICE REF]'}
GSTIN: {gstin or '[GSTIN]'}
Date: {today}

Sir/Madam,

{template['opening'].format(date='[Notice Date]', period='[Period]')}

"""

    legal_paras = "\n".join(f"  {i+1}. As per {ref}, we submit that our compliance is in order with respect to the said provision." for i, ref in enumerate(template["legal_ref"]))

    footer = f"""
We hereby confirm that all statutory compliances have been duly met and the above facts are true and correct to the best of our knowledge.

We request you to kindly consider the above submissions and drop the proceedings / observations raised in the notice.

Thanking You,

Yours faithfully,
{taxpayer_name or '[TAXPAYER NAME]'}
GSTIN: {gstin or '[GSTIN]'}
Date: {today}

Enclosures:
1. Relevant GST Returns / Challan copies
2. Books of account / Ledgers
3. Supporting invoices as applicable
"""

    try:
        ai_body = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": f"You are a senior CA and GST consultant. Draft a professional, legally sound GST notice reply. Language: {language}. Use formal tone. Reference: {', '.join(template['legal_ref'])}"},
                {"role": "user",   "content": f"Notice type: {notice_type}. Notice details: {notice_details or 'Standard scrutiny notice'}. Taxpayer reply points: {reply_points or 'Returns filed correctly, all ITC eligible, no suppression of facts'}. Draft 3-4 paragraphs of substantive reply with legal references."},
            ],
            model=OLLAMA_MODEL, max_tokens=600,
        )
    except Exception:
        ai_body = f"""We wish to state that our GST returns for the relevant period have been filed correctly and in accordance with the provisions of the CGST Act, 2017 and rules thereunder.

{legal_paras}

The Input Tax Credit availed by us is in accordance with Section 16 of the CGST Act, 2017, and all the conditions stipulated therein have been duly complied with. The vendors from whom ITC has been availed are duly registered taxpayers and have filed their returns.

We submit that there is no suppression of facts, fraud, or wilful misstatement on our part. The difference, if any, is purely on account of timing differences which have since been rectified.

We therefore request that the above reply be accepted and the notice proceedings be dropped forthwith."""

    full_letter = header + ai_body + footer

    return {
        "action":         "gst_notice_reply",
        "notice_type":    notice_type,
        "taxpayer_name":  taxpayer_name,
        "gstin":          gstin,
        "notice_ref":     notice_ref,
        "section":        template["section"],
        "subject":        template["subject"],
        "legal_references": template["legal_ref"],
        "full_letter":    full_letter,
        "word_count":     len(full_letter.split()),
        "tips": [
            "Attach all supporting documents mentioned in the enclosure list.",
            "Submit reply within the time limit specified in the notice (usually 15-30 days).",
            "Keep a copy of the reply with proof of submission (acknowledgement).",
            "If demand is upheld, you can file an appeal under Section 107 within 3 months.",
        ],
    }


# ── Cash Flow Forecaster (Round 10) ──────────────────────────────────────────

_INDUSTRY_SEASONALITY = {
    "retail":       [0.8, 0.7, 0.9, 1.0, 1.1, 1.0, 0.9, 0.9, 1.0, 1.1, 1.3, 1.5],
    "ecommerce":    [0.7, 0.8, 0.9, 1.0, 1.1, 1.0, 1.1, 1.0, 1.0, 1.1, 1.3, 1.6],
    "education":    [0.9, 0.8, 0.9, 1.0, 1.3, 1.4, 0.7, 1.5, 1.2, 1.0, 0.9, 0.8],
    "agriculture":  [0.6, 0.7, 0.9, 1.2, 1.3, 0.8, 0.7, 0.8, 1.2, 1.3, 1.1, 0.9],
    "hospitality":  [0.9, 0.9, 1.1, 1.2, 0.9, 0.8, 1.1, 1.0, 0.9, 1.0, 1.1, 1.3],
    "technology":   [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.9, 0.9, 1.1, 1.1, 1.0, 0.9],
    "manufacturing":[0.9, 0.9, 1.0, 1.1, 1.1, 1.0, 0.9, 1.0, 1.1, 1.1, 1.0, 0.9],
    "general":      [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
}

_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def calculate_cash_flow_forecast(
    company_name: str,
    monthly_revenue: float,
    revenue_growth: float,
    fixed_expenses: float,
    variable_expense_pct: float,
    opening_cash: float,
    one_time_inflows: list,
    one_time_outflows: list,
    industry: str,
) -> dict:
    industry_key = industry.lower() if industry.lower() in _INDUSTRY_SEASONALITY else "general"
    seasonality = _INDUSTRY_SEASONALITY[industry_key]
    var_pct = variable_expense_pct / 100.0
    growth_factor = 1 + (revenue_growth / 100.0)

    months_data = []
    running_cash = opening_cash
    cumulative_inflow = 0.0
    cumulative_outflow = 0.0
    lowest_cash = opening_cash
    lowest_month = "Start"
    highest_cash = opening_cash
    highest_month = "Start"

    one_time_in_map = {}
    for oi in one_time_inflows:
        m = int(oi.get("month", 1)) - 1
        one_time_in_map[m] = one_time_in_map.get(m, 0) + float(oi.get("amount", 0))

    one_time_out_map = {}
    for oo in one_time_outflows:
        m = int(oo.get("month", 1)) - 1
        one_time_out_map[m] = one_time_out_map.get(m, 0) + float(oo.get("amount", 0))

    for i in range(12):
        base_rev = monthly_revenue * (growth_factor ** i)
        season_rev = base_rev * seasonality[i]
        extra_in = one_time_in_map.get(i, 0.0)
        total_inflow = season_rev + extra_in

        variable_exp = season_rev * var_pct
        total_outflow = fixed_expenses + variable_exp + one_time_out_map.get(i, 0.0)

        net_cash = total_inflow - total_outflow
        running_cash += net_cash
        cumulative_inflow += total_inflow
        cumulative_outflow += total_outflow

        if running_cash < lowest_cash:
            lowest_cash = running_cash
            lowest_month = _MONTHS[i]
        if running_cash > highest_cash:
            highest_cash = running_cash
            highest_month = _MONTHS[i]

        months_data.append({
            "month": _MONTHS[i],
            "month_num": i + 1,
            "revenue": round(season_rev, 0),
            "extra_inflow": round(extra_in, 0),
            "total_inflow": round(total_inflow, 0),
            "fixed_expenses": round(fixed_expenses, 0),
            "variable_expenses": round(variable_exp, 0),
            "extra_outflow": round(one_time_out_map.get(i, 0.0), 0),
            "total_outflow": round(total_outflow, 0),
            "net_cashflow": round(net_cash, 0),
            "closing_cash": round(running_cash, 0),
            "status": "surplus" if net_cash >= 0 else "deficit",
        })

    avg_monthly_burn = cumulative_outflow / 12
    runway_months = round(running_cash / avg_monthly_burn, 1) if avg_monthly_burn > 0 else 99
    annual_profit = cumulative_inflow - cumulative_outflow

    deficit_months = [m for m in months_data if m["status"] == "deficit"]

    recommendations = []
    if deficit_months:
        recommendations.append(f"Cash deficit in {len(deficit_months)} month(s) — arrange overdraft facility or accelerate receivables before {deficit_months[0]['month']}.")
    if runway_months < 6:
        recommendations.append(f"Runway is only {runway_months} months — prioritize fundraising or cost reduction immediately.")
    if revenue_growth < 5:
        recommendations.append("Revenue growth below 5% — explore upsell/cross-sell or new revenue streams to improve trajectory.")
    if variable_expense_pct > 50:
        recommendations.append(f"Variable costs at {variable_expense_pct}% of revenue — negotiate supplier contracts or automate to reduce below 40%.")
    if not recommendations:
        recommendations.append("Cash flow is healthy. Consider investing surplus in growth or building a 3-month emergency reserve.")

    return {
        "action":           "cash_flow_forecast",
        "company_name":     company_name or "Your Company",
        "industry":         industry,
        "forecast_period":  "12 months",
        "opening_cash":     round(opening_cash, 0),
        "closing_cash":     round(running_cash, 0),
        "annual_revenue":   round(cumulative_inflow, 0),
        "annual_expenses":  round(cumulative_outflow, 0),
        "annual_profit":    round(annual_profit, 0),
        "avg_monthly_burn": round(avg_monthly_burn, 0),
        "runway_months":    runway_months,
        "lowest_cash":      round(lowest_cash, 0),
        "lowest_month":     lowest_month,
        "highest_cash":     round(highest_cash, 0),
        "highest_month":    highest_month,
        "deficit_months":   len(deficit_months),
        "months":           months_data,
        "recommendations":  recommendations,
        "summary":          f"{company_name or 'Company'} 12-month forecast: ₹{annual_profit/100000:.1f}L net profit, {runway_months}m runway, {'⚠️ cash deficit risk' if deficit_months else '✅ healthy cash flow'}.",
    }


# ── P&L Statement Builder (Round 12) ─────────────────────────────────────────

_INDUSTRY_BENCHMARKS = {
    "technology":    {"gross_margin": 70, "ebitda_margin": 20, "net_margin": 15},
    "ecommerce":     {"gross_margin": 35, "ebitda_margin": 8,  "net_margin": 5},
    "manufacturing": {"gross_margin": 30, "ebitda_margin": 12, "net_margin": 8},
    "retail":        {"gross_margin": 28, "ebitda_margin": 6,  "net_margin": 4},
    "services":      {"gross_margin": 65, "ebitda_margin": 18, "net_margin": 12},
    "healthcare":    {"gross_margin": 50, "ebitda_margin": 15, "net_margin": 10},
    "food_beverage": {"gross_margin": 40, "ebitda_margin": 10, "net_margin": 6},
    "general":       {"gross_margin": 45, "ebitda_margin": 12, "net_margin": 8},
}


# ── MSME Loan Eligibility Calculator (Round 13) ──────────────────────────────

_MSME_CATEGORIES = {
    "manufacturing": {
        "micro":  {"turnover": 5_00_00_000,   "investment": 1_00_00_000},
        "small":  {"turnover": 50_00_00_000,  "investment": 10_00_00_000},
        "medium": {"turnover": 250_00_00_000, "investment": 50_00_00_000},
    },
    "service": {
        "micro":  {"turnover": 5_00_00_000,   "investment": 50_00_000},
        "small":  {"turnover": 50_00_00_000,  "investment": 5_00_00_000},
        "medium": {"turnover": 250_00_00_000, "investment": 10_00_00_000},
    },
}

_LOAN_SCHEMES = {
    "working_capital": {
        "schemes": ["CC/OD from banks under CGTMSE", "MUDRA Loan (Tarun/Shishu/Kishor)", "SIDBI Direct Lending"],
        "max_without_collateral": 2_00_00_000,
        "interest_range": "8.5% – 12% p.a.",
        "tenure": "12 months (renewable)",
        "processing_fee": "0.5% – 1%",
    },
    "term_loan": {
        "schemes": ["SIDBI Term Loan", "PSB 59-minute loan", "Stand-Up India Scheme"],
        "max_without_collateral": 2_00_00_000,
        "interest_range": "9% – 14% p.a.",
        "tenure": "3 – 7 years",
        "processing_fee": "1% – 2%",
    },
    "machinery": {
        "schemes": ["SIDBI Equipment Finance", "TReDS platform", "CGTMSE covered term loan"],
        "max_without_collateral": 1_00_00_000,
        "interest_range": "9% – 13% p.a.",
        "tenure": "5 – 10 years",
        "processing_fee": "1%",
    },
    "export": {
        "schemes": ["ECGC Export Credit", "SIDBI Export Finance", "Bank Pre-shipment Credit"],
        "max_without_collateral": 5_00_00_000,
        "interest_range": "7% – 10% p.a. (subsidised)",
        "tenure": "180 days per cycle",
        "processing_fee": "0.5%",
    },
    "trade_receivables": {
        "schemes": ["TReDS (Invoice Discounting)", "Factoring via RXIL/M1xchange/INVOICEMART"],
        "max_without_collateral": 10_00_00_000,
        "interest_range": "7% – 11% p.a.",
        "tenure": "30 – 90 days",
        "processing_fee": "0.3% – 0.5% per invoice",
    },
}

_GOVERNMENT_SUBSIDIES = [
    {
        "name":        "CGTMSE (Credit Guarantee)",
        "benefit":     "Collateral-free loans up to ₹2 Cr. Bank gets 75-85% guarantee from govt.",
        "eligibility": "All MSMEs. No collateral or third-party guarantee needed.",
        "apply_via":   "Through your bank — just ask for 'CGTMSE covered loan'",
    },
    {
        "name":        "MUDRA Yojana",
        "benefit":     "₹10L (Shishu), ₹10L-50L (Kishor), ₹50L-10L (Tarun) at subsidised rates",
        "eligibility": "Non-corporate, non-farm businesses. No minimum turnover.",
        "apply_via":   "Any bank, NBFC, or MFI. Apply at mudramitra.in",
    },
    {
        "name":        "Stand-Up India",
        "benefit":     "₹10L – ₹1Cr greenfield enterprise loans for SC/ST and Women entrepreneurs",
        "eligibility": "SC/ST or Women promoters. First-time entrepreneurs. Min 51% stake.",
        "apply_via":   "standupmitra.in or any scheduled commercial bank",
    },
    {
        "name":        "PSB 59-Minute Loan",
        "benefit":     "In-principle approval in 59 minutes for ₹1L – ₹5Cr",
        "eligibility": "GST-registered MSMEs with 6+ months IT returns. CIBIL 700+",
        "apply_via":   "psbloansin59minutes.com",
    },
    {
        "name":        "SIDBI Make in India Loans for Enterprises (SMILE)",
        "benefit":     "Soft loans at 8-9% for manufacturing MSMEs. Moratorium up to 36 months.",
        "eligibility": "Manufacturing units with 3+ years operations and positive net worth.",
        "apply_via":   "sidbi.in or SIDBI branch offices",
    },
]


# ── Client Proposal Generator (Round 15) ─────────────────────────────────────

_CA_SERVICES = {
    "bookkeeping":       {"label": "Bookkeeping & Accounts Maintenance",    "deliverables": ["Monthly ledger reconciliation","Bank reconciliation statement","Accounts payable/receivable ledger","Monthly trial balance"], "typical_fee": (3000, 8000), "unit": "per month"},
    "gst_filing":        {"label": "GST Compliance & Filing",               "deliverables": ["GSTR-1 filing (monthly/quarterly)","GSTR-3B filing","GST reconciliation","ITC matching","Annual GSTR-9"], "typical_fee": (2000, 6000), "unit": "per month"},
    "tds_compliance":    {"label": "TDS Compliance",                        "deliverables": ["Monthly TDS deduction working","Challan payment","Quarterly 26Q/27Q/24Q filing","Form 16/16A issuance"], "typical_fee": (2000, 5000), "unit": "per month"},
    "income_tax":        {"label": "Income Tax Return Filing",              "deliverables": ["ITR preparation and filing","Advance tax computation","Tax planning advisory","Tax audit (if applicable) — 3CA/3CB/3CD"], "typical_fee": (5000, 25000), "unit": "per year"},
    "audit":             {"label": "Statutory Audit",                       "deliverables": ["Audit planning and execution","Management representation letter","Audit report (Form 3CA/3CB)","CARO 2020 reporting","UDIN generation"], "typical_fee": (15000, 75000), "unit": "per year"},
    "roc_compliance":    {"label": "ROC & Company Law Compliance",          "deliverables": ["Annual Return filing (MGT-7)","Financial Statements filing (AOC-4)","Board meeting minutes","Director KYC (DIR-3)","Charge registration/satisfaction"], "typical_fee": (5000, 15000), "unit": "per year"},
    "payroll":           {"label": "Payroll Processing",                    "deliverables": ["Monthly salary computation","PF/ESI compliance","Professional tax filing","Form 16 generation","Payroll MIS reports"], "typical_fee": (2000, 8000), "unit": "per month"},
    "msme_advisory":     {"label": "MSME & Startup Advisory",              "deliverables": ["MSME/Udyam registration","Startup India recognition","Business plan preparation","CMA data preparation","Loan documentation support"], "typical_fee": (10000, 30000), "unit": "one-time"},
    "virtual_cfo":       {"label": "Virtual CFO Services",                  "deliverables": ["Monthly MIS reports","Cash flow forecasting","Budget vs actual analysis","Investor-ready financials","Board reporting"], "typical_fee": (15000, 50000), "unit": "per month"},
    "gst_notice":        {"label": "GST Notice & Litigation",               "deliverables": ["Notice analysis and reply drafting","SCN (Show Cause Notice) response","Assessment representation","Appeal filing if required"], "typical_fee": (5000, 25000), "unit": "per matter"},
}

_ENGAGEMENT_LETTER_TEMPLATE = """ENGAGEMENT LETTER

Date: {date}
From: {firm_name}
To: {client_name}

Dear {client_contact},

Re: Engagement for Professional Services

We are pleased to confirm our engagement to provide the following professional services to {client_name} ("the Client") commencing {start_date}.

SCOPE OF SERVICES:
{scope_text}

PROFESSIONAL FEES:
{fee_text}

TERMS & CONDITIONS:
1. The Client shall provide all necessary documents and information in a timely manner.
2. Any delay in providing information may result in delays in deliverables and may attract additional charges.
3. Fees are payable within 15 days of invoice date. Late payment attracts interest at 18% p.a.
4. This engagement may be terminated by either party with 30 days' written notice.
5. All work product remains property of {firm_name} until fees are paid in full.
6. Professional fees are exclusive of applicable GST (currently 18%).
7. Out-of-pocket expenses (courier, filing fees, travel) will be charged at actuals.

CONFIDENTIALITY:
Both parties agree to maintain strict confidentiality of information shared during this engagement.

GOVERNING LAW:
This engagement shall be governed by the laws of India.

Please sign and return a copy of this letter to confirm your acceptance.

Yours faithfully,
{ca_name}
Proprietor / Partner
{firm_name}

Accepted on behalf of {client_name}:
Signature: _______________
Name: _______________
Designation: _______________
Date: _______________
"""

_PROPOSAL_SECTIONS = [
    "executive_summary",
    "about_firm",
    "scope_of_work",
    "our_approach",
    "fee_schedule",
    "timeline",
    "team",
    "why_us",
    "next_steps",
]


_INDIAN_STATES = {
    "andhra_pradesh": "Andhra Pradesh", "arunachal_pradesh": "Arunachal Pradesh",
    "assam": "Assam", "bihar": "Bihar", "chhattisgarh": "Chhattisgarh",
    "goa": "Goa", "gujarat": "Gujarat", "haryana": "Haryana",
    "himachal_pradesh": "Himachal Pradesh", "jharkhand": "Jharkhand",
    "karnataka": "Karnataka", "kerala": "Kerala", "madhya_pradesh": "Madhya Pradesh",
    "maharashtra": "Maharashtra", "manipur": "Manipur", "meghalaya": "Meghalaya",
    "mizoram": "Mizoram", "nagaland": "Nagaland", "odisha": "Odisha",
    "punjab": "Punjab", "rajasthan": "Rajasthan", "sikkim": "Sikkim",
    "tamil_nadu": "Tamil Nadu", "telangana": "Telangana", "tripura": "Tripura",
    "uttar_pradesh": "Uttar Pradesh", "uttarakhand": "Uttarakhand",
    "west_bengal": "West Bengal", "delhi": "Delhi (NCT)",
    "jammu_kashmir": "Jammu & Kashmir", "ladakh": "Ladakh",
    "chandigarh": "Chandigarh", "puducherry": "Puducherry",
}

_GST_INVOICE_NOTES = [
    "This is a computer-generated invoice.",
    "Subject to jurisdiction of courts in seller's city.",
    "Payment within due date helps avoid interest under GST.",
    "E-way bill required for goods movement > ₹50,000.",
    "Goods once sold will not be taken back.",
]

_PAYMENT_TERMS_MAP = {
    "immediate":  "Payment due immediately upon receipt",
    "7_days":     "Net 7 — Payment due within 7 days of invoice date",
    "15_days":    "Net 15 — Payment due within 15 days of invoice date",
    "30_days":    "Net 30 — Payment due within 30 days of invoice date",
    "45_days":    "Net 45 — Payment due within 45 days of invoice date",
    "advance":    "100% advance payment required before delivery",
}

_COMMON_HSN_SAC = {
    # Goods HSN
    "9403":  {"desc": "Office furniture", "gst": 18},
    "8471":  {"desc": "Computers & laptops", "gst": 18},
    "8517":  {"desc": "Mobile phones", "gst": 12},
    "6403":  {"desc": "Footwear", "gst": 18},
    "6204":  {"desc": "Readymade garments", "gst": 12},
    "1901":  {"desc": "Food preparations", "gst": 18},
    "3004":  {"desc": "Medicines", "gst": 12},
    "2710":  {"desc": "Petroleum products", "gst": 18},
    # Services SAC
    "998314": {"desc": "IT / Software services", "gst": 18},
    "998312": {"desc": "Management consulting", "gst": 18},
    "998313": {"desc": "Engineering services", "gst": 18},
    "997212": {"desc": "Commercial property rental", "gst": 18},
    "996311": {"desc": "Restaurant / food services", "gst": 5},
    "9971":   {"desc": "Financial & banking services", "gst": 18},
    "9993":   {"desc": "Health & education services", "gst": 0},
    "9954":   {"desc": "Construction services", "gst": 12},
    "998231": {"desc": "Accounting / CA services", "gst": 18},
    "998221": {"desc": "Legal services", "gst": 18},
    "9983":   {"desc": "Professional & technical services", "gst": 18},
    "9972":   {"desc": "Real estate services", "gst": 18},
}


# ── Round 17: Depreciation Calculator ────────────────────────────────────────

_ASSET_CATEGORIES = {
    "plant_machinery":   {"label": "Plant & Machinery",          "it_rate_wdv": 15.0, "companies_act_life": 15, "companies_act_slm": 6.33},
    "computers":         {"label": "Computers & Software",       "it_rate_wdv": 40.0, "companies_act_life": 3,  "companies_act_slm": 31.67},
    "furniture":         {"label": "Furniture & Fixtures",       "it_rate_wdv": 10.0, "companies_act_life": 10, "companies_act_slm": 9.50},
    "vehicles":          {"label": "Motor Vehicles",             "it_rate_wdv": 15.0, "companies_act_life": 8,  "companies_act_slm": 11.88},
    "buildings":         {"label": "Buildings (Office/Factory)", "it_rate_wdv": 10.0, "companies_act_life": 30, "companies_act_slm": 3.17},
    "intangibles":       {"label": "Intangible Assets",          "it_rate_wdv": 25.0, "companies_act_life": 10, "companies_act_slm": 9.50},
    "electrical":        {"label": "Electrical Fittings",        "it_rate_wdv": 10.0, "companies_act_life": 10, "companies_act_slm": 9.50},
    "office_equipment":  {"label": "Office Equipment",           "it_rate_wdv": 15.0, "companies_act_life": 5,  "companies_act_slm": 19.00},
}

_DEPRECIATION_NOTES = {
    "slm": [
        "SLM (Straight Line Method): Equal depreciation every year — simple and predictable.",
        "Used under Companies Act 2013 (Schedule II) for financial statements.",
        "Formula: (Cost − Salvage Value) ÷ Useful Life",
    ],
    "wdv": [
        "WDV (Written Down Value): Higher depreciation in early years — better for tax planning.",
        "Used under Income Tax Act 1961 for computing taxable income.",
        "Formula: Opening WDV × IT Rate% each year",
        "Under IT Act, depreciation is allowed on assets used for ≥180 days in FY (full rate); <180 days = 50% rate.",
    ],
    "double_declining": [
        "Double Declining Balance: Accelerated method — 2× the SLM rate applied on WDV.",
        "Common in IFRS; not standard under Indian IT Act but useful for management accounts.",
    ],
}


# ── Round 18: ITR Filing Checklist ───────────────────────────────────────────

_ITR_FORMS = {
    "salary_only":     {"form": "ITR-1 (Sahaj)", "who": "Salaried individuals with income up to ₹50L"},
    "salary_capital":  {"form": "ITR-2", "who": "Salaried + capital gains / foreign income / multiple properties"},
    "business":        {"form": "ITR-3", "who": "Individuals/HUF with business or profession income"},
    "presumptive":     {"form": "ITR-4 (Sugam)", "who": "Presumptive business income (44AD/44ADA/44AE)"},
    "company":         {"form": "ITR-6", "who": "Companies other than charitable trust"},
    "trust":           {"form": "ITR-7", "who": "Trusts / political parties / charitable institutions"},
}

_INCOME_SOURCE_DOCS = {
    "salary": {
        "label": "Salary Income",
        "documents": [
            "Form 16 (Part A + Part B) from all employers",
            "Salary slips for the full year (April to March)",
            "Form 12BB (if submitted to employer)",
            "Joining / relieving letter if changed jobs",
        ],
        "itr_schedule": "Schedule S — Salary",
    },
    "business": {
        "label": "Business / Professional Income",
        "documents": [
            "P&L Statement (audited if turnover > ₹1 crore; ₹50L for professionals)",
            "Balance Sheet as on 31st March",
            "GST returns (GSTR-1, GSTR-3B) for the full year",
            "Bank statements for all business accounts",
            "Purchase / sales invoices (sample set)",
            "Audit report (Form 3CD) if audit applicable",
            "Partnership deed / MoA / AoA if applicable",
        ],
        "itr_schedule": "Schedule BP — Business / Profession",
    },
    "capital_gains": {
        "label": "Capital Gains",
        "documents": [
            "Broker contract notes / P&L report for equity / mutual funds",
            "Form 26AS (capital gains section)",
            "Purchase deeds / cost of acquisition for property sold",
            "Indexed cost calculation worksheet for property",
            "Mutual fund capital gains statement (from AMC / CAMS / KFintech)",
            "Statement showing STT paid on equity transactions",
        ],
        "itr_schedule": "Schedule CG — Capital Gains",
    },
    "rental": {
        "label": "House Property / Rental Income",
        "documents": [
            "Rent receipts / rental agreement for each property",
            "Municipal tax receipts (deductible under Sec 24)",
            "Home loan interest certificate from bank (Sec 24(b))",
            "Property tax payment receipt",
            "Details of co-owner(s) and their share",
        ],
        "itr_schedule": "Schedule HP — House Property",
    },
    "other_income": {
        "label": "Other Income (Interest, Dividends, Gifts)",
        "documents": [
            "Bank interest certificates / passbook (FD, savings)",
            "Dividend warrants or Form 26AS (dividend section)",
            "Winning from lottery / game shows (if any)",
            "Gift deeds / receipts (gifts above ₹50,000 taxable)",
            "Interest on NSC, KVP, Post Office schemes",
        ],
        "itr_schedule": "Schedule OS — Other Sources",
    },
    "agriculture": {
        "label": "Agricultural Income",
        "documents": [
            "Land records / patta (proof of agricultural land ownership)",
            "Sale receipts for agricultural produce",
            "Revenue receipts from state government if exempt",
        ],
        "itr_schedule": "Schedule EI — Exempt Income",
    },
}

_DEDUCTION_DOCS = {
    "80c": {
        "label": "Section 80C (up to ₹1.5L)",
        "items": [
            "LIC premium receipts",
            "ELSS / Tax-saving mutual fund statements",
            "PPF passbook (contribution proof)",
            "EPF contribution (from Form 16)",
            "Children's school tuition fee receipts",
            "Home loan principal repayment certificate",
            "5-year FD / NSC certificates",
            "Sukanya Samriddhi account passbook",
        ],
    },
    "80d": {
        "label": "Section 80D — Health Insurance Premium (up to ₹25K / ₹50K senior)",
        "items": [
            "Health insurance premium receipt",
            "Premium receipt for parents' health insurance",
            "Preventive health check-up receipt (up to ₹5,000)",
        ],
    },
    "80e": {
        "label": "Section 80E — Education Loan Interest",
        "items": ["Education loan interest certificate from bank / NBFC"],
    },
    "80g": {
        "label": "Section 80G — Donations",
        "items": [
            "Donation receipts with PAN and 80G registration number of trust",
            "Bank statement showing donation payment",
        ],
    },
    "hra": {
        "label": "HRA Exemption (Sec 10(13A))",
        "items": [
            "Rent receipts (monthly, with landlord signature)",
            "Rental agreement",
            "Landlord's PAN (mandatory if annual rent > ₹1L)",
        ],
    },
    "nps": {
        "label": "Section 80CCD(1B) — NPS Additional ₹50K",
        "items": [
            "NPS Tier-1 contribution statement (PRAN statement)",
            "Transaction statement from NSDL CRA",
        ],
    },
    "home_loan_interest": {
        "label": "Section 24(b) — Home Loan Interest (up to ₹2L for self-occupied)",
        "items": [
            "Home loan interest certificate from lender",
            "Possession letter (for under-construction property)",
            "Provisional certificate if final not received",
        ],
    },
}

_COMMON_DOCS = [
    "PAN card",
    "Aadhaar card (linked to PAN)",
    "Form 26AS / Annual Information Statement (AIS) — download from IT portal",
    "Bank account details (IFSC + account number for refund)",
    "Bank statements for all accounts (April–March)",
    "Last year's ITR acknowledgement (ITR-V)",
    "Last year's assessment order / intimation (if any)",
]

_DEADLINES = {
    "non_audit_individual": "31st July of assessment year",
    "audit_required":       "31st October of assessment year",
    "company":              "31st October of assessment year",
    "revised_return":       "31st December of assessment year",
    "belated_return":       "31st December of assessment year (with penalty)",
}

_ITR_FORM_SELECTOR = {
    ("salary",):                                    "ITR-1 (Sahaj)",
    ("salary", "rental"):                           "ITR-1 (Sahaj)",
    ("salary", "capital_gains"):                    "ITR-2",
    ("salary", "rental", "capital_gains"):          "ITR-2",
    ("business",):                                  "ITR-3 or ITR-4 (Sugam if presumptive)",
    ("salary", "business"):                         "ITR-3",
}


# ── Round 19: Salary Slip Generator ─────────────────────────────────────────

_PT_SLABS = {
    "karnataka":     [(15000, 0), (14999, 150), (999999, 200)],  # monthly gross → PT
    "maharashtra":   [(7500, 0), (7500, 175), (999999, 200)],
    "andhra_pradesh":[(15000, 0), (999999, 150)],
    "telangana":     [(15000, 0), (999999, 150)],
    "west_bengal":   [(10000, 0), (999999, 110)],
    "tamil_nadu":    [(21000, 0), (999999, 208)],
    "gujarat":       [(5999, 0), (999999, 200)],
    "delhi":         [(999999, 0)],  # No PT in Delhi
    "none":          [(999999, 0)],
}

_ALLOWANCE_LABELS = {
    "basic":        "Basic Salary",
    "hra":          "House Rent Allowance (HRA)",
    "ta":           "Travel Allowance",
    "medical":      "Medical Allowance",
    "special":      "Special Allowance",
    "lta":          "Leave Travel Allowance",
}

_DEDUCTION_LABELS = {
    "pf_employee":  "Provident Fund (Employee 12%)",
    "esi":          "ESI (Employee 0.75%)",
    "pt":           "Professional Tax",
    "tds":          "TDS (Income Tax)",
    "advance":      "Advance Recovery",
    "lop":          "Loss of Pay",
}


# ── Round 20: Multi-Client Compliance Dashboard ───────────────────────────────

_COMPLIANCE_DEADLINES = {
    "gst_monthly":   {"return": "GSTR-1", "due_day": 11, "frequency": "monthly",   "penalty": "₹50/day (₹20 for nil return)"},
    "gst_quarterly": {"return": "GSTR-1 (QRMP)", "due_day": 13, "frequency": "quarterly", "penalty": "₹50/day"},
    "gstr3b_monthly":{"return": "GSTR-3B", "due_day": 20, "frequency": "monthly",  "penalty": "₹50/day + 18% interest on tax"},
    "tds_quarterly": {"return": "TDS Return (26Q/24Q)", "due_day": 31, "frequency": "quarterly", "penalty": "₹200/day u/s 234E"},
    "tds_payment":   {"return": "TDS Challan Payment", "due_day": 7, "frequency": "monthly", "penalty": "1.5%/month interest"},
    "itr_individual":{"return": "ITR-1/ITR-2", "due_day": 31, "month": "July", "frequency": "annual", "penalty": "₹5,000 (₹1,000 if income < 5L)"},
    "itr_business":  {"return": "ITR-3/ITR-4", "due_day": 31, "month": "July", "frequency": "annual", "penalty": "₹5,000"},
    "itr_audit":     {"return": "ITR (Audit Cases)", "due_day": 31, "month": "October", "frequency": "annual", "penalty": "₹5,000"},
    "pt_monthly":    {"return": "Professional Tax", "due_day": 15, "frequency": "monthly", "penalty": "Varies by state"},
    "roc_annual":    {"return": "MGT-7 / AOC-4", "due_day": 60, "note": "60 days from AGM", "frequency": "annual", "penalty": "₹100/day"},
}

_RISK_FLAGS = {
    "nil_return_pending": "GST nil return not filed — ₹20/day accumulating",
    "tds_not_deducted":   "TDS not deducted on eligible payments — disallowance risk u/s 40a(ia)",
    "itr_not_filed":      "ITR not filed — Interest u/s 234A + penalty u/s 271F",
    "audit_due":          "Audit report not filed — Penalty u/s 271B (₹1.5L or 0.5% of turnover)",
    "gst_mismatch":       "GSTR-1 vs GSTR-3B mismatch — ITC denial risk for recipients",
    "overdue_invoice":    "Invoices unpaid >45 days — MSME Act violation risk for payers",
}


# ── Round 21: Form 16 Generator ──────────────────────────────────────────────

_FORM16_TAX_SLABS_NEW = [
    (300000,  0,    "Nil"),
    (600000,  0.05, "5%"),
    (900000,  0.10, "10%"),
    (1200000, 0.15, "15%"),
    (1500000, 0.20, "20%"),
    (float('inf'), 0.30, "30%"),
]

_DEDUCTION_HEADS_80C = ["PPF", "ELSS", "LIC Premium", "Home Loan Principal", "Tuition Fees", "NPS (80CCD1)", "EPF Contribution"]
_DEDUCTION_80D = "Medical insurance premium"
_HRA_EXEMPTION_NOTE = "HRA exemption calculated as min of: actual HRA received, 50%/40% of basic (metro/non-metro), rent paid minus 10% of basic"


# ── R22: Balance Sheet Builder ───────────────────────────────────────────────

_BS_RATIOS = {
    "current_ratio":       {"formula": "Current Assets / Current Liabilities", "healthy": "> 1.5", "warning": "< 1.0"},
    "debt_to_equity":      {"formula": "Total Debt / Shareholders Equity",     "healthy": "< 1.0", "warning": "> 2.0"},
    "working_capital":     {"formula": "Current Assets - Current Liabilities", "healthy": "Positive", "warning": "Negative"},
    "asset_turnover":      {"formula": "Revenue / Total Assets",               "healthy": "> 1.0", "warning": "< 0.5"},
}

_BS_INDUSTRY_BENCHMARKS = {
    "manufacturing":   {"current_ratio": 1.8, "debt_to_equity": 0.9},
    "retail":          {"current_ratio": 1.4, "debt_to_equity": 0.7},
    "services":        {"current_ratio": 1.6, "debt_to_equity": 0.5},
    "technology":      {"current_ratio": 2.5, "debt_to_equity": 0.3},
    "real_estate":     {"current_ratio": 1.2, "debt_to_equity": 1.5},
    "hospitality":     {"current_ratio": 1.1, "debt_to_equity": 1.2},
}

_BS_NOTES_TEMPLATES = {
    "high_debt":    "Debt-to-equity ratio is above industry benchmark. Consider debt restructuring or equity infusion.",
    "low_liquidity":"Current ratio below 1.5 — monitor working capital closely to avoid cash flow stress.",
    "strong_equity":"Healthy equity base. Company is well-positioned for expansion or credit.",
    "healthy":      "Balance sheet is healthy. Key ratios are within or above industry benchmarks.",
}


def generate_balance_sheet(
    company_name: str,
    period: str,
    industry: str,
    # Fixed Assets
    land_building: float = 0,
    plant_machinery: float = 0,
    furniture: float = 0,
    vehicles: float = 0,
    intangibles: float = 0,
    # Current Assets
    cash: float = 0,
    bank: float = 0,
    debtors: float = 0,
    inventory: float = 0,
    loans_advances: float = 0,
    other_current: float = 0,
    # Equity & Reserves
    share_capital: float = 0,
    reserves_surplus: float = 0,
    # Long-term Liabilities
    long_term_loans: float = 0,
    deferred_tax: float = 0,
    # Current Liabilities
    creditors: float = 0,
    short_term_loans: float = 0,
    provisions: float = 0,
    other_current_liab: float = 0,
    language: str = "en",
) -> dict:
    # Assets
    total_fixed = land_building + plant_machinery + furniture + vehicles + intangibles
    total_current_assets = cash + bank + debtors + inventory + loans_advances + other_current
    total_assets = total_fixed + total_current_assets

    # Liabilities
    total_equity = share_capital + reserves_surplus
    total_lt_liab = long_term_loans + deferred_tax
    total_current_liab = creditors + short_term_loans + provisions + other_current_liab
    total_equity_liab = total_equity + total_lt_liab + total_current_liab

    # Balance check
    difference = round(total_assets - total_equity_liab, 2)
    balanced = abs(difference) < 1

    # Ratios
    cur_ratio = round(total_current_assets / total_current_liab, 2) if total_current_liab else 0
    d2e = round((long_term_loans + short_term_loans) / total_equity, 2) if total_equity else 0
    working_cap = round(total_current_assets - total_current_liab, 2)

    bench = _BS_INDUSTRY_BENCHMARKS.get(industry.lower(), _BS_INDUSTRY_BENCHMARKS["services"])

    # Notes
    notes = []
    if d2e > bench["debt_to_equity"] * 1.5:
        notes.append(_BS_NOTES_TEMPLATES["high_debt"])
    if cur_ratio < 1.5:
        notes.append(_BS_NOTES_TEMPLATES["low_liquidity"])
    if not notes:
        notes.append(_BS_NOTES_TEMPLATES["healthy"] if cur_ratio >= bench["current_ratio"] else _BS_NOTES_TEMPLATES["low_liquidity"])

    return {
        "company": company_name,
        "period": period,
        "industry": industry,
        "balanced": balanced,
        "difference": difference,
        "assets": {
            "fixed_assets": {
                "land_and_building": land_building,
                "plant_and_machinery": plant_machinery,
                "furniture_and_fixtures": furniture,
                "vehicles": vehicles,
                "intangible_assets": intangibles,
                "total_fixed_assets": round(total_fixed, 2),
            },
            "current_assets": {
                "cash_in_hand": cash,
                "bank_balances": bank,
                "trade_debtors": debtors,
                "inventory": inventory,
                "loans_and_advances": loans_advances,
                "other_current_assets": other_current,
                "total_current_assets": round(total_current_assets, 2),
            },
            "total_assets": round(total_assets, 2),
        },
        "equity_and_liabilities": {
            "shareholders_equity": {
                "share_capital": share_capital,
                "reserves_and_surplus": reserves_surplus,
                "total_equity": round(total_equity, 2),
            },
            "long_term_liabilities": {
                "long_term_loans": long_term_loans,
                "deferred_tax_liability": deferred_tax,
                "total_lt_liabilities": round(total_lt_liab, 2),
            },
            "current_liabilities": {
                "trade_creditors": creditors,
                "short_term_borrowings": short_term_loans,
                "provisions": provisions,
                "other_current_liabilities": other_current_liab,
                "total_current_liabilities": round(total_current_liab, 2),
            },
            "total_equity_and_liabilities": round(total_equity_liab, 2),
        },
        "ratios": {
            "current_ratio": {"value": cur_ratio, "benchmark": bench["current_ratio"],
                               "status": "✅ Healthy" if cur_ratio >= bench["current_ratio"] else "⚠️ Below benchmark"},
            "debt_to_equity": {"value": d2e, "benchmark": bench["debt_to_equity"],
                                "status": "✅ Healthy" if d2e <= bench["debt_to_equity"] else "⚠️ Above benchmark"},
            "working_capital": {"value": working_cap, "status": "✅ Positive" if working_cap > 0 else "🔴 Negative"},
        },
        "auditor_notes": notes,
        "schedule_vi_ready": True,
    }


# ── R23: Advance Tax Calculator ──────────────────────────────────────────────

_ADV_TAX_INSTALLMENTS = [
    {"quarter": "Q1", "due_date": "15 June",      "cumulative_pct": 15, "section": "207"},
    {"quarter": "Q2", "due_date": "15 September", "cumulative_pct": 45, "section": "207"},
    {"quarter": "Q3", "due_date": "15 December",  "cumulative_pct": 75, "section": "207"},
    {"quarter": "Q4", "due_date": "15 March",     "cumulative_pct": 100,"section": "207"},
]

_ADV_TAX_OLD_SLABS_IND = [
    (250000, 0.0), (250000, 0.05), (500000, 0.20), (float('inf'), 0.30)
]

_ADV_TAX_NEW_SLABS = [
    (300000, 0.0), (300000, 0.05), (300000, 0.10), (300000, 0.15), (300000, 0.20), (float('inf'), 0.30)
]

_INTEREST_RATE_PER_MONTH = 0.01  # 1% per month u/s 234B & 234C


def _calc_tax_on_slabs(income: float, slabs: list) -> float:
    tax = 0.0
    remaining = income
    for limit, rate in slabs:
        taxable = min(remaining, limit)
        tax += taxable * rate
        remaining -= taxable
        if remaining <= 0:
            break
    return tax


# ── R24: Partnership Deed Generator ──────────────────────────────────────────

_DEED_CLAUSES = {
    "nature_of_business": "The partners shall carry on the business of {business_nature} under the firm name '{firm_name}'.",
    "commencement":       "The partnership shall commence on {commencement_date} and shall continue {duration_clause}.",
    "capital":            "Each partner shall contribute capital as agreed and specified in Schedule A. Additional capital may be introduced by unanimous consent.",
    "profit_loss":        "The net profits and losses of the firm shall be shared among the partners in the following ratio: {profit_loss_ratio}.",
    "interest_on_capital":"Interest on capital shall be allowed at the rate of {interest_rate}% per annum as per Section 40(b) of the Income Tax Act, 1961.",
    "partner_salary":     "Working partners shall be entitled to salary/remuneration as agreed and within limits prescribed under Section 40(b) of the Income Tax Act.",
    "drawings":           "Each partner may draw from the firm account such amounts as agreed, subject to the firm's working capital requirements.",
    "bank_operations":    "The firm's bank account at {bank_name} shall be operated jointly by any two partners / by {managing_partner}.",
    "books_of_accounts":  "Proper books of accounts shall be maintained at the principal place of business and shall be open for inspection by all partners.",
    "audit":              "The accounts of the firm shall be audited annually by a Chartered Accountant appointed by mutual consent.",
    "admission":          "No new partner shall be admitted into the firm without the written consent of all existing partners.",
    "retirement":         "Any partner wishing to retire shall give [3 months] written notice to the other partners.",
    "death_dissolution":  "In the event of death or insolvency of a partner, the remaining partners shall have the option to purchase the deceased/insolvent partner's share at fair value.",
    "arbitration":        "Any dispute arising between the partners shall be referred to arbitration under the Arbitration and Conciliation Act, 1996.",
    "governing_law":      "This deed shall be governed by the Indian Partnership Act, 1932 and the laws in force in the State of {state}.",
}

_DURATION_CLAUSES = {
    "at_will":   "until dissolved by mutual consent or as per the provisions of this deed",
    "fixed":     "for a fixed term of {term} years from the date of commencement",
    "project":   "until the completion of the project for which it was formed",
}

_STAMP_DUTY_BY_STATE = {
    "Maharashtra": "₹500 stamp paper",
    "Karnataka":   "₹200 stamp paper",
    "Tamil Nadu":  "₹100 stamp paper",
    "Delhi":       "₹1,000 stamp paper",
    "Gujarat":     "₹300 stamp paper",
    "Telangana":   "₹200 stamp paper",
    "default":     "stamp paper as per state stamp duty act",
}


# ── R25: Startup India Registration Guide ────────────────────────────────────

_STARTUP_ENTITY_TYPES = {
    "private_limited": {
        "name":        "Private Limited Company",
        "law":         "Companies Act 2013",
        "min_capital": "No minimum",
        "members":     "2–200 shareholders",
        "liability":   "Limited",
        "ideal_for":   "VC/PE funding, scalable startups",
    },
    "llp": {
        "name":        "Limited Liability Partnership",
        "law":         "LLP Act 2008",
        "min_capital": "No minimum",
        "members":     "Min 2 designated partners",
        "liability":   "Limited",
        "ideal_for":   "Professional services, small teams",
    },
    "opc": {
        "name":        "One Person Company",
        "law":         "Companies Act 2013",
        "min_capital": "No minimum",
        "members":     "1 shareholder",
        "liability":   "Limited",
        "ideal_for":   "Solo founders, service businesses",
    },
    "partnership": {
        "name":        "Partnership Firm",
        "law":         "Indian Partnership Act 1932",
        "min_capital": "No minimum",
        "members":     "2–20 partners",
        "liability":   "Unlimited",
        "ideal_for":   "Family/small businesses, low formality",
    },
}

_STARTUP_INDIA_BENEFITS = [
    "Self-certification under 9 labour and 3 environment laws",
    "Fast-track patent examination at 80% discounted cost",
    "Income tax exemption under Sec 80-IAC for 3 consecutive years (out of 10)",
    "Exemption from Angel Tax (Sec 56(2)(viib)) for DPIIT recognised startups",
    "₹10 lakh seed funding via Startup India Seed Fund Scheme (SISFS)",
    "Government tender relaxation — no prior experience / turnover required",
    "Easy winding up within 90 days under Insolvency & Bankruptcy Code",
    "Access to SIDBI Fund of Funds (₹10,000 cr corpus)",
    "Networking & mentorship through Startup India Hub",
    "State-specific incentives (e.g. Tamil Nadu: TANSIM, Karnataka: Elevate)",
]

_STARTUP_REGISTRATION_STEPS = {
    "private_limited": [
        {"step": 1,  "action": "Obtain DSC (Digital Signature Certificate) for all directors",              "timeline": "1–2 days",  "portal": "MCA21 / private agencies"},
        {"step": 2,  "action": "Obtain DIN (Director Identification Number) via SPICe+ form",               "timeline": "1–2 days",  "portal": "mca.gov.in"},
        {"step": 3,  "action": "Name approval via SPICe+ Part A (RUN form)",                                "timeline": "2–5 days",  "portal": "mca.gov.in"},
        {"step": 4,  "action": "Draft MOA & AOA",                                                           "timeline": "1 day",     "portal": "Company Secretary"},
        {"step": 5,  "action": "File SPICe+ Part B for incorporation",                                      "timeline": "3–5 days",  "portal": "mca.gov.in"},
        {"step": 6,  "action": "Receive Certificate of Incorporation (CoI) + CIN + PAN + TAN",             "timeline": "1–2 days",  "portal": "MCA21"},
        {"step": 7,  "action": "Open current bank account in company name",                                 "timeline": "2–3 days",  "portal": "Bank"},
        {"step": 8,  "action": "File INC-20A (Declaration of Commencement of Business)",                   "timeline": "Within 180 days of CoI", "portal": "mca.gov.in"},
        {"step": 9,  "action": "Apply for DPIIT Startup India recognition on Startup India portal",         "timeline": "2–5 days",  "portal": "startupindia.gov.in"},
        {"step": 10, "action": "Apply for GST registration if applicable",                                  "timeline": "3–7 days",  "portal": "gst.gov.in"},
        {"step": 11, "action": "Apply for MSME/Udyam registration",                                        "timeline": "Instant",   "portal": "udyamregistration.gov.in"},
        {"step": 12, "action": "Register for ESI/PF if headcount ≥ 10/20",                                "timeline": "As applicable", "portal": "esic.in / epfindia.gov.in"},
    ],
    "llp": [
        {"step": 1, "action": "Obtain DSC for designated partners",                                        "timeline": "1–2 days",  "portal": "MCA21"},
        {"step": 2, "action": "Apply for DPIN (Designated Partner Identification Number)",                  "timeline": "1–2 days",  "portal": "mca.gov.in"},
        {"step": 3, "action": "Name reservation via RUN-LLP",                                              "timeline": "2–3 days",  "portal": "mca.gov.in"},
        {"step": 4, "action": "File FiLLiP (Form for Incorporation of LLP)",                               "timeline": "3–5 days",  "portal": "mca.gov.in"},
        {"step": 5, "action": "Draft and file LLP Agreement within 30 days",                               "timeline": "30 days",   "portal": "mca.gov.in (Form 3)"},
        {"step": 6, "action": "Receive Certificate of Incorporation",                                      "timeline": "1–2 days",  "portal": "MCA21"},
        {"step": 7, "action": "Open current bank account",                                                 "timeline": "2–3 days",  "portal": "Bank"},
        {"step": 8, "action": "Apply for GST / MSME / DPIIT recognition",                                 "timeline": "2–7 days",  "portal": "Respective portals"},
    ],
}

_STARTUP_COMPLIANCES = {
    "annual": [
        "ROC Annual Return (MGT-7 / LLP-11) — 60 days from AGM",
        "Financial Statements (AOC-4) — 30 days from AGM",
        "Income Tax Return — 31 Oct (audit) / 31 Jul (non-audit)",
        "DPT-3 (Deposits Return) — 30 June",
        "DIR-3 KYC for all directors — 30 September",
        "MSME Form I if outstanding payments to MSME > 45 days",
    ],
    "monthly": [
        "GST Return (GSTR-1, GSTR-3B) — 11th & 20th of next month",
        "TDS payment by 7th of next month",
        "Advance Tax instalments — Jun 15, Sep 15, Dec 15, Mar 15",
        "PF/ESI challan by 15th of next month",
    ],
}

_STARTUP_COSTS = {
    "private_limited": {"govt_fees": "₹0–₹2,000 (waived for authorised capital ≤ ₹15L)", "professional": "₹8,000–₹25,000", "total_est": "₹8,000–₹30,000"},
    "llp":             {"govt_fees": "₹500–₹5,600",  "professional": "₹5,000–₹15,000", "total_est": "₹6,000–₹20,000"},
    "opc":             {"govt_fees": "₹0–₹2,000",    "professional": "₹6,000–₹15,000", "total_est": "₹6,000–₹18,000"},
    "partnership":     {"govt_fees": "₹0–₹500",      "professional": "₹2,000–₹5,000",  "total_est": "₹2,000–₹6,000"},
}


# ── R26: Director's Report Generator ─────────────────────────────────────────

_DR_SECTIONS = [
    "state_of_company_affairs",
    "financial_highlights",
    "dividend",
    "reserves",
    "share_capital",
    "directors_responsibility_statement",
    "auditors",
    "related_party_transactions",
    "material_changes",
    "conservation_of_energy",
    "technology_absorption",
    "foreign_exchange",
    "risk_management",
    "corporate_social_responsibility",
    "vigil_mechanism",
    "declarations",
    "acknowledgement",
]

_DR_RESPONSIBILITY_STATEMENT = [
    "The applicable accounting standards have been followed in preparation of annual accounts and there are no material departures.",
    "Accounting policies have been selected and applied consistently; judgements and estimates made are reasonable and prudent.",
    "Proper and sufficient care has been taken for the maintenance of adequate accounting records in accordance with the provisions of the Companies Act, 2013.",
    "The annual accounts have been prepared on a going concern basis.",
    "Internal financial controls have been laid down and such controls are adequate and operating effectively.",
    "Proper systems have been devised to ensure compliance with the provisions of all applicable laws and such systems are adequate and operating effectively.",
]

_DR_AUDITOR_STATEMENTS = {
    "no_qualification": "The Auditors' Report does not contain any qualification, reservation or adverse remark.",
    "qualified":        "The Auditors' Report contains the following qualifications/remarks: [Details]. The Board's explanation: [Explanation].",
    "secretarial":      "The Secretarial Audit Report for the year is annexed as Annexure and does not contain any qualification, reservation or adverse remark.",
}

_DR_CSR_NOTE = "As per Section 135 of the Companies Act, 2013, the provisions of CSR are applicable to companies with net worth ≥ ₹500 crore OR turnover ≥ ₹1,000 crore OR net profit ≥ ₹5 crore."

_DR_RISK_CATEGORIES = [
    {"risk": "Market Risk",       "mitigation": "Diversified revenue streams, regular market analysis"},
    {"risk": "Credit Risk",       "mitigation": "Strict credit appraisal, customer credit limits"},
    {"risk": "Operational Risk",  "mitigation": "SOPs, internal audits, business continuity plan"},
    {"risk": "Regulatory Risk",   "mitigation": "Dedicated compliance team, periodic legal review"},
    {"risk": "Technology Risk",   "mitigation": "Cybersecurity policy, data backup, IT audits"},
    {"risk": "Human Resource Risk","mitigation": "Competitive remuneration, succession planning, training"},
]


# ── R27: MCA / ROC Filing Calendar ───────────────────────────────────────────

_ROC_FILINGS = [
    # Form, Description, Due Date, Applicable To, Penalty
    {"form":"MGT-7 / MGT-7A", "desc":"Annual Return",                      "due":"Within 60 days of AGM (usually by 29 Nov for 31 Mar FY)",     "applicable":"All companies",                    "penalty":"₹100/day per form"},
    {"form":"AOC-4 / AOC-4 XBRL","desc":"Financial Statements",             "due":"Within 30 days of AGM (usually by 29 Oct for 31 Mar FY)",     "applicable":"All companies",                    "penalty":"₹100/day per form"},
    {"form":"ADT-1",          "desc":"Auditor Appointment",                 "due":"Within 15 days of AGM",                                       "applicable":"All companies on auditor change",  "penalty":"₹100/day"},
    {"form":"DIR-3 KYC",      "desc":"Director KYC",                        "due":"30 September every year",                                     "applicable":"All directors with DIN",           "penalty":"₹5,000 per director"},
    {"form":"DPT-3",          "desc":"Return of Deposits",                  "due":"30 June every year",                                          "applicable":"Companies with deposits/loans",    "penalty":"₹500–₹5,000/day"},
    {"form":"MSME-1",         "desc":"MSME Outstanding Payments",           "due":"30 April (Oct–Mar period) / 31 Oct (Apr–Sep period)",          "applicable":"Companies with MSME vendor dues>45 days","penalty":"₹25,000–₹3 lakh"},
    {"form":"BEN-2",          "desc":"Beneficial Owner Declaration",        "due":"Within 30 days of receipt of BEN-1",                          "applicable":"Companies with significant beneficial owners","penalty":"₹1,000/day"},
    {"form":"INC-20A",        "desc":"Business Commencement",               "due":"Within 180 days of CoI",                                      "applicable":"New companies (Pvt Ltd / OPC)",    "penalty":"₹50,000 company + ₹1,000/day directors"},
    {"form":"PAS-6",          "desc":"Reconciliation of Share Capital Audit","due":"60 days from end of each half-year",                          "applicable":"Unlisted public companies",         "penalty":"₹1,000/day"},
    {"form":"LLP-11",         "desc":"LLP Annual Return",                   "due":"30 May every year",                                           "applicable":"LLPs",                             "penalty":"₹100/day"},
    {"form":"Form 8 (LLP)",   "desc":"LLP Statement of Accounts",           "due":"30 October every year",                                       "applicable":"LLPs",                             "penalty":"₹100/day"},
    {"form":"MGT-14",         "desc":"Board/Member Resolutions",            "due":"Within 30 days of passing resolution",                        "applicable":"Public companies / listed cos",     "penalty":"₹1,000/day"},
    {"form":"INC-22A (ACTIVE)","desc":"Active Company Tagging",             "due":"One-time compliance (check if done)",                         "applicable":"Companies incorporated before 2017","penalty":"₹10,000"},
]

_TAX_CALENDAR = [
    {"month":"April",    "due_dates":["7 Apr: TDS payment (Mar)", "15 Apr: ESI/PF challan (Mar)", "30 Apr: MSME-1 (Oct–Mar)"]},
    {"month":"May",      "due_dates":["7 May: TDS payment (Apr)", "15 May: ESI/PF challan (Apr)", "30 May: LLP Annual Return (Form 11)", "31 May: TDS Return (Q4 Jan–Mar)"]},
    {"month":"June",     "due_dates":["7 Jun: TDS payment (May)", "15 Jun: Advance Tax Instalment 1 (15%)", "15 Jun: ESI/PF challan (May)", "30 Jun: DPT-3 Return of Deposits"]},
    {"month":"July",     "due_dates":["7 Jul: TDS payment (Jun)", "15 Jul: TDS Certificate (Q1)", "15 Jul: ESI/PF challan (Jun)", "31 Jul: ITR (non-audit individuals)", "31 Jul: TDS Return (Q1 Apr–Jun)"]},
    {"month":"August",   "due_dates":["7 Aug: TDS payment (Jul)", "15 Aug: ESI/PF challan (Jul)"]},
    {"month":"September","due_dates":["7 Sep: TDS payment (Aug)", "15 Sep: Advance Tax Instalment 2 (45% cumulative)", "15 Sep: ESI/PF challan (Aug)", "30 Sep: DIR-3 KYC", "30 Sep: AGM deadline (31 Mar FY)"]},
    {"month":"October",  "due_dates":["7 Oct: TDS payment (Sep)", "15 Oct: TDS Certificate (Q2)", "15 Oct: ESI/PF challan (Sep)", "29 Oct: AOC-4 Financial Statements (if AGM on 30 Sep)", "31 Oct: ITR (audit cases)", "31 Oct: LLP Form 8", "31 Oct: MSME-1 (Apr–Sep)"]},
    {"month":"November", "due_dates":["7 Nov: TDS payment (Oct)", "15 Nov: ESI/PF challan (Oct)", "29 Nov: MGT-7 Annual Return (if AGM on 30 Sep)", "30 Nov: TDS Return (Q2 Jul–Sep)"]},
    {"month":"December", "due_dates":["7 Dec: TDS payment (Nov)", "15 Dec: Advance Tax Instalment 3 (75% cumulative)", "15 Dec: ESI/PF challan (Nov)"]},
    {"month":"January",  "due_dates":["7 Jan: TDS payment (Dec)", "15 Jan: TDS Certificate (Q3)", "15 Jan: ESI/PF challan (Dec)", "31 Jan: TDS Return (Q3 Oct–Dec)"]},
    {"month":"February", "due_dates":["7 Feb: TDS payment (Jan)", "15 Feb: ESI/PF challan (Jan)"]},
    {"month":"March",    "due_dates":["7 Mar: TDS payment (Feb)", "15 Mar: Advance Tax Instalment 4 (100%)", "15 Mar: ESI/PF challan (Feb)", "31 Mar: Invest for tax-saving (80C, 80D, NPS etc.)"]},
]

_HIGH_RISK_FILINGS = ["DIR-3 KYC", "INC-20A", "AOC-4 / AOC-4 XBRL", "MGT-7 / MGT-7A", "DPT-3"]


def generate_mca_roc_calendar(
    company_name: str,
    entity_type: str = "private_limited",
    fy_end_month: str = "March",
    has_msme_vendors: bool = False,
    has_deposits: bool = False,
    is_newly_incorporated: bool = False,
    language: str = "en",
) -> dict:
    # Filter relevant filings
    filings = []
    for f in _ROC_FILINGS:
        applicable = f["applicable"].lower()
        include = True

        # Skip LLP-specific for companies
        if entity_type in ("private_limited","opc","public") and "llp" in applicable:
            include = False
        # Skip company-specific for LLPs
        if entity_type == "llp" and "llp" not in applicable and "all companies" not in applicable:
            include = False
        if not has_msme_vendors and "msme" in applicable:
            include = False
        if not has_deposits and "deposit" in applicable.lower():
            include = False
        if not is_newly_incorporated and ("new compan" in applicable or "incorporated before" in applicable):
            include = False

        if include:
            filings.append({
                **f,
                "high_risk": f["form"] in _HIGH_RISK_FILINGS,
            })

    # GST monthly reminders
    gst_reminders = [
        "11th of each month: GSTR-1 (outward supplies)",
        "13th of each month: GSTR-2B auto-populated (ITC reconciliation)",
        "20th of each month: GSTR-3B (summary + payment)",
        "Quarterly GSTR-1 (QRMP scheme): 13th of month after quarter end",
    ]

    return {
        "company_name":    company_name,
        "entity_type":     entity_type,
        "fy_end_month":    fy_end_month,
        "roc_filings":     filings,
        "tax_calendar":    _TAX_CALENDAR,
        "gst_reminders":   gst_reminders,
        "high_risk_forms": _HIGH_RISK_FILINGS,
        "penalty_summary": {
            "late_filing_general": "₹100 per day per form (no cap for most forms)",
            "dir_3_kyc":           "₹5,000 per director if DIN marked deactivated",
            "inc_20a":             "₹50,000 company + ₹1,000/day for directors until filed",
            "dpt_3":               "₹500–₹5,000 per day; personal liability on officers",
        },
        "best_practices": [
            "Maintain a compliance tracker with due dates and responsible person",
            "Set calendar reminders 15 days before each due date",
            "File AOC-4 and MGT-7 together — they share most data",
            "DIR-3 KYC is annual — missing it deactivates your DIN",
            "MSME-1 is semi-annual — check vendor registration before filing",
            "Pre-pay advance tax to avoid 234B/C interest",
            "Reconcile GSTR-2B with books monthly to maximise ITC",
        ],
        "ca_notes": [
            "ROC due dates shift if AGM is held before 30 Sep — recalculate accordingly",
            "Strike-off companies still have pending filing obligations — check before closure",
            "LLP annual filings (Form 11 and Form 8) have different deadlines from Pvt Ltd",
            "XBRL filing required for companies with turnover >₹500 Cr or listed companies",
            "Condonation of delay for overdue filings available via CFSS schemes periodically",
        ],
    }


def generate_directors_report(
    company_name: str,
    cin: str,
    fy_start: str,
    fy_end: str,
    revenue: float = 0.0,
    profit_before_tax: float = 0.0,
    profit_after_tax: float = 0.0,
    dividend_declared: bool = False,
    dividend_per_share: float = 0.0,
    directors: list = None,
    new_directors: list = None,
    resigned_directors: list = None,
    auditor_status: str = "no_qualification",
    csr_applicable: bool = False,
    csr_amount_spent: float = 0.0,
    foreign_exchange_earnings: float = 0.0,
    foreign_exchange_outgo: float = 0.0,
    language: str = "en",
) -> dict:
    directors = directors or []
    new_directors = new_directors or []
    resigned_directors = resigned_directors or []

    revenue_cr     = revenue / 1e7
    pbt_cr         = profit_before_tax / 1e7
    pat_cr         = profit_after_tax / 1e7
    fx_earn_lakhs  = foreign_exchange_earnings / 1e5
    fx_out_lakhs   = foreign_exchange_outgo / 1e5

    report_sections = {}

    report_sections["state_of_company_affairs"] = (
        f"During the financial year {fy_start} to {fy_end}, the Company carried on its business satisfactorily. "
        f"The total revenue for the year stood at ₹{revenue_cr:.2f} crore. "
        f"The Profit Before Tax (PBT) was ₹{pbt_cr:.2f} crore and Profit After Tax (PAT) was ₹{pat_cr:.2f} crore. "
        f"The Board of Directors is pleased to report that the Company continued to maintain its growth trajectory."
    )

    if dividend_declared:
        report_sections["dividend"] = (
            f"The Board of Directors is pleased to recommend a dividend of ₹{dividend_per_share:.2f} per equity share "
            f"(face value ₹10 each) for the financial year {fy_end}, subject to approval of shareholders at the ensuing Annual General Meeting."
        )
    else:
        report_sections["dividend"] = (
            f"In order to conserve resources for future growth and operations, the Board of Directors does not recommend "
            f"any dividend for the financial year ended {fy_end}."
        )

    report_sections["reserves"] = (
        f"The Company proposes to transfer the net profit of ₹{pat_cr:.2f} crore to the Reserves and Surplus. "
        f"No amount has been transferred to the General Reserve during the year."
    )

    report_sections["directors_responsibility_statement"] = _DR_RESPONSIBILITY_STATEMENT

    report_sections["auditors"] = _DR_AUDITOR_STATEMENTS.get(auditor_status, _DR_AUDITOR_STATEMENTS["no_qualification"])

    report_sections["related_party_transactions"] = (
        "All related party transactions that were entered into during the financial year were on arm's length basis "
        "and were in the ordinary course of business. There are no materially significant related party transactions "
        "which may have a potential conflict with the interest of the Company at large."
    )

    report_sections["material_changes"] = (
        f"There have been no material changes and commitments affecting the financial position of the Company "
        f"which have occurred between the end of the financial year {fy_end} and the date of this Report."
    )

    report_sections["conservation_of_energy"] = (
        "The Company continues to take measures to reduce energy consumption by using energy-efficient equipment "
        "and processes. LED lighting, energy-star rated equipment, and awareness programmes have been implemented."
    )

    report_sections["technology_absorption"] = (
        "The Company has not imported any technology during the year. The Company continues to explore and adopt "
        "latest technologies to improve its processes and product quality."
    )

    report_sections["foreign_exchange"] = {
        "earnings": f"₹{fx_earn_lakhs:.2f} lakhs" if foreign_exchange_earnings else "Nil",
        "outgo":    f"₹{fx_out_lakhs:.2f} lakhs" if foreign_exchange_outgo else "Nil",
    }

    report_sections["risk_management"] = _DR_RISK_CATEGORIES

    if csr_applicable:
        report_sections["corporate_social_responsibility"] = {
            "applicable": True,
            "amount_spent": f"₹{csr_amount_spent/1e5:.2f} lakhs",
            "note": _DR_CSR_NOTE,
        }
    else:
        report_sections["corporate_social_responsibility"] = {
            "applicable": False,
            "note": "The provisions of Section 135 of the Companies Act, 2013 relating to Corporate Social Responsibility are not applicable to the Company during the year under review.",
        }

    report_sections["vigil_mechanism"] = (
        "The Company has established a Vigil Mechanism/Whistle Blower Policy to deal with instances of fraud and "
        "mismanagement, if any. The details of the Vigil Mechanism Policy are available on the Company's website."
    )

    report_sections["declarations"] = [
        "The Company has not accepted any deposits within the meaning of Section 73 of the Companies Act, 2013.",
        "No significant or material orders have been passed by the Regulators or Courts during the year.",
        "The Company has in place adequate internal financial controls with reference to financial statements.",
        "The Company has complied with the applicable Secretarial Standards issued by the Institute of Company Secretaries of India.",
    ]

    director_changes = []
    for d in new_directors:
        director_changes.append(f"{d.get('name','')} was appointed as {d.get('designation','')} w.e.f. {d.get('date','')}")
    for d in resigned_directors:
        director_changes.append(f"{d.get('name','')} resigned as {d.get('designation','')} w.e.f. {d.get('date','')}")

    return {
        "company_name":     company_name,
        "cin":              cin,
        "fy_start":         fy_start,
        "fy_end":           fy_end,
        "financial_summary": {
            "revenue_cr":   revenue_cr,
            "pbt_cr":       pbt_cr,
            "pat_cr":       pat_cr,
        },
        "directors":          directors,
        "director_changes":   director_changes,
        "report_sections":    report_sections,
        "mandatory_annexures": [
            "Annexure I — Extract of Annual Return (MGT-9)",
            "Annexure II — Secretarial Audit Report (MR-3) — if applicable",
            "Annexure III — Report on CSR activities — if applicable",
            "Annexure IV — Statement of particulars of employees — if applicable",
            "Annexure V — Related Party Transactions (Form AOC-2)",
        ],
        "filing_deadlines": {
            "AGM":    "Within 6 months from end of FY (30 Sep for 31 Mar FY)",
            "AOC-4":  "Within 30 days of AGM",
            "MGT-7":  "Within 60 days of AGM",
        },
        "ca_notes": [
            "Director's Report must be signed by at least 2 directors (one must be MD/WTD if applicable)",
            "Attach extract of Annual Return (MGT-9 or MGT-7A for small companies) as annexure",
            "For listed companies, additional SEBI LODR disclosures are mandatory",
            "Director's Report is part of Annual Report — file with AOC-4 with MCA",
            "Any qualification in Auditor's Report must have Board's explanation in Director's Report",
        ],
    }


def generate_startup_registration_guide(
    startup_name: str,
    entity_type: str = "private_limited",
    industry_sector: str = "",
    state: str = "Tamil Nadu",
    founders_count: int = 2,
    language: str = "en",
) -> dict:
    entity = _STARTUP_ENTITY_TYPES.get(entity_type, _STARTUP_ENTITY_TYPES["private_limited"])
    steps = _STARTUP_REGISTRATION_STEPS.get(entity_type, _STARTUP_REGISTRATION_STEPS["private_limited"])
    costs = _STARTUP_COSTS.get(entity_type, _STARTUP_COSTS["private_limited"])

    # DPIIT eligibility check
    dpiit_eligible = entity_type in ("private_limited", "llp", "opc")
    dpiit_criteria = [
        "Entity incorporated less than 10 years ago",
        "Annual turnover not exceeding ₹100 crore in any year",
        "Working towards innovation/improvement of product, process, or service",
        "Scalable business model with potential for high employment / wealth creation",
        "Not formed by splitting up or reconstructing existing business",
    ]

    # State-specific incentives
    state_incentives = {
        "Tamil Nadu":   ["TANSIM investment matching", "TIDCO startup space", "Power tariff concession"],
        "Karnataka":    ["Elevate programme grant up to ₹50L", "KBITS support", "T-Hub access"],
        "Maharashtra":  ["Maharashtra State Innovation Society grants", "SINE IIT-B incubation"],
        "Delhi":        ["Delhi Startup Policy 2023 benefits", "iStart Delhi support"],
        "Gujarat":      ["iCreate incubation", "GiZ support", "GUSEC programmes"],
    }.get(state, [f"Check {state} government startup policy for specific incentives"])

    total_time = "15–25 working days" if entity_type == "private_limited" else "10–18 working days"

    return {
        "startup_name":      startup_name,
        "entity_type":       entity_type,
        "entity_details":    entity,
        "industry_sector":   industry_sector,
        "state":             state,
        "founders_count":    founders_count,
        "registration_steps": steps,
        "total_estimated_time": total_time,
        "cost_estimate":     costs,
        "dpiit_eligible":    dpiit_eligible,
        "dpiit_criteria":    dpiit_criteria,
        "startup_india_benefits": _STARTUP_INDIA_BENEFITS,
        "annual_compliances": _STARTUP_COMPLIANCES["annual"],
        "monthly_compliances": _STARTUP_COMPLIANCES["monthly"],
        "state_incentives":  state_incentives,
        "documents_required": [
            "PAN card of all founders",
            "Aadhar card of all founders",
            "Passport-size photographs",
            "Address proof of registered office (rent agreement + NOC from owner OR utility bill)",
            "Latest bank statement / utility bill of founders (address proof)",
            "MOA & AOA draft (CA/CS will prepare)",
            "Digital Signature Certificate (DSC)",
        ],
        "ca_notes": [
            "Choose Pvt Ltd if you plan to raise VC/angel funding — LLPs cannot issue equity shares",
            "DPIIT recognition is FREE and unlocks Angel Tax exemption — apply within 3 months of incorporation",
            "File INC-20A within 180 days of incorporation to avoid ₹50,000+ penalty",
            "Register under MSME/Udyam — it's free and unlocks priority lending and govt tender access",
            f"Check {state} startup policy — many states offer free office space, seed grants, and mentorship",
        ],
    }


def generate_partnership_deed(
    firm_name: str,
    business_nature: str,
    registered_address: str,
    commencement_date: str,
    duration: str = "at_will",
    partners: list = None,
    profit_loss_ratio: str = "",
    bank_name: str = "",
    language: str = "en",
) -> dict:
    partners = partners or []
    state = registered_address.split(",")[-1].strip() if registered_address else "Maharashtra"
    stamp = _STAMP_DUTY_BY_STATE.get(state, _STAMP_DUTY_BY_STATE["default"])
    managing_partner = partners[0].get("name", "Partner 1") if partners else "designated partner"

    duration_clause = _DURATION_CLAUSES.get(duration, _DURATION_CLAUSES["at_will"])
    interest_rate = 12  # Section 40(b) limit

    # Build partner schedule
    partner_schedule = []
    for i, p in enumerate(partners):
        partner_schedule.append({
            "sl_no": i + 1,
            "name": p.get("name", f"Partner {i+1}"),
            "father_name": p.get("father_name", ""),
            "address": p.get("address", ""),
            "pan": p.get("pan", ""),
            "capital_contribution": p.get("capital", "As agreed"),
            "profit_share": p.get("profit_share", f"{100 // max(len(partners), 1)}%"),
            "designation": p.get("designation", "Partner"),
        })

    # Auto profit ratio if not given
    if not profit_loss_ratio and partners:
        shares = [p.get("profit_share", f"{100//len(partners)}%") for p in partners]
        profit_loss_ratio = " : ".join(s.replace("%","") for s in shares)

    # Build clauses
    filled_clauses = {}
    for key, template in _DEED_CLAUSES.items():
        filled = template.format(
            firm_name=firm_name, business_nature=business_nature,
            commencement_date=commencement_date, duration_clause=duration_clause,
            profit_loss_ratio=profit_loss_ratio, interest_rate=interest_rate,
            bank_name=bank_name or "as decided by partners",
            managing_partner=managing_partner, state=state,
        )
        filled_clauses[key] = filled

    # Registration checklist
    registration_checklist = [
        f"Execute deed on {stamp}",
        "All partners sign in presence of witnesses",
        "Get deed notarised",
        "Apply for firm registration at Registrar of Firms (optional but recommended)",
        "Apply for PAN for the firm (Form 49A)",
        "Open current account in firm's name",
        "Apply for GST registration if turnover exceeds threshold",
        "Obtain relevant trade/shop licences",
        "File partnership deed with Income Tax Dept if firm wants to claim 40(b) deductions",
    ]

    return {
        "firm_name": firm_name,
        "business_nature": business_nature,
        "registered_address": registered_address,
        "commencement_date": commencement_date,
        "duration": duration,
        "partner_count": len(partners),
        "partner_schedule": partner_schedule,
        "profit_loss_ratio": profit_loss_ratio,
        "clauses": filled_clauses,
        "stamp_duty": stamp,
        "registration_checklist": registration_checklist,
        "key_sections": [
            "Indian Partnership Act, 1932 — Sec 4 (Definition), Sec 58 (Registration)",
            "Income Tax Act, 1961 — Sec 40(b) (Partner salary/interest limits)",
            "GST Act — Firm treated as separate taxable person",
        ],
        "ca_notes": [
            "Register the firm even though optional — avoids disputes and enables legal action against debtors",
            "Specify exact remuneration figures in deed to claim 40(b) deduction",
            "Interest on capital cannot exceed 12% per annum as per Sec 40(b)",
            "Deed must be signed before commencement date for it to be effective from day 1",
            "All partners must have PAN; firm must apply for separate PAN",
        ],
    }


def generate_advance_tax(
    taxpayer_name: str,
    taxpayer_type: str,
    financial_year: str,
    estimated_income: float,
    tds_deducted: float = 0,
    regime: str = "new",
    business_income: float = 0,
    salary_income: float = 0,
    capital_gains_stcg: float = 0,
    capital_gains_ltcg: float = 0,
    other_income: float = 0,
    deductions_80c: float = 0,
    language: str = "en",
) -> dict:
    # Compute total if not given
    total_income = estimated_income or (business_income + salary_income + capital_gains_stcg + capital_gains_ltcg + other_income)

    # Tax on STCG at 15% (Section 111A), LTCG >1L at 10% (Section 112A)
    stcg_tax = capital_gains_stcg * 0.15
    ltcg_exempt = 100000
    ltcg_tax = max(0, capital_gains_ltcg - ltcg_exempt) * 0.10

    normal_income = total_income - capital_gains_stcg - capital_gains_ltcg

    if regime == "new":
        slabs = _ADV_TAX_NEW_SLABS
        std_deduction = 75000 if salary_income > 0 else 0
        taxable_normal = max(0, normal_income - std_deduction)
    else:
        slabs = _ADV_TAX_OLD_SLABS_IND
        taxable_normal = max(0, normal_income - min(deductions_80c, 150000) - (75000 if salary_income > 0 else 50000))

    normal_tax = _calc_tax_on_slabs(taxable_normal, slabs)

    # 87A Rebate (new regime: income ≤ 7L full rebate; old regime: income ≤ 5L rebate up to 12500)
    rebate = 0
    if regime == "new" and taxable_normal <= 700000:
        rebate = normal_tax
    elif regime == "old" and taxable_normal <= 500000:
        rebate = min(normal_tax, 12500)
    normal_tax = max(0, normal_tax - rebate)

    gross_tax = normal_tax + stcg_tax + ltcg_tax

    # Surcharge
    surcharge = 0
    if total_income > 50_00_000:
        surcharge = gross_tax * (0.15 if total_income <= 1_00_00_000 else 0.25)
    tax_before_cess = gross_tax + surcharge

    # Health & Education Cess 4%
    cess = tax_before_cess * 0.04
    total_tax = round(tax_before_cess + cess, 0)

    # Net advance tax after TDS
    net_advance_tax = max(0, total_tax - tds_deducted)

    # Threshold: advance tax only if liability > ₹10,000
    advance_tax_applicable = net_advance_tax > 10000

    # Installments
    installments = []
    paid_so_far = 0
    for inst in _ADV_TAX_INSTALLMENTS:
        cumulative_due = round(net_advance_tax * inst["cumulative_pct"] / 100, 0)
        installment_amount = max(0, cumulative_due - paid_so_far)
        paid_so_far = cumulative_due
        shortfall_interest = round(installment_amount * _INTEREST_RATE_PER_MONTH * 3, 0) if installment_amount > 0 else 0
        installments.append({
            "quarter": inst["quarter"],
            "due_date": inst["due_date"] + f" {financial_year.split('-')[0] if inst['quarter'] in ['Q1','Q2','Q3'] else '20' + financial_year.split('-')[1]}",
            "cumulative_percent": inst["cumulative_pct"],
            "cumulative_due": cumulative_due,
            "installment_amount": installment_amount,
            "section_234C_interest_if_missed": shortfall_interest,
        })

    fy_parts = financial_year.split("-")
    ay = f"20{fy_parts[1]}-{str(int('20'+fy_parts[1])+1)[2:]}" if len(fy_parts) == 2 else ""

    return {
        "taxpayer": taxpayer_name,
        "taxpayer_type": taxpayer_type,
        "financial_year": financial_year,
        "assessment_year": ay,
        "regime": regime,
        "income_summary": {
            "salary_income": salary_income,
            "business_income": business_income,
            "capital_gains_stcg": capital_gains_stcg,
            "capital_gains_ltcg": capital_gains_ltcg,
            "other_income": other_income,
            "total_income": total_income,
        },
        "tax_computation": {
            "normal_income_tax": round(normal_tax, 0),
            "stcg_tax_15pct": round(stcg_tax, 0),
            "ltcg_tax_10pct": round(ltcg_tax, 0),
            "surcharge": round(surcharge, 0),
            "cess_4pct": round(cess, 0),
            "total_tax_liability": total_tax,
            "tds_already_deducted": tds_deducted,
            "net_advance_tax_payable": net_advance_tax,
            "rebate_87a": round(rebate, 0),
        },
        "advance_tax_applicable": advance_tax_applicable,
        "advance_tax_not_applicable_reason": None if advance_tax_applicable else "Tax liability ≤ ₹10,000 — advance tax not required (Section 208)",
        "installments": installments,
        "payment_mode": "Challan ITNS 280 — online at tin.tin.nsdl.com or via net banking",
        "key_sections": ["Section 207 — Liability to pay advance tax", "Section 208 — ₹10,000 threshold", "Section 234B — Interest for non-payment", "Section 234C — Interest for deferred payment"],
        "tips": [
            f"Estimate income conservatively — you can revise upward in later quarters",
            "Include all freelance / side income — advance tax applies to ALL income",
            "TDS on salary is already being deducted — only shortfall needs advance payment",
            f"Missing {'Q1' if net_advance_tax > 0 else ''} installment attracts 1% per month interest u/s 234C",
        ],
    }


def _compute_tax_new_regime(taxable_income: float) -> dict:
    slabs = [(300000, 0), (300000, 0.05), (300000, 0.10), (300000, 0.15), (300000, 0.20), (float('inf'), 0.30)]
    tax = 0.0
    remaining = max(0, taxable_income)
    breakdown = []
    lower = 0
    for slab_size, rate in slabs:
        if remaining <= 0:
            break
        taxable_in_slab = min(remaining, slab_size)
        tax_in_slab = taxable_in_slab * rate
        if taxable_in_slab > 0:
            breakdown.append({"range": f"₹{lower:,.0f}–₹{lower + taxable_in_slab:,.0f}", "rate": f"{int(rate*100)}%", "tax": round(tax_in_slab)})
        tax += tax_in_slab
        remaining -= taxable_in_slab
        lower += slab_size
    # Rebate u/s 87A — if total income ≤ 7L, full tax rebate
    rebate = min(tax, 25000) if taxable_income <= 700000 else 0
    tax_after_rebate = max(0, tax - rebate)
    surcharge = 0
    if taxable_income > 5000000:
        surcharge = tax_after_rebate * 0.10
    if taxable_income > 10000000:
        surcharge = tax_after_rebate * 0.15
    cess = (tax_after_rebate + surcharge) * 0.04
    total = tax_after_rebate + surcharge + cess
    return {
        "slab_breakdown": breakdown,
        "gross_tax": round(tax),
        "rebate_87a": round(rebate),
        "tax_after_rebate": round(tax_after_rebate),
        "surcharge": round(surcharge),
        "health_edu_cess_4pct": round(cess),
        "total_tax_liability": round(total),
    }


def generate_form16(
    employee_name: str,
    employee_pan: str,
    employee_designation: str,
    employer_name: str,
    employer_tan: str,
    employer_pan: str,
    employer_address: str,
    financial_year: str,
    assessment_year: str,
    gross_salary: float,
    basic_salary: float,
    hra_received: float,
    hra_exemption: float,
    lta: float,
    other_allowances: float,
    standard_deduction: float,
    professional_tax: float,
    deduction_80c: float,
    deduction_80d: float,
    deduction_80ccd: float,
    other_deductions: float,
    tds_q1: float,
    tds_q2: float,
    tds_q3: float,
    tds_q4: float,
) -> dict:
    emp = employee_name or "Employee"
    fy = financial_year or "2024-25"
    ay = assessment_year or "2025-26"

    # Part A — TDS summary
    total_tds = tds_q1 + tds_q2 + tds_q3 + tds_q4
    part_a = {
        "title": "PART A — Details of Tax Deducted and Deposited in Central Government Account",
        "employer_name": employer_name or "Employer",
        "employer_tan": employer_tan or "—",
        "employer_pan": employer_pan or "—",
        "employer_address": employer_address or "—",
        "employee_name": emp,
        "employee_pan": employee_pan or "—",
        "financial_year": fy,
        "assessment_year": ay,
        "tds_quarters": [
            {"quarter": "Q1 (Apr–Jun)", "tds_deducted": round(tds_q1), "tds_deposited": round(tds_q1)},
            {"quarter": "Q2 (Jul–Sep)", "tds_deducted": round(tds_q2), "tds_deposited": round(tds_q2)},
            {"quarter": "Q3 (Oct–Dec)", "tds_deducted": round(tds_q3), "tds_deposited": round(tds_q3)},
            {"quarter": "Q4 (Jan–Mar)", "tds_deducted": round(tds_q4), "tds_deposited": round(tds_q4)},
        ],
        "total_tds_deducted": round(total_tds),
        "total_tds_deposited": round(total_tds),
    }

    # Part B — Income computation
    total_exemptions = hra_exemption + lta
    income_from_salary = gross_salary - total_exemptions - standard_deduction - professional_tax
    income_from_salary = max(0, income_from_salary)

    total_deductions_vi_a = deduction_80c + deduction_80d + deduction_80ccd + other_deductions
    total_deductions_vi_a = min(total_deductions_vi_a, 150000 + deduction_80d + deduction_80ccd + other_deductions)

    taxable_income = max(0, income_from_salary - total_deductions_vi_a)
    tax_computation = _compute_tax_new_regime(taxable_income)
    balance_tds = max(0, tax_computation["total_tax_liability"] - total_tds)
    excess_tds = max(0, total_tds - tax_computation["total_tax_liability"])

    part_b = {
        "title": "PART B — Details of Salary Paid and any other income and tax deducted",
        "salary_particulars": {
            "gross_salary": round(gross_salary),
            "allowances_exempt_u10": {
                "hra_exemption": round(hra_exemption),
                "lta": round(lta),
                "total_exemptions": round(total_exemptions),
            },
            "standard_deduction_16ia": round(standard_deduction) if standard_deduction else 50000,
            "professional_tax_16iii": round(professional_tax),
            "net_salary": round(income_from_salary),
        },
        "deductions_chapter_via": {
            "80c_investments": round(deduction_80c),
            "80d_medical_insurance": round(deduction_80d),
            "80ccd_nps": round(deduction_80ccd),
            "other_deductions": round(other_deductions),
            "total_deductions": round(total_deductions_vi_a),
            "note": "80C limit: ₹1,50,000. 80D: ₹25,000 (₹50,000 for senior citizens). 80CCD(1B): ₹50,000 additional NPS.",
        },
        "taxable_income": round(taxable_income),
        "tax_computation": tax_computation,
        "tax_relief": {"relief_89": 0, "note": "If salary arrears received, claim relief u/s 89 separately"},
        "tds_summary": {
            "total_tax_payable": tax_computation["total_tax_liability"],
            "total_tds_deducted": round(total_tds),
            "balance_tax_payable": round(balance_tds),
            "excess_tds_refundable": round(excess_tds),
            "status": "Balanced" if balance_tds == 0 and excess_tds == 0 else ("Refund due" if excess_tds > 0 else "Additional tax payable"),
        },
    }

    # Guidance
    notes = [
        f"File ITR-1 (salary only) or ITR-2 by 31 July {ay.split('-')[0]} to claim excess TDS refund.",
        "Keep Form 16 safe — needed for home loan applications, visa processing, and ITR filing.",
        "Cross-check TDS amounts with Form 26AS (https://www.incometax.gov.in) before filing ITR.",
        f"Standard deduction of ₹50,000 is auto-applied under new tax regime.",
        "If you have other income (rent, FD interest, capital gains), declare separately in ITR.",
    ]
    if balance_tds > 0:
        notes.append(f"⚠️ Additional tax of ₹{balance_tds:,.0f} is payable. Pay via Challan 280 before filing ITR.")
    if excess_tds > 0:
        notes.append(f"✅ Excess TDS of ₹{excess_tds:,.0f} is refundable. File ITR promptly to get the refund.")

    return {
        "action": "form_16",
        "financial_year": fy,
        "assessment_year": ay,
        "employee_name": emp,
        "part_a": part_a,
        "part_b": part_b,
        "employee_notes": notes,
        "itr_filing_guide": {
            "form_to_use": "ITR-1 (Sahaj) — for salary income only. ITR-2 if capital gains/foreign income.",
            "deadline": f"31 July {ay.split('-')[0]} (without penalty). 31 Dec {ay.split('-')[0]} (with ₹5,000 penalty).",
            "documents_needed": ["Form 16 (this document)", "Form 26AS", "AIS (Annual Information Statement)", "Bank statements", "Investment proofs for deductions"],
        },
    }


def generate_client_compliance_status(
    client_name: str,
    pan: str,
    gstin: str,
    business_type: str,
    filing_type: str,
    state: str,
    turnover_lakh: float,
    has_employees: bool,
    is_audit_case: bool,
    current_month: int,
    current_year: int,
) -> dict:
    import datetime
    today = datetime.date.today()
    month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    # Determine applicable filings
    filings = []

    # GST
    if gstin:
        if filing_type == "monthly":
            filings.append({
                "filing": "GSTR-1 (Monthly)",
                "due": f"11th of every month",
                "status": "pending" if today.day > 11 else "upcoming",
                "penalty": _COMPLIANCE_DEADLINES["gst_monthly"]["penalty"],
                "priority": "high",
            })
            filings.append({
                "filing": "GSTR-3B (Monthly)",
                "due": "20th of every month",
                "status": "pending" if today.day > 20 else "upcoming",
                "penalty": _COMPLIANCE_DEADLINES["gstr3b_monthly"]["penalty"],
                "priority": "high",
            })
        else:
            filings.append({
                "filing": "GSTR-1 (QRMP / Quarterly)",
                "due": "13th of Jan/Apr/Jul/Oct",
                "status": "upcoming",
                "penalty": _COMPLIANCE_DEADLINES["gst_quarterly"]["penalty"],
                "priority": "medium",
            })

    # TDS
    if has_employees or turnover_lakh > 10:
        filings.append({
            "filing": "TDS Challan Payment",
            "due": "7th of every month",
            "status": "pending" if today.day > 7 else "upcoming",
            "penalty": _COMPLIANCE_DEADLINES["tds_payment"]["penalty"],
            "priority": "high",
        })
        filings.append({
            "filing": "TDS Return (26Q/24Q)",
            "due": "31st of Jul/Oct/Jan/Apr",
            "status": "upcoming",
            "penalty": _COMPLIANCE_DEADLINES["tds_quarterly"]["penalty"],
            "priority": "medium",
        })

    # ITR
    itr_type = "itr_audit" if is_audit_case else ("itr_business" if business_type in ["pvt_ltd", "partnership", "llp"] else "itr_individual")
    filings.append({
        "filing": _COMPLIANCE_DEADLINES[itr_type]["return"],
        "due": f"31st {_COMPLIANCE_DEADLINES[itr_type].get('month', 'July')} {current_year}",
        "status": "upcoming" if current_month < 7 else ("due_soon" if current_month == 7 else "overdue"),
        "penalty": _COMPLIANCE_DEADLINES[itr_type]["penalty"],
        "priority": "critical",
    })

    # PT
    if state in ["Karnataka", "Maharashtra", "West Bengal", "Andhra Pradesh", "Telangana"]:
        filings.append({
            "filing": "Professional Tax (Employer)",
            "due": "15th of every month",
            "status": "pending" if today.day > 15 else "upcoming",
            "penalty": "State-specific penalty",
            "priority": "medium",
        })

    # ROC
    if business_type in ["pvt_ltd", "llp"]:
        filings.append({
            "filing": "ROC Annual Return (MGT-7 / AOC-4)",
            "due": f"Within 60 days of AGM (usually by Sep 30)",
            "status": "upcoming",
            "penalty": _COMPLIANCE_DEADLINES["roc_annual"]["penalty"],
            "priority": "medium",
        })

    # Risk flags
    risk_flags = []
    pending_count = sum(1 for f in filings if f["status"] in ["pending", "overdue"])
    if pending_count > 2:
        risk_flags.append(_RISK_FLAGS["nil_return_pending"])
    if is_audit_case and current_month >= 9:
        risk_flags.append(_RISK_FLAGS["audit_due"])

    # Health score (100 − penalty points)
    health = max(40, 100 - pending_count * 15)
    health_label = "Healthy" if health >= 80 else ("At Risk" if health >= 60 else "Critical")
    health_color = "green" if health >= 80 else ("yellow" if health >= 60 else "red")

    # Action items
    actions = [f for f in filings if f["status"] in ["pending", "overdue", "due_soon"]]

    return {
        "action": "client_compliance_status",
        "client_name": client_name or "Client",
        "pan": pan or "—",
        "gstin": gstin or "Not registered",
        "business_type": business_type,
        "state": state,
        "health_score": health,
        "health_label": health_label,
        "health_color": health_color,
        "filings": filings,
        "immediate_actions": actions,
        "risk_flags": risk_flags,
        "next_due": filings[0]["filing"] if filings else "None",
        "reminder_message": f"Dear {client_name}, your {actions[0]['filing'] if actions else 'compliance'} is due soon. Please share the required documents at the earliest to avoid penalties. — Your CA",
        "whatsapp_reminder": f"Hi {client_name}! 👋 Friendly reminder: *{actions[0]['filing'] if actions else 'Filing'}* is due. Please share docs ASAP to avoid penalty. Call us: [number]",
    }


def generate_salary_slip(
    employee_name: str,
    employee_id: str,
    designation: str,
    department: str,
    company_name: str,
    month_year: str,
    ctc_annual: float,
    basic_pct: float,
    hra_pct: float,
    city_tier: str,
    pf_applicable: bool,
    pt_state: str,
    bonus: float,
    advance_deduction: float,
    lop_days: int,
    working_days: int,
) -> dict:
    from datetime import datetime as _dt

    ctc   = float(ctc_annual) if ctc_annual else 600000.0
    bpct  = float(basic_pct) if basic_pct else 40.0
    hpct  = float(hra_pct) if hra_pct else 20.0
    wdays = int(working_days) if working_days else 26
    lop   = int(lop_days) if lop_days else 0
    bonus_amt = float(bonus) if bonus else 0.0
    advance   = float(advance_deduction) if advance_deduction else 0.0
    my = month_year or _dt.now().strftime("%B %Y")

    # Monthly CTC
    monthly_ctc = ctc / 12

    # Earnings
    basic       = round(monthly_ctc * bpct / 100, 2)
    hra         = round(monthly_ctc * hpct / 100, 2)
    ta          = round(monthly_ctc * 0.04, 2)   # 4% travel
    medical     = round(monthly_ctc * 0.04, 2)   # 4% medical
    special     = round(monthly_ctc - basic - hra - ta - medical, 2)
    gross       = round(basic + hra + ta + medical + special + bonus_amt, 2)

    # LOP adjustment
    lop_deduction = round((gross / wdays) * lop, 2) if lop > 0 else 0.0
    gross_after_lop = round(gross - lop_deduction, 2)

    # Deductions
    pf_emp  = round(min(basic, 15000) * 0.12, 2) if pf_applicable else 0.0
    pf_er   = round(min(basic, 15000) * 0.12, 2) if pf_applicable else 0.0  # employer share
    # ESI applicable if gross ≤ 21000
    esi_emp = round(gross_after_lop * 0.0075, 2) if gross_after_lop <= 21000 else 0.0
    esi_er  = round(gross_after_lop * 0.0325, 2) if gross_after_lop <= 21000 else 0.0

    # Professional Tax
    pt_slabs = _PT_SLABS.get(pt_state.lower().replace(" ", "_"), _PT_SLABS["none"])
    pt_amt = 0.0
    remaining = gross_after_lop
    for slab_max, slab_pt in pt_slabs:
        if remaining <= slab_max:
            pt_amt = slab_pt
            break

    # Estimated TDS (simplified — annual tax / 12)
    annual_taxable = max(0, (gross_after_lop * 12) - pf_emp * 12 - 50000)  # std deduction ₹50K
    # New tax regime slabs FY 2024-25
    if annual_taxable <= 300000:
        annual_tax = 0
    elif annual_taxable <= 600000:
        annual_tax = (annual_taxable - 300000) * 0.05
    elif annual_taxable <= 900000:
        annual_tax = 15000 + (annual_taxable - 600000) * 0.10
    elif annual_taxable <= 1200000:
        annual_tax = 45000 + (annual_taxable - 900000) * 0.15
    elif annual_taxable <= 1500000:
        annual_tax = 90000 + (annual_taxable - 1200000) * 0.20
    else:
        annual_tax = 150000 + (annual_taxable - 1500000) * 0.30
    # Rebate 87A if taxable ≤ 7L (new regime)
    if annual_taxable <= 700000:
        annual_tax = 0
    annual_tax_with_cess = round(annual_tax * 1.04, 2)
    tds_monthly = round(annual_tax_with_cess / 12, 2)

    total_deductions = round(pf_emp + esi_emp + pt_amt + tds_monthly + advance + lop_deduction, 2)
    net_pay = round(gross_after_lop - pf_emp - esi_emp - pt_amt - tds_monthly - advance, 2)

    # CTC reconciliation
    ctc_components = {
        "gross_salary":     round(gross, 2),
        "pf_employer":      pf_er,
        "esi_employer":     esi_er,
        "total_ctc_monthly": round(gross + pf_er + esi_er, 2),
        "total_ctc_annual":  round((gross + pf_er + esi_er) * 12, 2),
    }

    earnings = [
        {"component": "Basic Salary",                       "amount": basic},
        {"component": "House Rent Allowance (HRA)",         "amount": hra},
        {"component": "Travel Allowance",                   "amount": ta},
        {"component": "Medical Allowance",                  "amount": medical},
        {"component": "Special Allowance",                  "amount": max(0, special)},
    ]
    if bonus_amt:
        earnings.append({"component": "Bonus / Incentive", "amount": bonus_amt})

    deductions = []
    if pf_emp:      deductions.append({"component": "Provident Fund (Employee 12%)", "amount": pf_emp})
    if esi_emp:     deductions.append({"component": "ESI (Employee 0.75%)",          "amount": esi_emp})
    if pt_amt:      deductions.append({"component": "Professional Tax",              "amount": pt_amt})
    if tds_monthly: deductions.append({"component": "TDS (Income Tax)",              "amount": tds_monthly})
    if advance:     deductions.append({"component": "Advance Recovery",              "amount": advance})
    if lop_deduction: deductions.append({"component": f"Loss of Pay ({lop} days)",  "amount": lop_deduction})

    # Amount in words helper
    def _n2w(n):
        n = int(round(n))
        if n >= 100000: return f"Rupees {n//100000} Lakh {(n%100000)//1000} Thousand {n%1000} only"
        if n >= 1000:   return f"Rupees {n//1000} Thousand {n%1000} only"
        return f"Rupees {n} only"

    return {
        "action": "salary_slip",
        "employee": {
            "name": employee_name or "Employee",
            "id": employee_id or "EMP001",
            "designation": designation or "Software Engineer",
            "department": department or "Engineering",
        },
        "company_name": company_name or "Company Pvt. Ltd.",
        "month_year": my,
        "working_days_in_month": wdays,
        "days_worked": wdays - lop,
        "lop_days": lop,
        "earnings": earnings,
        "gross_salary": gross,
        "deductions": deductions,
        "total_deductions": total_deductions,
        "net_pay": net_pay,
        "net_pay_words": _n2w(net_pay),
        "ctc_breakdown": ctc_components,
        "tax_info": {
            "regime": "New Tax Regime (FY 2025-26)",
            "annual_taxable_income": annual_taxable,
            "annual_tax_before_cess": round(annual_tax, 2),
            "annual_tax_with_cess": annual_tax_with_cess,
            "monthly_tds": tds_monthly,
            "note": "TDS estimated under new tax regime. Consult CA for old regime or investment declarations.",
        },
        "employer_contributions": {
            "pf_employer": pf_er,
            "esi_employer": esi_er,
            "note": "Employer contributions are part of CTC but not shown in net pay.",
        },
        "compliance_notes": [
            "PF deducted on basic salary capped at ₹15,000 (statutory limit).",
            "ESI applicable only if gross salary ≤ ₹21,000/month.",
            f"Professional Tax as per {pt_state.title()} state rules.",
            "TDS computed under new tax regime (FY 2025-26) — assumes no deduction declarations.",
            "Issue salary slips by 7th of the following month as per Shops & Establishment Act.",
        ],
    }


def generate_itr_checklist(
    taxpayer_name: str,
    pan: str,
    assessment_year: str,
    income_sources: list,
    has_foreign_income: bool,
    has_crypto: bool,
    has_home_loan: bool,
    deductions: list,
    taxpayer_type: str,
) -> dict:
    name = taxpayer_name or "Taxpayer"
    ay   = assessment_year or "2025-26"

    # Determine recommended ITR form
    sources_set = tuple(sorted(set(income_sources)))
    itr_form = _ITR_FORM_SELECTOR.get(sources_set, "ITR-2 or ITR-3 (consult CA)")
    if has_foreign_income:
        itr_form = "ITR-2 (mandatory for foreign income/assets)"
    if "business" in income_sources:
        itr_form = "ITR-3 or ITR-4 (Sugam if opting for presumptive scheme)"
    if taxpayer_type == "company":
        itr_form = "ITR-6"

    # Build income document checklist
    income_checklist = []
    for src in (income_sources or ["salary"]):
        src_info = _INCOME_SOURCE_DOCS.get(src)
        if src_info:
            income_checklist.append({
                "category": src_info["label"],
                "schedule": src_info["itr_schedule"],
                "documents": [{"doc": d, "collected": False} for d in src_info["documents"]],
            })

    # Special additions
    if has_foreign_income:
        income_checklist.append({
            "category": "Foreign Income / Assets",
            "schedule": "Schedule FA / Schedule FSI",
            "documents": [
                {"doc": "Foreign bank account statements", "collected": False},
                {"doc": "Foreign income proof (salary slip / dividend statement)", "collected": False},
                {"doc": "DTAA (Double Tax Avoidance Agreement) details", "collected": False},
                {"doc": "Form 67 (if claiming foreign tax credit)", "collected": False},
            ],
        })

    if has_crypto:
        income_checklist.append({
            "category": "Virtual Digital Assets (Crypto / NFT)",
            "schedule": "Schedule VDA",
            "documents": [
                {"doc": "Exchange P&L report / trade history (CoinDCX, WazirX, Binance, etc.)", "collected": False},
                {"doc": "Purchase price and date of each crypto asset", "collected": False},
                {"doc": "TDS certificate (Form 26AS — 1% TDS under Sec 194S)", "collected": False},
                {"doc": "Wallet transfer statements if moved between wallets", "collected": False},
            ],
        })

    # Deduction checklist
    deduction_checklist = []
    deduct_list = deductions if deductions else []
    if has_home_loan and "home_loan_interest" not in deduct_list:
        deduct_list.append("home_loan_interest")

    for ded in deduct_list:
        ded_info = _DEDUCTION_DOCS.get(ded)
        if ded_info:
            deduction_checklist.append({
                "section": ded_info["label"],
                "documents": [{"doc": d, "collected": False} for d in ded_info["items"]],
            })

    # Deadline
    deadline = _DEADLINES["audit_required"] if "business" in income_sources else _DEADLINES["non_audit_individual"]
    if taxpayer_type == "company":
        deadline = _DEADLINES["company"]

    # Key reminders
    reminders = [
        f"File by {deadline} to avoid penalty under Sec 234F (₹5,000 / ₹1,000 for income ≤ ₹5L)",
        "Download AIS and Form 26AS before filing — reconcile with your records",
        "Pre-validate bank account on IT portal for faster refund",
        "Link Aadhaar with PAN if not done — mandatory for filing",
        "Check Form 26AS for any TDS mismatch before filing",
    ]
    if has_crypto:
        reminders.append("Crypto gains taxed at flat 30% + 4% cess — no deductions allowed (Sec 115BBH)")
    if "capital_gains" in income_sources:
        reminders.append("LTCG above ₹1.25L on equity/mutual funds taxed at 12.5% from FY 2024-25 Budget changes")

    return {
        "action": "itr_checklist",
        "taxpayer_name": name,
        "pan": pan,
        "assessment_year": ay,
        "recommended_itr_form": itr_form,
        "filing_deadline": deadline,
        "common_documents": [{"doc": d, "collected": False} for d in _COMMON_DOCS],
        "income_checklist": income_checklist,
        "deduction_checklist": deduction_checklist,
        "key_reminders": reminders,
        "total_document_count": len(_COMMON_DOCS) + sum(len(c["documents"]) for c in income_checklist) + sum(len(d["documents"]) for d in deduction_checklist),
        "portal_link": "https://www.incometax.gov.in/iec/foportal/",
        "form_26as_link": "https://www.incometax.gov.in (Login → e-file → Income Tax Returns → View Form 26AS)",
    }


def generate_depreciation_calc(
    asset_name: str,
    asset_category: str,
    cost: float,
    purchase_date: str,
    useful_life_years: int,
    salvage_value: float,
    method: str,
    financial_year_start: int,
) -> dict:
    from datetime import date as _date

    cat      = _ASSET_CATEGORIES.get(asset_category, _ASSET_CATEGORIES["plant_machinery"])
    cost     = float(cost) if cost else 100000.0
    salvage  = float(salvage_value) if salvage_value else 0.0
    life     = int(useful_life_years) if useful_life_years else cat["companies_act_life"]
    fy_start = int(financial_year_start) if financial_year_start else 2024

    # Parse purchase date
    try:
        pd = _date.fromisoformat(purchase_date) if purchase_date else _date(fy_start, 4, 1)
    except Exception:
        pd = _date(fy_start, 4, 1)

    # Determine if asset was used < 180 days in purchase FY (for IT Act WDV)
    fy_end = _date(fy_start + 1, 3, 31)
    days_in_fy = (fy_end - pd).days + 1
    half_rate = days_in_fy < 180

    schedule = []

    if method == "slm":
        annual_dep = (cost - salvage) / life if life > 0 else (cost - salvage)
        dep_rate   = (annual_dep / cost * 100) if cost > 0 else 0
        wdv = cost
        for yr in range(life):
            fy_label = f"FY {fy_start + yr}-{str(fy_start + yr + 1)[-2:]}"
            dep = annual_dep if yr > 0 else (annual_dep * 0.5 if half_rate else annual_dep)
            dep = min(dep, max(0, wdv - salvage))
            wdv = wdv - dep
            schedule.append({
                "year": yr + 1,
                "fy": fy_label,
                "opening_wdv": round(wdv + dep, 2),
                "depreciation": round(dep, 2),
                "closing_wdv": round(wdv, 2),
                "accumulated_dep": round(cost - wdv, 2),
            })

    elif method == "wdv":
        it_rate = cat["it_rate_wdv"] / 100
        wdv = cost
        # Run for IT Act useful life (until WDV < 5% of cost)
        yr = 0
        while wdv > cost * 0.05 and yr < 40:
            fy_label = f"FY {fy_start + yr}-{str(fy_start + yr + 1)[-2:]}"
            rate = (it_rate * 0.5) if (yr == 0 and half_rate) else it_rate
            dep = wdv * rate
            dep = min(dep, max(0, wdv - salvage))
            wdv = wdv - dep
            yr += 1
            schedule.append({
                "year": yr,
                "fy": fy_label,
                "opening_wdv": round(wdv + dep, 2),
                "depreciation": round(dep, 2),
                "closing_wdv": round(wdv, 2),
                "accumulated_dep": round(cost - wdv, 2),
            })

    else:  # double_declining
        rate = (2 / life) if life > 0 else 0.4
        wdv = cost
        for yr in range(life):
            fy_label = f"FY {fy_start + yr}-{str(fy_start + yr + 1)[-2:]}"
            dep = wdv * rate
            dep = min(dep, max(0, wdv - salvage))
            wdv = wdv - dep
            schedule.append({
                "year": yr + 1,
                "fy": fy_label,
                "opening_wdv": round(wdv + dep, 2),
                "depreciation": round(dep, 2),
                "closing_wdv": round(wdv, 2),
                "accumulated_dep": round(cost - wdv, 2),
            })

    total_dep = sum(s["depreciation"] for s in schedule)

    summary = {
        "asset_name": asset_name or "Asset",
        "asset_category": cat["label"],
        "cost": round(cost, 2),
        "salvage_value": round(salvage, 2),
        "depreciable_amount": round(cost - salvage, 2),
        "method": method.upper(),
        "useful_life_years": life,
        "purchase_date": str(pd),
        "half_rate_first_year": half_rate,
        "it_act_rate_wdv": f"{cat['it_rate_wdv']}%",
        "companies_act_slm_rate": f"{cat['companies_act_slm']}%",
        "companies_act_useful_life": f"{cat['companies_act_life']} years",
        "total_depreciation": round(total_dep, 2),
        "final_book_value": round(cost - total_dep, 2),
    }

    # Comparison: show both SLM and WDV year-1 for context
    slm_y1 = (cost - salvage) / life if life > 0 else 0
    wdv_y1 = cost * (cat["it_rate_wdv"] / 100)
    comparison = {
        "slm_year1": round(slm_y1, 2),
        "wdv_year1": round(wdv_y1, 2),
        "wdv_it_rate": cat["it_rate_wdv"],
        "recommendation": "WDV gives higher deduction in early years — better for tax saving. SLM gives equal deduction — better for stable P&L.",
    }

    return {
        "action": "depreciation_calc",
        "summary": summary,
        "schedule": schedule,
        "method_notes": _DEPRECIATION_NOTES.get(method, _DEPRECIATION_NOTES["slm"]),
        "comparison": comparison,
        "journal_entry": {
            "debit": "Depreciation A/c",
            "credit": "Accumulated Depreciation A/c",
            "note": "At year end, transfer to P&L: Debit P&L A/c, Credit Depreciation A/c",
        },
        "compliance_notes": [
            "Schedule II of Companies Act 2013 mandates SLM or WDV for financial statements.",
            "Income Tax Act Section 32 allows WDV at prescribed rates for tax deduction.",
            "Both methods can be used simultaneously — one for books, one for tax.",
            f"IT Act WDV rate for {cat['label']}: {cat['it_rate_wdv']}%",
            f"Companies Act useful life for {cat['label']}: {cat['companies_act_life']} years",
        ],
    }


def generate_gst_invoice(
    seller_name: str,
    seller_gstin: str,
    seller_address: str,
    seller_state: str,
    buyer_name: str,
    buyer_gstin: str,
    buyer_address: str,
    buyer_state: str,
    invoice_number: str,
    invoice_date: str,
    items: list,
    reverse_charge: bool = False,
    payment_terms: str = "30_days",
    notes: str = "",
) -> dict:
    from datetime import date as _date
    today      = _date.today()
    inv_num    = invoice_number  or f"INV/{today.year}-{str(today.year+1)[2:]}/{str(today.month).zfill(2)}/001"
    inv_date   = invoice_date    or today.strftime("%d-%m-%Y")
    seller     = seller_name     or "Your Business Name"
    s_gstin    = seller_gstin    or "29XXXXX0000X0XX"
    s_state    = _INDIAN_STATES.get(seller_state, seller_state.title())
    buyer      = buyer_name      or "Customer Name"
    b_gstin    = buyer_gstin     or ""
    b_state    = _INDIAN_STATES.get(buyer_state, buyer_state.title())
    is_igst    = seller_state.lower() != buyer_state.lower()  # interstate = IGST

    # Use demo items if none provided
    if not items:
        items = [
            {"description": "Professional consulting services", "hsn_sac": "998314", "qty": 10, "unit": "Hours", "rate": 2000, "gst_pct": 18},
            {"description": "Project management fee", "hsn_sac": "998312", "qty": 1, "unit": "Lump Sum", "rate": 15000, "gst_pct": 18},
        ]

    # Calculate line items
    line_items = []
    subtotal = 0.0
    total_gst = 0.0

    for item in items:
        desc    = item.get("description", "Item")
        hsn     = item.get("hsn_sac", "9983")
        qty     = float(item.get("qty", 1))
        unit    = item.get("unit", "Nos")
        rate    = float(item.get("rate", 0))
        gst_pct = float(item.get("gst_pct", 18))

        taxable = round(qty * rate, 2)
        gst_amt = round(taxable * gst_pct / 100, 2)
        total   = round(taxable + gst_amt, 2)
        subtotal   += taxable
        total_gst  += gst_amt

        if is_igst:
            tax_breakdown = {"igst_pct": gst_pct, "igst_amt": gst_amt, "cgst_pct": 0, "cgst_amt": 0, "sgst_pct": 0, "sgst_amt": 0}
        else:
            half = gst_pct / 2
            tax_breakdown = {"igst_pct": 0, "igst_amt": 0, "cgst_pct": half, "cgst_amt": round(gst_amt/2, 2), "sgst_pct": half, "sgst_amt": round(gst_amt/2, 2)}

        line_items.append({
            "description": desc, "hsn_sac": hsn, "qty": qty, "unit": unit,
            "rate": rate, "taxable_value": taxable, "gst_pct": gst_pct,
            **tax_breakdown, "total": total,
        })

    subtotal    = round(subtotal, 2)
    total_gst   = round(total_gst, 2)
    grand_total = round(subtotal + total_gst, 2)

    # Tax summary
    if is_igst:
        tax_summary = [{"type": "IGST", "taxable": subtotal, "rate": "", "amount": total_gst}]
    else:
        cgst = round(total_gst / 2, 2)
        sgst = round(total_gst / 2, 2)
        tax_summary = [
            {"type": "CGST", "taxable": subtotal, "rate": "", "amount": cgst},
            {"type": f"SGST ({s_state})", "taxable": subtotal, "rate": "", "amount": sgst},
        ]

    # Amount in words (simple)
    rupees = int(grand_total)
    paise  = round((grand_total - rupees) * 100)

    def _num_to_words(n: int) -> str:
        ones = ["","One","Two","Three","Four","Five","Six","Seven","Eight","Nine",
                "Ten","Eleven","Twelve","Thirteen","Fourteen","Fifteen","Sixteen",
                "Seventeen","Eighteen","Nineteen"]
        tens = ["","","Twenty","Thirty","Forty","Fifty","Sixty","Seventy","Eighty","Ninety"]
        if n == 0: return "Zero"
        if n < 20: return ones[n]
        if n < 100: return tens[n//10] + (" " + ones[n%10] if n%10 else "")
        if n < 1000: return ones[n//100] + " Hundred" + (" " + _num_to_words(n%100) if n%100 else "")
        if n < 100000: return _num_to_words(n//1000) + " Thousand" + (" " + _num_to_words(n%1000) if n%1000 else "")
        if n < 10000000: return _num_to_words(n//100000) + " Lakh" + (" " + _num_to_words(n%100000) if n%100000 else "")
        return _num_to_words(n//10000000) + " Crore" + (" " + _num_to_words(n%10000000) if n%10000000 else "")

    amount_words = _num_to_words(rupees) + " Rupees"
    if paise: amount_words += f" and {_num_to_words(paise)} Paise"
    amount_words += " Only"

    pt_label = _PAYMENT_TERMS_MAP.get(payment_terms, payment_terms)

    return {
        "action":         "gst_invoice",
        "invoice_number": inv_num,
        "invoice_date":   inv_date,
        "supply_type":    "Inter-State (IGST)" if is_igst else f"Intra-State (CGST + SGST — {s_state})",
        "reverse_charge": "Yes" if reverse_charge else "No",
        "seller": {
            "name": seller, "gstin": s_gstin,
            "address": seller_address or "[Seller Address]", "state": s_state,
        },
        "buyer": {
            "name": buyer, "gstin": b_gstin or "Unregistered / Consumer",
            "address": buyer_address or "[Buyer Address]", "state": b_state,
        },
        "line_items":      line_items,
        "subtotal":        subtotal,
        "total_gst":       total_gst,
        "grand_total":     grand_total,
        "amount_in_words": amount_words,
        "tax_summary":     tax_summary,
        "payment_terms":   pt_label,
        "notes":           notes or _GST_INVOICE_NOTES[0],
        "compliance_flags": [
            f"{'IGST' if is_igst else 'CGST+SGST'} applicable — {'Inter' if is_igst else 'Intra'}-state supply",
            "Reverse Charge: Yes — buyer to pay GST directly" if reverse_charge else "Reverse Charge: No",
            "E-way bill mandatory if goods value > ₹50,000 and distance > 50 km" if any(i.get("qty", 1) > 0 for i in items) else "",
            f"GSTIN of buyer {'verified' if b_gstin else 'not provided — ITC cannot be claimed by buyer'}",
        ],
        "hsn_sac_reference": {k: v for k, v in _COMMON_HSN_SAC.items() if k in [i.get("hsn_sac","") for i in items]},
    }


def generate_client_proposal(
    firm_name: str,
    client_name: str,
    client_industry: str,
    client_turnover: str,
    services: list,
    fee_type: str,
    engagement_start: str,
    ca_name: str,
) -> dict:
    import datetime
    firm = firm_name or "Sharma & Associates, Chartered Accountants"
    client = client_name or "ABC Pvt Ltd"
    industry = client_industry or "manufacturing"
    turnover = client_turnover or "₹5 Cr – ₹10 Cr"
    ca = ca_name or "CA Rajesh Sharma"
    today = datetime.date.today()
    start = engagement_start or f"1st {today.strftime('%B %Y')}" if today.day > 15 else f"1st {today.strftime('%B %Y')}"

    selected_services = services if services else ["bookkeeping", "gst_filing", "tds_compliance", "income_tax"]

    scope_items = []
    deliverables_all = []
    monthly_fee = 0
    annual_fee = 0
    one_time_fee = 0

    for svc_key in selected_services:
        if svc_key not in _CA_SERVICES:
            continue
        svc = _CA_SERVICES[svc_key]
        low, high = svc["typical_fee"]
        mid = (low + high) // 2
        scope_items.append({
            "service": svc["label"],
            "key": svc_key,
            "deliverables": svc["deliverables"],
            "fee": mid,
            "unit": svc["unit"],
            "fee_range": f"₹{low:,} – ₹{high:,} {svc['unit']}",
        })
        deliverables_all.extend(svc["deliverables"])
        if svc["unit"] == "per month":
            monthly_fee += mid
        elif svc["unit"] == "per year":
            annual_fee += mid
        else:
            one_time_fee += mid

    total_monthly = monthly_fee
    total_annual = annual_fee + (monthly_fee * 12)
    total_with_gst_monthly = round(monthly_fee * 1.18)
    total_with_gst_annual = round(total_annual * 1.18)

    scope_text = "\n".join([f"  {i+1}. {s['service']}" for i, s in enumerate(scope_items)])
    if fee_type == "monthly_retainer":
        fee_text = f"  Monthly Retainer: ₹{total_monthly:,} + GST 18% = ₹{total_with_gst_monthly:,} per month\n  Annual Value: ₹{total_with_gst_annual:,} (incl. GST)"
    else:
        fee_text = f"  Annual Fee: ₹{total_annual:,} + GST 18% = ₹{total_with_gst_annual:,} per year"

    engagement_letter = _ENGAGEMENT_LETTER_TEMPLATE.format(
        date=today.strftime("%d %B %Y"),
        firm_name=firm,
        client_name=client,
        client_contact=f"The Management, {client}",
        start_date=start,
        scope_text=scope_text,
        fee_text=fee_text,
        ca_name=ca,
    )

    timeline = [
        {"week": "Week 1", "milestone": "Engagement kick-off meeting + document collection", "owner": "Both parties"},
        {"week": "Week 2", "milestone": "Data onboarding, accounting software setup, opening balance verification", "owner": firm},
        {"week": "Week 3", "milestone": "First deliverable: GST/TDS working for current month", "owner": firm},
        {"week": "Week 4", "milestone": "Review meeting — confirm processes, flag gaps, align on workflows", "owner": "Both parties"},
        {"week": "Month 2", "milestone": "Full cadence established — all recurring services running", "owner": firm},
    ]

    value_propositions = [
        f"Dedicated CA with {industry} sector experience — not a junior executive",
        "UDIN-enabled deliverables — every certificate is verifiable by your stakeholders",
        "Proactive compliance alerts — you won't miss a deadline again",
        "Direct partner access — call/WhatsApp CA directly, not a helpdesk",
        f"Fixed monthly fee, no surprise bills — budgetable professional cost for {client}",
        "Digital-first practice — cloud accounting, e-signatures, online dashboards",
    ]

    document_checklist = [
        "Company PAN and TAN card",
        "GST Registration Certificate",
        "MOA/AOA + Certificate of Incorporation",
        "Last 3 years ITR and financial statements",
        "Bank statements (all accounts, last 12 months)",
        "Previous auditor's reports (if any)",
        "Tally/accounting data backup or access",
        "All contracts, agreements, and vendor MSAs",
        "Payroll data and employee list",
        "Fixed asset register",
    ]

    proposal_content = {
        "executive_summary": f"{firm} is pleased to present this proposal to {client} for professional accounting and compliance services. With expertise in the {industry} sector and a client base of {industry}-focused businesses with turnover ranging from ₹1 Cr to ₹50 Cr, we bring deep domain knowledge to your specific compliance needs. Our engagement will ensure {client} remains fully compliant, with clean books and proactive tax planning.",
        "scope_of_work": scope_items,
        "fee_schedule": {
            "monthly_fee": monthly_fee,
            "annual_fee": annual_fee,
            "one_time_fee": one_time_fee,
            "total_monthly_ex_gst": monthly_fee,
            "total_monthly_incl_gst": total_with_gst_monthly,
            "total_annual_incl_gst": total_with_gst_annual,
            "fee_type": fee_type,
        },
        "timeline": timeline,
        "value_propositions": value_propositions,
        "document_checklist": document_checklist,
        "total_deliverables": len(deliverables_all),
    }

    return {
        "action":              "client_proposal",
        "firm_name":           firm,
        "client_name":         client,
        "client_industry":     industry,
        "ca_name":             ca,
        "engagement_start":    start,
        "services_selected":   [_CA_SERVICES[k]["label"] for k in selected_services if k in _CA_SERVICES],
        "proposal_content":    proposal_content,
        "engagement_letter":   engagement_letter,
        "scope_items":         scope_items,
        "fee_summary": {
            "monthly_retainer_excl_gst": monthly_fee,
            "monthly_retainer_incl_gst": total_with_gst_monthly,
            "annual_value_incl_gst":     total_with_gst_annual,
        },
        "document_checklist":  document_checklist,
        "summary":             f"Proposal for {client} ({industry}) — {len(scope_items)} services. Monthly retainer: ₹{total_with_gst_monthly:,}/month incl GST. Annual value: ₹{total_with_gst_annual:,}.",
    }


# ── TDS Compliance Tracker (Round 14) ────────────────────────────────────────

_TDS_SECTIONS = {
    "192":  {"nature": "Salary",                      "rate_default": 0,    "threshold": 250000, "form": "24Q", "due_govt": 7, "due_others": 7,  "quarterly_return": "Q4 due 31 May"},
    "192A": {"nature": "EPF Premature Withdrawal",    "rate_default": 10,   "threshold": 50000,  "form": "26Q", "due_govt": 7, "due_others": 7,  "quarterly_return": "Q4 due 31 May"},
    "193":  {"nature": "Interest on Securities",      "rate_default": 10,   "threshold": 10000,  "form": "26Q", "due_govt": 7, "due_others": 7,  "quarterly_return": "Quarterly"},
    "194":  {"nature": "Dividend",                    "rate_default": 10,   "threshold": 5000,   "form": "26Q", "due_govt": 7, "due_others": 7,  "quarterly_return": "Quarterly"},
    "194A": {"nature": "Interest (Non-Bank)",         "rate_default": 10,   "threshold": 5000,   "form": "26Q", "due_govt": 7, "due_others": 7,  "quarterly_return": "Quarterly"},
    "194B": {"nature": "Winnings Lottery/Game",       "rate_default": 30,   "threshold": 10000,  "form": "26Q", "due_govt": 7, "due_others": 7,  "quarterly_return": "Quarterly"},
    "194C": {"nature": "Contractor/Sub-contractor",   "rate_default": 1,    "threshold": 30000,  "form": "26Q", "due_govt": 7, "due_others": 7,  "quarterly_return": "Quarterly"},
    "194D": {"nature": "Insurance Commission",        "rate_default": 5,    "threshold": 15000,  "form": "26Q", "due_govt": 7, "due_others": 7,  "quarterly_return": "Quarterly"},
    "194G": {"nature": "Commission on Lottery",       "rate_default": 5,    "threshold": 15000,  "form": "26Q", "due_govt": 7, "due_others": 7,  "quarterly_return": "Quarterly"},
    "194H": {"nature": "Commission/Brokerage",        "rate_default": 5,    "threshold": 15000,  "form": "26Q", "due_govt": 7, "due_others": 7,  "quarterly_return": "Quarterly"},
    "194I": {"nature": "Rent (P&M, Land, Building)",  "rate_default": 10,   "threshold": 240000, "form": "26Q", "due_govt": 7, "due_others": 7,  "quarterly_return": "Quarterly"},
    "194IA":{"nature": "Purchase of Immovable Property","rate_default": 1,  "threshold": 5000000,"form": "26QB","due_govt": 30,"due_others": 30, "quarterly_return": "Per transaction"},
    "194IB":{"nature": "Rent by Individual/HUF >50K/month","rate_default": 5,"threshold":600000, "form": "26QC","due_govt": 30,"due_others": 30, "quarterly_return": "Yearly March"},
    "194J": {"nature": "Professional/Technical Fees", "rate_default": 10,   "threshold": 30000,  "form": "26Q", "due_govt": 7, "due_others": 7,  "quarterly_return": "Quarterly"},
    "194JA":{"nature": "Technical Services (reduced)", "rate_default": 2,   "threshold": 30000,  "form": "26Q", "due_govt": 7, "due_others": 7,  "quarterly_return": "Quarterly"},
    "194N": {"nature": "Cash Withdrawal >1Cr",        "rate_default": 2,    "threshold": 10000000,"form":"26Q", "due_govt": 7, "due_others": 7,  "quarterly_return": "Quarterly"},
    "194Q": {"nature": "Purchase of Goods >50L",      "rate_default": 0.1,  "threshold": 5000000,"form": "26Q", "due_govt": 7, "due_others": 7,  "quarterly_return": "Quarterly"},
    "195":  {"nature": "Payment to Non-Resident",     "rate_default": 20,   "threshold": 0,      "form": "27Q", "due_govt": 7, "due_others": 7,  "quarterly_return": "Quarterly"},
}

_MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"]

_TDS_CALENDAR = {
    1:  {"due_7th": "Jan 7 — TDS for Dec deductions",  "due_15th": "Jan 15 — Q3 return (26Q/27Q/24Q)",        "due_31st": None},
    2:  {"due_7th": "Feb 7 — TDS for Jan deductions",  "due_15th": "Feb 15 — Q3 certificates (Form 16A)",     "due_31st": None},
    3:  {"due_7th": "Mar 7 — TDS for Feb deductions",  "due_15th": None,                                       "due_31st": "Mar 31 — FY closes, ensure all TDS deposited"},
    4:  {"due_7th": "Apr 7 — TDS for Mar (non-Govt)",  "due_15th": None,                                       "due_31st": "Apr 30 — TDS for March (Govt deductors): 7th Apr"}  ,
    5:  {"due_7th": "May 7 — TDS for Apr deductions",  "due_15th": "May 15 — Q4 return (26Q/27Q/24Q)",        "due_31st": "May 31 — Form 16/16A for Q4 FY"},
    6:  {"due_7th": "Jun 7 — TDS for May deductions",  "due_15th": "Jun 15 — Q4 certificates (Form 16A)",     "due_31st": None},
    7:  {"due_7th": "Jul 7 — TDS for Jun deductions",  "due_15th": "Jul 15 — Q1 return (26Q/27Q/24Q)",        "due_31st": "Jul 31 — Q1 TDS certificate (Form 16A)"},
    8:  {"due_7th": "Aug 7 — TDS for Jul deductions",  "due_15th": "Aug 15 — Q1 certificates (Form 16A)",     "due_31st": None},
    9:  {"due_7th": "Sep 7 — TDS for Aug deductions",  "due_15th": "Sep 15 — Advance Tax 2nd instalment (45%)","due_31st": None},
    10: {"due_7th": "Oct 7 — TDS for Sep deductions",  "due_15th": "Oct 15 — Q2 return (26Q/27Q/24Q)",        "due_31st": "Oct 31 — Q2 TDS certificate (Form 16A)"},
    11: {"due_7th": "Nov 7 — TDS for Oct deductions",  "due_15th": "Nov 15 — Q2 certificates (Form 16A)",     "due_31st": None},
    12: {"due_7th": "Dec 7 — TDS for Nov deductions",  "due_15th": "Dec 15 — Advance Tax 3rd instalment (75%)","due_31st": None},
}

_LATE_PAYMENT_INTEREST_PCT = 1.5   # per month u/s 201(1A)
_LATE_DEDUCTION_INTEREST_PCT = 1.0  # per month u/s 201(1A)
_PENALTY_PER_DAY = 200              # u/s 234E late filing fee
_MAX_PENALTY_PCT = 100              # penalty cannot exceed TDS amount


def generate_tds_compliance_tracker(
    company_name: str,
    month: int,
    year: int,
    deductions: list,
    pan_verified: bool,
) -> dict:
    import datetime
    company = company_name or "Your Company"
    today = datetime.date.today()
    m = month if 1 <= month <= 12 else today.month
    y = year if year >= 2020 else today.year
    month_name = _MONTHS[m - 1]

    demo_deductions = deductions if deductions else [
        {"section": "194J", "payee": "Consulting Firm XYZ",     "amount": 150000, "tds_deducted": 15000, "date": f"{y}-{m:02d}-05", "pan": "ABCDE1234F", "deposited": False},
        {"section": "194C", "payee": "Transport Contractor ABC", "amount": 200000, "tds_deducted": 2000,  "date": f"{y}-{m:02d}-10", "pan": "XYZAB5678G", "deposited": True},
        {"section": "194I", "payee": "Office Landlord Sharma",  "amount": 80000,  "tds_deducted": 8000,  "date": f"{y}-{m:02d}-01", "pan": "LMNOP9012H", "deposited": False},
        {"section": "192",  "payee": "Salary — All Employees",  "amount": 800000, "tds_deducted": 42000, "date": f"{y}-{m:02d}-28", "pan": "MULTIPLE",   "deposited": True},
        {"section": "194Q", "payee": "Vendor Purchase >50L",    "amount": 600000, "tds_deducted": 600,   "date": f"{y}-{m:02d}-15", "pan": "PQRST3456I", "deposited": False},
    ]

    # Challan due date (7th of following month for non-govt)
    if m == 12:
        due_month, due_year = 1, y + 1
    else:
        due_month, due_year = m + 1, y
    challan_due = datetime.date(due_year, due_month, 7)
    days_to_due = (challan_due - today).days

    processed = []
    total_tds = 0
    total_deposited = 0
    total_pending = 0

    for d in demo_deductions:
        sec = d.get("section", "194J")
        sec_info = _TDS_SECTIONS.get(sec, _TDS_SECTIONS["194J"])
        amt = float(d.get("amount", 0))
        tds = float(d.get("tds_deducted", 0))
        deposited = bool(d.get("deposited", False))
        pan = d.get("pan", "")

        # Verify PAN — higher rate if PAN not furnished
        pan_issue = pan_verified and (not pan or pan == "MULTIPLE" or len(pan) != 10)
        effective_rate = 20.0 if (pan_issue and sec not in ("192",)) else sec_info["rate_default"]

        # Late fee calculation (simplified — days overdue * 200, max = TDS amount)
        overdue_days = max(0, (today - challan_due).days) if not deposited else 0
        late_fee = min(overdue_days * _PENALTY_PER_DAY, tds) if overdue_days > 0 else 0
        late_interest = round(tds * _LATE_PAYMENT_INTEREST_PCT / 100 * max(1, overdue_days // 30), 2) if overdue_days > 0 else 0

        total_tds += tds
        if deposited:
            total_deposited += tds
        else:
            total_pending += tds

        processed.append({
            "section":         sec,
            "nature":          sec_info["nature"],
            "payee":           d.get("payee", ""),
            "amount":          amt,
            "tds_amount":      tds,
            "rate":            effective_rate,
            "pan":             pan,
            "pan_issue":       pan_issue,
            "deposited":       deposited,
            "form":            sec_info["form"],
            "date":            d.get("date", ""),
            "overdue_days":    overdue_days,
            "late_fee_234E":   late_fee,
            "late_interest_201": late_interest,
            "total_liability": round(tds + late_fee + late_interest, 2),
            "status":          "deposited" if deposited else ("overdue" if overdue_days > 0 else "pending"),
        })

    # Monthly calendar
    cal = _TDS_CALENDAR.get(m, {})
    deadlines = [v for v in cal.values() if v]

    # Return filing calendar
    quarter = (m - 1) // 3 + 1
    quarter_months = {1: "Apr-Jun", 2: "Jul-Sep", 3: "Oct-Dec", 4: "Jan-Mar"}
    quarter_due = {1: "Jul 15", 2: "Oct 15", 3: "Jan 15", 4: "May 15"}

    # Form 26Q/24Q checklist
    filing_checklist = [
        {"task": "Collect all invoices/vouchers with TDS deducted", "done": False, "mandatory": True},
        {"task": "Verify PAN of all deductees — missing PAN attracts 20% TDS", "done": False, "mandatory": True},
        {"task": f"Deposit TDS challan via NSDL/TRACES before {challan_due.strftime('%d %b %Y')}", "done": total_pending == 0, "mandatory": True},
        {"task": f"File {sec_info['form']} quarterly return by {quarter_due[quarter]}", "done": False, "mandatory": True},
        {"task": "Issue Form 16A to deductees within 15 days of return filing", "done": False, "mandatory": True},
        {"task": "Reconcile Form 26AS with books for all parties", "done": False, "mandatory": True},
        {"task": "Check for short deduction / short deposit notices in TRACES", "done": False, "mandatory": False},
        {"task": "Update deductee master with any PAN corrections", "done": False, "mandatory": False},
    ]

    common_errors = [
        "PAN not updated — default 20% TDS applies and deductee can't claim credit",
        "Depositing TDS under wrong section code — mismatch in Form 26AS",
        "Not deducting TDS on part-payments (TDS applies when credit or payment, whichever earlier)",
        "Ignoring 194Q threshold — tracks cumulative purchases from same vendor in FY",
        "Not filing nil returns when no deductions made — attracts late filing fee",
        "Issuing Form 16A late — deductee can't file ITR properly without it",
    ]

    return {
        "action":              "tds_compliance_tracker",
        "company":             company,
        "month":               month_name,
        "year":                y,
        "challan_due_date":    challan_due.strftime("%d %b %Y"),
        "days_to_due":         days_to_due,
        "due_status":          "overdue" if days_to_due < 0 else ("urgent" if days_to_due <= 3 else "on_track"),
        "total_tds_deducted":  round(total_tds, 2),
        "total_deposited":     round(total_deposited, 2),
        "total_pending":       round(total_pending, 2),
        "total_late_fee":      round(sum(d["late_fee_234E"] for d in processed), 2),
        "total_late_interest": round(sum(d["late_interest_201"] for d in processed), 2),
        "deductions":          processed,
        "month_deadlines":     deadlines,
        "quarter":             f"Q{quarter} ({quarter_months[quarter]})",
        "return_due":          quarter_due[quarter],
        "return_form":         "24Q (salary) + 26Q (non-salary) + 27Q (NR payments)",
        "filing_checklist":    filing_checklist,
        "common_errors":       common_errors,
        "sections_reference":  {k: {"nature": v["nature"], "rate": v["rate_default"], "threshold": v["threshold"], "form": v["form"]} for k, v in _TDS_SECTIONS.items()},
        "summary":             f"{company} — {month_name} {y} TDS. Total: ₹{total_tds/100000:.1f}L | Deposited: ₹{total_deposited/100000:.1f}L | Pending: ₹{total_pending/100000:.1f}L. Challan due {challan_due.strftime('%d %b')}.",
    }


def calculate_msme_loan_eligibility(
    company_name: str,
    business_type: str,
    annual_turnover: float,
    plant_machinery_value: float,
    years_in_business: int,
    loan_purpose: str,
    loan_amount_requested: float,
    existing_loans: float,
    monthly_revenue: float,
    gst_registered: bool,
) -> dict:
    company = company_name or "Your Company"
    btype = business_type if business_type in _MSME_CATEGORIES else "service"
    purpose_key = loan_purpose if loan_purpose in _LOAN_SCHEMES else "working_capital"

    # Determine MSME category
    cats = _MSME_CATEGORIES[btype]
    msme_category = "not_eligible"
    for cat in ["micro", "small", "medium"]:
        if annual_turnover <= cats[cat]["turnover"] and plant_machinery_value <= cats[cat]["investment"]:
            msme_category = cat
            break

    # Eligibility scoring
    score = 0
    score_details = []

    if msme_category != "not_eligible":
        score += 25
        score_details.append({"factor": "MSME Classification", "status": "pass", "points": 25, "note": f"Classified as {msme_category.title()} Enterprise"})
    else:
        score_details.append({"factor": "MSME Classification", "status": "fail", "points": 0, "note": "Turnover or investment exceeds MSME limits"})

    if gst_registered:
        score += 20
        score_details.append({"factor": "GST Registration", "status": "pass", "points": 20, "note": "GST registration verified"})
    else:
        score_details.append({"factor": "GST Registration", "status": "warn", "points": 0, "note": "Not GST registered — limits eligibility for bank loans and PSB 59-min scheme"})

    if years_in_business >= 3:
        score += 20
        score_details.append({"factor": "Business Vintage", "status": "pass", "points": 20, "note": f"{years_in_business} years — meets 3-year minimum for most schemes"})
    elif years_in_business >= 1:
        score += 10
        score_details.append({"factor": "Business Vintage", "status": "warn", "points": 10, "note": f"{years_in_business} year(s) — eligible for MUDRA but not SIDBI/SMILE"})
    else:
        score_details.append({"factor": "Business Vintage", "status": "fail", "points": 0, "note": "Less than 1 year — very limited options (startup schemes only)"})

    # DSCR (Debt Service Coverage Ratio)
    annual_revenue = monthly_revenue * 12 if monthly_revenue else annual_turnover
    if loan_amount_requested > 0 and annual_revenue > 0:
        assumed_emi = (loan_amount_requested * 0.01)  # rough 1% monthly EMI estimate
        annual_debt_service = (assumed_emi * 12) + (existing_loans * 0.15)
        net_income_estimate = annual_revenue * 0.15  # assume 15% net margin
        dscr = net_income_estimate / max(annual_debt_service, 1)
        if dscr >= 1.5:
            score += 20
            score_details.append({"factor": "DSCR", "status": "pass", "points": 20, "note": f"Est. DSCR {dscr:.2f} — strong repayment capacity"})
        elif dscr >= 1.0:
            score += 10
            score_details.append({"factor": "DSCR", "status": "warn", "points": 10, "note": f"Est. DSCR {dscr:.2f} — marginal. Banks prefer 1.5+"})
        else:
            score_details.append({"factor": "DSCR", "status": "fail", "points": 0, "note": f"Est. DSCR {dscr:.2f} — repayment risk. Reduce loan amount or increase revenue"})
    else:
        dscr = 0
        score += 10
        score_details.append({"factor": "DSCR", "status": "info", "points": 10, "note": "Provide monthly revenue and loan amount for DSCR calculation"})

    # Loan amount vs turnover sanity
    if loan_amount_requested > 0 and annual_turnover > 0:
        loan_to_turnover = loan_amount_requested / annual_turnover
        if loan_to_turnover <= 0.25:
            score += 15
            score_details.append({"factor": "Loan-to-Turnover Ratio", "status": "pass", "points": 15, "note": f"{loan_to_turnover*100:.0f}% of turnover — conservative ask"})
        elif loan_to_turnover <= 0.5:
            score += 8
            score_details.append({"factor": "Loan-to-Turnover Ratio", "status": "warn", "points": 8, "note": f"{loan_to_turnover*100:.0f}% of turnover — acceptable but at the limit"})
        else:
            score_details.append({"factor": "Loan-to-Turnover Ratio", "status": "fail", "points": 0, "note": f"{loan_to_turnover*100:.0f}% of turnover — too high. Banks typically lend up to 25-50% of annual turnover"})
    else:
        score += 0
        score_details.append({"factor": "Loan-to-Turnover Ratio", "status": "info", "points": 0, "note": "Provide loan amount and turnover for ratio analysis"})

    # Eligibility verdict
    if score >= 70:
        verdict = "Strong"
        verdict_color = "green"
        verdict_msg = "You have strong loan eligibility. Multiple schemes available at competitive rates."
    elif score >= 45:
        verdict = "Moderate"
        verdict_color = "yellow"
        verdict_msg = "Moderate eligibility. Some gaps to address — see recommendations below."
    else:
        verdict = "Weak"
        verdict_color = "red"
        verdict_msg = "Several eligibility gaps found. Address these before applying to avoid rejection which impacts CIBIL."

    scheme_cfg = _LOAN_SCHEMES[purpose_key]
    applicable_subsidies = _GOVERNMENT_SUBSIDIES[:]
    if not gst_registered:
        applicable_subsidies = [s for s in applicable_subsidies if "PSB" not in s["name"]]

    # Document checklist
    docs_checklist = [
        {"doc": "Udyam Registration Certificate", "mandatory": True, "note": "Register free at udyamregistration.gov.in"},
        {"doc": "GST Registration + 12 months GSTR returns", "mandatory": gst_registered, "note": "Banks use GSTR data to verify turnover"},
        {"doc": "3 years ITR + P&L + Balance Sheet (CA certified)", "mandatory": years_in_business >= 3, "note": "Audited statements required for loans > ₹25L"},
        {"doc": "6 months bank statements (all accounts)", "mandatory": True, "note": "Must show consistent cash flow"},
        {"doc": "KYC — Aadhaar, PAN (promoter + business)", "mandatory": True, "note": "Both promoter and business PAN needed"},
        {"doc": "Business proof (GST cert / Shop Act / MCA registration)", "mandatory": True, "note": "Any one is sufficient"},
        {"doc": "Property documents (if offering collateral)", "mandatory": False, "note": "Optional under CGTMSE scheme — skip if going collateral-free"},
        {"doc": "Projected financials (for new or young businesses)", "mandatory": years_in_business < 3, "note": "CA-certified 3-year projections required"},
    ]

    recommendations = []
    for sd in score_details:
        if sd["status"] in ("fail", "warn"):
            if "GST" in sd["factor"]:
                recommendations.append("Register for GST immediately at gst.gov.in — unlocks PSB 59-min loan, SIDBI, and most bank schemes.")
            elif "Vintage" in sd["factor"]:
                recommendations.append("While under 3 years, focus on MUDRA Kishor (up to ₹50L) and CGTMSE-covered loans via local banks.")
            elif "DSCR" in sd["factor"]:
                recommendations.append("Reduce loan amount requested OR show higher revenue via GSTR/bank statements to improve repayment capacity ratio.")
            elif "Turnover" in sd["factor"]:
                recommendations.append(f"Reduce loan request to ≤25% of annual turnover (≤₹{annual_turnover*0.25/1e5:.0f}L) for easier approval.")

    def fmt_cr(amt):
        if amt >= 1e7:
            return f"₹{amt/1e7:.1f} Cr"
        return f"₹{amt/1e5:.0f}L"

    return {
        "action":              "msme_loan_eligibility",
        "company":             company,
        "msme_category":       msme_category,
        "business_type":       btype,
        "eligibility_score":   score,
        "eligibility_max":     100,
        "verdict":             verdict,
        "verdict_color":       verdict_color,
        "verdict_message":     verdict_msg,
        "score_breakdown":     score_details,
        "annual_turnover_fmt": fmt_cr(annual_turnover) if annual_turnover else "Not provided",
        "loan_requested_fmt":  fmt_cr(loan_amount_requested) if loan_amount_requested else "Not provided",
        "recommended_schemes": scheme_cfg["schemes"],
        "max_without_collateral": fmt_cr(scheme_cfg["max_without_collateral"]),
        "interest_range":      scheme_cfg["interest_range"],
        "tenure":              scheme_cfg["tenure"],
        "government_subsidies": applicable_subsidies,
        "document_checklist":  docs_checklist,
        "recommendations":     recommendations,
        "dscr_estimate":       round(dscr, 2) if dscr else None,
        "summary":             f"{company} — {msme_category.title()} Enterprise. Eligibility score {score}/100 ({verdict}). {len(applicable_subsidies)} schemes applicable.",
    }


def generate_pl_statement(
    company_name: str,
    period: str,
    revenue_items: list,
    cogs_items: list,
    opex_items: list,
    other_income: float,
    tax_rate: float,
    industry: str,
    prev_period_revenue: float,
    prev_period_profit: float,
) -> dict:
    company = company_name or "Your Company"
    per = period or "FY 2024-25"

    if not revenue_items:
        revenue_items = [
            {"name": "Product Sales",   "amount": 3500000},
            {"name": "Service Revenue", "amount": 1200000},
            {"name": "Subscription",    "amount": 800000},
        ]
    if not cogs_items:
        cogs_items = [
            {"name": "Raw Materials / Inventory", "amount": 1400000},
            {"name": "Direct Labour",              "amount": 420000},
            {"name": "Packaging & Delivery",       "amount": 180000},
        ]
    if not opex_items:
        opex_items = [
            {"name": "Salaries & Benefits",  "amount": 900000},
            {"name": "Rent & Utilities",     "amount": 240000},
            {"name": "Marketing & Ads",      "amount": 300000},
            {"name": "Software & Tech",      "amount": 120000},
            {"name": "Admin & Legal",        "amount": 80000},
            {"name": "Depreciation",         "amount": 60000},
        ]

    total_revenue = sum(float(r.get("amount", 0)) for r in revenue_items)
    total_cogs    = sum(float(c.get("amount", 0)) for c in cogs_items)
    gross_profit  = total_revenue - total_cogs
    gross_margin  = (gross_profit / total_revenue * 100) if total_revenue else 0

    depn_items    = [o for o in opex_items if "depreciation" in o.get("name", "").lower() or "amort" in o.get("name", "").lower()]
    depn_total    = sum(float(d.get("amount", 0)) for d in depn_items)
    total_opex    = sum(float(o.get("amount", 0)) for o in opex_items)
    ebitda        = gross_profit - (total_opex - depn_total)
    ebit          = gross_profit - total_opex
    ebitda_margin = (ebitda / total_revenue * 100) if total_revenue else 0

    pbt           = ebit + other_income
    tax_amount    = max(0, pbt * (tax_rate / 100))
    pat           = pbt - tax_amount
    net_margin    = (pat / total_revenue * 100) if total_revenue else 0

    bench = _INDUSTRY_BENCHMARKS.get(industry.lower() if industry else "general", _INDUSTRY_BENCHMARKS["general"])

    def vs_bench(actual: float, bench_val: float, label: str) -> dict:
        diff = actual - bench_val
        status = "above" if diff >= 0 else "below"
        color  = "#22c55e" if diff >= 0 else "#ef4444"
        return {"label": label, "actual": round(actual, 1), "benchmark": bench_val, "diff": round(diff, 1), "status": status, "color": color}

    benchmarks = [
        vs_bench(gross_margin,  bench["gross_margin"],  "Gross Margin %"),
        vs_bench(ebitda_margin, bench["ebitda_margin"], "EBITDA Margin %"),
        vs_bench(net_margin,    bench["net_margin"],    "Net Margin %"),
    ]

    yoy_revenue_growth = ((total_revenue - prev_period_revenue) / prev_period_revenue * 100) if prev_period_revenue else None
    yoy_profit_growth  = ((pat - prev_period_profit) / abs(prev_period_profit) * 100) if prev_period_profit else None

    insights = []
    if gross_margin < bench["gross_margin"] - 5:
        insights.append(f"Gross margin ({gross_margin:.1f}%) is {bench['gross_margin'] - gross_margin:.1f}pp below {industry} benchmark — review supplier costs or pricing.")
    if ebitda_margin < bench["ebitda_margin"] - 3:
        biggest_opex = max(opex_items, key=lambda x: float(x.get("amount", 0)), default={})
        insights.append(f"EBITDA margin below benchmark. Largest opex line: {biggest_opex.get('name','Salaries')} (₹{float(biggest_opex.get('amount',0))/100000:.1f}L) — review for optimisation.")
    if net_margin > bench["net_margin"] + 3:
        insights.append(f"Net margin ({net_margin:.1f}%) is ahead of industry benchmark — strong position. Consider reinvesting surplus in growth.")
    if total_cogs / total_revenue > 0.6:
        insights.append("COGS exceeds 60% of revenue — high cost of delivery. Explore automation or renegotiation of supplier terms.")
    if not insights:
        insights.append(f"P&L is broadly healthy. Focus on maintaining gross margin above {bench['gross_margin']}% as you scale.")
    if yoy_revenue_growth is not None:
        if yoy_revenue_growth > 20:
            insights.append(f"Revenue grew {yoy_revenue_growth:.1f}% YoY — strong growth trajectory. Ensure opex scales sub-linearly to protect margins.")
        elif yoy_revenue_growth < 5:
            insights.append(f"Revenue growth of {yoy_revenue_growth:.1f}% YoY is below inflation — review pricing strategy and new revenue streams.")

    cr = lambda x: f"₹{x/10000000:.2f} Cr" if x >= 10000000 else f"₹{x/100000:.1f}L"

    return {
        "action":           "pl_statement",
        "company":          company,
        "period":           per,
        "industry":         industry or "general",
        "revenue": {
            "items":        [{"name": r["name"], "amount": float(r["amount"])} for r in revenue_items],
            "total":        round(total_revenue, 0),
            "formatted":    cr(total_revenue),
        },
        "cogs": {
            "items":        [{"name": c["name"], "amount": float(c["amount"])} for c in cogs_items],
            "total":        round(total_cogs, 0),
            "formatted":    cr(total_cogs),
        },
        "gross_profit":     round(gross_profit, 0),
        "gross_profit_fmt": cr(gross_profit),
        "gross_margin_pct": round(gross_margin, 1),
        "opex": {
            "items":        [{"name": o["name"], "amount": float(o["amount"])} for o in opex_items],
            "total":        round(total_opex, 0),
            "formatted":    cr(total_opex),
        },
        "ebitda":           round(ebitda, 0),
        "ebitda_fmt":       cr(ebitda),
        "ebitda_margin":    round(ebitda_margin, 1),
        "ebit":             round(ebit, 0),
        "other_income":     round(other_income, 0),
        "pbt":              round(pbt, 0),
        "tax_amount":       round(tax_amount, 0),
        "tax_rate":         tax_rate,
        "pat":              round(pat, 0),
        "pat_fmt":          cr(pat),
        "net_margin_pct":   round(net_margin, 1),
        "yoy_revenue_growth": round(yoy_revenue_growth, 1) if yoy_revenue_growth is not None else None,
        "yoy_profit_growth":  round(yoy_profit_growth, 1) if yoy_profit_growth is not None else None,
        "benchmark_comparison": benchmarks,
        "insights":         insights,
        "summary": f"{company} {per}: Revenue {cr(total_revenue)} | Gross {gross_margin:.0f}% | EBITDA {ebitda_margin:.0f}% | PAT {cr(pat)} ({net_margin:.1f}%)",
    }


# ── Overdue Invoice Collector (Round 11) ─────────────────────────────────────

def generate_overdue_collection(
    company_name: str,
    invoices: list,
    contact_name: str,
    sender_name: str,
    payment_terms: str,
    late_fee_pct: float,
) -> dict:
    company = company_name or "Your Company"
    contact = contact_name or "Sir/Madam"
    sender = sender_name or f"{company} Finance Team"
    terms = payment_terms or "Net 30"

    if not invoices:
        invoices = [
            {"invoice_no": "INV-2024-101", "amount": 85000, "due_date": "2024-11-15", "days_overdue": 45, "client": "ABC Enterprises"},
            {"invoice_no": "INV-2024-118", "amount": 42500, "due_date": "2024-11-28", "days_overdue": 32, "client": "XYZ Trading Co"},
            {"invoice_no": "INV-2024-135", "amount": 125000, "due_date": "2024-12-05", "days_overdue": 15, "client": "PQR Solutions"},
        ]

    total_overdue = sum(float(inv.get("amount", 0)) for inv in invoices)
    late_fee_total = total_overdue * (late_fee_pct / 100)

    processed = []
    for inv in invoices:
        days = int(inv.get("days_overdue", 0))
        amount = float(inv.get("amount", 0))
        late_fee = amount * (late_fee_pct / 100)

        if days <= 15:
            stage = "gentle"
            urgency = "low"
        elif days <= 30:
            stage = "firm"
            urgency = "medium"
        elif days <= 60:
            stage = "strong"
            urgency = "high"
        else:
            stage = "legal"
            urgency = "critical"

        client = inv.get("client", contact)
        inv_no = inv.get("invoice_no", "INV-XXX")
        due_date = inv.get("due_date", "")

        if stage == "gentle":
            subject = f"Friendly Reminder — Invoice {inv_no} Payment Due"
            body = f"""Dear {client},

I hope this message finds you well.

This is a friendly reminder that Invoice {inv_no} for ₹{amount:,.0f} was due on {due_date} and appears to be outstanding on our records.

We understand that sometimes payments slip through the cracks — if you have already initiated the transfer, please disregard this note and share the UTR/reference number at your convenience.

Invoice Details:
• Invoice No: {inv_no}
• Amount: ₹{amount:,.0f}
• Due Date: {due_date}
• Days Overdue: {days} days

Kindly arrange payment at the earliest. Our bank details are on the invoice. Feel free to reach out if you have any questions.

Warm regards,
{sender}"""

        elif stage == "firm":
            subject = f"Payment Overdue — Invoice {inv_no} | Action Required"
            body = f"""Dear {client},

We are writing to bring to your attention that Invoice {inv_no} for ₹{amount:,.0f} is now {days} days overdue (original due date: {due_date}).

Despite our earlier reminder, we have not received payment or any communication regarding this invoice. We request you to please clear this immediately.

Invoice Details:
• Invoice No: {inv_no}
• Amount Due: ₹{amount:,.0f}
• Original Due Date: {due_date}
• Days Overdue: {days} days
• Late Fee Applicable: ₹{late_fee:,.0f} ({late_fee_pct}% per month as per our terms)

To avoid late fees, please process payment by [DATE+3 DAYS] and share confirmation.

If there is a dispute or issue with this invoice, please let us know immediately so we can resolve it together.

Regards,
{sender}"""

        elif stage == "strong":
            subject = f"URGENT: Invoice {inv_no} — {days} Days Overdue | ₹{amount:,.0f} Outstanding"
            body = f"""Dear {client},

This is our third and final reminder regarding Invoice {inv_no} for ₹{amount:,.0f}, which is now {days} days past due.

We have a strong business relationship with you and wish to resolve this amicably. However, the continued non-payment is affecting our cash flow and we need this resolved immediately.

Outstanding Amount Summary:
• Principal: ₹{amount:,.0f}
• Late Fee ({late_fee_pct}%/month): ₹{late_fee:,.0f}
• TOTAL NOW DUE: ₹{amount + late_fee:,.0f}

If payment is not received by [DATE+7 DAYS], we will be left with no option but to escalate this matter, which may include:
1. Suspension of future services/deliveries
2. Referral to our legal team for recovery proceedings
3. Reporting to credit bureaus (if applicable)

We sincerely hope it does not come to this. Please arrange payment or call us at [PHONE] today.

{sender}"""

        else:
            subject = f"LEGAL NOTICE — Invoice {inv_no} | {days} Days Overdue | ₹{amount + late_fee:,.0f} Due"
            body = f"""Dear {client},

NOTICE OF OVERDUE PAYMENT AND INTENTION TO INITIATE LEGAL PROCEEDINGS

This notice is served upon you in the matter of Invoice {inv_no} dated [INVOICE DATE] for ₹{amount:,.0f}, which has remained unpaid for {days} days despite multiple reminders.

Demand Details:
• Principal Amount: ₹{amount:,.0f}
• Late Fee Accrued: ₹{late_fee:,.0f}
• Total Amount in Demand: ₹{amount + late_fee:,.0f}

Under the terms of our agreement ({terms}), you are in breach of your payment obligation. Under Section 138 of the Negotiable Instruments Act and the MSME Delayed Payments Act (if applicable), we are entitled to recover the outstanding amount along with interest at 1.5x the bank rate.

You are hereby given 7 (SEVEN) days from the date of this notice to settle the full amount. Failure to do so will result in:
1. Filing a complaint under Section 138 NI Act
2. Initiation of arbitration/civil suit for recovery
3. Reporting to credit rating agencies

To avoid legal action, transfer the amount immediately and send proof to [EMAIL].

This notice is issued without prejudice to all other rights and remedies available to {company}.

{sender}
[Designation], {company}
[Date]

Note: Consult your CA/lawyer before sending the Legal Notice stage. This draft is a starting template."""

        processed.append({
            "invoice_no":    inv_no,
            "client":        client,
            "amount":        amount,
            "late_fee":      round(late_fee, 0),
            "total_due":     round(amount + late_fee, 0),
            "due_date":      due_date,
            "days_overdue":  days,
            "stage":         stage,
            "urgency":       urgency,
            "subject":       subject,
            "email_body":    body,
        })

    processed.sort(key=lambda x: x["days_overdue"], reverse=True)

    tips = [
        "Always CC your CA on the Legal Notice stage — it adds credibility and protects you legally.",
        "Under the MSME Act, buyers must pay within 45 days; you can file a complaint with MSME Samadhaan portal.",
        "Call the client 24h after sending the email — a voice conversation often unblocks payment faster than email.",
        "Consider offering a payment plan if the client is genuinely struggling — a part-payment is better than bad debt.",
        f"Your late fee clause ({late_fee_pct}% per month) should be on every invoice and in your service agreement to be enforceable.",
    ]

    return {
        "action":          "overdue_collector",
        "company":         company,
        "total_invoices":  len(processed),
        "total_overdue":   round(total_overdue, 0),
        "total_late_fees": round(late_fee_total, 0),
        "total_recoverable": round(total_overdue + late_fee_total, 0),
        "invoices":        processed,
        "collection_tips": tips,
        "urgency_count":   {
            "critical": sum(1 for i in processed if i["urgency"] == "critical"),
            "high":     sum(1 for i in processed if i["urgency"] == "high"),
            "medium":   sum(1 for i in processed if i["urgency"] == "medium"),
            "low":      sum(1 for i in processed if i["urgency"] == "low"),
        },
        "summary": f"Generated {len(processed)} collection emails. Total overdue: ₹{total_overdue/100000:.1f}L + ₹{late_fee_total/100000:.1f}L late fees = ₹{(total_overdue+late_fee_total)/100000:.1f}L recoverable.",
    }
