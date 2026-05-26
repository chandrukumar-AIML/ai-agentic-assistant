// frontend/src/pages/SalesPage.tsx — Feature 16: Sales & CRM
import { useState } from 'react'
import { PageShell, Card, Btn, Input, Select, ResultBox, Tabs, TwoCol, useApi, SectionHead, Badge } from '../components/ui'
import { scoreLead, handleObjection } from '../lib/api'

const SAMPLE_LEAD = {
  name: 'Rajesh Kumar', email: 'rajesh@techindia.com', company: 'TechIndia Solutions',
  title: 'CTO', budget_usd: 75000,
  timeline_days: 60, has_need: true,
  company_size: 200,   // integer: employee count
  phone: '+91-9876543210',
}

const OBJECTIONS = [
  'Your pricing is too high compared to competitors',
  'We are happy with our current solution',
  'We need to think about it more',
  'The timing is not right for us',
  'We need approval from the board',
]

export default function SalesPage() {
  const [tab, setTab]   = useState('score')
  const [lead, setLead] = useState(SAMPLE_LEAD)
  const [objection, setObjection] = useState(OBJECTIONS[0])
  const [product, setProduct]     = useState('AI Agentic Platform')
  const scoreApi = useApi()
  const objApi   = useApi()

  const updateLead = (key: string, val: string | number | boolean) => setLead(p => ({ ...p, [key]: val }))

  return (
    <PageShell icon="💼" title="AI Sales Assistant & Lead Qualifier" subtitle="Feature 16 — BANT scoring (100pts), HubSpot CRM, Salesforce, Clearbit enrichment">
      <Tabs
        tabs={[
          { id: 'score',     label: 'Lead Scoring',  icon: '📊' },
          { id: 'objection', label: 'Objection Handler', icon: '🗣️' },
        ]}
        active={tab} onChange={setTab}
      />

      {tab === 'score' && (
        <TwoCol>
          <Card>
            <SectionHead title="Lead Qualification — BANT Scoring" sub="Budget(25) + Authority(25) + Need(25) + Timeline(25) = 100 pts" />
            <Input label="Full Name" value={lead.name} onChange={v => updateLead('name', v)} />
            <Input label="Email" value={lead.email} onChange={v => updateLead('email', v)} />
            <Input label="Company" value={lead.company} onChange={v => updateLead('company', v)} />
            <Input label="Job Title" value={lead.title} onChange={v => updateLead('title', v)} />
            <Input label="Budget (USD)" value={String(lead.budget_usd)} onChange={v => updateLead('budget_usd', Number(v))} type="number" />
            <Input label="Company Size (employees)" value={String(lead.company_size)} onChange={v => updateLead('company_size', Number(v))} type="number" />
            <Select label="Timeline" value={String(lead.timeline_days)} onChange={v => updateLead('timeline_days', Number(v))}
              options={[
                { label: 'Immediate (≤ 30 days)', value: '30' },
                { label: 'Within 3 months', value: '90' },
                { label: 'Within 6 months', value: '180' },
                { label: 'No clear timeline', value: '365' },
              ]} />
            <Select label="Has Confirmed Need?" value={String(lead.has_need)} onChange={v => updateLead('has_need', v === 'true')}
              options={[{ label: '✅ Yes — confirmed need', value: 'true' }, { label: '❌ No — exploratory', value: 'false' }]} />
            <Btn onClick={() => scoreApi.call(() => scoreLead(lead))} loading={scoreApi.loading}>
              📊 Score Lead
            </Btn>
          </Card>

          <div>
            {scoreApi.data && !scoreApi.loading && (
              <Card style={{ marginBottom: 12 }}>
                <div style={{ textAlign: 'center', marginBottom: 16 }}>
                  <div style={{ fontSize: 48, fontWeight: 700, color: scoreApi.data.score >= 70 ? '#22c55e' : scoreApi.data.score >= 40 ? '#f59e0b' : '#ef4444' }}>
                    {scoreApi.data.score}
                  </div>
                  <div style={{ color: '#6b7280', fontSize: 12 }}>BANT Score / 100</div>
                  <div style={{ marginTop: 8 }}>
                    <Badge
                      text={scoreApi.data.tier || scoreApi.data.classification || 'UNKNOWN'}
                      color={(scoreApi.data.tier || scoreApi.data.classification) === 'HOT' || (scoreApi.data.tier || scoreApi.data.classification) === 'ENTERPRISE' ? 'green' : (scoreApi.data.tier || scoreApi.data.classification) === 'WARM' ? 'yellow' : 'blue'}
                    />
                  </div>
                </div>
                {scoreApi.data.bant && (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 8, marginBottom: 12 }}>
                    {Object.entries(scoreApi.data.bant).map(([k, v]) => (
                      <div key={k} style={{ background: '#0f1117', borderRadius: 8, padding: 10, textAlign: 'center' }}>
                        <div style={{ color: '#e2e8f0', fontSize: 16, fontWeight: 700 }}>{v as number}</div>
                        <div style={{ color: '#6b7280', fontSize: 10, textTransform: 'capitalize' }}>{k}</div>
                        <div style={{ height: 3, background: '#1e2535', borderRadius: 2, marginTop: 6 }}>
                          <div style={{ height: '100%', background: '#6366f1', borderRadius: 2, width: `${((v as number)/25)*100}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                {(scoreApi.data.next_action || scoreApi.data.recommended_action) && (
                  <div style={{ background: 'rgba(99,102,241,0.1)', borderRadius: 8, padding: 12, fontSize: 12, color: '#a5b4fc' }}>
                    💡 {scoreApi.data.next_action || scoreApi.data.recommended_action}
                  </div>
                )}
              </Card>
            )}
            <ResultBox data={scoreApi.data} loading={scoreApi.loading} error={scoreApi.error} title="Full Lead Analysis" />
          </div>
        </TwoCol>
      )}

      {tab === 'objection' && (
        <TwoCol>
          <Card>
            <SectionHead title="Objection Handler" sub="AI-powered responses to common sales objections" />
            <Input label="Product/Service" value={product} onChange={setProduct} />
            <div style={{ marginBottom: 14 }}>
              <label style={{ display: 'block', fontSize: 12, color: '#9ca3af', marginBottom: 6, fontWeight: 500 }}>Common Objections</label>
              {OBJECTIONS.map(o => (
                <button key={o} onClick={() => setObjection(o)} style={{
                  display: 'block', width: '100%', textAlign: 'left', padding: '7px 10px', marginBottom: 5,
                  background: objection === o ? 'rgba(99,102,241,0.1)' : 'none',
                  border: `1px solid ${objection === o ? '#6366f1' : '#1e2535'}`,
                  borderRadius: 7, color: objection === o ? '#a5b4fc' : '#6b7280', fontSize: 12, cursor: 'pointer',
                }}>{o}</button>
              ))}
            </div>
            <Input label="Custom Objection" value={objection} onChange={setObjection} rows={2} />
            <Btn onClick={() => objApi.call(() => handleObjection(objection, product))} loading={objApi.loading}>
              🗣️ Handle Objection
            </Btn>
          </Card>
          <ResultBox data={objApi.data} loading={objApi.loading} error={objApi.error} title="AI Response" />
        </TwoCol>
      )}
    </PageShell>
  )
}
