// frontend/src/pages/QAPage.tsx — QA Engineer Vertical
import { useState } from 'react'
import { PageShell, Card, Btn, Input, Select, ResultBox, Tabs, TwoCol, useApi, SectionHead, Badge } from '../components/ui'
import { apiFetch } from '../lib/api'

const qaAction = (action: string, payload: object) =>
  apiFetch('/verticals/qa/action', {
    method: 'POST',
    body: JSON.stringify({ action, payload }),
  }, 360_000)

const TEST_TYPES = ['unit', 'integration', 'e2e', 'performance', 'security']
const FRAMEWORKS = ['pytest', 'jest', 'junit', 'mocha', 'cypress', 'playwright']
const SEVERITIES  = ['Critical', 'Major', 'Minor', 'Trivial']

export default function QAPage() {
  const [tab, setTab] = useState('tests')

  // Generate Tests tab
  const [featureDesc, setFeatureDesc]   = useState('User can log in with email and password. If credentials are wrong, show error. After 5 failed attempts, lock the account for 15 minutes.')
  const [testType, setTestType]         = useState('unit')
  const [framework, setFramework]       = useState('pytest')
  const testsApi                        = useApi()

  // Bug Analysis tab
  const [bugDesc, setBugDesc]           = useState('Login button stops working after user switches tabs and comes back. The button becomes unresponsive. Refresh fixes it.')
  const [bugLogs, setBugLogs]           = useState('')
  const [bugEnv, setBugEnv]             = useState('Chrome 120, macOS 14, React 18')
  const bugApi                          = useApi()

  // Test Plan tab
  const [planProject, setPlanProject]   = useState('AI Agentic Platform v2')
  const [planScope, setPlanScope]       = useState('Authentication, Dashboard, and all 19 vertical features')
  const [planModules, setPlanModules]   = useState('Auth, Chat, AgriTech, Legal, HR, Sales, Email')
  const [planDays, setPlanDays]         = useState('21')
  const planApi                         = useApi()

  // Acceptance Criteria tab
  const [userStory, setUserStory]       = useState('As a sales manager, I want to see a lead score dashboard so that I can prioritise which leads my team should contact first.')
  const acApi                           = useApi()

  return (
    <PageShell
      icon="🧪"
      title="AI QA Engineer"
      subtitle="Test case generation, bug analysis, test plans, and Gherkin acceptance criteria"
    >
      <Tabs
        tabs={[
          { id: 'tests',  label: 'Generate Tests',       icon: '🧪' },
          { id: 'bug',    label: 'Bug Analysis',         icon: '🐛' },
          { id: 'plan',   label: 'Test Plan',            icon: '📋' },
          { id: 'ac',     label: 'Acceptance Criteria',  icon: '✅' },
        ]}
        active={tab} onChange={setTab}
      />

      {/* ── Generate Tests ── */}
      {tab === 'tests' && (
        <TwoCol>
          <Card>
            <SectionHead title="Test Case Generator" sub="Describe the feature — get test cases + code stubs" />
            <Input
              label="Feature Description"
              value={featureDesc}
              onChange={setFeatureDesc}
              rows={5}
            />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 14 }}>
              <Select
                label="Test Type"
                value={testType}
                onChange={setTestType}
                options={TEST_TYPES.map(t => ({ value: t, label: t.charAt(0).toUpperCase() + t.slice(1) }))}
              />
              <Select
                label="Framework"
                value={framework}
                onChange={setFramework}
                options={FRAMEWORKS.map(f => ({ value: f, label: f }))}
              />
            </div>
            <Btn
              onClick={() => testsApi.call(() => qaAction('generate_tests', {
                feature_description: featureDesc,
                test_type: testType,
                framework,
              }))}
              loading={testsApi.loading}
            >
              🧪 Generate Test Cases
            </Btn>
          </Card>
          <ResultBox
            data={testsApi.data ? { test_cases: (testsApi.data as any).test_cases } : null}
            loading={testsApi.loading}
            error={testsApi.error}
            title="Generated Test Cases"
          />
        </TwoCol>
      )}

      {/* ── Bug Analysis ── */}
      {tab === 'bug' && (
        <TwoCol>
          <Card>
            <SectionHead title="Bug Report Analyzer" sub="Paste bug description — get root cause, severity, fix recommendations" />
            <Input
              label="Bug Description"
              value={bugDesc}
              onChange={setBugDesc}
              rows={4}
            />
            <Input
              label="Environment (browser, OS, version)"
              value={bugEnv}
              onChange={setBugEnv}
            />
            <Input
              label="Logs / Stack Trace (optional)"
              value={bugLogs}
              onChange={setBugLogs}
              rows={4}
            />
            <Btn
              onClick={() => bugApi.call(() => qaAction('analyze_bug', {
                bug_description: bugDesc,
                logs: bugLogs,
                environment: bugEnv,
              }))}
              loading={bugApi.loading}
            >
              🐛 Analyze Bug
            </Btn>
          </Card>
          <div>
            {(bugApi.data as any)?.analysis && !bugApi.loading && (
              <Card style={{ marginBottom: 12 }}>
                <SectionHead title="Severity Reference" sub="" />
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {[
                    { label: 'Critical', color: '#ef4444', desc: 'System crash / data loss' },
                    { label: 'Major',    color: '#f97316', desc: 'Feature broken' },
                    { label: 'Minor',    color: '#eab308', desc: 'Partial degradation' },
                    { label: 'Trivial',  color: '#6b7280', desc: 'Cosmetic issue' },
                  ].map(s => (
                    <div key={s.label} style={{ padding: '4px 8px', borderRadius: 6, background: s.color + '22', border: `1px solid ${s.color}44` }}>
                      <span style={{ color: s.color, fontSize: 11, fontWeight: 600 }}>{s.label}</span>
                      <span style={{ color: '#6b7280', fontSize: 10, marginLeft: 4 }}>{s.desc}</span>
                    </div>
                  ))}
                </div>
              </Card>
            )}
            <ResultBox
              data={bugApi.data ? { analysis: (bugApi.data as any).analysis } : null}
              loading={bugApi.loading}
              error={bugApi.error}
              title="Bug Analysis Report"
            />
          </div>
        </TwoCol>
      )}

      {/* ── Test Plan ── */}
      {tab === 'plan' && (
        <TwoCol>
          <Card>
            <SectionHead title="Test Plan Generator" sub="Enterprise-grade test plan with coverage matrix and schedule" />
            <Input label="Project Name"        value={planProject}  onChange={setPlanProject} />
            <Input label="Test Scope"          value={planScope}    onChange={setPlanScope} rows={2} />
            <Input label="Modules (comma-sep)" value={planModules}  onChange={setPlanModules} />
            <Input label="Timeline (days)"     value={planDays}     onChange={setPlanDays} />
            <Btn
              onClick={() => planApi.call(() => qaAction('test_plan', {
                project_name:  planProject,
                scope:         planScope,
                modules:       planModules.split(',').map(m => m.trim()).filter(Boolean),
                timeline_days: parseInt(planDays) || 14,
              }))}
              loading={planApi.loading}
            >
              📋 Generate Test Plan
            </Btn>
          </Card>
          <ResultBox
            data={planApi.data ? { test_plan: (planApi.data as any).test_plan } : null}
            loading={planApi.loading}
            error={planApi.error}
            title="Test Plan"
          />
        </TwoCol>
      )}

      {/* ── Acceptance Criteria ── */}
      {tab === 'ac' && (
        <TwoCol>
          <Card>
            <SectionHead title="Acceptance Criteria Generator" sub="User story → Gherkin scenarios + Definition of Done" />
            <Input
              label="User Story"
              value={userStory}
              onChange={setUserStory}
              rows={4}
            />
            <div style={{
              padding: 12, background: 'rgba(99,102,241,0.08)', borderRadius: 8,
              marginBottom: 14, border: '1px solid rgba(99,102,241,0.2)',
            }}>
              <div style={{ fontSize: 11, color: '#a5b4fc', marginBottom: 4, fontWeight: 600 }}>Format reminder</div>
              <div style={{ fontSize: 11, color: '#6b7280' }}>
                "As a [persona], I want [goal] so that [benefit]"
              </div>
            </div>
            <Btn
              onClick={() => acApi.call(() => qaAction('acceptance_criteria', { user_story: userStory }))}
              loading={acApi.loading}
            >
              ✅ Generate Criteria
            </Btn>
          </Card>
          <div>
            <Card style={{ marginBottom: 12 }}>
              <SectionHead title="Gherkin Syntax" sub="BDD format" />
              {[
                { keyword: 'Feature:', desc: 'High-level feature description' },
                { keyword: 'Scenario:', desc: 'Specific behaviour to test' },
                { keyword: 'Given',    desc: 'Precondition / starting state' },
                { keyword: 'When',     desc: 'Action performed by user/system' },
                { keyword: 'Then',     desc: 'Expected observable outcome' },
                { keyword: 'And / But', desc: 'Additional steps in same clause' },
              ].map(({ keyword, desc }) => (
                <div key={keyword} style={{ display: 'flex', gap: 10, marginBottom: 6, alignItems: 'flex-start' }}>
                  <code style={{ color: '#a5b4fc', fontSize: 11, minWidth: 90, fontFamily: 'monospace' }}>{keyword}</code>
                  <span style={{ color: '#6b7280', fontSize: 11 }}>{desc}</span>
                </div>
              ))}
            </Card>
            <ResultBox
              data={acApi.data ? { criteria: (acApi.data as any).acceptance_criteria } : null}
              loading={acApi.loading}
              error={acApi.error}
              title="Acceptance Criteria"
            />
          </div>
        </TwoCol>
      )}
    </PageShell>
  )
}
