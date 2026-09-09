# AI Agentic Assistant

> Multi-tenant Business AI Suite for Indian SMBs — one login, every AI tool a business needs.

[![CI](https://github.com/chandrukumar-AIML/ai-agentic-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/chandrukumar-AIML/ai-agentic-assistant/actions)
[![Live Demo](https://img.shields.io/badge/demo-live-green)](https://ai-agentic-backend-ywdx.onrender.com/docs)

---

## 1. Problem

Indian SMBs (small businesses, CAs, e-commerce shops) need multiple AI tools — content creation, tax compliance, customer support — but can't afford or manage 10 separate SaaS subscriptions. They need one AI workspace that speaks their domain language (GST, GSTR-3B, festive campaigns, regional languages).

---

## 2. Solution

Three production AI agents under one login:

| Agent | Actions | Use Case |
|-------|---------|---------|
| **Social Media (SM)** | 40 | Instagram captions, competitor audits, festive posts, YouTube scripts |
| **CA & Accounting (CA)** | 44 | GST queries, TDS calc, ITR advice, invoice generation, tally analysis |
| **Customer Support (CS)** | 41 | Ticket triage, SLA tracking, winback campaigns, CSAT analysis |

**125 QA-tested AI features. Live on Render. Zero LLM cost in demo mode.**

---

## 3. Architecture

```mermaid
flowchart TD
    User["👤 User (Browser)"]
    Landing["Landing Page\nReact 18 + TypeScript\nVercel"]
    Auth["JWT Auth\n/api/auth/login\n/api/auth/register"]
    API["FastAPI Backend\nRender.com\nRate Limit · CORS · Logging"]
    Router["Agent Dispatcher\n/api/verticals/{sm|ca|cs}/action"]

    SM["Social Media Agent\n40 actions"]
    CA["CA & Accounting Agent\n44 actions"]
    CS["Customer Support Agent\n41 actions"]

    Det["Deterministic Layer\nGST rates · TDS calc\nITR grounding · Compliance dates"]
    LLM["LLM Router\nGroq → Gemini → OpenAI → Ollama"]
    Demo["Demo Responder\nInstant canned output\nDEMO_MODE=true"]

    DB["PostgreSQL\nNeon (prod) / Docker (local)"]
    Cache["Redis\nRate limit · Session"]

    User --> Landing
    Landing --> Auth
    Auth --> API
    API --> Router
    Router --> SM & CA & CS
    SM & CA & CS --> Det
    Det --> LLM
    LLM -->|"DEMO_MODE=true"| Demo
    LLM -->|"API key set"| Groq & Gemini & OpenAI
    LLM -->|"local"| Ollama
    API --> DB
    API --> Cache
```

**Data flow per request:**
`User → HTTPS → FastAPI (JWT verify + rate limit) → Agent dispatcher → Deterministic layer → LLM Router → Response`

---

## 4. Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite, Framer Motion, Tailwind (minimal) |
| Backend | FastAPI 0.115, Python 3.11, Pydantic v2, uvicorn |
| Auth | JWT (HS256), bcrypt, 24h access + 7d refresh tokens |
| LLM Chain | Groq (Llama 3) → Gemini 2.0 Flash → GPT-4o → Ollama (llama3.2) |
| Database | PostgreSQL 16 + pgvector (Neon free tier in prod) |
| Cache | Redis 7.2 |
| Deployment | Render (backend) · Vercel (frontend) |
| CI/CD | GitHub Actions (lint → test → build → smoke test) |
| Containers | Docker multi-stage + docker-compose |
| Testing | pytest (14 unit) · Vitest (12 frontend) · QA scripts (125 integration) |

---

## 5. Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker + Docker Compose (optional, for full stack)

### Option A — Docker (recommended)

```bash
git clone https://github.com/chandrukumar-AIML/ai-agentic-assistant.git
cd ai-agentic-assistant
cp .env.example .env          # fill in API keys
docker compose up             # starts backend + frontend + postgres + redis + ollama
```

Open http://localhost:5173

### Option B — Local dev

```bash
# Backend
pip install -r backend/requirements.txt
cp .env.example .env
uvicorn backend.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

---

## 6. Environment Variables

Copy `.env.example` to `.env` and fill in:

```bash
# LLM (pick one or more — fallback chain activates automatically)
GROQ_API_KEY=gsk_...          # free tier, fastest
GEMINI_API_KEY=AIza...        # production recommended
OPENAI_API_KEY=sk-...         # optional fallback

# Demo mode (no LLM cost — instant canned responses)
DEMO_MODE=false               # set true on free hosting tiers

# Auth
JWT_SECRET=<generate with: openssl rand -hex 32>

# Database
DATABASE_URL=postgresql://user:pass@host/db   # Neon free tier

# App
APP_ENV=development           # skips JWT in local dev
```

**Never commit `.env` to git.** Only `.env.example` (no real values) is committed.

---

## 7. Running Locally

```bash
# Backend only
uvicorn backend.main:app --reload --port 8000
# → http://localhost:8000/docs (Swagger UI)
# → http://localhost:8000/api/health

# Frontend only
cd frontend && npm run dev
# → http://localhost:5173

# Full stack (Docker)
docker compose up

# Demo login credentials
# Admin: admin@agentic.local / admin123
# Client: demo@agentic.local / demo123
```

---

## 8. API

Base URL: `https://ai-agentic-backend-ywdx.onrender.com/api`

Interactive docs: [/docs](https://ai-agentic-backend-ywdx.onrender.com/docs)

### Auth
```
POST /api/auth/login      → { access_token, refresh_token }
POST /api/auth/register   → { access_token, refresh_token }
GET  /api/auth/me         → { email, role, plan }
```

### Agent Actions
```
POST /api/verticals/social/action   → SM agent (40 actions)
POST /api/verticals/ca/action       → CA agent (44 actions)
POST /api/verticals/cs/action       → CS agent (41 actions)
```

**Request format:**
```json
{
  "action": "gst_query",
  "payload": { "query": "GST rate on software services" },
  "language": "en"
}
```

**Response headers:**
- `X-Process-Time: 42.3ms` — per-request latency

All endpoints require `Authorization: Bearer <token>`.

---

## 9. AI Pipeline

```
User input
    ↓
Agent dispatcher (_impl.py)
    ↓
Deterministic layer (for CA: GST rates, TDS calc, ITR grounding)
    ↓
call_llm() → LLM Router
    ↓
[DEMO_MODE=true]  → demo_responder.py (instant, zero cost)
[GROQ_API_KEY]    → Groq (Llama 3, 30 RPM free)
[GEMINI_API_KEY]  → Gemini 2.0 Flash
[OPENAI_API_KEY]  → GPT-4o
[fallback]        → Ollama (llama3.2, local)
    ↓
Response + structured validation
```

**Key design decisions:**
- CA calculations (GST rate, TDS %, ITR form selection) are **deterministic** — never LLM-generated
- GST rate grounding is injected into the prompt as a verified fact before LLM call
- All 4 LLM providers fail → returns a safe fallback string (never crashes)

---

## 10. Database

Schema managed via SQL migrations in `backend/auth/migrations/` and `backend/memory/init.sql`.

Key tables: `users`, `workspaces`, `action_history`, `prompt_versions`

Relationships:
- `users` → `workspaces` (1:many, per-agent config)
- `users` → `action_history` (1:many, audit log)

Indexes on `user_id`, `created_at`, `action` for query performance.

**Local:** PostgreSQL via docker-compose (`pgvector/pgvector:pg16`)
**Production:** Neon free tier (set `DATABASE_URL` in Render environment)

---

## 11. Testing

```bash
# Unit tests (14 pytest)
pytest backend/tests/ -v

# Frontend tests (12 Vitest)
cd frontend && npm test

# QA integration tests (125 actions — runs against live backend)
python qa/qa_sm_full.py     # 40/41 (DALL-E skipped, no key)
python qa/qa_ca_full.py     # 44/44
python qa/qa_cs_full.py     # 41/41

# LLM quality eval (A-F grades)
python qa/eval_llm.py --vertical all

# Load test (p50/p95/p99 latency)
python qa/load_test.py --url http://localhost:8000 --users 5 --duration 30
```

**CI runs automatically on every push** — lint → unit tests → frontend build → smoke test against Render.

---

## 12. Deployment

### Backend → Render (auto-deploy on push to master)

```bash
# Environment variables to set in Render dashboard:
DEMO_MODE=true
GROQ_API_KEY=...          # or GEMINI_API_KEY
JWT_SECRET=...
DATABASE_URL=...          # Neon Postgres
APP_ENV=production
```

### Frontend → Vercel (auto-deploy on push to master)

```bash
# Environment variable in Vercel:
VITE_API_URL=https://ai-agentic-backend-ywdx.onrender.com/api
```

### Smoke test after deploy
```bash
curl https://ai-agentic-backend-ywdx.onrender.com/api/health
```

---

## 13. Performance

Measured via `qa/load_test.py` — 5 concurrent users, 20-second run:

| Mode | p50 | p95 | Error rate | Notes |
|------|-----|-----|------------|-------|
| Deterministic actions (CA calc, invoice, TDS) | 47ms | 50ms | 0% | No LLM — pure Python logic |
| DEMO_MODE=true (Render) | ~35ms | ~120ms | 0% | Canned responses, no LLM call |
| Ollama CPU (local, llama3.2) | 47ms | ~9000ms | 0% | LLM inference on CPU, not GPU |
| Groq API (cloud) | ~200ms | ~600ms | <1% | Estimated from manual testing |

> Key insight: API + routing overhead is **47ms p50**. All latency above that is LLM inference time. On Render with DEMO_MODE=true, the p95 is ~120ms. With a real LLM API (Groq/Gemini), add ~200-600ms for inference.

---

## 14. Limitations

**Current limitations (honest engineering assessment):**

| Limitation | Impact | Mitigation plan |
|-----------|--------|----------------|
| Single Render worker | ~8 RPS max throughput | Upgrade to Render Starter (2 workers) or move to Railway |
| Free tier cold start (30s) | First request after 15-min idle is slow | UptimeRobot ping every 5 min keeps it warm |
| No vector DB / RAG | Answers based on training data, not real-time docs | Add ChromaDB + document upload for v2 |
| DEMO_MODE responses are generic | Canned output doesn't reflect exact user input | Replace with lightweight local LLM (Phi-3 mini) |
| No streaming | Users wait for full response before seeing output | Add SSE streaming endpoint in v2 |
| GST rates hardcoded | Rate changes require code update | Pull from GSTN API in v2 |
| SQLite fallback in dev | History not persisted between restarts | Set DATABASE_URL for persistent Postgres |

**What this version is designed for:** Demos, portfolio projects, MVP validation, interview discussions.
**What it is NOT yet designed for:** 1000+ concurrent users, HIPAA/SOC2 compliance, production billing.

---

## 15. Future Improvements

**v2 Roadmap (Q4 2026):**
- [ ] RAG pipeline: ChromaDB + document upload per client
- [ ] Streaming responses (SSE) for all LLM actions
- [ ] WhatsApp Business API integration (real send)
- [ ] LinkedIn + Buffer OAuth (post scheduling)
- [ ] Multi-language UI (Tamil, Hindi, Marathi)
- [ ] Razorpay billing integration (Free → Starter → Pro)
- [ ] Admin dashboard: usage analytics, cost tracking per tenant
- [ ] Real GSTN portal API integration for live rate lookup
- [ ] Mobile app (React Native, same API)

---

## Project Structure

```
ai-agentic-assistant/
├── backend/
│   ├── main.py                  # FastAPI app, middleware, auth routers
│   ├── config.py                # Pydantic Settings (all env vars)
│   ├── api/                     # Auth, health, vertical routes
│   ├── llm/                     # LLM router, Groq/Gemini/OpenAI/Ollama clients
│   └── verticals/               # SM / CA / CS agents (agent.py + _impl.py)
├── frontend/
│   └── src/
│       ├── pages/               # LandingPage, LoginPage, Dashboard, SM, CA, CS
│       ├── components/          # Shared UI primitives (ui.tsx, Sidebar, WorkspaceSetup)
│       └── lib/                 # API client, workspace hook
├── qa/
│   ├── qa_sm_full.py            # 40 SM action tests
│   ├── qa_ca_full.py            # 44 CA action tests
│   ├── qa_cs_full.py            # 41 CS action tests
│   ├── eval_llm.py              # LLM quality grader (A-F)
│   └── load_test.py             # p50/p95/p99 latency benchmark
├── backend/Dockerfile           # Multi-stage, non-root, healthcheck
├── docker-compose.yml           # Full stack: backend + frontend + postgres + redis + ollama
├── docker-compose.prod.yml      # Production overrides
├── ARCHITECTURE.md              # System design + ADRs
├── ENGINEERING_PLAYBOOK.md      # 17-level production audit framework
└── CHANGELOG.md                 # Full feature history
```

---

## License

MIT © 2026 Chandru Kumar
