// frontend/src/pages/DevopsPage.tsx — DevOps Vertical (GitHub + Docker + Prometheus + Jira)
import { useState } from 'react'
import { PageShell, Card, Btn, Input, ResultBox, Tabs, TwoCol, useApi, SectionHead, Badge } from '../components/ui'
import { devopsQuery } from '../lib/api'

const SAMPLE_QUERIES = [
  'Why is the backend service failing? Check recent logs and CI status',
  'Show me all open pull requests pending review',
  'What changed in the last 5 commits that might have caused this error?',
  'Check Prometheus metrics and alert status for the API service',
  'Create a Jira bug ticket for the authentication timeout issue',
]

export default function DevopsPage() {
  const [tab, setTab]             = useState('debug')
  const [query, setQuery]         = useState(SAMPLE_QUERIES[0])
  const [repo, setRepo]           = useState('')
  const [service, setService]     = useState('')
  const [jiraProject, setJira]    = useState('')
  const devopsApi                 = useApi()

  const runQuery = () => {
    devopsApi.call(() => devopsQuery(query, repo.trim(), service.trim(), jiraProject.trim()))
  }

  const data = devopsApi.data as any

  return (
    <PageShell
      icon="⚙️"
      title="AI DevOps Engineer"
      subtitle="GitHub CI/CD, Docker logs, Prometheus metrics, Jira tickets — unified ops intelligence"
    >
      <Tabs
        tabs={[
          { id: 'debug',   label: 'Debug & Analyse', icon: '🔍' },
          { id: 'about',   label: 'Capabilities',    icon: '🛠️' },
        ]}
        active={tab} onChange={setTab}
      />

      {tab === 'debug' && (
        <TwoCol>
          <Card>
            <SectionHead
              title="DevOps Query"
              sub="Describe what's wrong — the agent fetches CI runs, logs, metrics, and correlates root cause"
            />

            {/* Quick examples */}
            <div style={{ marginBottom: 12 }}>
              <label style={{ display: 'block', fontSize: 12, color: '#9ca3af', marginBottom: 6, fontWeight: 500 }}>
                Quick Examples
              </label>
              {SAMPLE_QUERIES.map(q => (
                <button
                  key={q}
                  onClick={() => setQuery(q)}
                  style={{
                    display: 'block', width: '100%', textAlign: 'left',
                    padding: '6px 10px', marginBottom: 4,
                    background: query === q ? 'rgba(99,102,241,0.1)' : 'none',
                    border: `1px solid ${query === q ? '#6366f1' : '#1e2535'}`,
                    borderRadius: 7, color: query === q ? '#a5b4fc' : '#6b7280',
                    fontSize: 12, cursor: 'pointer',
                  }}
                >
                  {q}
                </button>
              ))}
            </div>

            <Input
              label="Query / Problem Description"
              value={query}
              onChange={setQuery}
              rows={3}
            />

            <div style={{
              background: '#0f1117', borderRadius: 8, padding: 12,
              marginBottom: 14, border: '1px solid #1e2535',
            }}>
              <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 10, fontWeight: 500 }}>
                Optional Context (helps the agent target the right resources)
              </div>
              <Input
                label="GitHub Repo  (owner/repo)"
                value={repo}
                onChange={setRepo}
              />
              <Input
                label="Docker Service / Container Name"
                value={service}
                onChange={setService}
              />
              <Input
                label="Jira Project Key (e.g. ENG)"
                value={jiraProject}
                onChange={setJira}
              />
            </div>

            <Btn onClick={runQuery} loading={devopsApi.loading}>
              🔍 Analyse
            </Btn>
          </Card>

          <div>
            {/* Metadata summary */}
            {data?.metadata && !devopsApi.loading && (
              <Card style={{ marginBottom: 12 }}>
                <SectionHead title="Context Used" sub="Sources the agent queried" />
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 10 }}>
                  {data.metadata.repo && (
                    <Badge text={`GitHub: ${data.metadata.repo}`} color="blue" />
                  )}
                  {data.metadata.service && (
                    <Badge text={`Service: ${data.metadata.service}`} color="green" />
                  )}
                  {data.metadata.jira?.created && (
                    <Badge text={`Jira: ${data.metadata.jira.issue_key}`} color="yellow" />
                  )}
                  {!data.metadata.repo && !data.metadata.service && (
                    <span style={{ fontSize: 12, color: '#6b7280' }}>
                      No repo/service detected — add context for richer diagnostics
                    </span>
                  )}
                </div>

                {/* Sources */}
                {data.sources?.length > 0 && (
                  <div>
                    <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 6 }}>Sources</div>
                    {data.sources.map((s: string, i: number) => (
                      <a
                        key={i}
                        href={s}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          display: 'block', fontSize: 11, color: '#6366f1',
                          wordBreak: 'break-all', marginBottom: 3,
                          textDecoration: 'none',
                        }}
                      >
                        🔗 {s}
                      </a>
                    ))}
                  </div>
                )}

                {data.latency_ms && (
                  <div style={{ fontSize: 11, color: '#4b5563', marginTop: 8 }}>
                    ⏱ {Math.round(data.latency_ms)}ms
                  </div>
                )}
              </Card>
            )}

            <ResultBox
              data={data?.content ? { analysis: data.content } : null}
              loading={devopsApi.loading}
              error={devopsApi.error}
              title="Root Cause Analysis"
            />
          </div>
        </TwoCol>
      )}

      {tab === 'about' && (
        <TwoCol>
          <Card>
            <SectionHead title="DevOps Agent Workflow" sub="7-step automated debugging pipeline" />
            {[
              { step: '1', icon: '🔴', title: 'Identify Component',   desc: 'Extracts repo and service names from your query using regex and context hints' },
              { step: '2', icon: '📝', title: 'Fetch Commits',        desc: 'Gets last 5 commits from GitHub — "did something just change?"' },
              { step: '3', icon: '⚙️', title: 'Check CI/CD',         desc: 'Pulls workflow run history: pass/fail status, branch, triggered commit' },
              { step: '4', icon: '🐳', title: 'Docker Logs',         desc: 'Fetches container logs, extracts error lines, checks CPU/memory stats' },
              { step: '5', icon: '📡', title: 'Prometheus Metrics',   desc: 'Queries error rate, p95 latency, availability, and active alert rules' },
              { step: '6', icon: '🧠', title: 'Correlate & Diagnose', desc: 'LLM synthesises all data into root cause + time correlation' },
              { step: '7', icon: '🎫', title: 'Jira Ticket',         desc: 'Optionally creates a bug/task ticket with full diagnostic context' },
            ].map(({ step, icon, title, desc }) => (
              <div key={step} style={{ display: 'flex', gap: 10, marginBottom: 14, alignItems: 'flex-start' }}>
                <div style={{
                  width: 24, height: 24, borderRadius: '50%',
                  background: 'rgba(99,102,241,0.2)', border: '1px solid #6366f1',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 11, color: '#a5b4fc', fontWeight: 700, flexShrink: 0,
                }}>
                  {step}
                </div>
                <div>
                  <div style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 600, marginBottom: 2 }}>
                    {icon} {title}
                  </div>
                  <div style={{ color: '#6b7280', fontSize: 12 }}>{desc}</div>
                </div>
              </div>
            ))}
          </Card>
          <Card>
            <SectionHead title="Integrations" sub="Connected external systems" />
            {[
              { name: 'GitHub',     icon: '🐙', status: 'REST API via token',       badge: 'Commits, PRs, Actions' },
              { name: 'Docker',     icon: '🐳', status: 'Docker daemon socket',      badge: 'Logs, Stats, Container list' },
              { name: 'Prometheus', icon: '📡', status: 'PromQL HTTP API',           badge: 'Metrics, Alerts, Health' },
              { name: 'Jira',       icon: '🎫', status: 'Jira Cloud REST API v3',    badge: 'Create, Search, Sprint' },
            ].map(({ name, icon, status, badge }) => (
              <div key={name} style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '10px 0', borderBottom: '1px solid #1e2535',
              }}>
                <span style={{ fontSize: 22, flexShrink: 0 }}>{icon}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 600 }}>{name}</div>
                  <div style={{ color: '#6b7280', fontSize: 11 }}>{status}</div>
                </div>
                <Badge text={badge} color="blue" />
              </div>
            ))}
            <div style={{ marginTop: 14, padding: 10, background: 'rgba(99,102,241,0.08)', borderRadius: 8 }}>
              <div style={{ fontSize: 11, color: '#a5b4fc', marginBottom: 4 }}>💡 Pro tip</div>
              <div style={{ fontSize: 11, color: '#6b7280' }}>
                Include the repo name (owner/repo) and service name in your query for the deepest diagnostics.
                E.g. <em>"Debug repo myorg/api-service, container backend"</em>
              </div>
            </div>
          </Card>
        </TwoCol>
      )}
    </PageShell>
  )
}
