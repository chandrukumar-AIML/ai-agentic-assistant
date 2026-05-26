# backend/guardrails/compliance_checker.py
"""
Multi-framework compliance rule engine.

Frameworks:
  HIPAA    — 45 CFR §164 (PHI, access controls, audit, encryption, breach)
  GDPR     — EU 2016/679 (consent, erasure, minimization, cross-border)
  SOC2     — AICPA Trust Services Criteria (security, availability, integrity,
             confidentiality, privacy)
  EU_AI_ACT — EU AI Act 2024 (risk tiers: minimal/limited/high/unacceptable,
              transparency, human oversight)

Each check returns a ComplianceVerdict with:
  - status: APPROVE | WARN | REJECT | ESCALATE
  - violations: list of specific rule breaches
  - recommendations: remediation steps
  - audit_fields: dict written to PostgreSQL audit table
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from backend.guardrails.phi_detector import detect_phi, phi_summary

logger = logging.getLogger(__name__)


# ── Verdict types ─────────────────────────────────────────────────────────────
class ComplianceStatus(str, Enum):
    APPROVE         = "APPROVE"           # safe to proceed
    WARN            = "WARN"              # proceed with caution + log
    REJECT          = "REJECT"            # block — compliance violation
    ESCALATE        = "ESCALATE"          # send to human reviewer


class RiskTier(str, Enum):
    """EU AI Act risk classification."""
    MINIMAL        = "minimal"
    LIMITED        = "limited"
    HIGH           = "high"
    UNACCEPTABLE   = "unacceptable"


@dataclass
class ComplianceViolation:
    framework:      str            # HIPAA | GDPR | SOC2 | EU_AI_ACT
    rule_id:        str            # e.g. "HIPAA-164.312(a)(1)"
    severity:       str            # LOW | MEDIUM | HIGH | CRITICAL
    description:    str
    recommendation: str


@dataclass
class ComplianceVerdict:
    status:         ComplianceStatus
    frameworks:     list[str]       # frameworks checked
    violations:     list[ComplianceViolation]
    risk_tier:      Optional[str]   # EU AI Act tier
    phi_summary:    Optional[dict]  # from phi_detector
    timestamp:      str
    latency_ms:     float
    audit_fields:   dict[str, Any]
    recommendations: list[str] = field(default_factory=list)

    @property
    def is_approved(self) -> bool:
        return self.status == ComplianceStatus.APPROVE

    @property
    def is_blocked(self) -> bool:
        return self.status in (ComplianceStatus.REJECT, ComplianceStatus.ESCALATE)

    def to_api_dict(self) -> dict:
        return {
            "status":          self.status.value,
            "frameworks":      self.frameworks,
            "violations":      [
                {
                    "framework":      v.framework,
                    "rule_id":        v.rule_id,
                    "severity":       v.severity,
                    "description":    v.description,
                    "recommendation": v.recommendation,
                }
                for v in self.violations
            ],
            "risk_tier":       self.risk_tier,
            "phi":             self.phi_summary,
            "recommendations": self.recommendations,
            "timestamp":       self.timestamp,
        }


# ── Framework definitions ──────────────────────────────────────────────────────

# Keywords that indicate healthcare/medical context → triggers HIPAA
_HEALTHCARE_KEYWORDS = re.compile(
    r'(?i)\b('
    r'patient|diagnosis|prescription|medication|treatment|clinical|'
    r'medical|health\s*record|EHR|EMR|PHI|HIPAA|doctor|physician|'
    r'hospital|clinic|lab\s*result|blood\s*test|radiology|biopsy|'
    r'insurance\s*claim|beneficiary|medical\s*history|vital\s*sign|'
    r'ICD[-\s]?\d+|CPT\s*code|NDC\s*code|NPI|drug|dosage|allerg'
    r')\b'
)

# GDPR-sensitive operations
_GDPR_SENSITIVE_OPS = re.compile(
    r'(?i)\b('
    r'personal\s*data|personally\s*identifiable|PII|GDPR|data\s*subject|'
    r'consent|opt.in|opt.out|right\s*to\s*erasure|right\s*to\s*be\s*forgotten|'
    r'data\s*portability|cross.border\s*transfer|third\s*party\s*shar|'
    r'data\s*processing|data\s*controller|data\s*processor|DPA|'
    r'EU\s*resident|European\s*Union|CCPA|PIPEDA'
    r')\b'
)

# High-risk AI Act triggers
_HIGH_RISK_AI_KEYWORDS = re.compile(
    r'(?i)\b('
    r'biometric|facial\s*recognition|emotion\s*recognition|'
    r'credit\s*scor|criminal|law\s*enforcement|border\s*control|'
    r'recruitment|hiring|firing|employment\s*decision|'
    r'education\s*evaluation|grading|student\s*assessment|'
    r'welfare\s*eligibility|social\s*benefit|asylum|migration|'
    r'critical\s*infrastructure|safety\s*component|medical\s*device|'
    r'self.driv|autonomous\s*vehicle'
    r')\b'
)

# Unacceptable AI Act triggers
_UNACCEPTABLE_AI_KEYWORDS = re.compile(
    r'(?i)\b('
    r'social\s*scor|citizen\s*rank|mass\s*surveillance|'
    r'subliminal\s*manipulat|exploit\s*vulnerab|'
    r'real.time\s*biometric\s*surveillance|predictive\s*policing'
    r')\b'
)

# SOC2 — indicators of security/data handling actions
_SOC2_SENSITIVE_OPS = re.compile(
    r'(?i)\b('
    r'encrypt|decrypt|access\s*control|authentication|authorization|'
    r'audit\s*log|data\s*backup|disaster\s*recovery|incident\s*response|'
    r'vulnerability|penetration\s*test|compliance\s*report|'
    r'availability|uptime|SLA|data\s*integrity|data\s*loss'
    r')\b'
)


def _check_hipaa(text: str, context: dict) -> list[ComplianceViolation]:
    """HIPAA 45 CFR §164 checks."""
    violations: list[ComplianceViolation] = []

    # Run PHI scan
    phi = detect_phi(text)
    if phi.has_phi:
        severity = "CRITICAL" if phi.risk_level == "CRITICAL" else "HIGH"
        violations.append(ComplianceViolation(
            framework="HIPAA",
            rule_id="HIPAA-164.514(b)",
            severity=severity,
            description=(
                f"PHI detected in input ({phi.match_count} identifiers, "
                f"categories: {', '.join(phi.categories)}, risk: {phi.risk_level})"
            ),
            recommendation=(
                "Apply de-identification per 45 CFR §164.514(b) Safe Harbor before "
                "processing. Ensure audit trail is written and minimum-necessary rule applied."
            ),
        ))

    # Check for unencrypted PHI transmission signals
    if phi.has_phi and context.get("channel") in ("http", "email_plain", "sms_unencrypted"):
        violations.append(ComplianceViolation(
            framework="HIPAA",
            rule_id="HIPAA-164.312(e)(1)",
            severity="HIGH",
            description="PHI may be transmitted over unencrypted channel",
            recommendation="Use TLS 1.2+ (HTTPS/WSS) for all PHI transmissions.",
        ))

    # Check for missing audit trail
    if phi.has_phi and not context.get("audit_trail_enabled", True):
        violations.append(ComplianceViolation(
            framework="HIPAA",
            rule_id="HIPAA-164.312(b)",
            severity="HIGH",
            description="Access to PHI without audit trail recording",
            recommendation=(
                "Enable audit logging for all PHI access events. "
                "Logs must be retained for ≥6 years."
            ),
        ))

    # Access control — role check
    user_role = context.get("user_role", "unknown")
    if phi.has_phi and user_role == "unknown":
        violations.append(ComplianceViolation(
            framework="HIPAA",
            rule_id="HIPAA-164.312(a)(1)",
            severity="MEDIUM",
            description="PHI accessed without verified user role",
            recommendation=(
                "Implement role-based access control (RBAC). Verify user is a "
                "covered entity or business associate before PHI access."
            ),
        ))

    return violations


def _check_gdpr(text: str, context: dict) -> list[ComplianceViolation]:
    """GDPR EU 2016/679 checks."""
    violations: list[ComplianceViolation] = []

    has_personal_data = bool(_GDPR_SENSITIVE_OPS.search(text))
    phi = detect_phi(text)

    # Any personal data processing needs legal basis
    if phi.has_phi or has_personal_data:
        if not context.get("consent_obtained") and not context.get("legal_basis"):
            violations.append(ComplianceViolation(
                framework="GDPR",
                rule_id="GDPR-Art.6",
                severity="HIGH",
                description="Personal data processing without documented legal basis",
                recommendation=(
                    "Document lawful basis: consent (Art.6.1.a), contract (b), "
                    "legal obligation (c), vital interests (d), public task (e), "
                    "or legitimate interests (f)."
                ),
            ))

    # Data minimization
    if phi.match_count > 5:
        violations.append(ComplianceViolation(
            framework="GDPR",
            rule_id="GDPR-Art.5(1)(c)",
            severity="MEDIUM",
            description=f"Excessive personal data identifiers detected ({phi.match_count})",
            recommendation=(
                "Apply data minimization — collect only what is strictly necessary. "
                "Review if all identifiers are required for this processing purpose."
            ),
        ))

    # Cross-border transfer warning
    geo = context.get("data_residency", "")
    if geo and geo.lower() not in ("eu", "eea", "adequacy_decision"):
        if phi.has_phi or has_personal_data:
            violations.append(ComplianceViolation(
                framework="GDPR",
                rule_id="GDPR-Art.44-49",
                severity="HIGH",
                description=f"Personal data transfer to non-adequate country: {geo}",
                recommendation=(
                    "Use Standard Contractual Clauses (SCCs) or Binding Corporate Rules (BCRs) "
                    "for transfers to non-EEA countries without adequacy decision."
                ),
            ))

    # Right to erasure — if user requests deletion
    if re.search(r'(?i)\b(delete|erase|remove|forget)\s+(my|user|account|data|record)', text):
        violations.append(ComplianceViolation(
            framework="GDPR",
            rule_id="GDPR-Art.17",
            severity="MEDIUM",
            description="Potential right-to-erasure request detected in input",
            recommendation=(
                "Verify if this is a data subject erasure request. "
                "If so, process within 30 days per Art.17."
            ),
        ))

    return violations


def _check_soc2(text: str, context: dict) -> list[ComplianceViolation]:
    """SOC2 Type II Trust Services Criteria checks."""
    violations: list[ComplianceViolation] = []

    # CC6.1 — Logical access controls
    if context.get("user_authenticated") is False:
        violations.append(ComplianceViolation(
            framework="SOC2",
            rule_id="SOC2-CC6.1",
            severity="HIGH",
            description="Unauthenticated access attempt to controlled resource",
            recommendation="Enforce authentication before granting access. Log attempt.",
        ))

    # CC7.2 — Monitor for security events
    phi = detect_phi(text)
    if phi.has_phi and not context.get("security_monitoring_enabled", True):
        violations.append(ComplianceViolation(
            framework="SOC2",
            rule_id="SOC2-CC7.2",
            severity="MEDIUM",
            description="Sensitive data processed without security monitoring active",
            recommendation="Enable real-time security event monitoring and SIEM integration.",
        ))

    # A1.1 — Availability: check for DoS indicators
    input_size = context.get("input_size_bytes", 0)
    if input_size > 10 * 1024 * 1024:   # > 10MB
        violations.append(ComplianceViolation(
            framework="SOC2",
            rule_id="SOC2-A1.1",
            severity="MEDIUM",
            description=f"Oversized input ({input_size / 1e6:.1f}MB) — potential DoS vector",
            recommendation="Apply input size limits to protect service availability.",
        ))

    # PI1.1 — Processing Integrity: error rates
    error_rate = context.get("recent_error_rate", 0.0)
    if error_rate > 0.05:   # > 5% error rate
        violations.append(ComplianceViolation(
            framework="SOC2",
            rule_id="SOC2-PI1.1",
            severity="LOW",
            description=f"Elevated processing error rate: {error_rate:.1%}",
            recommendation="Investigate root cause. Review error thresholds in SLA.",
        ))

    return violations


def _check_eu_ai_act(text: str, context: dict) -> tuple[list[ComplianceViolation], str]:
    """
    EU AI Act 2024 risk tier classification and checks.
    Returns (violations, risk_tier).
    """
    violations: list[ComplianceViolation] = []
    risk_tier   = RiskTier.MINIMAL.value

    # Check unacceptable risk first
    if _UNACCEPTABLE_AI_KEYWORDS.search(text):
        risk_tier = RiskTier.UNACCEPTABLE.value
        violations.append(ComplianceViolation(
            framework="EU_AI_ACT",
            rule_id="EU-AI-Act-Art.5",
            severity="CRITICAL",
            description="Input references AI use prohibited under EU AI Act Art.5",
            recommendation=(
                "This use case is banned under EU AI Act. "
                "Do not proceed: social scoring, mass surveillance, "
                "subliminal manipulation, and exploitation of vulnerabilities are prohibited."
            ),
        ))

    # High risk
    elif _HIGH_RISK_AI_KEYWORDS.search(text):
        risk_tier = RiskTier.HIGH.value

        # Human oversight required for high-risk
        if not context.get("human_oversight_enabled"):
            violations.append(ComplianceViolation(
                framework="EU_AI_ACT",
                rule_id="EU-AI-Act-Art.14",
                severity="HIGH",
                description="High-risk AI application lacks mandatory human oversight",
                recommendation=(
                    "Implement Human-in-the-Loop (HITL) approval for high-risk decisions. "
                    "Document oversight mechanism per EU AI Act Annex III."
                ),
            ))

        # Technical documentation required
        if not context.get("technical_documentation"):
            violations.append(ComplianceViolation(
                framework="EU_AI_ACT",
                rule_id="EU-AI-Act-Art.11",
                severity="MEDIUM",
                description="High-risk AI system lacks required technical documentation",
                recommendation=(
                    "Prepare technical documentation per EU AI Act Art.11 and Annex IV. "
                    "Include risk assessment, training data description, and performance metrics."
                ),
            ))

        # Risk assessment
        if not context.get("conformity_assessment"):
            violations.append(ComplianceViolation(
                framework="EU_AI_ACT",
                rule_id="EU-AI-Act-Art.43",
                severity="MEDIUM",
                description="High-risk AI system requires conformity assessment",
                recommendation=(
                    "Conduct conformity assessment before deployment. "
                    "Register in EU database per Art.49."
                ),
            ))

    # Limited risk → transparency obligations
    elif re.search(r'(?i)\b(chatbot|ai\s+system|automated|virtual\s+assistant)\b', text):
        risk_tier = RiskTier.LIMITED.value
        if not context.get("ai_disclosure"):
            violations.append(ComplianceViolation(
                framework="EU_AI_ACT",
                rule_id="EU-AI-Act-Art.52",
                severity="LOW",
                description="AI interaction without mandatory transparency disclosure",
                recommendation=(
                    "Inform users they are interacting with an AI system. "
                    "Required for chatbots and emotion recognition systems."
                ),
            ))

    return violations, risk_tier


# ── Public API ────────────────────────────────────────────────────────────────

ACTIVE_FRAMEWORKS = ("HIPAA", "GDPR", "SOC2", "EU_AI_ACT")


async def run_compliance_check(
    text:       str,
    context:    Optional[dict] = None,
    frameworks: Optional[list[str]] = None,
) -> ComplianceVerdict:
    """
    Run compliance checks across requested frameworks.

    Args:
        text:       User input or agent output to check.
        context:    Runtime context dict — keys:
                      user_id, user_role, session_id, channel,
                      consent_obtained, legal_basis, data_residency,
                      user_authenticated, audit_trail_enabled,
                      human_oversight_enabled, ai_disclosure,
                      technical_documentation, conformity_assessment,
                      security_monitoring_enabled, input_size_bytes,
                      recent_error_rate
        frameworks: Subset to check. Defaults to all 4.

    Returns:
        ComplianceVerdict with status and all violations.
    """
    import time
    start = time.monotonic()

    ctx        = context or {}
    to_check   = set(frameworks or ACTIVE_FRAMEWORKS)
    violations: list[ComplianceViolation] = []
    risk_tier:  Optional[str]             = None

    # Run HIPAA
    if "HIPAA" in to_check:
        violations.extend(_check_hipaa(text, ctx))

    # Run GDPR
    if "GDPR" in to_check:
        violations.extend(_check_gdpr(text, ctx))

    # Run SOC2
    if "SOC2" in to_check:
        violations.extend(_check_soc2(text, ctx))

    # Run EU AI Act
    if "EU_AI_ACT" in to_check:
        eu_viols, risk_tier = _check_eu_ai_act(text, ctx)
        violations.extend(eu_viols)

    # Determine overall status
    severities = {v.severity for v in violations}
    if "CRITICAL" in severities:
        status = ComplianceStatus.REJECT
    elif "HIGH" in severities:
        # Unacceptable AI tier → always REJECT
        if risk_tier == RiskTier.UNACCEPTABLE.value:
            status = ComplianceStatus.REJECT
        else:
            status = ComplianceStatus.ESCALATE
    elif "MEDIUM" in severities:
        status = ComplianceStatus.WARN
    elif violations:
        status = ComplianceStatus.WARN
    else:
        status = ComplianceStatus.APPROVE

    # PHI summary (safe — no original text)
    phi_result = detect_phi(text)
    phi_s      = phi_summary(phi_result) if phi_result.has_phi else None

    # Build recommendations list
    recs = list(dict.fromkeys(v.recommendation for v in violations))   # deduplicated

    elapsed  = (time.monotonic() - start) * 1000
    ts       = datetime.now(timezone.utc).isoformat()

    audit_fields = {
        "timestamp":       ts,
        "user_id":         ctx.get("user_id", ""),
        "session_id":      ctx.get("session_id", ""),
        "frameworks":      list(to_check),
        "status":          status.value,
        "violation_count": len(violations),
        "risk_tier":       risk_tier,
        "phi_detected":    phi_result.has_phi,
        "phi_categories":  phi_result.categories,
        "latency_ms":      round(elapsed, 2),
    }

    logger.info(
        "Compliance check — status: %s, violations: %d, risk: %s, %.1fms",
        status.value, len(violations), risk_tier, elapsed,
    )

    return ComplianceVerdict(
        status=status,
        frameworks=list(to_check),
        violations=violations,
        risk_tier=risk_tier,
        phi_summary=phi_s,
        timestamp=ts,
        latency_ms=round(elapsed, 2),
        audit_fields=audit_fields,
        recommendations=recs,
    )


def get_framework_status() -> dict:
    """Return enabled frameworks and their rule counts."""
    return {
        "frameworks": [
            {
                "id":          "HIPAA",
                "name":        "HIPAA 45 CFR §164",
                "enabled":     True,
                "rule_count":  4,
                "description": "Health Insurance Portability and Accountability Act — PHI protection",
            },
            {
                "id":          "GDPR",
                "name":        "GDPR EU 2016/679",
                "enabled":     True,
                "rule_count":  4,
                "description": "General Data Protection Regulation — EU personal data",
            },
            {
                "id":          "SOC2",
                "name":        "SOC2 Type II",
                "enabled":     True,
                "rule_count":  4,
                "description": "AICPA Trust Services Criteria — security & availability",
            },
            {
                "id":          "EU_AI_ACT",
                "name":        "EU AI Act 2024",
                "enabled":     True,
                "rule_count":  5,
                "description": "EU AI Act risk tiers — minimal/limited/high/unacceptable",
            },
        ],
        "total_rules": 17,
        "active":      True,
    }
