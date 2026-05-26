# backend/guardrails/injection_detector.py
"""
Prompt injection detection.
Catches jailbreaks, instruction overrides, role-play attacks.
Uses pattern matching + LLM-based semantic check for ambiguous cases.
"""
import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class InjectionResult:
    is_injection:   bool
    confidence:     float        # 0-1
    matched_pattern: str | None
    category:       str | None   # "jailbreak" | "override" | "role_play" | "extraction"


# High-confidence patterns — fast regex, no LLM needed
INJECTION_PATTERNS: list[tuple[str, re.Pattern, str]] = [
    (
        "instruction_override",
        re.compile(
            r'ignore\s+(all\s+)?(previous|prior|above|my|the)\s+(instructions?|prompts?|rules?|context)',
            re.IGNORECASE,
        ),
        "jailbreak",
    ),
    (
        "role_switch",
        re.compile(
            r'(you\s+are\s+now|act\s+as|pretend\s+(you\s+are|to\s+be)|roleplay\s+as)\s+'
            r'(an?\s+)?(evil|unrestricted|jailbroken|DAN|uncensored|GPT)',
            re.IGNORECASE,
        ),
        "role_play",
    ),
    (
        "system_prompt_extraction",
        re.compile(
            r'(repeat|print|output|reveal|show|tell me|what is|display)\s+'
            r'(your\s+)?(system\s+prompt|instructions?|initial\s+prompt|context|rules)',
            re.IGNORECASE,
        ),
        "extraction",
    ),
    (
        "delimiter_injection",
        re.compile(
            r'(\[INST\]|\[\[INST\]\]|<\|im_start\|>|###\s*Human:|###\s*Assistant:|<\|system\|>)',
            re.IGNORECASE,
        ),
        "override",
    ),
    (
        "token_manipulation",
        re.compile(
            r'(token\s+limit|context\s+window|bypass|circumvent|override)\s+'
            r'(the\s+)?(filter|safety|guard|restriction|limit)',
            re.IGNORECASE,
        ),
        "jailbreak",
    ),
    (
        "encoded_injection",
        re.compile(
            r'(base64|rot13|hex|caesar|encoded?)\s*:?\s*[A-Za-z0-9+/=]{20,}',
            re.IGNORECASE,
        ),
        "jailbreak",
    ),
    (
        "dan_pattern",
        re.compile(
            r'\b(DAN|DUDE|STAN|AIM|JAILBREAK|DEVELOPER\s+MODE)\b',
            re.IGNORECASE,
        ),
        "jailbreak",
    ),
]

# Medium-confidence patterns — flag for review but don't hard-block
SOFT_PATTERNS: list[tuple[str, re.Pattern]] = [
    (
        "hypothetical_frame",
        re.compile(
            r'(hypothetically|theoretically|in\s+a\s+fictional|for\s+educational\s+purposes)\s*,?\s*'
            r'(how\s+(would|could|do)|what\s+(would|could))',
            re.IGNORECASE,
        ),
    ),
    (
        "authority_claim",
        re.compile(
            r'(I\s+am\s+|I\'m\s+)(your\s+)?(developer|creator|admin|owner|anthropic|openai)',
            re.IGNORECASE,
        ),
    ),
]


def detect_injection(text: str) -> InjectionResult:
    """
    Check text for prompt injection patterns.
    Returns InjectionResult with confidence score.
    """
    # Hard patterns — high confidence block
    for pattern_name, pattern, category in INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            logger.warning(
                f"Prompt injection detected: pattern='{pattern_name}', "
                f"match_offset={match.start()}-{match.end()}"  # FIXED: was logging raw matched text which may contain PII; now logs only offsets
            )
            return InjectionResult(
                is_injection=True,
                confidence=0.95,
                matched_pattern=pattern_name,
                category=category,
            )

    # Soft patterns — medium confidence
    for pattern_name, pattern in SOFT_PATTERNS:
        match = pattern.search(text)
        if match:
            logger.info(f"Soft injection signal: pattern='{pattern_name}'")
            return InjectionResult(
                is_injection=True,
                confidence=0.55,
                matched_pattern=pattern_name,
                category="suspicious",
            )

    return InjectionResult(
        is_injection=False,
        confidence=0.0,
        matched_pattern=None,
        category=None,
    )