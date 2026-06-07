# 🚀 Demo & Smoke Test

`demo.py` exercises the **entire platform end-to-end** with predefined demo data so
anyone can verify every layer works with a single command. LLM calls run through the
local **Ollama** model — **zero OpenAI cost**.

## Prerequisites
- Backend running: `python -m uvicorn backend.main:app --port 8000`
- Ollama running locally with `llama3.2` (only needed for LLM checks)

## Run

```bash
python demo.py --mock     # ~15s  — INSTANT showcase: ALL 43 agents/features with output
                          #          (deterministic run real; LLM/external show canned output)
python demo.py --quick    # ~10s  — real backend, deterministic + platform only (no LLM)
python demo.py            # ~4min — everything + 3 real Ollama calls (default "smoke")
python demo.py --full     # ~40min — every LLM vertical live via Ollama
python demo.py --show     # add output previews to any live run
python demo.py --base https://your-backend.onrender.com/api   # against a deployed instance
```

Exit code is `0` when all executed checks pass, `1` otherwise (CI-friendly).

**43 checks** cover every agent and feature: infra, auth/tenancy, F1 Guardian,
F4 Scheduler, F6 HITL, F7 Output-gen, F8 Billing, F12 A/B, RAG, all deterministic
engines (GST/TDS/HSN/BANT/validation/HR-match), every LLM vertical (Agri, Legal,
Receptionist, Accountant, HR, Social, Healthcare, Real Estate, EdTech, Sales),
every dev role (Analyst, DevOps, QA, PM, Code, ML, DBA, Tech Lead, Cybersec), and
external integrations (Email, Social auto-post).

> `--mock` is the best way to **see what every feature outputs in 15 seconds** —
> ideal for a screen-recorded walkthrough or a quick sanity pass before going deep.

## What it verifies

| Layer | Checks |
|-------|--------|
| **Infra** | `/health` — LLM router, Redis, circuit breaker |
| **Auth & tenancy** | login → JWT, `/auth/me`, tool catalog, client list |
| **Platform** | integration status, billing plans, subscription |
| **Deterministic engines** | GST calc (asserts ₹1000@18% = ₹1180), TDS, HSN lookup, BANT lead score, PAN/GSTIN validation, HR skill-match |
| **LLM business verticals** | AgriTech, Healthcare, Real Estate, EdTech, Sales, Social, Legal |
| **LLM dev roles** | QA, DevOps IaC, Tech Lead, Cybersec OWASP |

## Notes
- **`--quick` is always green in seconds** — ideal for a live walkthrough or CI smoke gate.
- LLM checks that exceed their timeout are marked `SKIP` (Ollama is slow on CPU), never `FAIL`.
- Demo login: `admin@agentic.local` / `admin123` (seeded automatically).
