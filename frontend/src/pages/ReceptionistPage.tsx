// frontend/src/pages/ReceptionistPage.tsx — Feature 13
import { useState } from 'react'
import { PageShell, Card, Btn, TwoCol, SectionHead, Badge } from '../components/ui'
import { receptionistQuery } from '../lib/api'

export default function ReceptionistPage() {
  const [message, setMessage] = useState('I would like to schedule an appointment with Dr. Sharma for next Monday')
  const [sessionId, setSessionId] = useState('demo-session-001')
  const [chat, setChat] = useState<Array<{role:string;content:string}>>([])
  const [sending, setSending] = useState(false)

  const send = async () => {
    if (!message.trim() || sending) return
    const userMsg = message
    setChat(c => [...c, { role: 'user', content: userMsg }])
    setMessage('')
    setSending(true)
    try {
      const res = await receptionistQuery(userMsg, sessionId) as any
      if (res?.response) setChat(c => [...c, { role: 'assistant', content: res.response }])
    } catch (e: any) {
      setChat(c => [...c, { role: 'assistant', content: `⚠️ ${e.message || 'Request failed'}` }])
    } finally {
      setSending(false)
    }
  }

  const WIDGET_CODE = `<!-- AI Receptionist Widget -->
<script src="http://localhost:8000/api/verticals/receptionist/widget.js"
  data-session-id="${sessionId}"
  data-theme="dark">
</script>`

  return (
    <PageShell icon="☎️" title="AI Receptionist Agent" subtitle="Feature 13 — Twilio Voice + WhatsApp + Embeddable JS Widget">
      <TwoCol>
        <div>
          <Card style={{ marginBottom: 16 }}>
            <SectionHead title="Chat Simulation" sub="Test the receptionist flow" />
            <div style={{ background: '#0f1117', borderRadius: 8, padding: 12, height: 300, overflowY: 'auto', marginBottom: 12 }}>
              {chat.length === 0 && (
                <div style={{ color: '#6b7280', fontSize: 12, textAlign: 'center', marginTop: 40 }}>
                  Start a conversation with the AI receptionist...
                </div>
              )}
              {chat.map((m, i) => (
                <div key={i} style={{
                  display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start',
                  marginBottom: 8,
                }}>
                  <div style={{
                    maxWidth: '80%', padding: '8px 12px', borderRadius: 10,
                    background: m.role === 'user' ? '#6366f1' : '#1e2535',
                    color: '#e2e8f0', fontSize: 13, lineHeight: 1.4,
                  }}>{m.content}</div>
                </div>
              ))}
              {sending && <div style={{ color: '#6b7280', fontSize: 12, textAlign: 'center' }}>⏳ Receptionist typing...</div>}
            </div>

            <div style={{ display: 'flex', gap: 8 }}>
              {['I want to book a meeting','What are your business hours?','Can I speak to the manager?','I need help with my order'].map(q => (
                <button key={q} onClick={() => setMessage(q)} style={{
                  padding: '4px 8px', borderRadius: 6, background: '#1e2535', border: '1px solid #374151',
                  color: '#9ca3af', fontSize: 10, cursor: 'pointer', flexShrink: 0,
                }}>{q.slice(0, 20)}...</button>
              ))}
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
              <input value={message} onChange={e => setMessage(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && send()}
                placeholder="Type a message..." style={{
                  flex: 1, background: '#0f1117', border: '1px solid #1e2535', borderRadius: 8,
                  padding: '9px 12px', color: '#e2e8f0', fontSize: 13, outline: 'none',
                }} />
              <Btn onClick={send} loading={sending}>Send</Btn>
            </div>
          </Card>
        </div>

        <div>
          <Card style={{ marginBottom: 16 }}>
            <SectionHead title="Capabilities" />
            {[
              { icon: '📞', label: 'Twilio Voice', desc: 'Inbound call TwiML — IVR + voicemail' },
              { icon: '💬', label: 'WhatsApp Business', desc: 'Twilio WhatsApp API integration' },
              { icon: '📅', label: 'Appointment Booking', desc: 'Calendar integration via Calendly' },
              { icon: '🎙️', label: 'Voicemail Transcription', desc: 'Whisper STT for missed calls' },
              { icon: '🌐', label: 'Embeddable Widget', desc: 'Copy-paste JS for any website' },
            ].map(c => (
              <div key={c.label} style={{ display: 'flex', gap: 10, marginBottom: 10, alignItems: 'flex-start' }}>
                <span style={{ fontSize: 18, flexShrink: 0 }}>{c.icon}</span>
                <div>
                  <div style={{ color: '#e2e8f0', fontSize: 12, fontWeight: 600 }}>{c.label}</div>
                  <div style={{ color: '#6b7280', fontSize: 11 }}>{c.desc}</div>
                </div>
              </div>
            ))}
          </Card>

          <Card>
            <SectionHead title="Website Widget Embed" sub="Copy-paste snippet" />
            <pre style={{
              background: '#0f1117', borderRadius: 8, padding: 14,
              color: '#86efac', fontSize: 11, overflowX: 'auto', lineHeight: 1.6,
              fontFamily: 'Monaco, Consolas, monospace', whiteSpace: 'pre-wrap',
            }}>{WIDGET_CODE}</pre>
            <div style={{ marginTop: 8 }}>
              <Badge text="Twilio Voice" color="blue" />
              {' '}
              <Badge text="WhatsApp" color="green" />
              {' '}
              <Badge text="Embeddable" color="purple" />
            </div>
          </Card>
        </div>
      </TwoCol>
    </PageShell>
  )
}
