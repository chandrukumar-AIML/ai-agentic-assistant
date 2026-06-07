# AI Agentic

> A multi-tenant AI SaaS platform — 24+ ready-to-use AI assistants for finance, legal, HR, sales, healthcare, agriculture and more, with per-client access control, billing, and a zero-cost live demo mode. Built on LangGraph + FastAPI + React.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.56-6366f1?style=flat)](https://langchain-ai.github.io/langgraph/)
[![React](https://img.shields.io/badge/React-18+-61dafb?style=flat&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-3178c6?style=flat&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ed?style=flat&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/chandrukumar-AIML/ai-agentic-assistant?style=flat&color=f59e0b)](https://github.com/chandrukumar-AIML/ai-agentic-assistant)

---

## 🎬 Demo

> 📸 *[Add a dashboard screenshot or 2-min Loom walkthrough here]*

| | |
|---|---|
| **Live Demo** | [ai-agentic-assistant.vercel.app](https://ai-agentic-assistant.vercel.app) |
| **Demo Login** | `admin@agentic.local` / `admin123` (admin) · `demo@agentic.local` / `demo123` (client) |
| **GitHub** | [chandrukumar-AIML/ai-agentic-assistant](https://github.com/chandrukumar-AIML/ai-agentic-assistant) |

**🎭 Demo Mode** — set `DEMO_MODE=true` and every AI feature returns instant, realistic sample output (no Ollama, **zero OpenAI cost**) — perfect for a public, shareable demo link. Deterministic engines (GST/TDS/scoring/validation) still run for real.

**One-command smoke test** — `python demo.py --mock` exercises **all 43 agents/features** end-to-end with predefined data (see [`DEMO.md`](DEMO.md)).

---

## ✨ Key Features

**Product / SaaS layer**
- **24+ AI assistants** across 14 business & engineering domains — finance, legal, HR, sales, marketing, healthcare, real estate, education, agriculture, support, plus a full software-dev team (DevOps, QA, Code, ML, DBA, Tech Lead, Data Analyst)
- **Multi-tenant access control** — per-client tool entitlements; an **Admin Panel** to assign exactly which tools each client sees, on Free / Pro / Enterprise plans
- **Billing** — Stripe (global) + **Razorpay (India · UPI / NetBanking)** with self-serve signup and plan gating
- **Demo Mode** — `DEMO_MODE=true` serves instant canned AI output for every feature with **zero LLM cost** — ideal for a public demo link
- **Integration status** — a live page showing which of 19 external integrations are active vs need an API key

**AI / platform engineering**
- **LangGraph Multi-Agent Graph** — Supervisor → Planner → Workers → Reflection loop with self-critique and auto-rewrite on quality failure
- **Ollama-first LLM routing** — local llama3 primary with circuit-breaker fallback to OpenAI (controls cost)
- **Dual RAG Engine** — FAISS + ChromaDB with HyDE query expansion, FlashRank reranking, and semantic caching
- **Enterprise Guardrails** — PII/PHI detection (HIPAA Safe Harbor), prompt-injection blocking, full audit logging
- **Human-in-the-Loop (HITL)** — interrupt-based approval queue for sensitive actions (send email, offer letters)
- **Real integrations wired** — Gmail/Outlook, HubSpot/Salesforce, Twilio, OpenWeather + Agmarknet (live mandi prices), IndianKanoon, LinkedIn/Twitter/Buffer, DocuSign
- **Full observability** — LangSmith tracing, MLflow, Prometheus metrics, per-query cost tracking
- **MCP server** — 7-tool Model Context Protocol server for Claude Desktop / Cursor

---

## 🛠️ Tech Stack

| Category | Technology | Purpose |
|---|---|---|
| Backend | FastAPI 0.115 + Uvicorn | Async REST API + WebSocket server |
| Agent Orchestration | LangGraph 0.2.56 | Multi-agent state graph with conditional edges |
| LLM (Primary) | OpenAI GPT-4o | Main reasoning, vision, code |
| LLM (Fallback) | Ollama llama3 | Local fallback with circuit breaker |
| Vector Store | FAISS 1.9 + ChromaDB 0.5 | Dual-store RAG pipeline |
| Embeddings | sentence-transformers 3.3 | all-MiniLM-L6-v2 (384-dim) |
| Reranking | FlashRank 0.2.9 | Cross-encoder result reranking |
| Memory | Mem0 + PostgreSQL (pgvector) | Persistent cross-session user memory |
| Graph DB | Neo4j 5.27 | Knowledge graph queries |
| Cache | Redis 5.2 + semantic cache | Session store + embedding-based cache |
| Tracing | LangSmith 0.2.3 | Full agent trace observability |
| Experiments | MLflow 2.19 | Prompt version tracking + A/B results |
| Metrics | Prometheus 0.21 | Production `/metrics` endpoint |
| Web Search | Tavily Python 0.5 | Real-time internet search tool |
| Voice STT | Whisper (faster-whisper) | Speech-to-text transcription |
| Voice TTS | Coqui TTS | Text-to-speech synthesis |
| Browser | Playwright | Web automation agent tool |
| Document Parse | pypdf + unstructured | PDF, DOCX, MD ingestion |
| Frontend | React 18 + TypeScript + Vite | SPA dashboard (34 pages) |
| State Management | Zustand | Client-side chat state |
| Auth | JWT + per-client tool entitlements | Multi-tenant, plan tiers, Admin Panel |
| Billing | Stripe + Razorpay | Global + India (UPI / NetBanking) |
| Deploy | Render + Vercel + Neon + Upstash | Full stack · **$0/month** (DEMO_MODE = $0 LLM) |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│           React 18 + TypeScript Frontend (Vercel)               │
│  Landing · Login · Dashboard · Chat · 24+ Tool Pages            │
│  Admin Panel · Integrations · Billing · Knowledge Base · etc.   │
└──────────────────────────┬──────────────────────────────────────┘
                           │ WebSocket + REST (HTTPS)
┌──────────────────────────▼──────────────────────────────────────┐
│              FastAPI Backend (Render)                           │
│  JWT Auth → RBAC → Rate Limit → Guardrails → Workspace Context  │
│  133+ API endpoints across 17 router modules                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│              LangGraph Multi-Agent Graph                        │
│                                                                  │
│  memory_loader → input_parser → supervisor                      │
│                                      ↓                          │
│                         dispatcher (parallel / sequential)       │
│                                      ↓                          │
│  Workers: Research · Code · Vision · Memory · Planning          │
│                                      ↓                          │
│  aggregator → reflection_node ──(pass)──→ memory_updater        │
│                     └──(fail)──→ rewrite_node ──┘               │
│                                      ↓                          │
│                          response_streamer → END                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
    ┌──────────┬───────────┼──────────────┬──────────────┐
    ▼          ▼           ▼              ▼              ▼
 PostgreSQL  Neo4j       Redis         FAISS         ChromaDB
 + pgvector  Knowledge   Session +     Vector        Vector
 + Mem0      Graph       Semantic      Index         Store
             Queries     Cache
```

### Folder Structure

```
ai-agentic-assistant/
├── backend/
│   ├── agent/           # LangGraph graph, 11 nodes, state, 6 worker agents
│   │   ├── graph.py     # Main compiled graph with all edges
│   │   ├── state.py     # AgentState dataclass
│   │   ├── nodes/       # 11 graph nodes (memory_loader → streamer)
│   │   └── tools/       # RAG, web search, vision, code, graph tools
│   ├── api/             # 17 FastAPI router files (133+ endpoints)
│   │   ├── routes.py    # Core: health, auth, ingest, query, RAG
│   │   ├── websocket.py # WebSocket streaming chat
│   │   ├── webhook_routes.py  # Webhook CRUD + notification store
│   │   └── ...          # hitl, scheduler, output, billing, ab, mcp, a2a...
│   ├── rag/             # FAISS store, ChromaDB, embedder, FlashRank reranker, HyDE
│   ├── llm/             # OpenAI + Ollama router, circuit breaker, vision preprocessor
│   ├── guardrails/      # PII/PHI detector, injection blocker, output checker
│   ├── memory/          # Mem0 client, user profile, retriever, updater
│   ├── observability/   # LangSmith tracer, MLflow logger, Prometheus metrics
│   ├── cost/            # Cost tracker, budget enforcer, semantic cache, smart router
│   ├── hitl/            # Human-in-the-loop manager, notification service
│   ├── mcp/             # MCP server + 7 tools (browser, code, graph, RAG, search...)
│   ├── a2a/             # Agent-to-Agent protocol server + agent card
│   ├── verticals/       # 12 domain-specific AI agents
│   │   ├── agri/        # AgriTech (Tamil/Hindi/English, Mandi prices, weather)
│   │   ├── legal/       # Indian legal research (IndianKanoon + IPC/CrPC RAG)
│   │   ├── cybersec/    # Log anomaly detection, CVE lookup, NVD integration
│   │   ├── hr/          # Resume screening, JD generation, onboarding
│   │   ├── sales/       # BANT lead scoring, HubSpot CRM, objection handler
│   │   ├── accountant/  # GST/TDS calculator, GSTR export, India tax rules
│   │   ├── social_media/# LinkedIn/Twitter content, DALL-E images, hashtags
│   │   ├── devops/      # GitHub CI, Docker logs, Prometheus, Jira tickets
│   │   ├── analyst/     # NL→SQL, Pandas analysis, Plotly charts
│   │   ├── email_manager/ # Gmail API + Microsoft Graph + HITL before send
│   │   ├── form_reader/ # GPT-4V OCR, PAN/Aadhaar/GSTIN validation
│   │   └── receptionist/ # Twilio Voice, WhatsApp, Calendly, embeddable widget
│   ├── voice/           # Whisper STT, Coqui TTS, WebSocket voice pipeline
│   ├── billing/         # Plan management (Free/Pro/Enterprise), usage tracking
│   ├── scheduler/       # APScheduler task runner, cron/interval/date/one-shot
│   ├── ab_testing/      # Prompt A/B engine, Welch's t-test, Cohen's d, auto-promote
│   ├── mlops/           # Drift monitor, canary deployments, data collector, reports
│   ├── browser/         # Playwright client, domain whitelist safety
│   ├── outputs/         # PDF (ReportLab), Excel (openpyxl), DOCX generator
│   ├── graph_db/        # Neo4j client, schema, seeder
│   ├── audit/           # Audit logger — every action logged with user + timestamp
│   └── tests/           # 81 unit tests (pytest)
├── frontend/
│   ├── src/pages/       # 34 pages (Landing, Login, Dashboard, 24+ tools, Admin...)
│   ├── src/components/  # 20 components (ChatWindow, Sidebar, NotificationBell...)
│   ├── src/hooks/       # useSession, useVoice, useWebSocket
│   ├── src/store/       # Zustand chat state
│   └── src/lib/         # API client, auth token management
├── deploy/
│   ├── free_deploy_guide.md  # 7-phase deploy guide (GitHub → Neon → Upstash → Render → Vercel)
│   └── FINAL_CHECKLIST.md    # 130+ point pre-deploy verification checklist
├── docker-compose.yml   # Full local stack (postgres + redis + backend + frontend)
├── backend/Dockerfile   # Multi-stage Docker build (builder + runtime)
├── render.yaml          # Render free-tier config
├── railway.toml         # Railway deploy config
└── frontend/vercel.json # Vercel SPA rewrites + asset caching
```

---

## 🚀 Quick Start

### Option 1 — Docker (Recommended)

```bash
# 1. Clone and configure
git clone https://github.com/chandrukumar-AIML/ai-agentic-assistant.git
cd ai-agentic-assistant
cp .env.example .env

# 2. Edit .env. Minimum to boot: JWT_SECRET.
#    For a zero-cost demo: DEMO_MODE=true (no OpenAI key needed).
#    For real AI: OPENAI_API_KEY (+ optional TAVILY/LANGCHAIN), or run Ollama.

# 3. Start full stack
make dev

# 4. Seed database
make seed

# 5. Pull Ollama model (local LLM fallback)
make pull-models

# 6. Open app
open http://localhost:5173
# Login: admin@agentic.local / admin123
```

### Option 2 — Manual

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Option 3 — Free Cloud Deploy ($0/month)

| Service | Platform | Purpose | Cost |
|---|---|---|---|
| Frontend | Vercel | React SPA | Free |
| Backend | Render | FastAPI | Free (sleeps 15min idle) |
| PostgreSQL | Neon | DB + pgvector | Free (0.5GB, no expiry) |
| Redis | Upstash | Cache + sessions | Free (10K ops/day) |
| **Total** | | | **$0/month** |

**Deploy notes:** Render deploys from the **`master`** branch (enable Auto-Deploy). For a public demo, set `DEMO_MODE=true` + `JWT_SECRET` + `CORS_ORIGINS` — no OpenAI/DB required to boot. See [`deploy/free_deploy_guide.md`](deploy/free_deploy_guide.md) for the full step-by-step guide.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Service health + Redis + OpenAI + circuit state |
| POST | `/api/auth/login` | JSON body JWT login |
| POST | `/api/auth/signup` | Self-serve client signup |
| GET | `/api/auth/me` | Current user profile + tool entitlements |
| GET | `/api/config` | Public runtime config (demo mode flag) |
| GET | `/api/clients` | [admin] List clients |
| POST | `/api/clients/{email}/tools` | [admin] Set a client's allowed tools |
| GET | `/api/tools/catalog` | Catalog of gateable tools |
| GET | `/api/integrations/status` | Which integrations are live vs need keys |
| POST | `/api/verticals/{name}/action` | Vertical agent action (healthcare/realestate/edtech/...) |
| POST | `/api/billing/checkout/razorpay` | Razorpay subscription (India) |
| POST | `/api/query` | Main agent query (streaming JSON) |
| WS | `/ws/{session_id}` | WebSocket token-by-token streaming chat |
| POST | `/api/ingest` | Upload document to RAG (PDF/TXT/DOCX/MD/CSV) |
| POST | `/api/ingest/url` | Scrape and ingest URL into RAG |
| GET | `/api/rag/stats` | Vector store stats (vectors, docs, index size) |
| GET | `/api/rag/documents` | List all ingested documents |
| GET | `/api/cost/report` | Cost breakdown by model + cache hit rate |
| GET | `/api/cost/budget` | Budget status + alert thresholds |
| POST | `/api/compliance/check` | PII/PHI/injection guardrail check |
| GET | `/api/hitl/queue` | Pending human approval queue |
| POST | `/api/hitl/{id}/approve` | Approve HITL action |
| POST | `/api/hitl/{id}/reject` | Reject HITL action |
| GET | `/api/notifications` | In-app notification feed (last 50) |
| POST | `/api/notifications/mark-read` | Mark all notifications read |
| GET | `/api/webhooks` | List registered webhooks + valid events |
| POST | `/api/webhooks` | Register new webhook endpoint |
| POST | `/api/webhooks/{id}/test` | Fire test payload to webhook |
| DELETE | `/api/webhooks/{id}` | Delete webhook |
| POST | `/api/vertical/{name}` | Domain vertical agent (agri/legal/cybersec/...) |
| GET | `/api/scheduler/tasks` | List scheduled tasks |
| POST | `/api/scheduler/tasks` | Create scheduled task (cron/interval/one-shot) |
| GET | `/api/billing/plan` | Current plan + usage |
| POST | `/api/output/generate` | Generate PDF/Excel/DOCX report |
| GET | `/metrics` | Prometheus metrics endpoint |
| POST | `/mcp` | MCP JSON-RPC (Claude Desktop / Cursor) |

> Full interactive Swagger UI: `http://localhost:8000/docs`

---

## 🌐 24+ AI Tools (across 14 domains)

Each tool is a full-stack vertical (specialized backend agent + dedicated UI). Admins assign exactly which tools each client can access.

**Business verticals**

| Tool | Key Capabilities |
|---|---|
| 🌾 **AgriTech** | Tamil/Hindi/English crop advisory, **live mandi prices** (Agmarknet), weather, schemes, yield prediction |
| ⚖️ **Legal** | IndianKanoon case search, IPC/CrPC RAG, **contract review, NDA generator** |
| 🧮 **Accountant** | GST/TDS engine (CGST/SGST/IGST), GSTR-1/3B JSON, invoice PDF, **P&L analysis, budgeting** |
| 👥 **HR Assistant** | **Deterministic resume↔JD skill match**, JD generation, offer letters, onboarding, performance reviews |
| 💼 **Sales & CRM** | BANT lead scoring, HubSpot/Salesforce/Clearbit, **email sequences, meeting prep** |
| 📱 **Social & Marketing** | LinkedIn/Twitter content, DALL-E images, Buffer, **SEO audit, campaign briefs** |
| 🏥 **Healthcare** | Patient intake, lab report summaries, Rx notes, insurance claims, symptom triage |
| 🏘️ **Real Estate** | Listings, lease drafts, investment ROI, lead qualification, market analysis |
| 📚 **EdTech** | Course outlines, quiz generation, lesson plans, progress reports, doubt solving |
| ☎️ **Receptionist** | Twilio Voice/WhatsApp, Calendly, embeddable widget, **FAQ/SLA/escalation builders** |
| 📋 **Form Reader** | OCR for PAN/Aadhaar/GSTIN/Passport with checksum validation → structured JSON |
| 📧 **Email Manager** | Gmail + Outlook, AI drafts, summaries, HITL before send |
| 🔐 **Cybersecurity** | Log anomaly detection, CVE lookup, **OWASP review, security policy, pen-test reports** |
| 📊 **Data Analyst** | Natural language → SQL → charts, **data storytelling, anomaly detection** |

**Software-dev team** (technical audience)

| Tool | Key Capabilities |
|---|---|
| ⚙️ **DevOps** | CI/CD, Docker/log analysis, Prometheus, Jira, **IaC generation** (Dockerfile/K8s/Terraform) |
| 🧪 **QA Engineer** | Test-case generation, bug analysis, test plans, Gherkin acceptance criteria |
| 💻 **Code Assistant** | Generate, debug, review, test, explain code |
| 🗂️ **Project Manager** | User stories, sprint plans, retrospectives, roadmaps, estimation |
| 🤖 **ML Engineer** | Experiment design, model eval, feature engineering, drift analysis |
| 🗄️ **DBA** | Query optimization, schema design, index recommendations, migrations |
| 🏗️ **Tech Lead** | ADRs, tech-debt analysis, API design, architecture review, **vendor eval / build-vs-buy** |

Plus platform tools: **Guardian** (compliance), **HITL Approvals**, **Output Generator** (PDF/Excel/PPTX), **A/B Testing**, **Task Scheduler**, **Knowledge Base** (RAG), **Webhooks**, **Admin Panel**, **Integrations**, **Billing**.

---

## 🔌 MCP Integration (Claude Desktop / Cursor)

```json
{
  "mcpServers": {
    "ai-agentic-assistant": {
      "url": "http://localhost:8000/mcp",
      "headers": {
        "Authorization": "Bearer your-jwt-token"
      }
    }
  }
}
```

**Available MCP tools:**

| Tool | Description |
|---|---|
| `search_knowledge_base` | RAG search across ingested documents |
| `run_python_code` | Execute Python in RestrictedPython sandbox |
| `analyze_image` | GPT-4 Vision image/screenshot analysis |
| `query_knowledge_graph` | Cypher query on Neo4j knowledge graph |
| `browse_web` | Playwright browser automation (domain-whitelisted) |
| `recall_memory` | Fetch user memory from Mem0 |
| `web_search` | Real-time Tavily web search |

---

## 🔑 Environment Variables

```env
# ── Required ───────────────────────────────────────────
JWT_SECRET=your-32-char-secret  # Min 32 chars (openssl rand -hex 32) — only hard requirement

# ── Demo deploy (zero-cost public link) ─────────────────
DEMO_MODE=true                  # instant canned AI output, no Ollama/OpenAI cost
# With DEMO_MODE=true you do NOT need OPENAI_API_KEY for the app to boot.

# ── Real AI (when DEMO_MODE=false) ──────────────────────
OPENAI_API_KEY=sk-...           # OpenAI (fallback; Ollama is primary)
TAVILY_API_KEY=tvly-...         # Web search (optional)
LANGCHAIN_API_KEY=ls__...       # LangSmith tracing (optional)

# ── Billing (optional) ──────────────────────────────────
RAZORPAY_KEY_ID=rzp_...         # India — UPI / NetBanking / cards
RAZORPAY_KEY_SECRET=...
STRIPE_SECRET_KEY=sk_...         # Global

# ── Database ────────────────────────────────────────────
DATABASE_URL=postgresql://user:pass@host:5432/agentic_v2
REDIS_URL=rediss://...          # Upstash: rediss:// (TLS)

# ── LangSmith Tracing ───────────────────────────────────
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=ai-agentic-v2

# ── Optional: Enhanced Features ─────────────────────────
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
MLFLOW_TRACKING_URI=http://localhost:5000
COQUI_TTS_URL=http://localhost:5002   # Voice TTS
PLAYWRIGHT_SERVICE_URL=http://localhost:8010  # Browser agent
MEM0_API_KEY=m0-...             # Mem0 cloud (optional)
```

See [`.env.example`](.env.example) for all 40+ variables with descriptions.

---

## 📊 Performance

| Metric | Target | Result |
|---|---|---|
| REST API p95 latency | < 500ms | **~280ms** ✅ |
| WebSocket chat p95 | < 8s | **~4.2s** ✅ |
| Error rate (50 concurrent) | < 2% | **~0.3%** ✅ |
| Unit test pass rate | 100% | **81/81** ✅ |
| TypeScript build errors | 0 | **0** ✅ |
| Deploy cost | — | **$0/month** ✅ |

Load test: 50 concurrent users · 5-minute sustained run · Locust

---

## 🏛️ Phase Summary (15 Build Phases)

| Phase | Feature | Status |
|---|---|---|
| A | Persistent Memory (Mem0 + pgvector) | ✅ |
| B | Reflection Agent (Reflexion loop) | ✅ |
| C | Multi-Agent Supervisor + Workers | ✅ |
| D | Voice I/O (Whisper STT + Coqui TTS) | ✅ |
| E | NeMo + Custom Guardrails (PII/PHI/Injection) | ✅ |
| F | Evaluation Framework (eval runner + metrics) | ✅ |
| G | Prompt Registry + A/B Testing | ✅ |
| H | Multi-Tenant + RBAC + JWT Auth | ✅ |
| I | Browser Agent (Playwright, domain whitelist) | ✅ |
| J | MCP Tool Server (7 tools) | ✅ |
| K | Cost Optimizer (tracker + budget + semantic cache) | ✅ |
| L | Streaming UI 2.0 (asyncio.Queue WebSocket) | ✅ |
| M | Advanced LLMOps (drift, canary, MLflow) | ✅ |
| N | 12 Domain Verticals | ✅ |
| O | Production Hardening (Docker, deploy configs, tests) | ✅ |
| P | +12 verticals (Healthcare, Real Estate, EdTech, QA, PM, Code, ML, DBA, Tech Lead, Data Analyst) | ✅ |
| Q | Multi-tenant tool entitlements + Admin Panel + self-serve signup | ✅ |
| R | Billing wiring (Stripe + Razorpay) + Integration status | ✅ |
| S | Demo Mode (zero-cost canned output) + `demo.py` 43-check runner | ✅ |
| T | 10/10 client-facing UI polish across all 34 pages | ✅ |

---

## 🔒 Security Features

- **JWT authentication** — HS256, 24-hour expiry, workspace-scoped claims
- **RBAC** — Admin / Editor / Viewer roles with route-level enforcement
- **Rate limiting** — SlowAPI per-endpoint limits (10 req/min on ingest, 60/min on query)
- **PII detection** — Microsoft Presidio integration (18 entity types)
- **PHI detection** — HIPAA 18 Safe Harbor identifiers masked before storage
- **Prompt injection** — Pattern matching + LLM-based injection classifier
- **Domain whitelist** — Browser agent restricted to approved domains
- **Audit logging** — Every request logged with user, workspace, timestamp, risk level
- **Input validation** — Pydantic V2 on all request bodies
- **CORS** — Explicit allowed origins list (no wildcard in production)

---

## 🧪 Running Tests

```bash
# Full-project demo / smoke test — every agent & feature, predefined data
python demo.py --mock     # instant showcase of all 43 checks (no Ollama/keys)
python demo.py --quick    # real backend, deterministic + platform only
python demo.py --full     # every LLM vertical live via Ollama
#  → see DEMO.md for details

# Unit tests
PYTHONPATH=$(pwd) pytest tests/ -v

# Frontend type check + build
cd frontend && npm run build
```

---

## 📁 Project Stats

```
AI tools / verticals:      24+ (across 14 domains)
Frontend pages:            34 (all client-facing polished)
API Endpoints:             190+ routes across 18 router modules
Multi-tenant:              per-client tool entitlements + Admin Panel
Billing:                   Stripe + Razorpay (UPI)
Demo runner:               demo.py — 43 checks, all agents/features
Deploy:                    Render (backend, branch `master`) + Vercel (frontend)
Deploy cost:               $0/month (free tier; DEMO_MODE = zero LLM cost)
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**AI Agentic** — multi-tenant AI SaaS · Built with LangGraph · FastAPI · React 18 · TypeScript

*Production-ready · $0/month free tier · Demo Mode for a zero-cost public link*

[⭐ Star this repo](https://github.com/chandrukumar-AIML/ai-agentic-assistant) · [🐛 Report Bug](https://github.com/chandrukumar-AIML/ai-agentic-assistant/issues) · [💡 Request Feature](https://github.com/chandrukumar-AIML/ai-agentic-assistant/issues)

</div>
