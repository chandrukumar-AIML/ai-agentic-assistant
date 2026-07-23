import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { saveWorkspace, AgentType, SMWorkspace, CSWorkspace, CAWorkspace } from '../lib/workspace'

// ── Shared step layout ────────────────────────────────────────────────────────
function StepWrap({ title, sub, children }: { title: string; sub: string; children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -24 }}
      transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
      style={{ display: 'flex', flexDirection: 'column', gap: 20 }}
    >
      <div>
        <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text)', letterSpacing: '-0.01em' }}>{title}</div>
        <div style={{ fontSize: 13, color: 'var(--text-3)', marginTop: 4 }}>{sub}</div>
      </div>
      {children}
    </motion.div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-2)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</label>
      {children}
    </div>
  )
}

function TextInput({ value, onChange, placeholder }: { value: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <input value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder} style={{
      background: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: 8,
      padding: '10px 12px', color: 'var(--text)', fontSize: 13, outline: 'none',
      width: '100%', boxSizing: 'border-box' as const, fontFamily: 'inherit',
    }} />
  )
}

function SelectInput({ value, onChange, options }: { value: string; onChange: (v: string) => void; options: { label: string; value: string }[] }) {
  return (
    <select value={value} onChange={e => onChange(e.target.value)} style={{
      background: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: 8,
      padding: '10px 12px', color: 'var(--text)', fontSize: 13, outline: 'none',
      width: '100%', boxSizing: 'border-box' as const, fontFamily: 'inherit', cursor: 'pointer',
    }}>
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  )
}

function CheckChip({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button type="button" onClick={() => onChange(!checked)} style={{
      padding: '6px 14px', borderRadius: 20, fontSize: 12, fontWeight: 500,
      border: `1px solid ${checked ? 'transparent' : 'var(--border)'}`,
      background: checked ? 'var(--accent)' : 'var(--surface-2)',
      color: checked ? '#fff' : 'var(--text-2)',
      cursor: 'pointer', transition: 'all 0.15s',
    }}>{label}</button>
  )
}

// ── SM Wizard ─────────────────────────────────────────────────────────────────
const SM_INDUSTRIES = [
  { label: 'E-commerce / Retail', value: 'ecommerce' },
  { label: 'SaaS / Tech', value: 'saas' },
  { label: 'Healthcare / Wellness', value: 'healthcare' },
  { label: 'Education / EdTech', value: 'education' },
  { label: 'Food & Beverage', value: 'food' },
  { label: 'Fashion / Lifestyle', value: 'fashion' },
  { label: 'Finance / Fintech', value: 'finance' },
  { label: 'Real Estate', value: 'realestate' },
  { label: 'Agency / Consulting', value: 'agency' },
  { label: 'Manufacturing / B2B', value: 'manufacturing' },
  { label: 'Other', value: 'other' },
]
const SM_TONES = [
  { label: 'Professional', value: 'professional' },
  { label: 'Casual & Friendly', value: 'casual' },
  { label: 'Witty & Humorous', value: 'witty' },
  { label: 'Inspirational', value: 'inspirational' },
  { label: 'Educational', value: 'educational' },
  { label: 'Bold & Direct', value: 'bold' },
]
const SM_PLATFORMS = ['Instagram', 'LinkedIn', 'Twitter/X', 'Facebook', 'YouTube', 'WhatsApp']

function SMWizard({ step, data, setData }: { step: number; data: Partial<SMWorkspace>; setData: (d: Partial<SMWorkspace>) => void }) {
  const set = (key: keyof SMWorkspace, val: any) => setData({ ...data, [key]: val })
  const togglePlatform = (p: string) => {
    const cur = data.platforms ?? []
    set('platforms', cur.includes(p) ? cur.filter(x => x !== p) : [...cur, p])
  }

  if (step === 0) return (
    <StepWrap title="Brand Basics" sub="Tell us about your brand so AI can generate on-brand content">
      <Field label="Brand / Company Name"><TextInput value={data.brand_name ?? ''} onChange={v => set('brand_name', v)} placeholder="e.g. ShopEasy India" /></Field>
      <Field label="Industry"><SelectInput value={data.industry ?? 'ecommerce'} onChange={v => set('industry', v)} options={SM_INDUSTRIES} /></Field>
      <Field label="Target Audience"><TextInput value={data.target_audience ?? ''} onChange={v => set('target_audience', v)} placeholder="e.g. Indian SMB owners, 25–45, decision makers" /></Field>
    </StepWrap>
  )
  if (step === 1) return (
    <StepWrap title="Platforms & Tone" sub="Where do you post? What voice should AI use?">
      <Field label="Active Platforms">
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {SM_PLATFORMS.map(p => <CheckChip key={p} label={p} checked={(data.platforms ?? []).includes(p)} onChange={() => togglePlatform(p)} />)}
        </div>
      </Field>
      <Field label="Brand Tone"><SelectInput value={data.tone ?? 'professional'} onChange={v => set('tone', v)} options={SM_TONES} /></Field>
      <Field label="Hashtag Style"><TextInput value={data.hashtag_style ?? ''} onChange={v => set('hashtag_style', v)} placeholder="e.g. #MakeInIndia #StartupIndia — max 5" /></Field>
    </StepWrap>
  )
  return (
    <StepWrap title="Content Strategy" sub="AI will use this to make content that stands out">
      <Field label="Competitor Brands"><TextInput value={data.competitor_brands ?? ''} onChange={v => set('competitor_brands', v)} placeholder="e.g. Meesho, Flipkart, Nykaa" /></Field>
      <Field label="Content Pillars">
        <textarea value={data.content_pillars ?? ''} onChange={e => set('content_pillars', e.target.value)}
          placeholder="e.g. Product tips, Behind the scenes, Customer success stories, Industry news"
          rows={3} style={{
            background: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: 8,
            padding: '10px 12px', color: 'var(--text)', fontSize: 13, outline: 'none',
            width: '100%', boxSizing: 'border-box' as const, fontFamily: 'inherit', resize: 'vertical',
          }} />
      </Field>
    </StepWrap>
  )
}

// ── CS Wizard ─────────────────────────────────────────────────────────────────
const CS_BIZ_TYPES = [
  { label: 'E-commerce / Online Store', value: 'ecommerce' },
  { label: 'SaaS / Software', value: 'saas' },
  { label: 'Healthcare / Clinic', value: 'healthcare' },
  { label: 'Education / Coaching', value: 'education' },
  { label: 'Financial Services', value: 'finance' },
  { label: 'Retail / Physical Store', value: 'retail' },
  { label: 'Logistics / Delivery', value: 'logistics' },
  { label: 'Agency / Consulting', value: 'agency' },
  { label: 'Other', value: 'other' },
]
const CS_TONES = [
  { label: 'Formal & Professional', value: 'formal' },
  { label: 'Friendly & Warm', value: 'friendly' },
  { label: 'Empathetic & Caring', value: 'empathetic' },
  { label: 'Quick & Direct', value: 'direct' },
]
const SLA_OPTIONS = [
  { label: '1 hour', value: '1' }, { label: '2 hours', value: '2' },
  { label: '4 hours', value: '4' }, { label: '8 hours', value: '8' },
  { label: '24 hours', value: '24' }, { label: '48 hours', value: '48' },
]

function CSWizard({ step, data, setData }: { step: number; data: Partial<CSWorkspace>; setData: (d: Partial<CSWorkspace>) => void }) {
  const set = (key: keyof CSWorkspace, val: string) => setData({ ...data, [key]: val })

  if (step === 0) return (
    <StepWrap title="Company Info" sub="Tell us about your business so AI generates accurate support content">
      <Field label="Company Name"><TextInput value={data.company_name ?? ''} onChange={v => set('company_name', v)} placeholder="e.g. ShopEasy India Pvt Ltd" /></Field>
      <Field label="Business Type"><SelectInput value={data.business_type ?? 'ecommerce'} onChange={v => set('business_type', v)} options={CS_BIZ_TYPES} /></Field>
      <Field label="Products / Services">
        <textarea value={data.products_services ?? ''} onChange={e => set('products_services', e.target.value)}
          placeholder="e.g. Online fashion store — ethnic wear, western wear, accessories. Deliver PAN India."
          rows={3} style={{
            background: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: 8,
            padding: '10px 12px', color: 'var(--text)', fontSize: 13, outline: 'none',
            width: '100%', boxSizing: 'border-box' as const, fontFamily: 'inherit', resize: 'vertical',
          }} />
      </Field>
    </StepWrap>
  )
  if (step === 1) return (
    <StepWrap title="Support Channels" sub="How do your customers reach you?">
      <Field label="WhatsApp Business Number"><TextInput value={data.whatsapp_number ?? ''} onChange={v => set('whatsapp_number', v)} placeholder="e.g. +91 98765 43210" /></Field>
      <Field label="Business Hours"><TextInput value={data.business_hours ?? ''} onChange={v => set('business_hours', v)} placeholder="e.g. Mon–Sat 9am–7pm IST" /></Field>
      <Field label="Escalation Email"><TextInput value={data.escalation_email ?? ''} onChange={v => set('escalation_email', v)} placeholder="e.g. support@yourcompany.com" /></Field>
      <Field label="Support Tone"><SelectInput value={data.support_tone ?? 'friendly'} onChange={v => set('support_tone', v)} options={CS_TONES} /></Field>
    </StepWrap>
  )
  return (
    <StepWrap title="SLA & Standards" sub="Define your support quality benchmarks">
      <Field label="First Response SLA"><SelectInput value={data.sla_first_response ?? '4'} onChange={v => set('sla_first_response', v)} options={SLA_OPTIONS} /></Field>
      <div style={{ padding: 16, borderRadius: 10, background: 'var(--surface-2)', border: '1px solid var(--border)' }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-2)', marginBottom: 8 }}>✅ Setup Complete After This</div>
        <div style={{ fontSize: 12, color: 'var(--text-3)', lineHeight: 1.7 }}>
          All support features (FAQ Bot, WhatsApp drafter, complaint handler, NPS builder etc.) will auto-use your company context. No more re-entering details every time.
        </div>
      </div>
    </StepWrap>
  )
}

// ── CA Wizard ─────────────────────────────────────────────────────────────────
const CA_BIZ_TYPES = [
  { label: 'Proprietorship', value: 'proprietorship' },
  { label: 'Partnership Firm', value: 'partnership' },
  { label: 'Private Limited Company', value: 'pvt_ltd' },
  { label: 'LLP', value: 'llp' },
  { label: 'Public Limited Company', value: 'public_ltd' },
  { label: 'Trust / NGO', value: 'trust' },
  { label: 'HUF', value: 'huf' },
  { label: 'Individual (Professional)', value: 'individual' },
]
const INDIAN_STATES = [
  { label: 'Andhra Pradesh', value: 'AP' }, { label: 'Assam', value: 'AS' },
  { label: 'Bihar', value: 'BR' }, { label: 'Chhattisgarh', value: 'CG' },
  { label: 'Delhi', value: 'DL' }, { label: 'Goa', value: 'GA' },
  { label: 'Gujarat', value: 'GJ' }, { label: 'Haryana', value: 'HR' },
  { label: 'Himachal Pradesh', value: 'HP' }, { label: 'Jharkhand', value: 'JH' },
  { label: 'Karnataka', value: 'KA' }, { label: 'Kerala', value: 'KL' },
  { label: 'Madhya Pradesh', value: 'MP' }, { label: 'Maharashtra', value: 'MH' },
  { label: 'Odisha', value: 'OD' }, { label: 'Punjab', value: 'PB' },
  { label: 'Rajasthan', value: 'RJ' }, { label: 'Tamil Nadu', value: 'TN' },
  { label: 'Telangana', value: 'TS' }, { label: 'Uttar Pradesh', value: 'UP' },
  { label: 'Uttarakhand', value: 'UK' }, { label: 'West Bengal', value: 'WB' },
]
const FILING_FREQ = [
  { label: 'Monthly (QRMP opted out)', value: 'monthly' },
  { label: 'Quarterly (QRMP scheme)', value: 'quarterly' },
]
const TAXPAYER_TYPES = [
  { label: 'Regular Taxpayer', value: 'regular' },
  { label: 'QRMP Scheme', value: 'qrmp' },
  { label: 'Composition Scheme', value: 'composition' },
  { label: 'Non-GST / Exempt', value: 'exempt' },
]

function CAWizard({ step, data, setData }: { step: number; data: Partial<CAWorkspace>; setData: (d: Partial<CAWorkspace>) => void }) {
  const set = (key: keyof CAWorkspace, val: string) => setData({ ...data, [key]: val })

  if (step === 0) return (
    <StepWrap title="Firm & Client Info" sub="Set up your CA firm or client profile once">
      <Field label="CA Firm Name"><TextInput value={data.firm_name ?? ''} onChange={v => set('firm_name', v)} placeholder="e.g. Sharma & Co. Chartered Accountants" /></Field>
      <Field label="Client / Business Name"><TextInput value={data.client_name ?? ''} onChange={v => set('client_name', v)} placeholder="e.g. ZenFit Pvt Ltd" /></Field>
      <Field label="Business Structure"><SelectInput value={data.business_type ?? 'pvt_ltd'} onChange={v => set('business_type', v)} options={CA_BIZ_TYPES} /></Field>
    </StepWrap>
  )
  if (step === 1) return (
    <StepWrap title="Tax Registration" sub="Your GST and PAN details — used across all tax features">
      <Field label="GSTIN"><TextInput value={data.gstin ?? ''} onChange={v => set('gstin', v.toUpperCase())} placeholder="e.g. 33AABCZ1234M1Z5" /></Field>
      <Field label="PAN"><TextInput value={data.pan ?? ''} onChange={v => set('pan', v.toUpperCase())} placeholder="e.g. AABCZ1234M" /></Field>
      <Field label="State of Registration"><SelectInput value={data.state ?? 'TN'} onChange={v => set('state', v)} options={INDIAN_STATES} /></Field>
    </StepWrap>
  )
  return (
    <StepWrap title="Filing Preferences" sub="Your filing cycle determines which deadlines we track">
      <Field label="Financial Year">
        <SelectInput value={data.financial_year ?? '2025-26'} onChange={v => set('financial_year', v)} options={[
          { label: 'FY 2025–26', value: '2025-26' },
          { label: 'FY 2024–25', value: '2024-25' },
          { label: 'FY 2023–24', value: '2023-24' },
        ]} />
      </Field>
      <Field label="Filing Frequency"><SelectInput value={data.filing_frequency ?? 'monthly'} onChange={v => set('filing_frequency', v)} options={FILING_FREQ} /></Field>
      <Field label="Taxpayer Type"><SelectInput value={data.taxpayer_type ?? 'regular'} onChange={v => set('taxpayer_type', v)} options={TAXPAYER_TYPES} /></Field>
    </StepWrap>
  )
}

// ── Config per agent ──────────────────────────────────────────────────────────
const AGENT_CONFIG = {
  sm: {
    accent: '#8B5CF6', icon: '📱', name: 'Social Media',
    steps: ['Brand Basics', 'Platforms & Tone', 'Strategy'],
  },
  cs: {
    accent: '#10B981', icon: '💬', name: 'Customer Support',
    steps: ['Company Info', 'Support Channels', 'SLA & Standards'],
  },
  ca: {
    accent: '#F59E0B', icon: '🧮', name: 'CA & Accounting',
    steps: ['Firm & Client', 'Tax Registration', 'Filing Prefs'],
  },
}

// ── Main WorkspaceSetup modal ─────────────────────────────────────────────────
interface Props {
  agent: AgentType
  initialData?: any
  onDone: (data: any) => void
  onSkip?: () => void
}

export default function WorkspaceSetup({ agent, initialData, onDone, onSkip }: Props) {
  const cfg = AGENT_CONFIG[agent]
  const [step, setStep] = useState(0)
  const [data, setData] = useState<any>(initialData ?? {})
  const totalSteps = cfg.steps.length
  const isLast = step === totalSteps - 1

  function handleSave() {
    saveWorkspace(agent, data)
    onDone(data)
  }

  return (
    // Backdrop
    <div style={{
      position: 'fixed', inset: 0, zIndex: 1000,
      background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16,
    }}>
      <motion.div
        initial={{ opacity: 0, scale: 0.94, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
        style={{
          width: '100%', maxWidth: 480,
          background: 'var(--surface)', border: '1px solid var(--border-2)',
          borderRadius: 20, overflow: 'hidden',
          boxShadow: `0 0 60px rgba(0,0,0,0.5), 0 0 120px ${cfg.accent}22`,
        }}
      >
        {/* Header */}
        <div style={{
          padding: '20px 24px',
          background: `linear-gradient(135deg, ${cfg.accent}18, transparent)`,
          borderBottom: '1px solid var(--border)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
            <div style={{
              width: 38, height: 38, borderRadius: 11, flexShrink: 0,
              background: `linear-gradient(135deg, ${cfg.accent}, ${cfg.accent}88)`,
              display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18,
            }}>{cfg.icon}</div>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text)' }}>Setup {cfg.name} Workspace</div>
              <div style={{ fontSize: 12, color: 'var(--text-3)' }}>One-time setup — AI uses this for every feature</div>
            </div>
          </div>

          {/* Step progress */}
          <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            {cfg.steps.map((s, i) => (
              <div key={s} style={{ display: 'flex', alignItems: 'center', gap: 6, flex: 1 }}>
                <div style={{
                  flex: 1, height: 3, borderRadius: 2,
                  background: i <= step ? cfg.accent : 'var(--surface-3)',
                  transition: 'background 0.3s',
                }} />
              </div>
            ))}
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 6 }}>
            Step {step + 1} of {totalSteps} — {cfg.steps[step]}
          </div>
        </div>

        {/* Body */}
        <div style={{ padding: 24, minHeight: 280 }}>
          <AnimatePresence mode="wait">
            <div key={step}>
              {agent === 'sm' && <SMWizard step={step} data={data} setData={setData} />}
              {agent === 'cs' && <CSWizard step={step} data={data} setData={setData} />}
              {agent === 'ca' && <CAWizard step={step} data={data} setData={setData} />}
            </div>
          </AnimatePresence>
        </div>

        {/* Footer */}
        <div style={{
          padding: '16px 24px', borderTop: '1px solid var(--border)',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <div style={{ display: 'flex', gap: 8 }}>
            {onSkip && step === 0 && (
              <button onClick={onSkip} style={{
                background: 'none', border: 'none', color: 'var(--text-3)', fontSize: 13,
                cursor: 'pointer', padding: '8px 0',
              }}>Skip for now</button>
            )}
            {step > 0 && (
              <button onClick={() => setStep(s => s - 1)} style={{
                padding: '8px 16px', borderRadius: 8, fontSize: 13, fontWeight: 500,
                background: 'var(--surface-2)', border: '1px solid var(--border)',
                color: 'var(--text-2)', cursor: 'pointer',
              }}>← Back</button>
            )}
          </div>
          <button
            onClick={isLast ? handleSave : () => setStep(s => s + 1)}
            style={{
              padding: '10px 24px', borderRadius: 10, fontSize: 13, fontWeight: 700,
              background: cfg.accent, color: '#fff', border: 'none', cursor: 'pointer',
              boxShadow: `0 0 20px ${cfg.accent}44`,
            }}
          >
            {isLast ? '✓ Save Workspace' : 'Continue →'}
          </button>
        </div>
      </motion.div>
    </div>
  )
}
