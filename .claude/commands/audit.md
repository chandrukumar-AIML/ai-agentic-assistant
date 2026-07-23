# /audit — 17-Level Engineering Audit

Act as the **Engineering Manager + Product Lead** from AGENTS.md.
Run the full ENGINEERING_PLAYBOOK.md audit against the current codebase.

## Steps

1. Read `ENGINEERING_PLAYBOOK.md` — all 17 levels
2. For each level, check the current codebase:
   - Read relevant files
   - Run relevant commands
   - Score honestly (0-10 per level)

## Levels to Audit

| # | Level | Key files to check |
|---|---|---|
| L1 | Product-Market Fit | PITCH.md, PERSONAS.md, README.md |
| L2 | Architecture | ARCHITECTURE.md, backend/main.py |
| L3 | Code Quality | ruff check, tsc --noEmit |
| L4 | Testing | qa/qa_cs_full.py, qa/qa_ca_full.py |
| L5 | Security | SECURITY.md, auth.py, JWT |
| L6 | Performance | LLM fallback chain, response times |
| L7 | Documentation | README.md, CONTRIBUTING.md, CLAUDE.md |
| L8 | DevEx | CONTRIBUTING.md, dev setup steps |
| L9 | Observability | backend/main.py logging, PostHog |
| L10 | Deployment | .github/workflows/ci.yml, railway.toml |
| L11 | Data Management | models.py, multi-tenant JWT claims |
| L12 | API Design | dispatcher pattern, versioning |
| L13 | Frontend Quality | ui.tsx CSS vars, TypeScript strict |
| L14 | Analytics | PostHog in main.tsx |
| L15 | Business Metrics | ROADMAP.md, PITCH.md TAM/SAM |
| L16 | Team Processes | CONTRIBUTING.md, CHANGELOG.md |
| L17 | Interview Readiness | PORTFOLIO.md, ARCHITECTURE.md ADRs |

## Output Format

```
## Audit Results — {date}

| Level | Name | Score | Key Finding |
|---|---|---|---|
| L1 | Product-Market Fit | 8/10 | Strong India-first positioning |
| L2 | Architecture | 9/10 | Dispatcher pattern excellent |
...

**Total: XX/170 (XX%)**
**Grade: A/B/C/D/F**

## Top 5 Gaps to Fix
1. L{n} — {finding} — {fix}
...

## Comparison vs Last Audit
Previous: XX/170 | Current: XX/170 | Delta: +X
```
