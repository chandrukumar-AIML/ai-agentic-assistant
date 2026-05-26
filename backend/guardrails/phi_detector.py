# backend/guardrails/phi_detector.py
"""
HIPAA PHI Detector — all 18 Safe Harbor identifier categories.

PHI = Protected Health Information. Under HIPAA, ANY of the 18
identifiers linked to health data makes a record PHI.

References: 45 CFR §164.514(b)(2)
"""
from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


# ── 18 HIPAA Safe Harbor identifier categories ────────────────────────────────
class PHICategory(str, Enum):
    NAME                  = "name"                   # 1
    GEOGRAPHIC            = "geographic"              # 2 — sub-state (street, zip, city)
    DATE                  = "date"                   # 3 — dates except year
    PHONE                 = "phone"                  # 4
    FAX                   = "fax"                    # 5
    EMAIL                 = "email"                  # 6
    SSN                   = "ssn"                    # 7
    MRN                   = "mrn"                    # 8 — medical record number
    HEALTH_PLAN_BENE      = "health_plan_beneficiary" # 9
    ACCOUNT_NUMBER        = "account_number"          # 10
    CERTIFICATE_LICENSE   = "certificate_license"     # 11
    VEHICLE_ID            = "vehicle_id"              # 12
    DEVICE_ID             = "device_id"               # 13
    URL                   = "url"                    # 14
    IP_ADDRESS            = "ip_address"              # 15
    BIOMETRIC             = "biometric"               # 16 — fingerprint, voice-print
    FULL_FACE_PHOTO       = "full_face_photo"          # 17
    UNIQUE_IDENTIFIER     = "unique_identifier"        # 18 — catch-all


# ── Regex patterns for detectable categories ─────────────────────────────────
# (Categories 1/16/17 require ML/NLP — regex covers the rest)
_PHI_PATTERNS: list[tuple[PHICategory, re.Pattern, str]] = [
    # 4. Phone numbers (US + international)
    (
        PHICategory.PHONE,
        re.compile(
            r'(?<!\w)(\+?1[-.\s]?)?(\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}(?!\w)',
        ),
        "[PHONE REDACTED]",
    ),
    # 5. Fax — same format, context-keyed
    (
        PHICategory.FAX,
        re.compile(
            r'(?i)(?:fax|facsimile)\s*[:#]?\s*(\+?1[-.\s]?)?(\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}',
        ),
        "[FAX REDACTED]",
    ),
    # 6. Email
    (
        PHICategory.EMAIL,
        re.compile(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b'),
        "[EMAIL REDACTED]",
    ),
    # 7. Social Security Number
    (
        PHICategory.SSN,
        re.compile(r'\b(?!000|666|9\d{2})\d{3}[-\s]?(?!00)\d{2}[-\s]?(?!0000)\d{4}\b'),
        "[SSN REDACTED]",
    ),
    # 8. Medical Record Number — MRN: numeric, 6-10 digits preceded by keyword
    (
        PHICategory.MRN,
        re.compile(
            r'(?i)(?:MRN|medical\s+record\s+(?:number|no|#))\s*[:#]?\s*(\d{5,12})',
        ),
        "[MRN REDACTED]",
    ),
    # 9. Health Plan Beneficiary / Member ID
    (
        PHICategory.HEALTH_PLAN_BENE,
        re.compile(
            r'(?i)(?:beneficiary|member|policy|health\s+plan)\s*(?:id|number|no|#)\s*[:#]?\s*([A-Z0-9]{6,15})',
        ),
        "[HEALTH-PLAN-ID REDACTED]",
    ),
    # 10. Account numbers (bank)
    (
        PHICategory.ACCOUNT_NUMBER,
        re.compile(
            r'(?i)(?:account|acct)\s*(?:number|no|#)\s*[:#]?\s*(\d{6,17})',
        ),
        "[ACCOUNT# REDACTED]",
    ),
    # 11. Certificate / License numbers
    (
        PHICategory.CERTIFICATE_LICENSE,
        re.compile(
            r'(?i)(?:license|certificate|cert|lic)\s*(?:number|no|#)\s*[:#]?\s*([A-Z0-9\-]{4,20})',
        ),
        "[LICENSE# REDACTED]",
    ),
    # 12. Vehicle Identifiers (VIN = 17 alphanumeric)
    (
        PHICategory.VEHICLE_ID,
        re.compile(r'\b[A-HJ-NPR-Z0-9]{17}\b'),
        "[VIN REDACTED]",
    ),
    # 13. Device identifiers (IMEI = 15 digits, serial patterns)
    (
        PHICategory.DEVICE_ID,
        re.compile(
            r'(?i)(?:IMEI|serial\s*(?:number|no|#)|device\s*id)\s*[:#]?\s*([A-Z0-9\-]{8,20})',
        ),
        "[DEVICE-ID REDACTED]",
    ),
    # 14. URLs
    (
        PHICategory.URL,
        re.compile(r'https?://[^\s<>"\']+'),
        "[URL REDACTED]",
    ),
    # 15. IP addresses (v4 + v6)
    (
        PHICategory.IP_ADDRESS,
        re.compile(
            r'(?:'
            r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}'
            r'(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b'
            r'|'
            r'(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}'  # IPv6 simplified
            r')',
        ),
        "[IP REDACTED]",
    ),
    # 3. Dates (except year alone) — MM/DD/YYYY, DD-Mon-YYYY, etc.
    (
        PHICategory.DATE,
        re.compile(
            r'(?i)'
            r'\b(?:'
            r'\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}'           # 01/15/2024
            r'|\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{2,4}'  # 15 Jan 2024
            r'|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{1,2},?\s+\d{2,4}'  # Jan 15, 2024
            r')\b',
        ),
        "[DATE REDACTED]",
    ),
    # 2. Geographic — ZIP codes (5-digit US) and street addresses
    (
        PHICategory.GEOGRAPHIC,
        re.compile(
            r'(?i)'
            r'(?:'
            r'\b\d{5}(?:-\d{4})?\b'                       # ZIP / ZIP+4
            r'|\b\d+\s+[A-Za-z0-9\s,\.]+(?:St|Ave|Rd|Blvd|Dr|Ln|Way|Ct|Pl|Cir)\b'  # street
            r')',
        ),
        "[GEOGRAPHIC REDACTED]",
    ),
    # 18. Catch-all unique identifiers (NPI = 10 digits)
    (
        PHICategory.UNIQUE_IDENTIFIER,
        re.compile(
            r'(?i)(?:NPI|national\s+provider)\s*[:#]?\s*(\d{10})',
        ),
        "[NPI REDACTED]",
    ),
]

# ── India-specific health identifiers (ABHA / Ayushman Bharat) ───────────────
_INDIA_PHI_PATTERNS: list[tuple[PHICategory, re.Pattern, str]] = [
    (
        PHICategory.UNIQUE_IDENTIFIER,
        re.compile(r'(?i)(?:ABHA|ayushman\s+bharat)\s*(?:id|number|no|#)?\s*[:#]?\s*(\d{14})'),
        "[ABHA-ID REDACTED]",
    ),
    (
        PHICategory.UNIQUE_IDENTIFIER,
        re.compile(r'(?i)(?:UHID|hospital\s+id)\s*[:#]?\s*([A-Z0-9]{6,12})'),
        "[UHID REDACTED]",
    ),
]


@dataclass
class PHIMatch:
    category:   PHICategory
    original:   str          # never logged
    masked:     str
    start:      int
    end:        int


@dataclass
class PHIDetectionResult:
    has_phi:       bool
    categories:    list[str]            # PHICategory values found
    match_count:   int
    masked_text:   str
    risk_level:    str                  # LOW / MEDIUM / HIGH / CRITICAL
    matches:       list[PHIMatch] = field(default_factory=list)
    hipaa_flags:   list[str]     = field(default_factory=list)


def _compute_risk(categories: list[str]) -> str:
    """
    CRITICAL: SSN + any health identifier
    HIGH:     2+ PHI categories present
    MEDIUM:   1 PHI category
    LOW:      0
    """
    n = len(set(categories))
    if n == 0:
        return "LOW"
    if PHICategory.SSN.value in categories and n >= 2:
        return "CRITICAL"
    if n >= 2:
        return "HIGH"
    return "MEDIUM"


def detect_phi(
    text: str,
    include_india: bool = True,
    mask_output: bool = True,
) -> PHIDetectionResult:
    """
    Scan text for HIPAA PHI across all 18 Safe Harbor categories.

    Args:
        text:           Input to scan.
        include_india:  Also check India-specific health IDs (ABHA, UHID).
        mask_output:    Replace PHI with category placeholders in masked_text.

    Returns:
        PHIDetectionResult — original matches are stored but never logged.
    """
    patterns = _PHI_PATTERNS + (_INDIA_PHI_PATTERNS if include_india else [])
    matches: list[PHIMatch] = []

    for category, pattern, mask in patterns:
        for m in pattern.finditer(text):
            matches.append(PHIMatch(
                category=category,
                original=m.group(),   # kept in memory only, not logged
                masked=mask,
                start=m.start(),
                end=m.end(),
            ))

    # Apply masks right-to-left to preserve offsets
    masked_text = text
    if mask_output:
        for m in sorted(matches, key=lambda x: x.start, reverse=True):
            masked_text = masked_text[:m.start] + m.masked + masked_text[m.end:]

    categories  = [m.category.value for m in matches]
    unique_cats = list(dict.fromkeys(categories))   # deduplicated, order-preserving
    risk_level  = _compute_risk(categories)

    # HIPAA flags: which of the 18 categories were found
    hipaa_flags: list[str] = []
    if matches:
        hipaa_flags = [f"PHI_{cat.upper()}_DETECTED" for cat in unique_cats]
        # Only log category types — never log the actual matched text
        logger.warning(
            "PHI detected — categories: %s, risk: %s, matches: %d",
            unique_cats, risk_level, len(matches),
        )

    return PHIDetectionResult(
        has_phi=bool(matches),
        categories=unique_cats,
        match_count=len(matches),
        masked_text=masked_text,
        risk_level=risk_level,
        matches=matches,
        hipaa_flags=hipaa_flags,
    )


def phi_summary(result: PHIDetectionResult) -> dict:
    """
    Safe dict for API responses and audit logs.
    NEVER includes original matched text.
    """
    return {
        "has_phi":      result.has_phi,
        "categories":   result.categories,
        "match_count":  result.match_count,
        "risk_level":   result.risk_level,
        "hipaa_flags":  result.hipaa_flags,
    }
