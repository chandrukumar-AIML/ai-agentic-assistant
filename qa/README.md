# QA Scripts — AI Agentic Assistant

Integration test suite for all AI agent verticals.

## Run QA

```bash
# Start backend first
uvicorn backend.main:app --reload --port 8000

# Run CS Agent QA (37 actions)
python qa/qa_cs_full.py

# Run CA Agent QA (40 actions)
python qa/qa_ca_full.py
```

## Results

| Script | Actions | Status |
|--------|---------|--------|
| `qa_cs_full.py` | 37/38 (send_whatsapp skipped — needs Twilio) | ✅ 37/37 PASS |
| `qa_ca_full.py` | 40/40 | ✅ 40/40 PASS |
| `eval_llm.py` | 23 quality evals across CS + CA + SM | Quality scoring |

## LLM Eval (Quality Scoring)

```bash
# Run quality scoring — grades each action A/B/C/D/F
python qa/eval_llm.py              # all verticals
python qa/eval_llm.py --vertical cs   # CS only
python qa/eval_llm.py --vertical ca   # CA only
```

Scores on: completeness (50%), response length (30%), JSON validity (20%).

## Persona

All QA tests use realistic Indian SMB personas:
- **CS:** ShopEasy (ecommerce) / Rajesh Kumar (customer)
- **CA:** Sharma & Co (CA firm) / Priya Sharma (CA partner) / ZenFit (client)

## PASS / PARTIAL / FAIL Logic

- **PASS** — response has expected keys with non-empty values
- **PARTIAL** — response returned but expected keys missing (wrong key name)
- **FAIL** — HTTP error, LLM error, or Python exception
