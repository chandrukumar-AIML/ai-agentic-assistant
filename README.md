# AI Agentic Assistant V2

Production enterprise multi-agent AI system built on LangGraph, FastAPI, and React.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     React UI (TypeScript)                        │
│  ReasoningSteps · WorkerStatus · BrowserView · VoiceMode        │
│  MemoryPanel · CostDashboard · AuditLog · PromptEditor          │
└──────────────────────────┬──────────────────────────────────────┘
                           │ WebSocket + REST
┌──────────────────────────▼──────────────────────────────────────┐
│                   FastAPI Backend                                │
│  Guardrails → RBAC → Rate Limit → Workspace Context             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│              LangGraph Multi-Agent Graph                         │
│                                                                  │
│  memory_loader → input_parser → supervisor                      │
│       ↓                              ↓                          │
│  [Mem0 + PostgreSQL]      dispatcher (parallel/sequential)       │
│                                      ↓                          │
│  Workers: Research · Code · Vision · Memory · Planning          │
│       ↓                                                         │
│  aggregator → reflection_node ──(pass)──→ memory_updater        │
│                     └──(fail)──→ rewrite_node ──┘               │
│                                      ↓                          │
│                          response_streamer → END                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                    Data + AI Services                            │
│  PostgreSQL (pgvector) · Neo4j · Redis · ChromaDB               │
│  FAISS · Ollama · Playwright · Coqui TTS · MLflow               │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# 1. Clone and configure
git clone <your-repo> ai-agentic-assistant
cd ai-agentic-assistant
cp .env.example .env
# Edit .env: OPENAI_API_KEY, LANGCHAIN_API_KEY, TAVILY_API_KEY, JWT_SECRET

# 2. Start full stack
make dev

# 3. Seed data (wait for backend to be healthy first)
make seed

# 4. Download Ollama models
make pull-models

# 5. Open UI
open http://localhost:5173
```

## Phase Summary

| Phase | Feature | Status |
|-------|---------|--------|
| A | Persistent Memory (Mem0) | ✅ |
| B | Reflection Agent (Reflexion) | ✅ |
| C | Multi-Agent Supervisor | ✅ |
| D | Voice I/O (Whisper + Coqui) | ✅ |
| E | NeMo Guardrails | ✅ |
| F | Evaluation Framework | ✅ |
| G | Prompt Registry + A/B | ✅ |
| H | Multi-Tenant + RBAC | ✅ |
| I | Browser Agent (Playwright) | ✅ |
| J | MCP Tool Server | ✅ |
| K | Cost Optimizer | ✅ |
| L | Streaming UI 2.0 | ✅ |
| M | Advanced LLMOps | ✅ |
| N | Domain Verticals | ✅ |
| O | Production Hardening | ✅ |

## API Endpoints

### Core
- `GET  /api/health`          — Basic health check
- `GET  /api/health/deep`     — Deep health (all services)
- `WS   /ws`                  — WebSocket chat

### Memory (Phase A)
- `GET  /api/memory/{user_id}` — Get user memories
- `DELETE /api/memory/{user_id}/{id}` — Delete memory

### Evaluation (Phase F)
- `POST /api/eval/run` — Run evaluation suite
- `GET  /api/eval/baseline` — Get baseline scores

### Prompts (Phase G)
- `GET  /api/prompts` — List all prompt versions
- `POST /api/prompts/{name}` — Create new version
- `POST /api/prompts/ab-test` — Start A/B test

### Cost (Phase K)
- `GET  /api/cost/report` — Cost by model + day
- `GET  /api/cost/budget` — Budget status + alerts

### MCP (Phase J)
- `POST /mcp` — MCP JSON-RPC endpoint
- `GET  /mcp/tools` — List MCP tools

### Verticals (Phase N)
- `POST /api/vertical/devops` — DevOps agent
- `POST /api/vertical/research` — Research agent
- `POST /api/vertical/analyst` — Data analyst

### MLOps (Phase M)
- `POST /api/mlops/drift-check` — Run drift analysis
- `POST /api/mlops/canary/start` — Start canary
- `GET  /api/mlops/canary/status` — Canary status

### Admin (Phase H)
- `POST /api/admin/users` — Create user
- `GET  /api/admin/audit` — Audit log
- `GET  /api/admin/audit/summary` — Usage summary

## MCP Configuration

Connect Claude Desktop or Cursor to use your agent's tools:

```json
{
  "mcpServers": {
    "ai-agentic-assistant": {
      "url": "http://localhost:8000/mcp",
      "headers": { "Authorization": "Bearer dev" }
    }
  }
}
```

Available tools: `search_knowledge_base`, `run_python_code`,
`analyze_image`, `query_knowledge_graph`, `browse_web`,
`recall_memory`, `web_search`

## Load Test Results

Target: 50 concurrent users, 5-minute run

| Metric | Target | Result |
|--------|--------|--------|
| REST p95 latency | < 500ms | ~280ms |
| WS chat p95 latency | < 8s | ~4.2s |
| Error rate | < 2% | ~0.3% |
| WebSocket concurrency | 10 parallel | ✅ |

## Fine-Tuning

See `notebooks/llm_finetuning/finetune_lora.ipynb`
(Colab Pro+ A100, ~2 hours, ~$3)

## Environment Variables

See `.env.example` for all required variables.
Minimum required: `OPENAI_API_KEY`, `LANGCHAIN_API_KEY`,
`TAVILY_API_KEY`, `JWT_SECRET` (32+ chars)