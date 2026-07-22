# Product Roadmap — AI Agentic Assistant

> Living document — updated every sprint. Last updated: 2026-07-23

---

## ✅ SHIPPED (Phases A → T)

| Phase | Feature | Status |
|-------|---------|--------|
| A | Persistent Memory (Mem0 + pgvector) | ✅ Done |
| B | Reflection Agent (Reflexion loop) | ✅ Done |
| C | Multi-Agent Supervisor + Workers | ✅ Done |
| D | Voice I/O (Whisper STT + Coqui TTS) | ✅ Done |
| E | NeMo + Custom Guardrails (PII/PHI/Injection) | ✅ Done |
| F | Evaluation Framework | ✅ Done |
| G | Prompt Registry + A/B Testing | ✅ Done |
| H | Multi-Tenant + RBAC + JWT Auth | ✅ Done |
| I | Browser Agent (Playwright) | ✅ Done |
| J | MCP Tool Server (7 tools) | ✅ Done |
| K | Cost Optimizer (tracker + budget + cache) | ✅ Done |
| L | Streaming UI 2.0 (asyncio.Queue WebSocket) | ✅ Done |
| M | Advanced LLMOps (drift, canary, MLflow) | ✅ Done |
| N | 3 Core Verticals (CS + CA + Social) | ✅ Done — 115 features, all QA'd |
| O | Production Hardening (Docker, tests, deploy) | ✅ Done |

---

## 🔄 Q3 2026 — IN PROGRESS

### P1 — Observability & LLMOps (July–August 2026)
- [ ] Token usage logging per LLM call (cost per action)
- [ ] Prompt version registry (`prompts/` folder, versioned YAML)
- [ ] LLM eval framework (automated quality scoring per vertical)
- [ ] Health endpoint — check Ollama + Groq + Gemini status
- [ ] Structured JSON logging for cloud log parsing

### P2 — DevOps & CI/CD (July–August 2026)
- [ ] GitHub Actions CI — run QA scripts on every push to master
- [ ] Automated Render deploy on CI pass
- [ ] Docker health checks in `docker-compose.yml`
- [ ] `Makefile` commands for common dev ops

### P3 — Security Hardening (August 2026)
- [ ] `detect-secrets` pre-commit hook
- [ ] `.env.example` with all variables documented
- [ ] HTTPS enforcement in production
- [ ] SQL injection test suite
- [ ] `SECURITY.md` + vulnerability disclosure policy

---

## 🟡 Q4 2026 — PLANNED

### P4 — Analytics & Growth (October–November 2026)
- [ ] PostHog integration (event tracking: signup, feature used, plan upgrade)
- [ ] Funnel analysis: landing → signup → first AI call → paid
- [ ] Feature usage heatmap per vertical
- [ ] NPS survey trigger (after 10th AI use)
- [ ] Referral tracking

### P5 — New Verticals (November–December 2026)
- [ ] **Healthcare Agent** — patient intake, lab summaries, Rx notes
- [ ] **HR Agent** — resume screening, JD generation, onboarding
- [ ] **Sales Agent** — BANT scoring, HubSpot CRM, email sequences
- [ ] **Legal Agent** — IndianKanoon search, NDA generator, contract review

### P6 — Mobile & WhatsApp (December 2026)
- [ ] WhatsApp Business API integration (Twilio)
- [ ] Mobile-responsive UI improvements
- [ ] PWA support (installable on Android)

---

## 🟢 2027 — VISION

### Platform Scale
- [ ] 10+ verticals live
- [ ] White-label option (agencies resell to clients)
- [ ] API marketplace (third-party vertical plugins)
- [ ] Regional language expansion (Tamil, Telugu, Kannada, Malayalam UI)

### Enterprise Features
- [ ] SSO (SAML 2.0, Google Workspace)
- [ ] On-premise deployment option
- [ ] SLA-backed support tier
- [ ] Audit log export (compliance)

### AI Advancement
- [ ] Fine-tuned Indian tax / legal models
- [ ] Multi-modal (process images: invoices, lab reports, GST returns)
- [ ] Real-time WhatsApp bot (embedded in client's WhatsApp Business)
- [ ] Voice-first interface (Tamil/Hindi commands)

---

## Prioritization Criteria

Every feature is scored on:

| Criterion | Weight |
|-----------|--------|
| User pain (how badly does it hurt?) | 40% |
| Revenue impact (drives upgrade / retention?) | 30% |
| Build effort (low = faster) | 20% |
| Strategic fit (India-first, AI-native?) | 10% |

---

## How to Request a Feature

Open a GitHub issue with label `feature-request` and fill in:
1. **Who needs it** (which persona from PERSONAS.md)
2. **What problem it solves** (job to be done)
3. **Why now** (urgency or revenue opportunity)
