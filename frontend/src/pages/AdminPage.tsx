// frontend/src/pages/AdminPage.tsx — Enterprise admin: Audit · Usage · RBAC · Security
import { useEffect, useState } from 'react'
import { PageShell, Card, Btn, Tabs, SectionHead, Badge } from '../components/ui'
import {
  getAuditLog, getAuditSummary, getWorkspaceUsage,
  getAdminUsers, updateUserTools, updateUserRole,
} from '../lib/api'

const CORE_AGENTS = [
  { id: 'social',            label: 'Social Media Agent',    color: '#8b5cf6' },
  { id: 'ca-accounting',     label: 'CA & Accounting Agent', color: '#f59e0b' },
  { id: 'customer-support',  label: 'Customer Support Agent',color: '#10b981' },
]

const ROLE_OPTS = ['admin', 'member', 'viewer']

function Chip({ label, color = '#6b7280' }: { label: string; color?: string }) {
  return (
    <span style={{
      fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 20,
      background: `${color}22`, color, border: `1px solid ${color}44`,
    }}>{label}</span>
  )
}

export default function AdminPage() {
  const [tab, setTab] = useState('audit')

  // ── Audit Log ──
  const [auditRows, setAuditRows]   = useState<any[]>([])
  const [auditSum,  setAuditSum]    = useState<any>(null)
  const [auditDays, setAuditDays]   = useState(7)
  const [auditLoad, setAuditLoad]   = useState(false)
  const [auditErr,  setAuditErr]    = useState('')
  const [auditFilter, setAuditFilter] = useState('')

  const loadAudit = async (days: number) => {
    setAuditLoad(true); setAuditErr('')
    try {
      const [rows, sum] = await Promise.all([
        getAuditLog({ limit: 100 }),
        getAuditSummary(days),
      ])
      setAuditRows(Array.isArray(rows) ? rows : rows?.entries || [])
      setAuditSum(sum)
    } catch (e: any) {
      setAuditErr(e.message || 'Audit log unavailable — DB not connected')
      // Demo data for preview
      setAuditSum({ total_queries: 142, total_tokens: 58400, total_cost_usd: 0.0012, avg_latency_ms: 1240, guardrail_count: 3, pii_count: 1, error_count: 2, period_days: days })
      setAuditRows([
        { id: 1, user_id: 'admin@agentic.local', action: 'gst_query',       tool_called: 'ca-accounting',    timestamp: new Date().toISOString(), latency_ms: 980,  error: null, pii_detected: false },
        { id: 2, user_id: 'demo@agentic.local',  action: 'faq_bot',          tool_called: 'customer-support', timestamp: new Date(Date.now()-60000).toISOString(), latency_ms: 1200, error: null, pii_detected: false },
        { id: 3, user_id: 'admin@agentic.local', action: 'generate_post',    tool_called: 'social',           timestamp: new Date(Date.now()-120000).toISOString(), latency_ms: 1540, error: null, pii_detected: false },
        { id: 4, user_id: 'demo@agentic.local',  action: 'whatsapp_content', tool_called: 'social',           timestamp: new Date(Date.now()-180000).toISOString(), latency_ms: 870,  error: null, pii_detected: true },
        { id: 5, user_id: 'admin@agentic.local', action: 'cultural_calendar',tool_called: 'social',           timestamp: new Date(Date.now()-240000).toISOString(), latency_ms: 2100, error: null, pii_detected: false },
        { id: 6, user_id: 'demo@agentic.local',  action: 'tally_analysis',   tool_called: 'ca-accounting',    timestamp: new Date(Date.now()-300000).toISOString(), latency_ms: 1800, error: 'DB timeout', pii_detected: false },
      ])
    } finally { setAuditLoad(false) }
  }

  useEffect(() => { if (tab === 'audit') loadAudit(auditDays) }, [tab, auditDays])

  const filteredAudit = auditFilter
    ? auditRows.filter(r => r.user_id?.includes(auditFilter) || r.action?.includes(auditFilter) || r.tool_called?.includes(auditFilter))
    : auditRows

  // ── Usage Dashboard ──
  const [usage,     setUsage]     = useState<any>(null)
  const [usageDays, setUsageDays] = useState(30)
  const [usageLoad, setUsageLoad] = useState(false)

  const loadUsage = async (days: number) => {
    setUsageLoad(true)
    try {
      const u = await getWorkspaceUsage(days)
      setUsage(u)
    } catch {
      setUsage({
        period_days: days, total_calls: 142, total_tokens: 58400,
        total_cost_usd: 0.0012, active_users: 2,
        demo_mode: true,
        by_agent: [
          { agent: 'ca-accounting',    calls: 61, tokens: 24800, cost: 0.0005, avg_latency_ms: 1180, errors: 1 },
          { agent: 'social',           calls: 54, tokens: 19200, cost: 0.0004, avg_latency_ms: 1420, errors: 0 },
          { agent: 'customer-support', calls: 27, tokens: 14400, cost: 0.0003, avg_latency_ms: 960,  errors: 1 },
        ],
      })
    } finally { setUsageLoad(false) }
  }

  useEffect(() => { if (tab === 'usage') loadUsage(usageDays) }, [tab, usageDays])

  // ── RBAC / Users ──
  const [users,      setUsers]      = useState<any[]>([])
  const [rbacLoad,   setRbacLoad]   = useState(false)
  const [rbacErr,    setRbacErr]    = useState('')
  const [saving,     setSaving]     = useState<string>('')
  const [rbacMsg,    setRbacMsg]    = useState('')

  const loadUsers = async () => {
    setRbacLoad(true); setRbacErr('')
    try {
      const r = await getAdminUsers()
      setUsers(r.users || [])
    } catch {
      setRbacErr('User list unavailable — DB not connected')
      setUsers([
        { id: 'u1', email: 'admin@agentic.local',  full_name: 'Admin',      role: 'admin',  plan_tier: 'enterprise', is_active: true, allowed_tools: ['social','ca-accounting','customer-support'] },
        { id: 'u2', email: 'demo@agentic.local',   full_name: 'Demo User',  role: 'member', plan_tier: 'pro',        is_active: true, allowed_tools: ['social','customer-support'] },
      ])
    } finally { setRbacLoad(false) }
  }

  useEffect(() => { if (tab === 'rbac') loadUsers() }, [tab])

  const toggleTool = async (userId: string, tool: string, current: string[]) => {
    const next = current.includes(tool) ? current.filter(t => t !== tool) : [...current, tool]
    setSaving(userId); setRbacMsg('')
    try {
      await updateUserTools(userId, next)
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, allowed_tools: next } : u))
      setRbacMsg('Saved')
      setTimeout(() => setRbacMsg(''), 2000)
    } catch {
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, allowed_tools: next } : u))
      setRbacMsg('Saved (demo)')
      setTimeout(() => setRbacMsg(''), 2000)
    } finally { setSaving('') }
  }

  const AGENT_COLORS: Record<string, string> = { social: '#8b5cf6', 'ca-accounting': '#f59e0b', 'customer-support': '#10b981' }

  return (
    <PageShell icon="🛡️" title="Admin Panel" subtitle="Audit log · Usage analytics · Per-agent RBAC · Security">
      <Tabs
        tabs={[
          { id: 'audit', label: 'Audit Log',        icon: '📋' },
          { id: 'usage', label: 'Usage Dashboard',  icon: '📊' },
          { id: 'rbac',  label: 'User Access',      icon: '🔐' },
          { id: 'security', label: 'Security & Data', icon: '🛡️' },
        ]}
        active={tab} onChange={setTab}
      />

      {/* ── AUDIT LOG ── */}
      {tab === 'audit' && (
        <div>
          {/* Summary stats */}
          {auditSum && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(140px,1fr))', gap: 10, marginBottom: 18 }}>
              {[
                { label: 'Total Queries', value: auditSum.total_queries, color: '#10b981' },
                { label: 'Tokens Used',  value: (auditSum.total_tokens || 0).toLocaleString(), color: '#3b82f6' },
                { label: 'Cost (USD)',   value: `$${(auditSum.total_cost_usd || 0).toFixed(4)}`, color: '#a855f7' },
                { label: 'Avg Latency', value: `${Math.round(auditSum.avg_latency_ms || 0)}ms`, color: '#f59e0b' },
                { label: 'Guardrails',  value: auditSum.guardrail_count, color: '#ef4444' },
                { label: 'PII Flags',   value: auditSum.pii_count, color: '#f97316' },
                { label: 'Errors',      value: auditSum.error_count, color: '#ef4444' },
              ].map(s => (
                <div key={s.label} style={{ background: '#161b27', border: '1px solid #1e2535', borderRadius: 8, padding: '12px 14px' }}>
                  <div style={{ color: s.color, fontSize: 20, fontWeight: 700 }}>{s.value}</div>
                  <div style={{ color: '#6b7280', fontSize: 10, marginTop: 2 }}>{s.label}</div>
                </div>
              ))}
            </div>
          )}

          {/* Controls */}
          <div style={{ display: 'flex', gap: 10, marginBottom: 14, alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{ fontSize: 12, color: '#6b7280' }}>Period:</span>
            {[7, 14, 30].map(d => (
              <button key={d} onClick={() => setAuditDays(d)} style={{
                padding: '4px 12px', borderRadius: 20, fontSize: 11, cursor: 'pointer', border: 'none',
                background: auditDays === d ? 'rgba(16,185,129,0.2)' : '#1e2535',
                color: auditDays === d ? '#10b981' : '#6b7280', fontWeight: auditDays === d ? 600 : 400,
              }}>{d}d</button>
            ))}
            <input
              value={auditFilter} onChange={e => setAuditFilter(e.target.value)}
              placeholder="Filter by user / action / agent..."
              style={{
                marginLeft: 'auto', padding: '6px 12px', borderRadius: 8, fontSize: 12,
                background: '#0f1117', border: '1px solid #1e2535', color: '#e2e8f0', width: 220,
              }}
            />
            <Btn onClick={() => loadAudit(auditDays)} loading={auditLoad}>Refresh</Btn>
          </div>

          {auditErr && (
            <div style={{ padding: '8px 12px', marginBottom: 12, background: 'rgba(245,158,11,0.08)', border: '1px solid #f59e0b44', borderRadius: 6, fontSize: 11, color: '#fbbf24' }}>
              Demo data — {auditErr}
            </div>
          )}

          {/* Table */}
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #1e2535' }}>
                  {['Timestamp', 'User', 'Action', 'Agent', 'Latency', 'PII', 'Status'].map(h => (
                    <th key={h} style={{ padding: '8px 12px', textAlign: 'left', color: '#4b5563', fontWeight: 600, fontSize: 10, textTransform: 'uppercase', whiteSpace: 'nowrap' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filteredAudit.map((row: any, i: number) => (
                  <tr key={row.id || i} style={{ borderBottom: '1px solid #1e253588' }}>
                    <td style={{ padding: '8px 12px', color: '#6b7280', whiteSpace: 'nowrap' }}>
                      {new Date(row.timestamp).toLocaleString('en-IN', { hour12: false, month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td style={{ padding: '8px 12px', color: '#9ca3af', maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{row.user_id}</td>
                    <td style={{ padding: '8px 12px', color: '#e2e8f0', fontFamily: 'monospace' }}>{row.action}</td>
                    <td style={{ padding: '8px 12px' }}>
                      <Chip label={row.tool_called || 'system'} color={AGENT_COLORS[row.tool_called] || '#6b7280'} />
                    </td>
                    <td style={{ padding: '8px 12px', color: (row.latency_ms || 0) > 2000 ? '#f59e0b' : '#6b7280' }}>{row.latency_ms}ms</td>
                    <td style={{ padding: '8px 12px' }}>
                      {row.pii_detected ? <Chip label="PII" color="#f97316" /> : <span style={{ color: '#374151', fontSize: 11 }}>—</span>}
                    </td>
                    <td style={{ padding: '8px 12px' }}>
                      {row.error ? <Chip label="Error" color="#ef4444" /> : <Chip label="OK" color="#10b981" />}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filteredAudit.length === 0 && !auditLoad && (
              <div style={{ textAlign: 'center', padding: 32, color: '#374151', fontSize: 13 }}>No audit entries found</div>
            )}
          </div>
        </div>
      )}

      {/* ── USAGE DASHBOARD ── */}
      {tab === 'usage' && (
        <div>
          <div style={{ display: 'flex', gap: 10, marginBottom: 18, alignItems: 'center' }}>
            <span style={{ fontSize: 12, color: '#6b7280' }}>Period:</span>
            {[7, 30, 90].map(d => (
              <button key={d} onClick={() => setUsageDays(d)} style={{
                padding: '4px 12px', borderRadius: 20, fontSize: 11, cursor: 'pointer', border: 'none',
                background: usageDays === d ? 'rgba(16,185,129,0.2)' : '#1e2535',
                color: usageDays === d ? '#10b981' : '#6b7280', fontWeight: usageDays === d ? 600 : 400,
              }}>{d}d</button>
            ))}
            {usage?.demo_mode && (
              <span style={{ marginLeft: 'auto', fontSize: 10, color: '#fbbf24', background: 'rgba(245,158,11,0.1)', padding: '3px 10px', borderRadius: 20 }}>Demo data</span>
            )}
          </div>

          {usage && (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 12, marginBottom: 24 }}>
                {[
                  { label: 'Total Calls',   value: usage.total_calls,                       color: '#10b981' },
                  { label: 'Tokens Used',   value: (usage.total_tokens || 0).toLocaleString(), color: '#3b82f6' },
                  { label: 'Cost (USD)',     value: `$${(usage.total_cost_usd || 0).toFixed(4)}`, color: '#a855f7' },
                  { label: 'Active Users',  value: usage.active_users,                      color: '#f59e0b' },
                ].map(s => (
                  <div key={s.label} style={{ background: '#161b27', border: '1px solid #1e2535', borderRadius: 10, padding: '16px 18px', textAlign: 'center' }}>
                    <div style={{ color: s.color, fontSize: 28, fontWeight: 800 }}>{s.value}</div>
                    <div style={{ color: '#6b7280', fontSize: 11, marginTop: 4 }}>{s.label}</div>
                  </div>
                ))}
              </div>

              <div style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0', marginBottom: 12 }}>Agent Breakdown</div>
              {(usage.by_agent || []).map((a: any) => {
                const total = (usage.by_agent || []).reduce((s: number, x: any) => s + x.calls, 0)
                const pct = total > 0 ? Math.round(a.calls / total * 100) : 0
                const agentColor = AGENT_COLORS[a.agent] || '#6b7280'
                return (
                  <div key={a.agent} style={{ background: '#161b27', border: '1px solid #1e2535', borderRadius: 10, padding: '14px 18px', marginBottom: 10 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <div style={{ width: 10, height: 10, borderRadius: '50%', background: agentColor }} />
                        <span style={{ color: '#e2e8f0', fontWeight: 600, fontSize: 13 }}>{a.agent}</span>
                      </div>
                      <div style={{ display: 'flex', gap: 16 }}>
                        <span style={{ color: '#6b7280', fontSize: 11 }}>{a.calls} calls</span>
                        <span style={{ color: '#6b7280', fontSize: 11 }}>{(a.tokens || 0).toLocaleString()} tokens</span>
                        <span style={{ color: '#6b7280', fontSize: 11 }}>${(a.cost || 0).toFixed(4)}</span>
                        <span style={{ color: a.errors > 0 ? '#ef4444' : '#6b7280', fontSize: 11 }}>{a.errors} errors</span>
                      </div>
                    </div>
                    <div style={{ height: 6, background: '#1e2535', borderRadius: 3, overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${pct}%`, background: agentColor, borderRadius: 3, transition: 'width 0.4s ease' }} />
                    </div>
                    <div style={{ color: '#4b5563', fontSize: 10, marginTop: 4 }}>{pct}% of total calls · avg {a.avg_latency_ms}ms</div>
                  </div>
                )
              })}
            </>
          )}
          {usageLoad && <div style={{ textAlign: 'center', padding: 32, color: '#6b7280', fontSize: 13 }}>Loading usage data...</div>}
        </div>
      )}

      {/* ── RBAC / USER ACCESS ── */}
      {tab === 'rbac' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div>
              <div style={{ color: '#e2e8f0', fontSize: 14, fontWeight: 600 }}>Per-Agent Access Control</div>
              <div style={{ color: '#6b7280', fontSize: 12, marginTop: 2 }}>Toggle which agents each user can access</div>
            </div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              {rbacMsg && <span style={{ color: '#10b981', fontSize: 12 }}>{rbacMsg}</span>}
              <Btn onClick={loadUsers} loading={rbacLoad}>Refresh</Btn>
            </div>
          </div>

          {rbacErr && (
            <div style={{ padding: '8px 12px', marginBottom: 12, background: 'rgba(245,158,11,0.08)', border: '1px solid #f59e0b44', borderRadius: 6, fontSize: 11, color: '#fbbf24' }}>
              Demo data — {rbacErr}
            </div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {users.map(user => (
              <div key={user.id} style={{ background: '#161b27', border: '1px solid #1e2535', borderRadius: 12, padding: '16px 20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
                  <div>
                    <div style={{ color: '#e2e8f0', fontWeight: 600, fontSize: 14 }}>{user.full_name || user.email}</div>
                    <div style={{ color: '#6b7280', fontSize: 11, marginTop: 2 }}>{user.email}</div>
                  </div>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <Chip label={user.role} color={user.role === 'admin' ? '#ef4444' : '#3b82f6'} />
                    <Chip label={user.plan_tier} color={user.plan_tier === 'enterprise' ? '#10b981' : '#a855f7'} />
                    <Chip label={user.is_active ? 'Active' : 'Inactive'} color={user.is_active ? '#10b981' : '#6b7280'} />
                  </div>
                </div>
                <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 10, fontWeight: 600 }}>AGENT ACCESS</div>
                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                  {CORE_AGENTS.map(agent => {
                    const hasAccess = (user.allowed_tools || []).includes(agent.id)
                    return (
                      <button
                        key={agent.id}
                        onClick={() => toggleTool(user.id, agent.id, user.allowed_tools || [])}
                        disabled={saving === user.id}
                        style={{
                          padding: '8px 16px', borderRadius: 8, fontSize: 12, cursor: 'pointer',
                          border: `1px solid ${hasAccess ? agent.color : '#1e2535'}`,
                          background: hasAccess ? `${agent.color}22` : 'transparent',
                          color: hasAccess ? agent.color : '#4b5563',
                          fontWeight: hasAccess ? 600 : 400,
                          transition: 'all 0.15s',
                          display: 'flex', alignItems: 'center', gap: 6,
                        }}
                      >
                        <span style={{ width: 8, height: 8, borderRadius: '50%', background: hasAccess ? agent.color : '#374151', display: 'inline-block' }} />
                        {agent.label}
                      </button>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── SECURITY & DATA ── */}
      {tab === 'security' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <Card>
            <SectionHead title="Data Localisation" sub="Where your data lives" />
            {[
              { label: 'Backend Hosting', value: 'Render (Singapore region)', icon: '☁️', ok: true },
              { label: 'Database',        value: 'Neon PostgreSQL (ap-southeast-1)', icon: '🗄️', ok: true },
              { label: 'LLM Provider',    value: 'Groq (US) / Gemini (US) — prompts only, no data stored', icon: '🤖', ok: true },
              { label: 'Data Residency',  value: 'All user data stays in Asia-Pacific region', icon: '🌏', ok: true },
              { label: 'CERT-In Ready',   value: 'Audit logs retained 60 days (configurable)', icon: '📋', ok: true },
            ].map(item => (
              <div key={item.label} style={{ display: 'flex', gap: 12, padding: '10px 0', borderBottom: '1px solid #1e2535' }}>
                <span style={{ fontSize: 18 }}>{item.icon}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ color: '#9ca3af', fontSize: 11, fontWeight: 600 }}>{item.label}</div>
                  <div style={{ color: '#e2e8f0', fontSize: 12, marginTop: 2 }}>{item.value}</div>
                </div>
                <span style={{ color: item.ok ? '#10b981' : '#ef4444', fontSize: 16 }}>{item.ok ? '✓' : '✗'}</span>
              </div>
            ))}
          </Card>

          <Card>
            <SectionHead title="Security Controls" sub="Active protection layers" />
            {[
              { label: 'PII Detection',      desc: 'Aadhaar, PAN, phone, email auto-detected and flagged', ok: true },
              { label: 'JWT Authentication', desc: 'Signed tokens, 30-day expiry, sessionStorage only', ok: true },
              { label: 'RBAC',               desc: 'Per-agent access control, role-based permissions', ok: true },
              { label: 'Audit Trail',        desc: 'Every AI call logged with user, action, latency, cost', ok: true },
              { label: 'Rate Limiting',      desc: 'Per-user token quotas enforced at API layer', ok: true },
              { label: 'HTTPS Only',         desc: 'TLS 1.3 enforced, no HTTP downgrade', ok: true },
              { label: 'SSO / Google Login', desc: 'OAuth2 integration — coming in next release', ok: false },
            ].map(item => (
              <div key={item.label} style={{ display: 'flex', gap: 12, padding: '10px 0', borderBottom: '1px solid #1e2535' }}>
                <span style={{ color: item.ok ? '#10b981' : '#6b7280', fontSize: 18, marginTop: 1 }}>{item.ok ? '✓' : '○'}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ color: item.ok ? '#e2e8f0' : '#6b7280', fontSize: 12, fontWeight: 600 }}>{item.label}</div>
                  <div style={{ color: '#6b7280', fontSize: 11, marginTop: 2 }}>{item.desc}</div>
                </div>
              </div>
            ))}
          </Card>

          <Card>
            <SectionHead title="Compliance Checklist" sub="What enterprise buyers ask for" />
            {[
              { label: 'Data Processing Agreement (DPA)', status: 'Available on request', color: '#f59e0b' },
              { label: 'CERT-In Compliance',             status: 'Audit logs + incident response', color: '#10b981' },
              { label: 'PDPB / DPDP Act readiness',      status: 'Data minimisation + consent layer', color: '#10b981' },
              { label: 'ISO 27001',                      status: 'Target Q3 2026', color: '#6b7280' },
              { label: 'SOC 2 Type II',                  status: 'Target Q4 2026', color: '#6b7280' },
              { label: 'Pen Test Report',                status: 'Available for enterprise tier', color: '#f59e0b' },
            ].map(item => (
              <div key={item.label} style={{ display: 'flex', justifyContent: 'space-between', padding: '9px 0', borderBottom: '1px solid #1e2535' }}>
                <span style={{ color: '#9ca3af', fontSize: 12 }}>{item.label}</span>
                <span style={{ color: item.color, fontSize: 11, fontWeight: 600 }}>{item.status}</span>
              </div>
            ))}
          </Card>

          <Card>
            <SectionHead title="LLM Data Handling" sub="What gets sent to AI providers" />
            <div style={{ padding: '10px 0', borderBottom: '1px solid #1e2535' }}>
              <div style={{ color: '#e2e8f0', fontSize: 12, fontWeight: 600, marginBottom: 6 }}>What is sent to Groq / Gemini</div>
              <div style={{ color: '#6b7280', fontSize: 11, lineHeight: 1.7 }}>
                Only the prompt text you enter. No user account data, no auth tokens, no database records are included in LLM calls.
              </div>
            </div>
            <div style={{ padding: '10px 0', borderBottom: '1px solid #1e2535' }}>
              <div style={{ color: '#e2e8f0', fontSize: 12, fontWeight: 600, marginBottom: 6 }}>PII Handling</div>
              <div style={{ color: '#6b7280', fontSize: 11, lineHeight: 1.7 }}>
                PII detected in prompts is flagged in the audit log. Aadhaar, PAN, phone numbers are detected via regex before LLM submission.
              </div>
            </div>
            <div style={{ padding: '10px 0' }}>
              <div style={{ color: '#e2e8f0', fontSize: 12, fontWeight: 600, marginBottom: 6 }}>LLM Provider Data Retention</div>
              <div style={{ color: '#6b7280', fontSize: 11, lineHeight: 1.7 }}>
                Groq: 0 days (no training on API data). Gemini: per Google API terms — prompts not used for training on paid tier.
              </div>
            </div>
          </Card>
        </div>
      )}
    </PageShell>
  )
}
