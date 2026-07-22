# Portfolio Showcase — AI Agentic Assistant

> *For hiring managers, technical interviewers, and collaborators.*
> This page explains what I built, why it's hard, and what it demonstrates.

---

## What Is This Project?

A **production-grade, multi-tenant AI SaaS platform** that puts 24+ business AI assistants behind one login — built specifically for Indian SMBs.

Think of it as the "Zoho + ChatGPT" for Indian small businesses — but open-source, AI-native, and built by one engineer.

**Live:** [ai-agentic-assistant.vercel.app](https://ai-agentic-assistant.vercel.app)
**Demo:** `demo@agentic.local` / `demo123`
**GitHub:** [chandrukumar-AIML/ai-agentic-assistant](https://github.com/chandrukumar-AIML/ai-agentic-assistant)

---

## What I Built (By Role)

### As an AI Agent Engineer
- Built a **dispatcher-based multi-agent system** — each vertical (CS, CA, Social) has its own agent with 37–40 individual AI actions
- Implemented **LLM routing**: Ollama (local) → Groq → Gemini → OpenAI fallback chain
- All agents share a common `_llm()` bridge with environment-aware LLM selection
- **115+ AI features** across 3 verticals, all individually QA'd with Python integration tests

### As a Backend Engineer
- FastAPI with **JWT auth**, RBAC, rate limiting (SlowAPI), CORS
- 190+ REST endpoints across 18 router modules
- Pydantic V2 validation on all request bodies
- Global exception handler, rate limit handler, health check endpoint
- Vertical routing via `POST /api/verticals/{name}/action` — single unified entry point

### As a Prompt Engineer
- Wrote structured system prompts for 3 AI agents with **India-specific context** (GST, Tamil/Hindi, Indian legal references)
- Each action has a dedicated prompt with: role definition, output format, reasoning instructions, language handling
- Prompts designed for structured JSON output — every action returns typed, predictable keys

### As a QA Automation Engineer
- Built Python QA scripts for all 3 agents (115 features tested)
- Persona-driven test data (ShopEasy / Rajesh Kumar, Sharma & Co / Priya Sharma)
- Assertion framework with PASS / PARTIAL / FAIL classification and key-level diff output
- Fixed 8+ backend bugs discovered through QA (NameError, IndexError, TypeError, wrong response keys)
- **Final result: 37/37 CS, 40/40 CA, all SM features — 100% pass rate**

### As a DevOps Engineer
- Docker multi-stage build (`builder` + `runtime` layers)
- `docker-compose.yml` for local full-stack dev
- `docker-compose.prod.yml` for production
- Render backend deploy + Vercel frontend deploy ($0/month)

### As a Frontend Engineer
- React 18 + TypeScript + Vite
- 6 pages: Landing, Login, Dashboard, CS, CA, Social
- Auth flow with JWT token management
- Sidebar navigation, theme toggle, error boundary
- API client with typed responses

### As a Security Engineer
- JWT authentication (HS256, environment-aware bypass for dev)
- CORS configured with explicit allow-list
- Rate limiting on all endpoints
- Pydantic input validation (no unvalidated user input reaches business logic)

---

## What Makes This Hard (Technical Depth)

### 1. Multi-Agent Dispatcher Pattern
Each vertical has `cs_agent(action, payload, language)` → dispatches to 37+ specialized functions. Building 40 functions that all return consistent typed JSON — and debugging when they don't — requires systematic QA, not just "it runs."

### 2. LLM Reliability in India
Ollama (local) is free but slow. OpenAI costs money. Groq is fast but rate-limited. Building a fallback chain that's environment-aware (`APP_ENV`, `DEMO_MODE`, available API keys) without crashing on missing keys was a non-trivial engineering challenge.

### 3. India-Specific AI
GST has 3 components (CGST + SGST for intra-state, IGST for inter-state). TDS has 30+ sections. Indian court references require IndianKanoon. Tamil/Hindi code-switching in customer support messages. These aren't solved by generic LLMs — they require Indian domain knowledge baked into every prompt.

### 4. 115-Feature QA at Scale
Writing and running 115 integration tests (CS + CA + SM) revealed 8 bugs that unit tests would never catch — including a silent Python function name collision, a `.split()[0]` crash on empty strings, and wrong response key assumptions. This is real QA engineering.

---

## Resume Bullet Points

**Pick the ones that match the JD:**

```
• Built a production multi-tenant AI SaaS with 115+ AI features across 3 verticals
  (Customer Support, CA Accounting, Social Media) using FastAPI + React 18 + Ollama

• Designed and implemented a dispatcher-based multi-agent architecture
  routing 37–40 AI actions per vertical with structured JSON output validation

• Wrote India-specific AI prompts for GST, TDS, Tamil/Hindi customer support,
  and Indian legal references — increasing response accuracy vs generic LLMs

• Achieved 100% QA pass rate (37/37 CS, 40/40 CA) through persona-driven
  Python integration test suite that caught 8 production bugs pre-launch

• Built multi-tenant JWT auth + RBAC + per-client tool entitlements for
  Free/Pro/Enterprise plan gating on $0/month infrastructure (Render + Vercel)

• Implemented LLM fallback chain: Ollama → Groq → Gemini → OpenAI with
  environment-aware routing and demo mode for zero-cost public deployment
```

---

## Skills Demonstrated

| Skill | Evidence |
|-------|----------|
| AI Agent Engineering | 3 verticals, 115 features, dispatcher pattern |
| Prompt Engineering | India-specific prompts, structured JSON output |
| Backend Engineering | FastAPI, JWT, RBAC, rate limiting, 190+ endpoints |
| QA Automation | Python QA scripts, 100% pass rate, bug discovery |
| Frontend Engineering | React 18, TypeScript, Vite, auth flow |
| DevOps | Docker multi-stage, Render + Vercel deploy |
| System Design | Multi-tenant, LLM routing, modular verticals |
| India Domain | GST, TDS, Tamil/Hindi, UPI, Indian compliance |

---

## What's Next

See [ROADMAP.md](ROADMAP.md) for planned features.

Currently adding: CI/CD pipeline, LLMOps (prompt versioning, eval), analytics, and 4 new verticals (Healthcare, HR, Sales, Legal).

---

*Built by Chandru Kumar — Enterprise AI Platform Engineer*
*Open to: AI Engineer, Backend Engineer, Full-Stack Engineer, Platform Engineer roles*
*Email: terazionservices@gmail.com*
