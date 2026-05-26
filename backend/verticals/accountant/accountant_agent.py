# backend/verticals/accountant/accountant_agent.py
"""
AI Accountant Assistant (Feature 17) — India-specific.

Capabilities:
  1. GSTIN validation (already in form_agent) + GST rate lookup by HSN code
  2. GST calculation: CGST + SGST (intra-state) or IGST (inter-state)
  3. TDS calculation: Section 194C, 194J, 194I, 194H
  4. GSTR-1 export: monthly outward supply summary (JSON → Excel)
  5. GSTR-3B export: monthly summary return (JSON → Excel)
  6. Invoice generation (PDF via output_generator)
  7. HSN code lookup and description
  8. Financial year helper (India FY: April–March)

Compliance:
  - All amounts in INR
  - GST rates from official CGST schedule (simplified subset)
  - TDS rates per Finance Act 2024
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


# ── Indian Financial Year helpers ─────────────────────────────────────────────

def get_india_fy(d: Optional[date] = None) -> str:
    """Return Indian Financial Year string for a date, e.g. '2024-25'."""
    d = d or date.today()
    if d.month >= 4:
        return f"{d.year}-{str(d.year + 1)[2:]}"
    return f"{d.year - 1}-{str(d.year)[2:]}"


def get_tax_period(d: Optional[date] = None) -> str:
    """Return GSTR period string, e.g. '032025' for March 2025."""
    d = d or date.today()
    return f"{d.month:02d}{d.year}"


# ── HSN code database (sample — most common in India) ────────────────────────

_HSN_CODES: dict[str, dict] = {
    "0101":   {"desc": "Live horses, asses, mules",                "gst_rate": 0.0},
    "0901":   {"desc": "Coffee",                                    "gst_rate": 5.0},
    "1001":   {"desc": "Wheat and meslin",                         "gst_rate": 0.0},
    "2201":   {"desc": "Waters, mineral waters",                   "gst_rate": 18.0},
    "3004":   {"desc": "Medicaments",                              "gst_rate": 12.0},
    "4901":   {"desc": "Printed books",                            "gst_rate": 0.0},
    "5208":   {"desc": "Woven fabrics of cotton",                  "gst_rate": 5.0},
    "6101":   {"desc": "Men's overcoats, windcheaters",            "gst_rate": 12.0},
    "8471":   {"desc": "Computers, laptops",                       "gst_rate": 18.0},
    "8517":   {"desc": "Telephone sets, smartphones",             "gst_rate": 18.0},
    "8703":   {"desc": "Motor cars",                               "gst_rate": 28.0},
    "9983":   {"desc": "IT services, software",                    "gst_rate": 18.0},
    "9985":   {"desc": "Support services",                         "gst_rate": 18.0},
    "9954":   {"desc": "Construction services",                    "gst_rate": 12.0},
    "9961":   {"desc": "Retail trade services",                    "gst_rate": 18.0},
    "9971":   {"desc": "Financial and related services",           "gst_rate": 18.0},
    "9972":   {"desc": "Real estate services",                     "gst_rate": 18.0},
    "9992":   {"desc": "Education services",                       "gst_rate": 0.0},
    "9993":   {"desc": "Human health and social care services",    "gst_rate": 0.0},
    "9994":   {"desc": "Sewage and waste collection services",     "gst_rate": 18.0},
    "9995":   {"desc": "Services of membership organisations",    "gst_rate": 18.0},
    "9997":   {"desc": "Other services",                           "gst_rate": 18.0},
    "997331": {"desc": "Licensing of software",                    "gst_rate": 18.0},
    "997212": {"desc": "Rental of office premises",               "gst_rate": 18.0},
}

# Standard GST rates
_GST_RATES = {0.0, 0.1, 0.25, 1.0, 1.5, 3.0, 5.0, 6.0, 7.5, 9.0, 12.0, 14.0, 18.0, 28.0}


def lookup_hsn(hsn_code: str) -> dict:
    """Look up HSN/SAC code description and GST rate."""
    code = hsn_code.strip()
    if code in _HSN_CODES:
        return {"hsn": code, **_HSN_CODES[code], "found": True}
    # Try prefix match (4-digit HSN)
    prefix = code[:4]
    if prefix in _HSN_CODES:
        return {"hsn": code, **_HSN_CODES[prefix], "found": True, "matched_prefix": prefix}
    return {"hsn": code, "found": False, "desc": "HSN code not in local database", "gst_rate": 18.0}


# ── GST calculation ───────────────────────────────────────────────────────────

def calculate_gst(
    base_amount:  float,
    gst_rate:     float,
    transaction:  str = "intra",   # "intra" (CGST+SGST) or "inter" (IGST)
    is_inclusive: bool = False,    # True if base_amount already includes GST
) -> dict:
    """
    Calculate GST components for a transaction.

    Args:
        base_amount:  Invoice value (exclusive or inclusive)
        gst_rate:     Total GST rate (e.g., 18.0 for 18%)
        transaction:  "intra" for intra-state, "inter" for inter-state
        is_inclusive: True if gst_rate is already included in base_amount
    """
    if is_inclusive:
        taxable = round(base_amount * 100 / (100 + gst_rate), 2)
    else:
        taxable = round(base_amount, 2)

    total_tax = round(taxable * gst_rate / 100, 2)

    result: dict = {
        "taxable_value": taxable,
        "gst_rate":      gst_rate,
        "total_tax":     total_tax,
        "invoice_total": round(taxable + total_tax, 2),
        "transaction":   transaction,
    }

    if transaction == "intra":
        half_rate = gst_rate / 2
        result.update({
            "cgst_rate":  half_rate,
            "sgst_rate":  half_rate,
            "cgst":       round(taxable * half_rate / 100, 2),
            "sgst":       round(taxable * half_rate / 100, 2),
            "igst":       0.0,
            "igst_rate":  0.0,
        })
    else:  # inter-state
        result.update({
            "cgst_rate": 0.0,
            "sgst_rate": 0.0,
            "cgst":      0.0,
            "sgst":      0.0,
            "igst_rate": gst_rate,
            "igst":      total_tax,
        })

    return result


# ── TDS calculation ───────────────────────────────────────────────────────────

# TDS sections under Income Tax Act (Finance Act 2024 rates)
_TDS_SECTIONS: dict[str, dict] = {
    "194C": {
        "description": "Payment to Contractors/Sub-contractors",
        "rate_individual_huf": 1.0,
        "rate_others":         2.0,
        "threshold":           30000,   # per payment or 1L annual
        "threshold_annual":    100000,
    },
    "194J": {
        "description": "Professional/Technical Services",
        "rate_individual_huf": 10.0,
        "rate_others":         10.0,
        "threshold":           30000,
        "threshold_annual":    None,
    },
    "194I": {
        "description": "Rent",
        "rate_land_building":  10.0,
        "rate_machinery":      2.0,
        "threshold":           240000,  # annual
        "threshold_annual":    240000,
    },
    "194H": {
        "description": "Commission/Brokerage",
        "rate_individual_huf": 5.0,
        "rate_others":         5.0,
        "threshold":           15000,
        "threshold_annual":    15000,
    },
    "194A": {
        "description": "Interest (other than securities)",
        "rate_individual_huf": 10.0,
        "rate_others":         10.0,
        "threshold":           40000,  # 50k for senior citizens
        "threshold_annual":    40000,
    },
    "192": {
        "description": "Salary",
        "rate_individual_huf": None,    # as per slab rate
        "rate_others":         None,
        "threshold":           250000,  # basic exemption
        "threshold_annual":    250000,
        "note": "Rate depends on employee's income tax slab. Compute separately.",
    },
}


def calculate_tds(
    payment_amount: float,
    section:        str,
    entity_type:    str = "others",   # "individual_huf" or "others"
    pan_available:  bool = True,
) -> dict:
    """
    Calculate TDS for a payment under a given Income Tax section.

    Returns:
      tds_amount, net_payment, applicable_rate, threshold, section_info
    """
    section_upper = section.upper()
    if section_upper not in _TDS_SECTIONS:
        return {
            "error":   f"TDS section {section} not in database.",
            "valid_sections": list(_TDS_SECTIONS.keys()),
        }

    info = _TDS_SECTIONS[section_upper]

    # Salary — special case
    if section_upper == "192":
        return {
            "section":     section_upper,
            "description": info["description"],
            "note":        info.get("note", ""),
            "payment":     payment_amount,
            "guidance":    "TDS on salary computed per employee's estimated annual income and tax slab.",
        }

    # Threshold check
    threshold = info.get("threshold", 0) or 0
    if payment_amount <= threshold:
        return {
            "section":           section_upper,
            "description":       info["description"],
            "payment":           payment_amount,
            "threshold":         threshold,
            "tds_applicable":    False,
            "tds_amount":        0.0,
            "net_payment":       payment_amount,
            "reason":            f"Payment ≤ threshold ₹{threshold:,.0f}. No TDS applicable.",
        }

    # Get applicable rate
    if entity_type == "individual_huf":
        rate = info.get("rate_individual_huf") or info.get("rate_others", 10.0)
    else:
        rate = info.get("rate_others", 10.0)

    # Section 194I — sub-type
    if section_upper == "194I":
        rate_land = info.get("rate_land_building", 10.0)
        rate_mach = info.get("rate_machinery", 2.0)
        rate = rate_land  # default to land/building

    # PAN not available → 20% or twice the applicable rate (whichever higher)
    if not pan_available:
        rate = max(20.0, rate * 2)

    tds_amount  = round(payment_amount * rate / 100, 2)
    net_payment = round(payment_amount - tds_amount, 2)

    surcharge = 0.0
    health_edu = round(tds_amount * 0.04, 2)   # 4% health & education cess

    return {
        "section":          section_upper,
        "description":      info["description"],
        "payment":          payment_amount,
        "entity_type":      entity_type,
        "applicable_rate":  rate,
        "tds_amount":       tds_amount,
        "surcharge":        surcharge,
        "health_edu_cess":  health_edu,
        "total_tds":        round(tds_amount + surcharge + health_edu, 2),
        "net_payment":      net_payment,
        "pan_available":    pan_available,
        "threshold":        threshold,
        "due_date":         "7th of following month (15th for March)",
        "challan":          "ITNS 281",
    }


# ── GSTR-1 export ─────────────────────────────────────────────────────────────

def generate_gstr1_data(
    invoices: list[dict],
    gstin:    str,
    period:   Optional[str] = None,   # "MMYYYY"
) -> dict:
    """
    Generate GSTR-1 summary from a list of invoice dicts.
    Returns structured JSON suitable for filing or Excel export.

    Invoice dict keys:
      invoice_number, invoice_date, customer_gstin, customer_name,
      taxable_value, igst, cgst, sgst, total_value, hsn_code, place_of_supply
    """
    period    = period or get_tax_period()
    b2b_items = []   # B2B invoices (registered customers)
    b2c_items = []   # B2C invoices (unregistered)
    total_tax = 0.0

    for inv in invoices:
        cust_gstin = inv.get("customer_gstin", "")
        taxable    = float(inv.get("taxable_value", 0))
        igst       = float(inv.get("igst", 0))
        cgst       = float(inv.get("cgst", 0))
        sgst       = float(inv.get("sgst", 0))
        tax        = igst + cgst + sgst
        total_tax += tax

        row = {
            "invoice_number": inv.get("invoice_number", ""),
            "invoice_date":   inv.get("invoice_date", ""),
            "taxable_value":  taxable,
            "igst":           igst,
            "cgst":           cgst,
            "sgst":           sgst,
            "total_value":    taxable + tax,
            "hsn_code":       inv.get("hsn_code", ""),
            "place_of_supply": inv.get("place_of_supply", ""),
        }

        if cust_gstin:
            b2b_items.append({**row, "customer_gstin": cust_gstin,
                               "customer_name": inv.get("customer_name", "")})
        else:
            b2c_items.append({**row, "customer_name": inv.get("customer_name", "")})

    return {
        "gstin":         gstin,
        "period":        period,
        "generated_at":  datetime.now(timezone.utc).isoformat(),
        "b2b":           {"count": len(b2b_items), "invoices": b2b_items},
        "b2c":           {"count": len(b2c_items), "invoices": b2c_items},
        "summary": {
            "total_invoices":  len(invoices),
            "total_taxable":   round(sum(float(i.get("taxable_value", 0)) for i in invoices), 2),
            "total_igst":      round(sum(float(i.get("igst", 0)) for i in invoices), 2),
            "total_cgst":      round(sum(float(i.get("cgst", 0)) for i in invoices), 2),
            "total_sgst":      round(sum(float(i.get("sgst", 0)) for i in invoices), 2),
            "total_tax":       round(total_tax, 2),
            "total_value":     round(sum(float(i.get("taxable_value", 0)) + float(i.get("igst", 0)) + float(i.get("cgst", 0)) + float(i.get("sgst", 0)) for i in invoices), 2),
        },
    }


def generate_gstr3b_data(
    outward_supplies: dict,
    inward_supplies:  dict,
    gstin:            str,
    period:           Optional[str] = None,
) -> dict:
    """
    Generate GSTR-3B summary from outward and inward supply totals.

    outward_supplies keys: taxable, igst, cgst, sgst, exempt, nil_rated, non_gst
    inward_supplies keys:  itc_igst, itc_cgst, itc_sgst (input tax credit)
    """
    period = period or get_tax_period()

    out_taxable = float(outward_supplies.get("taxable", 0))
    out_igst    = float(outward_supplies.get("igst", 0))
    out_cgst    = float(outward_supplies.get("cgst", 0))
    out_sgst    = float(outward_supplies.get("sgst", 0))

    itc_igst    = float(inward_supplies.get("itc_igst", 0))
    itc_cgst    = float(inward_supplies.get("itc_cgst", 0))
    itc_sgst    = float(inward_supplies.get("itc_sgst", 0))

    net_igst = round(out_igst - itc_igst, 2)
    net_cgst = round(out_cgst - itc_cgst, 2)
    net_sgst = round(out_sgst - itc_sgst, 2)

    return {
        "gstin":         gstin,
        "period":        period,
        "generated_at":  datetime.now(timezone.utc).isoformat(),
        "3.1_outward_supplies": {
            "taxable_value": out_taxable,
            "igst":          out_igst,
            "cgst":          out_cgst,
            "sgst":          out_sgst,
            "exempt":        float(outward_supplies.get("exempt", 0)),
            "nil_rated":     float(outward_supplies.get("nil_rated", 0)),
            "non_gst":       float(outward_supplies.get("non_gst", 0)),
        },
        "4_itc": {
            "itc_igst":  itc_igst,
            "itc_cgst":  itc_cgst,
            "itc_sgst":  itc_sgst,
            "total_itc": round(itc_igst + itc_cgst + itc_sgst, 2),
        },
        "6.1_payment": {
            "net_igst":   max(0, net_igst),
            "net_cgst":   max(0, net_cgst),
            "net_sgst":   max(0, net_sgst),
            "total_payable": max(0, round(net_igst + net_cgst + net_sgst, 2)),
            "late_fee_applicable": False,
        },
        "due_date": "20th of following month",
    }


# ── PDF invoice generation ────────────────────────────────────────────────────

async def generate_tax_invoice(
    seller:       dict,
    buyer:        dict,
    items:        list[dict],
    invoice_no:   str,
    invoice_date: str,
    transaction:  str = "intra",
) -> dict:
    """
    Generate a GST-compliant tax invoice PDF.

    seller/buyer keys: name, gstin, address, state
    item keys: description, hsn_code, qty, unit, unit_price, gst_rate
    """
    # Calculate GST for each line item
    line_items = []
    grand_total = 0.0
    total_tax   = 0.0

    for item in items:
        qty    = float(item.get("qty", 1))
        price  = float(item.get("unit_price", 0))
        rate   = float(item.get("gst_rate", 18.0))
        base   = round(qty * price, 2)
        gst    = calculate_gst(base, rate, transaction)

        line_items.append({
            "description":  item.get("description", ""),
            "hsn_code":     item.get("hsn_code", ""),
            "qty":          qty,
            "unit":         item.get("unit", "Nos"),
            "unit_price":   price,
            "taxable":      base,
            "gst_rate":     rate,
            "cgst":         gst.get("cgst", 0),
            "sgst":         gst.get("sgst", 0),
            "igst":         gst.get("igst", 0),
            "total":        gst["invoice_total"],
        })
        grand_total += gst["invoice_total"]
        total_tax   += gst["total_tax"]

    # Build PDF content
    content = (
        f"Invoice No: {invoice_no}  |  Date: {invoice_date}\n"
        f"Seller: {seller.get('name')} | GSTIN: {seller.get('gstin', 'N/A')}\n"
        f"Buyer: {buyer.get('name')} | GSTIN: {buyer.get('gstin', 'Unregistered')}\n\n"
        f"Transaction Type: {'Intra-State (CGST + SGST)' if transaction == 'intra' else 'Inter-State (IGST)'}\n"
        f"Total Tax: ₹{total_tax:,.2f}  |  Grand Total: ₹{grand_total:,.2f}"
    )

    sections = [{
        "heading": "Line Items",
        "body":    "\n".join(
            f"{i['description']} | HSN: {i['hsn_code']} | "
            f"Qty: {i['qty']} {i['unit']} @ ₹{i['unit_price']} | "
            f"Taxable: ₹{i['taxable']} | Tax: {i['gst_rate']}% | Total: ₹{i['total']}"
            for i in line_items
        ),
    }]

    try:
        from backend.outputs.output_generator import generate_pdf
        pdf_bytes, _, filename = generate_pdf(
            title=f"Tax Invoice — {invoice_no}",
            content=content,
            sections=sections,
            author=seller.get("name", "Seller"),
        )
        import base64
        return {
            "invoice_number":  invoice_no,
            "grand_total":     grand_total,
            "total_tax":       total_tax,
            "line_items":      line_items,
            "pdf_b64":         base64.b64encode(pdf_bytes).decode(),
            "filename":        filename,
        }
    except Exception as e:
        logger.error("Invoice PDF generation failed: %s", e)
        return {
            "invoice_number": invoice_no,
            "grand_total":    grand_total,
            "total_tax":      total_tax,
            "line_items":     line_items,
            "error":          "PDF generation failed.",
        }


# ── Main accountant dispatcher ────────────────────────────────────────────────

async def accountant_agent(
    action:   str,    # gst_calc | tds_calc | hsn_lookup | gstr1 | gstr3b | invoice | query
    payload:  dict,
    language: str = "en",
) -> dict:
    """Main AI Accountant dispatcher."""
    if action == "gst_calc":
        return calculate_gst(
            base_amount=payload.get("amount", 0),
            gst_rate=payload.get("gst_rate", 18.0),
            transaction=payload.get("transaction", "intra"),
            is_inclusive=payload.get("is_inclusive", False),
        )

    elif action == "tds_calc":
        return calculate_tds(
            payment_amount=payload.get("amount", 0),
            section=payload.get("section", "194J"),
            entity_type=payload.get("entity_type", "others"),
            pan_available=payload.get("pan_available", True),
        )

    elif action == "hsn_lookup":
        return lookup_hsn(payload.get("hsn_code", ""))

    elif action == "gstr1":
        return generate_gstr1_data(
            invoices=payload.get("invoices", []),
            gstin=payload.get("gstin", ""),
            period=payload.get("period"),
        )

    elif action == "gstr3b":
        return generate_gstr3b_data(
            outward_supplies=payload.get("outward_supplies", {}),
            inward_supplies=payload.get("inward_supplies", {}),
            gstin=payload.get("gstin", ""),
            period=payload.get("period"),
        )

    elif action == "invoice":
        return await generate_tax_invoice(
            seller=payload.get("seller", {}),
            buyer=payload.get("buyer", {}),
            items=payload.get("items", []),
            invoice_no=payload.get("invoice_no", "INV-001"),
            invoice_date=payload.get("invoice_date", str(date.today())),
            transaction=payload.get("transaction", "intra"),
        )

    elif action == "query":
        # General accounting question → LLM (Ollama-first)
        from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL
        try:
            response_text = await ollama_chat_completion(
                messages=[
                    {"role": "system", "content": (
                        f"You are an expert Indian Chartered Accountant (CA). "
                        f"Answer in {language}. Focus on GST, TDS, Income Tax, GSTR filings. "
                        f"Always mention applicable sections and deadlines. "
                        f"Recommend consulting a CA for specific advice."
                    )},
                    {"role": "user", "content": payload.get("question", "")},
                ],
                model=OLLAMA_MODEL,
                max_tokens=700,
            )
            return {
                "response": response_text or "Accounting assistant temporarily unavailable.",
                "disclaimer": "⚠️ For reference only. Consult a qualified CA for specific tax advice.",
            }
        except Exception as e:
            logger.error("Accountant LLM query failed: %s", e)
            return {"error": "Accounting assistant temporarily unavailable."}

    return {"error": f"Unknown action: {action}"}
