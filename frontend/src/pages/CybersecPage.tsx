// frontend/src/pages/CybersecPage.tsx — Feature 11
import { useState } from 'react'
import { PageShell, Card, Btn, Input, Select, ResultBox, Tabs, TwoCol, useApi, SectionHead, Badge } from '../components/ui'
import { cybersecQuery, analyzeLogs, searchCVE } from '../lib/api'

const SAMPLE_LOG = `2024-01-15 10:23:41 Failed password for admin from 192.168.1.100 port 22 ssh2
2024-01-15 10:23:42 Failed login attempt invalid password for root
2024-01-15 10:23:43 Failed password for root from 10.0.0.1 port 22 ssh2
2024-01-15 10:23:44 Failed password for user from 192.168.1.100 port 22 ssh2
2024-01-15 10:23:45 Failed login incorrect auth for admin
2024-01-15 10:25:11 GET /search?q=' OR 1=1 -- HTTP/1.1 400 Bad Request
2024-01-15 10:26:03 Request: <script>alert('XSS')</script>
2024-01-15 10:27:15 User-Agent: nmap -sS 192.168.1.0/24`

export default function CybersecPage() {
  const [tab, setTab]           = useState('logs')
  const [logText, setLogText]   = useState(SAMPLE_LOG)
  const [cveKw, setCveKw]       = useState('log4j remote code execution')
  const [severity, setSeverity] = useState('')
  const [query, setQuery]       = useState('What is OWASP Top 10?')

  const logApi = useApi()
  const cveApi = useApi()
  const qApi   = useApi()

  return (
    <PageShell icon="🔐" title="Cybersecurity Monitoring Agent" subtitle="Feature 11 — Log anomaly detection, NVD CVE lookup, Incident reports, Slack alerts">
      <Tabs
        tabs={[
          { id: 'logs', label: 'Log Analysis', icon: '📋' },
          { id: 'cve',  label: 'CVE Lookup',   icon: '🔍' },
          { id: 'ask',  label: 'AI Security',  icon: '🤖' },
        ]}
        active={tab} onChange={setTab}
      />

      {tab === 'logs' && (
        <TwoCol>
          <Card>
            <SectionHead title="Log Anomaly Detection" sub="6 detection rules: Brute Force, SQL Injection, XSS, Dir Traversal, Scanning, Priv Escalation" />
            <Input label="Log Content (paste server/access logs)" value={logText} onChange={setLogText} rows={12} />
            <Btn onClick={() => logApi.call(() => analyzeLogs(logText))} loading={logApi.loading}>
              🔐 Analyze Logs
            </Btn>
          </Card>
          <div>
            {logApi.data && (
              <Card style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
                  <div style={{ flex: 1, background: '#0f1117', borderRadius: 8, padding: 12, textAlign: 'center' }}>
                    <div style={{ fontSize: 22, fontWeight: 700, color: logApi.data.risk_score >= 20 ? '#ef4444' : logApi.data.risk_score >= 10 ? '#f59e0b' : '#22c55e' }}>{logApi.data.risk_score}</div>
                    <div style={{ fontSize: 11, color: '#6b7280' }}>Risk Score</div>
                  </div>
                  <div style={{ flex: 1, background: '#0f1117', borderRadius: 8, padding: 12, textAlign: 'center' }}>
                    <div style={{ fontSize: 22, fontWeight: 700, color: '#e2e8f0' }}>{logApi.data.findings?.length || 0}</div>
                    <div style={{ fontSize: 11, color: '#6b7280' }}>Findings</div>
                  </div>
                  <div style={{ flex: 1, background: '#0f1117', borderRadius: 8, padding: 12, textAlign: 'center' }}>
                    <div style={{ fontSize: 22, fontWeight: 700, color: '#e2e8f0' }}>{logApi.data.lines_analyzed}</div>
                    <div style={{ fontSize: 11, color: '#6b7280' }}>Lines</div>
                  </div>
                </div>
                {logApi.data.findings?.map((f: any) => (
                  <div key={f.rule_id} style={{ background: '#0f1117', border: '1px solid #1e2535', borderRadius: 8, padding: 12, marginBottom: 8, borderLeft: `3px solid ${f.severity === 'CRITICAL' ? '#ef4444' : f.severity === 'HIGH' ? '#f59e0b' : '#22c55e'}` }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 600 }}>{f.name}</span>
                      <Badge text={f.severity} color={f.severity === 'CRITICAL' ? 'red' : f.severity === 'HIGH' ? 'yellow' : 'blue'} />
                    </div>
                    <div style={{ color: '#9ca3af', fontSize: 12 }}>{f.description}</div>
                    <div style={{ color: '#6b7280', fontSize: 11, marginTop: 4 }}>✅ {f.remediation}</div>
                  </div>
                ))}
              </Card>
            )}
            <ResultBox data={logApi.data} loading={logApi.loading} error={logApi.error} title="Full Analysis JSON" />
          </div>
        </TwoCol>
      )}

      {tab === 'cve' && (
        <TwoCol>
          <Card>
            <SectionHead title="NVD CVE Database Search" sub="NIST National Vulnerability Database — no API key required" />
            <Input label="Search Keyword" value={cveKw} onChange={setCveKw} placeholder="e.g. log4j, OpenSSL, Apache RCE" />
            <Select label="Severity Filter" value={severity} onChange={setSeverity}
              options={[{ label: 'All Severities', value: '' }, { label: 'CRITICAL', value: 'CRITICAL' }, { label: 'HIGH', value: 'HIGH' }, { label: 'MEDIUM', value: 'MEDIUM' }]} />
            <div style={{ marginBottom: 12 }}>
              {['log4j','OpenSSL heartbleed','Apache log4shell','Microsoft Exchange RCE','Spring4Shell'].map(k => (
                <button key={k} onClick={() => setCveKw(k)} style={{
                  marginRight: 6, marginBottom: 6, padding: '3px 9px', borderRadius: 20,
                  background: '#1e2535', border: '1px solid #374151', color: '#9ca3af', fontSize: 11, cursor: 'pointer',
                }}>{k}</button>
              ))}
            </div>
            <Btn onClick={() => cveApi.call(() => searchCVE(cveKw, severity || undefined))} loading={cveApi.loading}>
              🔍 Search CVEs
            </Btn>
          </Card>
          <ResultBox data={cveApi.data} loading={cveApi.loading} error={cveApi.error} title="CVE Results" />
        </TwoCol>
      )}

      {tab === 'ask' && (
        <TwoCol>
          <Card>
            <SectionHead title="AI Security Advisor" sub="Senior cybersecurity analyst — NIST/OWASP/ISO 27001" />
            {['What is OWASP Top 10?','How to implement zero-trust architecture?','Best practices for JWT security?','How to prevent SQL injection?'].map(q => (
              <button key={q} onClick={() => setQuery(q)} style={{
                display: 'block', width: '100%', textAlign: 'left', padding: '7px 10px', marginBottom: 5,
                background: query === q ? 'rgba(99,102,241,0.1)' : 'none', border: '1px solid ' + (query === q ? '#6366f1' : '#1e2535'),
                borderRadius: 7, color: query === q ? '#a5b4fc' : '#6b7280', fontSize: 12, cursor: 'pointer',
              }}>{q}</button>
            ))}
            <Input label="Custom Query" value={query} onChange={setQuery} rows={3} />
            <Btn onClick={() => qApi.call(() => cybersecQuery(query))} loading={qApi.loading}>
              🤖 Ask Security AI
            </Btn>
          </Card>
          <ResultBox data={qApi.data} loading={qApi.loading} error={qApi.error} title="Security Advisory" />
        </TwoCol>
      )}
    </PageShell>
  )
}
