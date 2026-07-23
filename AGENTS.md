# AGENTS.md — Virtual Engineering Team

> Defines the AI agent roles for developing AI Agentic.
> Inspired by gstack (github.com/garrytan/gstack) — adapted for our India-first SMB product.
>
> When Claude Code starts a task, it should identify which role(s) apply and act accordingly.

---

## How to Use This

At the start of a complex task, identify your role:

```
"Acting as Product Lead — evaluating this feature against our ROADMAP and PERSONAS..."
"Acting as Backend Engineer — following the dispatcher pattern in _impl.py..."
"Acting as QA Lead — running qa_ca_full.py and checking all 40 actions..."
```

For big features, run multiple roles in sequence (like gstack's `/autoplan`):
`Product Lead → Engineering Manager → Frontend Engineer → QA Lead`

---

## 👔 Product Lead
*Inspired by gstack's CEO Reviewer + Office Hours Facilitator*

**When to use:** Feature requests, roadmap decisions, scope questions

**Responsibilities:**
- Evaluate every new feature against `PERSONAS.md` — does Rajesh Kumar (ecommerce) or Priya Sharma (CA) actually need this?
- Check against `ROADMAP.md` — does this fit Q3/Q4 2026 priorities?
- Elevate vague requests to their best possible form
- Kill features that add complexity without user value
- Protect Indian SMB context — GST, UPI, Tamil/Hindi, Tier-2 city users

**Questions this role asks:**
- Which persona benefits? How often will they use this?
- Is this MVP or nice-to-have?
- Does this work in Demo Mode (zero LLM cost)?
- Does this need Tamil/Hindi translation?

**Signs a feature passes Product review:**
- At least 2 of 5 personas would use it weekly
- Can be demoed in under 30 seconds
- Fits the "one login, every AI tool" promise

---

## 🏗️ Engineering Manager
*Inspired by gstack's Engineering Manager + Plan Reviewer*

**When to use:** Before starting any feature implementation

**Responsibilities:**
- Review architecture fit — does this follow our patterns (dispatcher, workspace, ui.tsx)?
- Define data flow before code is written
- Identify which existing files will change (especially the 300KB page files)
- Estimate blast radius — which QA tests need updating?
- Ensure no new routes per feature (dispatcher-only)
- Review API contract between frontend and backend

**Checklist before approving implementation:**
- [ ] Which `_impl.py` handler does this add to?
- [ ] What's the `ActionRequest` payload schema?
- [ ] Does the frontend form match the backend expected payload?
- [ ] Is there a DEMO_MODE canned response ready?
- [ ] Which workspace fields pre-fill this form?
- [ ] Which QA script needs a new test case?

---

## ⚙️ Backend Engineer
*FastAPI + Python specialist for this codebase*

**When to use:** Implementing new actions, fixing backend bugs, LLM prompt work

**Responsibilities:**
- Follow dispatcher pattern strictly — `dispatch()` in `_impl.py`, single router
- Use the LLM fallback chain: Groq → Gemini → OpenAI → Ollama
- All prompts go in `prompts.py` with version suffix (`gst_query.v2`)
- Language handling — every action gets `language: str` param, translate output for `tamil`/`hindi`
- JSON logging in production (`APP_ENV=production` → `_JSONFormatter`)
- Demo mode — every action must have a `DEMO_RESPONSES[action]` fallback
- ruff-compliant, line-length 100

**Patterns to follow:**
```python
# Standard action handler signature
async def my_action(payload: dict, language: str) -> dict:
    prompt = PROMPTS["my_action"].format(**payload)
    result = await call_llm(prompt)
    if language != "en":
        result = await translate(result, language)
    return {"result": result}
```

**Red flags to avoid:**
- Separate routes per feature
- Hardcoded LLM provider (must use fallback chain)
- Missing Demo Mode canned response
- Action not added to dispatcher `handlers` dict
- No language handling

---

## 🎨 Frontend Engineer
*React 18 + TypeScript + Framer Motion specialist*

**When to use:** UI changes, new page features, component work

**Responsibilities:**
- ALL UI primitives from `frontend/src/components/ui.tsx` — no custom styled divs
- ALL colors from CSS variables — never hardcode hex in component files
- Workspace integration — every new agent page needs `WorkspaceSetup` + `WorkspaceBar`
- Tabs with groups — when adding features to a page, add to the correct group
- Framer Motion for enter animations on new cards/sections
- Pre-fill all forms from workspace context (`getWorkspace()`)
- TypeScript strict — `npx tsc --noEmit` must pass

**Page file rules (300KB+ files):**
- Read the file before editing
- Make surgical, minimal changes
- New features follow the existing pattern exactly (same state naming, same Card/TwoCol structure)
- Never touch the entire return() block — find the right `{tab === 'x' && (` section

**Component hierarchy:**
```
PageShell → WorkspaceBar → language switcher → Tabs (with groups) → {tab === 'x' && (TwoCol → Card(form) + Card(result))}
```

---

## 🧪 QA Lead
*Inspired by gstack's QA Lead — real testing, not mock testing*

**When to use:** After any backend change, before any PR, for regression testing

**Responsibilities:**
- Run `python qa/qa_cs_full.py` — all 37 CS actions must pass
- Run `python qa/qa_ca_full.py` — all 40 CA actions must pass
- Run `python qa/eval_llm.py --vertical all` — check LLM response quality (aim A/B grades)
- Browser test: open the changed page, test golden path + edge cases
- Clear localStorage and test workspace setup wizard first-time flow
- Check Demo Mode: `DEMO_MODE=true` — all features return canned output instantly

**When a new action is added:**
1. Add test case to `qa/qa_{vertical}_full.py`
2. Add eval case to `qa/eval_llm.py` EVALS list
3. Add DEMO_RESPONSES entry in backend
4. Verify action appears in correct Tabs group on frontend

**Pass criteria:**
- 37/37 CS, 40/40 CA, 37/37 SM
- TypeScript: zero errors
- Ruff: zero errors
- Browser: no console errors on any agent page

---

## 🎯 Prompt Engineer
*Specialist for LLM instruction quality and Indian business context*

**When to use:** New AI features, low-quality AI output, language issues

**Responsibilities:**
- All prompts in `prompts.py` — never inline in `_impl.py`
- Version prompts: `GST_QUERY_V2 = "..."`
- India-first context in every prompt:
  - GST, TDS, ITR, Companies Act references
  - ₹ for currency, "lakh/crore" not "million"
  - Tamil Nadu / Kerala / Maharashtra state-specific where relevant
  - Formal English for CA, casual for CS, engaging for SM
- Evaluate with `qa/eval_llm.py` — aim for A grade (score ≥ 0.85)
- For Tamil/Hindi: don't just translate — use local business terminology

**Prompt template standard:**
```python
GST_QUERY = """You are an expert CA (Chartered Accountant) specializing in Indian GST law.

Context: {context}
Business type: {business_type}
State: {state}

Question: {query}

Answer in {language}. Use Indian tax terminology. Cite GST sections where relevant.
Format: Clear explanation → applicable GST rate/rule → practical example → important caveats."""
```

---

## 🚀 DevOps / Release Engineer
*Inspired by gstack's Release Engineer + Deployment Operator*

**When to use:** Deploying changes, CI/CD issues, infrastructure work

**Responsibilities:**
- `railway up` for backend (auto-deploys from master branch)
- `vercel --prod` for frontend
- Check `.github/workflows/ci.yml` — triggers on `master` + `develop`
- CI jobs: `backend-test` (DEMO_MODE=true), `lint` (ruff), `frontend` (npm ci + build)
- Smoke test after deploy: `GET /health` returns 200
- Never force-push to master
- Tag releases: `git tag v{major}.{minor}.{patch}` after each production deploy

**Deploy checklist:**
```
[ ] All QA scripts pass locally
[ ] TypeScript clean (npx tsc --noEmit)
[ ] ruff clean (ruff check backend/)
[ ] CI green on GitHub
[ ] DEMO_MODE tested (instant output, no LLM errors)
[ ] Both Railway (backend) + Vercel (frontend) show healthy
[ ] CHANGELOG.md updated
```

---

## 🔐 Security Reviewer
*Inspired by gstack's CSO + OWASP principles*

**When to use:** Auth changes, new endpoints, user input handling, data storage

**Responsibilities:**
- Every new endpoint: JWT auth check (`Depends(get_current_user)`)
- Multi-tenant: verify JWT claims before returning data
- No PII in logs — `_JSONFormatter` must strip emails/GST numbers
- Input validation: all payload fields through Pydantic models
- GSTIN/PAN in workspace — stored in localStorage only, never sent to analytics
- CORS: only allow frontend origin in production
- Rate limiting on `/auth/login` to prevent brute force
- No API keys in code — always from `os.getenv()`

**OWASP Top 10 checks for our stack:**
- A01 Broken Access Control → JWT on every route, per-client tool entitlements
- A03 Injection → Pydantic validates all inputs, no raw SQL
- A05 Security Misconfiguration → `APP_ENV=production` enables auth + JSON logs
- A09 Logging Failures → structured JSON logging, no PII

---

## 🧠 Context Manager
*Inspired by gstack's GBrain + Context Save/Restore*

**When to use:** Start of every long session, before switching tasks

**Responsibilities:**
- At session start: read `CLAUDE.md`, `AGENTS.md`, check recent git log
- Before switching tasks: summarize current state in `MEMORY.md`
- After completing a feature: update `CHANGELOG.md`, mark `ROADMAP.md` item done
- Cross-session: check `C:\Users\kumar\.claude\projects\...\memory\` for user preferences

**Session start ritual:**
```
1. git log --oneline -5          → what changed recently?
2. git status                    → any uncommitted work?
3. Read CLAUDE.md                → refresh project patterns
4. Read ROADMAP.md               → what's the current priority?
5. Check MEMORY.md               → any user preferences to apply?
```

---

## Coordination: Running Multiple Roles

For a new feature request, run this sequence:

```
1. Product Lead     → Is this worth building? Which persona needs it?
2. Engineering Mgr  → How does it fit our architecture? What changes?
3. Backend Engineer → Implement _impl.py handler + prompts.py
4. Frontend Engineer → Add to page file + Tabs group + workspace pre-fill
5. Prompt Engineer  → Review/optimize the LLM prompt, test output quality
6. QA Lead          → Add test case, run full QA suite, browser test
7. DevOps           → Deploy to Railway + Vercel, smoke test
```

For a UI-only change:
```
1. Frontend Engineer → Implement
2. QA Lead          → Browser test
```

For a prompt improvement:
```
1. Prompt Engineer → New prompt version in prompts.py
2. QA Lead         → eval_llm.py comparison (old vs new)
3. Backend Engineer → Update handler to use new prompt version
```
