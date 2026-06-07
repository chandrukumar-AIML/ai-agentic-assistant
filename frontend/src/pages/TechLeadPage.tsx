// frontend/src/pages/TechLeadPage.tsx — Tech Lead / Architect Vertical
import { useState } from 'react'
import { PageShell, Card, Btn, Input, Select, ResultBox, Tabs, TwoCol, useApi, SectionHead } from '../components/ui'
import { apiFetch, tlEnhance } from '../lib/api'

const tlAction = (action: string, payload: object) =>
  apiFetch('/verticals/techlead/action', { method: 'POST', body: JSON.stringify({ action, payload }) }, 360_000)

const AUTH_TYPES = ['JWT', 'OAuth2', 'API Key', 'Session Cookie', 'mTLS']

export default function TechLeadPage() {
  const [tab, setTab] = useState('adr')

  // ADR tab
  const [adrTitle, setAdrTitle]     = useState('Use PostgreSQL instead of MongoDB for the main application database')
  const [adrContext, setAdrContext]  = useState('We are building a multi-tenant SaaS platform. Data is highly relational (users → orgs → projects → tasks). We need ACID guarantees for billing and audit logs. The team has strong SQL experience. Expected scale: 10M rows in 3 years.')
  const [adrOptions, setAdrOptions] = useState('PostgreSQL 16 with asyncpg\nMongoDB 7 with Motor\nCockroachDB (distributed SQL)\nPlanetScale (MySQL-compatible)')
  const [adrDecision, setAdrDecision] = useState('PostgreSQL 16 with asyncpg')
  const adrApi                       = useApi()

  // Tech Debt tab
  const [codebaseDesc, setCodebaseDesc] = useState('FastAPI backend, 45K LOC, 3 years old. No type hints on 60% of functions. Tests at 23% coverage. God-class APIRouter file (3000 lines). Direct DB queries in route handlers (no repository pattern). No async everywhere — some blocking I/O in async functions. 12 TODO comments for critical paths.')
  const [knownIssues, setKnownIssues]   = useState('No repository pattern — DB calls everywhere\nSingle APIRouter file is 3000+ lines\nBlocking I/O in async route handlers\nNo integration tests — only unit tests\n60% of functions have no type hints\nOutdated dependencies (8 CVEs)')
  const [teamSize, setTeamSize]         = useState('6')
  const debtApi                         = useApi()

  // API Design tab
  const [apiName, setApiName]       = useState('Task Management API')
  const [resources, setResources]   = useState('projects\ntasks\nusers\ncomments\nattachments\nlabels')
  const [useCases, setUseCases]     = useState('Create and manage projects and tasks. Assign tasks to users. Comment on tasks. Attach files. Filter tasks by status, priority, label, assignee, and due date. Support bulk operations. Webhooks for task state changes.')
  const [authType, setAuthType]     = useState('JWT')
  const apiApi                      = useApi()

  // Architecture Review tab
  const [sysDesc, setSysDesc]         = useState('Monolithic FastAPI app + React frontend. PostgreSQL main DB. Redis for sessions and caching. Celery for background jobs. All on a single Render instance. No CDN. Direct DB queries in all routes. Single deployment unit for all features.')
  const [currentScale, setCurrentScale] = useState('500 DAU, 50 req/sec peak, 2GB RAM, 5M rows in DB')
  const [targetScale, setTargetScale]   = useState('50,000 DAU, 2000 req/sec peak, global users, 99.9% SLA')
  const [painPoints, setPainPoints]     = useState('Deploys take 8 minutes and require downtime\nSingle DB connection pool shared by all features\nBackground jobs block API responses\nNo caching layer — DB hit on every request\nNo horizontal scaling possible')
  const archApi                         = useApi()

  // Performance tab
  const [symptoms, setSymptoms]     = useState('API p99 latency spiked from 200ms to 4s after the last deploy. Dashboard page takes 8 seconds to load. DB CPU hits 95% at 9am every day. Users report timeouts on search. Memory usage growing 50MB/hour — possible leak.')
  const [sysInfo, setSysInfo]       = useState('FastAPI + PostgreSQL + Redis. 4 CPU, 8GB RAM server. 10M rows in tasks table. Redis hit rate 45%.')
  const [perfMetrics, setPerfMetrics] = useState('p50_latency_ms: 180\np99_latency_ms: 4200\ndb_query_avg_ms: 340\nredis_hit_rate: 0.45\nmemory_mb: 5800\ncpu_pct: 78\nactive_connections: 94\nrequests_per_sec: 120')
  const perfApi                     = useApi()

  // Tech Radar tab
  const [teamCtx, setTeamCtx]       = useState('8-person product engineering team building a B2B SaaS platform. Stack: Python/FastAPI backend, React/TypeScript frontend, PostgreSQL, Redis. 3 years old codebase. Currently evaluating: moving to microservices, adopting Kubernetes, adding GraphQL.')
  const [currentStack, setCurrentStack] = useState('Python/FastAPI\nReact 18/TypeScript\nPostgreSQL 15\nRedis 7\nDocker + Render\nGitHub Actions\nSentry\nDatadog')
  const radarApi                        = useApi()

  // Vendor Evaluation tab
  const [vendorName, setVendorName]     = useState('Datadog')
  const [vendorCat, setVendorCat]       = useState('Observability & APM platform')
  const [vendorReqs, setVendorReqs]     = useState('Real-time metrics, distributed tracing, log aggregation, alerting, 99.9% uptime SLA, SOC2 compliance, Python/FastAPI integration, custom dashboards')
  const [vendorAlts, setVendorAlts]     = useState('New Relic, Grafana Cloud, Dynatrace, AWS CloudWatch + X-Ray')
  const [vendorBudget, setVendorBudget] = useState('$30,000/year')
  const vendorApi                       = useApi()

  // Build vs Buy tab
  const [buildFeature, setBuildFeature]   = useState('Multi-factor authentication (MFA) system')
  const [buildTeam, setBuildTeam]         = useState('4')
  const [buildTimeline, setBuildTimeline] = useState('2 months')
  const [buildVendors, setBuildVendors]   = useState('Auth0, AWS Cognito, Okta, Firebase Auth')
  const bvbApi                            = useApi()

  const parseMetrics = (raw: string): Record<string, string> =>
    Object.fromEntries(
      raw.split('\n')
        .map(l => l.split(':').map(s => s.trim()))
        .filter(p => p.length === 2)
    )

  return (
    <PageShell
      icon="🏗️"
      title="AI Tech Lead"
      subtitle="Architecture Decision Records, tech debt, API design, architecture reviews, and tech radar"
    >
      <Tabs
        tabs={[
          { id: 'adr',    label: 'ADR Generator',     icon: '📄' },
          { id: 'debt',   label: 'Tech Debt',         icon: '💳' },
          { id: 'api',    label: 'API Design',        icon: '🔌' },
          { id: 'arch',   label: 'Arch Review',       icon: '🏗️' },
          { id: 'perf',   label: 'Performance',       icon: '⚡' },
          { id: 'radar',  label: 'Tech Radar',        icon: '📡' },
          { id: 'vendor', label: 'Vendor Eval',       icon: '🏢' },
        ]}
        active={tab} onChange={setTab}
      />

      {/* ── ADR ── */}
      {tab === 'adr' && (
        <TwoCol>
          <Card>
            <SectionHead title="ADR Generator" sub="Decision → formal Architecture Decision Record in Michael Nygard format" />
            <Input label="Decision Title"        value={adrTitle}    onChange={setAdrTitle} />
            <Input label="Context & Problem"     value={adrContext}  onChange={setAdrContext}  rows={4} />
            <Input label="Options Considered (one per line)" value={adrOptions} onChange={setAdrOptions} rows={4} />
            <Input label="Preferred Decision"    value={adrDecision} onChange={setAdrDecision} />
            <Btn
              onClick={() => adrApi.call(() => tlAction('adr', {
                decision_title:     adrTitle,
                context:            adrContext,
                options_considered: adrOptions.split('\n').map(l => l.trim()).filter(Boolean),
                decision:           adrDecision,
              }))}
              loading={adrApi.loading}
            >
              📄 Generate ADR
            </Btn>
          </Card>
          <ResultBox
            data={adrApi.data ? { adr: (adrApi.data as any).adr } : null}
            loading={adrApi.loading}
            error={adrApi.error}
            title="Architecture Decision Record"
          />
        </TwoCol>
      )}

      {/* ── Tech Debt ── */}
      {tab === 'debt' && (
        <TwoCol>
          <Card>
            <SectionHead title="Tech Debt Analyzer" sub="Codebase description → ranked debt backlog with ROI estimates" />
            <Input label="Codebase Description" value={codebaseDesc} onChange={setCodebaseDesc} rows={5} />
            <Input label="Known Issues (one per line)" value={knownIssues} onChange={setKnownIssues} rows={6} />
            <Input label="Team Size" value={teamSize} onChange={setTeamSize} />
            <Btn
              onClick={() => debtApi.call(() => tlAction('tech_debt', {
                codebase_description: codebaseDesc,
                known_issues:         knownIssues.split('\n').map(l => l.trim()).filter(Boolean),
                team_size:            parseInt(teamSize) || 5,
              }))}
              loading={debtApi.loading}
            >
              💳 Analyze Debt
            </Btn>
          </Card>
          <ResultBox
            data={debtApi.data ? { analysis: (debtApi.data as any).analysis } : null}
            loading={debtApi.loading}
            error={debtApi.error}
            title="Tech Debt Report"
          />
        </TwoCol>
      )}

      {/* ── API Design ── */}
      {tab === 'api' && (
        <TwoCol>
          <Card>
            <SectionHead title="REST API Designer" sub="Resources + use cases → OpenAPI spec with all endpoints" />
            <Input label="API Name"           value={apiName}   onChange={setApiName} />
            <Input label="Resources (one per line)" value={resources} onChange={setResources} rows={4} />
            <Input label="Use Cases"          value={useCases}  onChange={setUseCases} rows={4} />
            <Select
              label="Authentication Type"
              value={authType}
              onChange={setAuthType}
              options={AUTH_TYPES.map(t => ({ value: t, label: t }))}
            />
            <Btn
              onClick={() => apiApi.call(() => tlAction('api_design', {
                api_name:  apiName,
                resources: resources.split('\n').map(l => l.trim()).filter(Boolean),
                use_cases: useCases,
                auth_type: authType,
              }))}
              loading={apiApi.loading}
            >
              🔌 Design API
            </Btn>
          </Card>
          <ResultBox
            data={apiApi.data ? { design: (apiApi.data as any).design } : null}
            loading={apiApi.loading}
            error={apiApi.error}
            title="API Design"
          />
        </TwoCol>
      )}

      {/* ── Architecture Review ── */}
      {tab === 'arch' && (
        <TwoCol>
          <Card>
            <SectionHead title="Architecture Reviewer" sub="Current system → Well-Architected review with migration roadmap" />
            <Input label="System Description"    value={sysDesc}       onChange={setSysDesc}       rows={4} />
            <Input label="Current Scale"         value={currentScale}  onChange={setCurrentScale} />
            <Input label="Target Scale"          value={targetScale}   onChange={setTargetScale} />
            <Input label="Pain Points (one per line)" value={painPoints} onChange={setPainPoints}  rows={5} />
            <Btn
              onClick={() => archApi.call(() => tlAction('arch_review', {
                system_description: sysDesc,
                current_scale:      currentScale,
                target_scale:       targetScale,
                pain_points:        painPoints.split('\n').map(l => l.trim()).filter(Boolean),
              }))}
              loading={archApi.loading}
            >
              🏗️ Review Architecture
            </Btn>
          </Card>
          <ResultBox
            data={archApi.data ? { review: (archApi.data as any).review } : null}
            loading={archApi.loading}
            error={archApi.error}
            title="Architecture Review"
          />
        </TwoCol>
      )}

      {/* ── Performance Analysis ── */}
      {tab === 'perf' && (
        <TwoCol>
          <Card>
            <SectionHead title="Performance Analyzer" sub="Symptoms + metrics → root cause, quick wins, architecture fixes" />
            <Input label="Symptoms / Problem Description" value={symptoms}    onChange={setSymptoms}    rows={4} />
            <Input label="System Info"                    value={sysInfo}     onChange={setSysInfo} />
            <Input label="Metrics (key: value)"          value={perfMetrics} onChange={setPerfMetrics} rows={8} />
            <Btn
              onClick={() => perfApi.call(() => tlAction('perf_analysis', {
                symptoms:    symptoms,
                system_info: sysInfo,
                metrics:     parseMetrics(perfMetrics),
              }))}
              loading={perfApi.loading}
            >
              ⚡ Analyze Performance
            </Btn>
          </Card>
          <ResultBox
            data={perfApi.data ? { analysis: (perfApi.data as any).analysis } : null}
            loading={perfApi.loading}
            error={perfApi.error}
            title="Performance Analysis"
          />
        </TwoCol>
      )}

      {/* ── Tech Radar ── */}
      {tab === 'radar' && (
        <TwoCol>
          <Card>
            <SectionHead title="Technology Radar" sub="Team context → Thoughtworks-style radar with Adopt/Trial/Assess/Hold" />
            <Input label="Team Context"         value={teamCtx}      onChange={setTeamCtx}      rows={4} />
            <Input label="Current Stack (one per line)" value={currentStack} onChange={setCurrentStack} rows={8} />
            <div style={{ padding: 10, background: 'rgba(16,185,129,0.08)', borderRadius: 8, marginBottom: 14 }}>
              <div style={{ fontSize: 11, color: '#5eead4', fontWeight: 600, marginBottom: 6 }}>Radar Rings</div>
              {[
                { ring: 'ADOPT',  color: '#22c55e', desc: 'Use in production now' },
                { ring: 'TRIAL',  color: '#10b981', desc: 'Try on low-risk project' },
                { ring: 'ASSESS', color: '#eab308', desc: 'Research and spike' },
                { ring: 'HOLD',   color: '#ef4444', desc: 'Migrate away from' },
              ].map(({ ring, color, desc }) => (
                <div key={ring} style={{ display: 'flex', gap: 8, marginBottom: 4, alignItems: 'center' }}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: color, flexShrink: 0 }} />
                  <span style={{ color, fontSize: 11, fontWeight: 600, minWidth: 55 }}>{ring}</span>
                  <span style={{ color: '#6b7280', fontSize: 11 }}>{desc}</span>
                </div>
              ))}
            </div>
            <Btn
              onClick={() => radarApi.call(() => tlAction('tech_radar', {
                team_context:  teamCtx,
                current_stack: currentStack.split('\n').map(l => l.trim()).filter(Boolean),
              }))}
              loading={radarApi.loading}
            >
              📡 Generate Tech Radar
            </Btn>
          </Card>
          <ResultBox
            data={radarApi.data ? { radar: (radarApi.data as any).radar } : null}
            loading={radarApi.loading}
            error={radarApi.error}
            title="Technology Radar"
          />
        </TwoCol>
      )}
      {/* ── Vendor Evaluation ── */}
      {tab === 'vendor' && (
        <TwoCol>
          <Card>
            <SectionHead title="Vendor Evaluation" sub="Scorecard, TCO, build-vs-buy analysis, contract negotiation points" />
            <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
              {[
                { label: 'Vendor Scorecard', value: 'vendor_eval' },
                { label: 'Build vs Buy', value: 'build_vs_buy' },
              ].map(({ label, value }) => {
                const currentAction = value === 'vendor_eval' ? 'vendor_eval' : 'build_vs_buy'
                return (
                  <div key={value} />
                )
              })}
            </div>

            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 12, color: '#5eead4', fontWeight: 600, marginBottom: 12, paddingBottom: 8, borderBottom: '1px solid #1e2535' }}>
                📊 Vendor Scorecard
              </div>
              <Input label="Vendor Name"      value={vendorName}   onChange={setVendorName} />
              <Input label="Category"         value={vendorCat}    onChange={setVendorCat} />
              <Input label="Annual Budget"    value={vendorBudget} onChange={setVendorBudget} />
              <Input label="Requirements"     value={vendorReqs}   onChange={setVendorReqs}   rows={4} />
              <Input label="Alternatives"     value={vendorAlts}   onChange={setVendorAlts}   rows={2} />
              <Btn
                onClick={() => vendorApi.call(() => tlEnhance('vendor_eval', {
                  vendor_name:   vendorName,
                  category:      vendorCat,
                  annual_budget: vendorBudget,
                  requirements:  vendorReqs,
                  alternatives:  vendorAlts,
                }))}
                loading={vendorApi.loading}
              >
                🏢 Evaluate Vendor
              </Btn>
            </div>

            <div style={{ borderTop: '1px solid #1e2535', paddingTop: 16 }}>
              <div style={{ fontSize: 12, color: '#5eead4', fontWeight: 600, marginBottom: 12 }}>
                ⚖️ Build vs Buy
              </div>
              <Input label="Feature to Build/Buy"   value={buildFeature}   onChange={setBuildFeature} />
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <Input label="Team Size (engineers)" value={buildTeam}     onChange={setBuildTeam} />
                <Input label="Timeline"              value={buildTimeline} onChange={setBuildTimeline} />
              </div>
              <Input label="Vendor Options"          value={buildVendors}  onChange={setBuildVendors} rows={2} />
              <Btn
                onClick={() => bvbApi.call(() => tlEnhance('build_vs_buy', {
                  feature:        buildFeature,
                  team_size:      buildTeam,
                  timeline:       buildTimeline,
                  vendor_options: buildVendors,
                }))}
                loading={bvbApi.loading}
              >
                ⚖️ Analyse Build vs Buy
              </Btn>
            </div>
          </Card>
          <div>
            {vendorApi.data && (
              <div style={{ marginBottom: 12 }}>
                <ResultBox data={{ evaluation: (vendorApi.data as any).result }} loading={vendorApi.loading} error={vendorApi.error} title="Vendor Evaluation" />
              </div>
            )}
            <ResultBox data={bvbApi.data ? { analysis: (bvbApi.data as any).result } : null} loading={bvbApi.loading} error={bvbApi.error} title="Build vs Buy Analysis" />
          </div>
        </TwoCol>
      )}
    </PageShell>
  )
}
