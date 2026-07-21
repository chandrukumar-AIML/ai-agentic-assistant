// frontend/src/pages/CustomerSupportPage.tsx - AI Customer Support Agent
import { useState } from 'react'
import { csAction } from '../lib/api'
import { PageShell, Card, Btn, Input, Select, Tabs, SectionHead } from '../components/ui'

type Lang = 'en' | 'ta' | 'hi'

function Badge({ label, color }: { label: string; color: string }) {
  return (
    <span style={{
      fontSize: 11, padding: '2px 8px', borderRadius: 20, fontWeight: 600,
      background: color + '22', color,
    }}>{label}</span>
  )
}

function Empty({ text }: { text: string }) {
  return (
    <div style={{
      background: '#0f1117', border: '1px solid #1e2535', borderRadius: 8,
      padding: '32px 20px', textAlign: 'center', color: '#4b5563', fontSize: 13,
    }}>{text}</div>
  )
}

function Row({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>
      {children}
    </div>
  )
}

const LANG_OPTIONS = [
  { value: 'en', label: 'English' },
  { value: 'ta', label: 'Tamil' },
  { value: 'hi', label: 'Hindi' },
]

const TABS = [
  { id: 'faq',        label: 'FAQ Bot' },
  { id: 'whatsapp',   label: 'WhatsApp Send' },
  { id: 'sentiment',  label: 'Sentiment' },
  { id: 'complaint',  label: 'Complaint Handler' },
  { id: 'lead',       label: 'Lead Qualifier' },
  { id: 'ticket',     label: 'Ticket Summary' },
  { id: 'template',   label: 'Response Templates' },
  { id: 'kb',         label: 'Knowledge Base' },
  { id: 'report',     label: 'Weekly Report' },
  { id: 'canned',     label: 'Canned Responses' },
  { id: 'sla',        label: 'SLA Tracker' },
  { id: 'csat',       label: 'CSAT Survey' },
  { id: 'escalation', label: 'Escalation Manager' },
  { id: 'churn',      label: 'Churn Risk' },
  { id: 'onboarding', label: 'Onboarding Planner' },
  { id: 'categorizer',label: 'Ticket Categorizer' },
  { id: 'rulebook',   label: 'Escalation Rulebook' },
  { id: 'health',     label: 'Customer Health Score' },
  { id: 'winback',    label: 'Win-back Sequence' },
  { id: 'scorecard',  label: 'Agent Scorecard' },
]

const WA_TYPES = [
  { value: 'welcome',           label: 'Welcome Message' },
  { value: 'follow_up',         label: 'Follow-up' },
  { value: 'payment_reminder',  label: 'Payment Reminder' },
  { value: 'delivery_update',   label: 'Delivery Update' },
  { value: 'feedback_request',  label: 'Feedback Request' },
  { value: 'apology',           label: 'Apology' },
  { value: 'offer',             label: 'Promotional Offer' },
  { value: 'reactivation',      label: 'Re-engagement' },
]

const COMPLAINT_CATEGORIES = [
  { value: 'delivery',  label: 'Delivery Issue' },
  { value: 'billing',   label: 'Billing / Payment' },
  { value: 'product',   label: 'Product Quality' },
  { value: 'technical', label: 'Technical Problem' },
  { value: 'refund',    label: 'Refund Request' },
  { value: 'fraud',     label: 'Fraud / Scam Concern' },
  { value: 'general',   label: 'General Complaint' },
]

const TONE_OPTIONS = [
  { value: 'friendly',   label: 'Friendly' },
  { value: 'formal',     label: 'Formal' },
  { value: 'empathetic', label: 'Empathetic' },
  { value: 'direct',     label: 'Direct' },
]

function TA({ rows = 4, value, onChange, placeholder }: { rows?: number; value: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <textarea
      rows={rows}
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      style={{
        width: '100%', background: '#0f1117', border: '1px solid #1e2535',
        borderRadius: 8, color: '#e2e8f0', padding: '10px 12px',
        fontSize: 13, resize: 'vertical', boxSizing: 'border-box',
      }}
    />
  )
}

function FaqTab({ lang }: { lang: Lang }) {
  const [query, setQuery]     = useState('')
  const [bizName, setBizName] = useState('')
  const [bizType, setBizType] = useState('')
  const [faqCtx, setFaqCtx]   = useState('')
  const [res, setRes]         = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [err, setErr]         = useState('')

  const run = async () => {
    if (!query.trim()) return
    setLoading(true); setErr(''); setRes(null)
    try {
      setRes(await csAction('faq_bot', {
        query, business_name: bizName || 'Our Business',
        business_type: bizType || 'General', faq_context: faqCtx,
      }, lang))
    } catch (e: any) { setErr(e.message) }
    setLoading(false)
  }

  return (
    <Row>
      <Card>
        <SectionHead title="FAQ Bot" sub="Answer customer questions using your FAQ context" />
        <Input label="Business Name" value={bizName} onChange={setBizName} placeholder="e.g. Ravi Textiles" />
        <Input label="Business Type" value={bizType} onChange={setBizType} placeholder="e.g. Online Fashion Store" />
        <div style={{ marginTop: 14 }}>
          <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 4 }}>FAQ / Knowledge Context</div>
          <TA value={faqCtx} onChange={setFaqCtx} placeholder="Q: What are your timings? A: 9am-6pm Mon-Sat" rows={5} />
        </div>
        <div style={{ marginTop: 14 }}>
          <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 4 }}>Customer Question *</div>
          <TA value={query} onChange={setQuery} placeholder="What is your return policy?" rows={3} />
        </div>
        <Btn onClick={run} loading={loading} style={{ marginTop: 14, width: '100%' }}>Get Answer</Btn>
        {err && <div style={{ color: '#ef4444', fontSize: 13, marginTop: 8 }}>{err}</div>}
      </Card>
      <Card>
        <SectionHead title="AI Response" />
        {res ? (
          <div>
            {res.needs_escalation && (
              <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid #ef4444', borderRadius: 8, padding: '10px 14px', marginBottom: 14 }}>
                <span style={{ color: '#ef4444', fontWeight: 600 }}>Escalation Recommended</span>
                <div style={{ color: '#fca5a5', fontSize: 12, marginTop: 4 }}>{res.escalation_reason}</div>
              </div>
            )}
            <div style={{ background: '#0f1117', border: '1px solid #1e2535', borderRadius: 8, padding: '14px 16px', color: '#e2e8f0', fontSize: 14, lineHeight: 1.7, whiteSpace: 'pre-wrap', marginBottom: 12 }}>
              {res.answer}
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <Badge label={'Confidence: ' + res.confidence} color={res.confidence === 'high' ? '#10b981' : '#f59e0b'} />
              <Badge label={'Lang: ' + (res.language || '').toUpperCase()} color="#3b82f6" />
            </div>
          </div>
        ) : <Empty text="FAQ answer will appear here..." />}
      </Card>
    </Row>
  )
}

function WhatsAppTab({ lang }: { lang: Lang }) {
  const [msgType, setMsgType]   = useState('follow_up')
  const [custName, setCustName] = useState('')
  const [bizName, setBizName]   = useState('')
  const [context, setContext]   = useState('')
  const [res, setRes]           = useState<any>(null)
  const [loading, setLoading]   = useState(false)
  const [err, setErr]           = useState('')

  // Direct send
  const [toNumber, setToNumber] = useState('')
  const [sendMsg, setSendMsg]   = useState('')
  const [sending, setSending]   = useState(false)
  const [sendRes, setSendRes]   = useState<any>(null)
  const [sendErr, setSendErr]   = useState('')

  const draft = async () => {
    setLoading(true); setErr(''); setRes(null)
    try {
      const r = await csAction('draft_whatsapp', {
        message_type: msgType, customer_name: custName || 'Customer',
        business_name: bizName || 'Our Business', context,
      }, lang)
      setRes(r)
      if (r.message) setSendMsg(r.message)
    } catch (e: any) { setErr(e.message) }
    setLoading(false)
  }

  const send = async () => {
    setSending(true); setSendErr(''); setSendRes(null)
    try {
      setSendRes(await csAction('send_whatsapp', { to_number: toNumber, message: sendMsg }, lang))
    } catch (e: any) { setSendErr(e.message) }
    setSending(false)
  }

  return (
    <Row>
      <Card>
        <SectionHead title="WhatsApp Draft + Send" sub="AI drafts the message — you review and send directly" />
        <Select label="Message Type" value={msgType} onChange={setMsgType} options={WA_TYPES} />
        <Input label="Customer Name" value={custName} onChange={setCustName} placeholder="Priya" />
        <Input label="Business Name" value={bizName} onChange={setBizName} placeholder="Sri Lakshmi Stores" />
        <div style={{ marginTop: 14 }}>
          <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 4 }}>Context / Details</div>
          <TA value={context} onChange={setContext} placeholder="e.g. Order delivered yesterday, asking for review..." rows={3} />
        </div>
        <Btn onClick={draft} loading={loading} style={{ marginTop: 14, width: '100%' }}>Draft Message</Btn>
        {err && <div style={{ color: '#ef4444', fontSize: 13, marginTop: 8 }}>{err}</div>}

        {/* Send panel — shown after draft */}
        {res && (
          <div style={{ marginTop: 20, paddingTop: 16, borderTop: '1px solid #1e2535' }}>
            <SectionHead title="Send via WhatsApp" sub="Requires TWILIO_ACCOUNT_SID in backend env" />
            <Input label="To Number" value={toNumber} onChange={setToNumber} placeholder="+919876543210" />
            <div style={{ marginTop: 10 }}>
              <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 4 }}>Message (editable)</div>
              <TA value={sendMsg} onChange={setSendMsg} rows={4} />
            </div>
            <div style={{ padding: '8px 12px', background: 'rgba(37,211,102,0.06)', border: '1px solid #25d36633', borderRadius: 6, fontSize: 11, color: '#4ade80', marginBottom: 10 }}>
              Mock mode: send works without Twilio — set TWILIO_ACCOUNT_SID to go live
            </div>
            <Btn onClick={send} loading={sending} disabled={!toNumber || !sendMsg} style={{ width: '100%' }}>
              Send WhatsApp
            </Btn>
            {sendErr && <div style={{ color: '#ef4444', fontSize: 12, marginTop: 8 }}>{sendErr}</div>}
            {sendRes && (
              <div style={{
                marginTop: 10, padding: '10px 14px', borderRadius: 8,
                background: sendRes.success ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
                border: `1px solid ${sendRes.success ? '#10b98144' : '#ef444444'}`,
              }}>
                <div style={{ color: sendRes.success ? '#10b981' : '#ef4444', fontWeight: 600, fontSize: 13 }}>
                  {sendRes.success ? (sendRes.mock ? 'Sent (Mock Mode)' : 'Delivered!') : 'Send Failed'}
                </div>
                {sendRes.sid && <div style={{ color: '#6b7280', fontSize: 11, marginTop: 4 }}>SID: {sendRes.sid}</div>}
                {sendRes.error && <div style={{ color: '#fca5a5', fontSize: 11, marginTop: 4 }}>{sendRes.error}</div>}
              </div>
            )}
          </div>
        )}
      </Card>

      <Card>
        <SectionHead title="Drafted Message" />
        {res ? (
          <div>
            <div style={{ background: '#075e54', borderRadius: 12, padding: '16px 18px', color: '#ecfdf5', fontSize: 14, lineHeight: 1.7, whiteSpace: 'pre-wrap', marginBottom: 12, fontFamily: 'system-ui' }}>
              {res.message}
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <Badge label={(res.word_count || '') + ' words'} color="#6b7280" />
              <Badge label={res.channel || 'WhatsApp'} color="#25d366" />
            </div>
          </div>
        ) : <Empty text="Drafted message will appear here. Then send directly below." />}
      </Card>
    </Row>
  )
}

function SentimentTab({ lang }: { lang: Lang }) {
  const [text, setText]         = useState('')
  const [custName, setCustName] = useState('')
  const [res, setRes]           = useState<any>(null)
  const [loading, setLoading]   = useState(false)
  const [err, setErr]           = useState('')

  const run = async () => {
    if (!text.trim()) return
    setLoading(true); setErr(''); setRes(null)
    try {
      setRes(await csAction('analyze_sentiment', { text, customer_name: custName || 'Customer' }, lang))
    } catch (e: any) { setErr(e.message) }
    setLoading(false)
  }

  const LABELS: Record<string, string> = { positive: 'Happy', neutral: 'Neutral', negative: 'Frustrated', critical: 'Critical - Escalate' }

  return (
    <Row>
      <Card>
        <SectionHead title="Sentiment Analyzer" sub="Detect mood, urgency, and whether to escalate" />
        <Input label="Customer Name" value={custName} onChange={setCustName} placeholder="Ramesh" />
        <div style={{ marginTop: 14 }}>
          <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 4 }}>Customer Message *</div>
          <TA value={text} onChange={setText} placeholder="I've been waiting 2 weeks and nobody responds! This is ridiculous..." rows={6} />
        </div>
        <Btn onClick={run} loading={loading} style={{ marginTop: 14, width: '100%' }}>Analyze Sentiment</Btn>
        {err && <div style={{ color: '#ef4444', fontSize: 13, marginTop: 8 }}>{err}</div>}
      </Card>
      <Card>
        <SectionHead title="Sentiment Analysis" />
        {res ? (
          <div>
            <div style={{ textAlign: 'center', padding: '20px 0 16px', borderBottom: '1px solid #1e2535', marginBottom: 16 }}>
              <div style={{ fontSize: 22, fontWeight: 700, color: res.color || '#e2e8f0' }}>
                {LABELS[res.sentiment] || res.sentiment}
              </div>
              <div style={{ color: '#6b7280', fontSize: 13 }}>Score: {res.score}/100</div>
            </div>
            {res.needs_human && (
              <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid #ef4444', borderRadius: 8, padding: '10px 14px', marginBottom: 12, color: '#ef4444', fontWeight: 600, fontSize: 13 }}>
                Requires Human Agent
              </div>
            )}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 12 }}>
              {[{ label: 'Urgency', value: res.urgency }, { label: 'Tone Suggestion', value: res.suggested_tone }].map(item => (
                <div key={item.label} style={{ background: '#0f1117', borderRadius: 8, padding: '10px 12px' }}>
                  <div style={{ color: '#6b7280', fontSize: 11 }}>{item.label}</div>
                  <div style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 600, textTransform: 'capitalize' }}>{item.value}</div>
                </div>
              ))}
            </div>
            {res.key_issues?.length > 0 && (
              <div style={{ marginBottom: 12 }}>
                <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 6 }}>Key Issues</div>
                {res.key_issues.map((issue: string, i: number) => (
                  <div key={i} style={{ color: '#e2e8f0', fontSize: 13, padding: '3px 0' }}>- {issue}</div>
                ))}
              </div>
            )}
            {res.summary && (
              <div style={{ background: '#0f1117', borderRadius: 8, padding: '10px 12px', color: '#9ca3af', fontSize: 13, lineHeight: 1.6 }}>{res.summary}</div>
            )}
          </div>
        ) : <Empty text="Sentiment results will appear here..." />}
      </Card>
    </Row>
  )
}

function ComplaintTab({ lang }: { lang: Lang }) {
  const [complaint, setComplaint] = useState('')
  const [custName, setCustName]   = useState('')
  const [orderId, setOrderId]     = useState('')
  const [bizName, setBizName]     = useState('')
  const [category, setCategory]   = useState('general')
  const [res, setRes]             = useState<any>(null)
  const [loading, setLoading]     = useState(false)
  const [err, setErr]             = useState('')

  const run = async () => {
    if (!complaint.trim()) return
    setLoading(true); setErr(''); setRes(null)
    try {
      setRes(await csAction('handle_complaint', {
        complaint, customer_name: custName || 'Customer',
        order_id: orderId, business_name: bizName || 'Our Business', category,
      }, lang))
    } catch (e: any) { setErr(e.message) }
    setLoading(false)
  }

  return (
    <Row>
      <Card>
        <SectionHead title="Complaint Handler" sub="AI-generated resolution for customer complaints" />
        <Input label="Customer Name" value={custName} onChange={setCustName} placeholder="Ananya" />
        <Input label="Business Name" value={bizName} onChange={setBizName} placeholder="Tech Solutions Pvt Ltd" />
        <Input label="Order / Reference ID" value={orderId} onChange={setOrderId} placeholder="ORD-2025-001" />
        <Select label="Category" value={category} onChange={setCategory} options={COMPLAINT_CATEGORIES} />
        <div style={{ marginTop: 14 }}>
          <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 4 }}>Customer Complaint *</div>
          <TA value={complaint} onChange={setComplaint} placeholder="Describe the complaint in detail..." rows={5} />
        </div>
        <Btn onClick={run} loading={loading} style={{ marginTop: 14, width: '100%' }}>Handle Complaint</Btn>
        {err && <div style={{ color: '#ef4444', fontSize: 13, marginTop: 8 }}>{err}</div>}
      </Card>
      <Card>
        <SectionHead title="Resolution Plan" />
        {res ? (
          <div>
            {res.escalate && (
              <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid #ef4444', borderRadius: 8, padding: '10px 14px', marginBottom: 14, color: '#ef4444', fontWeight: 600 }}>
                Escalation Required - {res.escalate_reason}
              </div>
            )}
            <div style={{ marginBottom: 14 }}>
              <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 6 }}>Acknowledgment</div>
              <div style={{ background: '#0f1117', borderRadius: 8, padding: '12px 14px', color: '#e2e8f0', fontSize: 13, lineHeight: 1.7 }}>{res.acknowledgment}</div>
            </div>
            <div style={{ marginBottom: 14 }}>
              <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 6 }}>Resolution Steps</div>
              {(res.resolution_steps || []).map((step: string, i: number) => (
                <div key={i} style={{ display: 'flex', gap: 10, alignItems: 'flex-start', padding: '6px 0', borderBottom: '1px solid #1e2535' }}>
                  <span style={{ minWidth: 22, height: 22, borderRadius: '50%', background: '#10b981', color: '#fff', fontSize: 11, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{i + 1}</span>
                  <span style={{ color: '#e2e8f0', fontSize: 13, lineHeight: 1.5 }}>{step}</span>
                </div>
              ))}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              <div style={{ background: '#0f1117', borderRadius: 8, padding: '10px 12px' }}>
                <div style={{ color: '#6b7280', fontSize: 11 }}>Timeline</div>
                <div style={{ color: '#f59e0b', fontSize: 13, fontWeight: 600 }}>{res.timeline}</div>
              </div>
              <div style={{ background: '#0f1117', borderRadius: 8, padding: '10px 12px' }}>
                <div style={{ color: '#6b7280', fontSize: 11 }}>Category</div>
                <div style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 600, textTransform: 'capitalize' }}>{res.category}</div>
              </div>
            </div>
            {res.reassurance && (
              <div style={{ marginTop: 12, background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: 8, padding: '10px 14px', color: '#5eead4', fontSize: 13, lineHeight: 1.6 }}>
                {res.reassurance}
              </div>
            )}
          </div>
        ) : <Empty text="Resolution plan will appear here..." />}
      </Card>
    </Row>
  )
}

function LeadTab({ lang }: { lang: Lang }) {
  const [custName, setCustName] = useState('')
  const [bizType, setBizType]   = useState('')
  const [budget, setBudget]     = useState('')
  const [requirement, setReq]   = useState('')
  const [timeline, setTimeline] = useState('')
  const [channel, setChannel]   = useState('')
  const [res, setRes]           = useState<any>(null)
  const [loading, setLoading]   = useState(false)
  const [err, setErr]           = useState('')

  const run = async () => {
    setLoading(true); setErr(''); setRes(null)
    try {
      setRes(await csAction('qualify_lead', {
        customer_name: custName || 'Lead', business_type: bizType || 'General',
        responses: { budget, requirement, timeline, channel },
      }, lang))
    } catch (e: any) { setErr(e.message) }
    setLoading(false)
  }

  const QUALITY_COLORS: Record<string, string> = { Hot: '#ef4444', Warm: '#f59e0b', Cold: '#3b82f6' }

  return (
    <Row>
      <Card>
        <SectionHead title="Lead Qualifier" sub="Score and qualify inbound leads with AI" />
        <Input label="Lead Name" value={custName} onChange={setCustName} placeholder="Karthik Kumar" />
        <Input label="Your Business Type" value={bizType} onChange={setBizType} placeholder="e.g. SaaS, Textile, Catering" />
        <Input label="Budget Mentioned" value={budget} onChange={setBudget} placeholder="e.g. Rs.5000/month, not sure yet" />
        <div style={{ marginTop: 14 }}>
          <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 4 }}>Requirement</div>
          <TA value={requirement} onChange={setReq} placeholder="What does the lead need?" rows={3} />
        </div>
        <Input label="Decision Timeline" value={timeline} onChange={setTimeline} placeholder="e.g. ASAP, next month, just exploring" />
        <Input label="How They Found You" value={channel} onChange={setChannel} placeholder="e.g. WhatsApp, Instagram, Reference" />
        <Btn onClick={run} loading={loading} style={{ marginTop: 14, width: '100%' }}>Qualify Lead</Btn>
        {err && <div style={{ color: '#ef4444', fontSize: 13, marginTop: 8 }}>{err}</div>}
      </Card>
      <Card>
        <SectionHead title="Lead Score and Insights" />
        {res ? (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginBottom: 16 }}>
              {[
                { label: 'Lead Quality', value: res.quality, color: QUALITY_COLORS[res.quality] || '#6b7280' },
                { label: 'Budget Fit',   value: res.budget_fit, color: res.budget_fit === 'Good' ? '#10b981' : res.budget_fit === 'Maybe' ? '#f59e0b' : '#ef4444' },
                { label: 'Timeline',     value: res.timeline, color: '#3b82f6' },
              ].map(item => (
                <div key={item.label} style={{ background: '#0f1117', borderRadius: 10, padding: 12, border: '1px solid ' + item.color + '40', textAlign: 'center' }}>
                  <div style={{ color: '#6b7280', fontSize: 10, marginBottom: 4 }}>{item.label}</div>
                  <div style={{ color: item.color, fontSize: 16, fontWeight: 700 }}>{item.value}</div>
                </div>
              ))}
            </div>
            {res.buying_signals?.length > 0 && (
              <div style={{ marginBottom: 14 }}>
                <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 6 }}>Buying Signals</div>
                {res.buying_signals.map((s: string, i: number) => (
                  <div key={i} style={{ color: '#10b981', fontSize: 13, padding: '2px 0' }}>+ {s}</div>
                ))}
              </div>
            )}
            {res.next_action && (
              <div style={{ background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.2)', borderRadius: 8, padding: '10px 14px', marginBottom: 14, color: '#93c5fd', fontSize: 13 }}>
                <span style={{ fontWeight: 600 }}>Next Action: </span>{res.next_action}
              </div>
            )}
            {res.whatsapp_followup && (
              <div>
                <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 6 }}>Suggested WhatsApp Follow-up</div>
                <div style={{ background: '#075e54', borderRadius: 10, padding: '14px 16px', color: '#ecfdf5', fontSize: 13, lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>
                  {res.whatsapp_followup}
                </div>
              </div>
            )}
          </div>
        ) : <Empty text="Lead qualification report will appear here..." />}
      </Card>
    </Row>
  )
}

function TicketTab({ lang }: { lang: Lang }) {
  const [conv, setConv]         = useState('')
  const [custName, setCustName] = useState('')
  const [res, setRes]           = useState<any>(null)
  const [loading, setLoading]   = useState(false)
  const [err, setErr]           = useState('')

  const run = async () => {
    if (!conv.trim()) return
    setLoading(true); setErr(''); setRes(null)
    try {
      setRes(await csAction('summarize_ticket', { conversation: conv, customer_name: custName || 'Customer' }, lang))
    } catch (e: any) { setErr(e.message) }
    setLoading(false)
  }

  const PRIORITY_COLORS: Record<string, string> = { low: '#6b7280', medium: '#3b82f6', high: '#f59e0b', critical: '#ef4444' }

  return (
    <Row>
      <Card>
        <SectionHead title="Ticket Summarizer" sub="Summarize long conversations for agent handoff" />
        <Input label="Customer Name" value={custName} onChange={setCustName} placeholder="Suresh" />
        <div style={{ marginTop: 14 }}>
          <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 4 }}>Full Conversation *</div>
          <TA value={conv} onChange={setConv} placeholder="Customer: My order hasn't arrived yet..." rows={10} />
        </div>
        <Btn onClick={run} loading={loading} style={{ marginTop: 14, width: '100%' }}>Summarize Ticket</Btn>
        {err && <div style={{ color: '#ef4444', fontSize: 13, marginTop: 8 }}>{err}</div>}
      </Card>
      <Card>
        <SectionHead title="Ticket Summary" />
        {res ? (
          <div>
            <div style={{ display: 'flex', gap: 8, marginBottom: 14, flexWrap: 'wrap' }}>
              <Badge label={'Priority: ' + (res.priority || '').toUpperCase()} color={PRIORITY_COLORS[res.priority] || '#6b7280'} />
              <Badge label={'Category: ' + res.category} color="#6b7280" />
              <Badge label={'Mood: ' + res.customer_mood} color={res.customer_mood === 'angry' ? '#ef4444' : '#3b82f6'} />
            </div>
            <div style={{ marginBottom: 14 }}>
              <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 6 }}>Issue Summary</div>
              <div style={{ background: '#0f1117', borderRadius: 8, padding: '12px 14px', color: '#e2e8f0', fontSize: 13, lineHeight: 1.7 }}>{res.issue_summary}</div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 14 }}>
              <div>
                <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 6 }}>What Was Tried</div>
                {(res.what_was_tried || []).map((s: string, i: number) => (
                  <div key={i} style={{ color: '#6b7280', fontSize: 12, padding: '2px 0' }}>- {s}</div>
                ))}
              </div>
              <div>
                <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 6 }}>Pending Actions</div>
                {(res.what_is_needed || []).map((s: string, i: number) => (
                  <div key={i} style={{ color: '#f59e0b', fontSize: 12, padding: '2px 0' }}>{'>'} {s}</div>
                ))}
              </div>
            </div>
            {res.suggested_resolution && (
              <div style={{ background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: 8, padding: '10px 14px', color: '#5eead4', fontSize: 13 }}>
                <span style={{ fontWeight: 600 }}>Suggested: </span>{res.suggested_resolution}
              </div>
            )}
          </div>
        ) : <Empty text="Ticket summary will appear here..." />}
      </Card>
    </Row>
  )
}

function TemplateTab({ lang }: { lang: Lang }) {
  const [scenario, setScenario] = useState('')
  const [bizType, setBizType]   = useState('')
  const [tone, setTone]         = useState('friendly')
  const [res, setRes]           = useState<any>(null)
  const [loading, setLoading]   = useState(false)
  const [err, setErr]           = useState('')

  const run = async () => {
    if (!scenario.trim()) return
    setLoading(true); setErr(''); setRes(null)
    try {
      setRes(await csAction('response_template', { scenario, business_type: bizType || 'General', tone }, lang))
    } catch (e: any) { setErr(e.message) }
    setLoading(false)
  }

  return (
    <Row>
      <Card>
        <SectionHead title="Response Template Generator" sub="Get 3 ready-to-use templates for any scenario" />
        <Input label="Business Type" value={bizType} onChange={setBizType} placeholder="e.g. Restaurant, Online Store" />
        <div style={{ marginTop: 14 }}>
          <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 4 }}>Scenario *</div>
          <TA value={scenario} onChange={setScenario} placeholder="e.g. Customer asking for refund after 3 days" rows={3} />
        </div>
        <Select label="Tone" value={tone} onChange={setTone} options={TONE_OPTIONS} />
        <Btn onClick={run} loading={loading} style={{ marginTop: 14, width: '100%' }}>Generate Templates</Btn>
        {err && <div style={{ color: '#ef4444', fontSize: 13, marginTop: 8 }}>{err}</div>}
      </Card>
      <Card>
        <SectionHead title="Response Templates" />
        {res?.templates ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {res.templates.map((t: any, i: number) => (
              <div key={i} style={{ background: '#0f1117', border: '1px solid #1e2535', borderRadius: 10, padding: '14px 16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                  <span style={{ color: '#5eead4', fontWeight: 600, fontSize: 14 }}>{t.variation}</span>
                  {t.use_case && <span style={{ color: '#4b5563', fontSize: 11 }}>{t.use_case}</span>}
                </div>
                {t.subject_or_opening && <div style={{ color: '#f59e0b', fontSize: 12, marginBottom: 6 }}>{t.subject_or_opening}</div>}
                <div style={{ color: '#e2e8f0', fontSize: 13, lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>{t.body}</div>
                {t.closing && <div style={{ color: '#6b7280', fontSize: 12, marginTop: 8 }}>{t.closing}</div>}
              </div>
            ))}
          </div>
        ) : <Empty text="3 template variations will appear here..." />}
      </Card>
    </Row>
  )
}

function KBTab({ lang }: { lang: Lang }) {
  const [question, setQuestion]   = useState('')
  const [kbContent, setKbContent] = useState('')
  const [bizName, setBizName]     = useState('')
  const [res, setRes]             = useState<any>(null)
  const [loading, setLoading]     = useState(false)
  const [err, setErr]             = useState('')

  const run = async () => {
    if (!question.trim()) return
    setLoading(true); setErr(''); setRes(null)
    try {
      setRes(await csAction('kb_answer', { question, kb_content: kbContent, business_name: bizName || 'Our Business' }, lang))
    } catch (e: any) { setErr(e.message) }
    setLoading(false)
  }

  return (
    <Row>
      <Card>
        <SectionHead title="Knowledge Base Q&A" sub="Ask questions against your knowledge base content" />
        <Input label="Business Name" value={bizName} onChange={setBizName} placeholder="My Business" />
        <div style={{ marginTop: 14 }}>
          <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 4 }}>Knowledge Base Content</div>
          <TA value={kbContent} onChange={setKbContent} placeholder="Paste your product docs, policies, SOPs here..." rows={6} />
        </div>
        <div style={{ marginTop: 14 }}>
          <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 4 }}>Question *</div>
          <TA value={question} onChange={setQuestion} placeholder="What is the cancellation policy?" rows={3} />
        </div>
        <Btn onClick={run} loading={loading} style={{ marginTop: 14, width: '100%' }}>Search Knowledge Base</Btn>
        {err && <div style={{ color: '#ef4444', fontSize: 13, marginTop: 8 }}>{err}</div>}
      </Card>
      <Card>
        <SectionHead title="KB Answer" />
        {res ? (
          <div>
            <div style={{ display: 'flex', gap: 8, marginBottom: 14, flexWrap: 'wrap' }}>
              <Badge label={res.found_in_kb ? 'Found in KB' : 'Not in KB'} color={res.found_in_kb ? '#10b981' : '#f59e0b'} />
              <Badge label={'Confidence: ' + res.confidence} color="#3b82f6" />
            </div>
            <div style={{ background: '#0f1117', borderRadius: 8, padding: '14px 16px', color: '#e2e8f0', fontSize: 14, lineHeight: 1.7, whiteSpace: 'pre-wrap', marginBottom: 14 }}>
              {res.answer}
            </div>
            {res.related_topics?.length > 0 && (
              <div style={{ marginBottom: 14 }}>
                <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 6 }}>Related Topics</div>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {res.related_topics.map((t: string) => (
                    <span key={t} style={{ background: '#1e2535', borderRadius: 4, padding: '3px 10px', color: '#9ca3af', fontSize: 12 }}>{t}</span>
                  ))}
                </div>
              </div>
            )}
            {res.should_add_to_faq && (
              <div style={{ background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.2)', borderRadius: 8, padding: '10px 14px' }}>
                <div style={{ color: '#93c5fd', fontSize: 12, fontWeight: 600, marginBottom: 4 }}>Suggested FAQ Addition</div>
                <div style={{ color: '#e2e8f0', fontSize: 13 }}>{res.suggested_faq_question}</div>
              </div>
            )}
          </div>
        ) : <Empty text="Answer from your knowledge base will appear here..." />}
      </Card>
    </Row>
  )
}

function ReportTab({ lang }: { lang: Lang }) {
  const [ticketData, setTicketData] = useState('')
  const [period, setPeriod]         = useState('')
  const [bizName, setBizName]       = useState('')
  const [res, setRes]               = useState<any>(null)
  const [loading, setLoading]       = useState(false)
  const [err, setErr]               = useState('')

  const run = async () => {
    setLoading(true); setErr(''); setRes(null)
    try {
      setRes(await csAction('weekly_report', {
        ticket_data: ticketData || 'No data provided',
        period: period || 'This week',
        business_name: bizName || 'Our Business',
      }, lang))
    } catch (e: any) { setErr(e.message) }
    setLoading(false)
  }

  return (
    <Row>
      <Card>
        <SectionHead title="Weekly Intelligence Report" sub="AI-generated insights from your support data" />
        <Input label="Business Name" value={bizName} onChange={setBizName} placeholder="My Business" />
        <Input label="Period" value={period} onChange={setPeriod} placeholder="e.g. July 14-20, 2025" />
        <div style={{ marginTop: 14 }}>
          <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 4 }}>Ticket Data / Notes</div>
          <TA value={ticketData} onChange={setTicketData} placeholder="25 tickets: 10 delivery delays, 8 billing questions..." rows={8} />
        </div>
        <Btn onClick={run} loading={loading} style={{ marginTop: 14, width: '100%' }}>Generate Report</Btn>
        {err && <div style={{ color: '#ef4444', fontSize: 13, marginTop: 8 }}>{err}</div>}
      </Card>
      <Card>
        <SectionHead title="Weekly Report" />
        {res ? (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 16 }}>
              {[
                { label: 'Avg Resolution', value: res.avg_resolution_time, color: '#3b82f6' },
                { label: 'CSAT Score',     value: res.csat_score,          color: '#10b981' },
              ].map(item => (
                <div key={item.label} style={{ background: '#0f1117', borderRadius: 8, padding: 12, border: '1px solid ' + item.color + '30', textAlign: 'center' }}>
                  <div style={{ color: '#6b7280', fontSize: 11 }}>{item.label}</div>
                  <div style={{ color: item.color, fontSize: 18, fontWeight: 700 }}>{item.value}</div>
                </div>
              ))}
            </div>
            {res.executive_summary && (
              <div style={{ marginBottom: 14 }}>
                <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 6 }}>Executive Summary</div>
                <div style={{ background: '#0f1117', borderRadius: 8, padding: '12px 14px', color: '#e2e8f0', fontSize: 13, lineHeight: 1.7 }}>{res.executive_summary}</div>
              </div>
            )}
            {res.top_issues?.length > 0 && (
              <div style={{ marginBottom: 14 }}>
                <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 6 }}>Top Issues</div>
                {res.top_issues.map((issue: any, i: number) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: '#0f1117', borderRadius: 6, marginBottom: 4 }}>
                    <span style={{ color: '#e2e8f0', fontSize: 13 }}>{issue.issue}</span>
                    <span style={{ color: '#6b7280', fontSize: 12 }}>{issue.percentage}</span>
                  </div>
                ))}
              </div>
            )}
            {(res.key_wins?.length > 0 || res.action_items?.length > 0) && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 14 }}>
                <div>
                  <div style={{ color: '#10b981', fontSize: 12, marginBottom: 6 }}>Key Wins</div>
                  {(res.key_wins || []).map((w: string, i: number) => <div key={i} style={{ color: '#e2e8f0', fontSize: 12, padding: '2px 0' }}>+ {w}</div>)}
                </div>
                <div>
                  <div style={{ color: '#f59e0b', fontSize: 12, marginBottom: 6 }}>Action Items</div>
                  {(res.action_items || []).map((a: string, i: number) => <div key={i} style={{ color: '#e2e8f0', fontSize: 12, padding: '2px 0' }}>- {a}</div>)}
                </div>
              </div>
            )}
            {res.recommended_faq_additions?.length > 0 && (
              <div>
                <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 6 }}>Recommended FAQ Additions</div>
                {res.recommended_faq_additions.map((q: string, i: number) => (
                  <div key={i} style={{ background: '#0f1117', borderRadius: 6, padding: '6px 10px', marginBottom: 4, color: '#93c5fd', fontSize: 12 }}>{q}</div>
                ))}
              </div>
            )}
          </div>
        ) : <Empty text="Weekly intelligence report will appear here..." />}
      </Card>
    </Row>
  )
}

// ── SLA Tracker ───────────────────────────────────────────────────────────────

const PRIORITY_COLORS: Record<string, string> = { critical: '#ef4444', high: '#f59e0b', medium: '#3b82f6', low: '#10b981' }
const DEMO_TICKETS = [
  { id: 'TKT-001', subject: 'Payment not processed', priority: 'critical', created_at: new Date(Date.now() - 2 * 3600000).toISOString(), first_response_at: null, resolved_at: null, assignee: 'Ravi' },
  { id: 'TKT-002', subject: 'Order stuck in processing', priority: 'high', created_at: new Date(Date.now() - 20 * 3600000).toISOString(), first_response_at: new Date(Date.now() - 18 * 3600000).toISOString(), resolved_at: null, assignee: 'Priya' },
  { id: 'TKT-003', subject: 'GST invoice not received', priority: 'medium', created_at: new Date(Date.now() - 10 * 3600000).toISOString(), first_response_at: new Date(Date.now() - 9 * 3600000).toISOString(), resolved_at: null, assignee: 'Ravi' },
  { id: 'TKT-004', subject: 'Login issue', priority: 'low', created_at: new Date(Date.now() - 5 * 3600000).toISOString(), first_response_at: new Date(Date.now() - 4.5 * 3600000).toISOString(), resolved_at: new Date(Date.now() - 1 * 3600000).toISOString(), assignee: 'Meena' },
  { id: 'TKT-005', subject: 'Refund not credited', priority: 'high', created_at: new Date(Date.now() - 30 * 3600000).toISOString(), first_response_at: null, resolved_at: null, assignee: 'Priya' },
]

function SlaTab({ lang }: { lang: Lang }) {
  const [ticketJson, setTicketJson] = useState(JSON.stringify(DEMO_TICKETS, null, 2))
  const [bizName, setBizName]       = useState('')
  const [res, setRes]               = useState<any>(null)
  const [loading, setLoading]       = useState(false)
  const [err, setErr]               = useState('')
  const [view, setView]             = useState<'breaches' | 'at_risk' | 'on_track' | 'assignees'>('breaches')

  const analyze = async () => {
    setLoading(true); setErr(''); setRes(null)
    try {
      const tickets = JSON.parse(ticketJson)
      setRes(await csAction('analyze_sla', { tickets, business_name: bizName || 'My Business' }, lang))
    } catch (e: any) { setErr(e.message) }
    setLoading(false)
  }

  const HEALTH_COLOR: Record<string, string> = { Healthy: '#10b981', 'At Risk': '#f59e0b', Critical: '#ef4444' }

  return (
    <Row>
      <Card style={{ flex: '0 0 380px' }}>
        <SectionHead title="SLA Tracker" sub="Paste ticket data (JSON) — AI flags breaches and risk" />
        <Input label="Business Name" value={bizName} onChange={setBizName} placeholder="Sri Lakshmi Stores" />
        <div style={{ marginTop: 10 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
            <div style={{ color: '#9ca3af', fontSize: 12 }}>Tickets (JSON array)</div>
            <span onClick={() => setTicketJson(JSON.stringify(DEMO_TICKETS, null, 2))} style={{ cursor: 'pointer', color: '#818cf8', fontSize: 11 }}>Load Demo</span>
          </div>
          <TA value={ticketJson} onChange={setTicketJson} rows={12} placeholder='[{"id":"T1","subject":"...","priority":"high","created_at":"ISO","assignee":"Ravi"}]' />
        </div>
        <div style={{ padding: '8px 12px', background: 'rgba(129,140,248,0.06)', border: '1px solid #818cf833', borderRadius: 6, fontSize: 11, color: '#a5b4fc', marginTop: 8, marginBottom: 8 }}>
          Fields: id, subject, priority (critical/high/medium/low), created_at (ISO), first_response_at (ISO or null), resolved_at (ISO or null), assignee
        </div>
        <Btn onClick={analyze} loading={loading} style={{ width: '100%' }}>Analyze SLA</Btn>
        {err && <div style={{ color: '#ef4444', fontSize: 12, marginTop: 6 }}>{err}</div>}
      </Card>

      <Card>
        {res ? (
          <div>
            {/* Health + KPIs */}
            <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 14 }}>
              <div style={{ padding: '6px 16px', borderRadius: 20, background: (HEALTH_COLOR[res.sla_health] || '#6b7280') + '22', color: HEALTH_COLOR[res.sla_health] || '#6b7280', fontWeight: 700, fontSize: 13 }}>
                {res.sla_health === 'Critical' ? '🔴' : res.sla_health === 'At Risk' ? '🟡' : '🟢'} {res.sla_health}
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 8, marginBottom: 16 }}>
              {[
                { label: 'Total', value: res.stats.total, color: '#6b7280' },
                { label: 'Breached', value: res.stats.breached, color: '#ef4444' },
                { label: 'At Risk', value: res.stats.at_risk, color: '#f59e0b' },
                { label: 'Resolved', value: res.stats.resolved, color: '#10b981' },
              ].map(kpi => (
                <div key={kpi.label} style={{ background: '#0f1117', borderRadius: 8, padding: '10px 12px', textAlign: 'center', border: `1px solid ${kpi.color}33` }}>
                  <div style={{ color: kpi.color, fontSize: 22, fontWeight: 700 }}>{kpi.value}</div>
                  <div style={{ color: '#6b7280', fontSize: 11 }}>{kpi.label}</div>
                </div>
              ))}
            </div>

            {/* View toggle */}
            <div style={{ display: 'flex', gap: 6, marginBottom: 14, flexWrap: 'wrap' }}>
              {(['breaches', 'at_risk', 'on_track', 'assignees'] as const).map(v => (
                <span key={v} onClick={() => setView(v)} style={{ cursor: 'pointer', padding: '4px 12px', borderRadius: 16, fontSize: 12, fontWeight: 600, textTransform: 'capitalize',
                  background: view === v ? '#818cf8' : '#1e2535', color: view === v ? '#fff' : '#9ca3af' }}>
                  {v === 'at_risk' ? 'At Risk' : v === 'on_track' ? 'On Track' : v.charAt(0).toUpperCase() + v.slice(1)}
                  {v === 'breaches' && res.breaches.length > 0 && <span style={{ marginLeft: 6, background: '#ef4444', color: '#fff', fontSize: 10, borderRadius: 10, padding: '1px 5px' }}>{res.breaches.length}</span>}
                  {v === 'at_risk' && res.at_risk.length > 0 && <span style={{ marginLeft: 6, background: '#f59e0b', color: '#fff', fontSize: 10, borderRadius: 10, padding: '1px 5px' }}>{res.at_risk.length}</span>}
                </span>
              ))}
            </div>

            {/* Ticket list */}
            {view !== 'assignees' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {((view === 'breaches' ? res.breaches : view === 'at_risk' ? res.at_risk : res.on_track) as any[]).length === 0
                  ? <Empty text={`No tickets in ${view} status`} />
                  : ((view === 'breaches' ? res.breaches : view === 'at_risk' ? res.at_risk : res.on_track) as any[]).map((t: any) => (
                    <div key={t.id} style={{ background: '#0f1117', borderRadius: 8, padding: '10px 14px', border: `1px solid ${PRIORITY_COLORS[t.priority] || '#6b7280'}44` }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                          <span style={{ color: '#6b7280', fontSize: 11 }}>{t.id}</span>
                          <span style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 600 }}>{t.subject}</span>
                        </div>
                        <Badge label={t.priority} color={PRIORITY_COLORS[t.priority] || '#6b7280'} />
                      </div>
                      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                        <span style={{ color: '#6b7280', fontSize: 11 }}>👤 {t.assignee}</span>
                        <span style={{ color: '#6b7280', fontSize: 11 }}>⏱ {t.age_hrs}h old</span>
                        {t.responded && <span style={{ color: '#10b981', fontSize: 11 }}>✓ Responded {t.resp_time_hrs}h</span>}
                        {!t.responded && <span style={{ color: '#ef4444', fontSize: 11 }}>⚠ No response yet</span>}
                        {t.resolved && <span style={{ color: '#10b981', fontSize: 11 }}>✓ Resolved {t.resolution_time_hrs}h</span>}
                      </div>
                      {(t.breach_reason || t.risk_reason) && (
                        <div style={{ marginTop: 4, color: view === 'breaches' ? '#fca5a5' : '#fcd34d', fontSize: 11 }}>
                          {view === 'breaches' ? '🚨' : '⚠️'} {t.breach_reason || t.risk_reason}
                        </div>
                      )}
                    </div>
                  ))}
              </div>
            )}

            {/* Assignee summary */}
            {view === 'assignees' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {(res.assignee_summary as any[]).map((a: any) => (
                  <div key={a.assignee} style={{ background: '#0f1117', borderRadius: 8, padding: '10px 14px', border: '1px solid #1e2535', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 600 }}>👤 {a.assignee}</span>
                    <div style={{ display: 'flex', gap: 10 }}>
                      <Badge label={`${a.total} tickets`} color="#6b7280" />
                      {a.breached > 0 && <Badge label={`${a.breached} breached`} color="#ef4444" />}
                      {a.resolved > 0 && <Badge label={`${a.resolved} resolved`} color="#10b981" />}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : <Empty text="Paste ticket JSON and click Analyze SLA →" />}
      </Card>
    </Row>
  )
}

// ── CSAT Survey Builder (Round 5) ─────────────────────────────────────────────

const CSAT_TOUCHPOINTS = ['purchase experience', 'delivery', 'product quality', 'customer service', 'overall satisfaction']
const CSAT_BIZ_TYPES   = [{ label: 'Retail / E-commerce', value: 'retail' }, { label: 'Restaurant / Food', value: 'restaurant' }, { label: 'Service Business', value: 'service' }, { label: 'SaaS / Tech', value: 'saas' }, { label: 'Healthcare', value: 'healthcare' }, { label: 'Education', value: 'education' }]

const DEMO_RESPONSES = [
  { nps: 9,  overall_rating: 5, scores: { 'purchase experience': 5, 'delivery': 4, 'customer service': 5 }, comment: 'Really happy with the quick response!' },
  { nps: 7,  overall_rating: 4, scores: { 'purchase experience': 4, 'delivery': 3, 'customer service': 4 }, comment: 'Delivery was a bit slow but product quality great' },
  { nps: 3,  overall_rating: 2, scores: { 'purchase experience': 2, 'delivery': 2, 'customer service': 3 }, comment: 'Took too long, support wasnt helpful' },
  { nps: 10, overall_rating: 5, scores: { 'purchase experience': 5, 'delivery': 5, 'customer service': 5 }, comment: '' },
  { nps: 6,  overall_rating: 3, scores: { 'purchase experience': 3, 'delivery': 2, 'customer service': 3 }, comment: 'Average experience, expected better delivery time' },
  { nps: 8,  overall_rating: 4, scores: { 'purchase experience': 4, 'delivery': 4, 'customer service': 5 }, comment: 'Customer support was excellent!' },
]

function CsatTab({ lang }: { lang: Lang }) {
  const [mode, setMode]             = useState<'build' | 'analyze'>('build')
  const [bizName, setBizName]       = useState('')
  const [bizType, setBizType]       = useState('retail')
  const [touchpoints, setTouchpoints] = useState<string[]>(['purchase experience', 'delivery', 'customer service'])
  const [survey, setSurvey]         = useState<any>(null)
  const [surveyLoading, setSurveyLoading] = useState(false)
  const [surveyErr, setSurveyErr]   = useState('')
  const [responsesJson, setResponsesJson] = useState(JSON.stringify(DEMO_RESPONSES, null, 2))
  const [analysis, setAnalysis]     = useState<any>(null)
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [analysisErr, setAnalysisErr] = useState('')

  const toggleTp = (tp: string) => setTouchpoints(prev => prev.includes(tp) ? prev.filter(x => x !== tp) : [...prev, tp])

  const buildSurvey = async () => {
    setSurveyLoading(true); setSurveyErr(''); setSurvey(null)
    try {
      setSurvey(await csAction('build_csat_survey', { business_name: bizName, business_type: bizType, touchpoints }, lang))
    } catch (e: any) { setSurveyErr(e.message) }
    setSurveyLoading(false)
  }

  const analyzeCsat = async () => {
    setAnalysisLoading(true); setAnalysisErr(''); setAnalysis(null)
    try {
      const responses = JSON.parse(responsesJson)
      setAnalysis(await csAction('analyze_csat', { responses, business_name: bizName }, lang))
    } catch (e: any) { setAnalysisErr(e.message) }
    setAnalysisLoading(false)
  }

  const HEALTH_COLORS: Record<string, string> = { Excellent: '#10b981', Good: '#3b82f6', 'Needs Attention': '#f59e0b', Critical: '#ef4444' }
  const STATUS_COLORS: Record<string, string>  = { Good: '#10b981', 'Needs Work': '#f59e0b', Critical: '#ef4444' }

  return (
    <Row>
      <Card style={{ flex: '0 0 360px' }}>
        <SectionHead title="CSAT Survey Builder" sub="Generate survey & analyze customer satisfaction" />
        <div style={{ display: 'flex', gap: 6, marginBottom: 16 }}>
          {(['build', 'analyze'] as const).map(m => (
            <span key={m} onClick={() => setMode(m)} style={{ cursor: 'pointer', flex: 1, textAlign: 'center', padding: '7px', borderRadius: 8, fontSize: 13, fontWeight: 600, background: mode === m ? '#10b981' : '#1e2535', color: mode === m ? '#fff' : '#9ca3af' }}>
              {m === 'build' ? '🔨 Build Survey' : '📊 Analyze Responses'}
            </span>
          ))}
        </div>

        <Input label="Business Name" value={bizName} onChange={setBizName} placeholder="Sri Lakshmi Stores" />

        {mode === 'build' && (
          <>
            <Select label="Business Type" value={bizType} onChange={setBizType} options={CSAT_BIZ_TYPES} />
            <div style={{ marginTop: 14 }}>
              <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 8 }}>Touchpoints to survey</div>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {CSAT_TOUCHPOINTS.map(tp => (
                  <span key={tp} onClick={() => toggleTp(tp)} style={{ cursor: 'pointer', padding: '4px 10px', borderRadius: 20, fontSize: 11, fontWeight: 600, textTransform: 'capitalize',
                    background: touchpoints.includes(tp) ? '#10b981' : '#1e2535', color: touchpoints.includes(tp) ? '#fff' : '#9ca3af', border: touchpoints.includes(tp) ? '1px solid #10b981' : '1px solid #374151' }}>
                    {tp}
                  </span>
                ))}
              </div>
            </div>
            <Btn onClick={buildSurvey} loading={surveyLoading} style={{ marginTop: 14, width: '100%' }}>Build Survey</Btn>
            {surveyErr && <div style={{ color: '#ef4444', fontSize: 12, marginTop: 6 }}>{surveyErr}</div>}
          </>
        )}

        {mode === 'analyze' && (
          <>
            <div style={{ marginTop: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <div style={{ color: '#9ca3af', fontSize: 12 }}>Responses (JSON array)</div>
                <span onClick={() => setResponsesJson(JSON.stringify(DEMO_RESPONSES, null, 2))} style={{ cursor: 'pointer', color: '#10b981', fontSize: 11 }}>Load Demo</span>
              </div>
              <TA value={responsesJson} onChange={setResponsesJson} rows={10} placeholder='[{"nps":9,"overall_rating":5,"scores":{"delivery":4},"comment":"Great!"}]' />
            </div>
            <div style={{ padding: '6px 10px', background: 'rgba(16,185,129,0.06)', border: '1px solid #10b98133', borderRadius: 6, fontSize: 11, color: '#6ee7b7', marginTop: 8 }}>
              Fields: nps (0-10), overall_rating (1-5), scores ({'{'}touchpoint: 1-5{'}'}), comment (optional)
            </div>
            <Btn onClick={analyzeCsat} loading={analysisLoading} style={{ marginTop: 10, width: '100%' }}>Analyze CSAT</Btn>
            {analysisErr && <div style={{ color: '#ef4444', fontSize: 12, marginTop: 6 }}>{analysisErr}</div>}
          </>
        )}
      </Card>

      <Card>
        {mode === 'build' && survey && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
              <SectionHead title={survey.survey_title} sub={`${survey.total_questions} questions · ~${survey.estimated_time}`} />
            </div>
            {survey.share_tip && (
              <div style={{ padding: '8px 12px', background: 'rgba(16,185,129,0.07)', border: '1px solid #10b98133', borderRadius: 6, color: '#6ee7b7', fontSize: 12, marginBottom: 14 }}>
                💡 {survey.share_tip}
              </div>
            )}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {(survey.questions || []).map((q: any, i: number) => (
                <div key={q.id} style={{ background: '#0f1117', borderRadius: 8, padding: '10px 14px', border: '1px solid #1e2535' }}>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                    <span style={{ minWidth: 22, height: 22, borderRadius: '50%', background: '#10b98122', color: '#10b981', fontSize: 11, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', marginTop: 1 }}>{i + 1}</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ color: '#e2e8f0', fontSize: 13, lineHeight: 1.5, marginBottom: 4 }}>{q.text}</div>
                      <div style={{ display: 'flex', gap: 6 }}>
                        <Badge label={q.type === 'nps' ? 'NPS 0-10' : q.type === 'rating' ? `Rating ${q.scale}` : 'Open Text'} color={q.type === 'nps' ? '#818cf8' : q.type === 'rating' ? '#10b981' : '#6b7280'} />
                        {q.required && <Badge label="Required" color="#f59e0b" />}
                        {q.touchpoint && <Badge label={q.touchpoint} color="#3b82f6" />}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {mode === 'analyze' && analysis && (
          <div>
            <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 14 }}>
              <div style={{ padding: '6px 16px', borderRadius: 20, fontWeight: 700, fontSize: 13, background: (HEALTH_COLORS[analysis.health] || '#6b7280') + '22', color: HEALTH_COLORS[analysis.health] || '#6b7280' }}>
                {analysis.health}
              </div>
              <div style={{ color: '#6b7280', fontSize: 12 }}>{analysis.total_responses} responses analyzed</div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 8, marginBottom: 16 }}>
              {[
                { label: 'CSAT Score', value: `${analysis.csat_score}%`, color: '#10b981' },
                { label: 'Avg Rating', value: `${analysis.avg_rating}/5`,  color: '#818cf8' },
                { label: 'NPS Score',  value: analysis.nps_score,          color: analysis.nps_score >= 0 ? '#3b82f6' : '#ef4444' },
              ].map(k => (
                <div key={k.label} style={{ background: '#0f1117', borderRadius: 8, padding: '10px', textAlign: 'center', border: `1px solid ${k.color}33` }}>
                  <div style={{ color: '#6b7280', fontSize: 10, marginBottom: 4 }}>{k.label}</div>
                  <div style={{ color: k.color, fontSize: 20, fontWeight: 700 }}>{k.value}</div>
                </div>
              ))}
            </div>

            {/* NPS breakdown */}
            <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
              {[
                { label: `Promoters (9-10)`, value: analysis.nps_breakdown?.promoters, color: '#10b981' },
                { label: `Passives (7-8)`,   value: analysis.nps_breakdown?.passives,  color: '#f59e0b' },
                { label: `Detractors (0-6)`, value: analysis.nps_breakdown?.detractors, color: '#ef4444' },
              ].map(b => (
                <div key={b.label} style={{ flex: 1, background: '#0f1117', borderRadius: 6, padding: '8px 10px', textAlign: 'center', border: `1px solid ${b.color}33` }}>
                  <div style={{ color: b.color, fontSize: 16, fontWeight: 700 }}>{b.value}</div>
                  <div style={{ color: '#6b7280', fontSize: 10 }}>{b.label}</div>
                </div>
              ))}
            </div>

            {/* Touchpoint scores */}
            {analysis.touchpoint_summary?.length > 0 && (
              <div style={{ marginBottom: 14 }}>
                <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 8 }}>Touchpoint Scores</div>
                {(analysis.touchpoint_summary as any[]).map((t: any) => (
                  <div key={t.touchpoint} style={{ marginBottom: 8 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
                      <span style={{ color: '#e2e8f0', fontSize: 12, textTransform: 'capitalize' }}>{t.touchpoint}</span>
                      <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                        <span style={{ color: STATUS_COLORS[t.status] || '#6b7280', fontSize: 11 }}>{t.status}</span>
                        <span style={{ color: '#e2e8f0', fontSize: 12, fontWeight: 600 }}>{t.avg_score}/5</span>
                      </div>
                    </div>
                    <div style={{ height: 5, background: '#1e2535', borderRadius: 3 }}>
                      <div style={{ height: '100%', width: `${t.pct}%`, background: STATUS_COLORS[t.status] || '#6b7280', borderRadius: 3 }} />
                    </div>
                  </div>
                ))}
              </div>
            )}

            {analysis.top_action && (
              <div style={{ padding: '10px 14px', background: 'rgba(245,158,11,0.08)', border: '1px solid #f59e0b33', borderRadius: 8, color: '#fcd34d', fontSize: 13 }}>
                🎯 <strong>Top Action:</strong> {analysis.top_action}
              </div>
            )}

            {analysis.comments?.length > 0 && (
              <div style={{ marginTop: 12 }}>
                <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 6 }}>Customer Comments</div>
                {analysis.comments.slice(0, 4).map((c: string, i: number) => (
                  <div key={i} style={{ background: '#0f1117', borderRadius: 6, padding: '7px 10px', marginBottom: 4, color: '#9ca3af', fontSize: 12, fontStyle: 'italic' }}>"{c}"</div>
                ))}
              </div>
            )}
          </div>
        )}

        {!survey && !analysis && (
          <Empty text={mode === 'build' ? 'Configure your survey on the left and click Build Survey →' : 'Paste survey responses and click Analyze CSAT →'} />
        )}
      </Card>
    </Row>
  )
}

const CANNED_CATS = ['General', 'Billing', 'Delivery', 'Technical', 'Refund', 'Greeting', 'Escalation']

interface CannedItem { id: string; category: string; trigger: string; body: string }

function CannedTab({ lang }: { lang: Lang }) {
  const STORAGE_KEY = 'cs_canned_responses'
  const load = (): CannedItem[] => {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]') } catch { return [] }
  }
  const [items, setItems]       = useState<CannedItem[]>(load)
  const [catFilter, setCatFilter] = useState('All')
  const [editing, setEditing]   = useState<CannedItem | null>(null)
  const [form, setForm]         = useState({ category: 'General', trigger: '', body: '' })
  const [incomingMsg, setIncoming] = useState('')
  const [bizName, setBizName]   = useState('')
  const [aiRes, setAiRes]       = useState<any>(null)
  const [aiLoading, setAiLoading] = useState(false)
  const [aiErr, setAiErr]       = useState('')

  const save = (list: CannedItem[]) => { setItems(list); localStorage.setItem(STORAGE_KEY, JSON.stringify(list)) }

  const addOrUpdate = () => {
    if (!form.trigger || !form.body) return
    if (editing) {
      save(items.map(i => i.id === editing.id ? { ...editing, ...form } : i))
      setEditing(null)
    } else {
      save([...items, { id: Date.now().toString(), ...form }])
    }
    setForm({ category: 'General', trigger: '', body: '' })
  }

  const del = (id: string) => save(items.filter(i => i.id !== id))

  const startEdit = (item: CannedItem) => { setEditing(item); setForm({ category: item.category, trigger: item.trigger, body: item.body }) }

  const aiSuggest = async () => {
    setAiLoading(true); setAiErr(''); setAiRes(null)
    try {
      setAiRes(await csAction('suggest_canned_response', {
        incoming_message: incomingMsg,
        business_name: bizName || 'Our Business',
        existing_templates: items.map(i => ({ trigger: i.trigger, body: i.body })),
      }, lang))
    } catch (e: any) { setAiErr(e.message) }
    setAiLoading(false)
  }

  const saveAiSuggestion = () => {
    if (!aiRes?.suggested_text) return
    save([...items, { id: Date.now().toString(), category: aiRes.category || 'General', trigger: incomingMsg.slice(0, 60), body: aiRes.suggested_text }])
    setAiRes(null); setIncoming('')
  }

  const filtered = catFilter === 'All' ? items : items.filter(i => i.category === catFilter)
  const CAT_COLOR: Record<string, string> = { Billing: '#f59e0b', Delivery: '#3b82f6', Technical: '#8b5cf6', Refund: '#ef4444', Greeting: '#10b981', Escalation: '#ec4899', General: '#6b7280' }

  return (
    <Row>
      <Card style={{ flex: '0 0 340px' }}>
        <SectionHead title="Add / Edit Template" sub="Save reusable canned responses" />
        <Select label="Category" value={form.category} onChange={v => setForm(f => ({ ...f, category: v }))} options={CANNED_CATS.map(c => ({ value: c, label: c }))} />
        <Input label="Trigger / Short Name" value={form.trigger} onChange={v => setForm(f => ({ ...f, trigger: v }))} placeholder="e.g. Order not received" />
        <div style={{ marginTop: 14 }}>
          <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 4 }}>Response Body</div>
          <TA value={form.body} onChange={v => setForm(f => ({ ...f, body: v }))} rows={5} placeholder="Dear [Customer Name], Thank you for reaching out..." />
        </div>
        <div style={{ display: 'flex', gap: 8, marginTop: 14 }}>
          <Btn onClick={addOrUpdate} style={{ flex: 1 }}>{editing ? 'Update Template' : 'Save Template'}</Btn>
          {editing && <Btn onClick={() => { setEditing(null); setForm({ category: 'General', trigger: '', body: '' }) }} style={{ background: '#374151' }}>Cancel</Btn>}
        </div>

        <div style={{ marginTop: 24, paddingTop: 16, borderTop: '1px solid #1e2535' }}>
          <SectionHead title="AI Suggest" sub="AI matches message to existing or writes new" />
          <Input label="Business Name" value={bizName} onChange={setBizName} placeholder="Sri Lakshmi Stores" />
          <div style={{ marginTop: 10 }}>
            <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 4 }}>Incoming Message</div>
            <TA value={incomingMsg} onChange={setIncoming} rows={3} placeholder="Customer: My order hasn't arrived yet and it's been 5 days..." />
          </div>
          <Btn onClick={aiSuggest} loading={aiLoading} disabled={!incomingMsg} style={{ marginTop: 10, width: '100%' }}>
            AI Suggest Response
          </Btn>
          {aiErr && <div style={{ color: '#ef4444', fontSize: 12, marginTop: 6 }}>{aiErr}</div>}
          {aiRes && (
            <div style={{ marginTop: 10, background: '#0f1117', borderRadius: 8, padding: '12px 14px', border: '1px solid #10b98133' }}>
              <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
                <Badge label={aiRes.category || 'General'} color={CAT_COLOR[aiRes.category] || '#6b7280'} />
                <Badge label={`${Math.round((aiRes.confidence || 0) * 100)}% confidence`} color="#3b82f6" />
                {aiRes.matched_existing && <Badge label="Matched existing" color="#10b981" />}
              </div>
              <div style={{ color: '#e2e8f0', fontSize: 13, lineHeight: 1.6, marginBottom: 8 }}>{aiRes.suggested_text}</div>
              {aiRes.reason && <div style={{ color: '#6b7280', fontSize: 11, marginBottom: 8 }}>{aiRes.reason}</div>}
              <Btn onClick={saveAiSuggestion} style={{ width: '100%', fontSize: 12 }}>Save to Library</Btn>
            </div>
          )}
        </div>
      </Card>

      <Card>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
          <SectionHead title={`Canned Library (${items.length})`} sub="Click to copy, edit, or delete" />
        </div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 14 }}>
          {['All', ...CANNED_CATS].map(c => (
            <span key={c} onClick={() => setCatFilter(c)} style={{ cursor: 'pointer', padding: '4px 10px', borderRadius: 20, fontSize: 11, fontWeight: 600, background: catFilter === c ? (CAT_COLOR[c] || '#10b981') : '#1e2535', color: catFilter === c ? '#fff' : '#9ca3af', transition: 'all .15s' }}>{c}</span>
          ))}
        </div>
        {filtered.length === 0 ? <Empty text="No templates yet — add one on the left or use AI Suggest." /> : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {filtered.map(item => (
              <div key={item.id} style={{ background: '#0f1117', borderRadius: 8, padding: '12px 14px', border: '1px solid #1e2535' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                  <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                    <span style={{ background: CAT_COLOR[item.category] || '#6b7280', color: '#fff', fontSize: 10, fontWeight: 700, borderRadius: 4, padding: '2px 7px' }}>{item.category}</span>
                    <span style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 600 }}>{item.trigger}</span>
                  </div>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <span onClick={() => navigator.clipboard?.writeText(item.body)} title="Copy" style={{ cursor: 'pointer', color: '#6b7280', fontSize: 12, padding: '2px 6px', borderRadius: 4, background: '#1e2535' }}>Copy</span>
                    <span onClick={() => startEdit(item)} title="Edit" style={{ cursor: 'pointer', color: '#6b7280', fontSize: 12, padding: '2px 6px', borderRadius: 4, background: '#1e2535' }}>Edit</span>
                    <span onClick={() => del(item.id)} title="Delete" style={{ cursor: 'pointer', color: '#ef444480', fontSize: 12, padding: '2px 6px', borderRadius: 4, background: '#1e2535' }}>Del</span>
                  </div>
                </div>
                <div style={{ color: '#9ca3af', fontSize: 12, lineHeight: 1.5, maxHeight: 56, overflow: 'hidden' }}>{item.body}</div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </Row>
  )
}

export default function CustomerSupportPage() {
  const [tab, setTab]   = useState('faq')
  const [lang, setLang] = useState<Lang>('en')

  return (
    <PageShell title="Customer Support Agent" icon="cs">
      <div style={{ padding: '0 24px 8px', display: 'flex', alignItems: 'center', gap: 16 }}>
        <div style={{ color: '#6b7280', fontSize: 13 }}>Language:</div>
        <div style={{ display: 'flex', gap: 6 }}>
          {LANG_OPTIONS.map(opt => (
            <button key={opt.value} onClick={() => setLang(opt.value as Lang)} style={{
              padding: '4px 14px', borderRadius: 20, border: 'none', cursor: 'pointer',
              background: lang === opt.value ? '#10b981' : '#1e2535',
              color: lang === opt.value ? '#fff' : '#9ca3af',
              fontSize: 12, fontWeight: lang === opt.value ? 600 : 400, transition: 'all 0.15s',
            }}>
              {opt.label}
            </button>
          ))}
        </div>
      </div>
      <Tabs tabs={TABS} active={tab} onChange={setTab} />
      <div style={{ flex: 1, overflow: 'auto', padding: '0 24px 24px' }}>
        {tab === 'faq'       && <FaqTab lang={lang} />}
        {tab === 'whatsapp'  && <WhatsAppTab lang={lang} />}
        {tab === 'sentiment' && <SentimentTab lang={lang} />}
        {tab === 'complaint' && <ComplaintTab lang={lang} />}
        {tab === 'lead'      && <LeadTab lang={lang} />}
        {tab === 'ticket'    && <TicketTab lang={lang} />}
        {tab === 'template'  && <TemplateTab lang={lang} />}
        {tab === 'kb'        && <KBTab lang={lang} />}
        {tab === 'report'    && <ReportTab lang={lang} />}
        {tab === 'canned'    && <CannedTab lang={lang} />}
        {tab === 'sla'       && <SlaTab lang={lang} />}
        {tab === 'csat'      && <CsatTab lang={lang} />}
        {tab === 'escalation' && <EscalationTab lang={lang} />}
        {tab === 'churn'      && <ChurnRiskTab lang={lang} />}
        {tab === 'onboarding'  && <OnboardingTab lang={lang} />}
        {tab === 'categorizer' && <CategorizerTab lang={lang} />}
        {tab === 'rulebook'    && <EscalationRulebookTab lang={lang} />}
        {tab === 'health'      && <CustomerHealthTab lang={lang} />}
        {tab === 'winback'     && <WinbackTab lang={lang} />}
        {tab === 'scorecard'   && <AgentScorecardTab lang={lang} />}
      </div>
    </PageShell>
  )
}


// ── Escalation Manager (Round 6) ─────────────────────────────────────────────

const DEMO_ESC_TICKETS = [
  { id: 'T1001', subject: 'Complete data loss after your update!', customer_name: 'Rahul Sharma', customer_tier: 'Enterprise', status: 'open', priority: 'high', assignee: 'Priya K', created_at: new Date(Date.now() - 26 * 3600000).toISOString(), description: 'We lost 3 days of billing data after the forced update. This is unacceptable.', sentiment: 'very negative' },
  { id: 'T1002', subject: 'Refund not processed after 30 days', customer_name: 'Anita Menon', customer_tier: 'Premium', status: 'open', priority: 'medium', assignee: 'Dev S', created_at: new Date(Date.now() - 5 * 3600000).toISOString(), description: 'I requested a refund on 15th Jan and still no response. Double charge on my card.', sentiment: 'negative' },
  { id: 'T1003', subject: 'VIP account setup assistance needed', customer_name: 'CEO - TataGroup', customer_tier: 'VIP', status: 'open', priority: 'high', assignee: 'Unassigned', created_at: new Date(Date.now() - 2 * 3600000).toISOString(), description: 'Need dedicated onboarding support for our 500-seat enterprise deployment.' },
  { id: 'T1004', subject: 'Login page loading slow', customer_name: 'Karan Patel', customer_tier: 'Standard', status: 'open', priority: 'low', assignee: 'Tech Team', created_at: new Date(Date.now() - 1 * 3600000).toISOString(), description: 'Login page takes 8-10 seconds on mobile.' },
  { id: 'T1005', subject: 'Invoice export feature request', customer_name: 'Deepa R', customer_tier: 'Standard', status: 'resolved', priority: 'low', assignee: 'Meena L', created_at: new Date(Date.now() - 48 * 3600000).toISOString(), description: 'Can you add CSV export to the invoice module?' },
]

function EscalationTab({ lang }: { lang: Lang }) {
  const [escBusiness, setEscBusiness] = useState('')
  const [escEmail, setEscEmail]       = useState('')
  const [escJson, setEscJson]         = useState(JSON.stringify(DEMO_ESC_TICKETS, null, 2))
  const [escRes, setEscRes]           = useState<any>(null)
  const [escLoading, setEscLoading]   = useState(false)
  const [escErr, setEscErr]           = useState('')

  const runEscalation = async () => {
    setEscLoading(true); setEscErr(''); setEscRes(null)
    try {
      let tickets: any[]
      try { tickets = JSON.parse(escJson) } catch { throw new Error('Invalid JSON') }
      setEscRes(await csAction('escalation_manager', {
        tickets, business_name: escBusiness, escalation_email: escEmail, rules: {},
      }, lang))
    } catch (e: any) { setEscErr(e.message) }
    setEscLoading(false)
  }

  const PRIORITY_COLOR: Record<string, string> = { critical: '#ef4444', high: '#f97316', medium: '#f59e0b', low: '#22c55e' }

  return (
    <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>
      <div style={{ flex: '0 0 360px' }}>
        <div style={{ background: '#161b27', border: '1px solid #1e2535', borderRadius: 12, padding: 20 }}>
          <div style={{ fontSize: 15, fontWeight: 700, color: '#e2e8f0', marginBottom: 4 }}>Escalation Manager</div>
          <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 16 }}>Auto-detect tickets that need immediate attention</div>
          <div style={{ marginBottom: 10 }}>
            <div style={{ fontSize: 12, color: '#9ca3af', marginBottom: 4 }}>Business Name</div>
            <input value={escBusiness} onChange={e => setEscBusiness(e.target.value)} placeholder="e.g. Zoho Support" style={{ width: '100%', background: '#0f1117', color: '#e2e8f0', border: '1px solid #1e2535', borderRadius: 8, padding: '8px 12px', fontSize: 13, boxSizing: 'border-box' }} />
          </div>
          <div style={{ marginBottom: 10 }}>
            <div style={{ fontSize: 12, color: '#9ca3af', marginBottom: 4 }}>Escalation Email (for draft)</div>
            <input value={escEmail} onChange={e => setEscEmail(e.target.value)} placeholder="manager@company.com" style={{ width: '100%', background: '#0f1117', color: '#e2e8f0', border: '1px solid #1e2535', borderRadius: 8, padding: '8px 12px', fontSize: 13, boxSizing: 'border-box' }} />
          </div>
          <div style={{ fontSize: 12, color: '#9ca3af', marginBottom: 4 }}>Tickets JSON</div>
          <textarea value={escJson} onChange={e => setEscJson(e.target.value)} rows={12}
            style={{ width: '100%', background: '#0f1117', color: '#e2e8f0', border: '1px solid #1e2535', borderRadius: 8, padding: 10, fontSize: 11, fontFamily: 'monospace', resize: 'vertical', boxSizing: 'border-box' }} />
          <button onClick={runEscalation} disabled={escLoading} style={{
            marginTop: 12, width: '100%', padding: '10px 0', background: escLoading ? '#1e2535' : '#4f8ef7',
            color: '#fff', border: 'none', borderRadius: 8, fontWeight: 600, fontSize: 14, cursor: escLoading ? 'not-allowed' : 'pointer',
          }}>{escLoading ? 'Analysing…' : 'Run Escalation Analysis'}</button>
          {escErr && <div style={{ color: '#f59e0b', fontSize: 11, marginTop: 8 }}>Demo mode: {escErr}</div>}
        </div>
      </div>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 14 }}>
        {escRes ? (
          <>
            {/* Health bar */}
            <div style={{ background: '#161b27', border: `1px solid ${escRes.health_color === 'red' ? '#ef4444' : escRes.health_color === 'orange' ? '#f97316' : '#22c55e'}44`, borderRadius: 12, padding: 16, display: 'flex', gap: 20, alignItems: 'center', flexWrap: 'wrap' }}>
              <div>
                <div style={{ fontSize: 11, color: '#6b7280' }}>Status</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: escRes.health_color === 'red' ? '#ef4444' : escRes.health_color === 'orange' ? '#f97316' : '#22c55e' }}>{escRes.health}</div>
              </div>
              {[
                { label: 'Total', val: escRes.stats?.total },
                { label: 'Escalated', val: escRes.stats?.escalated, color: '#f97316' },
                { label: 'Critical', val: escRes.stats?.critical, color: '#ef4444' },
                { label: 'Resolved', val: escRes.stats?.resolved, color: '#22c55e' },
              ].map(k => (
                <div key={k.label} style={{ background: '#0f1117', borderRadius: 8, padding: '8px 14px', textAlign: 'center' }}>
                  <div style={{ fontSize: 20, fontWeight: 700, color: k.color || '#e2e8f0' }}>{k.val ?? 0}</div>
                  <div style={{ fontSize: 11, color: '#6b7280' }}>{k.label}</div>
                </div>
              ))}
            </div>

            {/* Escalated tickets */}
            {(escRes.escalated || []).length > 0 && (
              <div style={{ background: '#161b27', border: '1px solid #1e2535', borderRadius: 12, padding: 16 }}>
                <div style={{ fontSize: 14, fontWeight: 700, color: '#e2e8f0', marginBottom: 12 }}>Escalated Tickets ({escRes.escalated.length})</div>
                {escRes.escalated.map((t: any) => (
                  <div key={t.id} style={{ background: '#0f1117', border: `1px solid ${PRIORITY_COLOR[t.priority] || '#1e2535'}55`, borderRadius: 8, padding: 12, marginBottom: 8 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 4 }}>
                      <div>
                        <span style={{ fontWeight: 600, color: '#e2e8f0', fontSize: 13 }}>[{t.id}] {t.subject}</span>
                        <div style={{ fontSize: 11, color: '#6b7280', marginTop: 2 }}>{t.customer} · {t.customer_tier} · {t.hours_open}h open · {t.assignee}</div>
                      </div>
                      <Badge label={t.priority.toUpperCase()} color={PRIORITY_COLOR[t.priority] || '#6b7280'} />
                    </div>
                    <div style={{ fontSize: 12, color: '#f59e0b', margin: '6px 0' }}>⚠ {t.action_needed}</div>
                    <div style={{ fontSize: 11, color: '#4b5563' }}>Trigger: {(t.reason || '').replace(/_/g, ' ')}</div>
                  </div>
                ))}
              </div>
            )}

            {/* Email draft */}
            {escRes.email_draft && (
              <div style={{ background: '#161b27', border: '1px solid #1e2535', borderRadius: 12, padding: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: '#e2e8f0' }}>Escalation Email Draft</div>
                  <span onClick={() => navigator.clipboard?.writeText(escRes.email_draft)} style={{ cursor: 'pointer', fontSize: 11, padding: '3px 10px', background: '#374151', color: '#fff', borderRadius: 6 }}>Copy</span>
                </div>
                <pre style={{ color: '#9ca3af', fontSize: 12, whiteSpace: 'pre-wrap', margin: 0, fontFamily: 'inherit', lineHeight: 1.7 }}>{escRes.email_draft}</pre>
              </div>
            )}

            {/* Monitored */}
            {(escRes.monitored || []).length > 0 && (
              <div style={{ background: '#161b27', border: '1px solid #1e2535', borderRadius: 12, padding: 16 }}>
                <div style={{ fontSize: 14, fontWeight: 600, color: '#9ca3af', marginBottom: 8 }}>Monitoring ({escRes.monitored.length} tickets)</div>
                {escRes.monitored.map((t: any) => (
                  <div key={t.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '7px 0', borderBottom: '1px solid #0f1117', fontSize: 12 }}>
                    <span style={{ color: '#9ca3af' }}>[{t.id}] {t.subject.slice(0, 50)}</span>
                    <span style={{ color: '#6b7280' }}>{t.hours_open}h</span>
                  </div>
                ))}
              </div>
            )}
          </>
        ) : (
          <Empty text="Load demo tickets or paste your own JSON, then click Run Escalation Analysis →" />
        )}
      </div>
    </div>
  )
}


// ── Churn Risk Analyzer (Round 7) ─────────────────────────────────────────────

const DEMO_CHURN_CUSTOMERS = [
  { id: 'C001', name: 'TechCorp India', tier: 'Enterprise', mrr: 45000, no_login_days: 22, support_tickets_month: 5, nps_score: 4, contract_days_left: 18, feature_usage_drop_pct: 65 },
  { id: 'C002', name: 'Sharma Exports', tier: 'Premium',    mrr: 12000, no_login_days: 8,  support_tickets_month: 1, nps_score: 8, contract_days_left: 90, feature_usage_drop_pct: 10 },
  { id: 'C003', name: 'Ravi Consulting',tier: 'Standard',   mrr: 3500,  no_login_days: 35, payment_failed: true, support_tickets_month: 4, competitor_mention: true },
  { id: 'C004', name: 'Kiran Solutions',tier: 'Standard',   mrr: 4000,  no_login_days: 3,  support_tickets_month: 0, nps_score: 9 },
  { id: 'C005', name: 'PrimeRetail Ltd',tier: 'Premium',    mrr: 18000, downgrade_request: true, nps_score: 5, feature_usage_drop_pct: 70 },
]

function ChurnRiskTab({ lang }: { lang: Lang }) {
  const [churnBiz, setChurnBiz]       = useState('')
  const [churnIndustry, setChurnIndustry] = useState('saas')
  const [churnJson, setChurnJson]     = useState(JSON.stringify(DEMO_CHURN_CUSTOMERS, null, 2))
  const [churnRes, setChurnRes]       = useState<any>(null)
  const [churnLoading, setChurnLoading] = useState(false)
  const [churnErr, setChurnErr]       = useState('')
  const [expanded, setExpanded]       = useState<string | null>(null)

  const runChurn = async () => {
    setChurnLoading(true); setChurnErr(''); setChurnRes(null)
    try {
      let customers: any[]
      try { customers = JSON.parse(churnJson) } catch { throw new Error('Invalid JSON') }
      setChurnRes(await csAction('churn_risk', { customers, business_name: churnBiz, industry: churnIndustry }, lang))
    } catch (e: any) { setChurnErr(e.message) }
    setChurnLoading(false)
  }

  const RISK_COLOR: Record<string, string> = { Critical: '#ef4444', High: '#f97316', Medium: '#f59e0b', Low: '#22c55e' }

  return (
    <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>
      <div style={{ flex: '0 0 340px' }}>
        <div style={{ background: '#161b27', border: '1px solid #1e2535', borderRadius: 12, padding: 20 }}>
          <div style={{ fontSize: 15, fontWeight: 700, color: '#e2e8f0', marginBottom: 4 }}>Churn Risk Analyzer</div>
          <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 16 }}>Score every customer — find who's about to leave before they do</div>
          <div style={{ marginBottom: 10 }}>
            <div style={{ fontSize: 12, color: '#9ca3af', marginBottom: 4 }}>Business Name</div>
            <input value={churnBiz} onChange={e => setChurnBiz(e.target.value)} placeholder="e.g. Freshdesk" style={{ width: '100%', background: '#0f1117', color: '#e2e8f0', border: '1px solid #1e2535', borderRadius: 8, padding: '8px 12px', fontSize: 13, boxSizing: 'border-box' }} />
          </div>
          <div style={{ marginBottom: 10 }}>
            <div style={{ fontSize: 12, color: '#9ca3af', marginBottom: 4 }}>Industry</div>
            <select value={churnIndustry} onChange={e => setChurnIndustry(e.target.value)} style={{ width: '100%', background: '#0f1117', color: '#e2e8f0', border: '1px solid #1e2535', borderRadius: 8, padding: '8px 12px', fontSize: 13 }}>
              {['saas', 'ecommerce', 'fintech', 'healthcare', 'education', 'retail'].map(v => <option key={v} value={v}>{v.charAt(0).toUpperCase() + v.slice(1)}</option>)}
            </select>
          </div>
          <div style={{ fontSize: 12, color: '#9ca3af', marginBottom: 4 }}>Customers JSON</div>
          <textarea value={churnJson} onChange={e => setChurnJson(e.target.value)} rows={12}
            style={{ width: '100%', background: '#0f1117', color: '#e2e8f0', border: '1px solid #1e2535', borderRadius: 8, padding: 10, fontSize: 11, fontFamily: 'monospace', resize: 'vertical', boxSizing: 'border-box' }} />
          <button onClick={runChurn} disabled={churnLoading} style={{
            marginTop: 12, width: '100%', padding: '10px 0', background: churnLoading ? '#1e2535' : '#4f8ef7',
            color: '#fff', border: 'none', borderRadius: 8, fontWeight: 600, fontSize: 14, cursor: churnLoading ? 'not-allowed' : 'pointer',
          }}>{churnLoading ? 'Analysing…' : 'Analyse Churn Risk'}</button>
          {churnErr && <div style={{ color: '#f59e0b', fontSize: 11, marginTop: 8 }}>{churnErr}</div>}
        </div>
      </div>

      <div style={{ flex: 1 }}>
        {churnRes ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {/* Health bar */}
            <div style={{ background: '#161b27', border: `1px solid ${churnRes.health_color === 'red' ? '#ef4444' : churnRes.health_color === 'orange' ? '#f97316' : '#22c55e'}44`, borderRadius: 12, padding: 16, display: 'flex', gap: 20, alignItems: 'center', flexWrap: 'wrap' }}>
              <div>
                <div style={{ fontSize: 11, color: '#6b7280' }}>Portfolio Health</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: churnRes.health_color === 'red' ? '#ef4444' : churnRes.health_color === 'orange' ? '#f97316' : '#22c55e' }}>{churnRes.health}</div>
              </div>
              {[
                { label: 'Analyzed', val: churnRes.total_analyzed },
                { label: 'Critical', val: churnRes.critical_count, color: '#ef4444' },
                { label: 'High Risk', val: churnRes.high_count, color: '#f97316' },
                { label: 'ARR at Risk', val: `₹${((churnRes.arr_at_risk || 0) / 100000).toFixed(1)}L`, color: '#ef4444' },
              ].map(k => (
                <div key={k.label} style={{ background: '#0f1117', borderRadius: 8, padding: '8px 14px', textAlign: 'center' }}>
                  <div style={{ fontSize: 18, fontWeight: 700, color: k.color || '#e2e8f0' }}>{k.val}</div>
                  <div style={{ fontSize: 11, color: '#6b7280' }}>{k.label}</div>
                </div>
              ))}
            </div>

            {/* Customer cards */}
            <div style={{ background: '#161b27', border: '1px solid #1e2535', borderRadius: 12, padding: 16 }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#e2e8f0', marginBottom: 12 }}>Customers by Churn Risk</div>
              {(churnRes.customers || []).map((c: any) => {
                const isOpen = expanded === c.id
                return (
                  <div key={c.id} style={{ background: '#0f1117', border: `1px solid ${RISK_COLOR[c.risk_level] || '#1e2535'}44`, borderRadius: 8, padding: 12, marginBottom: 8, cursor: 'pointer' }}
                    onClick={() => setExpanded(isOpen ? null : c.id)}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <span style={{ fontWeight: 600, color: '#e2e8f0', fontSize: 13 }}>{c.name}</span>
                        <span style={{ fontSize: 11, color: '#6b7280', marginLeft: 8 }}>{c.tier} · MRR ₹{(c.mrr || 0).toLocaleString('en-IN')}</span>
                      </div>
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        <div style={{ fontSize: 18, fontWeight: 800, color: RISK_COLOR[c.risk_level] }}>{c.churn_score}%</div>
                        <Badge label={c.risk_level} color={RISK_COLOR[c.risk_level] || '#6b7280'} />
                      </div>
                    </div>
                    {/* Score bar */}
                    <div style={{ height: 4, background: '#1e2535', borderRadius: 2, margin: '8px 0' }}>
                      <div style={{ height: '100%', width: `${c.churn_score}%`, background: RISK_COLOR[c.risk_level], borderRadius: 2, transition: 'width 0.5s' }} />
                    </div>
                    {isOpen && (
                      <>
                        <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 6 }}>Risk Triggers:</div>
                        {(c.triggers || []).map((t: string, i: number) => (
                          <div key={i} style={{ fontSize: 12, color: '#f97316', marginBottom: 3 }}>⚠ {t}</div>
                        ))}
                        <div style={{ fontSize: 12, color: '#6b7280', marginTop: 10, marginBottom: 6 }}>Win-back Actions:</div>
                        {(c.winback_actions || []).map((a: string, i: number) => (
                          <div key={i} style={{ fontSize: 12, color: '#9ca3af', marginBottom: 4, display: 'flex', gap: 6 }}>
                            <span style={{ color: '#818cf8' }}>→</span>{a}
                          </div>
                        ))}
                        <div style={{ fontSize: 12, color: '#ef4444', marginTop: 8, fontWeight: 600 }}>
                          ARR at risk: ₹{((c.revenue_at_risk || 0)).toLocaleString('en-IN')}
                        </div>
                      </>
                    )}
                    {!isOpen && (c.triggers || []).length > 0 && (
                      <div style={{ fontSize: 11, color: '#4b5563' }}>{(c.triggers || []).length} triggers · click to expand</div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        ) : (
          <Empty text="Demo data is pre-loaded — click Analyse Churn Risk to see results →" />
        )}
      </div>
    </div>
  )
}


// ── Customer Onboarding Planner (Round 8) ────────────────────────────────────

function OnboardingTab({ lang }: { lang: Lang }) {
  const [obCustomer, setObCustomer] = useState('')
  const [obProduct, setObProduct]   = useState('')
  const [obIndustry, setObIndustry] = useState('')
  const [obTier, setObTier]         = useState('standard')
  const [obTeam, setObTeam]         = useState('5')
  const [obGoals, setObGoals]       = useState('improve efficiency, reduce manual work, scale operations')
  const [obRes, setObRes]           = useState<any>(null)
  const [obLoading, setObLoading]   = useState(false)
  const [obErr, setObErr]           = useState('')
  const [checkedTasks, setCheckedTasks] = useState<Record<string, boolean>>({})

  const toggleTask = (key: string) => setCheckedTasks(prev => ({ ...prev, [key]: !prev[key] }))

  const runOnboarding = async () => {
    setObLoading(true); setObErr(''); setObRes(null); setCheckedTasks({})
    try {
      setObRes(await csAction('onboarding_planner', {
        customer_name: obCustomer, product_name: obProduct, industry: obIndustry,
        tier: obTier, team_size: parseInt(obTeam) || 1,
        goals: obGoals.split(',').map(g => g.trim()).filter(Boolean),
      }, lang))
    } catch (e: any) { setObErr(e.message) }
    setObLoading(false)
  }

  const TIER_COLOR: Record<string, string> = { standard: '#6b7280', premium: '#818cf8', enterprise: '#f59e0b', vip: '#f59e0b' }

  return (
    <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>
      <div style={{ flex: '0 0 340px' }}>
        <div style={{ background: '#161b27', border: '1px solid #1e2535', borderRadius: 12, padding: 20 }}>
          <div style={{ fontSize: 15, fontWeight: 700, color: '#e2e8f0', marginBottom: 4 }}>Onboarding Planner</div>
          <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 16 }}>Generate a personalised, tier-based onboarding plan for any new customer</div>
          {[
            { label: 'Customer / Company Name', val: obCustomer, set: setObCustomer, ph: 'e.g. TechCorp India' },
            { label: 'Your Product Name', val: obProduct, set: setObProduct, ph: 'e.g. Freshdesk, Zoho CRM' },
            { label: 'Customer Industry', val: obIndustry, set: setObIndustry, ph: 'e.g. E-commerce, Healthcare' },
            { label: 'Team Size', val: obTeam, set: setObTeam, ph: 'e.g. 15' },
          ].map(f => (
            <div key={f.label} style={{ marginBottom: 10 }}>
              <div style={{ fontSize: 12, color: '#9ca3af', marginBottom: 4 }}>{f.label}</div>
              <input value={f.val} onChange={e => f.set(e.target.value)} placeholder={f.ph}
                style={{ width: '100%', background: '#0f1117', color: '#e2e8f0', border: '1px solid #1e2535', borderRadius: 8, padding: '8px 12px', fontSize: 13, boxSizing: 'border-box' }} />
            </div>
          ))}
          <div style={{ marginBottom: 10 }}>
            <div style={{ fontSize: 12, color: '#9ca3af', marginBottom: 4 }}>Customer Tier</div>
            <select value={obTier} onChange={e => setObTier(e.target.value)} style={{ width: '100%', background: '#0f1117', color: '#e2e8f0', border: '1px solid #1e2535', borderRadius: 8, padding: '8px 12px', fontSize: 13 }}>
              <option value="standard">Standard (30-day plan)</option>
              <option value="premium">Premium (30-day intensive)</option>
              <option value="enterprise">Enterprise (90-day full rollout)</option>
            </select>
          </div>
          <div style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 12, color: '#9ca3af', marginBottom: 4 }}>Customer Goals (comma-separated)</div>
            <textarea value={obGoals} onChange={e => setObGoals(e.target.value)} rows={2}
              style={{ width: '100%', background: '#0f1117', color: '#e2e8f0', border: '1px solid #1e2535', borderRadius: 8, padding: 10, fontSize: 12, resize: 'vertical', boxSizing: 'border-box' }} />
          </div>
          <button onClick={runOnboarding} disabled={obLoading} style={{
            width: '100%', padding: '10px 0', background: obLoading ? '#1e2535' : '#4f8ef7',
            color: '#fff', border: 'none', borderRadius: 8, fontWeight: 600, fontSize: 14, cursor: obLoading ? 'not-allowed' : 'pointer',
          }}>{obLoading ? 'Building plan…' : 'Generate Onboarding Plan'}</button>
          {obErr && <div style={{ color: '#f59e0b', fontSize: 11, marginTop: 8 }}>{obErr}</div>}
        </div>
      </div>

      <div style={{ flex: 1 }}>
        {obRes ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div style={{ background: '#161b27', border: '1px solid #1e2535', borderRadius: 12, padding: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                <div>
                  <div style={{ fontSize: 16, fontWeight: 700, color: '#e2e8f0' }}>{obRes.customer_name || 'Customer'} Onboarding Plan</div>
                  <div style={{ fontSize: 12, color: '#6b7280', marginTop: 2 }}>{obRes.product_name} · {obRes.team_size} people · {obRes.duration_days}-day plan</div>
                </div>
                <Badge label={(obRes.tier || '').toUpperCase()} color={TIER_COLOR[obRes.tier] || '#6b7280'} />
              </div>
              <div style={{ display: 'flex', gap: 10 }}>
                {[
                  { label: 'Total Tasks', val: obRes.total_tasks },
                  { label: 'Duration', val: `${obRes.duration_days} days` },
                  { label: 'CSM', val: (obRes.assigned_csm || '').includes('Dedicated') ? 'Dedicated' : 'Shared' },
                ].map(k => (
                  <div key={k.label} style={{ flex: 1, background: '#0f1117', borderRadius: 8, padding: '8px 12px', textAlign: 'center' }}>
                    <div style={{ fontSize: 16, fontWeight: 700, color: '#e2e8f0' }}>{k.val}</div>
                    <div style={{ fontSize: 11, color: '#6b7280' }}>{k.label}</div>
                  </div>
                ))}
              </div>
            </div>

            {(obRes.phases || []).map((phase: any, pi: number) => {
              const done = phase.tasks.filter((_: any, ti: number) => checkedTasks[`${pi}-${ti}`]).length
              return (
                <div key={pi} style={{ background: '#161b27', border: '1px solid #1e2535', borderRadius: 12, padding: 16 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                    <div>
                      <div style={{ fontSize: 14, fontWeight: 700, color: '#e2e8f0' }}>{phase.phase}</div>
                      <div style={{ fontSize: 11, color: '#6b7280' }}>{phase.days}</div>
                    </div>
                    <div style={{ fontSize: 12, color: done === phase.tasks.length ? '#22c55e' : '#9ca3af' }}>{done}/{phase.tasks.length} done</div>
                  </div>
                  {phase.tasks.map((task: string, ti: number) => {
                    const key = `${pi}-${ti}`
                    return (
                      <div key={ti} onClick={() => toggleTask(key)} style={{ display: 'flex', gap: 10, padding: '7px 0', borderBottom: '1px solid #0f1117', cursor: 'pointer', alignItems: 'flex-start' }}>
                        <span style={{ fontSize: 14, flexShrink: 0, marginTop: 1 }}>{checkedTasks[key] ? '✅' : '⬜'}</span>
                        <span style={{ fontSize: 13, color: checkedTasks[key] ? '#4b5563' : '#9ca3af', textDecoration: checkedTasks[key] ? 'line-through' : 'none' }}>{task}</span>
                      </div>
                    )
                  })}
                </div>
              )
            })}

            <div style={{ display: 'flex', gap: 14 }}>
              <div style={{ flex: 1, background: '#161b27', border: '1px solid #1e2535', borderRadius: 12, padding: 16 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: '#e2e8f0', marginBottom: 10 }}>Check-in Schedule</div>
                {(obRes.health_check_schedule || []).map((h: any, i: number) => (
                  <div key={i} style={{ display: 'flex', gap: 8, padding: '6px 0', borderBottom: '1px solid #0f1117', fontSize: 12 }}>
                    <Badge label={`Day ${h.day}`} color="#818cf8" />
                    <div>
                      <div style={{ color: '#e2e8f0' }}>{h.type}</div>
                      <div style={{ color: '#6b7280', fontSize: 11 }}>{h.focus}</div>
                    </div>
                  </div>
                ))}
              </div>
              <div style={{ flex: 1, background: '#161b27', border: '1px solid #1e2535', borderRadius: 12, padding: 16 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: '#e2e8f0', marginBottom: 10 }}>Success Metrics</div>
                {(obRes.success_metrics || []).map((m: any, i: number) => (
                  <div key={i} style={{ padding: '6px 0', borderBottom: '1px solid #0f1117', fontSize: 12 }}>
                    <div style={{ color: '#22c55e', fontWeight: 600 }}>{m.metric}</div>
                    <div style={{ color: '#6b7280', fontSize: 11 }}>Target: {m.target}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <Empty text="Fill in customer details and click Generate Onboarding Plan →" />
        )}
      </div>
    </div>
  )
}


// ── Ticket Auto-Categorizer (Round 9) ────────────────────────────────────────

const DEMO_TICKETS_CAT = [
  { id: 'T001', subject: 'Cannot login — password reset not working', description: 'I have tried resetting my password 3 times but the email never arrives. Urgent!' },
  { id: 'T002', subject: 'Invoice shows wrong amount', description: 'I was charged Rs.5,000 but my plan is Rs.2,500. Please refund the extra charge immediately.' },
  { id: 'T003', subject: 'API webhook not firing', description: 'Our Zapier integration broke after the latest update. Webhooks not triggering at all.' },
  { id: 'T004', subject: 'How do I export data to Excel?', description: 'New user here — trying to figure out how to export my reports to Excel format.' },
  { id: 'T005', subject: 'This product is absolutely terrible!', description: 'I have had 5 bugs in 3 days. This is completely unacceptable. I want a full refund or going to social media.' },
]

const URGENCY_COLOR: Record<string, string> = { critical: '#ef4444', high: '#f97316', medium: '#f59e0b', low: '#22c55e' }

function CategorizerTab({ lang }: { lang: Lang }) {
  const [catBiz, setCatBiz]     = useState('')
  const [catJson, setCatJson]   = useState(JSON.stringify(DEMO_TICKETS_CAT, null, 2))
  const [catRes, setCatRes]     = useState<any>(null)
  const [catLoading, setCatLoading] = useState(false)
  const [catErr, setCatErr]     = useState('')
  const [expanded, setExpanded] = useState<string | null>(null)

  const runCategorizer = async () => {
    setCatLoading(true); setCatErr(''); setCatRes(null)
    try {
      let tickets: any[]
      try { tickets = JSON.parse(catJson) } catch { throw new Error('Invalid JSON') }
      setCatRes(await csAction('ticket_categorizer', { tickets, business_name: catBiz }, lang))
    } catch (e: any) { setCatErr(e.message) }
    setCatLoading(false)
  }

  return (
    <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>
      <div style={{ flex: '0 0 340px' }}>
        <div style={{ background: '#161b27', border: '1px solid #1e2535', borderRadius: 12, padding: 20 }}>
          <div style={{ fontSize: 15, fontWeight: 700, color: '#e2e8f0', marginBottom: 4 }}>Ticket Auto-Categorizer</div>
          <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 16 }}>Auto-assign category, team, priority and SLA to every ticket instantly</div>
          <div style={{ marginBottom: 10 }}>
            <div style={{ fontSize: 12, color: '#9ca3af', marginBottom: 4 }}>Business Name</div>
            <input value={catBiz} onChange={e => setCatBiz(e.target.value)} placeholder="e.g. Freshdesk" style={{ width: '100%', background: '#0f1117', color: '#e2e8f0', border: '1px solid #1e2535', borderRadius: 8, padding: '8px 12px', fontSize: 13, boxSizing: 'border-box' }} />
          </div>
          <div style={{ fontSize: 12, color: '#9ca3af', marginBottom: 4 }}>Tickets JSON</div>
          <textarea value={catJson} onChange={e => setCatJson(e.target.value)} rows={14}
            style={{ width: '100%', background: '#0f1117', color: '#e2e8f0', border: '1px solid #1e2535', borderRadius: 8, padding: 10, fontSize: 11, fontFamily: 'monospace', resize: 'vertical', boxSizing: 'border-box' }} />
          <button onClick={runCategorizer} disabled={catLoading} style={{
            marginTop: 10, width: '100%', padding: '10px 0', background: catLoading ? '#1e2535' : '#4f8ef7',
            color: '#fff', border: 'none', borderRadius: 8, fontWeight: 600, fontSize: 14, cursor: catLoading ? 'not-allowed' : 'pointer',
          }}>{catLoading ? 'Categorizing…' : 'Auto-Categorize Tickets'}</button>
          {catErr && <div style={{ color: '#f59e0b', fontSize: 11, marginTop: 8 }}>{catErr}</div>}
        </div>
      </div>

      <div style={{ flex: 1 }}>
        {catRes ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {/* Summary */}
            <div style={{ background: '#161b27', border: '1px solid #1e2535', borderRadius: 12, padding: 16, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              {[
                { label: 'Total', val: catRes.total_tickets },
                { label: 'Critical', val: catRes.urgency_breakdown?.critical || 0, color: '#ef4444' },
                { label: 'High', val: catRes.urgency_breakdown?.high || 0, color: '#f97316' },
                { label: 'Categories', val: (catRes.category_breakdown || []).length },
              ].map(k => (
                <div key={k.label} style={{ background: '#0f1117', borderRadius: 8, padding: '8px 16px', textAlign: 'center' }}>
                  <div style={{ fontSize: 20, fontWeight: 700, color: k.color || '#e2e8f0' }}>{k.val}</div>
                  <div style={{ fontSize: 11, color: '#6b7280' }}>{k.label}</div>
                </div>
              ))}
              <div style={{ flex: 1, display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
                {(catRes.category_breakdown || []).map((c: any) => (
                  <div key={c.category} style={{ fontSize: 11, padding: '3px 10px', background: '#1e2535', color: '#9ca3af', borderRadius: 20 }}>
                    {c.category} ({c.count})
                  </div>
                ))}
              </div>
            </div>

            {/* Ticket cards */}
            <div style={{ background: '#161b27', border: '1px solid #1e2535', borderRadius: 12, padding: 16 }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#e2e8f0', marginBottom: 12 }}>Categorized Tickets (Priority Order)</div>
              {(catRes.tickets || []).map((t: any) => {
                const isOpen = expanded === t.id
                return (
                  <div key={t.id} onClick={() => setExpanded(isOpen ? null : t.id)}
                    style={{ background: '#0f1117', border: `1px solid ${t.category_color || '#1e2535'}33`, borderRadius: 8, padding: 12, marginBottom: 8, cursor: 'pointer' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 4 }}>
                      <div>
                        <span style={{ fontWeight: 600, color: '#e2e8f0', fontSize: 13 }}>[{t.id}] {t.subject}</span>
                        <div style={{ fontSize: 11, color: '#6b7280', marginTop: 2 }}>→ {t.team} · SLA: {t.sla_hours}h</div>
                      </div>
                      <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                        <span style={{ fontSize: 11, padding: '2px 8px', background: `${t.category_color || '#6b7280'}22`, color: t.category_color || '#6b7280', borderRadius: 6, fontWeight: 600 }}>{t.category}</span>
                        <Badge label={t.urgency.toUpperCase()} color={URGENCY_COLOR[t.urgency] || '#6b7280'} />
                      </div>
                    </div>
                    {isOpen && (
                      <>
                        <div style={{ fontSize: 12, color: '#6b7280', margin: '8px 0 4px' }}>Resolution Steps:</div>
                        {(t.resolution_steps || []).map((s: string, i: number) => (
                          <div key={i} style={{ fontSize: 12, color: '#9ca3af', padding: '3px 0', display: 'flex', gap: 6 }}>
                            <span style={{ color: '#818cf8' }}>{i + 1}.</span>{s}
                          </div>
                        ))}
                        <div style={{ marginTop: 10, background: '#161b27', borderRadius: 6, padding: '8px 12px', fontSize: 12 }}>
                          <div style={{ color: '#6b7280', marginBottom: 3 }}>Auto-reply draft:</div>
                          <div style={{ color: '#9ca3af' }}>{t.auto_reply}</div>
                          <span onClick={e => { e.stopPropagation(); navigator.clipboard?.writeText(t.auto_reply) }}
                            style={{ cursor: 'pointer', fontSize: 11, marginTop: 6, display: 'inline-block', padding: '2px 8px', background: '#374151', color: '#fff', borderRadius: 4 }}>Copy</span>
                        </div>
                      </>
                    )}
                    {!isOpen && <div style={{ fontSize: 11, color: '#4b5563', marginTop: 2 }}>Click to see steps & auto-reply</div>}
                  </div>
                )
              })}
            </div>
          </div>
        ) : (
          <Empty text="Demo tickets pre-loaded — click Auto-Categorize to see results →" />
        )}
      </div>
    </div>
  )
}

// ── Escalation Rulebook Tab (Round 10) ───────────────────────────────────────

function EscalationRulebookTab({ lang }: { lang: Lang }) {
  const [biz, setBiz]           = useState('Acme SaaS')
  const [industry, setIndustry] = useState('saas')
  const [slaTier, setSlaTier]   = useState('standard')
  const [products, setProducts] = useState('Core Platform, Mobile App')
  const [res, setRes]           = useState<any>(null)
  const [loading, setLoading]   = useState(false)
  const [err, setErr]           = useState('')
  const [copyMsg, setCopyMsg]   = useState('')

  const run = async () => {
    setLoading(true); setErr(''); setRes(null)
    try {
      const r = await csAction('escalation_rule_builder', {
        business_name: biz, industry, sla_tier: slaTier,
        products: products.split(',').map(s => s.trim()).filter(Boolean),
        team_structure: [],
      }, lang)
      setRes(r)
    } catch (e: any) { setErr(e.message) }
    finally { setLoading(false) }
  }

  const copyTemplate = (text: string) => {
    navigator.clipboard?.writeText(text)
    setCopyMsg('Copied!'); setTimeout(() => setCopyMsg(''), 1500)
  }

  const PRIORITY_COLOR: Record<string, string> = { critical: '#ef4444', high: '#f97316', medium: '#f59e0b', low: '#22c55e' }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.6fr', gap: 16 }}>
      <div>
        <Card>
          <SectionHead title="Escalation Rulebook Builder" sub="Generate a complete SLA + routing matrix for your support team" />
          <div style={{ marginBottom: 10 }}>
            <label style={{ fontSize: 12, color: '#9ca3af', display: 'block', marginBottom: 4 }}>Business Name</label>
            <input value={biz} onChange={e => setBiz(e.target.value)} placeholder="e.g. Acme SaaS" style={{ width: '100%', background: '#1e2535', border: '1px solid #374151', borderRadius: 6, padding: '7px 10px', color: '#e2e8f0', fontSize: 13, boxSizing: 'border-box' }} />
          </div>
          <div style={{ marginBottom: 10 }}>
            <label style={{ fontSize: 12, color: '#9ca3af', display: 'block', marginBottom: 4 }}>Industry</label>
            <select value={industry} onChange={e => setIndustry(e.target.value)} style={{ width: '100%', background: '#1e2535', border: '1px solid #374151', borderRadius: 6, padding: '7px 10px', color: '#e2e8f0', fontSize: 13, boxSizing: 'border-box' }}>
              <option value="saas">SaaS / Software</option>
              <option value="ecommerce">E-Commerce / Retail</option>
              <option value="default">General Business</option>
            </select>
          </div>
          <div style={{ marginBottom: 10 }}>
            <label style={{ fontSize: 12, color: '#9ca3af', display: 'block', marginBottom: 4 }}>SLA Tier</label>
            <select value={slaTier} onChange={e => setSlaTier(e.target.value)} style={{ width: '100%', background: '#1e2535', border: '1px solid #374151', borderRadius: 6, padding: '7px 10px', color: '#e2e8f0', fontSize: 13, boxSizing: 'border-box' }}>
              <option value="startup">Startup (lean SLAs)</option>
              <option value="standard">Standard (growing team)</option>
              <option value="enterprise">Enterprise (strict SLAs)</option>
            </select>
          </div>
          <div style={{ marginBottom: 14 }}>
            <label style={{ fontSize: 12, color: '#9ca3af', display: 'block', marginBottom: 4 }}>Products (comma-separated)</label>
            <input value={products} onChange={e => setProducts(e.target.value)} placeholder="e.g. Core Platform, Mobile App" style={{ width: '100%', background: '#1e2535', border: '1px solid #374151', borderRadius: 6, padding: '7px 10px', color: '#e2e8f0', fontSize: 13, boxSizing: 'border-box' }} />
          </div>
          <button onClick={run} disabled={loading} style={{ width: '100%', padding: '10px 0', background: loading ? '#374151' : '#10b981', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', fontSize: 14 }}>
            {loading ? 'Building Rulebook…' : 'Build Escalation Rulebook'}
          </button>
          {err && <div style={{ color: '#ef4444', fontSize: 12, marginTop: 8 }}>{err}</div>}
          {copyMsg && <div style={{ color: '#22c55e', fontSize: 12, marginTop: 6, textAlign: 'center' }}>{copyMsg}</div>}
        </Card>
      </div>
      <div>
        {res ? (
          <>
            {/* Priority Matrix */}
            <Card style={{ marginBottom: 12 }}>
              <SectionHead title="Priority Escalation Matrix" sub={`${res.sla_tier} SLA profile — ${res.business_name}`} />
              {(res.escalation_matrix || []).map((row: any) => (
                <div key={row.priority} style={{ border: `1px solid ${PRIORITY_COLOR[row.priority] || '#374151'}`, borderRadius: 8, padding: '12px 14px', marginBottom: 8, background: '#0f1117' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <span style={{ color: PRIORITY_COLOR[row.priority], fontWeight: 700, fontSize: 14, textTransform: 'uppercase' }}>{row.priority}</span>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <Badge label={`1st resp: ${row.first_response}`} color="#818cf8" />
                      <Badge label={`Resolve: ${row.resolution_sla}`} color="#6b7280" />
                    </div>
                  </div>
                  <div style={{ fontSize: 12, color: '#9ca3af', marginBottom: 6 }}>Breach action: <span style={{ color: '#e2e8f0' }}>{row.breach_action}</span></div>
                  <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                    {(row.trigger_keywords || []).map((kw: string) => (
                      <span key={kw} style={{ fontSize: 10, padding: '2px 8px', borderRadius: 10, background: 'rgba(255,255,255,0.05)', color: '#9ca3af', border: '1px solid #374151' }}>{kw}</span>
                    ))}
                  </div>
                </div>
              ))}
            </Card>

            {/* Routing Teams */}
            <Card style={{ marginBottom: 12 }}>
              <SectionHead title="Routing Teams" sub="Who handles what — in order of escalation" />
              {(res.routing_teams || []).map((team: any, i: number) => (
                <div key={i} style={{ background: '#111827', border: '1px solid #1e2535', borderRadius: 8, padding: '10px 14px', marginBottom: 8 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                    <span style={{ color: '#e2e8f0', fontWeight: 600, fontSize: 13 }}>Tier {i + 1}: {team.name}</span>
                    <Badge label={`max: ${team.max_priority}`} color={PRIORITY_COLOR[team.max_priority] || '#6b7280'} />
                  </div>
                  <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                    {(team.handles || []).map((h: string) => <span key={h} style={{ fontSize: 11, color: '#6b7280', background: '#1e2535', borderRadius: 4, padding: '2px 8px' }}>{h}</span>)}
                  </div>
                </div>
              ))}
            </Card>

            {/* Notification Templates */}
            <Card style={{ marginBottom: 12 }}>
              <SectionHead title="Notification Templates" sub="Copy and configure in your helpdesk" />
              {Object.entries(res.notification_templates || {}).map(([key, text]: [string, any]) => (
                <div key={key} style={{ background: '#0f1117', border: '1px solid #1e2535', borderRadius: 8, padding: '10px 14px', marginBottom: 8 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                    <span style={{ fontSize: 11, color: '#a78bfa', fontWeight: 700, textTransform: 'uppercase' }}>{key.replace(/_/g, ' ')}</span>
                    <span onClick={() => copyTemplate(text)} style={{ fontSize: 11, cursor: 'pointer', color: '#fff', padding: '2px 10px', background: '#374151', borderRadius: 6 }}>Copy</span>
                  </div>
                  <div style={{ fontSize: 12, color: '#9ca3af', lineHeight: 1.5 }}>{text}</div>
                </div>
              ))}
            </Card>

            {/* Best Practices */}
            <Card>
              <SectionHead title="Best Practices" sub="Implementation checklist for your team" />
              {(res.best_practices || []).map((bp: string, i: number) => (
                <div key={i} style={{ fontSize: 13, color: '#e2e8f0', background: '#0f1117', borderRadius: 6, padding: '8px 12px', marginBottom: 6, borderLeft: '3px solid #10b981' }}>{bp}</div>
              ))}
            </Card>
          </>
        ) : (
          <Card>
            <Empty text="Demo values pre-filled — click Build Escalation Rulebook to generate your custom matrix →" />
          </Card>
        )}
      </div>
    </div>
  )
}

// ── Customer Health Score Tab (Round 11) ─────────────────────────────────────

function CustomerHealthTab({ lang }: { lang: Lang }) {
  const [biz, setBiz]         = useState('Acme SaaS')
  const [product, setProduct] = useState('Core Platform')
  const [jsonData, setJsonData] = useState('')
  const [res, setRes]         = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [err, setErr]         = useState('')
  const [selected, setSelected] = useState<number | null>(null)

  const run = async () => {
    setLoading(true); setErr(''); setRes(null)
    let customers: any[] = []
    try { if (jsonData.trim()) customers = JSON.parse(jsonData) } catch { setErr('Invalid JSON'); setLoading(false); return }
    try {
      const r = await csAction('customer_health_score', { business_name: biz, product_name: product, customers }, lang)
      setRes(r)
    } catch (e: any) { setErr(e.message) }
    finally { setLoading(false) }
  }

  const SEG_COLOR: Record<string, string> = { champion: '#22c55e', healthy: '#10b981', at_risk: '#f59e0b', critical: '#f97316', churned: '#ef4444' }
  const SEG_LABEL: Record<string, string> = { champion: 'Champion', healthy: 'Healthy', at_risk: 'At Risk', critical: 'Critical', churned: 'Churned' }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.8fr', gap: 16 }}>
      <div>
        <Card>
          <SectionHead title="Customer Health Score" sub="Score 0–100 from usage signals — segment + intervention playbook" />
          <div style={{ marginBottom: 10 }}>
            <label style={{ fontSize: 12, color: '#9ca3af', display: 'block', marginBottom: 4 }}>Business Name</label>
            <input value={biz} onChange={e => setBiz(e.target.value)} style={{ width: '100%', background: '#1e2535', border: '1px solid #374151', borderRadius: 6, padding: '7px 10px', color: '#e2e8f0', fontSize: 13, boxSizing: 'border-box' }} />
          </div>
          <div style={{ marginBottom: 14 }}>
            <label style={{ fontSize: 12, color: '#9ca3af', display: 'block', marginBottom: 4 }}>Product Name</label>
            <input value={product} onChange={e => setProduct(e.target.value)} style={{ width: '100%', background: '#1e2535', border: '1px solid #374151', borderRadius: 6, padding: '7px 10px', color: '#e2e8f0', fontSize: 13, boxSizing: 'border-box' }} />
          </div>
          <div style={{ marginBottom: 14 }}>
            <label style={{ fontSize: 12, color: '#9ca3af', display: 'block', marginBottom: 4 }}>Customer Data JSON (blank = demo)</label>
            <textarea value={jsonData} onChange={e => setJsonData(e.target.value)} rows={7} placeholder={`[\n  {\n    "name": "Ravi Textiles",\n    "login_frequency": 8,\n    "feature_adoption": 75,\n    "support_tickets": 2,\n    "nps_score": 8,\n    "payment_history": 100,\n    "arr": 120000\n  }\n]`} style={{ width: '100%', background: '#1e2535', border: '1px solid #374151', borderRadius: 6, padding: '8px 10px', color: '#e2e8f0', fontSize: 11, fontFamily: 'monospace', boxSizing: 'border-box', resize: 'vertical' }} />
          </div>
          <button onClick={run} disabled={loading} style={{ width: '100%', padding: '10px 0', background: loading ? '#374151' : '#10b981', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', fontSize: 14 }}>
            {loading ? 'Scoring…' : 'Score All Customers'}
          </button>
          {err && <div style={{ color: '#ef4444', fontSize: 12, marginTop: 8 }}>{err}</div>}
          {res && (
            <div style={{ marginTop: 14 }}>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 10 }}>
                <Badge label={`Avg score: ${res.avg_health_score}/100`} color="#818cf8" />
                <Badge label={`ARR at risk: ₹${((res.arr_at_risk || 0)/100000).toFixed(1)}L`} color="#ef4444" />
              </div>
              {Object.entries(res.segment_breakdown || {}).map(([seg, count]: any) => (
                <div key={seg} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 5 }}>
                  <span style={{ fontSize: 11, color: SEG_COLOR[seg] || '#6b7280', minWidth: 72 }}>{SEG_LABEL[seg] || seg}</span>
                  <div style={{ flex: 1, background: '#1e2535', borderRadius: 4, height: 6 }}>
                    <div style={{ width: `${(count / res.total_customers) * 100}%`, height: '100%', background: SEG_COLOR[seg] || '#6b7280', borderRadius: 4 }} />
                  </div>
                  <span style={{ fontSize: 11, color: '#9ca3af', minWidth: 16 }}>{count}</span>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
      <div>
        {res ? (
          (res.customers || []).map((cust: any, i: number) => (
            <div key={i} style={{ border: `1px solid ${cust.color || '#374151'}`, borderRadius: 8, marginBottom: 10, overflow: 'hidden' }}>
              <div onClick={() => setSelected(selected === i ? null : i)} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: '#111827', cursor: 'pointer' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <span style={{ color: '#e2e8f0', fontWeight: 600, fontSize: 13 }}>{cust.name}</span>
                    <Badge label={cust.segment_label} color={cust.color} />
                    {cust.csm && <span style={{ fontSize: 11, color: '#4b5563' }}>CSM: {cust.csm}</span>}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: 22, fontWeight: 800, color: cust.color }}>{cust.health_score}</span>
                    <div style={{ flex: 1, background: '#1e2535', borderRadius: 4, height: 6 }}>
                      <div style={{ width: `${cust.health_score}%`, height: '100%', background: cust.color, borderRadius: 4 }} />
                    </div>
                    {cust.arr > 0 && <span style={{ fontSize: 11, color: '#6b7280', whiteSpace: 'nowrap' }}>₹{(cust.arr/1000).toFixed(0)}K ARR</span>}
                  </div>
                </div>
                <span style={{ fontSize: 14, marginLeft: 12, color: '#6b7280' }}>{selected === i ? '▲' : '▼'}</span>
              </div>
              {selected === i && (
                <div style={{ padding: '12px 14px', background: '#0f1117' }}>
                  {(cust.risk_flags || []).length > 0 && (
                    <div style={{ marginBottom: 10 }}>
                      <div style={{ fontSize: 11, color: '#ef4444', fontWeight: 700, marginBottom: 4 }}>Risk Flags</div>
                      {cust.risk_flags.map((f: string, j: number) => <div key={j} style={{ fontSize: 12, color: '#f97316' }}>• {f}</div>)}
                    </div>
                  )}
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 10 }}>
                    {Object.entries(cust.signals || {}).filter(([, v]) => v !== undefined && v !== null).map(([k, v]: any) => (
                      <Badge key={k} label={`${k.replace(/_/g, ' ')}: ${v}`} color="#374151" />
                    ))}
                  </div>
                  <div style={{ fontSize: 11, color: '#10b981', fontWeight: 700, marginBottom: 6 }}>Recommended Actions</div>
                  {(cust.actions || []).map((a: string, j: number) => (
                    <div key={j} style={{ fontSize: 12, color: '#e2e8f0', background: '#111827', borderRadius: 4, padding: '6px 10px', marginBottom: 4, borderLeft: '3px solid #10b981' }}>{a}</div>
                  ))}
                </div>
              )}
            </div>
          ))
        ) : !loading && (
          <Card>
            <Empty text="Demo data pre-loaded — click Score All Customers to see results →" />
          </Card>
        )}
      </div>
    </div>
  )
}

// ── Win-back Email Sequence Tab (Round 12) ───────────────────────────────────

function WinbackTab({ lang }: { lang: Lang }) {
  const [biz, setBiz]           = useState('Acme SaaS')
  const [product, setProduct]   = useState('Core Platform')
  const [reason, setReason]     = useState('unknown')
  const [offerType, setOfferType] = useState('discount')
  const [offerVal, setOfferVal] = useState('20%')
  const [industry, setIndustry] = useState('saas')
  const [custJson, setCustJson] = useState('')
  const [res, setRes]           = useState<any>(null)
  const [loading, setLoading]   = useState(false)
  const [err, setErr]           = useState('')
  const [activeEmail, setActiveEmail] = useState(0)
  const [activeCustomer, setActiveCustomer] = useState<number | null>(null)

  const run = async () => {
    setLoading(true); setErr(''); setRes(null)
    let customers: any[] = []
    try { if (custJson.trim()) customers = JSON.parse(custJson) } catch { setErr('Invalid JSON'); setLoading(false); return }
    try {
      const r = await csAction('winback_sequence', {
        business_name: biz, product_name: product, churn_reason: reason,
        offer_type: offerType, offer_value: offerVal, industry, churned_customers: customers,
      }, lang)
      setRes(r)
    } catch (e: any) { setErr(e.message) }
    finally { setLoading(false) }
  }

  const PRIORITY_COLOR: Record<string, string> = { high: '#ef4444', medium: '#f59e0b', low: '#22c55e' }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.6fr', gap: 16 }}>
      <div>
        <Card>
          <SectionHead title="Win-back Email Sequence" sub="4-email sequence to re-engage churned customers" />
          <div style={{ marginBottom: 10 }}>
            <label style={{ fontSize: 12, color: '#9ca3af', display: 'block', marginBottom: 4 }}>Business Name</label>
            <input value={biz} onChange={e => setBiz(e.target.value)} style={{ width: '100%', background: '#1e2535', border: '1px solid #374151', borderRadius: 6, padding: '7px 10px', color: '#e2e8f0', fontSize: 13, boxSizing: 'border-box' }} />
          </div>
          <div style={{ marginBottom: 10 }}>
            <label style={{ fontSize: 12, color: '#9ca3af', display: 'block', marginBottom: 4 }}>Product Name</label>
            <input value={product} onChange={e => setProduct(e.target.value)} style={{ width: '100%', background: '#1e2535', border: '1px solid #374151', borderRadius: 6, padding: '7px 10px', color: '#e2e8f0', fontSize: 13, boxSizing: 'border-box' }} />
          </div>
          <div style={{ marginBottom: 10 }}>
            <label style={{ fontSize: 12, color: '#9ca3af', display: 'block', marginBottom: 4 }}>Primary Churn Reason</label>
            <select value={reason} onChange={e => setReason(e.target.value)} style={{ width: '100%', background: '#1e2535', border: '1px solid #374151', borderRadius: 6, padding: '7px 10px', color: '#e2e8f0', fontSize: 13, boxSizing: 'border-box' }}>
              <option value="unknown">Unknown / General</option>
              <option value="price">Price / Too Expensive</option>
              <option value="competitor">Moved to Competitor</option>
              <option value="feature_gap">Missing Features</option>
              <option value="no_use">Not Using Product</option>
              <option value="bad_support">Poor Support Experience</option>
            </select>
          </div>
          <div style={{ marginBottom: 10 }}>
            <label style={{ fontSize: 12, color: '#9ca3af', display: 'block', marginBottom: 4 }}>Win-back Offer Type</label>
            <select value={offerType} onChange={e => setOfferType(e.target.value)} style={{ width: '100%', background: '#1e2535', border: '1px solid #374151', borderRadius: 6, padding: '7px 10px', color: '#e2e8f0', fontSize: 13, boxSizing: 'border-box' }}>
              <option value="discount">Discount on Return</option>
              <option value="free_months">Free Months</option>
              <option value="upgrade">Tier Upgrade</option>
              <option value="personal_call">Personal Outreach Call</option>
              <option value="credits">Account Credits</option>
            </select>
          </div>
          <div style={{ marginBottom: 14 }}>
            <label style={{ fontSize: 12, color: '#9ca3af', display: 'block', marginBottom: 4 }}>Offer Value</label>
            <input value={offerVal} onChange={e => setOfferVal(e.target.value)} placeholder="e.g. 20%, 2 months, Pro plan" style={{ width: '100%', background: '#1e2535', border: '1px solid #374151', borderRadius: 6, padding: '7px 10px', color: '#e2e8f0', fontSize: 13, boxSizing: 'border-box' }} />
          </div>
          <div style={{ marginBottom: 14 }}>
            <label style={{ fontSize: 12, color: '#9ca3af', display: 'block', marginBottom: 4 }}>Churned Customers JSON (blank = demo)</label>
            <textarea value={custJson} onChange={e => setCustJson(e.target.value)} rows={4} placeholder={'[\n  {"name":"Ravi Kumar","company":"Ravi Textiles","churned_months_ago":2,"arr":85000}\n]'} style={{ width: '100%', background: '#1e2535', border: '1px solid #374151', borderRadius: 6, padding: '8px 10px', color: '#e2e8f0', fontSize: 11, fontFamily: 'monospace', boxSizing: 'border-box' }} />
          </div>
          <button onClick={run} disabled={loading} style={{ width: '100%', padding: '10px 0', background: loading ? '#374151' : '#10b981', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', fontSize: 14 }}>
            {loading ? 'Building Sequence…' : 'Generate Win-back Sequence'}
          </button>
          {err && <div style={{ color: '#ef4444', fontSize: 12, marginTop: 8 }}>{err}</div>}
        </Card>
      </div>
      <div>
        {res ? (
          <>
            {/* Summary */}
            <Card style={{ marginBottom: 12 }}>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                <Badge label={`${res.email_sequence?.length || 4} emails`} color="#818cf8" />
                <Badge label={`${res.customer_queue?.length || 0} customers`} color="#6b7280" />
                <Badge label={`ARR at risk: ₹${((res.total_arr_at_risk || 0)/100000).toFixed(1)}L`} color="#ef4444" />
                <Badge label={`Reason: ${res.churn_reason}`} color="#f59e0b" />
              </div>
            </Card>

            {/* Email sequence tabs */}
            <Card style={{ marginBottom: 12 }}>
              <SectionHead title="Email Sequence" sub="Copy, customize and schedule in your CRM" />
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 12 }}>
                {(res.email_sequence || []).map((e: any, i: number) => (
                  <span key={i} onClick={() => setActiveEmail(i)} style={{
                    padding: '4px 12px', borderRadius: 20, fontSize: 11, cursor: 'pointer',
                    background: activeEmail === i ? '#10b981' : '#1e2535',
                    color: activeEmail === i ? '#fff' : '#9ca3af',
                    border: `1px solid ${activeEmail === i ? '#10b981' : '#374151'}`,
                  }}>Day {e.sequence_day}</span>
                ))}
              </div>
              {res.email_sequence?.[activeEmail] && (() => {
                const em = res.email_sequence[activeEmail]
                return (
                  <>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                      <span style={{ fontSize: 13, fontWeight: 700, color: '#a78bfa' }}>{em.label}</span>
                      <Badge label={em.goal} color="#6b7280" />
                    </div>
                    <div style={{ fontSize: 11, color: '#9ca3af', marginBottom: 6 }}>Subject: <span style={{ color: '#e2e8f0' }}>{em.subject}</span></div>
                    <div style={{ fontSize: 11, color: '#4b5563', marginBottom: 8 }}>Send: {em.send_timing}</div>
                    <div style={{ fontSize: 12, color: '#e2e8f0', lineHeight: 1.7, whiteSpace: 'pre-wrap', background: '#0f1117', borderRadius: 6, padding: '10px 12px', maxHeight: 280, overflowY: 'auto', marginBottom: 8 }}>{em.body}</div>
                    <span onClick={() => navigator.clipboard?.writeText(`Subject: ${em.subject}\n\n${em.body}`)} style={{ cursor: 'pointer', fontSize: 11, color: '#fff', padding: '4px 12px', background: '#374151', borderRadius: 6 }}>Copy Email</span>
                  </>
                )
              })()}
            </Card>

            {/* Customer queue */}
            <Card style={{ marginBottom: 12 }}>
              <SectionHead title="Customer Priority Queue" sub="Sorted by ARR — highest value first" />
              {(res.customer_queue || []).map((c: any, i: number) => (
                <div key={i} onClick={() => setActiveCustomer(activeCustomer === i ? null : i)} style={{ background: '#0f1117', borderRadius: 8, padding: '10px 12px', marginBottom: 6, cursor: 'pointer', border: '1px solid #1e2535' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <span style={{ color: '#e2e8f0', fontWeight: 600, fontSize: 13 }}>{c.name}</span>
                      {c.company && <span style={{ fontSize: 11, color: '#6b7280', marginLeft: 8 }}>{c.company}</span>}
                    </div>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <Badge label={c.winback_priority + ' priority'} color={PRIORITY_COLOR[c.winback_priority] || '#6b7280'} />
                      {c.arr > 0 && <span style={{ fontSize: 12, fontWeight: 700, color: '#22c55e' }}>₹{(c.arr/1000).toFixed(0)}K</span>}
                    </div>
                  </div>
                  {activeCustomer === i && (
                    <div style={{ marginTop: 8, fontSize: 12, color: '#6b7280' }}>
                      <div>Churned: {c.churned_months_ago} month(s) ago • Start at Email {c.start_at_email}</div>
                      {c.last_feature && <div>Last used: {c.last_feature}</div>}
                      <div style={{ color: '#f59e0b', marginTop: 4 }}>Tip: {c.personalization_note}</div>
                      <div>Expected win-back rate: {c.expected_winback_rate}</div>
                    </div>
                  )}
                </div>
              ))}
            </Card>

            {/* Best practices */}
            <Card>
              <SectionHead title="Best Practices" sub="India B2B win-back playbook" />
              {(res.best_practices || []).map((bp: string, i: number) => (
                <div key={i} style={{ fontSize: 12, color: '#9ca3af', padding: '6px 0', borderBottom: '1px solid #1e2535' }}>• {bp}</div>
              ))}
            </Card>
          </>
        ) : !loading && (
          <Card>
            <Empty text="Demo data pre-loaded — click Generate Win-back Sequence →" />
          </Card>
        )}
      </div>
    </div>
  )
}

// ── Agent Performance Scorecard Tab (Round 13) ────────────────────────────────

function AgentScorecardTab({ lang }: { lang: Lang }) {
  const [biz, setBiz]           = useState('')
  const [period, setPeriod]     = useState('July 2025')
  const [agentsJson, setAgentsJson] = useState('')
  const [res, setRes]           = useState<any>(null)
  const [loading, setLoading]   = useState(false)
  const [err, setErr]           = useState('')
  const [activeAgent, setActiveAgent] = useState(0)

  const run = async () => {
    setLoading(true); setErr(''); setRes(null); setActiveAgent(0)
    try {
      let agents: any[] = []
      if (agentsJson.trim()) {
        try { agents = JSON.parse(agentsJson) } catch { setErr('Invalid JSON for agents list'); setLoading(false); return }
      }
      setRes(await csAction('agent_performance_scorecard', { business_name: biz, period, agents, team_targets: {} }))
    } catch (e: any) { setErr(e.message) }
    finally { setLoading(false) }
  }

  const tierColor: Record<string, string> = { star: '#22c55e', solid: '#60a5fa', developing: '#f59e0b', needs_help: '#ef4444' }
  const statusColor = (s: string) => s === 'above' ? '#22c55e' : s === 'at' ? '#f59e0b' : '#ef4444'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 16 }}>
        {/* Left — inputs */}
        <div style={{ background: '#141b2d', borderRadius: 12, padding: 20, border: '1px solid #1e2535' }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: '#e2e8f0', marginBottom: 4 }}>📊 Agent Performance Scorecard</div>
          <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 16 }}>Score agents on CSAT, FCR, response time & more. Demo data pre-loaded.</div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ fontSize: 12, color: '#9ca3af', display: 'block', marginBottom: 4 }}>Business Name</label>
            <input value={biz} onChange={e => setBiz(e.target.value)} placeholder="e.g. Acme Support Team"
              style={{ width: '100%', background: '#1e2535', border: '1px solid #374151', borderRadius: 6, padding: '7px 10px', color: '#e2e8f0', fontSize: 13, boxSizing: 'border-box' }} />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ fontSize: 12, color: '#9ca3af', display: 'block', marginBottom: 4 }}>Period</label>
            <input value={period} onChange={e => setPeriod(e.target.value)} placeholder="e.g. July 2025"
              style={{ width: '100%', background: '#1e2535', border: '1px solid #374151', borderRadius: 6, padding: '7px 10px', color: '#e2e8f0', fontSize: 13, boxSizing: 'border-box' }} />
          </div>
          <div style={{ marginBottom: 14 }}>
            <label style={{ fontSize: 12, color: '#9ca3af', display: 'block', marginBottom: 4 }}>Agent Data JSON (blank = demo team of 5)</label>
            <textarea value={agentsJson} onChange={e => setAgentsJson(e.target.value)} rows={6}
              placeholder={'[\n  {"name":"Priya S.","csat_score":4.7,"fcr_pct":88,"tickets_per_day":28,"first_response_time_min":18,"resolution_time_hours":6,"reopen_rate_pct":2,"escalation_rate_pct":4,"tenure_months":18}\n]'}
              style={{ width: '100%', background: '#1e2535', border: '1px solid #374151', borderRadius: 6, padding: '8px 10px', color: '#e2e8f0', fontSize: 11, fontFamily: 'monospace', boxSizing: 'border-box', resize: 'vertical' }} />
          </div>
          <button onClick={run} disabled={loading} style={{ width: '100%', background: '#4f46e5', color: '#fff', border: 'none', borderRadius: 8, padding: '10px 0', fontSize: 13, fontWeight: 700, cursor: loading ? 'default' : 'pointer', opacity: loading ? 0.7 : 1 }}>
            {loading ? 'Scoring agents…' : '📊 Generate Scorecard'}
          </button>
          {err && <div style={{ color: '#ef4444', fontSize: 12, marginTop: 8 }}>{err}</div>}
        </div>

        {/* Right — results */}
        <div style={{ background: '#141b2d', borderRadius: 12, padding: 20, border: '1px solid #1e2535' }}>
          {res ? (() => {
            const agents: any[] = res.agents || []
            const active = agents[activeAgent] || agents[0]
            return (
              <>
                {/* Team summary */}
                <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
                  <div style={{ flex: 1, background: '#0f172a', borderRadius: 8, padding: 12, textAlign: 'center', minWidth: 80 }}>
                    <div style={{ fontSize: 22, fontWeight: 800, color: '#60a5fa' }}>{res.team_avg_score}</div>
                    <div style={{ fontSize: 10, color: '#6b7280' }}>Team Avg Score</div>
                  </div>
                  <div style={{ flex: 1, background: '#0f172a', borderRadius: 8, padding: 12, textAlign: 'center', minWidth: 80 }}>
                    <div style={{ fontSize: 22, fontWeight: 800, color: '#22c55e' }}>{res.tier_distribution?.star || 0}</div>
                    <div style={{ fontSize: 10, color: '#6b7280' }}>Star Agents</div>
                  </div>
                  <div style={{ flex: 1, background: '#0f172a', borderRadius: 8, padding: 12, textAlign: 'center', minWidth: 80 }}>
                    <div style={{ fontSize: 22, fontWeight: 800, color: '#ef4444' }}>{res.tier_distribution?.needs_help || 0}</div>
                    <div style={{ fontSize: 10, color: '#6b7280' }}>Need Coaching</div>
                  </div>
                  <div style={{ flex: 1, background: '#0f172a', borderRadius: 8, padding: 12, textAlign: 'center', minWidth: 80 }}>
                    <div style={{ fontSize: 16, fontWeight: 800, color: '#f59e0b' }}>{res.top_performer || '—'}</div>
                    <div style={{ fontSize: 10, color: '#6b7280' }}>Top Performer</div>
                  </div>
                </div>

                {/* Agent selector chips */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 14 }}>
                  {agents.map((a: any, i: number) => (
                    <span key={i} onClick={() => setActiveAgent(i)} style={{
                      padding: '5px 12px', borderRadius: 20, fontSize: 12, cursor: 'pointer', fontWeight: activeAgent === i ? 700 : 400,
                      background: activeAgent === i ? tierColor[a.tier_key] || '#4f46e5' : '#1e2535',
                      color: activeAgent === i ? '#fff' : '#9ca3af',
                      border: `1px solid ${activeAgent === i ? tierColor[a.tier_key] + '80' : 'transparent'}`,
                    }}>
                      {a.name} — {a.overall_score}
                    </span>
                  ))}
                </div>

                {/* Active agent detail */}
                {active && (
                  <div style={{ background: '#0f172a', borderRadius: 10, padding: 16, marginBottom: 14 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                      <div>
                        <div style={{ fontSize: 15, fontWeight: 700, color: '#e2e8f0' }}>{active.name}</div>
                        <div style={{ fontSize: 11, color: '#6b7280' }}>{active.tenure_months} months tenure</div>
                      </div>
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: 28, fontWeight: 800, color: tierColor[active.tier_key] || '#6b7280' }}>{active.overall_score}</div>
                        <Badge label={active.tier} color={active.tier_key === 'star' ? 'green' : active.tier_key === 'solid' ? 'blue' : active.tier_key === 'developing' ? 'yellow' : 'red'} />
                      </div>
                    </div>

                    {/* Metrics */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 12 }}>
                      {(active.metrics || []).map((m: any, i: number) => (
                        <div key={i} style={{ background: '#141b2d', borderRadius: 6, padding: 8 }}>
                          <div style={{ fontSize: 10, color: '#6b7280', marginBottom: 2 }}>{m.label}</div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontSize: 13, fontWeight: 700, color: statusColor(m.status) }}>{m.actual}{m.unit}</span>
                            <span style={{ fontSize: 10, color: '#4b5563' }}>target: {m.target}{m.unit}</span>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Strengths & Gaps */}
                    {active.strengths?.length > 0 && (
                      <div style={{ marginBottom: 8 }}>
                        <div style={{ fontSize: 10, color: '#22c55e', marginBottom: 3 }}>STRENGTHS</div>
                        <div style={{ fontSize: 11, color: '#d1d5db' }}>{active.strengths.join(' • ')}</div>
                      </div>
                    )}
                    {active.gaps?.length > 0 && (
                      <div style={{ marginBottom: 8 }}>
                        <div style={{ fontSize: 10, color: '#ef4444', marginBottom: 3 }}>GAPS</div>
                        <div style={{ fontSize: 11, color: '#d1d5db' }}>{active.gaps.join(' • ')}</div>
                      </div>
                    )}

                    {/* Coaching tips */}
                    {active.coaching_tips?.length > 0 && (
                      <div style={{ borderTop: '1px solid #1e2535', paddingTop: 10 }}>
                        <div style={{ fontSize: 10, color: '#f59e0b', marginBottom: 6 }}>COACHING ACTIONS</div>
                        {active.coaching_tips.map((ct: any, i: number) => (
                          <div key={i} style={{ marginBottom: 8 }}>
                            <div style={{ fontSize: 11, fontWeight: 600, color: '#e2e8f0' }}>{ct.area}</div>
                            <div style={{ fontSize: 11, color: '#94a3b8', lineHeight: 1.5 }}>{ct.tip}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </>
            )
          })() : <Empty text="Demo data pre-loaded — click Generate Scorecard →" />}
        </div>
      </div>
    </div>
  )
}
