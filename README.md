# AI Agentic Assistant V2

> Production enterprise multi-agent AI platform — built for developers, deployed for businesses.

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

> 📸 *[Add dashboard screenshot or Loom recording here — record with OBS/Loom]*

| | |
|---|---|
| **Live Demo** | [ai-agentic-assistant.vercel.app](https://ai-agentic-assistant.vercel.app) |
| **API Docs** | [your-backend.onrender.com/docs](https://your-backend.onrender.com/docs) |
| **Demo Login** | `admin@agentic.local` / `admin123` |
| **GitHub** | [chandrukumar-AIML/ai-agentic-assistant](https://github.com/chandrukumar-AIML/ai-agentic-assistant) |

---

## ✨ Key Features

- **LangGraph Multi-Agent Graph** — Supervisor → Planner → Workers → Reflection loop with self-critique and auto-rewrite on quality failure
- **Dual RAG Engine** — FAISS + ChromaDB vector stores with HyDE query expansion, FlashRank cross-encoder reranking, and semantic caching
- **Voice Pipeline** — Whisper STT → Agent reasoning → Coqui TTS over WebSocket in real time
- **Enterprise Guardrails** — PII/PHI detection (HIPAA 18 Safe Harbor), prompt injection blocking, NeMo Guardrails, full audit logging
- **12 Domain Verticals** — AgriTech, Legal Research, Cybersecurity, HR, Sales CRM, Accountant, Social Media, DevOps and 4 more
- **Human-in-the-Loop (HITL)** — LangGraph interrupt-based approval queue with 30-min auto-reject and Slack/SendGrid notifications
- **Full Observability** — LangSmith tracing, MLflow experiment tracking, Prometheus metrics, per-query cost tracking with budget enforcement
- **MCP + A2A Protocols** — 7-tool Model Context Protocol server + Agent-to-Agent communication (Google open specification)
- **Webhook Manager** — Register Slack/Discord/Zapier/n8n endpoints for 8 event types with HMAC-SHA256 signing
- **Production-Tested** — 50 concurrent users · p95 REST latency 280ms · p95 WebSocket 4.2s · 0.3% error rate

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
| Frontend | React 18 + TypeScript + Vite | SPA dashboard (25 pages) |
| State Management | Zustand | Client-side chat state |
| Auth | JWT + RBAC | Workspace isolation, plan tiers |
| Deploy | Render + Vercel + Neon + Upstash | Full stack · **$0/month** |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│           React 18 + TypeScript Frontend (Vercel)               │
│  Landing · Login · Dashboard · Chat · 12 Verticals              │
│  Knowledge Base · Webhooks · Settings · Notifications           │
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
│   ├── src/pages/       # 25 pages (Landing, Login, Dashboard, 12 verticals...)
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

# 2. Edit .env with your API keys (minimum required):
#    OPENAI_API_KEY, JWT_SECRET, TAVILY_API_KEY, LANGCHAIN_API_KEY

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

See [`deploy/free_deploy_guide.md`](deploy/free_deploy_guide.md) for the full 7-phase step-by-step guide.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Service health + Redis + OpenAI + circuit state |
| POST | `/api/auth/login` | JSON body JWT login |
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

## 🌐 12 Domain Verticals

| Vertical | Key Capabilities |
|---|---|
| 🌾 **AgriTech** | Tamil/Hindi/English crop advisory, Mandi price lookup, weather integration, Govt schemes |
| ⚖️ **Legal Research** | IndianKanoon + IPC/CrPC/IT Act Bare Acts RAG, case search, legal advice |
| 🔐 **Cybersecurity** | SSH/SQL/XSS log anomaly detection, NVD CVE lookup, incident reports, Slack alerts |
| ☎️ **Receptionist** | Twilio Voice IVR, WhatsApp Business API, Calendly booking, embeddable JS widget |
| 📋 **Form Reader** | GPT-4V OCR for PAN/Aadhaar/GSTIN/Passport, Verhoeff check, structured JSON output |
| 📧 **Email Manager** | Gmail API + Microsoft Graph (Outlook), AI draft generation, HITL before send |
| 💼 **Sales & CRM** | BANT lead scoring (100pts), HubSpot CRM, Salesforce, Clearbit enrichment |
| 🧮 **Accountant** | GST/TDS calculator, CGST+SGST/IGST split, GSTR-1/3B export, India tax rules |
| 👥 **HR Assistant** | Resume screening (0–100 score), JD generation, offer letter, BGV checklist |
| 📱 **Social Media** | LinkedIn/Twitter/Instagram content, DALL-E 3 image generation, Buffer scheduling |
| 📊 **Data Analyst** | Natural language → SQL → run → Plotly charts (powered by connected database) |
| ⚙️ **DevOps Engineer** | GitHub CI/CD, Docker log analysis, Prometheus metrics, Jira ticket creation |

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
OPENAI_API_KEY=sk-...           # OpenAI API key
JWT_SECRET=your-32-char-secret  # Min 32 characters
TAVILY_API_KEY=tvly-...         # Web search
LANGCHAIN_API_KEY=ls__...       # LangSmith tracing

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
# Unit tests only (no backend needed)
PYTHONPATH=$(pwd) pytest backend/tests/ \
  --ignore=backend/tests/test_integration.py \
  --ignore=backend/tests/test_rag.py \
  --ignore=backend/tests/test_load.py \
  -v

# All tests (requires running backend + services)
PYTHONPATH=$(pwd) pytest backend/tests/ -v

# Frontend type check + build
cd frontend && npm run build
```

---

## 📁 Project Stats

```
Backend Python files:     182 modules
Frontend TypeScript files: 48 files (25 pages + 20 components + hooks/lib)
API Endpoints:             133 routes (72 POST · 50 GET · 7 DELETE · 4 PATCH)
Enterprise Features:       24
Domain Verticals:          12
Build Phases:              15
Unit Tests:                81 passing
Total lines of code:       ~39,000
Deploy cost:               $0/month
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with LangGraph · FastAPI · React 18 · TypeScript**

*Production-ready · $0/month free tier · Deploy in 30 minutes*

[⭐ Star this repo](https://github.com/chandrukumar-AIML/ai-agentic-assistant) · [🐛 Report Bug](https://github.com/chandrukumar-AIML/ai-agentic-assistant/issues) · [💡 Request Feature](https://github.com/chandrukumar-AIML/ai-agentic-assistant/issues)

</div>
