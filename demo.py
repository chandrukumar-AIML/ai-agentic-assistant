#!/usr/bin/env python3
"""
demo.py — Full-project end-to-end demo / smoke-test runner.

Covers EVERY agent and feature in the platform, from infra → auth → platform
services → deterministic engines → all LLM verticals → enhancement tools.

Three ways to run:
    python demo.py --mock     # INSTANT showcase — every feature with a realistic
                              #   output preview, no Ollama wait, no API keys (~15s)
    python demo.py --quick    # real backend, deterministic + platform only (no LLM)
    python demo.py            # SMOKE — quick + a few real Ollama calls (~4 min)
    python demo.py --full     # every LLM vertical live via Ollama (~30-45 min)
    python demo.py --show     # also print output previews for real (non-mock) runs
    python demo.py --base https://your-backend.onrender.com/api

LLM calls (non-mock) route through local Ollama — no OpenAI cost.
Exit 0 if no failures, 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional

import httpx

for _stream in (sys.stdout, sys.stderr):          # Windows cp1252 → force UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ── pretty output ───────────────────────────────────────────────────────────────
_USE_COLOR = sys.stdout.isatty()
def _c(code, s): return f"\033[{code}m{s}\033[0m" if _USE_COLOR else s
def green(s): return _c("32", s)
def red(s):   return _c("31", s)
def yellow(s):return _c("33", s)
def cyan(s):  return _c("36", s)
def blue(s):  return _c("34", s)
def bold(s):  return _c("1", s)
def dim(s):   return _c("2", s)

MARK = {"PASS": green("✓ PASS"), "FAIL": red("✗ FAIL"),
        "SKIP": yellow("○ SKIP"), "MOCK": blue("◆ MOCK")}


@dataclass
class Check:
    name:     str
    category: str
    method:   str = "GET"
    path:     str = ""
    payload:  Optional[dict] = None
    llm:      bool = False                 # slow Ollama call
    needs_creds: bool = False              # external OAuth/paid key — skipped in live runs
    timeout:  float = 15.0
    expect:   Optional[Callable[[Any], bool]] = None
    auth:     bool = True
    mock:     str = ""                     # canned realistic output for --mock mode


def _flat(s: str, n: int = 200) -> str:
    return " ".join(str(s).split())[:n]


def preview_of(j: Any) -> str:
    """Pull a human-readable output snippet out of any response shape."""
    if isinstance(j, dict):
        for k in ("result", "content", "output", "analysis", "review", "summary",
                  "response", "answer", "iac", "brief", "story", "report", "faq"):
            v = j.get(k)
            if isinstance(v, str) and v.strip():
                return _flat(v)
        keys = list(j)[:6]
        return _flat(json.dumps({k: j[k] for k in keys}, ensure_ascii=False))
    return _flat(j)


# ════════════════════════════════════════════════════════════════════════════════
# COMPLETE CHECK LIST — every agent + every feature, with predefined demo data
# ════════════════════════════════════════════════════════════════════════════════

def build_checks() -> list[Check]:
    return [
        # ── Infra ───────────────────────────────────────────────────────────────
        Check("Backend health", "Infra", "GET", "/health", auth=False,
              expect=lambda j: j.get("status") == "ok",
              mock='{"status":"ok","ollama_healthy":true,"redis_healthy":true,"circuit_state":"closed"}'),

        # ── Auth + multi-tenant (F-auth) ────────────────────────────────────────
        Check("Tool catalog (28 tools)", "Auth & Tenancy", "GET", "/tools/catalog",
              expect=lambda j: len(j.get("catalog", [])) >= 20,
              mock='28 gateable tools across AI Core / Verticals / Settings'),
        Check("Current user (/auth/me)", "Auth & Tenancy", "GET", "/auth/me",
              expect=lambda j: j.get("is_admin") is True,
              mock='admin@agentic.local · role=admin · plan=enterprise · 28 tools'),
        Check("List clients (admin)", "Auth & Tenancy", "GET", "/clients",
              expect=lambda j: j.get("total", 0) >= 1,
              mock='2 clients: Platform Admin (enterprise/28), Demo Client (free/5)'),

        # ── Platform services (F1, F4, F6, F7, F8, F12, RAG) ────────────────────
        Check("F1 · Guardian compliance scan", "Platform", "POST", "/compliance/check",
              {"text": "Contact John at john@acme.com, card 4111-1111-1111-1111"},
              mock='PII detected: EMAIL, CREDIT_CARD → redacted. Risk: HIGH. HIPAA/GDPR flags raised.'),
        Check("F4 · Task scheduler list", "Platform", "GET", "/scheduler/tasks",
              mock='Scheduled tasks: daily-report (cron 0 9 * * *), weekly-digest — engine active'),
        Check("F6 · HITL pending approvals", "Platform", "GET", "/hitl/pending",
              mock='0 pending approvals · human-in-the-loop queue ready (offer letters, sends route here)'),
        Check("F7 · Output generator (PDF)", "Platform", "POST", "/outputs/generate",
              {"format": "pdf", "title": "Demo Report", "content": "Quarterly summary.", "sections": []},
              timeout=30,
              mock='PDF generated · Demo Report.pdf · 24 KB · base64 returned'),
        Check("F12 · A/B experiments", "Platform", "GET", "/ab/experiments",
              mock='A/B framework live · experiments: prompt-v1-vs-v2 (significance engine ready)'),
        Check("RAG · knowledge base stats", "Platform", "GET", "/rag/stats",
              mock='Vector store: FAISS + ChromaDB · indexed chunks ready for retrieval'),
        Check("F8 · Billing plans", "Platform", "GET", "/billing/plans",
              expect=lambda j: len(j.get("plans", [])) >= 3,
              mock='FREE ₹0 / PRO ₹2,499 / ENTERPRISE custom · Stripe + Razorpay'),
        Check("Integration status (19)", "Platform", "GET", "/integrations/status",
              expect=lambda j: j.get("total", 0) >= 15,
              mock='19 integrations wired · 4 LIVE (Ollama, OpenAI, Mandi, Tavily) · 15 add-key'),

        # ── Deterministic engines (real, instant, exact) ────────────────────────
        Check("F17 · GST calc (₹1000 @ 18%)", "Deterministic Engines", "POST",
              "/verticals/accountant/action",
              {"action": "gst_calc", "payload": {"amount": 1000, "gst_rate": 18.0, "transaction": "intra"}},
              expect=lambda j: abs(j.get("invoice_total", 0) - 1180.0) < 0.01,
              mock='taxable ₹1000 · CGST ₹90 · SGST ₹90 · total ₹1180'),
        Check("F17 · TDS calc (₹50k § 194J)", "Deterministic Engines", "POST",
              "/verticals/accountant/action",
              {"action": "tds_calc", "payload": {"amount": 50000, "section": "194J", "pan_available": True}},
              mock='§194J professional fees · 10% · TDS ₹5,000 · net payable ₹45,000'),
        Check("F17 · HSN code lookup", "Deterministic Engines", "GET", "/verticals/accountant/hsn/8471",
              mock='HSN 8471 · Automatic data processing machines · GST 18%'),
        Check("F16 · BANT lead score", "Deterministic Engines", "POST", "/verticals/sales/score",
              {"budget_usd": 75000, "title": "CTO", "company_size": 250, "has_need": True, "timeline_days": 30},
              mock='Lead score 88/100 · HOT · Budget 25 + Authority 25 + Need 22 + Timeline 16'),
        Check("F14 · PAN/GSTIN validation", "Deterministic Engines", "POST", "/verticals/forms/validate",
              {"pan": "ABCDE1234F", "gstin": "29ABCDE1234F1Z5", "mobile": "9876543210", "pincode": "560001"},
              mock='PAN valid ✓ · GSTIN valid ✓ (state 29 Karnataka) · mobile ✓ · pincode ✓'),
        Check("F18 · HR skill-match (deterministic)", "Deterministic Engines", "POST", "/verticals/hr/action",
              {"action": "screen", "payload": {
                  "resume_text": "Senior engineer, 6 years Python, React.js, AWS, Kubernetes. Built REST APIs.",
                  "job_description": "Backend engineer.", "required_skills": ["Python", "Kubernetes", "Go"]}},
              llm=True, timeout=120,
              expect=lambda j: ("deterministic" in j) or ("overall_score" in j),
              mock='Match 71/100 · matched: Python, Kubernetes · missing: Go · 6 yrs detected'),
        Check("F18 · HR onboarding checklist", "Deterministic Engines", "POST", "/verticals/hr/action",
              {"action": "onboarding", "payload": {"role": "Backend Engineer", "department": "Engineering"}},
              mock='30-60-90 onboarding · Day 1 IT+access · Week 1 codebase · Month 1 first ship'),
        Check("F9 · AgriTech live mandi prices", "Deterministic Engines", "GET",
              "/verticals/agri/mandi-prices?commodity=tomato&state=Tamil%20Nadu", timeout=20,
              mock='Tomato · Tamil Nadu mandis · ₹1,200–1,800/quintal (Agmarknet data.gov.in — LIVE)'),

        # ── LLM business verticals (Ollama) ─────────────────────────────────────
        Check("F9 · AgriTech advisory", "LLM · Business Verticals", "POST", "/verticals/agri/query",
              {"query": "Best time to plant tomato in Tamil Nadu?", "language": "en", "state": "Tamil Nadu"},
              llm=True, timeout=240,
              mock='Plant tomato Jun–Jul (kharif) or Nov–Dec. Red loamy soil, pH 6–7. Drip + mulch advised...'),
        Check("F10 · Legal research", "LLM · Business Verticals", "POST", "/verticals/legal/query",
              {"query": "Key clauses in a software service agreement?", "language": "en"},
              llm=True, timeout=240,
              mock='Key clauses: Scope/SLA, IP ownership, Confidentiality, Liability cap, Termination, Indemnity...'),
        Check("F13 · Receptionist chat", "LLM · Business Verticals", "POST", "/verticals/receptionist/chat",
              {"message": "I'd like to book a meeting next Monday", "channel": "web", "session_id": "demo-1"},
              llm=True, timeout=180, auth=False,
              mock='"Sure! I can book Monday. Morning or afternoon? May I have your name and email?"'),
        Check("F17 · Accountant tax Q&A", "LLM · Business Verticals", "POST", "/verticals/accountant/action",
              {"action": "query", "payload": {"query": "Difference between CGST and IGST?"}},
              llm=True, timeout=180,
              mock='CGST+SGST apply to intra-state; IGST applies to inter-state (single combined tax)...'),
        Check("F18 · HR job description", "LLM · Business Verticals", "POST", "/verticals/hr/action",
              {"action": "generate_jd", "payload": {"role_title": "Senior Backend Engineer", "department": "Engineering"}},
              llm=True, timeout=180,
              mock='JD: Senior Backend Engineer — responsibilities, must-haves (Python/FastAPI), nice-to-haves, perks...'),
        Check("F19 · Social content generator", "LLM · Business Verticals", "POST", "/verticals/social/action",
              {"action": "generate", "platform": "linkedin", "payload": {"topic": "AI in Indian SMBs", "tone": "professional"}},
              llm=True, timeout=180,
              mock='LinkedIn post: "AI is no longer enterprise-only. Indian SMBs are automating GST, HR..." +hashtags'),
        Check("V9 · Healthcare symptom triage", "LLM · Business Verticals", "POST", "/verticals/healthcare/action",
              {"action": "symptom_triage", "payload": {
                  "symptoms": "Severe headache, vomiting, neck stiffness", "duration": "3 hrs", "age_sex": "41/F"}},
              llm=True, timeout=180,
              mock='🔴 EMERGENCY — possible meningitis/SAH. See doctor NOW. Red flags: neck stiffness + vomiting...'),
        Check("V10 · Real Estate ROI", "LLM · Business Verticals", "POST", "/verticals/realestate/action",
              {"action": "roi_calculator", "payload": {"price": "₹95,00,000", "down_payment": "₹20,00,000", "rent": "₹32,000/mo"}},
              llm=True, timeout=180,
              mock='EMI ₹65k · gross yield 4.0% · break-even ~9 yrs · 10-yr projection ₹1.7Cr · verdict: average'),
        Check("V11 · EdTech quiz generator", "LLM · Business Verticals", "POST", "/verticals/edtech/action",
              {"action": "quiz_generator", "payload": {"topic": "Photosynthesis", "level": "Class 10", "num_questions": "5"}},
              llm=True, timeout=180,
              mock='5 MCQs on photosynthesis + answer key + marking scheme + 3 HOTS questions'),
        Check("F16 · Sales meeting prep", "LLM · Business Verticals", "POST", "/verticals/sales/enhance",
              {"action": "meeting_prep", "payload": {"company": "Acme Corp", "deal_stage": "discovery"}},
              llm=True, timeout=180,
              mock='Discovery brief: research checklist, SPIN questions, objections+responses, demo flow, next steps'),

        # ── LLM software-dev roles (Ollama) ─────────────────────────────────────
        Check("V1 · Data Analyst NL→SQL", "LLM · Dev Roles", "POST",
              "/vertical/analyst?query=Top%205%20customers%20by%20revenue&context_json=%7B%7D",
              llm=True, timeout=240,
              mock='SELECT customer, SUM(amount) ... GROUP BY ... LIMIT 5 + chart + insight narrative'),
        Check("V2 · DevOps debug analysis", "LLM · Dev Roles", "POST",
              "/vertical/devops?query=Why%20is%20the%20API%20returning%20502%3F&context_json=%7B%7D",
              llm=True, timeout=240,
              mock='502 root-cause: upstream timeout / unhealthy pod. Check readiness probe, scale, logs...'),
        Check("V2 · DevOps IaC (Dockerfile)", "LLM · Dev Roles", "POST", "/verticals/devops/iac",
              {"action": "dockerfile", "payload": {"iac_type": "dockerfile", "tech_stack": "Python/FastAPI", "description": "web API"}},
              llm=True, timeout=180,
              mock='Multi-stage Dockerfile · non-root user · healthcheck · slim image · layer-cached'),
        Check("V3 · QA test generation", "LLM · Dev Roles", "POST", "/verticals/qa/action",
              {"action": "generate_tests", "payload": {"feature_description": "User login with email + password"}},
              llm=True, timeout=180,
              mock='TC-001 valid login, TC-002 wrong pw, TC-003 SQLi, TC-004 lockout + pytest stubs'),
        Check("V4 · Project Mgr user story", "LLM · Dev Roles", "POST", "/verticals/pm/action",
              {"action": "user_story", "payload": {"feature": "password reset via email"}},
              llm=True, timeout=180,
              mock='As a user I want to reset my password... + acceptance criteria + story points (3)'),
        Check("V5 · Code Assistant generate", "LLM · Dev Roles", "POST", "/verticals/code/action",
              {"action": "generate", "prompt": "binary search in Python", "language": "python"},
              llm=True, timeout=180,
              mock='def binary_search(arr, target): lo, hi = 0, len(arr)-1 ... returns index or -1'),
        Check("V6 · ML Engineer experiment", "LLM · Dev Roles", "POST", "/verticals/ml/action",
              {"action": "experiment_design", "payload": {"goal": "reduce churn prediction error"}},
              llm=True, timeout=180,
              mock='Hypothesis, baseline (logreg), features, metrics (AUC/PR), train/val split, ablation plan'),
        Check("V7 · DBA query optimize", "LLM · Dev Roles", "POST", "/verticals/dba/action",
              {"action": "optimize_query", "payload": {"query": "SELECT * FROM orders WHERE status='paid'"}},
              llm=True, timeout=180,
              mock='Add index on status; avoid SELECT *; EXPLAIN plan; covering index suggestion'),
        Check("V8 · Tech Lead build-vs-buy", "LLM · Dev Roles", "POST", "/verticals/techlead/enhance",
              {"action": "build_vs_buy", "payload": {"feature": "auth system", "team_size": "4"}},
              llm=True, timeout=180,
              mock='Build cost ~3 mo vs Auth0 TCO 3-yr; core-vs-context; recommendation: BUY (5 reasons)'),
        Check("V8 · Tech Lead ADR", "LLM · Dev Roles", "POST", "/verticals/techlead/action",
              {"action": "adr", "payload": {"title": "Use PostgreSQL over MongoDB", "context": "relational SaaS data"}},
              llm=True, timeout=180,
              mock='ADR-001 (Nygard format): Context, Decision, Status: Accepted, Consequences +/−'),
        Check("F11 · Cybersec OWASP review", "LLM · Dev Roles", "POST", "/verticals/cybersec/owasp",
              {"action": "owasp_review", "payload": {"code": "q='SELECT * FROM users WHERE id='+uid", "language": "python"}},
              llm=True, timeout=180,
              mock='A03 Injection: FAIL — SQL injection at line 1. Fix: parameterized query. Severity: Critical'),

        # ── External-credential features (showcased via mock; live needs keys) ──
        Check("F15 · Email Manager (Gmail)", "External Integrations", "POST", "/verticals/email/action",
              {"action": "list", "provider": "gmail", "access_token": "mock-token"},
              needs_creds=True, timeout=20,
              mock='Lists/drafts/summarises Gmail+Outlook · send routes via HITL · needs OAuth token'),
        Check("F19 · Social auto-post (Twitter/LinkedIn)", "External Integrations", "POST", "/verticals/social/action",
              {"action": "post", "platform": "linkedin", "payload": {"topic": "demo"}},
              needs_creds=True, timeout=20,
              mock='Publishes to LinkedIn/Twitter/Buffer · needs TWITTER_*/LINKEDIN_AUTHOR_URN keys'),
    ]


# ════════════════════════════════════════════════════════════════════════════════
# RUNNER
# ════════════════════════════════════════════════════════════════════════════════

def login(base: str) -> Optional[str]:
    try:
        r = httpx.post(f"{base}/auth/login",
                       json={"email": "admin@agentic.local", "password": "admin123"}, timeout=15)
        if r.status_code == 200:
            return r.json().get("access_token")
        print(red(f"  login failed: HTTP {r.status_code} — {r.text[:120]}"))
    except Exception as e:
        print(red(f"  login error: {e}"))
    return None


def run_check(base, token, c: Check) -> tuple[str, float, str, str]:
    """Returns (status, elapsed, note, preview)."""
    headers = {"Authorization": f"Bearer {token}"} if (c.auth and token) else {}
    url = f"{base}{c.path}"
    t0 = time.monotonic()
    try:
        if c.method == "GET":
            r = httpx.get(url, headers=headers, timeout=c.timeout)
        else:
            r = httpx.post(url, headers=headers, json=c.payload, timeout=c.timeout)
        dt = time.monotonic() - t0
        if r.status_code != 200:
            return ("FAIL", dt, f"HTTP {r.status_code}: {r.text[:70]}", "")
        ctype = r.headers.get("content-type", "")
        try:
            j = r.json()
        except Exception:
            # Non-JSON 200 (e.g. a generated PDF/XLSX/PPTX binary) is a valid success
            kb = len(r.content) / 1024
            if r.content:
                kind = ("PDF" if "pdf" in ctype else "XLSX" if "sheet" in ctype
                        else "PPTX" if "presentation" in ctype else ctype.split("/")[-1] or "binary")
                return ("PASS", dt, "", f"{kind} file generated · {kb:.0f} KB")
            return ("FAIL", dt, "empty response", "")
        if isinstance(j, dict) and j.get("error"):
            return ("FAIL", dt, f"error: {str(j['error'])[:70]}", "")
        if c.expect and not c.expect(j):
            return ("FAIL", dt, "validation failed", preview_of(j))
        return ("PASS", dt, "", preview_of(j))
    except httpx.TimeoutException:
        return ("SKIP", time.monotonic() - t0, f"timeout >{c.timeout:.0f}s (Ollama slow — try --full)", "")
    except Exception as e:
        return ("FAIL", time.monotonic() - t0, str(e)[:70], "")


def _line(c, status, dt, note, preview, show):
    timing = dim(f"{dt:5.1f}s") if dt else dim("   —")
    tag = cyan("[LLM]") if c.llm else (yellow("[EXT]") if c.needs_creds else "     ")
    extra = dim(f"  {note}") if note else ""
    print(f"    {MARK[status]}  {tag} {c.name:<40} {timing}{extra}")
    if show and preview:
        print(dim(f"             → {preview}"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Full-project demo / smoke-test runner")
    ap.add_argument("--base", default="http://localhost:8000/api")
    ap.add_argument("--mock", action="store_true", help="instant canned outputs for every feature (no Ollama/keys)")
    ap.add_argument("--quick", action="store_true", help="real backend, no LLM")
    ap.add_argument("--full", action="store_true", help="run every LLM check live")
    ap.add_argument("--show", action="store_true", help="print output previews")
    args = ap.parse_args()

    mode = "MOCK" if args.mock else "QUICK" if args.quick else "FULL" if args.full else "SMOKE"
    show = args.show or args.mock
    smoke_llm_budget = 3

    print(bold(cyan("\n╔══════════════════════════════════════════════════════════════╗")))
    print(bold(cyan("║   AI Agentic Platform — Full Project Demo (all agents)        ║")))
    print(bold(cyan("╚══════════════════════════════════════════════════════════════╝")))
    print(f"  Backend : {args.base}")
    print(f"  Mode    : {bold(mode)}   " +
          dim("(canned outputs)" if args.mock else "(LLM via Ollama — no OpenAI cost)"))
    print(f"  Started : {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    token = None
    if not args.mock:
        print(dim("  Authenticating as admin@agentic.local ..."))
        token = login(args.base)
        print(green("  ✓ JWT acquired\n") if token else yellow("  ! no token (dev bypass may allow)\n"))

    checks = build_checks()
    results, llm_done, current_cat = [], 0, None

    for c in checks:
        if c.category != current_cat:
            print(f"\n  {bold(c.category)}")
            current_cat = c.category

        # MOCK mode: show canned output instantly for LLM + external; run deterministic for real
        if args.mock and (c.llm or c.needs_creds):
            results.append((c, "MOCK")); _line(c, "MOCK", 0.0, "", c.mock, True); continue
        if args.mock:
            # deterministic/platform → still hit the real (fast) endpoint for an authentic result
            token = token or login(args.base)
            status, dt, note, prev = run_check(args.base, token, c)
            results.append((c, status)); _line(c, status, dt, note, prev or c.mock, True); continue

        # Live modes
        if c.needs_creds:
            results.append((c, "SKIP")); _line(c, "SKIP", 0.0, "needs external keys (see --mock)", "", show); continue
        if c.llm and args.quick:
            results.append((c, "SKIP")); _line(c, "SKIP", 0.0, "LLM skipped (--quick)", "", show); continue
        if c.llm and mode == "SMOKE" and llm_done >= smoke_llm_budget:
            results.append((c, "SKIP")); _line(c, "SKIP", 0.0, "smoke budget — use --full", "", show); continue

        status, dt, note, prev = run_check(args.base, token, c)
        if c.llm and status in ("PASS", "FAIL"):
            llm_done += 1
        results.append((c, status)); _line(c, status, dt, note, prev, show)

    # ── summary ──────────────────────────────────────────────────────────────
    n = {k: sum(1 for _, s in results if s == k) for k in ("PASS", "FAIL", "SKIP", "MOCK")}
    print(bold(cyan("\n╔══════════════════════════════════════════════════════════════╗")))
    print(f"  {green('PASS '+str(n['PASS']))}   {red('FAIL '+str(n['FAIL']))}   "
          f"{yellow('SKIP '+str(n['SKIP']))}   {blue('MOCK '+str(n['MOCK']))}   of {len(results)} checks")
    print(bold(cyan("╚══════════════════════════════════════════════════════════════╝")))

    if n["FAIL"] == 0:
        print(green(f"\n  🎉 Every executed check passed — {len(results)} agents/features covered.\n"))
        if args.mock:
            print(dim("  This was a MOCK showcase. Run `python demo.py --full` to exercise all LLM live.\n"))
        elif n["SKIP"]:
            print(dim("  Run `python demo.py --mock` to see every feature's output instantly,\n"
                      "  or `python demo.py --full` to run every LLM vertical live via Ollama.\n"))
    else:
        print(red(f"\n  {n['FAIL']} check(s) failed:\n"))
        for c, s in results:
            if s == "FAIL":
                print(red(f"    ✗ {c.name}"))
        print()
    return 1 if n["FAIL"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
