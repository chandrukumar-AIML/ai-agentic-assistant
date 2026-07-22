# Architecture — AI Agentic Assistant

## Overview

Three-layer system: React frontend → FastAPI backend → AI Agent verticals → LLM.

```
┌──────────────────────────────────────────────────┐
│   React 18 + TypeScript (Vercel)                  │
│   Landing · Login · Dashboard · CS · CA · SM      │
└───────────────────┬──────────────────────────────┘
                    │ REST (HTTPS)
┌───────────────────▼──────────────────────────────┐
│   FastAPI Backend (Render)                        │
│   JWT Auth → Rate Limit → CORS → Router           │
│                                                   │
│   /api/auth/*          Auth endpoints             │
│   /api/health          Health check               │
│   /api/verticals/{n}/action   Agent dispatcher    │
└───────────────────┬──────────────────────────────┘
                    │
          ┌─────────┼──────────┐
          ▼         ▼          ▼
      CS Agent   CA Agent   SM Agent
      (38 acts) (40 acts) (37 acts)
          │         │          │
          └─────────┼──────────┘
                    │
┌───────────────────▼──────────────────────────────┐
│   LLM Router (_llm() bridge)                      │
│   Groq → Gemini → OpenAI → Ollama (fallback)      │
└──────────────────────────────────────────────────┘
```

---

## Key Components

### 1. FastAPI Backend (`backend/`)

```
backend/
├── main.py              # App factory — CORS, rate limiter, routers
├── config.py            # Pydantic Settings — all env vars, validated
├── api/
│   ├── auth.py          # /api/auth/login, /me, /profile — JWT issue
│   ├── health.py        # /api/health — service status
│   └── vertical_routes.py  # /api/verticals/{name}/action — dispatcher
├── llm/
│   ├── ollama_openai.py # Ollama client (OpenAI-compatible)
│   ├── groq_client.py   # Groq client
│   ├── gemini_client.py # Gemini client
│   └── demo_responder.py # Demo mode — instant canned output
└── verticals/
    ├── base.py          # BaseVertical class
    ├── customer_support/
    ├── ca_accounting/
    └── social_media/
```

### 2. Vertical Agent Pattern

Every vertical follows the same 5-file structure:

```
verticals/<name>/
├── __init__.py
├── agent.py        # HTTP handler — receives action + payload + language
├── _impl.py        # Dispatcher → 37–40 private action functions
├── schemas.py      # Pydantic request/response models
├── constants.py    # Metadata (name, description, supported actions)
└── tools/          # Functions split by category
    ├── support_core.py
    ├── analytics_reporting.py
    └── ...
```

**Dispatcher flow:**
```python
def cs_agent(action: str, payload: dict, language: str = "en") -> dict:
    if action == "faq_bot":
        return _faq_bot(payload, language)
    elif action == "analyze_sentiment":
        return _analyze_sentiment(payload, language)
    # ... 36 more branches
```

### 3. LLM Bridge (`_llm()`)

Centralized in each `_impl.py`. Priority: `Groq > Gemini > OpenAI > Ollama`

```python
def _llm(prompt: str, system: str = "", temperature: float = 0.7) -> str:
    settings = get_settings()
    if settings.groq_api_key:
        return groq_complete(prompt, system, temperature)
    if settings.gemini_api_key:
        return gemini_complete(prompt, system, temperature)
    if settings.openai_api_key:
        return openai_complete(prompt, system, temperature)
    return ollama_complete(prompt, system, temperature)  # local fallback
```

### 4. Auth Flow

```
POST /api/auth/login
  Body: { email, password }
  → verify credentials (hardcoded dev users or DB)
  → issue JWT (HS256, 24hr expiry)
  → return { access_token, token_type, user }

GET /api/auth/me
  Header: Authorization: Bearer <token>
  APP_ENV=development → skip verification, return dev user
  APP_ENV=production  → verify JWT, return user profile
```

### 5. Frontend → Backend Flow

```
User clicks "Analyze Sentiment"
  → React sends POST /api/verticals/cs/action
  → Body: { action: "analyze_sentiment", payload: {...}, language: "en" }
  → FastAPI vertical_routes.py routes to cs_agent()
  → cs_agent() dispatches to _analyze_sentiment()
  → _analyze_sentiment() calls _llm(prompt)
  → LLM router picks Groq/Gemini/Ollama
  → Returns structured JSON → response to frontend
```

---

## Architecture Decision Records (ADRs)

### ADR-001 — Dispatcher Pattern for Agent Actions

**Date:** 2026-01
**Status:** Accepted

**Context:** Each AI agent needs 37–40 actions. Options:
1. One endpoint per action (37 routes per agent = 111+ routes)
2. Single `POST /action` with `action` field dispatch (current)
3. GraphQL

**Decision:** Option 2 — single dispatcher endpoint.

**Rationale:**
- Frontend has one API call pattern for all verticals
- New actions added without new routes
- Consistent request/response format
- Easy to QA (same test harness for all actions)

**Trade-offs:**
- Dispatcher can get long (mitigated by `tools/` subfolder split)
- No automatic OpenAPI docs per action (mitigated by Pydantic schemas)

---

### ADR-002 — LLM Routing Priority (Groq > Gemini > OpenAI > Ollama)

**Date:** 2026-03
**Status:** Accepted

**Context:** Need LLM that works locally (dev), cheaply (demo), and reliably (prod).

**Decision:** Priority chain based on API key availability:
1. **Groq** (fastest, free 6K req/day) — when `GROQ_API_KEY` set
2. **Gemini** (free tier, Google) — when `GEMINI_API_KEY` set
3. **OpenAI** (paid, most capable) — when `OPENAI_API_KEY` set
4. **Ollama** (local, always available) — final fallback

**Rationale:**
- Zero-cost demo possible without any API key (Ollama)
- Production: Groq for speed + free tier
- No vendor lock-in: swap by setting/unsetting env vars

---

### ADR-003 — Multi-tenant via JWT Claims (not DB-per-tenant)

**Date:** 2026-02
**Status:** Accepted

**Context:** Need multi-tenant isolation without complexity.

**Decision:** JWT token carries `{ user_id, email, role, allowed_tools[] }`. All requests filtered at API layer by `allowed_tools`.

**Rationale:**
- Simple: no per-tenant DB schemas
- Stateless: no session store needed for auth
- Scalable: works on free-tier (no Redis needed for auth)

**Trade-offs:**
- Tool entitlement changes require new JWT (re-login)
- Not suitable for very high security (financial) isolation

---

## Deployment Architecture

```
GitHub (master branch)
  │
  ├── Push → Render auto-deploy (backend)
  │          docker build → uvicorn main:app --port 8000
  │
  └── Push → Vercel auto-deploy (frontend)
             npm run build → static SPA

Local Dev:
  docker-compose up → postgres + redis + backend + frontend
  OR: manual (uvicorn + npm run dev)
```

---

## Data Flow Diagrams

### CS Agent — Handle Complaint

```
1. POST /api/verticals/cs/action
   { action: "handle_complaint", payload: { complaint, customer_name, ... } }

2. vertical_routes.py → cs_agent("handle_complaint", payload, "en")

3. _impl.py dispatcher → _handle_complaint(payload, language)

4. _handle_complaint builds system_prompt:
   - Role: Expert CS manager at {business_name}
   - Task: Acknowledge + resolve + prevent recurrence
   - Format: JSON { acknowledgment, resolution_steps, compensation, ... }

5. _llm(prompt, system_prompt) → Groq/Gemini/Ollama

6. Parse JSON response → return dict

7. FastAPI → 200 JSON response to frontend
```

---

## Security Architecture

```
Request → Rate Limiter (SlowAPI)
        → CORS Check (explicit allow-list)
        → JWT Verification (production only)
        → Pydantic Validation (always)
        → Business Logic
        → Response
```

No request reaches business logic without passing all layers.
