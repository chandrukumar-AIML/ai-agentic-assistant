# backend/verticals/form_reader/form_agent.py
"""
AI Form Reader + Data Extractor (Feature 14).

Capabilities:
  1. GPT-4o Vision — extract structured data from any form image/PDF page
  2. India-specific validators:
       PAN card   — AAAAA9999A  (5 alpha + 4 digit + 1 alpha)
       Aadhaar    — 12 digits, Luhn-like Verhoeff check
       GSTIN      — 15-char GST Identification Number
       PAN-linked GSTIN state code validation
       Indian mobile — 10 digits, starts 6-9
       Indian pincode — 6 digits
  3. Confidence scores per field (0.0–1.0)
  4. Multi-page support (process page by page)
  5. Guardian compliance check — PII redaction option
  6. Output as structured JSON or Excel (via output_generator)

Supported form types (auto-detected from content):
  pan_card | aadhaar_card | gstin_reg | invoice | kyc | generic
"""
from __future__ import annotations

import base64
import logging
import re
from typing import Optional

from backend.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()


# ── India-specific validation patterns ───────────────────────────────────────

_PAN_RE      = re.compile(r'^[A-Z]{5}[0-9]{4}[A-Z]$')
_GSTIN_RE    = re.compile(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$')
_AADHAAR_RE  = re.compile(r'^[2-9][0-9]{11}$')
_MOBILE_IN   = re.compile(r'^[6-9][0-9]{9}$')
_PINCODE_IN  = re.compile(r'^[1-9][0-9]{5}$')
_IFSC_RE     = re.compile(r'^[A-Z]{4}0[A-Z0-9]{6}$')

# GSTIN state codes (2-digit prefix)
_GSTIN_STATES = {
    "01": "Jammu & Kashmir", "02": "Himachal Pradesh", "03": "Punjab",
    "04": "Chandigarh", "05": "Uttarakhand", "06": "Haryana",
    "07": "Delhi", "08": "Rajasthan", "09": "Uttar Pradesh",
    "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh",
    "13": "Nagaland", "14": "Manipur", "15": "Mizoram",
    "16": "Tripura", "17": "Meghalaya", "18": "Assam",
    "19": "West Bengal", "20": "Jharkhand", "21": "Odisha",
    "22": "Chhattisgarh", "23": "Madhya Pradesh", "24": "Gujarat",
    "26": "Dadra & Nagar Haveli and Daman & Diu", "27": "Maharashtra",
    "28": "Andhra Pradesh (old)", "29": "Karnataka", "30": "Goa",
    "31": "Lakshadweep", "32": "Kerala", "33": "Tamil Nadu",
    "34": "Puducherry", "35": "Andaman & Nicobar", "36": "Telangana",
    "37": "Andhra Pradesh", "38": "Ladakh",
    "97": "Other Territory", "99": "Centre Jurisdiction",
}

# PAN 4th char → entity type
_PAN_ENTITY = {
    "P": "Individual", "C": "Company", "H": "HUF",
    "F": "Firm", "A": "AOP", "T": "Trust",
    "B": "BOI", "L": "Local Authority", "J": "AJP",
    "G": "Government",
}


def validate_pan(pan: str) -> dict:
    """Validate Indian PAN number and return entity type."""
    pan = pan.strip().upper().replace(" ", "")
    if not _PAN_RE.match(pan):
        return {"valid": False, "pan": pan, "reason": "Format must be AAAAA9999A"}
    entity_code = pan[3]
    return {
        "valid":       True,
        "pan":         pan,
        "entity_type": _PAN_ENTITY.get(entity_code, "Unknown"),
        "holder_name_initials": pan[:3],  # first 3 chars = surname initials
    }


def validate_gstin(gstin: str) -> dict:
    """Validate GSTIN and extract embedded PAN + state."""
    gstin = gstin.strip().upper().replace(" ", "")
    if not _GSTIN_RE.match(gstin):
        return {"valid": False, "gstin": gstin, "reason": "Invalid GSTIN format"}
    state_code = gstin[:2]
    embedded_pan = gstin[2:12]
    return {
        "valid":        True,
        "gstin":        gstin,
        "state_code":   state_code,
        "state_name":   _GSTIN_STATES.get(state_code, "Unknown"),
        "embedded_pan": embedded_pan,
        "pan_valid":    validate_pan(embedded_pan)["valid"],
        "entity_num":   gstin[12],  # registration number for same PAN
        "check_digit":  gstin[14],
    }


def _verhoeff_check(n: str) -> bool:
    """
    Verhoeff algorithm check digit validation for Aadhaar.
    Returns True if the 12-digit number is valid per Verhoeff.
    """
    # Verhoeff tables
    d = [
        [0,1,2,3,4,5,6,7,8,9],
        [1,2,3,4,0,6,7,8,9,5],
        [2,3,4,0,1,7,8,9,5,6],
        [3,4,0,1,2,8,9,5,6,7],
        [4,0,1,2,3,9,5,6,7,8],
        [5,9,8,7,6,0,4,3,2,1],
        [6,5,9,8,7,1,0,4,3,2],
        [7,6,5,9,8,2,1,0,4,3],
        [8,7,6,5,9,3,2,1,0,4],
        [9,8,7,6,5,4,3,2,1,0],
    ]
    p = [
        [0,1,2,3,4,5,6,7,8,9],
        [1,5,7,6,2,8,3,0,9,4],
        [5,8,0,3,7,9,6,1,4,2],
        [8,9,1,6,0,4,3,5,2,7],
        [9,4,5,3,1,2,6,8,7,0],
        [4,2,8,6,5,7,3,9,0,1],
        [2,7,9,3,8,0,6,4,1,5],
        [7,0,4,6,9,1,3,2,5,8],
    ]
    inv = [0,4,3,2,1,5,6,7,8,9]
    c = 0
    reversed_n = list(reversed(str(n)))
    for i, ch in enumerate(reversed_n):
        c = d[c][p[i % 8][int(ch)]]
    return c == 0


def validate_aadhaar(aadhaar: str) -> dict:
    """Validate 12-digit Aadhaar number."""
    aadhaar = re.sub(r'[\s-]', '', aadhaar)
    if not _AADHAAR_RE.match(aadhaar):
        return {"valid": False, "aadhaar_masked": aadhaar, "reason": "Must be 12 digits starting 2-9"}
    verhoeff_ok = _verhoeff_check(aadhaar)
    # Always mask — never return full Aadhaar in response
    masked = "XXXX XXXX " + aadhaar[-4:]
    return {
        "valid":          verhoeff_ok,
        "aadhaar_masked": masked,
        "last_4":         aadhaar[-4:],
        "verhoeff_ok":    verhoeff_ok,
        "reason":         None if verhoeff_ok else "Verhoeff check digit failed",
    }


def validate_mobile_in(mobile: str) -> dict:
    mobile = re.sub(r'[\s\-\+]', '', mobile)
    if mobile.startswith("91") and len(mobile) == 12:
        mobile = mobile[2:]
    return {
        "valid":  bool(_MOBILE_IN.match(mobile)),
        "mobile": mobile,
    }


def validate_pincode_in(pincode: str) -> dict:
    pincode = pincode.strip()
    return {
        "valid":   bool(_PINCODE_IN.match(pincode)),
        "pincode": pincode,
    }


def validate_ifsc(ifsc: str) -> dict:
    ifsc = ifsc.strip().upper()
    return {
        "valid":    bool(_IFSC_RE.match(ifsc)),
        "ifsc":     ifsc,
        "bank_code": ifsc[:4] if len(ifsc) >= 4 else "",
        "branch":    ifsc[5:] if len(ifsc) >= 11 else "",
    }


# ── Form type detector ────────────────────────────────────────────────────────

def _detect_form_type(extracted_text: str) -> str:
    """Heuristic form type classification from extracted text keywords."""
    t = extracted_text.lower()
    if "permanent account number" in t or "income tax" in t and "pan" in t:
        return "pan_card"
    if "aadhaar" in t or "unique identification" in t or "uidai" in t:
        return "aadhaar_card"
    if "goods and services tax" in t or "gstin" in t or "gst" in t:
        return "gstin_reg" if "registration" in t or "certificate" in t else "invoice"
    if "kyc" in t or "know your customer" in t:
        return "kyc"
    return "generic"


# ── GPT-4o Vision extraction ──────────────────────────────────────────────────

_FORM_SYSTEM_PROMPT = """You are an expert data extraction AI. Analyze the form image and extract all fields.

Return a JSON object with this structure:
{
  "form_type": "pan_card|aadhaar_card|gstin_reg|invoice|kyc|generic",
  "fields": {
    "<field_name>": {
      "value": "<extracted value or null>",
      "confidence": <0.0-1.0>,
      "raw_text": "<exact text from form>"
    }
  },
  "raw_text": "<all text visible in the form>"
}

For India forms, extract these if present:
- pan_number, aadhaar_number, gstin, mobile, email, pincode, ifsc_code
- name, father_name, dob, address, bank_account_number
- invoice_number, invoice_date, total_amount, tax_amount, hsn_code

Confidence guidelines:
  1.0 = clearly visible, unambiguous
  0.7-0.9 = visible but slightly unclear
  0.4-0.6 = partially visible or inferred
  0.1-0.3 = very uncertain, guessed

Always extract what you can see. Use null for missing fields. Never fabricate values."""


_MAX_IMAGE_BYTES = 20 * 1024 * 1024   # 20 MB base64 limit (≈15 MB actual image)


async def extract_form_data(
    image_b64:   str,
    form_hint:   Optional[str] = None,   # "pan_card", "aadhaar_card", etc.
    redact_pii:  bool = False,
    language:    str  = "en",
) -> dict:
    """
    Extract structured data from a form image using GPT-4o Vision.
    Validates India-specific fields automatically.
    Optionally redacts PII from the response.

    Args:
        image_b64:  Base64-encoded JPEG/PNG (max 20 MB encoded).
        form_hint:  Optional hint: pan_card|aadhaar_card|gstin_reg|invoice|kyc|generic.
        redact_pii: Mask sensitive fields in the response.
        language:   Response language code.
    """
    # Security: enforce max image size before sending to OpenAI
    if len(image_b64) > _MAX_IMAGE_BYTES:
        return {
            "error":     "Image too large. Maximum allowed size is 15 MB.",
            "form_type": "unknown",
            "fields":    {},
            "validations": {},
        }

    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    hint_text = f"\nThis appears to be a {form_hint} form." if form_hint else ""
    user_msg  = f"Extract all data from this form.{hint_text} Return JSON only."

    try:
        resp = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": _FORM_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_msg},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url":    f"data:image/jpeg;base64,{image_b64}",
                                "detail": "high",
                            },
                        },
                    ],
                },
            ],
            max_tokens=1500,
            response_format={"type": "json_object"},
        )
        import json
        raw = resp.choices[0].message.content or "{}"
        extracted = json.loads(raw)
    except Exception as e:
        logger.error("Form extraction GPT-4o call failed: %s", e)
        return {
            "error":      "Form extraction temporarily unavailable.",
            "form_type":  "unknown",
            "fields":     {},
            "validations": {},
        }

    fields      = extracted.get("fields", {})
    raw_text    = extracted.get("raw_text", "")
    form_type   = extracted.get("form_type") or _detect_form_type(raw_text)

    # Run India-specific validations
    validations: dict = {}

    if pan := _get_field_value(fields, "pan_number"):
        validations["pan"] = validate_pan(pan)

    if aadhaar := _get_field_value(fields, "aadhaar_number"):
        validations["aadhaar"] = validate_aadhaar(aadhaar)

    if gstin := _get_field_value(fields, "gstin"):
        validations["gstin"] = validate_gstin(gstin)

    if mobile := _get_field_value(fields, "mobile"):
        validations["mobile"] = validate_mobile_in(mobile)

    if pincode := _get_field_value(fields, "pincode"):
        validations["pincode"] = validate_pincode_in(pincode)

    if ifsc := _get_field_value(fields, "ifsc_code"):
        validations["ifsc"] = validate_ifsc(ifsc)

    # Cross-validate GSTIN vs PAN
    if "gstin" in validations and "pan" in validations:
        gstin_info = validations["gstin"]
        pan_info   = validations["pan"]
        if gstin_info.get("valid") and pan_info.get("valid"):
            gstin_pan     = gstin_info.get("embedded_pan", "")
            extracted_pan = pan_info.get("pan", "")
            validations["gstin_pan_match"] = (gstin_pan == extracted_pan)

    # PII redaction if requested
    if redact_pii:
        fields = _redact_fields(fields, form_type)

    # Compute overall confidence
    confidences = [
        float(v.get("confidence", 0.5))
        for v in fields.values()
        if isinstance(v, dict) and v.get("value") is not None
    ]
    overall_confidence = round(sum(confidences) / len(confidences), 3) if confidences else 0.0

    return {
        "form_type":          form_type,
        "fields":             fields,
        "validations":        validations,
        "overall_confidence": overall_confidence,
        "field_count":        len([v for v in fields.values() if isinstance(v, dict) and v.get("value")]),
        "pii_redacted":       redact_pii,
        "model":              "gpt-4o-vision",
    }


def _get_field_value(fields: dict, key: str) -> Optional[str]:
    """Safely extract field value string from GPT-4o response."""
    field = fields.get(key)
    if not field:
        return None
    if isinstance(field, dict):
        return field.get("value")
    if isinstance(field, str):
        return field
    return None


_PII_FIELDS = {
    "pan_card":   ["aadhaar_number", "bank_account_number"],
    "aadhaar_card": ["aadhaar_number", "mobile", "email"],
    "kyc":        ["aadhaar_number", "pan_number", "bank_account_number", "mobile"],
    "generic":    ["aadhaar_number"],
}


def _redact_fields(fields: dict, form_type: str) -> dict:
    """Redact sensitive PII fields based on form type."""
    redact_keys = set(_PII_FIELDS.get(form_type, _PII_FIELDS["generic"]))
    result = {}
    for k, v in fields.items():
        if k in redact_keys and isinstance(v, dict) and v.get("value"):
            result[k] = {**v, "value": "[REDACTED]", "raw_text": "[REDACTED]"}
        else:
            result[k] = v
    return result


# ── Multi-page processing ─────────────────────────────────────────────────────

async def extract_multi_page(
    images_b64: list[str],
    form_hint:  Optional[str] = None,
    redact_pii: bool = False,
) -> dict:
    """
    Process multiple pages of a form.
    Merges extracted fields, keeping highest-confidence values per field.
    """
    import asyncio

    pages = await asyncio.gather(
        *[extract_form_data(img, form_hint, redact_pii) for img in images_b64]
    )

    merged_fields:  dict = {}
    all_validations: dict = {}
    form_type = "generic"

    for i, page in enumerate(pages):
        if page.get("form_type", "generic") != "generic":
            form_type = page["form_type"]
        for key, val in page.get("fields", {}).items():
            if key not in merged_fields:
                merged_fields[key] = val
            else:
                # Keep higher confidence value
                existing_conf = merged_fields[key].get("confidence", 0) if isinstance(merged_fields[key], dict) else 0
                new_conf      = val.get("confidence", 0) if isinstance(val, dict) else 0
                if new_conf > existing_conf:
                    merged_fields[key] = val
        all_validations.update(page.get("validations", {}))

    confidences = [
        float(v.get("confidence", 0.5))
        for v in merged_fields.values()
        if isinstance(v, dict) and v.get("value") is not None
    ]
    overall = round(sum(confidences) / len(confidences), 3) if confidences else 0.0

    return {
        "form_type":          form_type,
        "fields":             merged_fields,
        "validations":        all_validations,
        "overall_confidence": overall,
        "pages_processed":    len(images_b64),
        "field_count":        len([v for v in merged_fields.values() if isinstance(v, dict) and v.get("value")]),
        "pii_redacted":       redact_pii,
    }


# ── Main dispatcher ───────────────────────────────────────────────────────────

async def form_reader_agent(
    images_b64: list[str],
    form_hint:  Optional[str] = None,
    redact_pii: bool = False,
    export_excel: bool = False,
    language:   str = "en",
) -> dict:
    """
    Main form reader dispatcher.
    Handles single or multi-page forms.
    Optionally exports to Excel via output_generator.
    """
    if not images_b64:
        return {"error": "No images provided."}

    if len(images_b64) == 1:
        result = await extract_form_data(images_b64[0], form_hint, redact_pii, language)
    else:
        result = await extract_multi_page(images_b64, form_hint, redact_pii)

    if export_excel and not result.get("error"):
        try:
            import base64
            from backend.outputs.output_generator import generate_excel

            # generate_excel expects rows as lists, not dicts
            headers = ["Field", "Value", "Confidence", "Raw Text"]
            rows: list[list] = [
                [
                    k,
                    v.get("value", "")      if isinstance(v, dict) else str(v),
                    v.get("confidence", "") if isinstance(v, dict) else "",
                    v.get("raw_text", "")   if isinstance(v, dict) else "",
                ]
                for k, v in result.get("fields", {}).items()
            ]
            excel_bytes, _, filename = generate_excel(
                sheets=[{"name": "Extracted Fields", "headers": headers, "rows": rows}],
                title=f"Form Extraction — {result.get('form_type', 'generic')}",
            )
            result["excel_b64"]  = base64.b64encode(excel_bytes).decode()
            result["excel_file"] = filename
        except Exception as e:
            logger.warning("Excel export failed (non-fatal): %s", e)

    return result
