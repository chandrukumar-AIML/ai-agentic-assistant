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

    return {"error": f"Unknown CA action: {action}"}
