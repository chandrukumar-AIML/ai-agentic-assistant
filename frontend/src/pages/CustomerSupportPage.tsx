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
  { id: 'whatsapp',   label: 'WhatsApp Drafter' },
  { id: 'sentiment',  label: 'Sentiment' },
  { id: 'complaint',  label: 'Complaint Handler' },
  { id: 'lead',       label: 'Lead Qualifier' },
  { id: 'ticket',     label: 'Ticket Summary' },
  { id: 'template',   label: 'Response Templates' },
  { id: 'kb',         label: 'Knowledge Base' },
  { id: 'report',     label: 'Weekly Report' },
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

  const run = async () => {
    setLoading(true); setErr(''); setRes(null)
    try {
      setRes(await csAction('draft_whatsapp', {
        message_type: msgType, customer_name: custName || 'Customer',
        business_name: bizName || 'Our Business', context,
      }, lang))
    } catch (e: any) { setErr(e.message) }
    setLoading(false)
  }

  return (
    <Row>
      <Card>
        <SectionHead title="WhatsApp Message Drafter" sub="Generate ready-to-send WhatsApp messages" />
        <Select label="Message Type" value={msgType} onChange={setMsgType} options={WA_TYPES} />
        <Input label="Customer Name" value={custName} onChange={setCustName} placeholder="Priya" />
        <Input label="Business Name" value={bizName} onChange={setBizName} placeholder="Sri Lakshmi Stores" />
        <div style={{ marginTop: 14 }}>
          <div style={{ color: '#9ca3af', fontSize: 12, marginBottom: 4 }}>Context / Details</div>
          <TA value={context} onChange={setContext} placeholder="e.g. Order delivered yesterday, asking for review..." rows={4} />
        </div>
        <Btn onClick={run} loading={loading} style={{ marginTop: 14, width: '100%' }}>Draft Message</Btn>
        {err && <div style={{ color: '#ef4444', fontSize: 13, marginTop: 8 }}>{err}</div>}
      </Card>
      <Card>
        <SectionHead title="WhatsApp Message" />
        {res ? (
          <div>
            <div style={{ background: '#075e54', borderRadius: 12, padding: '16px 18px', color: '#ecfdf5', fontSize: 14, lineHeight: 1.7, whiteSpace: 'pre-wrap', marginBottom: 12, fontFamily: 'system-ui' }}>
              {res.message}
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <Badge label={res.word_count + ' words'} color="#6b7280" />
              <Badge label={res.channel || 'WhatsApp'} color="#25d366" />
            </div>
          </div>
        ) : <Empty text="WhatsApp message will appear here..." />}
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
      </div>
    </PageShell>
  )
}
