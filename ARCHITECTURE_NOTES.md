# Architecture Notes

*The page to walk an interviewer through. Accurate to the code as built.*

---

## 1. System overview

AI Agentic is a **multi-tenant AI SaaS** that puts 24+ business and engineering AI assistants (finance/GST, legal, HR, sales, support, marketing, healthcare, agriculture, education, plus a software-dev team) behind a single login. An admin grants each client exactly which tools they can use, on Free/Pro/Enterprise plans billed via Stripe or Razorpay (UPI). A FastAPI backend orchestrates agents on a LangGraph state graph with an Ollama-first (OpenAI-fallback) LLM router, RAG over FAISS/ChromaDB, and enterprise guardrails (PII detection, HITL approvals, audit logging). A React + TypeScript SPA is the dashboard. A `DEMO_MODE` flag serves instant canned output so the whole product is demoable at zero LLM cost.

## 2. Why each major technology was chosen

- **FastAPI** — async-native, Pydantic request validation for free, first-class WebSocket + OpenAPI docs.
- **LangGraph** — explicit, inspectable agent state machine with conditional edges and interrupt-based Human-in-the-Loop (vs an opaque hand-rolled loop).
- **Ollama (primary) + OpenAI (fallback)** — local inference controls cost; circuit-breaker fallback preserves reliability. Single chokepoint enabled Demo Mode.
- **FAISS + ChromaDB** — in-process FAISS needs no deployed service (free-tier friendly); ChromaDB adds metadata-filtered retrieval when available.
- **Redis** — sessions + semantic cache; fast, and degrades gracefully if absent.
- **PostgreSQL (optional) + file-store auth** — app boots with no DB; file-store gives multi-tenant entitlements with zero dependencies, Postgres is the scale path.
- **React + TypeScript + Vite** — typed SPA, fast builds, one shared component system (`ui.tsx`) across 34 pages.
- **slowapi** — per-route rate limiting (login/signup/ingest/query) without extra infra.
- **Presidio-style PII detection + HITL** — compliance guardrails for regulated verticals (health/legal/finance).

## 3. Data flow — one request, HTTP → response

1. Browser (Vercel SPA) sends `POST /api/verticals/<tool>/action` with a **JWT** `Authorization: Bearer`.
2. **CORS middleware** checks the origin against `CORS_ORIGINS`; **slowapi** applies rate limits; **`verify_token`** decodes the JWT (workspace + role + plan claims).
3. The route validates the body with a **Pydantic** model and dispatches to the vertical's `*_agent(action, payload, language)`.
4. The agent calls **`llm_router.complete()`** → Ollama first; if `DEMO_MODE` is on it short-circuits to a canned response; deterministic engines (GST/TDS/scoring/validation) skip the LLM entirely and compute directly.
5. For RAG-backed calls, the query hits FAISS/ChromaDB (HyDE expansion + reranking) before the LLM; sensitive actions (send email, offer letter) route to the **HITL** approval queue instead of executing.
6. Cost/usage is tracked; the structured result returns as JSON and the SPA's `ResultBox` renders it as markdown, a table, or a key/value list.

## 4. Scale bottleneck — what breaks first at 10× load

**The file-backed user store and single-instance in-process state break first.** It isn't concurrency-safe across multiple workers/instances, and the Render free instance sleeps and has 512 MB RAM.

**Fix path:**
1. Move auth/entitlements + sessions to **Postgres + Redis** (the DB-backed admin path already exists).
2. Run **multiple stateless workers** behind Render/Vercel autoscaling (the app is already mostly stateless; the LangGraph agent is compiled per-process and cached).
3. Offload heavy/long LLM and ingestion work to a **queue/worker** (Celery/RQ) instead of request threads.
4. Add a managed vector store (Chroma server / pgvector) so RAG scales beyond in-process FAISS.

## 5. Known trade-offs (sacrificed for speed of development)

- **Breadth over depth** — 24+ verticals exist, but most are a single guided LLM call; ~5 flagships (Accountant, HR, Sales, AgriTech, Social) have real deterministic/integration depth.
- **File store over DB** — fast to ship and dependency-free, but not durable/concurrent at scale.
- **Tool gating is enforced in the UI**, not yet on every backend route (a hardening item).
- **Integrations are wired but mostly untested with live keys** — they degrade gracefully and activate when keys are added.
- **Single small local model** — quality-critical output depends on the OpenAI fallback.

## 6. What would be different in v2

1. **Postgres + Redis as the source of truth** for users, entitlements, sessions and usage — with backend-enforced per-route tool authorization.
2. **Go deep on 3 flagships** with real integrations (GST filing API, live CRM sync, real mandi feeds) and per-client persisted data/history — turning demos into systems-of-record.
3. **Queue-based async** for ingestion and long LLM jobs, plus streaming everywhere, with proper observability (request IDs end-to-end, dashboards, alerting) and a real automated test suite gating CI.
