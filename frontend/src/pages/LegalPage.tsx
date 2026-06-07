// frontend/src/pages/LegalPage.tsx — Feature 10: Indian Legal Research
import { useState } from 'react'
import { PageShell, Card, Btn, Input, Select, ResultBox, Tabs, TwoCol, useApi, SectionHead, Badge } from '../components/ui'
import { legalQuery, legalEnhance } from '../lib/api'

const SAMPLES = {
  case_search: [
    'Supreme Court judgement on right to privacy 2017',
    'High Court verdict on GST input tax credit',
    'Section 138 NI Act cheque bounce case law',
  ],
  bare_act: [
    'IPC section 420 punishment for cheating',
    'CrPC section 41 police arrest without warrant',
    'IT Act section 66A unconstitutional ruling',
    'IPC 498A cruelty by husband',
  ],
  legal_advice: [
    'Can employer terminate without notice during probation?',
    'What are tenant rights under Rent Control Act?',
    'How to file consumer complaint in India?',
  ],
}

const CONTRACT_TYPES  = ['Service Agreement','Employment Contract','Vendor Agreement','Software License','SaaS Terms of Service','NDA','Partnership Deed','Lease Agreement','Consulting Agreement']
const NDA_TYPES       = [{ label: 'Mutual (both parties)', value: 'mutual' }, { label: 'One-way (disclosing party)', value: 'one-way' }]
const JURISDICTIONS   = ['India — Karnataka','India — Maharashtra','India — Tamil Nadu','India — Delhi','India — Telangana','India — Gujarat','Singapore','UAE — DIFC','United Kingdom']

export default function LegalPage() {
  const [tab, setTab] = useState('research')

  // Research tab
  const [query, setQuery]       = useState(SAMPLES.bare_act[0])
  const [language, setLanguage] = useState('en')
  const [category, setCategory] = useState<keyof typeof SAMPLES>('bare_act')
  const researchApi = useApi()

  // Contract Review tab
  const [contractText, setContractText]     = useState('')
  const [contractType, setContractType]     = useState('Service Agreement')
  const [reviewingParty, setReviewingParty] = useState('our company (service provider)')
  const contractApi = useApi()

  // NDA Generator tab
  const [ndaType, setNdaType]           = useState('mutual')
  const [ndaParty1, setNdaParty1]       = useState('Tech Innovations India Pvt Ltd')
  const [ndaParty2, setNdaParty2]       = useState('Client Company Name Pvt Ltd')
  const [ndaPurpose, setNdaPurpose]     = useState('Evaluation and potential engagement for AI platform development services')
  const [ndaDuration, setNdaDuration]   = useState('2 years from signing date')
  const [ndaJurisdiction, setNdaJuris]  = useState('India — Karnataka')
  const ndaApi = useApi()

  return (
    <PageShell icon="⚖️" title="Indian Legal Research Agent" subtitle="Feature 10 — IndianKanoon + IPC/CPC/CrPC Bare Acts + Contract Review + NDA Generator">
      <Tabs
        tabs={[
          { id: 'research',  label: 'Legal Research',  icon: '⚖️' },
          { id: 'contract',  label: 'Contract Review',  icon: '📜' },
          { id: 'nda',       label: 'NDA Generator',    icon: '🤝' },
        ]}
        active={tab} onChange={setTab}
      />

      {/* ── Legal Research ── */}
      {tab === 'research' && (
        <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: 20 }}>
          <div>
            <Card style={{ marginBottom: 16 }}>
              <SectionHead title="Query Settings" />
              <Select label="Language" value={language} onChange={setLanguage}
                options={[{ label: 'English', value: 'en' }, { label: 'Hindi', value: 'hi' }, { label: 'Tamil', value: 'ta' }]} />
              <div style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', fontSize: 12, color: '#9ca3af', marginBottom: 6, fontWeight: 500 }}>Category</label>
                {(['case_search','bare_act','legal_advice'] as const).map(cat => (
                  <button key={cat} onClick={() => { setCategory(cat); setQuery(SAMPLES[cat][0]) }} style={{
                    display: 'block', width: '100%', textAlign: 'left', padding: '7px 10px', marginBottom: 4,
                    background: category === cat ? 'rgba(99,102,241,0.15)' : '#0f1117',
                    border: `1px solid ${category === cat ? '#6366f1' : '#1e2535'}`,
                    borderRadius: 7, color: category === cat ? '#a5b4fc' : '#9ca3af', fontSize: 12, cursor: 'pointer',
                  }}>
                    {cat === 'case_search' ? '⚖️ Case Search' : cat === 'bare_act' ? '📜 Bare Acts' : '💬 Legal Advice'}
                  </button>
                ))}
              </div>
            </Card>
            <Card>
              <SectionHead title="Sample Queries" />
              {SAMPLES[category].map(s => (
                <button key={s} onClick={() => setQuery(s)} style={{
                  display: 'block', width: '100%', textAlign: 'left', padding: '7px 10px', marginBottom: 5,
                  background: query === s ? 'rgba(99,102,241,0.1)' : 'none',
                  border: '1px solid ' + (query === s ? '#6366f1' : '#1e2535'),
                  borderRadius: 7, color: query === s ? '#a5b4fc' : '#6b7280', fontSize: 12, cursor: 'pointer',
                }}>{s}</button>
              ))}
            </Card>
          </div>
          <div>
            <Card style={{ marginBottom: 16 }}>
              <SectionHead title="Legal Query" sub="Ask about cases, sections, or legal advice" />
              <Input value={query} onChange={setQuery} rows={4} label="Query" placeholder="Type your legal question..." />
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <Btn onClick={() => researchApi.call(() => legalQuery(query, language))} loading={researchApi.loading}>
                  ⚖️ Research
                </Btn>
                <Badge text={category === 'case_search' ? 'Case Search' : category === 'bare_act' ? 'Bare Act' : 'Legal Advice'} color="blue" />
              </div>
            </Card>
            <ResultBox data={researchApi.data} loading={researchApi.loading} error={researchApi.error} title="Legal Research Result" />
            <Card style={{ marginTop: 16 }}>
              <SectionHead title="Covered Sections (Inline Cache)" sub="Instant answers without LLM" />
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 8 }}>
                {['IPC 302 — Murder','IPC 376 — Rape','IPC 420 — Cheating','IPC 498A — Cruelty','IPC 354 — Modesty','CrPC 41 — Arrest','CrPC 125 — Maintenance','IT Act 66 — Cyberoffence','IT Act 66A — Struck down'].map(s => (
                  <div key={s} style={{ background: '#0f1117', border: '1px solid #1e2535', borderRadius: 6, padding: '6px 10px', fontSize: 11, color: '#9ca3af' }}>{s}</div>
                ))}
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* ── Contract Review ── */}
      {tab === 'contract' && (
        <TwoCol>
          <Card>
            <SectionHead title="AI Contract Reviewer" sub="Red flags, missing clauses, negotiation points — from your perspective" />
            <Select label="Contract Type" value={contractType} onChange={setContractType}
              options={CONTRACT_TYPES.map(c => ({ label: c, value: c }))} />
            <Input label="Reviewing as (your role/party)" value={reviewingParty} onChange={setReviewingParty} />
            <Input label="Paste Contract Text" value={contractText} onChange={setContractText} rows={14}
              placeholder="Paste the full contract text here..." />
            <div style={{ padding: 10, background: 'rgba(239,68,68,0.08)', borderRadius: 8, marginBottom: 14, border: '1px solid rgba(239,68,68,0.2)' }}>
              <div style={{ fontSize: 11, color: '#ef4444', fontWeight: 600, marginBottom: 4 }}>⚠️ AI Guidance Only</div>
              <div style={{ fontSize: 11, color: '#6b7280' }}>
                This is AI-generated analysis for informational purposes. Always consult a qualified attorney for actual legal matters.
              </div>
            </div>
            <Btn
              onClick={() => contractApi.call(() => legalEnhance('contract_review', {
                contract_type:    contractType,
                reviewing_party:  reviewingParty,
                contract_text:    contractText,
              }))}
              loading={contractApi.loading}
            >
              📜 Review Contract
            </Btn>
          </Card>
          <div>
            <Card style={{ marginBottom: 12 }}>
              <SectionHead title="Review Includes" sub="" />
              {[
                'Executive summary (3 sentences)',
                'Key terms table (Term/Position/Risk)',
                'Red flags with clause references',
                'Missing clauses checklist',
                'Negotiation leverage points',
                'Recommended redlines + alternative language',
              ].map(i => (
                <div key={i} style={{ display: 'flex', gap: 8, padding: '5px 0', borderBottom: '1px solid #1e2535' }}>
                  <span style={{ color: '#22c55e', fontSize: 12 }}>✓</span>
                  <span style={{ color: '#9ca3af', fontSize: 12 }}>{i}</span>
                </div>
              ))}
            </Card>
            <ResultBox data={contractApi.data ? { review: (contractApi.data as any).result } : null} loading={contractApi.loading} error={contractApi.error} title="Contract Review Report" />
          </div>
        </TwoCol>
      )}

      {/* ── NDA Generator ── */}
      {tab === 'nda' && (
        <TwoCol>
          <Card>
            <SectionHead title="NDA Generator" sub="Complete non-disclosure agreement with all standard clauses" />
            <Select label="NDA Type" value={ndaType} onChange={setNdaType} options={NDA_TYPES} />
            <Input label="Party 1 (Full legal name)"       value={ndaParty1}       onChange={setNdaParty1} />
            <Input label="Party 2 (Full legal name)"       value={ndaParty2}       onChange={setNdaParty2} />
            <Input label="Purpose of Disclosure"           value={ndaPurpose}      onChange={setNdaPurpose} rows={2} />
            <Input label="Confidentiality Duration"        value={ndaDuration}     onChange={setNdaDuration} />
            <Select label="Governing Law & Jurisdiction"   value={ndaJurisdiction} onChange={setNdaJuris}
              options={JURISDICTIONS.map(j => ({ label: j, value: j }))} />
            <div style={{ padding: 10, background: 'rgba(99,102,241,0.08)', borderRadius: 8, marginBottom: 14 }}>
              <div style={{ fontSize: 11, color: '#a5b4fc', marginBottom: 4 }}>📄 NDA includes</div>
              <div style={{ fontSize: 11, color: '#6b7280' }}>Recitals • Definition of Confidential Information • Obligations • Permitted disclosures • Return/destruction • Remedies • Term • Dispute resolution • Signature blocks</div>
            </div>
            <Btn
              onClick={() => ndaApi.call(() => legalEnhance('nda_generator', {
                nda_type:     ndaType,
                party1:       ndaParty1,
                party2:       ndaParty2,
                purpose:      ndaPurpose,
                duration:     ndaDuration,
                jurisdiction: ndaJurisdiction,
              }))}
              loading={ndaApi.loading}
            >
              🤝 Generate NDA
            </Btn>
          </Card>
          <ResultBox data={ndaApi.data ? { nda: (ndaApi.data as any).result } : null} loading={ndaApi.loading} error={ndaApi.error} title="Non-Disclosure Agreement" />
        </TwoCol>
      )}
    </PageShell>
  )
}
