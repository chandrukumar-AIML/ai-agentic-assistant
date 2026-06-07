// frontend/src/pages/HRPage.tsx — Feature 18: HR Assistant
import { useState } from 'react'
import { PageShell, Card, Btn, Input, Select, ResultBox, Tabs, TwoCol, useApi, SectionHead } from '../components/ui'
import { screenResume, generateJD, generateOnboardingChecklist, hrEnhance } from '../lib/api'

const SAMPLE_RESUME = `John Smith | john@email.com | LinkedIn: linkedin.com/in/johnsmith
Senior Software Engineer | 8 years experience

SKILLS: Python, FastAPI, React, TypeScript, PostgreSQL, Docker, Kubernetes, AWS, Machine Learning

EXPERIENCE:
- Senior Engineer at TechCorp (2021–2024): Led team of 6, built microservices handling 1M req/day
- Software Engineer at StartupXYZ (2019–2021): Full-stack development, React + Node.js
- Junior Developer at Agency (2016–2019): Built client websites and REST APIs

EDUCATION: B.Tech Computer Science, IIT Madras (2016) — CGPA 8.7/10

PROJECTS:
- AI-powered recommendation system (20% CTR increase)
- Real-time fraud detection pipeline (reduced fraud by 35%)

CERTIFICATIONS: AWS Solutions Architect, Google Cloud Professional`

const RATINGS = ['Exceeds Expectations','Meets Expectations','Partially Meets Expectations','Does Not Meet Expectations']
const DEPTS   = ['Engineering','Product','Design','Marketing','Sales','HR','Finance','Operations']

export default function HRPage() {
  const [tab, setTab]         = useState('screen')
  const [resume, setResume]   = useState(SAMPLE_RESUME)
  const [jobTitle, setJobTitle] = useState('Senior Software Engineer')
  const [jobDesc, setJobDesc]   = useState('We are looking for a Senior Software Engineer with 5+ years of experience in Python and FastAPI to lead our backend team.')
  const [reqs, setReqs]       = useState('Python, FastAPI, React, Leadership')
  const [dept, setDept]       = useState('Engineering')
  const [company, setCompany] = useState('Tech Innovations India')
  const [jdTitle, setJdTitle] = useState('Senior Software Engineer')
  const [role, setRole]       = useState('Software Engineer')

  const screenApi  = useApi()
  const jdApi      = useApi()
  const onboardApi = useApi()

  // Performance Review tab
  const [perfEmployee, setPerfEmp]  = useState('Arjun Sharma')
  const [perfRole, setPerfRole]     = useState('Senior Software Engineer')
  const [perfPeriod, setPerfPeriod] = useState('Q4 2025 (Oct–Dec)')
  const [perfRating, setPerfRating] = useState('Meets Expectations')
  const [perfAch, setPerfAch]       = useState('Delivered auth microservice 2 weeks ahead of schedule\nMentored 2 junior engineers\nReduced API p99 latency by 40% through query optimization')
  const [perfAreas, setPerfAreas]   = useState('Communication with stakeholders\nDocumentation coverage\nProactive escalation of blockers')
  const perfApi = useApi()

  // Employee Handbook tab
  const [hbCompany, setHbCo]     = useState('Tech Innovations India Pvt Ltd')
  const [hbIndustry, setHbInd]   = useState('B2B SaaS Technology')
  const [hbTopics, setHbTopics]  = useState('Leave policy (casual, sick, maternity/paternity), Remote work policy, Code of conduct, Performance management, Grievance redressal, IT & data security, Benefits & perks, Travel & expense policy')
  const hbApi = useApi()

  return (
    <PageShell icon="👥" title="AI HR Assistant" subtitle="Feature 18 — Resume screening, JD generation, Onboarding, Performance reviews, Handbook">
      <Tabs
        tabs={[
          { id: 'screen',   label: 'Resume Screen',   icon: '📄' },
          { id: 'jd',       label: 'JD Generator',    icon: '📝' },
          { id: 'onboard',  label: 'Onboarding',      icon: '🎯' },
          { id: 'perf',     label: 'Perf Review',     icon: '⭐' },
          { id: 'handbook', label: 'Handbook',         icon: '📖' },
        ]}
        active={tab} onChange={setTab}
      />

      {tab === 'screen' && (
        <TwoCol>
          <Card>
            <SectionHead title="Resume Screening" sub="GPT-4o → Ollama fallback — score 0-100 with strengths & gaps" />
            <Input label="Job Title"                              value={jobTitle} onChange={setJobTitle} />
            <Input label="Job Description"                        value={jobDesc}  onChange={setJobDesc} rows={3} />
            <Input label="Required Skills (comma-separated)"      value={reqs}     onChange={setReqs} />
            <Input label="Resume Text"                            value={resume}   onChange={setResume} rows={10} />
            <Btn onClick={() => screenApi.call(() => screenResume(resume, jobDesc, reqs.split(',').map(s => s.trim())))} loading={screenApi.loading}>
              📄 Screen Resume
            </Btn>
          </Card>

          <div>
            {screenApi.data && (
              <Card style={{ marginBottom: 12 }}>
                <div style={{ textAlign: 'center', marginBottom: 16 }}>
                  <div style={{ fontSize: 52, fontWeight: 700, color: (screenApi.data.overall_score ?? screenApi.data.score ?? 0) >= 70 ? '#22c55e' : (screenApi.data.overall_score ?? screenApi.data.score ?? 0) >= 50 ? '#f59e0b' : '#ef4444' }}>
                    {screenApi.data.overall_score ?? screenApi.data.score ?? '—'}
                  </div>
                  <div style={{ color: '#6b7280', fontSize: 12 }}>Resume Score / 100</div>
                  <div style={{ marginTop: 8, padding: '6px 14px', display: 'inline-block', borderRadius: 20,
                    background: ['strong_yes','yes','HIRE'].includes(screenApi.data.recommendation) ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)',
                    color: ['strong_yes','yes','HIRE'].includes(screenApi.data.recommendation) ? '#86efac' : '#fca5a5',
                    fontSize: 13, fontWeight: 600 }}>
                    {screenApi.data.recommendation?.replace('_', ' ').toUpperCase() || 'REVIEW'}
                  </div>
                </div>
                {(screenApi.data.highlights || screenApi.data.strengths) && (
                  <div style={{ marginBottom: 10 }}>
                    <div style={{ color: '#86efac', fontSize: 12, fontWeight: 600, marginBottom: 6 }}>✅ Highlights</div>
                    {(screenApi.data.highlights || screenApi.data.strengths || []).map((s: string, i: number) => (
                      <div key={i} style={{ color: '#9ca3af', fontSize: 12, marginBottom: 3 }}>• {s}</div>
                    ))}
                  </div>
                )}
                {(screenApi.data.concerns || screenApi.data.gaps) && (
                  <div>
                    <div style={{ color: '#fca5a5', fontSize: 12, fontWeight: 600, marginBottom: 6 }}>⚠ Concerns</div>
                    {(screenApi.data.concerns || screenApi.data.gaps || []).map((g: string, i: number) => (
                      <div key={i} style={{ color: '#9ca3af', fontSize: 12, marginBottom: 3 }}>• {g}</div>
                    ))}
                  </div>
                )}
              </Card>
            )}
            <ResultBox data={screenApi.data} loading={screenApi.loading} error={screenApi.error} title="Full Screening Data" />
          </div>
        </TwoCol>
      )}

      {tab === 'jd' && (
        <TwoCol>
          <Card>
            <SectionHead title="Job Description Generator" sub="AI-generated JD with requirements, responsibilities, benefits" />
            <Input label="Job Title"                          value={jdTitle}  onChange={setJdTitle} />
            <Input label="Company Name"                       value={company}  onChange={setCompany} />
            <Select label="Department" value={dept} onChange={setDept}
              options={DEPTS.map(d => ({ label: d, value: d }))} />
            <Input label="Required Skills (comma-separated)"  value={reqs}     onChange={setReqs} />
            <Btn onClick={() => jdApi.call(() => generateJD(jdTitle, dept, company, reqs.split(',').map(s => s.trim())))} loading={jdApi.loading}>
              📝 Generate JD
            </Btn>
          </Card>
          <ResultBox data={jdApi.data} loading={jdApi.loading} error={jdApi.error} title="Generated Job Description" />
        </TwoCol>
      )}

      {tab === 'onboard' && (
        <TwoCol>
          <Card>
            <SectionHead title="Onboarding Checklist" sub="Role-specific onboarding plan for new hires" />
            <Input label="Role" value={role} onChange={setRole} />
            <Select label="Department" value={dept} onChange={setDept}
              options={DEPTS.map(d => ({ label: d, value: d }))} />
            <Btn onClick={() => onboardApi.call(() => generateOnboardingChecklist(role, dept))} loading={onboardApi.loading}>
              🎯 Generate Checklist
            </Btn>
          </Card>
          <ResultBox data={onboardApi.data} loading={onboardApi.loading} error={onboardApi.error} title="Onboarding Plan" />
        </TwoCol>
      )}

      {/* ── Performance Review ── */}
      {tab === 'perf' && (
        <TwoCol>
          <Card>
            <SectionHead title="Performance Review Generator" sub="Structured review with SMART goals, competency ratings, and narrative" />
            <Input label="Employee Name"    value={perfEmployee} onChange={setPerfEmp} />
            <Input label="Role"             value={perfRole}     onChange={setPerfRole} />
            <Input label="Review Period"    value={perfPeriod}   onChange={setPerfPeriod} />
            <Select label="Overall Rating"  value={perfRating}   onChange={setPerfRating}
              options={RATINGS.map(r => ({ label: r, value: r }))} />
            <Input label="Key Achievements (one per line)" value={perfAch}   onChange={setPerfAch}   rows={4} />
            <Input label="Development Areas (one per line)" value={perfAreas} onChange={setPerfAreas} rows={3} />
            <Btn
              onClick={() => perfApi.call(() => hrEnhance('performance_review', {
                employee_name:    perfEmployee,
                role:             perfRole,
                review_period:    perfPeriod,
                overall_rating:   perfRating,
                achievements:     perfAch,
                improvement_areas: perfAreas,
              }))}
              loading={perfApi.loading}
            >
              ⭐ Generate Review
            </Btn>
          </Card>
          <div>
            <Card style={{ marginBottom: 12 }}>
              <SectionHead title="Review Includes" sub="" />
              {[
                'Performance summary narrative',
                'Goal achievement assessment',
                'Competency ratings (1-5) for 6 competencies',
                '3 SMART development goals',
                'Manager commentary template',
                'Rating justification statement',
              ].map(item => (
                <div key={item} style={{ display: 'flex', gap: 8, padding: '5px 0', borderBottom: '1px solid #1e2535' }}>
                  <span style={{ color: '#22c55e', fontSize: 12 }}>✓</span>
                  <span style={{ color: '#9ca3af', fontSize: 12 }}>{item}</span>
                </div>
              ))}
            </Card>
            <ResultBox data={perfApi.data ? { review: (perfApi.data as any).result } : null} loading={perfApi.loading} error={perfApi.error} title="Performance Review" />
          </div>
        </TwoCol>
      )}

      {/* ── Employee Handbook ── */}
      {tab === 'handbook' && (
        <TwoCol>
          <Card>
            <SectionHead title="Employee Handbook Generator" sub="Comprehensive, legally-aware handbook in professional format" />
            <Input label="Company Name"  value={hbCompany}  onChange={setHbCo} />
            <Input label="Industry"      value={hbIndustry} onChange={setHbInd} />
            <Input label="Topics to Cover (comma-separated)" value={hbTopics} onChange={setHbTopics} rows={4} />
            <div style={{ padding: 10, background: 'rgba(99,102,241,0.08)', borderRadius: 8, marginBottom: 14 }}>
              <div style={{ fontSize: 11, color: '#a5b4fc', marginBottom: 4 }}>📖 Handbook structure</div>
              <div style={{ fontSize: 11, color: '#6b7280' }}>Welcome • Company values • Employment policies • Benefits • Performance management • Grievance • IT security • Acknowledgement</div>
            </div>
            <Btn
              onClick={() => hbApi.call(() => hrEnhance('employee_handbook', {
                company:  hbCompany,
                industry: hbIndustry,
                topics:   hbTopics,
              }))}
              loading={hbApi.loading}
            >
              📖 Generate Handbook
            </Btn>
          </Card>
          <ResultBox data={hbApi.data ? { handbook: (hbApi.data as any).result } : null} loading={hbApi.loading} error={hbApi.error} title="Employee Handbook" />
        </TwoCol>
      )}
    </PageShell>
  )
}
