# CLAUDE.md — AI Agentic Assistant

> Project-level instructions for Claude Code. Read this before every task.
> Inspired by gstack (github.com/garrytan/gstack) — adapted for this project.
>
> **Methodology reference:** `C:/Users/kumar/chandLab/chandru-stack/CLAUDE.md`
> For engineering roles, workflow phases, and universal standards — read chandru-stack first.

---

## Project Identity

**AI Agentic** is a multi-tenant Business AI Suite for Indian SMBs — one login, every AI tool a business needs. Three live agent verticals: Social Media (SM), Customer Support (CS), CA & Accounting (CA). Each vertical has 37–40 AI-powered features.

**Stack:** FastAPI 0.115 · Python 3.11 · React 18 + TypeScript · Vite · Tailwind (minimal) · Framer Motion · LangGraph 0.2.56  
**LLM Chain:** Groq → Gemini → OpenAI → Ollama (priority order, automatic fallback)  
**Auth:** JWT (skipped in `APP_ENV=development`)  
**Multi-tenant:** per-client tool entitlements via JWT claims  
**Deployment:** Railway (backend) · Vercel (frontend)

---

## Repo Layout

```
ai-agentic-assistant/
├── backend/
│   ├── main.py               ← FastAPI app, middleware, logging, auth
│   ├── verticals/
│   │   ├── social/           ← SM agent (37 actions)
│   │   ├── customer_support/ ← CS agent (37 actions)
│   │   └── ca_accounting/    ← CA agent (40 actions)
│   │       ├── router.py     ← POST /api/{vertical}/action
│   │       ├── _impl.py      ← dispatcher → action functions
│   │       └── prompts.py    ← all prompt templates
│   └── auth.py, models.py, db.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui.tsx         ← ALL shared primitives (PageShell, Card, Btn, Input, Tabs...)
│   │   │   ├── Sidebar.tsx    ← animated sidebar (Framer Motion)
│   │   │   ├── WorkspaceSetup.tsx ← 3-step wizard per agent
│   │   │   └── WorkspaceBar.tsx   ← context bar showing saved profile
│   │   ├── pages/
│   │   │   ├── LandingPage.tsx
│   │   │   ├── LoginPage.tsx
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── SocialPage.tsx       ← 37 SM features (300KB+)
│   │   │   ├── CustomerSupportPage.tsx ← 37 CS features (300KB+)
│   │   │   └── CAPage.tsx           ← 40 CA features (300KB+)
│   │   ├── lib/
│   │   │   ├── api.ts         ← all API calls
│   │   │   └── workspace.ts   ← workspace hook (localStorage per agent)
│   │   └── index.css          ← CSS design system (all --var tokens)
│   └── package.json
├── qa/
│   ├── qa_cs_full.py          ← 37/37 CS action tests
│   ├── qa_ca_full.py          ← 40/40 CA action tests
│   └── eval_llm.py            ← LLM quality eval (grades A-F)
├── prompts/README.md          ← prompt versioning registry
├── ENGINEERING_PLAYBOOK.md    ← 17-level engineering audit framework
├── PERSONAS.md                ← 5 Indian SMB user personas
├── AGENTS.md                  ← virtual dev team roles
├── ARCHITECTURE.md            ← system diagram + 3 ADRs
├── ROADMAP.md                 ← Q3/Q4 2026 + 2027 plans
└── .claude/commands/          ← slash commands for this project
```

---

## Core Patterns — MUST follow

### Backend: Dispatcher Pattern
Every vertical has ONE endpoint: `POST /api/{vertical}/action`

```python
# router.py
@router.post("/action")
async def action(req: ActionRequest, user=Depends(get_current_user)):
    return await dispatch(req.action, req.payload, req.language)

# _impl.py
async def dispatch(action: str, payload: dict, language: str):
    handlers = {
        "gst_query":    gst_query,
        "tds_calc":     tds_calc,
        # ... 40 handlers
    }
    fn = handlers.get(action)
    if not fn: raise HTTPException(404, f"Unknown action: {action}")
    return await fn(payload, language)
```

**Never create separate routes per feature.** Always add to dispatcher.

### Backend: LLM Call Pattern
```python
async def call_llm(prompt: str, system: str = "") -> str:
    # Groq → Gemini → OpenAI → Ollama — automatic fallback
    for provider in ["groq", "gemini", "openai", "ollama"]:
        try:
            return await _call(provider, prompt, system)
        except Exception:
            continue
    raise RuntimeError("All LLM providers failed")
```

### Frontend: All UI from ui.tsx
**Never hardcode colors in page files.** Always use:
- `PageShell`, `Card`, `Btn`, `Input`, `Select`, `ResultBox`, `Tabs`, `TwoCol`, `SectionHead`, `Badge`, `StatCard`, `useApi`
- CSS variables: `var(--bg)`, `var(--surface)`, `var(--border)`, `var(--accent)`, `var(--text)`, `var(--text-2)`, `var(--text-3)`

### Frontend: Workspace Pattern
Each agent page MUST include:
```tsx
const [ws, setWs] = useState(() => getWorkspace<XWorkspace>('sm|cs|ca'))
const [showSetup, setShowSetup] = useState(() => !getWorkspace('sm|cs|ca'))

// In JSX:
{(showSetup || editMode) && <WorkspaceSetup agent="sm" ... />}
{ws && <WorkspaceBar agent="sm" onEdit={...} onClear={...} />}
```

### Frontend: Tabs with Groups
```tsx
<Tabs
  tabs={[...37 items...]}
  active={tab} onChange={setTab}
  accentColor="#8B5CF6"
  groups={[
    { label: 'Create', ids: ['content','hashtags',...] },
    { label: 'Research', ids: ['competitor','seo',...] },
  ]}
/>
```
Tabs auto-show search input when `tabs.length > 8`.

---

## Adding a New Agent Vertical

Follow the 5-file pattern:

```
backend/verticals/{name}/
  __init__.py
  router.py      ← POST /api/{name}/action + register in main.py
  _impl.py       ← dispatch() + all action handlers
  prompts.py     ← all prompt templates
  models.py      ← Pydantic models (ActionRequest, etc.)

frontend/src/pages/{Name}Page.tsx   ← all features in one file
```

1. Add router to `main.py`: `app.include_router(router, prefix="/api/{name}")`
2. Add to `Sidebar.tsx` NAV array and ICONS map
3. Add to `App.tsx` PAGE_MAP
4. Add to `DashboardPage.tsx` AGENTS array
5. Create QA script: `qa/qa_{name}_full.py`
6. Add workspace type to `lib/workspace.ts`

---

## Development Commands

```bash
# Backend
cd backend && uvicorn main:app --reload --port 8000
APP_ENV=development uvicorn main:app --reload   # skips JWT

# Frontend
cd frontend && npm run dev                       # port 5173

# QA
python qa/qa_cs_full.py                          # 37 CS tests
python qa/qa_ca_full.py                          # 40 CA tests
python qa/eval_llm.py --vertical all             # LLM quality A-F

# Type check
cd frontend && npx tsc --noEmit

# Lint
ruff check backend/
```

---

## Design System (index.css)

```css
--bg: #080808          --surface: #0F0F0F     --surface-2: #161616
--border: rgba(255,255,255,0.06)               --border-2: rgba(255,255,255,0.10)
--accent: #6366F1      --accent-2: #818CF8    --accent-glow: rgba(99,102,241,0.18)
--success: #10B981     --warning: #F59E0B     --danger: #EF4444
--text: #FAFAFA        --text-2: #A1A1AA      --text-3: #52525B

/* Agent accents */
--sm-from: #8B5CF6     --ca-from: #F59E0B     --cs-from: #10B981
```

Utility classes: `.glass`, `.card`, `.card-glow`, `.btn`, `.btn-primary`, `.btn-ghost`, `.input`, `.label`, `.chip`, `.dot-live`, `.badge-*`, `.skeleton`

---

## Code Style

- **No comments** unless WHY is non-obvious
- **No hardcoded hex** in components — always CSS vars
- **No magic strings** for action names — keep in a constant
- TypeScript strict — no `any` except in `renderResult()` smart renderer
- Python: ruff-compliant, line-length 100, f-strings preferred
- Commit format: `type(scope): message` — feat/fix/docs/refactor/test/chore

---

## Environment Variables

```bash
# Backend (.env)
APP_ENV=development          # skips JWT auth
GROQ_API_KEY=...
GEMINI_API_KEY=...
OPENAI_API_KEY=...
LOG_LEVEL=INFO
DEMO_MODE=false              # true = instant canned output, zero LLM cost

# Frontend (.env)
VITE_API_URL=http://localhost:8000/api
VITE_POSTHOG_KEY=...         # optional analytics
```

---

## QA Checklist (before every PR)

- [ ] All existing QA scripts pass: `python qa/qa_cs_full.py` + `python qa/qa_ca_full.py`
- [ ] TypeScript: `npx tsc --noEmit` — zero errors
- [ ] Lint: `ruff check backend/` — zero errors
- [ ] UI: open browser, test the changed feature end-to-end
- [ ] Workspace wizard: test first-time flow (clear localStorage) + edit flow
- [ ] No hardcoded colors or magic strings introduced

---

## Deployment

```bash
# Backend → Railway (auto-deploy on push to master)
railway up

# Frontend → Vercel (auto-deploy on push to master)
vercel --prod

# Smoke test after deploy
curl https://ai-agentic-backend.railway.app/health
```

---

## Key Constraints

1. **Never add a new route per feature** — always extend the dispatcher
2. **Never import styling directly in page files** — all from `ui.tsx`
3. **Never use pure black (#000)** — use `var(--bg)` (#080808)
4. **Page files are huge (300KB+)** — read before editing, minimal changes
5. **Workspace data is per-agent localStorage** — `aaa_ws_sm`, `aaa_ws_cs`, `aaa_ws_ca`
6. **Demo mode** — when `DEMO_MODE=true`, return canned output. Never call real LLM.
7. **Language support** — every action must handle `en`, `tamil`, `hindi`

---

## Reference Files

| File | Purpose |
|---|---|
| `ENGINEERING_PLAYBOOK.md` | 17-level audit framework — score the codebase |
| `PERSONAS.md` | 5 Indian SMB personas — design for these real users |
| `AGENTS.md` | Virtual dev team — which role to act as for each task |
| `ARCHITECTURE.md` | System diagram + ADR decisions |
| `ROADMAP.md` | Q3/Q4 2026 priorities |
| `SECURITY.md` | Vulnerability reporting + hardening checklist |
| `CHANGELOG.md` | Full feature history |
| `CONTRIBUTING.md` | How to add new verticals |
