# 🚀 Free Deployment Guide — AI Agentic Assistant V2

## Architecture (100% Free)

| Component  | Platform          | Free Limits              |
|------------|-------------------|--------------------------|
| Frontend   | Vercel            | 100GB/mo, always-on      |
| Backend    | Render            | 750hrs/mo, 512MB RAM     |
| PostgreSQL | Neon              | 0.5GB, pgvector, forever |
| Redis      | Upstash           | 10K cmd/day              |
| Neo4j      | Neo4j Aura Free   | 200K nodes (optional)    |

---

## Step 1 — GitHub Repo (Render/Vercel read from GitHub)

```bash
# Install GitHub CLI if needed
winget install GitHub.cli

# Authenticate
gh auth login

# Create repo and push
gh repo create ai-agentic-assistant --public --source=. --remote=origin --push
```

---

## Step 2 — Neon PostgreSQL (Free, pgvector)

1. Go to → https://neon.tech  → Sign up (GitHub login)
2. New Project → Name: `ai-agentic` → Region: US East
3. Dashboard → Connection string → copy the **pooled** connection string
   ```
   postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
4. Enable pgvector:
   ```sql
   -- Run in Neon SQL Editor
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
5. Save these values (needed later):
   - `DATABASE_URL` — the full connection string above
   - `POSTGRES_HOST` — the hostname (ep-xxx.us-east-2.aws.neon.tech)
   - `POSTGRES_DB`   — neondb
   - `POSTGRES_USER` — your Neon username
   - `POSTGRES_PASSWORD` — your Neon password

---

## Step 3 — Upstash Redis (Free)

1. Go to → https://upstash.com → Sign up (GitHub login)
2. Create Database → Name: `ai-agentic-redis` → Region: US-East-1 → **Free** plan
3. Copy the **Redis URL** (starts with `rediss://...`)
4. Save: `REDIS_URL` = rediss://...

---

## Step 4 — Neo4j Aura Free (Optional)

1. Go to → https://neo4j.com/cloud/platform/aura-graph-database
2. Create Free instance → Download credentials file
3. Save:
   - `NEO4J_URI`      = neo4j+s://xxxxxxxx.databases.neo4j.io
   - `NEO4J_USER`     = neo4j
   - `NEO4J_PASSWORD` = (from downloaded file)

---

## Step 5 — Deploy Backend on Render

1. Go to → https://render.com → Sign up (GitHub login)
2. **New** → **Web Service**
3. Connect GitHub → select `ai-agentic-assistant` repo
4. Settings:
   ```
   Name:             ai-agentic-backend
   Region:           Oregon (US West)
   Branch:           master
   Runtime:          Docker
   Dockerfile Path:  backend/Dockerfile
   Docker Context:   .
   Plan:             Free
   ```
5. **Environment Variables** → Add ALL of these:

   | Key | Value |
   |-----|-------|
   | `OPENAI_API_KEY` | sk-proj-... |
   | `LANGCHAIN_API_KEY` | lsv2_pt_... |
   | `TAVILY_API_KEY` | tvly-... |
   | `JWT_SECRET` | (run: `openssl rand -hex 32`) |
   | `DATABASE_URL` | postgresql://...neon.tech/neondb?sslmode=require |
   | `POSTGRES_HOST` | ep-xxx.us-east-2.aws.neon.tech |
   | `POSTGRES_PORT` | 5432 |
   | `POSTGRES_DB` | neondb |
   | `POSTGRES_USER` | (from Neon) |
   | `POSTGRES_PASSWORD` | (from Neon) |
   | `REDIS_URL` | rediss://...upstash.io:6379 |
   | `NEO4J_URI` | neo4j+s://...neo4j.io (or bolt://localhost:7687 to skip) |
   | `NEO4J_USER` | neo4j |
   | `NEO4J_PASSWORD` | (from Aura, or any string if skipping) |
   | `APP_ENV` | production |
   | `CORS_ORIGINS` | ["https://your-app.vercel.app"] |
   | `MLFLOW_TRACKING_URI` | /app/data/mlflow_runs |
   | `LANGCHAIN_TRACING_V2` | true |
   | `LANGCHAIN_PROJECT` | ai-agentic-assistant |

6. Click **Create Web Service** → wait ~10 minutes for first build
7. Copy your backend URL: `https://ai-agentic-backend.onrender.com`

---

## Step 6 — Deploy Frontend on Vercel

1. Go to → https://vercel.com → Sign up (GitHub login)
2. **Add New Project** → Import `ai-agentic-assistant` repo
3. Settings:
   ```
   Framework:        Vite
   Root Directory:   frontend
   Build Command:    npm run build
   Output Directory: dist
   ```
4. **Environment Variables**:

   | Key | Value |
   |-----|-------|
   | `VITE_API_URL` | https://ai-agentic-backend.onrender.com/api |
   | `VITE_WS_URL` | wss://ai-agentic-backend.onrender.com/ws |

5. Click **Deploy** → ~2 minutes
6. Your frontend URL: `https://ai-agentic-assistant.vercel.app`

---

## Step 7 — Update CORS on Render

Go back to Render → your backend service → Environment:
```
CORS_ORIGINS = ["https://ai-agentic-assistant.vercel.app","http://localhost:5173"]
```
Click **Save Changes** → Render redeploys automatically.

---

## Step 8 — Verify Deployment

```bash
# Backend health
curl https://ai-agentic-backend.onrender.com/api/health

# Expected:
# {"status":"ok","openai_healthy":true,"redis_healthy":true,...}
```

Open `https://ai-agentic-assistant.vercel.app` in browser ✅

---

## ⚠️ Free Tier Limitations

| Limitation | Impact | Workaround |
|------------|--------|------------|
| Render spins down after 15min idle | First request takes ~30s | Acceptable for demo |
| Neon pauses after 5 days no activity | DB cold start ~1s | Neon auto-resumes |
| Upstash 10K commands/day | ~200 chat messages/day | Enough for demo |
| No persistent disk on Render free | FAISS index lost on redeploy | Re-ingest docs after deploy |
| No Ollama on free tier | OpenAI is primary LLM | Circuit breaker handles this |

---

## 💡 Upgrade Path (Cheapest Paid)

When ready to scale:
- Render Starter: $7/month (always-on, 512MB)
- Render Standard: $25/month (always-on, 2GB RAM — recommended)
- Neon Pro: $19/month (10GB, no pause)
- Upstash Pro: $10/month (unlimited commands)

**Total minimum paid: ~$42/month** for production-grade always-on.
