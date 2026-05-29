// frontend/src/pages/WebhooksPage.tsx — Webhook integration manager
// Companies use this to connect the AI platform to Slack, Zapier, custom backends
import { useState, useEffect } from 'react'
import { PageShell, Card, Btn, SectionHead } from '../components/ui'
import { apiFetch } from '../lib/api'

interface Webhook {
  id:         string
  name:       string
  url:        string
  events:     string[]
  active:     boolean
  created_at: string
  last_fired: string | null
  fire_count: number
}

const EVENT_DESCRIPTIONS: Record<string, string> = {
  'agent.response':        'Every AI agent response',
  'hitl.created':          'Human approval requested',
  'hitl.resolved':         'Human approval decision made',
  'scheduler.completed':   'Scheduled task finished',
  'ingest.completed':      'Document ingestion done',
  'budget.alert':          'Cost budget threshold hit',
  'compliance.violation':  'Guardrail / compliance triggered',
  'user.login':            'User signs in',
}

const INTEGRATIONS = [
  { name: 'Slack',    icon: '💬', hint: 'https://hooks.slack.com/services/...' },
  { name: 'Discord',  icon: '🎮', hint: 'https://discord.com/api/webhooks/...' },
  { name: 'Zapier',   icon: '⚡', hint: 'https://hooks.zapier.com/hooks/catch/...' },
  { name: 'Make',     icon: '🔧', hint: 'https://hook.eu1.make.com/...' },
  { name: 'n8n',      icon: '🔄', hint: 'https://your-n8n.com/webhook/...' },
  { name: 'Custom',   icon: '🌐', hint: 'https://your-api.com/webhook' },
]

export default function WebhooksPage() {
  const [webhooks,      setWebhooks]    = useState<Webhook[]>([])
  const [validEvents,   setValidEvents] = useState<string[]>([])
  const [loading,       setLoading]     = useState(true)
  const [showForm,      setShowForm]    = useState(false)
  const [testing,       setTesting]     = useState<string | null>(null)
  const [testResult,    setTestResult]  = useState<Record<string, string>>({})

  // Form state
  const [name,     setName]    = useState('')
  const [url,      setUrl]     = useState('')
  const [secret,   setSecret]  = useState('')
  const [events,   setEvents]  = useState<string[]>([])
  const [saving,   setSaving]  = useState(false)
  const [formErr,  setFormErr] = useState('')

  async function load() {
    try {
      const data = await apiFetch('/webhooks')
      setWebhooks(data.webhooks || [])
      setValidEvents(data.valid_events || [])
    } catch {}
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  function toggleEvent(ev: string) {
    setEvents(prev => prev.includes(ev) ? prev.filter(e => e !== ev) : [...prev, ev])
  }

  async function createWebhook() {
    if (!name.trim() || !url.trim() || events.length === 0) {
      setFormErr('Name, URL, and at least one event are required.')
      return
    }
    setSaving(true); setFormErr('')
    try {
      const wh = await apiFetch('/webhooks', {
        method: 'POST',
        body: JSON.stringify({ name, url, events, secret: secret || undefined }),
      })
      setWebhooks(prev => [...prev, wh])
      setName(''); setUrl(''); setSecret(''); setEvents([]); setShowForm(false)
    } catch (e: any) {
      setFormErr(e.message || 'Failed to create webhook')
    } finally { setSaving(false) }
  }

  async function deleteWebhook(id: string) {
    try {
      await apiFetch(`/webhooks/${id}`, { method: 'DELETE' })
      setWebhooks(prev => prev.filter(w => w.id !== id))
    } catch {}
  }

  async function toggleWebhook(id: string) {
    try {
      const data = await apiFetch(`/webhooks/${id}/toggle`, { method: 'PATCH' })
      setWebhooks(prev => prev.map(w => w.id === id ? { ...w, active: data.active } : w))
    } catch {}
  }

  async function testWebhook(id: string) {
    setTesting(id)
    try {
      const data = await apiFetch(`/webhooks/${id}/test`, { method: 'POST' })
      setTestResult(prev => ({ ...prev, [id]: data.message || 'Test fired ✓' }))
      setTimeout(() => setTestResult(prev => { const n = { ...prev }; delete n[id]; return n }), 4000)
    } catch (e: any) {
      setTestResult(prev => ({ ...prev, [id]: `✗ ${e.message}` }))
    } finally { setTesting(null) }
  }

  function fmt(iso: string | null) {
    if (!iso) return '—'
    return new Date(iso).toLocaleString()
  }

  return (
    <PageShell icon="🔌" title="Webhook Manager"
      subtitle="Connect AI events to Slack, Discord, Zapier, n8n, or any custom endpoint">

      {/* Integration logos row */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
        {INTEGRATIONS.map(i => (
          <div key={i.name} style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '6px 12px', borderRadius: 20,
            background: '#161b27', border: '1px solid #1e2535',
            fontSize: 12, color: '#9ca3af',
          }}>
            <span>{i.icon}</span> {i.name}
          </div>
        ))}
      </div>

      {/* Active webhooks */}
      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
          <SectionHead
            title={`Active Webhooks (${webhooks.length})`}
            sub="Registered endpoints that receive AI platform events"
          />
          <Btn variant="primary" onClick={() => setShowForm(s => !s)}>
            {showForm ? '✕ Cancel' : '+ Add Webhook'}
          </Btn>
        </div>

        {/* Create form */}
        {showForm && (
          <div style={{
            background: '#0f1117', borderRadius: 10,
            border: '1px solid #1e2535', padding: '18px 20px',
            marginBottom: 20,
          }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
              <div>
                <label style={{ display: 'block', color: '#6b7280', fontSize: 11, marginBottom: 4 }}>WEBHOOK NAME</label>
                <input value={name} onChange={e => setName(e.target.value)}
                  placeholder="e.g. Slack Alerts"
                  style={{ width: '100%', padding: '8px 10px', background: '#161b27', border: '1px solid #1e2535', borderRadius: 6, color: '#e2e8f0', fontSize: 13, outline: 'none', boxSizing: 'border-box' }} />
              </div>
              <div>
                <label style={{ display: 'block', color: '#6b7280', fontSize: 11, marginBottom: 4 }}>SECRET (optional)</label>
                <input value={secret} onChange={e => setSecret(e.target.value)}
                  placeholder="HMAC signing secret"
                  style={{ width: '100%', padding: '8px 10px', background: '#161b27', border: '1px solid #1e2535', borderRadius: 6, color: '#e2e8f0', fontSize: 13, outline: 'none', boxSizing: 'border-box' }} />
              </div>
            </div>
            <div style={{ marginBottom: 12 }}>
              <label style={{ display: 'block', color: '#6b7280', fontSize: 11, marginBottom: 4 }}>ENDPOINT URL</label>
              <input value={url} onChange={e => setUrl(e.target.value)}
                placeholder="https://hooks.slack.com/services/..."
                style={{ width: '100%', padding: '8px 10px', background: '#161b27', border: '1px solid #1e2535', borderRadius: 6, color: '#e2e8f0', fontSize: 13, outline: 'none', boxSizing: 'border-box' }} />
            </div>

            <div style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', color: '#6b7280', fontSize: 11, marginBottom: 8 }}>SUBSCRIBE TO EVENTS</label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {validEvents.map(ev => (
                  <button key={ev} onClick={() => toggleEvent(ev)} style={{
                    padding: '4px 12px', borderRadius: 20, fontSize: 11, cursor: 'pointer',
                    border: '1px solid',
                    borderColor: events.includes(ev) ? '#6366f1' : '#1e2535',
                    background: events.includes(ev) ? 'rgba(99,102,241,0.15)' : '#161b27',
                    color: events.includes(ev) ? '#a5b4fc' : '#6b7280',
                    transition: 'all 0.15s',
                  }}>
                    {ev}
                  </button>
                ))}
              </div>
              {events.length > 0 && (
                <div style={{ marginTop: 8, fontSize: 11, color: '#4b5563' }}>
                  Selected: {events.join(', ')}
                </div>
              )}
            </div>

            {formErr && (
              <div style={{ color: '#f87171', fontSize: 12, marginBottom: 10 }}>⚠ {formErr}</div>
            )}

            <Btn variant="primary" onClick={createWebhook} disabled={saving}>
              {saving ? 'Registering…' : '✓ Register Webhook'}
            </Btn>
          </div>
        )}

        {/* Webhook list */}
        {loading ? (
          <div style={{ color: '#6b7280', fontSize: 13, textAlign: 'center', padding: '30px 0' }}>
            Loading webhooks…
          </div>
        ) : webhooks.length === 0 && !showForm ? (
          <div style={{ textAlign: 'center', padding: '40px 0', color: '#6b7280' }}>
            <div style={{ fontSize: 36, marginBottom: 12 }}>🔌</div>
            <div style={{ fontSize: 14, marginBottom: 6 }}>No webhooks registered yet.</div>
            <div style={{ fontSize: 12 }}>Click "Add Webhook" to connect Slack, Zapier, n8n, or your own API.</div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {webhooks.map(wh => (
              <div key={wh.id} style={{
                background: '#0f1117', border: '1px solid #1e2535',
                borderRadius: 10, padding: '14px 16px',
                opacity: wh.active ? 1 : 0.6,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <span style={{
                        width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                        background: wh.active ? '#22c55e' : '#ef4444',
                        display: 'inline-block',
                      }} />
                      <span style={{ fontWeight: 600, fontSize: 13, color: '#e2e8f0' }}>{wh.name}</span>
                      <span style={{ fontSize: 10, color: '#4b5563', fontWeight: 500 }}>
                        {wh.fire_count} fires
                      </span>
                    </div>
                    <code style={{ fontSize: 11, color: '#6366f1', wordBreak: 'break-all' }}>{wh.url}</code>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 8 }}>
                      {wh.events.map(ev => (
                        <span key={ev} style={{
                          fontSize: 10, fontWeight: 600, padding: '1px 7px',
                          borderRadius: 10, background: 'rgba(99,102,241,0.12)', color: '#a5b4fc',
                        }}>{ev}</span>
                      ))}
                    </div>
                    <div style={{ marginTop: 6, fontSize: 10, color: '#374151' }}>
                      Created {fmt(wh.created_at)} · Last fired: {fmt(wh.last_fired)}
                    </div>
                    {testResult[wh.id] && (
                      <div style={{ marginTop: 6, fontSize: 11, color: '#22c55e' }}>
                        {testResult[wh.id]}
                      </div>
                    )}
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6, flexShrink: 0 }}>
                    <Btn variant="secondary"
                      onClick={() => testWebhook(wh.id)}
                      disabled={testing === wh.id}
                      style={{ fontSize: 11, padding: '5px 10px' }}>
                      {testing === wh.id ? '…' : '⚡ Test'}
                    </Btn>
                    <Btn variant="secondary"
                      onClick={() => toggleWebhook(wh.id)}
                      style={{ fontSize: 11, padding: '5px 10px' }}>
                      {wh.active ? '⏸ Pause' : '▶ Enable'}
                    </Btn>
                    <Btn variant="secondary"
                      onClick={() => deleteWebhook(wh.id)}
                      style={{ fontSize: 11, padding: '5px 10px', color: '#ef4444' }}>
                      🗑 Delete
                    </Btn>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Event reference */}
      <Card>
        <SectionHead title="Event Reference" sub="All events your webhook can subscribe to" />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 8 }}>
          {Object.entries(EVENT_DESCRIPTIONS).map(([ev, desc]) => (
            <div key={ev} style={{
              background: '#0f1117', borderRadius: 8, padding: '10px 12px',
              display: 'flex', flexDirection: 'column', gap: 4,
            }}>
              <code style={{ fontSize: 11, color: '#a5b4fc' }}>{ev}</code>
              <span style={{ fontSize: 11, color: '#6b7280' }}>{desc}</span>
            </div>
          ))}
        </div>
      </Card>

      {/* Payload example */}
      <Card>
        <SectionHead title="Payload Format" sub="JSON structure sent to your endpoint on every event" />
        <pre style={{
          background: '#0f1117', borderRadius: 8, padding: '14px 16px',
          color: '#a5b4fc', fontSize: 11, lineHeight: 1.8, overflowX: 'auto',
          margin: 0,
        }}>
{`{
  "event":      "agent.response",
  "timestamp":  "2026-05-29T12:00:00Z",
  "webhook_id": "abc-123-def",
  "payload": {
    "session_id":  "sess-xyz",
    "query":       "Summarise Q2 report",
    "response":    "Q2 revenue grew by...",
    "latency_ms":  1240,
    "model":       "gpt-4o",
    "cost_usd":    0.00312
  }
}

// HMAC signature (if secret configured):
// Header: X-Webhook-Signature: sha256=<hex>`}
        </pre>
      </Card>
    </PageShell>
  )
}
