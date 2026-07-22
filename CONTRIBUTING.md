# Contributing to AI Agentic Assistant

Thank you for your interest! This guide covers how to contribute.

## Quick Start

```bash
git clone https://github.com/chandrukumar-AIML/ai-agentic-assistant.git
cd ai-agentic-assistant
cp .env.example .env
# Edit .env — minimum: JWT_SECRET=any-32-char-string

# Backend
cd backend
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

## How to Contribute

### 1. Bug Reports
Open an issue with:
- What you expected vs what happened
- Steps to reproduce
- OS, Python version, Node version

### 2. Feature Requests
Open an issue with label `feature-request`. See [PERSONAS.md](PERSONAS.md) for target users and [ROADMAP.md](ROADMAP.md) for planned features.

### 3. Code Contributions

```bash
# Create a branch
git checkout -b feat/your-feature-name

# Make changes, then test
python <scratchpad>/qa_cs_full.py   # CS QA
python <scratchpad>/qa_ca_full.py   # CA QA

# Commit with conventional commit format
git commit -m "feat(cs): add sentiment analysis for Tamil text"

# Push and open PR
git push origin feat/your-feature-name
```

## Commit Message Format

```
type(scope): short description

Types: feat | fix | refactor | docs | test | chore
Scope: cs | ca | sm | backend | frontend | auth | config | docs
```

Examples:
```
feat(ca): add advance tax calculator for FY 2025-26
fix(cs): resolve NameError in churn_risk language parameter
docs: add PERSONAS.md with 5 Indian SMB user profiles
test(ca): add QA coverage for MSME loan eligibility
```

## Adding a New Vertical

To add a new AI agent vertical:

1. Create `backend/verticals/<name>/` with:
   - `__init__.py`
   - `agent.py` — HTTP handler
   - `_impl.py` — dispatcher + action implementations
   - `schemas.py` — Pydantic request/response models
   - `constants.py` — agent metadata
   - `tools/` — split implementations by category

2. Register in `backend/api/vertical_routes.py`

3. Write QA script covering all actions

4. Add frontend page in `frontend/src/pages/`

## Code Standards

- **Python:** Follow existing patterns in `_impl.py` — each action is a private function `_action_name(payload, language)`
- **TypeScript:** Strict mode, no `any` types
- **Tests:** Every new action needs a QA test case
- **Prompts:** India-specific context in system prompts (GST, Tamil/Hindi, INR)

## Pull Request Checklist

- [ ] New action has a QA test that passes
- [ ] No hardcoded secrets or API keys
- [ ] `.env.example` updated if new env var added
- [ ] `CHANGELOG.md` updated with what changed
- [ ] `README.md` updated if new feature added to the feature list

## Questions?

Open a GitHub Discussion or email terazionservices@gmail.com
