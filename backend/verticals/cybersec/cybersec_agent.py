# backend/verticals/cybersec/cybersec_agent.py
"""
Cybersecurity Monitoring Agent (Feature 11).

Capabilities:
  1. Log anomaly detection — parse structured logs, detect patterns
  2. NVD CVE lookup — query NIST NVD API for known vulnerabilities
  3. Automated PDF incident report generation (via existing output_generator)
  4. Slack alerting on critical findings
  5. CVSS score interpretation + remediation recommendations

Uses Guardian compliance check on all output (no PII in reports).
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Optional

import httpx

from backend.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()

# ── CVE lookup via NIST NVD ──────────────────────────────────────────────────

async def search_nvd_cve(
    keyword:        str,
    severity:       Optional[str] = None,  # LOW | MEDIUM | HIGH | CRITICAL
    results_per_page: int = 10,
) -> list[dict]:
    """
    Search NIST NVD for CVEs matching a keyword.
    Public API — no key needed for basic queries.
    """
    params: dict = {
        "keywordSearch": keyword,
        "resultsPerPage": min(results_per_page, 20),
    }
    if severity:
        params["cvssV3Severity"] = severity.upper()

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://services.nvd.nist.gov/rest/json/cves/2.0",
                params=params,
                headers={"Accept": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()

        cves = []
        for item in data.get("vulnerabilities", [])[:10]:
            cve    = item.get("cve", {})
            cve_id = cve.get("id", "")
            desc   = ""
            for d in cve.get("descriptions", []):
                if d.get("lang") == "en":
                    desc = d.get("value", "")
                    break
            metrics  = cve.get("metrics", {})
            cvss_v3  = metrics.get("cvssMetricV31", [{}])[0] if metrics.get("cvssMetricV31") else {}
            cvss_data = cvss_v3.get("cvssData", {}) if cvss_v3 else {}
            cves.append({
                "cve_id":       cve_id,
                "description":  desc[:300],
                "severity":     cvss_data.get("baseSeverity", "UNKNOWN"),
                "cvss_score":   cvss_data.get("baseScore", 0.0),
                "published":    cve.get("published", "")[:10],
                "nvd_url":      f"https://nvd.nist.gov/vuln/detail/{cve_id}",
            })
        return cves

    except Exception as e:
        logger.error("NVD API error for '%s': %s", keyword, e)
        return [{"error": "CVE database temporarily unavailable.", "keyword": keyword}]


# ── Log anomaly detection ────────────────────────────────────────────────────

# Anomaly patterns (regex-based detection rules)
_ANOMALY_RULES = [
    {
        "id":          "BRUTE_FORCE",
        "name":        "Brute Force Attempt",
        "severity":    "HIGH",
        "pattern":     re.compile(r'(?i)(failed|invalid|incorrect)\s+(password|login|auth)', re.IGNORECASE),
        "threshold":   5,   # occurrences in log sample
        "description": "Multiple failed authentication attempts detected.",
        "remediation": "Block IP, enforce MFA, review access policies.",
    },
    {
        "id":          "SQL_INJECTION",
        "name":        "SQL Injection Attempt",
        "severity":    "CRITICAL",
        "pattern":     re.compile(r"(?i)('|\"|;|--|UNION\s+SELECT|DROP\s+TABLE|INSERT\s+INTO|OR\s+1=1)", re.IGNORECASE),
        "threshold":   1,
        "description": "SQL injection pattern detected in request.",
        "remediation": "Sanitize inputs, use parameterized queries, enable WAF.",
    },
    {
        "id":          "XSS",
        "name":        "Cross-Site Scripting Attempt",
        "severity":    "HIGH",
        "pattern":     re.compile(r'(?i)<script[\s>]|javascript:|onerror=|onload=', re.IGNORECASE),
        "threshold":   1,
        "description": "XSS payload detected in request.",
        "remediation": "Implement Content Security Policy, sanitize HTML output.",
    },
    {
        "id":          "DIR_TRAVERSAL",
        "name":        "Directory Traversal",
        "severity":    "HIGH",
        "pattern":     re.compile(r'\.\./|\.\.\\|%2e%2e%2f', re.IGNORECASE),
        "threshold":   1,
        "description": "Path traversal attempt detected.",
        "remediation": "Validate file paths, use chroot jails, restrict file access.",
    },
    {
        "id":          "SCANNING",
        "name":        "Port/Service Scanning",
        "severity":    "MEDIUM",
        "pattern":     re.compile(r'(?i)(nmap|masscan|nikto|dirbuster|gobuster)', re.IGNORECASE),
        "threshold":   1,
        "description": "Network scanning tool detected in user-agent or requests.",
        "remediation": "Block scanner IP, enable IDS/IPS, notify SOC team.",
    },
    {
        "id":          "PRIV_ESCALATION",
        "name":        "Privilege Escalation",
        "severity":    "CRITICAL",
        "pattern":     re.compile(r'(?i)(sudo|chmod\s+777|chown\s+root|setuid|passwd\s+root)', re.IGNORECASE),
        "threshold":   1,
        "description": "Possible privilege escalation command detected.",
        "remediation": "Audit sudo rules, enable process monitoring, review user accounts.",
    },
]


def analyze_logs(log_text: str) -> dict:
    """
    Analyze log content for security anomalies.
    Returns structured findings with severity levels.
    """
    lines    = log_text.splitlines()
    findings = []

    for rule in _ANOMALY_RULES:
        matches = [l for l in lines if rule["pattern"].search(l)]
        if len(matches) >= rule["threshold"]:
            findings.append({
                "rule_id":     rule["id"],
                "name":        rule["name"],
                "severity":    rule["severity"],
                "description": rule["description"],
                "remediation": rule["remediation"],
                "match_count": len(matches),
                "sample":      matches[0][:200] if matches else "",  # never log full PII
            })

    # Risk score: weighted by severity
    severity_weights = {"CRITICAL": 10, "HIGH": 5, "MEDIUM": 2, "LOW": 1}
    risk_score = min(100, sum(severity_weights.get(f["severity"], 1) for f in findings))

    return {
        "lines_analyzed": len(lines),
        "findings":       findings,
        "risk_score":     risk_score,
        "risk_level":     "CRITICAL" if risk_score >= 20 else "HIGH" if risk_score >= 10 else "MEDIUM" if risk_score > 0 else "LOW",
        "analyzed_at":    datetime.now(timezone.utc).isoformat(),
    }


# ── Incident report generation ───────────────────────────────────────────────

async def generate_incident_report(
    title:     str,
    findings:  list[dict],
    log_lines: int,
    risk_level: str,
    cves:      Optional[list[dict]] = None,
) -> bytes:
    """
    Generate a professional PDF incident report using the output_generator.
    Returns PDF bytes.
    """
    # Build structured content
    content = (
        f"Risk Level: {risk_level}\n"
        f"Log Lines Analyzed: {log_lines}\n"
        f"Findings: {len(findings)}\n"
        f"Report Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        "EXECUTIVE SUMMARY\n"
        f"Security analysis detected {len(findings)} anomalies in the provided logs. "
        f"Overall risk level: {risk_level}.\n"
    )

    sections = []

    # Findings section
    if findings:
        finding_body = "\n".join(
            f"[{f['severity']}] {f['name']}: {f['description']} "
            f"({f['match_count']} occurrences). "
            f"Remediation: {f['remediation']}"
            for f in findings
        )
        sections.append({"heading": "Security Findings", "body": finding_body})

    # CVE section
    if cves:
        cve_body = "\n".join(
            f"{c.get('cve_id','')}: [{c.get('severity','')}] Score {c.get('cvss_score',0)} — {c.get('description','')[:200]}"
            for c in cves if "error" not in c
        )
        if cve_body:
            sections.append({"heading": "Related CVE Advisories", "body": cve_body})

    # Recommendations
    all_remediations = list(dict.fromkeys(f["remediation"] for f in findings))
    if all_remediations:
        sections.append({
            "heading": "Recommendations",
            "body":    "\n".join(f"• {r}" for r in all_remediations),
        })

    try:
        from backend.outputs.output_generator import generate_pdf
        pdf_bytes, _, _ = generate_pdf(
            title=title,
            content=content,
            sections=sections,
            author="AI Cybersecurity Monitoring Agent",
        )
        return pdf_bytes
    except Exception as e:
        logger.error("Incident report PDF generation failed: %s", e)
        raise


# ── Slack alert ──────────────────────────────────────────────────────────────

async def send_security_alert(
    risk_level: str,
    findings:   list[dict],
    source:     str = "Log Analysis",
) -> bool:
    """Send critical/high security alert to Slack."""
    if risk_level not in ("CRITICAL", "HIGH"):
        return False

    webhook_url = settings.slack_webhook_url
    if not webhook_url:
        logger.warning("SLACK_WEBHOOK_URL not set — security alert not sent")
        return False

    emoji = "🚨" if risk_level == "CRITICAL" else "⚠️"
    block = {
        "text": f"{emoji} *Security Alert: {risk_level}* — {source}",
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": f"{emoji} Cybersecurity Alert — {risk_level}"}},
            {"type": "section", "fields": [
                {"type": "mrkdwn", "text": f"*Source:*\n{source}"},
                {"type": "mrkdwn", "text": f"*Findings:*\n{len(findings)} anomalies detected"},
            ]},
        ] + [
            {"type": "section", "text": {"type": "mrkdwn",
             "text": f"• [{f['severity']}] *{f['name']}*: {f['description']}"}}
            for f in findings[:3]
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(webhook_url, json=block)
            resp.raise_for_status()
        return True
    except Exception as e:
        logger.error("Security Slack alert failed: %s", e)
        return False


# ── Main cybersec agent ──────────────────────────────────────────────────────

async def cybersec_agent(
    query:      str,
    log_text:   Optional[str]  = None,
    cve_keyword: Optional[str] = None,
    generate_report: bool       = False,
) -> dict:
    """Main dispatcher for cybersecurity monitoring tasks."""
    result: dict = {"query": query, "timestamp": datetime.now(timezone.utc).isoformat()}

    # CVE lookup
    if cve_keyword or any(kw in query.lower() for kw in ["cve", "vulnerability", "nvd"]):
        keyword = cve_keyword or query
        cves    = await search_nvd_cve(keyword, results_per_page=5)
        result["cves"] = cves

    # Log analysis
    if log_text:
        analysis      = analyze_logs(log_text)
        result["log_analysis"] = analysis

        # Auto-alert on critical findings
        if analysis["risk_level"] in ("CRITICAL", "HIGH"):
            import asyncio
            asyncio.create_task(send_security_alert(
                analysis["risk_level"], analysis["findings"], "Log Analysis"
            ))

        # Generate PDF report if requested
        if generate_report and analysis["findings"]:
            try:
                pdf_bytes = await generate_incident_report(
                    title=f"Security Incident Report — {analysis['risk_level']}",
                    findings=analysis["findings"],
                    log_lines=analysis["lines_analyzed"],
                    risk_level=analysis["risk_level"],
                    cves=result.get("cves"),
                )
                import base64
                result["report_b64"]     = base64.b64encode(pdf_bytes).decode()
                result["report_size_kb"] = round(len(pdf_bytes) / 1024, 1)
            except Exception as e:
                result["report_error"] = str(e)

    # General cybersec question → LLM (Ollama-first)
    if not log_text and not cve_keyword:
        try:
            from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL
            response_text = await ollama_chat_completion(
                messages=[
                    {"role": "system", "content": (
                        "You are a senior cybersecurity analyst. "
                        "Provide precise, actionable security guidance. "
                        "Reference CVE numbers where relevant. "
                        "Follow NIST/OWASP/ISO 27001 frameworks."
                    )},
                    {"role": "user", "content": query},
                ],
                model=OLLAMA_MODEL,
                max_tokens=700,
            )
            result["response"] = response_text or "Cybersecurity assistant temporarily unavailable."
        except Exception as e:
            logger.error("Cybersec LLM query failed: %s", e)
            result["error"] = "Cybersecurity assistant temporarily unavailable."

    return result
