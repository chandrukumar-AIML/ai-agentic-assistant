// frontend/src/pages/AdminPage.tsx — Phase 1: client + tool-access management
import { useEffect, useMemo, useState } from 'react'
import { PageShell, Card, Btn, Select, SectionHead, Badge } from '../components/ui'
import {
  listClients, getToolsCatalog, setClientTools, setClientPlan, setClientActive,
  UserProfile,
} from '../lib/api'

type CatalogTool = { id: string; label: string; category: string }

const PLAN_COLORS: Record<string, 'blue' | 'green' | 'purple'> = { free: 'blue', pro: 'purple', enterprise: 'green' }

export default function AdminPage() {
  const [clients, setClients]   = useState<UserProfile[]>([])
  const [catalog, setCatalog]   = useState<CatalogTool[]>([])
  const [selected, setSelected] = useState<string>('')
  const [tools, setTools]       = useState<string[]>([])
  const [plan, setPlan]         = useState<string>('free')
  const [loading, setLoading]   = useState(false)
  const [saving, setSaving]     = useState(false)
  const [msg, setMsg]           = useState('')
  const [err, setErr]           = useState('')

  const load = async () => {
    setLoading(true); setErr('')
    try {
      const [c, cat] = await Promise.all([listClients(), getToolsCatalog()])
      setClients(c.clients)
      setCatalog(cat.catalog)
      if (!selected && c.clients.length) selectClient(c.clients[0])
    } catch (e: any) {
      setErr(e.message || 'Failed to load — admin access required')
    } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])  // eslint-disable-line react-hooks/exhaustive-deps

  const selectClient = (c: UserProfile) => {
    setSelected(c.email)
    setTools(c.allowed_tools || [])
    setPlan(c.plan_tier)
    setMsg(''); setErr('')
  }

  const current = clients.find(c => c.email === selected)

  const byCategory = useMemo(() => {
    const groups: Record<string, CatalogTool[]> = {}
    catalog.forEach(t => { (groups[t.category] ||= []).push(t) })
    return groups
  }, [catalog])

  const toggleTool = (id: string) =>
    setTools(prev => prev.includes(id) ? prev.filter(t => t !== id) : [...prev, id])

  const save = async () => {
    if (!selected) return
    setSaving(true); setMsg(''); setErr('')
    try {
      await setClientTools(selected, tools)
      await setClientPlan(selected, plan)
      setMsg('✓ Saved')
      await load()
    } catch (e: any) {
      setErr(e.message || 'Save failed')
    } finally { setSaving(false) }
  }

  const toggleActive = async (c: UserProfile) => {
    try { await setClientActive(c.email, !c.is_active); await load() }
    catch (e: any) { setErr(e.message || 'Failed') }
  }

  const presetAll  = () => setTools(catalog.map(t => t.id))
  const presetNone = () => setTools([])

  return (
    <PageShell icon="🛡️" title="Admin · Client Management" subtitle="Manage clients, assign tool access per plan, control activation">
      {err && (
        <div style={{ padding: '10px 14px', marginBottom: 12, background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 8, color: '#fca5a5', fontSize: 13 }}>
          ⚠ {err}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: 16, alignItems: 'start' }}>
        {/* Client list */}
        <Card>
          <SectionHead title={`Clients (${clients.length})`} sub="Select a client to manage" />
          {loading && <div style={{ color: '#6b7280', fontSize: 12 }}>Loading…</div>}
          {clients.map(c => (
            <div key={c.email}
              onClick={() => selectClient(c)}
              style={{
                padding: '10px 12px', marginBottom: 6, borderRadius: 8, cursor: 'pointer',
                background: selected === c.email ? 'rgba(99,102,241,0.15)' : '#0f1117',
                border: `1px solid ${selected === c.email ? '#6366f1' : '#1e2535'}`,
              }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 600 }}>{c.full_name || c.email}</span>
                {c.role === 'admin' && <Badge text="ADMIN" color="green" />}
              </div>
              <div style={{ color: '#6b7280', fontSize: 11, marginTop: 2 }}>{c.email}</div>
              <div style={{ display: 'flex', gap: 6, marginTop: 6, alignItems: 'center' }}>
                <Badge text={c.plan_tier} color={PLAN_COLORS[c.plan_tier] || 'blue'} />
                <span style={{ fontSize: 10, color: '#6b7280' }}>{(c.allowed_tools || []).length} tools</span>
                {!c.is_active && <span style={{ fontSize: 10, color: '#f87171' }}>· disabled</span>}
              </div>
            </div>
          ))}
        </Card>

        {/* Detail panel */}
        {current ? (
          <Card>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
              <SectionHead title={current.full_name || current.email} sub={current.email} />
              <button onClick={() => toggleActive(current)} style={{
                padding: '6px 12px', borderRadius: 6, fontSize: 12, cursor: 'pointer',
                background: current.is_active ? 'rgba(239,68,68,0.1)' : 'rgba(34,197,94,0.1)',
                border: `1px solid ${current.is_active ? 'rgba(239,68,68,0.3)' : 'rgba(34,197,94,0.3)'}`,
                color: current.is_active ? '#fca5a5' : '#86efac',
              }}>
                {current.is_active ? 'Deactivate' : 'Activate'}
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 8 }}>
              <Select label="Plan Tier" value={plan} onChange={setPlan}
                options={[{ label: 'Free', value: 'free' }, { label: 'Pro', value: 'pro' }, { label: 'Enterprise', value: 'enterprise' }]} />
              <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8 }}>
                <button onClick={presetAll}  style={presetBtn}>Select all</button>
                <button onClick={presetNone} style={presetBtn}>Clear all</button>
              </div>
            </div>

            <div style={{ fontSize: 12, color: '#9ca3af', margin: '8px 0 4px', fontWeight: 600 }}>
              Tool Access · {tools.length} selected
            </div>
            {Object.entries(byCategory).map(([cat, items]) => (
              <div key={cat} style={{ marginBottom: 10 }}>
                <div style={{ fontSize: 10, color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.06em', margin: '6px 0 4px' }}>{cat}</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4 }}>
                  {items.map(t => {
                    const on = tools.includes(t.id)
                    return (
                      <label key={t.id} style={{
                        display: 'flex', alignItems: 'center', gap: 8, padding: '6px 8px', borderRadius: 6, cursor: 'pointer',
                        background: on ? 'rgba(99,102,241,0.1)' : '#0f1117',
                        border: `1px solid ${on ? 'rgba(99,102,241,0.3)' : '#1e2535'}`,
                      }}>
                        <input type="checkbox" checked={on} onChange={() => toggleTool(t.id)} style={{ accentColor: '#6366f1' }} />
                        <span style={{ fontSize: 12, color: on ? '#a5b4fc' : '#9ca3af' }}>{t.label}</span>
                      </label>
                    )
                  })}
                </div>
              </div>
            ))}

            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 14 }}>
              <Btn onClick={save} loading={saving}>💾 Save Changes</Btn>
              {msg && <span style={{ color: '#86efac', fontSize: 13 }}>{msg}</span>}
            </div>
          </Card>
        ) : (
          <Card><div style={{ color: '#6b7280', fontSize: 13 }}>Select a client to manage their access.</div></Card>
        )}
      </div>
    </PageShell>
  )
}

const presetBtn: React.CSSProperties = {
  flex: 1, padding: '8px 0', borderRadius: 6, fontSize: 11, cursor: 'pointer',
  background: '#1e2535', border: '1px solid #374151', color: '#9ca3af',
}
