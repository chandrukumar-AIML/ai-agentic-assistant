# /ship — Prepare & Deploy

Act as **DevOps / Release Engineer** from AGENTS.md.

## Pre-ship checklist

```bash
# 1. QA
python qa/qa_cs_full.py   # 37/37
python qa/qa_ca_full.py   # 40/40
cd frontend && npx tsc --noEmit && cd ..
ruff check backend/

# 2. Git status
git status
git diff --stat HEAD

# 3. Build check
cd frontend && npm run build && cd ..
```

## Commit & PR

```bash
git add -p                          # stage hunks, not whole files
git commit -m "type(scope): what + why"
git push origin master
```

Commit types: `feat` · `fix` · `docs` · `refactor` · `test` · `chore`

## Deploy

```bash
# Backend → Railway
railway up
# or push to master (auto-deploy configured)

# Frontend → Vercel
vercel --prod
```

## Post-deploy smoke test

```bash
# Backend health
curl https://ai-agentic-backend-ywdx.onrender.com/health

# Test one live action
curl -X POST https://ai-agentic-backend-ywdx.onrender.com/api/cs/action \
  -H "Content-Type: application/json" \
  -d '{"action":"faq","payload":{"business_name":"Test","business_type":"Retail","faq_context":"Q: Hours? A: 9-6pm","query":"What are your hours?"},"language":"en"}'
```

## Post-deploy docs

- Update `CHANGELOG.md` — what shipped, for whom
- Update version in `package.json` if significant
- Tag: `git tag v{major}.{minor}.{patch} && git push --tags`
