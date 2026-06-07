"""
Demo-mode canned LLM responder.

When DEMO_MODE=true the LLM router short-circuits here instead of calling Ollama
or OpenAI. This lets the *deployed* app (Render free tier — no Ollama, and we
don't want OpenAI cost on a public demo link) return instant, realistic output
for every AI feature. Deterministic engines (GST/TDS/scoring/validation) still
run for real — only the LLM-backed text generation is mocked.

A lightweight keyword router picks a feature-appropriate template from the
system + user prompt, so each vertical shows believable, distinct output.
"""
from __future__ import annotations


def _texts(messages: list[dict]) -> tuple[str, str]:
    sys = " ".join(m.get("content", "") for m in messages if m.get("role") == "system")
    usr = " ".join(m.get("content", "") for m in messages if m.get("role") == "user")
    return usr.strip(), (sys + " " + usr).lower()


# (keywords, template) — first match wins. Templates are realistic markdown.
_TEMPLATES: list[tuple[tuple[str, ...], str]] = [
    (("owasp", "penetration", "security review", "vulnerab", "injection"),
     """## 🔐 OWASP Top 10 Security Review

| Category | Status | Notes |
|----------|--------|-------|
| A01 Broken Access Control | ⚠️ REVIEW | Verify object-level authz on resource routes |
| A02 Cryptographic Failures | ✅ PASS | TLS + hashed secrets |
| **A03 Injection** | ❌ **FAIL** | Unparameterised SQL — string concatenation detected |
| A05 Security Misconfig | ⚠️ REVIEW | Debug mode must be off in prod |

**Critical finding — SQL Injection**
```python
# Vulnerable
q = "SELECT * FROM users WHERE id=" + user_input
# Fix — parameterised
cur.execute("SELECT * FROM users WHERE id = %s", (user_input,))
```
**Severity:** Critical (CVSS 9.1) · **Remediation:** parameterise all queries, add input validation, enable WAF."""),

    (("dockerfile", "kubernetes", "k8s", "terraform", "ci/cd", "github actions", "iac", "devops", "pipeline"),
     """## ⚙️ Infrastructure-as-Code

```dockerfile
# Multi-stage, production-hardened
FROM python:3.11-slim AS base
RUN adduser --disabled-password --gecos "" appuser
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
USER appuser
HEALTHCHECK --interval=30s CMD curl -f http://localhost:8000/api/health || exit 1
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
**Hardening:** non-root user · slim base · layer-cached deps · healthcheck · no secrets baked in.
**Next:** add `.dockerignore`, scan with Trivy, pin base digest."""),

    (("test case", "qa engineer", "gherkin", "test plan", "acceptance criteria", "unit test"),
     """## 🧪 Generated Test Cases

| ID | Scenario | Type | Priority |
|----|----------|------|----------|
| TC-001 | Valid email + password → success | Positive | P0 |
| TC-002 | Wrong password → 401, no lockout reveal | Negative | P0 |
| TC-003 | SQL injection in email field → rejected | Security | P0 |
| TC-004 | 5 failed attempts → account lockout | Boundary | P1 |

```python
def test_login_success(client):
    r = client.post("/login", json={"email": "a@b.com", "password": "Valid123!"})
    assert r.status_code == 200 and "token" in r.json()
```
**Coverage:** happy path, negative, boundary, security. **DoD:** all P0 automated + reviewed."""),

    (("adr", "architecture decision", "build-vs-buy", "build vs buy", "vendor", "tech radar"),
     """## 🏗️ Architecture Decision Record

**ADR-001 — Use PostgreSQL over MongoDB**
- **Status:** Accepted
- **Context:** Highly relational SaaS data (users → orgs → projects). Need ACID + joins.
- **Decision:** PostgreSQL 16 with async driver.
- **Consequences:** ➕ Strong consistency, mature tooling, JSONB flexibility. ➖ Vertical-scaling ceiling; mitigated by read replicas.

**Build vs Buy verdict:** For auth → **BUY** (Auth0/Cognito). 3-yr TCO < build cost, security is context-not-core, faster GTM. 5 reasons documented."""),

    (("query optimi", "index", "explain plan", "schema design", "dba", "slow query"),
     """## 🗄️ Query Optimization

**Issue:** `SELECT * FROM orders WHERE status='paid'` → full table scan (250k rows, 480ms).

**Recommendations**
1. `CREATE INDEX idx_orders_status ON orders(status);` → seek instead of scan
2. Avoid `SELECT *` — project only needed columns
3. Covering index: `(status, created_at, amount)` for the common report query

**After:** ~480ms → ~8ms (60× faster). Verify with `EXPLAIN ANALYZE`. Watch write-amplification on the new index."""),

    (("experiment", "drift", "feature engineering", "model eval", "ml ", "training", "hyperparam"),
     """## 🤖 ML Experiment Design

**Goal:** Reduce churn-prediction error.
- **Hypothesis:** Engagement-trend features improve recall on at-risk users.
- **Baseline:** Logistic Regression (AUC 0.71).
- **Candidate:** Gradient Boosting + 6 new features (login_freq_delta, support_tickets_30d…).
- **Metrics:** AUC-ROC, PR-AUC (imbalanced), recall@top-decile.
- **Protocol:** 70/15/15 temporal split, 5-fold CV, ablation per feature group.
- **Ship gate:** +0.05 PR-AUC over baseline, no fairness regression."""),

    (("user story", "sprint", "retrospective", "roadmap", "story point", "backlog"),
     """## 📋 User Story

**As a** registered user **I want to** reset my password via email **so that** I can regain access securely.

**Acceptance Criteria (Gherkin)**
- Given a valid email, When I request reset, Then a time-limited link is sent.
- Given an expired link, When I open it, Then I'm told to request a new one.
- Reset tokens are single-use and expire in 30 min.

**Estimate:** 3 points · **Priority:** P1 · **Dependencies:** email service (SendGrid)."""),

    (("triage", "symptom", "clinical", "prescription", "patient", "diagnos"),
     """## 🚑 Symptom Triage

**🔴 EMERGENCY — escalate immediately.**

Severe headache + vomiting + neck stiffness suggests possible **meningitis** or **subarachnoid haemorrhage**.
- **Action:** Call emergency services / go to ED now. Do not wait for appointment.
- **Red flags present:** neck stiffness, sudden severe ("thunderclap") headache, vomiting.
- **Nurse to ask:** fever? photophobia? rash? onset speed? recent head injury?

⚠️ Decision-support only — must be verified by a licensed physician."""),

    (("lease", "property", "real estate", "roi calculat", "listing", "cma", "rent"),
     """## 🏘️ Investment ROI Analysis

| Metric | Value |
|--------|-------|
| Purchase | ₹95,00,000 |
| EMI (8.6%, 20y on ₹75L) | ₹65,600/mo |
| Gross rental yield | 4.0% |
| Net yield (post-costs) | 3.1% |
| Break-even | ~9 years |
| 10-yr projection (7% apprec.) | ≈ ₹1.72 Cr |

**Verdict:** Average investment — appreciation-led, not cashflow-led. Negotiate 5-8% or target higher-rent micro-market. Key risk: interest-rate sensitivity."""),

    (("quiz", "lesson", "course", "student", "syllabus", "edtech", "mcq", "doubt"),
     """## 📚 Quiz — Photosynthesis (Class 10)

1. Which pigment captures light energy? **(A)** Chlorophyll · (B) Haemoglobin · (C) Melanin · (D) Keratin
2. Site of photosynthesis? (A) Mitochondria · **(B)** Chloroplast · (C) Nucleus · (D) Ribosome
3. *(Short)* Write the balanced equation for photosynthesis.

**Answer key:** 1-A (chlorophyll absorbs red/blue light), 2-B.
**HOTS:** Why are leaves green? **Marking:** 1 mark MCQ, 3 marks short. Time: 15 min."""),

    (("gst", "tds", "invoice", "p&l", "profit and loss", "budget forecast", "accountant", "gstr"),
     """## 🧮 GST / Tax Summary

**Invoice ₹1,00,000 @ 18% (intra-state)**
| Component | Rate | Amount |
|-----------|------|--------|
| Taxable value | — | ₹1,00,000 |
| CGST | 9% | ₹9,000 |
| SGST | 9% | ₹9,000 |
| **Invoice total** | | **₹1,18,000** |

**GSTR-3B note:** report outward taxable supplies under 3.1(a); ITC eligible if supplier filed GSTR-1. Inter-state would attract IGST 18% instead of CGST+SGST."""),

    (("resume", "job description", "candidate", "screen", "handbook", "performance review", "onboarding", "hr "),
     """## 👥 Candidate Screening

**Match score: 71/100** — *Recommend: Yes (with interview)*

| Dimension | Score |
|-----------|-------|
| Skills (required) | 67% — Python ✓, Kubernetes ✓, **Go ✗** |
| Experience | 6 yrs (meets 5+ requirement ✓) |
| Nice-to-have | AWS ✓ |

**Strengths:** strong backend + cloud, REST/microservices experience.
**Gaps:** no Go (trainable). **Next:** technical round focused on Go + system design."""),

    (("lead", "objection", "outreach", "meeting prep", "bant", "sales", "discovery call"),
     """## 💼 Sales — Discovery Meeting Prep

**Account:** Acme Corp · **Stage:** Discovery
- **Research checklist:** funding, tech stack, recent hires, current tooling.
- **SPIN questions:** "What's your current process for X?" → "What does that cost in time?"
- **Likely objections:** *"Too expensive"* → reframe to ROI/time saved; *"We have a tool"* → integration + gaps.
- **Demo flow:** pain → 3 key features → pricing → next step.
- **Next step script:** "Shall we set a 30-min technical deep-dive next week?\""""),

    (("seo", "campaign", "hashtag", "linkedin", "social media", "marketing", "content calendar"),
     """## 📱 Marketing Campaign Brief

**Theme:** "AI for every Indian SMB" · **Tagline:** *Automate the boring, grow the bold.*
- **Personas:** SMB owner (cost-focused), Ops lead (time-focused), CA/consultant (compliance).
- **Channel mix:** LinkedIn 40% · Google Search 30% · Email 20% · Content 10%.
- **4-week calendar:** wk1 awareness → wk2 education → wk3 social proof → wk4 offer.
- **KPIs:** 50 MQLs/mo, CPL < ₹10k. **A/B:** subject lines + CTA colour."""),

    (("contract", "nda", "clause", "agreement", "legal", "indemnif", "jurisdiction"),
     """## ⚖️ Contract Review — Key Clauses

| Clause | Position | Risk |
|--------|----------|------|
| Liability cap | Capped at 12-mo fees | ✅ Balanced |
| IP ownership | Work-for-hire to client | ⚠️ Confirm pre-existing IP carve-out |
| Termination | 30-day notice either side | ✅ |
| Indemnity | One-sided (favours vendor) | ❌ Negotiate mutual |

**Red flags:** auto-renewal without notice; broad confidentiality with no time limit.
*AI guidance only — consult a qualified attorney before signing.*"""),

    (("crop", "mandi", "yield", "farmer", "soil", "agri", "irrigation", "fertiliz", "kharif"),
     """## 🌾 Crop Advisory — Tomato (Tamil Nadu)

- **Best sowing:** Jun–Jul (kharif) or Nov–Dec; avoid peak monsoon.
- **Soil:** red loamy, pH 6.0–7.0, good drainage.
- **Spacing:** 60×45 cm · **Irrigation:** drip + mulch (saves ~40% water).
- **Nutrition:** NPK 120:100:100 kg/ha, split doses.
- **Watch:** leaf curl virus (control whitefly), early blight.
- **Mandi:** ₹1,200–1,800/quintal — sell graded produce to premium markets."""),

    (("faq", "sla", "escalation", "receptionist", "appointment", "book a meeting", "business hours"),
     """## ☎️ Receptionist

"Sure! I can help you book that. We have **Monday 11:00 AM** or **3:30 PM** open — which suits you?
May I take your **name** and **email** to send the confirmation?

For anything urgent, our support hours are Mon–Sat, 9 AM–7 PM IST."

*(Appointment would be created via Calendly; confirmation sent by email — connect TWILIO/CALENDLY keys to go live.)*"""),

    (("binary search", "function", "refactor", "debug this", "write code", "code assistant", "algorithm"),
     """## 💻 Code

```python
def binary_search(arr: list[int], target: int) -> int:
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        if arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
```
**Complexity:** O(log n) time, O(1) space. Requires a sorted array. Edge cases handled: empty list, target absent (returns -1)."""),

    (("sql", "data analyst", "revenue", "top customers", "dashboard", "chart"),
     """## 📊 Data Analysis

```sql
SELECT customer, SUM(amount) AS revenue
FROM orders
WHERE status = 'paid'
GROUP BY customer
ORDER BY revenue DESC
LIMIT 5;
```
**Insight:** Top 5 customers drive ~78% of revenue (Pareto). Recommend a named-account retention motion for these and an expansion play for the next 20%. A bar chart of revenue-by-customer is generated alongside."""),
]

_GENERIC = """## ✅ Sample Result (Demo Mode)

This is a representative AI response generated instantly in **demo mode** (no live
model call). With a model key configured, this returns a full, tailored result for
your exact input — structured analysis, recommendations, and next steps.

> Tip: set `DEMO_MODE=false` and provide `OPENAI_API_KEY` (or run Ollama locally)
> to see real generated output."""


def demo_complete(messages: list[dict]) -> tuple[str, str]:
    """Return (canned_text, model_label) for demo mode."""
    _user, blob = _texts(messages)
    for keywords, template in _TEMPLATES:
        if any(k in blob for k in keywords):
            return template, "demo"
    return _GENERIC, "demo"
