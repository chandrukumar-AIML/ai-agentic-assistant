# /review — Code Review

Act as the **Code Reviewer** from AGENTS.md. Do a thorough pre-merge review.

## Steps

1. `git diff HEAD` — see all changed files
2. `git log --oneline -3` — understand recent context

## Review Checklist

### Backend changes
- [ ] Dispatcher pattern followed — no new standalone routes?
- [ ] New action added to `handlers` dict in `dispatch()`?
- [ ] Action handler in `prompts.py` (not inlined)?
- [ ] DEMO_MODE canned response added?
- [ ] Language (`tamil`/`hindi`) handled in every action?
- [ ] Pydantic model validates all inputs?
- [ ] JWT auth on every new endpoint?
- [ ] `ruff check backend/` passes?

### Frontend changes
- [ ] No hardcoded hex colors — only `var(--*)` tokens?
- [ ] All UI from `ui.tsx` — no custom styled divs?
- [ ] Workspace pre-fill added for new form fields?
- [ ] New feature added to correct Tabs group?
- [ ] `npx tsc --noEmit` passes?
- [ ] No console errors in browser?

### Any change
- [ ] Does it break existing QA? (`python qa/qa_cs_full.py` + `qa_ca_full.py`)
- [ ] Is `CHANGELOG.md` updated?
- [ ] No API keys or secrets hardcoded?
- [ ] Commit message follows `type(scope): description` format?

## Output Format

Report findings as:
- 🔴 **BLOCKER** — must fix before merge
- 🟡 **WARNING** — should fix, won't block
- 🟢 **GOOD** — note what's done well

End with: **APPROVE** or **REQUEST CHANGES**
