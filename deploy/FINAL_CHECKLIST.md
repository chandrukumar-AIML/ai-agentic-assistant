# AI Agentic Assistant V2 — Final Pre-Deploy Checklist
> Generated: 2026-05-29 | Use this for manual verification before going live

---

## ✅ SECTION 1 — LANDING PAGE (Public, No Login)

| # | Check | Expected | Status |
|---|---|---|---|
| 1.1 | Open app URL (no login) | Landing page shown (NOT dashboard) | ☐ |
| 1.2 | Navbar | "AI Agentic v2.0" logo + GitHub + Sign In button | ☐ |
| 1.3 | Hero headline | "Enterprise Multi-Agent AI Platform" | ☐ |
| 1.4 | Stats bar | 24 Features · 12 Verticals · 133+ APIs · 182 Modules | ☐ |
| 1.5 | Feature cards | 8 cards: LangGraph, RAG, Guardrails, Voice, HITL, Observability, MCP+A2A, 12 Verticals | ☐ |
| 1.6 | Verticals grid | All 12 tiles: AgriTech, Legal, Cybersec, Receptionist, Form Reader, Email, Sales, Accountant, HR, Social, Analyst, DevOps | ☐ |
| 1.7 | Tech stack | 16 badges visible (FastAPI, LangGraph, OpenAI GPT-4o, Ollama, React, TS, FAISS, ChromaDB, PG, Redis, Neo4j, LangSmith, MLflow, Prometheus, Docker, Whisper) | ☐ |
| 1.8 | "Why stands out" section | 6 value props visible | ☐ |
| 1.9 | "Launch Dashboard" button | Navigates to Login page | ☐ |
| 1.10 | "Sign In →" navbar button | Navigates to Login page | ☐ |
| 1.11 | Footer | GitHub link, API Docs link, Sign In link | ☐ |

---

## ✅ SECTION 2 — LOGIN PAGE

| # | Check | Expected | Status |
|---|---|---|---|
| 2.1 | Login form loads | Email pre-filled with admin@agentic.local | ☐ |
| 2.2 | Demo credentials box | Shows admin@agentic.local / admin123 | ☐ |
| 2.3 | Login with admin123 (backend running) | Redirects to Dashboard | ☐ |
| 2.4 | Wrong password | Red error banner appears | ☐ |
| 2.5 | No backend error | "Failed to fetch" error shows cleanly | ☐ |

---

## ✅ SECTION 3 — SIDEBAR NAVIGATION

| # | Check | Expected | Status |
|---|---|---|---|
| 3.1 | Logo + version | "AI Agentic v2.0 • 24 Features" | ☐ |
| 3.2 | 🔔 Notification Bell | Bell icon visible in header, click shows dropdown | ☐ |
| 3.3 | Notification dropdown | "All caught up!" when empty, lists alerts when present | ☐ |
| 3.4 | OVERVIEW group | Dashboard ⚡, AI Chat 💬 | ☐ |
| 3.5 | AI CORE group | Guardian F1, HITL F6, Output F7, A/B F12, Scheduler F4 | ☐ |
| 3.6 | VERTICALS group | 12 items F9→V2 all present | ☐ |
| 3.7 | SETTINGS group | Billing F8, Knowledge Base RAG, Webhooks NEW, Settings ⚙️ | ☐ |
| 3.8 | Active highlight | Current page highlights with purple left border | ☐ |
| 3.9 | Collapse toggle | ☰ button collapses to icon-only mode | ☐ |
| 3.10 | Footer | "Backend: port 8000" green dot visible | ☐ |

---

## ✅ SECTION 4 — DASHBOARD

| # | Check | Expected | Status |
|---|---|---|---|
| 4.1 | Page title | "AI Agentic Assistant V2 · Enterprise Multi-Agent Platform" | ☐ |
| 4.2 | Stat cards | Total Features, API Endpoints, LLM Model, Compliance % | ☐ |
| 4.3 | Tech stack badges | FastAPI, LangGraph, OpenAI GPT-4o, Ollama Llama3, FAISS+ChromaDB, Redis+Postgres, MLflow+LangSmith, Presidio PII | ☐ |
| 4.4 | Feature list | All 19+ market features listed with Live badges | ☐ |
| 4.5 | Live clock | Current date/time updating | ☐ |

---

## ✅ SECTION 5 — AI CHAT

| # | Check | Expected | Status |
|---|---|---|---|
| 5.1 | Page loads | "AI Chat" header with Memory + Clear buttons | ☐ |
| 5.2 | WebSocket status (no backend) | "Connecting…" → "Reconnecting in X.0s…" | ☐ |
| 5.3 | WebSocket status (backend up) | Green dot "Connected" | ☐ |
| 5.4 | Chat input | "Ask anything…" placeholder, Shift+Enter for newline | ☐ |
| 5.5 | Voice button 🎙️ | Microphone icon visible, click records audio | ☐ |
| 5.6 | Send message (backend up) | Message appears, streaming response with dots | ☐ |
| 5.7 | Source cards | RAG sources appear below response | ☐ |
| 5.8 | Reasoning steps | Agent thinking steps collapsible | ☐ |
| 5.9 | GuardBadge | PII/PHI warnings shown on risky responses | ☐ |
| 5.10 | Memory panel | Click Memory → shows user memory from Mem0 | ☐ |

---

## ✅ SECTION 6 — GUARDIAN (Compliance)

| # | Check | Expected | Status |
|---|---|---|---|
| 6.1 | Page loads | "Guardian Compliance Agent" + F1 badge | ☐ |
| 6.2 | Test samples | SAFE ✓, PII RISK, PHI RISK, GDPR RISK, XSS RISK visible | ☐ |
| 6.3 | Click PHI sample | Pre-fills with medical record text | ☐ |
| 6.4 | Frameworks listed | HIPAA 18 Safe Harbor, GDPR Art.6/17/44-49, SOC2 Type II | ☐ |
| 6.5 | Check Compliance (backend up) | Returns risk level + violations found | ☐ |

---

## ✅ SECTION 7 — HITL APPROVALS

| # | Check | Expected | Status |
|---|---|---|---|
| 7.1 | Page loads | Stats: Total / Pending / Approved / Rejected | ☐ |
| 7.2 | Empty queue | "No pending approvals! All actions up to date." | ☐ |
| 7.3 | Refresh button | Reloads queue from backend | ☐ |
| 7.4 | Pending item (backend up) | Shows Approve ✓ / Reject ✗ buttons | ☐ |

---

## ✅ SECTION 8 — OUTPUT GENERATOR

| # | Check | Expected | Status |
|---|---|---|---|
| 8.1 | 3 tabs | PDF Report, Excel, PowerPoint | ☐ |
| 8.2 | PDF form | Report Title + Executive Summary + Sections | ☐ |
| 8.3 | "Generate PDF" | Downloads file (backend up) | ☐ |
| 8.4 | Excel form | Columns + rows, table structure | ☐ |

---

## ✅ SECTION 9 — A/B TESTING

| # | Check | Expected | Status |
|---|---|---|---|
| 9.1 | Tabs | Experiments / Run Test / Statistics / New Experiment | ☐ |
| 9.2 | Empty state | "No experiments yet. Create one to start!" | ☐ |
| 9.3 | New Experiment form (backend up) | Variant A/B prompt fields, sample size, create button | ☐ |
| 9.4 | Statistics tab (backend up) | Win rate, p-value, Cohen's d, auto-promote logic | ☐ |

---

## ✅ SECTION 10 — TASK SCHEDULER

| # | Check | Expected | Status |
|---|---|---|---|
| 10.1 | Stats | Total / Active / Paused counts | ☐ |
| 10.2 | Create form | Task Name, Task Type dropdown, Cron input | ☐ |
| 10.3 | Quick-pick schedules | Every minute / Every hour / Daily 9am / Weekly Mon buttons | ☐ |
| 10.4 | Cron syntax pre-filled | "0 9 * * *" for daily 9am | ☐ |
| 10.5 | Task list (backend up) | Shows active tasks with pause/delete controls | ☐ |

---

## ✅ SECTION 11 — VERTICALS (12 Domain Agents)

### 11A — AgriTech
| # | Check | Expected | Status |
|---|---|---|---|
| 11A.1 | Tabs | AI Query / Mandi Prices / Weather / Govt Schemes | ☐ |
| 11A.2 | Language selector | English / Hindi / Tamil | ☐ |
| 11A.3 | Sample query | "What is the best time to plant tomatoes in Tamil Nadu?" pre-loaded | ☐ |
| 11A.4 | Get Advisory (backend up) | Returns crop advisory response | ☐ |

### 11B — Legal Research
| # | Check | Expected | Status |
|---|---|---|---|
| 11B.1 | Category selector | Case Search / Bare Acts / Legal Advice | ☐ |
| 11B.2 | Sample queries | IPC 420, CrPC 41, IT Act 66A, IPC 498A visible | ☐ |
| 11B.3 | Covered sections | IPC 302, 376, 420, 498A, 354 listed | ☐ |
| 11B.4 | Research (backend up) | Returns legal analysis with sections cited | ☐ |

### 11C — Cybersecurity
| # | Check | Expected | Status |
|---|---|---|---|
| 11C.1 | Tabs | Log Analysis / CVE Lookup / AI Security | ☐ |
| 11C.2 | Log pre-filled | SSH brute force logs visible | ☐ |
| 11C.3 | Detection rules | Brute Force, SQL Injection, XSS, Dir Traversal, Scanning, Priv Escalation | ☐ |
| 11C.4 | Analyze Logs (backend up) | Returns threat classification + severity | ☐ |

### 11D — Receptionist
| # | Check | Expected | Status |
|---|---|---|---|
| 11D.1 | Chat simulation | "Start a conversation with the AI receptionist…" | ☐ |
| 11D.2 | Capabilities | Twilio Voice, WhatsApp Business, Appointment Booking, Voicemail, Embeddable Widget | ☐ |
| 11D.3 | Embed code | JavaScript snippet visible | ☐ |
| 11D.4 | Quick prompts | "I want to book a meeting…" chips visible | ☐ |

### 11E — Form Reader
| # | Check | Expected | Status |
|---|---|---|---|
| 11E.1 | Document types | PAN, Aadhaar, GSTIN, Passport, Bank Statement | ☐ |
| 11E.2 | Upload area | Drag-drop zone + click to upload | ☐ |
| 11E.3 | India validation | PAN format XXXXX1234X, Aadhaar Verhoeff check, GSTIN format | ☐ |
| 11E.4 | Extract Data (backend up) | Returns structured JSON fields | ☐ |

### 11F — Email Manager
| # | Check | Expected | Status |
|---|---|---|---|
| 11F.1 | Tabs | Inbox / AI Draft / OAuth Setup | ☐ |
| 11F.2 | Provider | Gmail / Outlook dropdown | ☐ |
| 11F.3 | OAuth prompt | "Connect your Gmail or Outlook to see inbox" | ☐ |
| 11F.4 | AI Draft (backend up) | Subject + tone → generates email body | ☐ |

### 11G — Sales & CRM
| # | Check | Expected | Status |
|---|---|---|---|
| 11G.1 | Tabs | Lead Scoring / Objection Handler | ☐ |
| 11G.2 | BANT form | Name, Email, Company, Job Title, Budget, Company Size pre-filled | ☐ |
| 11G.3 | Score Lead (backend up) | Returns 0–100 BANT score with breakdown | ☐ |

### 11H — Accountant
| # | Check | Expected | Status |
|---|---|---|---|
| 11H.1 | Tabs | GST Calculator / TDS Calculator / Tax Query | ☐ |
| 11H.2 | GST form | Amount ₹100,000, Rate 18%, Intra-State pre-filled | ☐ |
| 11H.3 | Quick picks | ₹50K@5%, ₹200K@12%, ₹100K@18%, ₹75K@28% | ☐ |
| 11H.4 | Calculate GST (backend up) | Returns CGST + SGST breakdown | ☐ |

### 11I — HR Assistant
| # | Check | Expected | Status |
|---|---|---|---|
| 11I.1 | Tabs | Resume Screen / JD Generator / Onboarding | ☐ |
| 11I.2 | Pre-filled | Senior Software Engineer JD + John Smith resume | ☐ |
| 11I.3 | Required skills | Python, FastAPI, React, Leadership | ☐ |
| 11I.4 | Screen Resume (backend up) | Returns 0–100 score + strengths/gaps | ☐ |

### 11J — Social Media
| # | Check | Expected | Status |
|---|---|---|---|
| 11J.1 | Tabs | Content Generator / Hashtag Research / AI Image | ☐ |
| 11J.2 | Platform | LinkedIn / Twitter/X / Instagram dropdown | ☐ |
| 11J.3 | Tone | Professional / Casual / Humorous | ☐ |
| 11J.4 | Generate Content (backend up) | Platform-optimised post with char limit | ☐ |

### 11K — Data Analyst
| # | Check | Expected | Status |
|---|---|---|---|
| 11K.1 | Tabs | Query & Charts / Capabilities | ☐ |
| 11K.2 | Sample queries | Revenue by category, top 10 customers, DAU by cohort, declining products, API latency | ☐ |
| 11K.3 | Run Analysis (backend up) | Generates SQL → runs → returns table + Plotly chart | ☐ |

### 11L — DevOps Engineer
| # | Check | Expected | Status |
|---|---|---|---|
| 11L.1 | Tabs | Debug & Analyse / Capabilities | ☐ |
| 11L.2 | Sample queries | Backend failing CI, open PRs, 5 commits diff, Prometheus metrics, Jira ticket | ☐ |
| 11L.3 | Run Analysis (backend up) | Fetches GitHub/Docker/Prometheus data, returns root cause | ☐ |

---

## ✅ SECTION 12 — BILLING & PLANS

| # | Check | Expected | Status |
|---|---|---|---|
| 12.1 | Current plan | Shows ENTERPRISE (from JWT claim) | ☐ |
| 12.2 | Usage stats | Queries Today, Daily Limit, Resets At | ☐ |
| 12.3 | Plan cards | FREE ₹0 / PRO ₹2,499/mo (MOST POPULAR) / ENTERPRISE Custom | ☐ |
| 12.4 | Plan features | Each plan shows feature checklist | ☐ |

---

## ✅ SECTION 13 — KNOWLEDGE BASE

| # | Check | Expected | Status |
|---|---|---|---|
| 13.1 | Stats bar (backend up) | Total Vectors, Documents, Index Size, Embedding Model, Chunk Size | ☐ |
| 13.2 | Documents tab | "No documents ingested yet" + "Ingest First Document" button | ☐ |
| 13.3 | Ingest New tab | Drag-drop file upload zone | ☐ |
| 13.4 | Supported formats | PDF, TXT, DOCX, MD, CSV shown | ☐ |
| 13.5 | URL ingestion | URL input + Ingest button | ☐ |
| 13.6 | Upload file (backend up) | Shows "✓ N chunks ingested from filename.pdf" | ☐ |
| 13.7 | Document list (backend up) | Lists docs with chunk count + date | ☐ |

---

## ✅ SECTION 14 — WEBHOOK MANAGER

| # | Check | Expected | Status |
|---|---|---|---|
| 14.1 | Integration badges | Slack, Discord, Zapier, Make, n8n, Custom all visible | ☐ |
| 14.2 | Active Webhooks (0) | "No webhooks registered yet." empty state | ☐ |
| 14.3 | Add Webhook form | Name, URL, Secret, Event checkboxes | ☐ |
| 14.4 | Event selector | All 8 events shown: agent.response, hitl.created, hitl.resolved, scheduler.completed, ingest.completed, budget.alert, compliance.violation, user.login | ☐ |
| 14.5 | Register (backend up) | Webhook appears in list with green active dot | ☐ |
| 14.6 | Test button (backend up) | Fires test payload, shows "Test fired to URL" | ☐ |
| 14.7 | Pause / Enable toggle | Changes active status | ☐ |
| 14.8 | Delete | Removes webhook from list | ☐ |
| 14.9 | Event reference | All events with descriptions shown | ☐ |
| 14.10 | Payload format | JSON structure + HMAC signature example shown | ☐ |

---

## ✅ SECTION 15 — SETTINGS

| # | Check | Expected | Status |
|---|---|---|---|
| 15.1 | Profile tab | USER ID, EMAIL, ROLE, PLAN, WORKSPACE, TOKEN EXP all populated from JWT | ☐ |
| 15.2 | Role shows | "admin" (for admin@agentic.local) | ☐ |
| 15.3 | Plan shows | "enterprise" | ☐ |
| 15.4 | Token truncated | First 40 chars of JWT shown in code block | ☐ |
| 15.5 | Sign Out button | Clears sessionStorage, reloads to Landing page | ☐ |
| 15.6 | System Status tab | API Server, OpenAI, Redis Cache, LLM Circuit status dots | ☐ |
| 15.7 | Refresh health | ↻ Refresh re-calls /api/health | ☐ |
| 15.8 | Stack Info | FastAPI+LangGraph, React 18+Vite, OpenAI gpt-4o+Ollama, FAISS+ChromaDB, Neo4j, Redis, LangSmith+MLflow listed | ☐ |
| 15.9 | Cost Analytics tab | Total Cost $, Total Queries, Cache Hits, Hit Rate, Avg Cost/Query | ☐ |
| 15.10 | Model breakdown (backend up) | Per-model cost table shown | ☐ |

---

## ✅ SECTION 16 — BACKEND API ENDPOINTS

Run these with backend live at http://localhost:8000

| # | Endpoint | Method | Expected Response | Status |
|---|---|---|---|---|
| 16.1 | /api/health | GET | `{"status":"ok","openai_healthy":true,"redis_healthy":true}` | ☐ |
| 16.2 | /api/auth/login | POST | `{"access_token":"eyJ...","token_type":"bearer"}` with admin@agentic.local/admin123 | ☐ |
| 16.3 | /api/ingest | POST | `{"chunks_added":N,"source":"filename.pdf"}` | ☐ |
| 16.4 | /api/rag/stats | GET | `{"total_vectors":N,"embedding_model":"all-MiniLM-L6-v2"}` | ☐ |
| 16.5 | /api/rag/documents | GET | `{"documents":[...]}` | ☐ |
| 16.6 | /api/query | POST | Streaming JSON response from agent graph | ☐ |
| 16.7 | /api/cost/report | GET | `{"total_cost_usd":N,"total_queries":N,"cache_hit_rate":N}` | ☐ |
| 16.8 | /api/notifications | GET | `{"notifications":[],"unread_count":0}` | ☐ |
| 16.9 | /api/webhooks | GET | `{"webhooks":[],"valid_events":[...]}` | ☐ |
| 16.10 | /api/webhooks | POST | Creates and returns webhook object | ☐ |
| 16.11 | /api/hitl/queue | GET | `{"queue":[]}` | ☐ |
| 16.12 | /api/scheduler/tasks | GET | `{"tasks":[]}` | ☐ |
| 16.13 | /api/vertical/agri | POST | Returns agri advisory text | ☐ |
| 16.14 | /api/vertical/legal | POST | Returns legal research result | ☐ |
| 16.15 | /api/compliance/check | POST | Returns risk level + violations | ☐ |
| 16.16 | /api/output/generate | POST | Returns download URL for PDF/Excel | ☐ |
| 16.17 | /api/billing/plan | GET | Returns current plan info | ☐ |
| 16.18 | /docs | GET | FastAPI Swagger UI loads | ☐ |
| 16.19 | /metrics | GET | Prometheus metrics output | ☐ |

---

## ✅ SECTION 17 — DEPLOY READINESS

| # | Check | Expected | Status |
|---|---|---|---|
| 17.1 | `npm run build` | ✅ 0 TypeScript errors | ☐ |
| 17.2 | `pytest` (unit) | ✅ 81 tests pass | ☐ |
| 17.3 | `backend/Dockerfile` | Build context `.`, CMD `uvicorn backend.main:app` | ☐ |
| 17.4 | `frontend/Dockerfile` | nginx serving `/dist` | ☐ |
| 17.5 | `docker-compose.yml` | postgres + redis + backend + frontend all healthy | ☐ |
| 17.6 | `render.yaml` | Free tier, Docker runtime, healthCheckPath `/api/health` | ☐ |
| 17.7 | `frontend/vercel.json` | SPA rewrites, immutable asset cache | ☐ |
| 17.8 | `.env.example` | All required vars documented | ☐ |
| 17.9 | `deploy/free_deploy_guide.md` | 7-phase deploy guide present | ☐ |
| 17.10 | GitHub repo pushed | All commits on `main` branch | ☐ |

---

## ✅ SECTION 18 — DEPLOY STEPS (Execute in Order)

```
STEP 1 — Neon PostgreSQL (Free forever)
  → https://neon.tech → New project → Copy DATABASE_URL
  → Run: CREATE EXTENSION IF NOT EXISTS vector;

STEP 2 — Upstash Redis (Free 10K/day)
  → https://upstash.com → Create database → Copy REDIS_URL (rediss://)

STEP 3 — Neo4j Aura (Optional, Free 50K nodes)
  → https://neo4j.com/cloud/platform/aura-graph-database/

STEP 4 — GitHub (if not done)
  → git push origin main

STEP 5 — Render Backend (Free, sleeps after 15min idle)
  → https://render.com → New Web Service → Connect GitHub
  → Runtime: Docker | Root: . | Dockerfile: backend/Dockerfile
  → Set all .env.example variables
  → Copy your Render URL: https://your-app.onrender.com

STEP 6 — Vercel Frontend (Free, always-on)
  → https://vercel.com → Import GitHub repo
  → Root directory: frontend
  → VITE_API_URL = https://your-app.onrender.com/api
  → VITE_WS_URL  = wss://your-app.onrender.com/ws
  → Deploy → Copy URL

STEP 7 — Update CORS
  → backend/.env: ALLOWED_ORIGINS=https://your-app.vercel.app
  → Redeploy backend

STEP 8 — Verify
  → Visit Vercel URL → Landing page loads
  → Sign in → admin@agentic.local / admin123
  → Dashboard appears
  → /api/health returns {"status":"ok"}
```

---

## 🐛 KNOWN ISSUES (not blockers)

| Issue | Impact | Fix |
|---|---|---|
| Backend Render free tier sleeps after 15min idle | First request takes ~30s to wake | Expected — upgrade to paid or use Render cron keepalive |
| Integration tests fail without live backend | CI only | Run `pytest --ignore=backend/tests/test_integration.py` |
| RAG test fails on Windows (numpy DLL) | Local only | Not an issue in Linux Docker container |
| Dashboard "19 Production Features" subtitle | Display only | Will update to 24 in a future commit |
| `Backend: port 8000` footer hardcoded | Display only | Change to dynamic health check status in v2.1 |
| Voice pipeline requires Whisper + Coqui installed | Optional feature | Degrades gracefully if not installed |

---

## 📊 FINAL PROJECT SUMMARY

```
Files:          182 Python + 48 TypeScript/TSX = 230 source files
Code:           ~39,000 lines total
API Endpoints:  133 routes (72 POST, 50 GET, 7 DELETE, 4 PATCH)
Features:       24 enterprise features
Verticals:      12 domain-specific AI agents
Tests:          81 unit tests passing
Build:          0 TypeScript errors
Deploy:         $0/month (Vercel + Render + Neon + Upstash free tiers)
```

---

*Generated by AI Agentic Assistant V2 pre-deploy audit — 2026-05-29*
