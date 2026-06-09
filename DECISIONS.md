# Architecture Decision Records

The 5 most important technology choices in AI Agentic, and *why*.

---

## 1. Ollama-first LLM routing with OpenAI fallback (not OpenAI-only)

**Decision:** A single `LLMRouter.complete()` chokepoint calls a local **Ollama** model (`llama3.2`) first, with a circuit-breaker fallback to **OpenAI** only when Ollama is unavailable.

**Why:** Cost and control. Most agent calls run free on local inference during development; OpenAI is used only as a reliability fallback or when explicitly forced (vision, high-quality synthesis). The single chokepoint also made **Demo Mode** trivial — one short-circuit returns instant canned output with zero LLM cost, which is what powers the public demo link on free-tier hosting.

**Trade-off:** `llama3.2` (3B) is weaker than GPT-4o for complex reasoning; high-stakes output leans on the OpenAI fallback.

---

## 2. File-backed user/entitlement store (not Postgres) for auth

**Decision:** Multi-tenant users and per-client tool entitlements live in a JSON file store (`backend/auth/user_store.py`), not a database.

**Why:** The platform must boot and run on infra with **no database** (Render free tier, or a quick local clone). This makes the multi-tenant access-control layer work with zero external dependencies, and keeps the demo deployable for ₹0. The whole app boots with only `JWT_SECRET` set.

**Trade-off:** The file store resets on ephemeral redeploys and isn't concurrency-safe at scale. Production at volume would migrate this to Postgres (the richer DB-backed `admin_routes.py` path already exists for that).

---

## 3. LangGraph for agent orchestration (not a hand-rolled loop)

**Decision:** Agent reasoning is a **LangGraph** state graph: Supervisor → Planner → Workers → Aggregator → Reflection → (rewrite on fail) → Streamer.

**Why:** LangGraph gives explicit, inspectable state transitions, conditional edges (e.g. retry on a failed reflection check), and interrupt-based **Human-in-the-Loop** for free. A hand-rolled async loop would re-implement all of this with worse observability.

**Trade-off:** Heavier dependency and a learning curve; graph compile is deferred to first request to keep startup RAM under the 512 MB free-tier limit.

---

## 4. Dual vector store: FAISS + ChromaDB

**Decision:** RAG uses **FAISS** as the primary index with **ChromaDB** available, plus HyDE query expansion and cross-encoder reranking.

**Why:** FAISS is fast and runs in-process with no service to deploy (works on free tier); ChromaDB adds metadata-filtered retrieval when a richer store is available. Falling back to FAISS-only keeps RAG working when ChromaDB isn't deployed.

**Trade-off:** Two code paths to maintain; in the free-tier deployment only FAISS is active.

---

## 5. Per-vertical agent modules behind one generic action endpoint

**Decision:** Each of the 24+ tools is its own module (`backend/verticals/<name>/<name>_agent.py`) exposing a single `async def <name>_agent(action, payload, language)` dispatcher, surfaced through generic `POST /verticals/<name>/action` routes.

**Why:** Adding a vertical is a contained, repeatable pattern (agent + route + page + sidebar entry) with no churn to shared code — this is how 12 new verticals were added quickly and safely. The uniform request/response shape also let the frontend share one `ResultBox` renderer and the demo runner test all of them generically.

**Trade-off:** The generic action shape is less self-documenting than bespoke typed endpoints per action; deterministic engines (GST/TDS/scoring) deliberately bypass the LLM for correctness.
