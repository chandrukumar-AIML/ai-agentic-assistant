# 🚀 Demo & Smoke Test

`demo.py` exercises the **entire platform end-to-end** with predefined demo data so
anyone can verify every layer works with a single command. LLM calls run through the
local **Ollama** model — **zero OpenAI cost**.

## Prerequisites
- Backend running: `python -m uvicorn backend.main:app --port 8000`
- Ollama running locally with `llama3.2` (only needed for LLM checks)

## Run

```bash
python demo.py --quick    # ~10s  — auth + platform + deterministic engines (no LLM)
python demo.py            # ~3min — everything above + 3 real Ollama calls (default "smoke")
python demo.py --full     # ~30min — every LLM vertical live via Ollama
python demo.py --base https://your-backend.onrender.com/api   # against a deployed instance
```

Exit code is `0` when all executed checks pass, `1` otherwise (CI-friendly).

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
