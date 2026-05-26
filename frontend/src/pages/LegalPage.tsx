// frontend/src/pages/LegalPage.tsx — Feature 10: Indian Legal Research
import { useState } from 'react'
import { PageShell, Card, Btn, Input, Select, ResultBox, TwoCol, useApi, SectionHead, Badge } from '../components/ui'
import { legalQuery } from '../lib/api'

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

export default function LegalPage() {
  const [query, setQuery]       = useState(SAMPLES.bare_act[0])
  const [language, setLanguage] = useState('en')
  const [category, setCategory] = useState<keyof typeof SAMPLES>('bare_act')
  const api = useApi()

  return (
    <PageShell icon="⚖️" title="Indian Legal Research Agent" subtitle="Feature 10 — IndianKanoon + IPC/CPC/CrPC Bare Acts RAG">
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
              <Btn onClick={() => api.call(() => legalQuery(query, language))} loading={api.loading}>
                ⚖️ Research
              </Btn>
              <Badge text={category === 'case_search' ? 'Case Search' : category === 'bare_act' ? 'Bare Act' : 'Legal Advice'} color="blue" />
            </div>
          </Card>

          <ResultBox data={api.data} loading={api.loading} error={api.error} title="Legal Research Result" />

          {/* Covered sections panel */}
          <Card style={{ marginTop: 16 }}>
            <SectionHead title="Covered Sections (Inline Cache)" sub="Instant answers without LLM" />
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 8 }}>
              {[
                'IPC 302 — Murder', 'IPC 376 — Rape', 'IPC 420 — Cheating',
                'IPC 498A — Cruelty', 'IPC 354 — Modesty',
                'CrPC 41 — Arrest', 'CrPC 125 — Maintenance',
                'IT Act 66 — Cyberoffence', 'IT Act 66A — Struck down',
              ].map(s => (
                <div key={s} style={{
                  background: '#0f1117', border: '1px solid #1e2535',
                  borderRadius: 6, padding: '6px 10px', fontSize: 11, color: '#9ca3af',
                }}>{s}</div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </PageShell>
  )
}
