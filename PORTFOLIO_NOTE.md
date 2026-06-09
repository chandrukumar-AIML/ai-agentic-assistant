# Portfolio Note

## How this was built

AI Agentic was built **iteratively with Claude Code** as a pair-programming partner — the architecture, trade-offs, and every fix were reviewed and directed by me. The git history (`git log --oneline`, 36+ commits) reflects this: small, focused, conventional commits (`feat:`, `fix:`, `style:`, `docs:`, `test:`) rather than one giant dump.

## Logical phases

1. **Core platform (Phases A–O)** — LangGraph multi-agent graph, Ollama-first LLM router with OpenAI fallback, dual-store RAG, guardrails (PII/HITL), JWT auth, observability, and the first 12 domain verticals.
2. **Vertical expansion (Phase P)** — added Healthcare, Real Estate, EdTech and a full software-dev team (QA, PM, Code, ML, DBA, Tech Lead, Data Analyst) using a repeatable agent+route+page pattern.
3. **Multi-tenant SaaS (Phase Q)** — file-backed user store, per-client tool entitlements, Admin Panel, self-serve signup, sidebar gating.
4. **Billing + integrations (Phase R)** — Stripe + Razorpay (UPI) checkout wiring and a live integration-status page.
5. **Demo Mode + test runner (Phase S)** — zero-cost canned-output mode for a public demo link, plus `demo.py` (a 43-check end-to-end runner) and `DEMO.md`.
6. **Client-facing polish (Phase T)** — emerald/teal rebrand off the generic "AI purple", removal of developer tells across all 34 pages, markdown/table result rendering, and mobile responsiveness.
7. **Production audit** — a 15-level senior-engineer pass: rate-limiting on auth, startup timeout-guards so the service always binds its port on Render, and the `DECISIONS.md` / `ARCHITECTURE_NOTES.md` documentation set.

## Deployment

- **Backend:** Render (Docker, branch `master`) — `https://ai-agentic-backend-ywdx.onrender.com`
- **Frontend:** Vercel — `https://ai-agentic-assistant.vercel.app`
- **Cost:** ₹0/month on free tiers; `DEMO_MODE=true` = zero LLM cost.

## Demo credentials

`admin@agentic.local` / `admin123` (admin) · `demo@agentic.local` / `demo123` (restricted client)

> **TODO (manual):** record a 2-minute Loom walkthrough and embed the GIF/link at the top of `README.md`; set the GitHub repo description + topics.
