# backend/guardrails/guard_engine.py
"""
Central guardrail engine.
Orchestrates input + output checks.
Integrates with NeMo Guardrails for semantic rail checks.
Falls back to custom checks if NeMo unavailable.
"""
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from backend.guardrails.pii_detector    import detect_and_mask_pii, PIIDetectionResult
from backend.guardrails.injection_detector import detect_injection, InjectionResult
from backend.guardrails.output_checker  import check_output, OutputCheckResult
from backend.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()

CONFIG_DIR = Path(__file__).parent / "configs"

# Domain configs available
DOMAIN_CONFIGS = {
    "general": CONFIG_DIR / "general.yaml",
    "medical": CONFIG_DIR / "medical.yaml",
    "code":    CONFIG_DIR / "code.yaml",
    "legal":   CONFIG_DIR / "legal.yaml",
}

# Safety flags to send to React UI
SAFE_FLAG   = "safe"
BLOCKED_FLAG = "blocked"
WARNED_FLAG  = "warned"
REDACTED_FLAG = "redacted"


@dataclass
class GuardResult:
    passed:           bool
    flag:             str          # SAFE_FLAG | BLOCKED_FLAG | WARNED_FLAG | REDACTED_FLAG
    original_input:   str
    processed_input:  str          # after masking/modification
    pii_detected:     bool
    pii_types:        list[str]
    injection_detected: bool
    injection_category: str | None
    block_reason:     str | None
    latency_ms:       float
    audit_entry:      dict         # for audit log


@dataclass
class OutputGuardResult:
    passed:           bool
    flag:             str
    original_response: str
    processed_response: str
    pii_in_response:  bool
    hallucination_flag: bool
    block_reason:     str | None
    latency_ms:       float


_nemo_rails = {}   # domain → NeMo RailsConfig (lazy-loaded)


def _try_load_nemo(domain: str):
    """Lazy-load NeMo Guardrails config for a domain. Fails gracefully."""
    if domain in _nemo_rails:
        return _nemo_rails[domain]

    config_path = DOMAIN_CONFIGS.get(domain, CONFIG_DIR / "general.yaml")
    try:
        from nemoguardrails import RailsConfig, LLMRails
        config = RailsConfig.from_path(str(config_path.parent))
        _nemo_rails[domain] = LLMRails(config)
        logger.info(f"NeMo Guardrails loaded for domain: {domain}")
        return _nemo_rails[domain]
    except ImportError:
        logger.warning("nemoguardrails not installed — using custom checks only")
        _nemo_rails[domain] = None
        return None
    except Exception as e:
        logger.warning(f"NeMo config load failed for {domain}: {e} — using custom checks")
        _nemo_rails[domain] = None
        return None


async def check_input(
    user_input: str,
    user_id:    str,
    domain:     str = "general",
    session_id: str = "",
) -> GuardResult:
    """
    Run all input guardrails:
    1. PII detection + masking
    2. Prompt injection detection
    3. NeMo semantic rails (if available)
    4. Toxic content filter

    Returns GuardResult — if passed=False, the agent should NOT run.
    """
    start       = time.monotonic()
    processed   = user_input
    audit_entry = {
        "user_id":    user_id,
        "session_id": session_id,
        "domain":     domain,
        "input_len":  len(user_input),
    }

    # ── Step 1: PII Detection + Masking ────────────────────────────────────
    pii_result: PIIDetectionResult = detect_and_mask_pii(user_input)
    if pii_result.has_pii:
        processed = pii_result.masked_text
        audit_entry["pii_detected"]  = True
        audit_entry["pii_types"]     = pii_result.pii_types
        logger.info(f"PII masked for user {user_id}: {pii_result.pii_types}")

    # ── Step 2: Injection Detection ─────────────────────────────────────────
    injection_result: InjectionResult = detect_injection(processed)

    if injection_result.is_injection and injection_result.confidence >= 0.9:
        elapsed = (time.monotonic() - start) * 1000
        audit_entry["injection_detected"]  = True
        audit_entry["injection_category"]  = injection_result.category
        audit_entry["blocked"]             = True
        audit_entry["block_reason"]        = "prompt_injection"

        _write_audit_log(audit_entry)
        return GuardResult(
            passed=False,
            flag=BLOCKED_FLAG,
            original_input=user_input,
            processed_input=processed,
            pii_detected=pii_result.has_pii,
            pii_types=pii_result.pii_types,
            injection_detected=True,
            injection_category=injection_result.category,
            block_reason=f"Prompt injection detected: {injection_result.category}",
            latency_ms=round(elapsed, 2),
            audit_entry=audit_entry,
        )

    # ── Step 3: NeMo Semantic Rails (optional) ──────────────────────────────
    nemo = _try_load_nemo(domain)
    if nemo:
        try:
            # FIXED: Added timeout to prevent hanging
            import asyncio
            nemo_response = await asyncio.wait_for(
                nemo.generate_async(
                    messages=[{"role": "user", "content": processed}]
                ),
                timeout=5.0  # 5 second timeout for NeMo
            )
            # NeMo blocked the request if it returned a canned refusal
            blocked_phrases = [
                "i can't assist with that",
                "i'm not able to help",
                "this request violates",
                "i cannot provide",
            ]
            nemo_text = (nemo_response.get("content") or "").lower()
            if any(p in nemo_text for p in blocked_phrases):
                elapsed = (time.monotonic() - start) * 1000
                audit_entry["nemo_blocked"] = True
                _write_audit_log(audit_entry)
                return GuardResult(
                    passed=False,
                    flag=BLOCKED_FLAG,
                    original_input=user_input,
                    processed_input=processed,
                    pii_detected=pii_result.has_pii,
                    pii_types=pii_result.pii_types,
                    injection_detected=False,
                    injection_category=None,
                    block_reason="Request blocked by safety rails",
                    latency_ms=round((time.monotonic() - start) * 1000, 2),
                    audit_entry=audit_entry,
                )
        except asyncio.TimeoutError:
            # FIXED: If NeMo times out, log warning and continue (fail-safe)
            logger.warning(f"NeMo check timed out after 5s for user {user_id} — continuing")
            audit_entry["nemo_timeout"] = True
        except Exception as e:
            logger.warning(f"NeMo check failed (non-fatal): {e}")

    # ── All checks passed ────────────────────────────────────────────────────
    elapsed = (time.monotonic() - start) * 1000
    flag    = REDACTED_FLAG if pii_result.has_pii else SAFE_FLAG

    audit_entry["passed"] = True
    _write_audit_log(audit_entry)

    return GuardResult(
        passed=True,
        flag=flag,
        original_input=user_input,
        processed_input=processed,
        pii_detected=pii_result.has_pii,
        pii_types=pii_result.pii_types,
        injection_detected=injection_result.is_injection,
        injection_category=injection_result.category,
        block_reason=None,
        latency_ms=round(elapsed, 2),
        audit_entry=audit_entry,
    )


async def check_output_response(
    response:     str,
    tool_results: list[dict] | None = None,
    domain:       str = "general",
    user_id:      str = "",
    session_id:   str = "",
) -> OutputGuardResult:
    """
    Run output guardrails on agent's response.
    Returns OutputGuardResult with (possibly modified) safe response.
    """
    start  = time.monotonic()
    result = check_output(response=response, tool_results=tool_results)

    elapsed = (time.monotonic() - start) * 1000
    flag    = SAFE_FLAG if result.is_safe else BLOCKED_FLAG
    if result.hallucination_flag:
        flag = WARNED_FLAG
    if result.pii_types_found:
        flag = REDACTED_FLAG

    _write_audit_log({
        "user_id":          user_id,
        "session_id":       session_id,
        "phase":            "output",
        "is_safe":          result.is_safe,
        "pii_in_response":  bool(result.pii_types_found),
        "hallucination":    result.hallucination_flag,
        "block_reason":     result.reasons,
        "latency_ms":       round(elapsed, 2),
    })

    return OutputGuardResult(
        passed=result.is_safe,
        flag=flag,
        original_response=response,
        processed_response=result.modified_response,
        pii_in_response=bool(result.pii_types_found),
        hallucination_flag=result.hallucination_flag,
        block_reason=result.reasons[0] if result.reasons else None,
        latency_ms=round(elapsed, 2),
    )


def _write_audit_log(entry: dict):
    """
    Write guardrail event to audit log.
    Uses the existing audit_logger (fire-and-forget asyncio.create_task).
    Falls back to structured logger output when no event loop is running (tests).
    """
    import json
    from datetime import datetime, timezone
    entry["timestamp"] = datetime.now(timezone.utc).isoformat()
    logger.info(f"GUARDRAIL_AUDIT: {json.dumps(entry, default=str)}")

    try:
        from backend.audit.audit_logger import log_agent_action
        log_agent_action(
            user_id             = entry.get("user_id", ""),
            workspace_id        = entry.get("workspace_id", ""),
            session_id          = entry.get("session_id", ""),
            trace_id            = entry.get("trace_id", ""),
            action              = f"guardrail:{entry.get('phase', 'unknown')}",
            guardrail_triggered = not entry.get("is_safe", True),
            guardrail_type      = entry.get("block_reason") if isinstance(entry.get("block_reason"), str)
                                  else (entry.get("block_reason") or [""])[0] if entry.get("block_reason") else None,
            pii_detected        = entry.get("pii_in_response", False),
            latency_ms          = int(entry.get("latency_ms", 0)),
            metadata            = {k: v for k, v in entry.items()
                                   if k not in {"user_id", "workspace_id", "session_id", "trace_id"}},
        )
    except Exception as exc:
        logger.debug("Guardrail audit write skipped (no DB pool yet): %s", exc)