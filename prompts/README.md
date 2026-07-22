# Prompt Registry — AI Agentic Assistant

Central registry for all AI agent system prompts.

## Structure

```
prompts/
├── cs/          # Customer Support agent prompts
├── ca/          # CA Accounting agent prompts
└── sm/          # Social Media agent prompts
```

## Versioning Convention

Each prompt file is named: `{action}.v{N}.txt`
- `v1` = initial
- `v2` = improved after QA / user feedback
- Always keep old versions — never delete, just add new

## Prompt Format

```
ROLE: [Who the AI is]
CONTEXT: [Business context, Indian-specific rules]
TASK: [What to do with the payload]
OUTPUT: [Exact JSON structure expected]
RULES:
  - [Specific constraints]
  - [Language handling]
  - [Error cases]
```

## Current Status

Prompts are currently embedded in `backend/verticals/*/  _impl.py`.
Migration to this folder is planned for Q3 2026 (see ROADMAP.md).

## Why a Prompt Registry?

1. **Version tracking** — see exactly what changed between prompt versions
2. **A/B testing** — compare v1 vs v2 with real traffic
3. **Non-engineer edits** — domain experts can improve prompts without touching Python
4. **Eval framework** — run automated quality tests against each version
