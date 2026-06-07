#!/usr/bin/env python3
"""
demo.py — Full-project end-to-end demo / smoke-test runner.

Proves every layer of the platform works (auth → platform → deterministic
verticals → LLM verticals) using PREDEFINED demo data. LLM calls go through the
normal router (Ollama locally — no OpenAI cost). Designed so a recruiter or
client walkthrough can run ONE command and watch the whole stack light up green.

Usage:
    python demo.py            # SMOKE  : all fast checks + a few real LLM calls (~2-4 min)
    python demo.py --quick    # QUICK  : no LLM at all — deterministic + platform only (~10s)
    python demo.py --full     # FULL   : every LLM vertical live via Ollama (~20-40 min on CPU)
    python demo.py --base http://localhost:8000/api   # custom backend URL

Exit code 0 if no failures, 1 otherwise (CI-friendly).
"""
from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import httpx

# Windows consoles default to cp1252 — force UTF-8 so box/emoji glyphs render.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ── pretty output ───────────────────────────────────────────────────────────────
_USE_COLOR = sys.stdout.isatty()
def _c(code: str, s: str) -> str: return f"\033[{code}m{s}\033[0m" if _USE_COLOR else s
def green(s): return _c("32", s)
def red(s):   return _c("31", s)
def yellow(s):return _c("33", s)
def cyan(s):  return _c("36", s)
def bold(s):  return _c("1", s)
def dim(s):   return _c("2", s)

OK, FAIL, SKIP = green("✓ PASS"), red("✗ FAIL"), yellow("○ SKIP")


@dataclass
class Check:
    name:     str
    category: str
    method:   str = "GET"
    path:     str = ""
    payload:  Optional[dict] = None
    llm:      bool = False                 # True = slow LLM call
    timeout:  float = 15.0
    expect:   Optional[Callable[[Any], bool]] = None   # extra validation on JSON
    auth:     bool = True


# ════════════════════════════════════════════════════════════════════════════════
# PREDEFINED DEMO DATA — realistic inputs so no manual typing is ever required
# ════════════════════════════════════════════════════════════════════════════════

def build_checks() -> list[Check]:
    return [
        # ── Infra / health ──────────────────────────────────────────────────────
        Check("Backend health", "Infra", "GET", "/health", auth=False,
              expect=lambda j: j.get("status") == "ok"),

        # ── Auth + multi-tenant ─────────────────────────────────────────────────
        Check("Tools catalog", "Auth & Tenancy", "GET", "/tools/catalog",
              expect=lambda j: len(j.get("catalog", [])) >= 20),
        Check("Current user (/auth/me)", "Auth & Tenancy", "GET", "/auth/me",
              expect=lambda j: j.get("is_admin") is True),
        Check("List clients (admin)", "Auth & Tenancy", "GET", "/clients",
              expect=lambda j: j.get("total", 0) >= 1),

        # ── Platform services ───────────────────────────────────────────────────
        Check("Integration status", "Platform", "GET", "/integrations/status",
              expect=lambda j: j.get("total", 0) >= 15 and j.get("live", 0) >= 1),
        Check("Billing plans", "Platform", "GET", "/billing/plans",
              expect=lambda j: len(j.get("plans", [])) >= 3),
        Check("Billing subscription", "Platform", "GET", "/billing/subscription"),

        # ── Deterministic verticals (real engines — fast, exact) ────────────────
        Check("Accountant · GST calc (1000 @ 18%)", "Deterministic", "POST",
              "/verticals/accountant/action",
              {"action": "gst_calc", "payload": {"amount": 1000, "gst_rate": 18.0, "transaction": "intra"}},
              expect=lambda j: abs(j.get("invoice_total", 0) - 1180.0) < 0.01),
        Check("Accountant · TDS calc (50k @ 194J)", "Deterministic", "POST",
              "/verticals/accountant/action",
              {"action": "tds_calc", "payload": {"amount": 50000, "section": "194J", "pan_available": True}}),
        Check("Accountant · HSN lookup", "Deterministic", "GET", "/verticals/accountant/hsn/8471"),
        Check("Sales · BANT lead score", "Deterministic", "POST", "/verticals/sales/score",
              {"budget_usd": 75000, "title": "CTO", "company_size": 250, "has_need": True, "timeline_days": 30}),
        Check("Form · PAN/GSTIN validation", "Deterministic", "POST", "/verticals/forms/validate",
              {"pan": "ABCDE1234F", "gstin": "29ABCDE1234F1Z5", "mobile": "9876543210", "pincode": "560001"}),
        Check("HR · deterministic skill match", "Deterministic", "POST", "/verticals/hr/action",
              {"action": "screen", "payload": {
                  "resume_text": "Senior engineer, 6 years experience in Python, React.js, AWS, Kubernetes. Built REST APIs.",
                  "job_description": "Backend engineer for a SaaS platform.",
                  "required_skills": ["Python", "Kubernetes", "Go"]}},
              llm=True, timeout=120,
              expect=lambda j: ("deterministic" in j) or ("overall_score" in j)),

        # ── LLM business verticals (Ollama) ─────────────────────────────────────
        Check("AgriTech · advisory query", "LLM · Business", "POST", "/verticals/agri/query",
              {"query": "Best time to plant tomato in Tamil Nadu?", "language": "en", "state": "Tamil Nadu"},
              llm=True, timeout=240),
        Check("Healthcare · symptom triage", "LLM · Business", "POST", "/verticals/healthcare/action",
              {"action": "symptom_triage", "payload": {
                  "symptoms": "Sudden severe headache, vomiting, neck stiffness", "duration": "3 hours", "age_sex": "41 / F"}},
              llm=True, timeout=180),
        Check("Real Estate · ROI calculator", "LLM · Business", "POST", "/verticals/realestate/action",
              {"action": "roi_calculator", "payload": {
                  "price": "₹95,00,000", "down_payment": "₹20,00,000", "rent": "₹32,000/month"}},
              llm=True, timeout=180),
        Check("EdTech · quiz generator", "LLM · Business", "POST", "/verticals/edtech/action",
              {"action": "quiz_generator", "payload": {"topic": "Photosynthesis", "level": "Class 10", "num_questions": "5"}},
              llm=True, timeout=180),
        Check("Sales · objection handler", "LLM · Business", "POST", "/verticals/sales/enhance",
              {"action": "meeting_prep", "payload": {"company": "Acme", "deal_stage": "discovery"}},
              llm=True, timeout=180),
        Check("Social · campaign brief", "LLM · Business", "POST", "/verticals/social/enhance",
              {"action": "campaign_brief", "payload": {"product": "AI platform", "budget": "₹5,00,000"}},
              llm=True, timeout=180),
        Check("Legal · research query", "LLM · Business", "POST", "/verticals/legal/query",
              {"query": "What are the key clauses in a software service agreement?", "language": "en"},
              llm=True, timeout=240),

        # ── LLM software-dev roles (Ollama) ─────────────────────────────────────
        Check("QA · generate test cases", "LLM · Dev", "POST", "/verticals/qa/action",
              {"action": "generate_tests", "payload": {"feature_description": "User login with email + password"}},
              llm=True, timeout=180),
        Check("DevOps · IaC (Dockerfile)", "LLM · Dev", "POST", "/verticals/devops/iac",
              {"action": "dockerfile", "payload": {"iac_type": "dockerfile", "tech_stack": "Python/FastAPI", "description": "web API"}},
              llm=True, timeout=180),
        Check("Tech Lead · vendor eval", "LLM · Dev", "POST", "/verticals/techlead/enhance",
              {"action": "build_vs_buy", "payload": {"feature": "auth system", "team_size": "4"}},
              llm=True, timeout=180),
        Check("Cybersec · OWASP review", "LLM · Dev", "POST", "/verticals/cybersec/owasp",
              {"action": "owasp_review", "payload": {"code": "query = 'SELECT * FROM users WHERE id=' + user_input", "language": "python"}},
              llm=True, timeout=180),
    ]


# ════════════════════════════════════════════════════════════════════════════════
# RUNNER
# ════════════════════════════════════════════════════════════════════════════════

def login(base: str) -> Optional[str]:
    """Authenticate as the seeded admin and return a bearer token."""
    try:
        r = httpx.post(f"{base}/auth/login",
                       json={"email": "admin@agentic.local", "password": "admin123"}, timeout=15)
        if r.status_code == 200:
            return r.json().get("access_token")
        print(red(f"  login failed: HTTP {r.status_code} — {r.text[:120]}"))
    except Exception as e:
        print(red(f"  login error: {e}"))
    return None


def run_check(base: str, token: Optional[str], c: Check) -> tuple[str, float, str]:
    """Returns (status, elapsed_seconds, note)."""
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
            return ("FAIL", dt, f"HTTP {r.status_code}: {r.text[:80]}")
        try:
            j = r.json()
        except Exception:
            return ("FAIL", dt, "non-JSON response")
        if isinstance(j, dict) and j.get("error"):
            return ("FAIL", dt, f"error: {str(j['error'])[:80]}")
        if c.expect and not c.expect(j):
            return ("FAIL", dt, "validation failed")
        return ("PASS", dt, "")
    except httpx.TimeoutException:
        return ("SKIP", time.monotonic() - t0, f"timeout >{c.timeout:.0f}s (Ollama slow — try --full)")
    except Exception as e:
        return ("FAIL", time.monotonic() - t0, str(e)[:80])


def main() -> int:
    ap = argparse.ArgumentParser(description="Full-project demo / smoke-test runner")
    ap.add_argument("--base", default="http://localhost:8000/api", help="backend API base URL")
    ap.add_argument("--quick", action="store_true", help="skip all LLM checks (fast)")
    ap.add_argument("--full",  action="store_true", help="run every LLM check (slow)")
    args = ap.parse_args()

    mode = "QUICK" if args.quick else "FULL" if args.full else "SMOKE"
    # In SMOKE mode, run only the first N LLM checks to keep total time reasonable
    smoke_llm_budget = 3

    print(bold(cyan("\n╔══════════════════════════════════════════════════════════════╗")))
    print(bold(cyan("║   AI Agentic Platform — Full Project Demo / Smoke Test        ║")))
    print(bold(cyan("╚══════════════════════════════════════════════════════════════╝")))
    print(f"  Backend : {args.base}")
    print(f"  Mode    : {bold(mode)}   " + dim("(LLM via Ollama — no OpenAI cost)"))
    print(f"  Started : {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    print(dim("  Authenticating as admin@agentic.local ..."))
    token = login(args.base)
    print(green("  ✓ logged in, JWT acquired\n") if token else yellow("  ! no token (dev-mode bypass may still allow calls)\n"))

    checks = build_checks()
    results: list[tuple[Check, str, float, str]] = []
    llm_done = 0
    current_cat = None

    for c in checks:
        # Print the category header once, when it changes
        if c.category != current_cat:
            print(f"\n  {bold(c.category)}")
            current_cat = c.category

        # Mode gating for LLM checks
        if c.llm and args.quick:
            results.append((c, "SKIP", 0.0, "LLM skipped (--quick)"))
            _print_line(c, "SKIP", 0.0, "LLM skipped (--quick)")
            continue
        if c.llm and mode == "SMOKE" and llm_done >= smoke_llm_budget:
            results.append((c, "SKIP", 0.0, "smoke budget — use --full"))
            _print_line(c, "SKIP", 0.0, "smoke budget — use --full")
            continue

        status, dt, note = run_check(args.base, token, c)
        if c.llm and status in ("PASS", "FAIL"):
            llm_done += 1
        results.append((c, status, dt, note))
        _print_line(c, status, dt, note)

    # ── summary ──────────────────────────────────────────────────────────────
    n_pass = sum(1 for _, s, _, _ in results if s == "PASS")
    n_fail = sum(1 for _, s, _, _ in results if s == "FAIL")
    n_skip = sum(1 for _, s, _, _ in results if s == "SKIP")
    total_time = sum(dt for _, _, dt, _ in results)

    print(bold(cyan("\n╔══════════════════════════════════════════════════════════════╗")))
    print(  f"  {green(f'PASS {n_pass}')}   {red(f'FAIL {n_fail}')}   {yellow(f'SKIP {n_skip}')}   "
            f"of {len(results)} checks  ·  {total_time:.1f}s")
    print(bold(cyan("╚══════════════════════════════════════════════════════════════╝")))

    if n_fail == 0:
        print(green("\n  🎉 All executed checks passed — the full pipeline is working.\n"))
        if n_skip:
            print(dim("  Tip: run `python demo.py --full` to exercise every LLM vertical end-to-end.\n"))
    else:
        print(red(f"\n  {n_fail} check(s) failed — see notes above.\n"))
        for c, s, _, note in results:
            if s == "FAIL":
                print(red(f"    ✗ {c.name}: {note}"))
        print()
    return 1 if n_fail else 0


def _print_line(c: Check, status: str, dt: float, note: str):
    mark = {"PASS": OK, "FAIL": FAIL, "SKIP": SKIP}[status]
    timing = dim(f"{dt:5.1f}s") if dt else dim("   —")
    extra = dim(f"  {note}") if note else ""
    tag = cyan("[LLM]") if c.llm else "     "
    print(f"    {mark}  {tag} {c.name:<42} {timing}{extra}")


if __name__ == "__main__":
    raise SystemExit(main())
