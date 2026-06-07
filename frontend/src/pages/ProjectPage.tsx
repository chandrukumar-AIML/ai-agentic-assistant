// frontend/src/pages/ProjectPage.tsx — Project Manager / Scrum Vertical
import { useState } from 'react'
import { PageShell, Card, Btn, Input, Select, ResultBox, Tabs, TwoCol, useApi, SectionHead } from '../components/ui'
import { apiFetch } from '../lib/api'

const pmAction = (action: string, payload: object) =>
  apiFetch('/verticals/pm/action', {
    method: 'POST',
    body: JSON.stringify({ action, payload }),
  }, 360_000)

const PERSONAS   = ['user', 'admin', 'manager', 'developer', 'customer', 'analyst']
const PRIORITIES = ['high', 'medium', 'low']
const TECHNIQUES = ['planning_poker', 'pert', 't_shirt_sizing']

export default function ProjectPage() {
  const [tab, setTab] = useState('stories')

  // User Stories tab
  const [featureIdea, setFeatureIdea] = useState('Build a lead scoring dashboard that shows all leads ranked by AI score, with color-coded priority bands and one-click CRM sync.')
  const [persona, setPersona]         = useState('user')
  const [priority, setPriority]       = useState('high')
  const storiesApi                    = useApi()

  // Sprint Plan tab
  const [teamSize, setTeamSize]           = useState('5')
  const [sprintWeeks, setSprintWeeks]     = useState('2')
  const [velocity, setVelocity]           = useState('0')
  const [backlogRaw, setBacklogRaw]       = useState(
    'User login and registration\nAI chat interface\nLead scoring dashboard\nEmail campaign manager\nBilling and subscription management'
  )
  const sprintApi                         = useApi()

  // Retrospective tab
  const [retroSprint, setRetroSprint]    = useState('3')
  const [wentWell, setWentWell]          = useState('Daily standups were focused\nCode reviews improved quality\nCI/CD pipeline reduced deployment time')
  const [improvements, setImprovements]  = useState('Sprint planning took too long\nToo many context switches\nDocumentation always left to last')
  const [actionItems, setActionItems]    = useState('Timebox planning to 2 hours\nIntroduce WIP limits\nAdd doc tasks to definition of done')
  const retroApi                         = useApi()

  // Roadmap tab
  const [productName, setProductName]    = useState('AI Agentic Platform')
  const [vision, setVision]             = useState('Become the leading AI productivity suite for enterprise teams in India, delivering ROI in 30 days.')
  const [themes, setThemes]             = useState('AI-first workflow automation\nEnterprise integrations & CRM\nSecurity, compliance & audit\nMobile-first experience')
  const [quarters, setQuarters]          = useState('4')
  const roadmapApi                       = useApi()

  // Estimation tab
  const [storiesRaw, setStoriesRaw]      = useState(
    'Implement OAuth login with Google and Microsoft\nBuild real-time dashboard with WebSocket updates\nIntegrate Stripe payment gateway\nCreate PDF report generator\nBuild multi-language support (i18n)'
  )
  const [technique, setTechnique]        = useState('planning_poker')
  const estimateApi                      = useApi()

  const splitLines = (text: string) =>
    text.split('\n').map(l => l.trim()).filter(Boolean)

  return (
    <PageShell
      icon="📋"
      title="AI Project Manager"
      subtitle="User stories, sprint planning, retrospectives, roadmaps, and story point estimation"
    >
      <Tabs
        tabs={[
          { id: 'stories',   label: 'User Stories',    icon: '📝' },
          { id: 'sprint',    label: 'Sprint Plan',      icon: '🏃' },
          { id: 'retro',     label: 'Retrospective',    icon: '🔄' },
          { id: 'roadmap',   label: 'Roadmap',          icon: '🗺️' },
          { id: 'estimate',  label: 'Estimation',       icon: '📊' },
        ]}
        active={tab} onChange={setTab}
      />

      {/* ── User Stories ── */}
      {tab === 'stories' && (
        <TwoCol>
          <Card>
            <SectionHead title="User Story Generator" sub="Feature idea → INVEST-compliant user stories with story points" />
            <Input
              label="Feature Idea"
              value={featureIdea}
              onChange={setFeatureIdea}
              rows={4}
            />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 14 }}>
              <Select
                label="Persona"
                value={persona}
                onChange={setPersona}
                options={PERSONAS.map(p => ({ value: p, label: p.charAt(0).toUpperCase() + p.slice(1) }))}
              />
              <Select
                label="Priority"
                value={priority}
                onChange={setPriority}
                options={PRIORITIES.map(p => ({ value: p, label: p.charAt(0).toUpperCase() + p.slice(1) }))}
              />
            </div>
            <div style={{ padding: 10, background: 'rgba(16,185,129,0.08)', borderRadius: 8, marginBottom: 14 }}>
              <div style={{ fontSize: 11, color: '#5eead4', fontWeight: 600, marginBottom: 4 }}>INVEST Criteria</div>
              {['Independent', 'Negotiable', 'Valuable', 'Estimable', 'Small', 'Testable'].map(i => (
                <span key={i} style={{ fontSize: 10, color: '#6b7280', marginRight: 8 }}>✓ {i}</span>
              ))}
            </div>
            <Btn
              onClick={() => storiesApi.call(() => pmAction('user_story', { feature_idea: featureIdea, persona, priority }))}
              loading={storiesApi.loading}
            >
              📝 Generate User Stories
            </Btn>
          </Card>
          <ResultBox
            data={storiesApi.data ? { stories: (storiesApi.data as any).user_stories } : null}
            loading={storiesApi.loading}
            error={storiesApi.error}
            title="User Stories"
          />
        </TwoCol>
      )}

      {/* ── Sprint Plan ── */}
      {tab === 'sprint' && (
        <TwoCol>
          <Card>
            <SectionHead title="Sprint Planner" sub="Backlog items → prioritized sprint with capacity allocation" />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, marginBottom: 14 }}>
              <Input label="Team Size"        value={teamSize}    onChange={setTeamSize} />
              <Input label="Sprint (weeks)"   value={sprintWeeks} onChange={setSprintWeeks} />
              <Input label="Velocity (pts, 0=auto)" value={velocity} onChange={setVelocity} />
            </div>
            <Input
              label="Backlog Items (one per line)"
              value={backlogRaw}
              onChange={setBacklogRaw}
              rows={7}
            />
            <Btn
              onClick={() => sprintApi.call(() => pmAction('sprint_plan', {
                team_size:             parseInt(teamSize) || 5,
                sprint_duration_weeks: parseInt(sprintWeeks) || 2,
                velocity:              parseInt(velocity) || 0,
                backlog_items:         splitLines(backlogRaw),
              }))}
              loading={sprintApi.loading}
            >
              🏃 Create Sprint Plan
            </Btn>
          </Card>
          <ResultBox
            data={sprintApi.data ? { sprint_plan: (sprintApi.data as any).sprint_plan } : null}
            loading={sprintApi.loading}
            error={sprintApi.error}
            title="Sprint Plan"
          />
        </TwoCol>
      )}

      {/* ── Retrospective ── */}
      {tab === 'retro' && (
        <TwoCol>
          <Card>
            <SectionHead title="Sprint Retrospective" sub="Team inputs → root cause analysis + SMART action items" />
            <Input label="Sprint Number" value={retroSprint} onChange={setRetroSprint} />
            <Input label="What Went Well (one per line)" value={wentWell} onChange={setWentWell} rows={4} />
            <Input label="What Needs Improvement (one per line)" value={improvements} onChange={setImprovements} rows={4} />
            <Input label="Proposed Action Items (one per line)" value={actionItems} onChange={setActionItems} rows={4} />
            <Btn
              onClick={() => retroApi.call(() => pmAction('retrospective', {
                sprint_number: parseInt(retroSprint) || 1,
                went_well:     splitLines(wentWell),
                improvements:  splitLines(improvements),
                action_items:  splitLines(actionItems),
              }))}
              loading={retroApi.loading}
            >
              🔄 Facilitate Retrospective
            </Btn>
          </Card>
          <ResultBox
            data={retroApi.data ? { analysis: (retroApi.data as any).analysis } : null}
            loading={retroApi.loading}
            error={retroApi.error}
            title="Retrospective Analysis"
          />
        </TwoCol>
      )}

      {/* ── Roadmap ── */}
      {tab === 'roadmap' && (
        <TwoCol>
          <Card>
            <SectionHead title="Product Roadmap" sub="Vision + themes → quarterly roadmap with OKRs" />
            <Input label="Product Name"                  value={productName} onChange={setProductName} />
            <Input label="Product Vision"                value={vision}      onChange={setVision} rows={2} />
            <Input label="Strategic Themes (one per line)" value={themes}   onChange={setThemes} rows={4} />
            <Input label="Quarters to plan"              value={quarters}    onChange={setQuarters} />
            <Btn
              onClick={() => roadmapApi.call(() => pmAction('roadmap', {
                product_name: productName,
                vision,
                themes:   splitLines(themes),
                quarters: parseInt(quarters) || 4,
              }))}
              loading={roadmapApi.loading}
            >
              🗺️ Generate Roadmap
            </Btn>
          </Card>
          <ResultBox
            data={roadmapApi.data ? { roadmap: (roadmapApi.data as any).roadmap } : null}
            loading={roadmapApi.loading}
            error={roadmapApi.error}
            title="Product Roadmap"
          />
        </TwoCol>
      )}

      {/* ── Estimation ── */}
      {tab === 'estimate' && (
        <TwoCol>
          <Card>
            <SectionHead title="Story Point Estimation" sub="User stories → Fibonacci estimates with confidence rating" />
            <Input
              label="User Stories (one per line)"
              value={storiesRaw}
              onChange={setStoriesRaw}
              rows={7}
            />
            <Select
              label="Estimation Technique"
              value={technique}
              onChange={setTechnique}
              options={[
                { value: 'planning_poker', label: 'Planning Poker' },
                { value: 'pert',           label: 'PERT (3-point)' },
                { value: 't_shirt_sizing', label: 'T-Shirt Sizing' },
              ]}
            />
            <div style={{ padding: 10, background: 'rgba(16,185,129,0.08)', borderRadius: 8, marginBottom: 14 }}>
              <div style={{ fontSize: 11, color: '#5eead4', fontWeight: 600, marginBottom: 4 }}>Fibonacci Scale</div>
              {[1, 2, 3, 5, 8, 13, 21].map(n => (
                <span key={n} style={{
                  display: 'inline-block', marginRight: 6, padding: '2px 8px',
                  borderRadius: 4, background: '#1e2535', color: '#9ca3af', fontSize: 11,
                }}>{n}</span>
              ))}
            </div>
            <Btn
              onClick={() => estimateApi.call(() => pmAction('estimation', {
                stories:   splitLines(storiesRaw),
                technique,
              }))}
              loading={estimateApi.loading}
            >
              📊 Estimate Stories
            </Btn>
          </Card>
          <ResultBox
            data={estimateApi.data ? { estimates: (estimateApi.data as any).estimates } : null}
            loading={estimateApi.loading}
            error={estimateApi.error}
            title="Story Estimates"
          />
        </TwoCol>
      )}
    </PageShell>
  )
}
