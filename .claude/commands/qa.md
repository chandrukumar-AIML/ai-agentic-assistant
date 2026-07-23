# /qa — Full QA Suite

Act as the **QA Lead** from AGENTS.md. Run the complete test suite.

## Steps

```bash
# 1. Backend QA — all actions
python qa/qa_cs_full.py      # expect 37/37
python qa/qa_ca_full.py      # expect 40/40

# 2. LLM quality eval
python qa/eval_llm.py --vertical all   # aim A/B grades

# 3. TypeScript
cd frontend && npx tsc --noEmit        # expect 0 errors

# 4. Lint
ruff check backend/                    # expect 0 errors
```

## Browser QA (manual)

1. Open http://localhost:5173
2. Login with `admin@agentic.local` / `admin123`
3. For each changed agent page:
   - Clear localStorage (`localStorage.clear()` in console)
   - Verify workspace setup wizard appears
   - Complete wizard, verify WorkspaceBar shows
   - Test the changed feature end-to-end
   - Check no console errors

## Demo Mode QA

```bash
DEMO_MODE=true uvicorn backend.main:app --reload
```
Every feature must return instant canned output — no LLM calls, no errors.

## Report Format

```
CS QA:  37/37 ✅
CA QA:  40/40 ✅
LLM eval: CS=A, CA=B, SM=A ✅
TypeScript: 0 errors ✅
Ruff: 0 errors ✅
Browser: [list any issues found]
Demo Mode: [pass/fail + any issues]

OVERALL: PASS / FAIL
```
