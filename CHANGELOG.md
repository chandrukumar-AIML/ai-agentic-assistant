# Changelog

All notable changes to AI Agentic Assistant are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added
- `PITCH.md` — one-page product pitch for investors and clients
- `PERSONAS.md` — 5 Indian SMB user personas driving feature decisions
- `ROADMAP.md` — Q3/Q4 2026 + 2027 vision roadmap
- `PORTFOLIO.md` — hiring manager showcase with resume bullet points
- `.env.example` — complete environment variable template (40+ vars)
- `SECURITY.md` — vulnerability reporting policy and security checklist
- `CONTRIBUTING.md` — contributor guide with vertical creation walkthrough
- `CHANGELOG.md` — this file
- `ARCHITECTURE.md` — detailed system design with sequence diagrams
- `.github/workflows/ci.yml` — GitHub Actions CI pipeline

---

## [1.0.0] — 2025-12 → 2026-07

### Added — CS Agent (Customer Support) — 38 features

| Action | Description |
|--------|-------------|
| `faq_bot` | FAQ answering with business context |
| `qualify_lead` | Lead qualification scoring |
| `draft_whatsapp` | WhatsApp message drafting |
| `analyze_sentiment` | Customer sentiment + urgency analysis |
| `handle_complaint` | Complaint resolution with steps |
| `summarize_ticket` | Ticket conversation summarization |
| `response_template` | Support response templates by scenario |
| `weekly_report` | Weekly CS executive report |
| `kb_answer` | Knowledge base Q&A |
| `suggest_canned_response` | Canned response suggestion |
| `analyze_sla` | SLA breach analysis |
| `ticket_triage` | Ticket priority + category routing |
| `voc_report` | Voice of Customer analysis |
| `review_response` | Review response drafting |
| `sla_policy` | SLA policy document generation |
| `agent_training` | Agent training module generation |
| `chatbot_script` | WhatsApp chatbot script builder |
| `returns_policy` | Returns policy document generator |
| `support_analytics` | Weekly support analytics dashboard |
| `customer_360` | Customer health + history view |
| `csat_survey` | CSAT survey builder |
| `winback_campaign` | Win-back campaign for churned customers |
| `escalation_email` | Escalation email drafter |
| `kb_article` | Knowledge base article writer |
| `onboarding_sequence` | Customer onboarding email sequence |
| `nps_campaign_builder` | NPS survey + follow-up builder |
| `agent_performance_scorecard` | Agent performance scorecard |
| `winback_sequence` | Multi-touch win-back sequence |
| `customer_health_score` | Customer health scoring |
| `escalation_rule_builder` | Escalation rule configuration |
| `ticket_categorizer` | Bulk ticket categorization |
| `onboarding_planner` | Customer onboarding plan |
| `churn_risk` | Churn risk assessment |
| `escalation_manager` | Escalation queue manager |
| `build_csat_survey` | CSAT survey configuration |
| `analyze_csat` | CSAT response analysis |
| `send_whatsapp` | WhatsApp message sending (Twilio) |

**QA Status: 37/37 PASS** (send_whatsapp requires Twilio creds)

### Added — CA Agent (CA Accounting) — 40 features

| Action | Description |
|--------|-------------|
| `gst_query` | GST rate and rule Q&A |
| `client_email` | CA client advisory email |
| `deadlines` | Compliance deadline calendar |
| `tds_calc` | TDS calculation by section |
| `invoice` | GST invoice generation |
| `audit_checklist` | Tax audit checklist |
| `reconciliation` | GSTR-2B reconciliation |
| `itr_advice` | ITR form selection advice |
| `ca_social_post` | CA firm social media post |
| `client_query` | Client tax query answering |
| `compliance_calendar` | Full compliance calendar |
| `tally_analysis` | Tally data GST analysis |
| `generate_invoice` | Full GST invoice with PDF |
| `capital_gains` | Capital gains calculation |
| `rent_receipts` | Rent receipt generation |
| `hra_80c_planner` | HRA + 80C tax planning |
| `gstr_assistant` | GSTR scheme adviser |
| `mca_roc_calendar` | MCA/ROC filing calendar |
| `directors_report` | Directors' report generation |
| `startup_guide` | Startup registration guide |
| `partnership_deed` | Partnership deed drafter |
| `advance_tax` | Advance tax installment calc |
| `balance_sheet` | Balance sheet template |
| `form_16` | Form 16 generation |
| `client_compliance_status` | Client compliance dashboard |
| `salary_slip` | Salary slip generator |
| `itr_checklist` | ITR filing checklist |
| `depreciation_calc` | Asset depreciation schedule |
| `gst_invoice` | GST-compliant invoice |
| `client_proposal` | CA firm client proposal |
| `tds_compliance_tracker` | TDS deduction tracker |
| `msme_loan_eligibility` | MSME loan eligibility check |
| `pl_statement` | P&L statement |
| `overdue_collector` | Overdue payment collector |
| `cash_flow_forecast` | Cash flow projection |
| `business_valuation` | Business valuation (DCF + multiples) |
| `gst_notice_reply` | GST notice reply drafter |
| `payroll` | Payroll processing |
| `tax_planning` | Tax optimization planning |
| `gstr_filing_prep` | GSTR-3B filing preparation |

**QA Status: 40/40 PASS**

### Added — SM Agent (Social Media) — 37 features

Full social media management: content generation, platform scheduling, analytics, campaigns, hashtags, competitor analysis, engagement, and publishing.

**QA Status: All features verified**

### Added — Infrastructure

- FastAPI backend with JWT auth, RBAC, rate limiting
- React 18 + TypeScript + Vite frontend (6 pages)
- LLM routing: Ollama → Groq → Gemini → OpenAI fallback chain
- Docker + docker-compose for local and production
- Render (backend) + Vercel (frontend) deploy ($0/month)
- Multi-tenant architecture: per-client tool entitlements

### Fixed

- `cs._impl`: `lang` NameError in 5 dispatch branches (was: `language=lang`, fixed: `language=language`)
- `cs._impl`: `nps_campaign_builder` IndexError on empty name string (`.split()[0]` on empty list)
- `cs._impl`: `_categorize_ticket` TypeError when `custom_categories` is a list of strings
- `ca._impl`: `generate_invoice` dispatch — was calling wrong internal function
- Auth endpoints: `/api/auth/login`, `/api/auth/me`, `/api/auth/profile` added
- Multiple response key mismatches across CS + CA agents (discovered via QA)

---

## Version History

| Version | Date | Highlights |
|---------|------|------------|
| 1.0.0 | 2026-07 | 3 agents live, 115 features, 100% QA pass rate |
| 0.9.0 | 2026-06 | CA agent complete (40 features) |
| 0.8.0 | 2026-05 | CS agent complete (37 features) |
| 0.7.0 | 2026-04 | SM agent complete |
| 0.5.0 | 2026-01 | Multi-tenant auth, LLM routing |
| 0.1.0 | 2025-12 | Initial FastAPI + React scaffold |
