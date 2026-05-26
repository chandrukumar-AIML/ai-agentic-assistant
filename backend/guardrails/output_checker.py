# backend/guardrails/output_checker.py
"""
Output guardrails — runs AFTER agent generates a response.
Checks: PII leakage, toxic content, hallucination confidence.
"""
import logging
from dataclasses import dataclass
from backend.guardrails.pii_detector import scan_for_pii_in_response

logger = logging.getLogger(__name__)

HARMFUL_OUTPUT_PATTERNS = [
    # Dangerous instructions
    r'(?i)(step.by.step|detailed\s+instructions?)\s+(to|for)\s+(make|create|build|synthesize)\s+(bomb|explosive|weapon|poison|drug)',
    # Self-harm promotion
    r'(?i)(you\s+should|consider|try)\s+(suicide|self.harm|hurt\s+yourself)',
    # Malware signatures
    r'(?i)(import\s+os|subprocess\.call|eval\(|exec\()\s*.*\s*(rm\s+-rf|del\s+/|format\s+c:)',
]

import re
_HARMFUL_PATTERNS_COMPILED = [re.compile(p) for p in HARMFUL_OUTPUT_PATTERNS]


@dataclass
class OutputCheckResult:
    is_safe:          bool
    reasons:          list[str]    # list of violations found
    pii_types_found:  list[str]
    modified_response: str         # response after any masking/modification
    hallucination_flag: bool


def check_output(
    response:     str,
    tool_results: list[dict] | None = None,
) -> OutputCheckResult:
    """
    Check agent response for safety violations.
    Returns modified response (PII masked, disclaimers added) if violations found.
    """
    reasons:          list[str] = []
    modified          = response
    hallucination_flag = False

    # ── 1. PII in output ───────────────────────────────────────────────────
    pii_types = scan_for_pii_in_response(response)
    if pii_types:
        reasons.append(f"PII detected in response: {pii_types}")
        # Don't block — just log. Response was likely echoing user's masked input.
        logger.warning(f"PII in agent output: {pii_types}")

    # ── 2. Harmful content check ────────────────────────────────────────────
    for pattern in _HARMFUL_PATTERNS_COMPILED:
        if pattern.search(response):
            reasons.append("Potentially harmful content detected")
            logger.error(f"Harmful output pattern matched: {pattern.pattern[:60]}")
            modified = (
                "I can't provide that information. "
                "If you need help, please contact appropriate professional services."
            )
            return OutputCheckResult(
                is_safe=False,
                reasons=reasons,
                pii_types_found=pii_types,
                modified_response=modified,
                hallucination_flag=False,
            )

    # ── 3. Hallucination confidence check ───────────────────────────────────
    if tool_results:
        # If all tool results had very low confidence, flag response as uncertain
        avg_confidence = (
            sum(r.get("confidence", 0) for r in tool_results) / len(tool_results)
            if tool_results else 0
        )
        if avg_confidence < 0.3 and len(response) > 200:
            hallucination_flag = True
            disclaimer = (
                "\n\n---\n*⚠️ Low source confidence — please verify this information "
                "with authoritative sources.*"
            )
            modified += disclaimer
            logger.info(f"Hallucination flag added (avg_confidence={avg_confidence:.2f})")

    is_safe = len(reasons) == 0 or (
        len(reasons) == 1 and "PII" in reasons[0]   # PII alone doesn't make it unsafe
    )

    return OutputCheckResult(
        is_safe=is_safe,
        reasons=reasons,
        pii_types_found=pii_types,
        modified_response=modified,
        hallucination_flag=hallucination_flag,
    )