// frontend/src/lib/api.ts — Complete API client for all 19 features
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

// Dev-only: 30-day token for local testing (generated from backend JWT_SECRET)
// In production this constant is never used — getToken() returns '' and the
// real auth flow (OAuth / login page) must populate 'aaa_token'.
const DEV_TOKEN = import.meta.env.PROD
  ? ''
  : 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.' +
    'eyJzdWIiOiJkZXYtdXNlci0wMDEiLCJlbWFpbCI6ImRldkBhZ2VudGljLmxvY2FsIiwid29' +
    'ya3NwYWNlX2lkIjoid3MtZGVmYXVsdCIsIndvcmtzcGFjZV9zbHVnIjoiZGVmYXVsdCIsIn' +
    'JvbGUiOiJhZG1pbiIsInBsYW5fdGllciI6ImVudGVycHJpc2UiLCJpYXQiOjE3Nzk1OTg5' +
    'NDQsImV4cCI6MTc4MjE5MDk0NH0.' +
    'fHSryNMy-rRs7NoDmrkkxhguAhHjjH_0XKO1vdw1e3s'

// TODO production: replace sessionStorage JWT with httpOnly cookie for XSS protection
function getToken(): string {
  const stored = sessionStorage.getItem('aaa_token')
  if (stored) return stored
  // Seed dev token only in development builds
  if (DEV_TOKEN) {
    sessionStorage.setItem('aaa_token', DEV_TOKEN)
    return DEV_TOKEN
  }
  return ''
}

export async function apiFetch(path: string, options: RequestInit = {}, timeoutMs = 30_000): Promise<any> {
  const controller = new AbortController()
  const timeout    = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      signal:  controller.signal,
      headers: {
        'Authorization': `Bearer ${getToken()}`,
        'Content-Type':  'application/json',
        ...(options.headers || {}),
      },
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ message: res.statusText }))
      throw new Error(err.message || err.detail || `HTTP ${res.status}`)
    }
    return res.json()
  } finally {
    clearTimeout(timeout)
  }
}

// ── Core Chat ─────────────────────────────────────────────────────────────────
export async function submitFeedback(runId: string, score: number, comment = '', abLogId?: number) {
  await apiFetch('/feedback', { method: 'POST', body: JSON.stringify({ run_id: runId, score, comment, ab_log_id: abLogId }) })
}
export async function getHistory(sessionId: string) { return apiFetch(`/history/${sessionId}`) }
export async function clearHistory(sessionId: string) { return apiFetch(`/history/${sessionId}`, { method: 'DELETE' }) }
export async function getRagStats() { return apiFetch('/rag/stats') }

// ── Health ────────────────────────────────────────────────────────────────────
export async function getServerInfo() {
  const res = await fetch('http://localhost:8000/')
  return res.json()
}

// ── RAG File Ingest ───────────────────────────────────────────────────────────
export async function ingestFile(file: File, category = 'general'): Promise<{ chunks_indexed: number; filename: string }> {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 120_000)
  const form = new FormData()
  form.append('file', file)
  form.append('category', category)
  try {
    const res = await fetch(`${API_BASE}/ingest`, {
      method: 'POST', signal: controller.signal,
      headers: { Authorization: `Bearer ${getToken()}` },
      body: form,
    })
    if (!res.ok) throw new Error(`Upload failed: ${res.statusText}`)
    return res.json()
  } finally { clearTimeout(timeout) }
}

// ── Feature 1: Guardian / Compliance ─────────────────────────────────────────
export async function checkCompliance(content: string) {
  return apiFetch('/compliance/check', { method: 'POST', body: JSON.stringify({ text: content }) })
}

// ── Feature 3: Memory ─────────────────────────────────────────────────────────
export async function getMemories(userId: string) { return apiFetch(`/memory/${userId}`) }
export async function addMemory(userId: string, content: string) {
  return apiFetch(`/memory/${userId}`, { method: 'POST', body: JSON.stringify({ content }) })
}

// ── Feature 4: Task Scheduler ─────────────────────────────────────────────────
export async function listTasks() { return apiFetch('/scheduler/tasks') }
export async function createTask(payload: { name: string; task_type: string; schedule_expr: string; payload?: any }) {
  return apiFetch('/scheduler/tasks', { method: 'POST', body: JSON.stringify(payload) })
}
export async function pauseTask(id: string) { return apiFetch(`/scheduler/tasks/${id}/pause`, { method: 'POST' }) }
export async function resumeTask(id: string) { return apiFetch(`/scheduler/tasks/${id}/resume`, { method: 'POST' }) }
export async function deleteTask(id: string) { return apiFetch(`/scheduler/tasks/${id}`, { method: 'DELETE' }) }

// ── Feature 5: Commerce ───────────────────────────────────────────────────────
export async function createPaymentLink(amount: number, currency = 'INR', description = '') {
  return apiFetch('/commerce/payment-link', { method: 'POST', body: JSON.stringify({ amount, currency, description }) })
}

// ── Feature 6: HITL ───────────────────────────────────────────────────────────
export async function listApprovals(status?: string) {
  // Backend uses /hitl/pending (all pending) or /hitl/history
  const path = status === 'history' ? '/hitl/history' : '/hitl/pending'
  return apiFetch(path)
}
export async function reviewApproval(approvalId: string, action: 'approve' | 'reject' | 'request_changes', comment = '') {
  return apiFetch(`/hitl/${approvalId}/decision`, {
    method: 'POST',
    body: JSON.stringify({ decision: action === 'approve' ? 'approved' : action === 'reject' ? 'rejected' : 'request_changes', comment }),
  })
}

// ── Feature 7: Output Generator ───────────────────────────────────────────────
export async function generatePDF(title: string, content: string, sections?: any[]) {
  return apiFetch('/outputs/generate', { method: 'POST', body: JSON.stringify({ format: 'pdf', title, content, sections: sections || [] }) })
}
export async function generateExcel(sheets: any[]) {
  return apiFetch('/outputs/generate', { method: 'POST', body: JSON.stringify({ format: 'excel', sheets }) })
}
export async function generatePPTX(title: string, slides: any[]) {
  return apiFetch('/outputs/generate', { method: 'POST', body: JSON.stringify({ format: 'pptx', title, slides }) })
}

// ── Feature 8: Billing ────────────────────────────────────────────────────────
export async function getBillingStatus() { return apiFetch('/billing/subscription') }
export async function getBillingPlans() { return apiFetch('/billing/plans') }
export async function getUsageStats() { return apiFetch('/billing/usage') }
export async function upgradePlan(plan: string) {
  return apiFetch('/billing/checkout/stripe', { method: 'POST', body: JSON.stringify({ plan_tier: plan, success_url: window.location.href, cancel_url: window.location.href }) })
}
export async function upgradePlanRazorpay(plan: string, phone = '') {
  return apiFetch('/billing/checkout/razorpay', { method: 'POST', body: JSON.stringify({ plan_tier: plan, phone }) })
}

// ── Feature 9: AgriTech — all non-query are GET with query params ─────────────
export async function agriQuery(query: string, language = 'en', district?: string, state = 'Tamil Nadu') {
  // Ollama can take 2-5 min on CPU, so 360s timeout
  return apiFetch('/verticals/agri/query', { method: 'POST', body: JSON.stringify({ query, language, district, state }) }, 360_000)
}
export async function getMandiPrices(commodity: string, state = 'Tamil Nadu', district?: string) {
  // GET endpoint with query params
  const params = new URLSearchParams({ commodity, state })
  if (district) params.set('district', district)
  return apiFetch(`/verticals/agri/mandi-prices?${params}`)
}
export async function getWeather(district: string, state = 'Tamil Nadu', language = 'en') {
  // GET endpoint with query params
  const params = new URLSearchParams({ district, state, language })
  return apiFetch(`/verticals/agri/weather?${params}`)
}
export async function getSchemes(query: string, language = 'en') {
  // GET endpoint with query params
  const params = new URLSearchParams({ query, language })
  return apiFetch(`/verticals/agri/schemes?${params}`)
}

// ── Feature 10: Legal ─────────────────────────────────────────────────────────
export async function legalQuery(query: string, language = 'en') {
  return apiFetch('/verticals/legal/query', { method: 'POST', body: JSON.stringify({ query, language }) }, 360_000)
}
export async function legalCaseSearch(query: string, docTypes = 'judgments', maxResults = 5) {
  return apiFetch('/verticals/legal/case-search', {
    method: 'POST',
    body: JSON.stringify({ query, doc_types: docTypes, max_results: maxResults }),
  })
}

// ── Feature 11: Cybersec — cve-search is GET, others POST ────────────────────
export async function cybersecQuery(query: string, logText?: string, cveKeyword?: string) {
  return apiFetch('/verticals/cybersec/full-scan', {
    method: 'POST',
    body: JSON.stringify({ query, log_text: logText || query, cve_keyword: cveKeyword }),
  })
}
export async function analyzeLogs(logText: string, generateReport = false) {
  return apiFetch('/verticals/cybersec/analyze-logs', {
    method: 'POST',
    body: JSON.stringify({ log_text: logText, generate_report: generateReport }),
  })
}
export async function searchCVE(keyword: string, severity?: string, limit = 10) {
  // GET endpoint with query params — NVD API can take up to 60s
  const params = new URLSearchParams({ keyword, limit: String(limit) })
  if (severity) params.set('severity', severity.toUpperCase())
  return apiFetch(`/verticals/cybersec/cve-search?${params}`, {}, 60_000)
}

// ── Feature 12: A/B Testing ───────────────────────────────────────────────────
export async function listExperiments() { return apiFetch('/ab/experiments') }
export async function createExperiment(payload: any) {
  return apiFetch('/ab/experiments', { method: 'POST', body: JSON.stringify(payload) })
}
export async function getExperiment(id: string) { return apiFetch(`/ab/experiments/${id}`) }
export async function runABTurn(id: string, query: string) {
  return apiFetch(`/ab/experiments/${id}/run`, { method: 'POST', body: JSON.stringify({ query }) })
}
export async function getABSignificance(id: string) { return apiFetch(`/ab/experiments/${id}/significance`) }
export async function promoteWinner(id: string) {
  return apiFetch(`/ab/experiments/${id}/promote`, { method: 'POST' })
}

// ── Feature 13: Receptionist — endpoint is /receptionist/chat ────────────────
export async function receptionistQuery(message: string, sessionId = 'demo', userName?: string) {
  return apiFetch('/verticals/receptionist/chat', {
    method: 'POST',
    body: JSON.stringify({ message, channel: 'web', session_id: sessionId, user_name: userName }),
  }, 120_000)
}

// ── Feature 14: Form Reader — endpoint is /verticals/forms/extract ────────────
export async function extractForm(imageB64: string, formHint?: string, redactPii = false) {
  return apiFetch('/verticals/forms/extract', {
    method: 'POST',
    body: JSON.stringify({ image_b64: imageB64, form_hint: formHint, redact_pii: redactPii }),
  }, 120_000)
}
export async function validateIdentifiers(ids: {
  pan?: string; gstin?: string; aadhaar?: string; mobile?: string; pincode?: string; ifsc?: string
}) {
  return apiFetch('/verticals/forms/validate', { method: 'POST', body: JSON.stringify(ids) })
}

// ── Feature 15: Email Manager — uses /verticals/email/action ──────────────────
export async function listEmails(provider = 'gmail', accessToken = 'mock-token') {
  return apiFetch('/verticals/email/action', {
    method: 'POST',
    body: JSON.stringify({ action: 'list', provider, access_token: accessToken }),
  })
}
export async function draftEmail(to: string, subject: string, context: string, provider = 'gmail', accessToken = 'mock-token') {
  return apiFetch('/verticals/email/action', {
    method: 'POST',
    body: JSON.stringify({
      action: 'draft',
      provider,
      access_token: accessToken,
      draft_params: { to, subject, extra_context: context },
    }),
  }, 120_000)
}

// ── Feature 16: Sales — /verticals/sales/score and /verticals/sales/action ───
export async function scoreLead(lead: {
  budget_usd?: number;
  title?: string;
  company_size?: number;   // INTEGER (employee count)
  has_need?: boolean;
  timeline_days?: number;
  [key: string]: any
}) {
  return apiFetch('/verticals/sales/score', { method: 'POST', body: JSON.stringify(lead) })
}
export async function handleObjection(objection: string, product = 'AI Platform') {
  return apiFetch('/verticals/sales/action', {
    method: 'POST',
    body: JSON.stringify({
      action: 'generate_outreach',
      lead: { name: 'Prospect', objection },
      product,
    }),
  }, 120_000)
}
export async function salesAction(action: string, lead: any, product = 'our AI platform', crm = 'none') {
  return apiFetch('/verticals/sales/action', {
    method: 'POST',
    body: JSON.stringify({ action, lead, crm, product }),
  }, 120_000)
}

// ── Feature 17: Accountant — uses /verticals/accountant/action ───────────────
export async function calcGST(amount: number, gstRate: number, isInterstate = false) {
  return apiFetch('/verticals/accountant/action', {
    method: 'POST',
    body: JSON.stringify({
      action: 'gst_calc',
      payload: {
        amount,
        gst_rate: gstRate,
        transaction: isInterstate ? 'inter' : 'intra',   // backend uses "intra"/"inter"
      },
    }),
  })
}
export async function calcTDS(paymentType: string, amount: number, panAvailable = true) {
  return apiFetch('/verticals/accountant/action', {
    method: 'POST',
    body: JSON.stringify({
      action: 'tds_calc',
      payload: {
        amount,
        section: paymentType,       // backend expects "section" (e.g. "194J")
        pan_available: panAvailable,
      },
    }),
  })
}
export async function accountantQuery(query: string) {
  return apiFetch('/verticals/accountant/action', {
    method: 'POST',
    body: JSON.stringify({ action: 'query', payload: { query } }),
  }, 360_000)
}
export async function lookupHSN(hsnCode: string) {
  return apiFetch(`/verticals/accountant/hsn/${hsnCode}`)
}

// ── Feature 18: HR — uses /verticals/hr/action ────────────────────────────────
export async function screenResume(resumeText: string, jobDescription: string, requiredSkills: string[] = []) {
  return apiFetch('/verticals/hr/action', {
    method: 'POST',
    body: JSON.stringify({
      action: 'screen',
      payload: {
        resume_text: resumeText,
        job_description: jobDescription,
        required_skills: requiredSkills,
      },
    }),
  }, 360_000)   // Ollama resume screening can be slow
}
export async function generateJD(roleTitle: string, department = 'Engineering', companyName = 'Our Company', requiredSkills: string[] = []) {
  return apiFetch('/verticals/hr/action', {
    method: 'POST',
    body: JSON.stringify({
      action: 'generate_jd',
      payload: { role_title: roleTitle, department, company_name: companyName, required_skills: requiredSkills },
    }),
  }, 360_000)
}
export async function generateOnboardingChecklist(role: string, department = 'Engineering', startDate?: string) {
  return apiFetch('/verticals/hr/action', {
    method: 'POST',
    body: JSON.stringify({
      action: 'onboarding',
      payload: { role, department, start_date: startDate || new Date().toISOString().split('T')[0] },
    }),
  }, 120_000)
}
export async function hrPolicyQA(question: string) {
  return apiFetch('/verticals/hr/action', {
    method: 'POST',
    body: JSON.stringify({
      action: 'qa',
      payload: { question },
    }),
  }, 360_000)
}

// ── Feature 19: Social Media — uses /verticals/social/action ─────────────────
export async function generateContent(topic: string, platform: string, tone = 'professional', brand = '') {
  return apiFetch('/verticals/social/action', {
    method: 'POST',
    body: JSON.stringify({
      action: 'generate',
      platform,
      payload: { topic, tone, brand, include_hashtags: true },
    }),
  }, 360_000)
}
export async function generateHashtags(topic: string, platform = 'instagram') {
  return apiFetch('/verticals/social/action', {
    method: 'POST',
    body: JSON.stringify({
      action: 'hashtags',
      platform,
      payload: { topic },
    }),
  }, 120_000)
}
export async function generateImage(prompt: string) {
  return apiFetch('/verticals/social/action', {
    method: 'POST',
    body: JSON.stringify({
      action: 'image',
      platform: 'all',
      payload: { prompt },
    }),
  }, 120_000)
}
export async function socialGenerateAll(topic: string, tone = 'professional', brand = '') {
  const params = new URLSearchParams({ topic, tone, brand })
  return apiFetch(`/verticals/social/generate-all?${params}`, {}, 360_000)
}
export async function submitSocialForApproval(postText: string, platform: string, topic: string, reviewerEmail = '') {
  return apiFetch('/hitl/request', {
    method: 'POST',
    body: JSON.stringify({
      action_type:     'social_post_publish',
      action_payload:  { post_text: postText, platform, topic },
      context_summary: `Social post for ${platform.toUpperCase()} — "${topic.slice(0, 80)}" — needs team review before publishing.`,
      session_id:      '',
      reviewer_email:  reviewerEmail || undefined,
    }),
  })
}

export async function socialPro(action: string, payload: object, platform = 'linkedin', language = 'en') {
  return apiFetch('/verticals/social/pro', {
    method: 'POST',
    body: JSON.stringify({ action, platform, payload, language }),
  }, 480_000)
}

// ── QA Engineer Vertical ──────────────────────────────────────────────────────
export async function qaAction(action: string, payload: object) {
  return apiFetch('/verticals/qa/action', {
    method: 'POST',
    body: JSON.stringify({ action, payload }),
  }, 360_000)
}

// ── Project Manager Vertical ──────────────────────────────────────────────────
export async function pmAction(action: string, payload: object) {
  return apiFetch('/verticals/pm/action', {
    method: 'POST',
    body: JSON.stringify({ action, payload }),
  }, 360_000)
}

// ── Code Assistant Vertical ───────────────────────────────────────────────────
export async function codeAction(action: string, code: string, prompt: string, language = 'python') {
  return apiFetch('/verticals/code/action', {
    method: 'POST',
    body: JSON.stringify({ action, code, prompt, language }),
  }, 360_000)
}

// ── ML Engineer Vertical ──────────────────────────────────────────────────────
export async function mlAction(action: string, payload: object) {
  return apiFetch('/verticals/ml/action', {
    method: 'POST',
    body: JSON.stringify({ action, payload }),
  }, 360_000)
}

// ── DBA Vertical ──────────────────────────────────────────────────────────────
export async function dbaAction(action: string, payload: object) {
  return apiFetch('/verticals/dba/action', {
    method: 'POST',
    body: JSON.stringify({ action, payload }),
  }, 360_000)
}

// ── Tech Lead Vertical ────────────────────────────────────────────────────────
export async function techLeadAction(action: string, payload: object) {
  return apiFetch('/verticals/techlead/action', {
    method: 'POST',
    body: JSON.stringify({ action, payload }),
  }, 360_000)
}

// ── Auth + Entitlements (Phase 1) ─────────────────────────────────────────────
export interface UserProfile {
  email: string
  full_name: string
  role: string            // 'admin' | 'user' | 'viewer'
  plan_tier: string       // 'free' | 'pro' | 'enterprise'
  allowed_tools: string[]
  is_active: boolean
  total_queries?: number
  daily_query_count?: number
}

export async function login(email: string, password: string) {
  return apiFetch('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) })
}
export async function signup(email: string, password: string, fullName = '') {
  return apiFetch('/auth/signup', { method: 'POST', body: JSON.stringify({ email, password, full_name: fullName }) })
}
export async function getMe(): Promise<{ profile: UserProfile; always_allowed: string[]; is_admin: boolean; demo_mode?: boolean }> {
  return apiFetch('/auth/me')
}
export async function getToolsCatalog(): Promise<{ catalog: { id: string; label: string; category: string }[]; always_allowed: string[] }> {
  return apiFetch('/tools/catalog')
}
export interface Integration {
  id: string; name: string; vertical: string; unlocks: string
  configured: boolean; always_on: boolean; env_vars: string[]
}
export async function getIntegrationsStatus(): Promise<{ integrations: Integration[]; live: number; total: number }> {
  return apiFetch('/integrations/status')
}
export async function listClients(): Promise<{ clients: UserProfile[]; total: number }> {
  return apiFetch('/clients')
}
export async function setClientTools(email: string, tools: string[]) {
  return apiFetch(`/clients/${encodeURIComponent(email)}/tools`, { method: 'POST', body: JSON.stringify({ tools }) })
}
export async function setClientPlan(email: string, planTier: string) {
  return apiFetch(`/clients/${encodeURIComponent(email)}/plan`, { method: 'POST', body: JSON.stringify({ plan_tier: planTier }) })
}
export async function setClientActive(email: string, isActive: boolean) {
  return apiFetch(`/clients/${encodeURIComponent(email)}/active`, { method: 'POST', body: JSON.stringify({ is_active: isActive }) })
}

// ── Auth: Refresh Token ───────────────────────────────────────────────────────
export async function refreshToken(token: string) {
  return apiFetch('/auth/refresh', {
    method: 'POST',
    body: JSON.stringify({ refresh_token: token }),
  })
}

// ── Enhancement API helpers (new tabs across all verticals) ──────────────────
const enhanceAction = (path: string, action: string, payload: object, lang = 'en') =>
  apiFetch(path, { method: 'POST', body: JSON.stringify({ action, payload, language: lang }) }, 360_000)

export const devopsIac     = (action: string, p: object) => enhanceAction('/verticals/devops/iac', action, p)
export const cybersecOwasp = (action: string, p: object) => enhanceAction('/verticals/cybersec/owasp', action, p)
export const salesEnhance  = (action: string, p: object) => enhanceAction('/verticals/sales/enhance', action, p)
export const hrEnhance     = (action: string, p: object) => enhanceAction('/verticals/hr/enhance', action, p)
export const acctEnhance   = (action: string, p: object) => enhanceAction('/verticals/accountant/enhance', action, p)
export const legalEnhance  = (action: string, p: object) => enhanceAction('/verticals/legal/enhance', action, p)
export const socialEnhance = (action: string, p: object) => enhanceAction('/verticals/social/enhance', action, p)
export const rcptEnhance   = (action: string, p: object) => enhanceAction('/verticals/receptionist/enhance', action, p)
export const analystEnhance= (action: string, p: object) => enhanceAction('/verticals/analyst/enhance', action, p)
export const agriEnhance   = (action: string, p: object, lang = 'en') => enhanceAction('/verticals/agri/enhance', action, p, lang)
export const tlEnhance     = (action: string, p: object) => enhanceAction('/verticals/techlead/enhance', action, p)

// ── New Verticals: Healthcare, Real Estate, EdTech ───────────────────────────
export const healthcareAction = (action: string, payload: object) =>
  apiFetch('/verticals/healthcare/action', { method: 'POST', body: JSON.stringify({ action, payload }) }, 360_000)
export const realestateAction = (action: string, payload: object) =>
  apiFetch('/verticals/realestate/action', { method: 'POST', body: JSON.stringify({ action, payload }) }, 360_000)
export const edtechAction = (action: string, payload: object) =>
  apiFetch('/verticals/edtech/action', { method: 'POST', body: JSON.stringify({ action, payload }) }, 360_000)

// ── Analyst Vertical — POST /vertical/analyst?query=... ───────────────────────
export async function analystQuery(query: string, contextJson = '{}') {
  const params = new URLSearchParams({ query, context_json: contextJson })
  return apiFetch(`/vertical/analyst?${params}`, { method: 'POST' }, 360_000)
}

// ── DevOps Vertical — POST /vertical/devops?query=...&context_json=... ────────
export async function devopsQuery(
  query: string,
  repo = '',
  service = '',
  jiraProject = '',
) {
  const context: Record<string, string> = {}
  if (repo)        context['default_repo']    = repo
  if (service)     context['default_service'] = service
  if (jiraProject) context['jira_project']    = jiraProject
  const params = new URLSearchParams({
    query,
    context_json: JSON.stringify(context),
  })
  return apiFetch(`/vertical/devops?${params}`, { method: 'POST' }, 360_000)
}
