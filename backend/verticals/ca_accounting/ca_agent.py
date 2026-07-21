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
