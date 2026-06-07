// frontend/src/pages/IntegrationsPage.tsx — live integration status (realness made visible)
import { useEffect, useMemo, useState } from 'react'
import { PageShell, Card, SectionHead, StatCard } from '../components/ui'
import { getIntegrationsStatus, Integration } from '../lib/api'

export default function IntegrationsPage() {
  const [items, setItems]     = useState<Integration[]>([])
  const [live, setLive]       = useState(0)
  const [total, setTotal]     = useState(0)
  const [loading, setLoading] = useState(true)
  const [err, setErr]         = useState('')

  useEffect(() => {
    getIntegrationsStatus()
      .then(r => { setItems(r.integrations); setLive(r.live); setTotal(r.total) })
      .catch(e => setErr(e.message || 'Failed to load'))
      .finally(() => setLoading(false))
  }, [])

  const byVertical = useMemo(() => {
    const g: Record<string, Integration[]> = {}
    items.forEach(it => { (g[it.vertical] ||= []).push(it) })
    return g
  }, [items])

  return (
    <PageShell icon="🔌" title="Integrations" subtitle="Real external integrations — what's live now and what activates when you add API keys">
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 14, marginBottom: 22 }}>
        <StatCard label="Live Now"        value={loading ? '…' : live}  icon="🟢" />
        <StatCard label="Available"       value={loading ? '…' : total} icon="🔌" />
        <StatCard label="Activation"      value="Add API key" icon="🔑" />
      </div>

      {err && <div style={{ padding: '10px 14px', marginBottom: 14, background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 8, color: '#fca5a5', fontSize: 13 }}>⚠ {err}</div>}

      <div style={{ padding: '10px 14px', marginBottom: 18, background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.25)', borderRadius: 8, fontSize: 12, color: '#5eead4' }}>
        🟢 <b>Live</b> = real integration active now. ⚙️ <b>Setup</b> = code is wired and ready — add the listed environment variable on the server to switch it on. No code changes needed.
      </div>

      {Object.entries(byVertical).map(([vertical, list]) => (
        <Card key={vertical} style={{ marginBottom: 14 }}>
          <SectionHead title={vertical} sub={`${list.filter(i => i.configured).length}/${list.length} live`} />
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 10 }}>
            {list.map(it => (
              <div key={it.id} style={{
                padding: '12px 14px', borderRadius: 10,
                background: it.configured ? 'rgba(34,197,94,0.06)' : '#0f1117',
                border: `1px solid ${it.configured ? 'rgba(34,197,94,0.3)' : '#1e2535'}`,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <span style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 600 }}>{it.name}</span>
                  <span style={{
                    fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 20,
                    background: it.configured ? 'rgba(34,197,94,0.15)' : 'rgba(245,158,11,0.12)',
                    color: it.configured ? '#86efac' : '#fbbf24',
                  }}>
                    {it.configured ? (it.always_on ? '🟢 LIVE' : '🟢 LIVE') : '⚙️ SETUP'}
                  </span>
                </div>
                <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 6 }}>{it.unlocks}</div>
                {!it.configured && it.env_vars.length > 0 && (
                  <div style={{ fontSize: 10, color: '#6b7280' }}>
                    Add: {it.env_vars.map(v => (
                      <code key={v} style={{ color: '#5eead4', background: '#161b27', padding: '1px 5px', borderRadius: 4, marginRight: 4 }}>{v}</code>
                    ))}
                  </div>
                )}
                {it.always_on && <div style={{ fontSize: 10, color: '#6b7280' }}>No key required — always on</div>}
              </div>
            ))}
          </div>
        </Card>
      ))}
    </PageShell>
  )
}
