// frontend/src/pages/ReceptionistPage.tsx — Feature 13
import { useState } from 'react'
import { PageShell, Card, Btn, Input, Select, ResultBox, Tabs, TwoCol, useApi, SectionHead, Badge } from '../components/ui'
import { receptionistQuery, rcptEnhance } from '../lib/api'

export default function ReceptionistPage() {
  const [tab, setTab] = useState('chat')

  // Chat tab
  const [message, setMessage]     = useState('I would like to schedule an appointment with Dr. Sharma for next Monday')
  const [sessionId, setSessionId] = useState('demo-session-001')
  const [chat, setChat]           = useState<Array<{role:string;content:string}>>([])
  const [sending, setSending]     = useState(false)

  // FAQ Builder tab
  const [faqBusiness, setFaqBiz]      = useState('Tech Innovations India Pvt Ltd')
  const [faqService, setFaqService]   = useState('B2B SaaS AI Platform')
  const [faqQuestions, setFaqQs]      = useState('How do I get started?\nWhat integrations do you support?\nWhat is your refund policy?\nHow do I reset my password?\nWhat are your support hours?\nDo you offer a free trial?\nHow is my data protected?\nCan I export my data?')
  const faqApi = useApi()

  // SLA Policy tab
  const [slaCompany, setSlaCompany]   = useState('Tech Innovations India Pvt Ltd')
  const [slaService, setSlaService]   = useState('B2B SaaS platform')
  const [slaTiers, setSlaTiers]       = useState('Free (community support), Pro (business hours SLA), Enterprise (24×7 dedicated CSM)')
  const slaApi = useApi()

  // Escalation Matrix tab
  const [escCompany, setEscCompany]   = useState('Tech Innovations India Pvt Ltd')
  const [escTeamSize, setEscTeamSize] = useState('15')
  const [escLevels, setEscLevels]     = useState('L1 Support (first response, common issues)\nL2 Technical (complex bugs, integrations)\nL3 Engineering (production incidents, data issues)\nL4 Management (SLA breaches, enterprise escalations)')
  const escApi = useApi()

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
    } finally { setSending(false) }
  }

  const API_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api').replace('/api', '')
  const WIDGET_CODE = `<!-- AI Receptionist Widget -->
<script src="${API_BASE}/api/verticals/receptionist/widget.js"
  data-session-id="${sessionId}"
  data-theme="dark">
</script>`

  return (
    <PageShell icon="☎️" title="AI Receptionist Agent" subtitle="Feature 13 — Chat, FAQ Builder, SLA Policy, Escalation Matrix">
      <Tabs
        tabs={[
          { id: 'chat',       label: 'Chat Simulation', icon: '💬' },
          { id: 'faq',        label: 'FAQ Builder',     icon: '❓' },
          { id: 'sla',        label: 'SLA Policy',      icon: '📋' },
          { id: 'escalation', label: 'Escalation Matrix', icon: '🔺' },
        ]}
        active={tab} onChange={setTab}
      />

      {/* ── Chat ── */}
      {tab === 'chat' && (
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
                  <div key={i} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start', marginBottom: 8 }}>
                    <div style={{ maxWidth: '80%', padding: '8px 12px', borderRadius: 10, background: m.role === 'user' ? '#10b981' : '#1e2535', color: '#e2e8f0', fontSize: 13, lineHeight: 1.4 }}>
                      {m.content}
                    </div>
                  </div>
                ))}
                {sending && <div style={{ color: '#6b7280', fontSize: 12, textAlign: 'center' }}>⏳ Receptionist typing...</div>}
              </div>
              <div style={{ display: 'flex', gap: 8, marginBottom: 10, flexWrap: 'wrap' }}>
                {['I want to book a meeting','What are your business hours?','Can I speak to the manager?','I need help with my order'].map(q => (
                  <button key={q} onClick={() => setMessage(q)} style={{ padding: '4px 8px', borderRadius: 6, background: '#1e2535', border: '1px solid #374151', color: '#9ca3af', fontSize: 10, cursor: 'pointer' }}>
                    {q.slice(0, 20)}...
                  </button>
                ))}
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <input value={message} onChange={e => setMessage(e.target.value)} onKeyDown={e => e.key === 'Enter' && send()}
                  placeholder="Type a message..." style={{ flex: 1, background: '#0f1117', border: '1px solid #1e2535', borderRadius: 8, padding: '9px 12px', color: '#e2e8f0', fontSize: 13, outline: 'none' }} />
                <Btn onClick={send} loading={sending}>Send</Btn>
              </div>
            </Card>
          </div>
          <div>
            <Card style={{ marginBottom: 16 }}>
              <SectionHead title="Capabilities" />
              {[
                { icon: '📞', label: 'Twilio Voice',          desc: 'Inbound call TwiML — IVR + voicemail' },
                { icon: '💬', label: 'WhatsApp Business',     desc: 'Twilio WhatsApp API integration' },
                { icon: '📅', label: 'Appointment Booking',   desc: 'Calendar integration via Calendly' },
                { icon: '🎙️', label: 'Voicemail Transcription', desc: 'Whisper STT for missed calls' },
                { icon: '🌐', label: 'Embeddable Widget',     desc: 'Copy-paste JS for any website' },
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
              <pre style={{ background: '#0f1117', borderRadius: 8, padding: 14, color: '#86efac', fontSize: 11, overflowX: 'auto', lineHeight: 1.6, fontFamily: 'Monaco, Consolas, monospace', whiteSpace: 'pre-wrap' }}>{WIDGET_CODE}</pre>
              <div style={{ marginTop: 8 }}>
                <Badge text="Twilio Voice" color="blue" />{' '}
                <Badge text="WhatsApp" color="green" />{' '}
                <Badge text="Embeddable" color="purple" />
              </div>
            </Card>
          </div>
        </TwoCol>
      )}

      {/* ── FAQ Builder ── */}
      {tab === 'faq' && (
        <TwoCol>
          <Card>
            <SectionHead title="FAQ Document Builder" sub="20 categorized FAQs for your support portal, chatbot, or help center" />
            <Input label="Business Name"    value={faqBusiness}  onChange={setFaqBiz} />
            <Input label="Service / Product" value={faqService}  onChange={setFaqService} />
            <Input label="Common Customer Questions (one per line)" value={faqQuestions} onChange={setFaqQs} rows={8} />
            <div style={{ padding: 10, background: 'rgba(16,185,129,0.08)', borderRadius: 8, marginBottom: 14 }}>
              <div style={{ fontSize: 11, color: '#5eead4', marginBottom: 4 }}>❓ FAQ categories</div>
              <div style={{ fontSize: 11, color: '#6b7280' }}>Getting Started • Account & Billing • Features & Usage • Troubleshooting • Integrations • Security & Privacy • Policies</div>
            </div>
            <Btn
              onClick={() => faqApi.call(() => rcptEnhance('faq_builder', {
                business_name:    faqBusiness,
                service_type:     faqService,
                common_questions: faqQuestions,
              }))}
              loading={faqApi.loading}
            >
              ❓ Generate FAQ Document
            </Btn>
          </Card>
          <ResultBox data={faqApi.data ? { faq: (faqApi.data as any).result } : null} loading={faqApi.loading} error={faqApi.error} title="FAQ Document" />
        </TwoCol>
      )}

      {/* ── SLA Policy ── */}
      {tab === 'sla' && (
        <TwoCol>
          <Card>
            <SectionHead title="SLA Policy Generator" sub="Service Level Agreement with response times, uptime SLAs, credit policy" />
            <Input label="Company Name"    value={slaCompany}  onChange={setSlaCompany} />
            <Input label="Service Type"    value={slaService}  onChange={setSlaService} />
            <Input label="Support Tiers (one per line)" value={slaTiers} onChange={setSlaTiers} rows={3} />
            <div style={{ padding: 10, background: 'rgba(16,185,129,0.08)', borderRadius: 8, marginBottom: 14 }}>
              <div style={{ fontSize: 11, color: '#5eead4', marginBottom: 4 }}>📋 SLA document includes</div>
              <div style={{ fontSize: 11, color: '#6b7280' }}>Response times by severity × tier • Resolution targets • Uptime guarantee (99.9–99.99%) • Maintenance windows • Credit policy • Support channels • Business hours definition</div>
            </div>
            <Btn
              onClick={() => slaApi.call(() => rcptEnhance('sla_policy', {
                company:       slaCompany,
                service_type:  slaService,
                support_tiers: slaTiers,
              }))}
              loading={slaApi.loading}
            >
              📋 Generate SLA Policy
            </Btn>
          </Card>
          <ResultBox data={slaApi.data ? { policy: (slaApi.data as any).result } : null} loading={slaApi.loading} error={slaApi.error} title="SLA Policy" />
        </TwoCol>
      )}

      {/* ── Escalation Matrix ── */}
      {tab === 'escalation' && (
        <TwoCol>
          <Card>
            <SectionHead title="Escalation Matrix Designer" sub="Decision tree, RACI matrix, escalation triggers, communication templates" />
            <Input label="Company Name"     value={escCompany}   onChange={setEscCompany} />
            <Input label="Support Team Size" value={escTeamSize} onChange={setEscTeamSize} />
            <Input label="Escalation Levels (one per line)" value={escLevels} onChange={setEscLevels} rows={5} />
            <div style={{ padding: 10, background: 'rgba(16,185,129,0.08)', borderRadius: 8, marginBottom: 14 }}>
              <div style={{ fontSize: 11, color: '#5eead4', marginBottom: 4 }}>🔺 Matrix includes</div>
              <div style={{ fontSize: 11, color: '#6b7280' }}>Decision tree • RACI per level • Escalation triggers by issue type • Communication templates • VIP handling • SLA clock management</div>
            </div>
            <Btn
              onClick={() => escApi.call(() => rcptEnhance('escalation_matrix', {
                company:           escCompany,
                team_size:         escTeamSize,
                escalation_levels: escLevels,
              }))}
              loading={escApi.loading}
            >
              🔺 Design Escalation Matrix
            </Btn>
          </Card>
          <ResultBox data={escApi.data ? { matrix: (escApi.data as any).result } : null} loading={escApi.loading} error={escApi.error} title="Escalation Matrix" />
        </TwoCol>
      )}
    </PageShell>
  )
}
