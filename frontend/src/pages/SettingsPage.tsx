// frontend/src/pages/SettingsPage.tsx — User settings, system status, profile
import { useState, useEffect } from 'react'
import { PageShell, Card, Btn, SectionHead, Badge } from '../components/ui'
import { apiFetch } from '../lib/api'

interface Health {
  status: string
  openai_healthy: boolean
  redis_healthy: boolean
  circuit_state: string
  ollama_model?: string
}

interface CostReport {
  total_cost_usd: number
  total_queries: number
  cache_hits: number
  cache_hit_rate: number
  avg_cost_per_query: number
  model_breakdown: Record<string, number>
}

function decodeJwt(token: string): Record<string, any> {
  try { return JSON.parse(atob(token.split('.')[1])) } catch { return {} }
}

export default function SettingsPage() {
  const [health,  setHealth]  = useState<Health | null>(null)
  const [costs,   setCosts]   = useState<CostReport | null>(null)
  const [tab,     setTab]     = useState<'profile'|'system'|'cost'>('profile')

  const token   = sessionStorage.getItem('aaa_token') || ''
  const claims  = decodeJwt(token)
  const expires = claims.exp ? new Date(claims.exp * 1000) : null

  useEffect(() => {
    apiFetch('/health').then(setHealth).catch(() => {})
    apiFetch('/cost/report').then(setCosts).catch(() => {})
  }, [])

  function logout() {
    sessionStorage.removeItem('aaa_token')
    window.location.reload()
  }

  const TAB = (id: typeof tab, label: string): React.CSSProperties => ({
    padding: '7px 16px', borderRadius: 6, border: 'none', cursor: 'pointer', fontSize: 13,
    background: tab === id ? 'rgba(16,185,129,0.2)' : 'none',
    color: tab === id ? '#5eead4' : '#6b7280',
  })

  const StatusDot = ({ ok }: { ok: boolean }) => (
    <span style={{
      display: 'inline-block', width: 8, height: 8, borderRadius: '50%',
      background: ok ? '#22c55e' : '#ef4444', marginRight: 6,
    }} />
  )

  return (
    <PageShell icon="⚙️" title="Settings" subtitle="Profile, system status, and cost analytics">

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 16 }}>
        <button style={TAB('profile', 'Profile')} onClick={() => setTab('profile')}>👤 Profile</button>
        <button style={TAB('system',  'System')}  onClick={() => setTab('system')}>🔧 System Status</button>
        <button style={TAB('cost',    'Cost')}    onClick={() => setTab('cost')}>💰 Cost Analytics</button>
      </div>

      {/* Profile Tab */}
      {tab === 'profile' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card>
            <SectionHead title="Account Info" sub="JWT-based identity from your current session" />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              {[
                { label: 'User ID',    value: claims.sub || '—' },
                { label: 'Email',      value: claims.email || '—' },
                { label: 'Role',       value: claims.role || '—' },
                { label: 'Plan',       value: claims.plan_tier || '—' },
                { label: 'Workspace',  value: claims.workspace_slug || '—' },
                { label: 'Token Exp.', value: expires ? expires.toLocaleString() : '—' },
              ].map(f => (
                <div key={f.label} style={{ background: '#0f1117', borderRadius: 8, padding: '10px 14px' }}>
                  <div style={{ color: '#6b7280', fontSize: 11, marginBottom: 4 }}>{f.label.toUpperCase()}</div>
                  <div style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 500, wordBreak: 'break-all' }}>{f.value}</div>
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <SectionHead title="Session" sub="Manage your current session" />
            <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
              <div style={{ flex: 1 }}>
                <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 4 }}>Current Token (truncated)</div>
                <code style={{
                  display: 'block', background: '#0f1117', borderRadius: 6, padding: '8px 12px',
                  color: '#10b981', fontSize: 11, wordBreak: 'break-all',
                }}>
                  {token ? `${token.substring(0, 40)}…` : 'No token'}
                </code>
              </div>
              <Btn variant="secondary" onClick={logout} style={{ flexShrink: 0, color: '#ef4444' }}>
                🚪 Sign Out
              </Btn>
            </div>
          </Card>
        </div>
      )}

      {/* System Tab */}
      {tab === 'system' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card>
            <SectionHead title="Service Health" sub="Live status from /api/health" />
            {health ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {[
                  { label: 'API Server',    ok: health.status === 'ok' },
                  { label: 'OpenAI',        ok: health.openai_healthy },
                  { label: 'Redis Cache',   ok: health.redis_healthy },
                  { label: 'LLM Circuit',   ok: health.circuit_state === 'closed' },
                ].map(s => (
                  <div key={s.label} style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    background: '#0f1117', borderRadius: 8, padding: '10px 14px',
                  }}>
                    <span style={{ color: '#9ca3af', fontSize: 13 }}>
                      <StatusDot ok={s.ok} />{s.label}
                    </span>
                    <Badge text={s.ok ? 'Online' : 'Offline'} color={s.ok ? 'green' : 'red'} />
                  </div>
                ))}
                {health.ollama_model && (
                  <div style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    background: '#0f1117', borderRadius: 8, padding: '10px 14px',
                  }}>
                    <span style={{ color: '#9ca3af', fontSize: 13 }}><StatusDot ok={true} />Ollama Model</span>
                    <Badge text={health.ollama_model!} color="purple" />
                  </div>
                )}
              </div>
            ) : (
              <div style={{ color: '#6b7280', fontSize: 13, textAlign: 'center', padding: '20px 0' }}>
                Loading health status…
              </div>
            )}
            <Btn variant="secondary" style={{ marginTop: 12 }}
              onClick={() => apiFetch('/health').then(setHealth).catch(() => {})}>
              ↻ Refresh
            </Btn>
          </Card>

          <Card>
            <SectionHead title="Stack Info" sub="AI Agentic Assistant V2 tech stack" />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              {[
                { label: 'Backend',     value: 'FastAPI + LangGraph' },
                { label: 'Frontend',    value: 'React 18 + Vite + TS' },
                { label: 'LLM',        value: 'OpenAI gpt-4o + Ollama' },
                { label: 'Vector DB',   value: 'FAISS + ChromaDB' },
                { label: 'Graph DB',    value: 'Neo4j (optional)' },
                { label: 'Cache',       value: 'Redis + Semantic cache' },
                { label: 'Observ.',     value: 'LangSmith + MLflow' },
                { label: 'Auth',        value: 'JWT + RBAC' },
                { label: 'Features',    value: '21 enterprise features' },
                { label: 'Verticals',   value: '11 domain agents' },
              ].map(f => (
                <div key={f.label} style={{ background: '#0f1117', borderRadius: 8, padding: '8px 12px' }}>
                  <div style={{ color: '#6b7280', fontSize: 10 }}>{f.label.toUpperCase()}</div>
                  <div style={{ color: '#e2e8f0', fontSize: 12, fontWeight: 500, marginTop: 2 }}>{f.value}</div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Cost Tab */}
      {tab === 'cost' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {costs ? (
            <>
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                {[
                  { label: 'Total Cost',       value: `$${costs.total_cost_usd.toFixed(4)}`, color: '#f59e0b' },
                  { label: 'Total Queries',    value: costs.total_queries.toLocaleString(),   color: '#10b981' },
                  { label: 'Cache Hits',       value: costs.cache_hits.toLocaleString(),      color: '#22c55e' },
                  { label: 'Cache Hit Rate',   value: `${(costs.cache_hit_rate * 100).toFixed(1)}%`, color: '#06b6d4' },
                  { label: 'Avg Cost/Query',   value: `$${costs.avg_cost_per_query.toFixed(5)}`,  color: '#06b6d4' },
                ].map(s => (
                  <div key={s.label} style={{
                    background: '#161b27', border: '1px solid #1e2535',
                    borderRadius: 10, padding: '12px 18px', minWidth: 130,
                  }}>
                    <div style={{ color: '#6b7280', fontSize: 10, marginBottom: 4 }}>{s.label.toUpperCase()}</div>
                    <div style={{ color: s.color, fontSize: 18, fontWeight: 700 }}>{s.value}</div>
                  </div>
                ))}
              </div>

              {Object.keys(costs.model_breakdown || {}).length > 0 && (
                <Card>
                  <SectionHead title="Cost by Model" sub="Spend breakdown per LLM" />
                  {Object.entries(costs.model_breakdown).map(([model, cost]) => (
                    <div key={model} style={{
                      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                      background: '#0f1117', borderRadius: 8, padding: '10px 14px', marginBottom: 6,
                    }}>
                      <code style={{ color: '#5eead4', fontSize: 12 }}>{model}</code>
                      <span style={{ color: '#f59e0b', fontWeight: 600, fontSize: 13 }}>${Number(cost).toFixed(5)}</span>
                    </div>
                  ))}
                </Card>
              )}
            </>
          ) : (
            <Card>
              <div style={{ color: '#6b7280', fontSize: 13, textAlign: 'center', padding: '30px 0' }}>
                Loading cost data… (requires at least one query)
              </div>
            </Card>
          )}
        </div>
      )}
    </PageShell>
  )
}
