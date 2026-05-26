# backend/guardrails/pii_detector.py
"""
PII detection and masking.
Uses regex patterns for structured PII + optional spaCy NER for names.
Runs before sending input to the agent.
"""
import re
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PIIType(str, Enum):
    EMAIL        = "email"
    PHONE        = "phone"
    SSN          = "ssn"
    CREDIT_CARD  = "credit_card"
    IP_ADDRESS   = "ip_address"
    PASSPORT     = "passport"
    BANK_ACCOUNT = "bank_account"
    DATE_OF_BIRTH = "date_of_birth"


@dataclass
class PIIMatch:
    pii_type:   PIIType
    original:   str
    masked:     str
    start:      int
    end:        int


# ── PII patterns ────────────────────────────────────────────────────────────
PII_PATTERNS: list[tuple[PIIType, re.Pattern, str]] = [
    (
        PIIType.EMAIL,
        re.compile(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Z|a-z]{2,}\b'),
        "[EMAIL REDACTED]",
    ),
    (
        PIIType.PHONE,
        re.compile(
            r'(\+?1[-.\s]?)?'
            r'(\(?\d{3}\)?[-.\s]?)'
            r'\d{3}[-.\s]?\d{4}\b'
        ),
        "[PHONE REDACTED]",
    ),
    (
        PIIType.SSN,
        re.compile(r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b'),
        "[SSN REDACTED]",
    ),
    (
        PIIType.CREDIT_CARD,
        re.compile(
            r'\b(?:'
            r'4[0-9]{12}(?:[0-9]{3})?|'       # Visa
            r'5[1-5][0-9]{14}|'                # Mastercard
            r'3[47][0-9]{13}|'                 # Amex
            r'3(?:0[0-5]|[68][0-9])[0-9]{11}|' # Diners
            r'6(?:011|5[0-9]{2})[0-9]{12}'     # Discover
            r')\b'
        ),
        "[CREDIT CARD REDACTED]",
    ),
    (
        PIIType.IP_ADDRESS,
        re.compile(
            r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
            r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
        ),
        "[IP REDACTED]",
    ),
    (
        PIIType.BANK_ACCOUNT,
        re.compile(r'\b\d{8,17}\b(?=.*\b(?:account|acct|routing|ABA)\b)', re.IGNORECASE),
        "[ACCOUNT NUMBER REDACTED]",
    ),
    (
        PIIType.DATE_OF_BIRTH,
        re.compile(
            r'\b(?:DOB|date of birth|born on|birthday)\s*:?\s*'
            r'\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b',
            re.IGNORECASE,
        ),
        "[DATE OF BIRTH REDACTED]",
    ),
]


@dataclass
class PIIDetectionResult:
    has_pii:      bool
    matches:      list[PIIMatch]
    masked_text:  str
    pii_types:    list[str]


def detect_and_mask_pii(text: str) -> PIIDetectionResult:
    """
    Detect PII in text and return masked version.
    Processes patterns in order — more specific first.
    """
    matches:     list[PIIMatch] = []
    masked_text: str            = text

    # Sort by pattern specificity (SSN, credit card before phone)
    for pii_type, pattern, mask in PII_PATTERNS:
        for match in pattern.finditer(masked_text):
            pii_match = PIIMatch(
                pii_type=pii_type,
                original=match.group(),
                masked=mask,
                start=match.start(),
                end=match.end(),
            )
            matches.append(pii_match)

    # Apply masks from right to left (preserve offsets)
    matches_sorted = sorted(matches, key=lambda m: m.start, reverse=True)
    masked_text    = text
    for m in matches_sorted:
        masked_text = masked_text[:m.start] + m.masked + masked_text[m.end:]

    pii_types = list({m.pii_type.value for m in matches})

    if matches:
        logger.warning(f"PII detected: {pii_types} — masked in text")

    return PIIDetectionResult(
        has_pii=bool(matches),
        matches=matches,
        masked_text=masked_text,
        pii_types=pii_types,
    )


def scan_for_pii_in_response(response_text: str) -> list[str]:
    """
    Check if the agent's response accidentally contains PII.
    Returns list of PII types found.
    """
    result = detect_and_mask_pii(response_text)
    return result.pii_types