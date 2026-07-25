// frontend/src/pages/SettingsPage.tsx — User settings, system status, cost analytics, social accounts
import { useState, useEffect } from 'react'
import { PageShell, Card, Btn, SectionHead, Badge } from '../components/ui'
import { apiFetch } from '../lib/api'
import { getSocialTokens, setSocialTokens, clearSocialTokens } from '../lib/socialTokens'

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
  const [tab,     setTab]     = useState<'profile'|'system'|'cost'|'social'>('profile')
  const [tokens,  setTokens]  = useState(() => getSocialTokens())
  const [oauthMsg, setOauthMsg] = useState<{ ok: boolean; text: string } | null>(null)

  const token   = sessionStorage.getItem('aaa_token') || ''
  const claims  = decodeJwt(token)
  const expires = claims.exp ? new Date(claims.exp * 1000) : null

  const BACKEND = import.meta.env.VITE_API_URL?.replace('/api', '') ?? 'http://localhost:8000'

  useEffect(() => {
    apiFetch('/health').then(setHealth).catch(() => {})
    apiFetch('/cost/report').then(setCosts).catch(() => {})

    // App.tsx saves OAuth result to sessionStorage before rendering settings
    const raw = sessionStorage.getItem('social_notify')
    if (raw) {
      try {
        setOauthMsg(JSON.parse(raw))
        setTab('social')
        setTokens(getSocialTokens())
      } catch { /* ignore */ }
      sessionStorage.removeItem('social_notify')
    }
  }, [])

  function logout() {
    sessionStorage.removeItem('aaa_token')
    window.location.reload()
  }

  function disconnectLinkedIn() {
    setSocialTokens({ linkedin_access_token: '', linkedin_person_urn: '' })
    setTokens(getSocialTokens())
  }

  function disconnectBuffer() {
    setSocialTokens({ buffer_access_token: '' })
    setTokens(getSocialTokens())
  }

  const TAB = (id: typeof tab, _label: string): React.CSSProperties => ({
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
      <div style={{ display: 'flex', gap: 4, marginBottom: 16, flexWrap: 'wrap' }}>
        <button style={TAB('profile', 'Profile')} onClick={() => setTab('profile')}>👤 Profile</button>
        <button style={TAB('system',  'System')}  onClick={() => setTab('system')}>🔧 System Status</button>
        <button style={TAB('cost',    'Cost')}    onClick={() => setTab('cost')}>💰 Cost Analytics</button>
        <button style={TAB('social',  'Social')}  onClick={() => setTab('social')}>🔗 Social Accounts</button>
      </div>

      {/* Profile Tab */}
      {tab === 'profile' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card>
            <SectionHead title="Account Info" sub="Your account details" />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              {[
                { label: 'Email',           value: claims.email || '—' },
                { label: 'Plan',            value: (claims.plan_tier || '—').charAt(0).toUpperCase() + (claims.plan_tier || '').slice(1) },
                { label: 'Workspace',       value: claims.workspace_slug || 'default' },
                { label: 'Session Expires', value: expires ? expires.toLocaleString() : '—' },
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
            <div style={{ display: 'flex', gap: 12, alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#22c55e', display: 'inline-block' }} />
                <span style={{ color: '#9ca3af', fontSize: 13 }}>
                  Session active{expires ? ` · expires ${expires.toLocaleDateString()}` : ''}
                </span>
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
            <SectionHead title="Platform Status" sub="Live health of your AI workspace" />
            {health ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {[
                  { label: 'Platform',   ok: health.status === 'ok' },
                  { label: 'AI Engine',  ok: health.status === 'ok' },
                ].map(s => (
                  <div key={s.label} style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    background: '#0f1117', borderRadius: 8, padding: '10px 14px',
                  }}>
                    <span style={{ color: '#9ca3af', fontSize: 13 }}>
                      <StatusDot ok={s.ok} />{s.label}
                    </span>
                    <Badge text={s.ok ? 'Online' : 'Degraded'} color={s.ok ? 'green' : 'yellow'} />
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ color: '#6b7280', fontSize: 13, textAlign: 'center', padding: '20px 0' }}>
                Checking status…
              </div>
            )}
            <Btn variant="secondary" style={{ marginTop: 12 }}
              onClick={() => apiFetch('/health').then(setHealth).catch(() => {})}>
              ↻ Refresh
            </Btn>
          </Card>

          <Card>
            <SectionHead title="Platform Details" sub="What powers your AI workspace" />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              {[
                { label: 'AI Models',    value: 'Groq · Gemini · OpenAI' },
                { label: 'Languages',    value: 'English · Tamil · Hindi' },
                { label: 'AI Features',  value: '135 AI-powered tools' },
                { label: 'Security',     value: 'JWT Auth · PII-safe' },
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
      {/* Social Accounts Tab */}
      {tab === 'social' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16, maxWidth: 600 }}>

          {/* OAuth result banner */}
          {oauthMsg && (
            <div style={{
              padding: '12px 16px', borderRadius: 10, fontSize: 13, fontWeight: 500,
              background: oauthMsg.ok ? 'rgba(34,197,94,0.12)' : 'rgba(239,68,68,0.12)',
              border: `1px solid ${oauthMsg.ok ? 'rgba(34,197,94,0.35)' : 'rgba(239,68,68,0.35)'}`,
              color: oauthMsg.ok ? '#22c55e' : '#f87171',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            }}>
              <span>{oauthMsg.ok ? '✅' : '❌'} {oauthMsg.text}</span>
              <button onClick={() => setOauthMsg(null)} style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', fontSize: 16 }}>✕</button>
            </div>
          )}

          {/* LinkedIn */}
          <Card>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
              <SectionHead title="LinkedIn" sub="Post directly to your LinkedIn profile" />
              <span style={{
                padding: '3px 10px', borderRadius: 20, fontSize: 11, fontWeight: 600,
                background: tokens.linkedin_access_token ? 'rgba(34,197,94,0.15)' : 'rgba(107,114,128,0.15)',
                color: tokens.linkedin_access_token ? '#22c55e' : '#6b7280',
                border: `1px solid ${tokens.linkedin_access_token ? 'rgba(34,197,94,0.3)' : 'rgba(107,114,128,0.25)'}`,
                flexShrink: 0, marginTop: 4,
              }}>
                {tokens.linkedin_access_token ? '● Connected' : '○ Not connected'}
              </span>
            </div>

            {tokens.linkedin_access_token ? (
              <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
                <div style={{ flex: 1, fontSize: 12, color: '#22c55e' }}>
                  ✓ LinkedIn account connected
                </div>
                <Btn variant="secondary" onClick={disconnectLinkedIn}
                  style={{ fontSize: 12, padding: '6px 14px', color: '#ef4444' }}>
                  Disconnect
                </Btn>
                <Btn
                  onClick={() => window.location.href = `${BACKEND}/api/auth/linkedin/start`}
                  style={{ fontSize: 12, padding: '6px 14px', background: 'rgba(10,102,194,0.2)', border: '1px solid rgba(10,102,194,0.4)', color: '#60a5fa' }}>
                  Re-connect
                </Btn>
              </div>
            ) : (
              <div>
                <Btn
                  onClick={() => window.location.href = `${BACKEND}/api/auth/linkedin/start`}
                  style={{ background: '#0a66c2', color: '#fff', gap: 8 }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                  </svg>
                  Connect with LinkedIn
                </Btn>
                <div style={{ marginTop: 8, color: '#6b7280', fontSize: 12, lineHeight: 1.5 }}>
                  You'll be redirected to LinkedIn to authorize. Once connected, AI-generated posts can be published directly to your profile.
                </div>
              </div>
            )}
          </Card>

          {/* Buffer */}
          <Card>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
              <SectionHead title="Buffer" sub="Schedule posts to LinkedIn, Twitter, Instagram & Facebook" />
              <span style={{
                padding: '3px 10px', borderRadius: 20, fontSize: 11, fontWeight: 600,
                background: tokens.buffer_access_token ? 'rgba(34,197,94,0.15)' : 'rgba(107,114,128,0.15)',
                color: tokens.buffer_access_token ? '#22c55e' : '#6b7280',
                border: `1px solid ${tokens.buffer_access_token ? 'rgba(34,197,94,0.3)' : 'rgba(107,114,128,0.25)'}`,
                flexShrink: 0, marginTop: 4,
              }}>
                {tokens.buffer_access_token ? '● Connected' : '○ Not connected'}
              </span>
            </div>

            {tokens.buffer_access_token ? (
              <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                <div style={{ flex: 1, fontSize: 12, color: '#9ca3af' }}>Token saved ✓</div>
                <Btn variant="secondary" onClick={disconnectBuffer}
                  style={{ fontSize: 12, padding: '6px 14px', color: '#ef4444' }}>
                  Disconnect
                </Btn>
                <Btn
                  onClick={() => window.location.href = `${BACKEND}/api/auth/buffer/start`}
                  style={{ fontSize: 12, padding: '6px 14px', background: 'rgba(245,158,11,0.2)', border: '1px solid rgba(245,158,11,0.4)', color: '#fbbf24' }}>
                  Re-connect
                </Btn>
              </div>
            ) : (
              <div>
                <Btn
                  onClick={() => window.location.href = `${BACKEND}/api/auth/buffer/start`}
                  style={{ background: '#f5a623', color: '#000', fontWeight: 700, gap: 8 }}>
                  🗄 Connect with Buffer
                </Btn>
                <div style={{ marginTop: 8, color: '#6b7280', fontSize: 12, lineHeight: 1.5 }}>
                  Connects LinkedIn, Twitter/X, Instagram & Facebook in one place. Schedule AI-generated posts across all platforms.
                </div>
              </div>
            )}
          </Card>

          {/* Instagram */}
          <Card>
            <SectionHead title="Instagram" sub="Schedule via Buffer (recommended) or Meta Business API" />
            <div style={{ color: '#6b7280', fontSize: 13, lineHeight: 1.7 }}>
              Instagram requires a <strong style={{ color: '#e2e8f0' }}>Meta Business Account</strong> linked to a Facebook Page.<br />
              Easiest path: connect <strong style={{ color: '#fbbf24' }}>Buffer</strong> above — it handles Instagram scheduling for you, no extra setup needed.
            </div>
          </Card>

          <div style={{ color: '#374151', fontSize: 11 }}>
            🔒 Tokens stored only in your browser's localStorage. Never sent to third-party servers.
          </div>
        </div>
      )}
    </PageShell>
  )
}
