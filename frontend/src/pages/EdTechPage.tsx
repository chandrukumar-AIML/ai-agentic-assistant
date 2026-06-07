// frontend/src/pages/EdTechPage.tsx — EdTech / Training vertical
import { useState } from 'react'
import { PageShell, Card, Btn, Input, Select, ResultBox, Tabs, TwoCol, useApi, SectionHead } from '../components/ui'
import { edtechAction } from '../lib/api'

const LEVELS = ['Class 6','Class 7','Class 8','Class 9','Class 10','Class 11','Class 12','Undergraduate','Beginner','Intermediate','Advanced','JEE/NEET aspirant']

export default function EdTechPage() {
  const [tab, setTab] = useState('course')

  // Course Outline
  const [cSubject, setCSubject] = useState('Full-Stack Web Development with React & FastAPI')
  const [cLevel, setCLevel]     = useState('Beginner')
  const [cDur, setCDur]         = useState('8 weeks')
  const [cGoal, setCGoal]       = useState('Build and deploy a production-ready full-stack app')
  const courseApi = useApi()

  // Quiz
  const [qTopic, setQTopic]     = useState('Photosynthesis')
  const [qLevel, setQLevel]     = useState('Class 10')
  const [qNum, setQNum]         = useState('10')
  const [qTypes, setQTypes]     = useState('MCQ + 2 short answer')
  const [qDiff, setQDiff]       = useState('easy/medium/hard mix')
  const quizApi = useApi()

  // Lesson Plan
  const [lTopic, setLTopic]     = useState('Introduction to Fractions')
  const [lLevel, setLLevel]     = useState('Class 6')
  const [lDur, setLDur]         = useState('45 minutes')
  const [lCtx, setLCtx]         = useState('30 students, mixed ability, has projector')
  const lessonApi = useApi()

  // Progress Report
  const [pStudent, setPStudent] = useState('Aarav Sharma')
  const [pLevel, setPLevel]     = useState('Class 8')
  const [pSubject, setPSubject] = useState('Mathematics, Science')
  const [pMarks, setPMarks]     = useState('Math 78/100, Science 65/100, last term Math 70, Science 72')
  const [pObs, setPObs]         = useState('Strong in algebra, struggles with physics numericals. Active in class, sometimes rushes work.')
  const progressApi = useApi()

  // Doubt Solver
  const [dLevel, setDLevel]     = useState('Class 10')
  const [dDoubt, setDDoubt]     = useState('Why is the derivative of sin(x) equal to cos(x)? Explain intuitively.')
  const doubtApi = useApi()

  return (
    <PageShell icon="📚" title="AI EdTech Assistant" subtitle="Course outlines, quizzes, lesson plans, progress reports, doubt solving">
      <Tabs
        tabs={[
          { id: 'course',   label: 'Course Outline',   icon: '🗂️' },
          { id: 'quiz',     label: 'Quiz Generator',   icon: '❓' },
          { id: 'lesson',   label: 'Lesson Plan',      icon: '📋' },
          { id: 'progress', label: 'Progress Report',  icon: '📊' },
          { id: 'doubt',    label: 'Doubt Solver',     icon: '💡' },
        ]}
        active={tab} onChange={setTab}
      />

      {tab === 'course' && (
        <TwoCol>
          <Card>
            <SectionHead title="Course / Curriculum Outline" sub="Modules, outcomes, week-by-week schedule, assessment plan" />
            <Input label="Course / Subject" value={cSubject} onChange={setCSubject} rows={2} />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Select label="Level" value={cLevel} onChange={setCLevel} options={LEVELS.map(l => ({ label: l, value: l }))} />
              <Input label="Duration" value={cDur} onChange={setCDur} />
            </div>
            <Input label="Goal / Outcome" value={cGoal} onChange={setCGoal} rows={2} />
            <Btn onClick={() => courseApi.call(() => edtechAction('course_outline', { subject: cSubject, level: cLevel, duration: cDur, goal: cGoal }))} loading={courseApi.loading}>
              🗂️ Generate Outline
            </Btn>
          </Card>
          <ResultBox data={courseApi.data ? { outline: (courseApi.data as any).result } : null} loading={courseApi.loading} error={courseApi.error} title="Course Outline" />
        </TwoCol>
      )}

      {tab === 'quiz' && (
        <TwoCol>
          <Card>
            <SectionHead title="Quiz Generator" sub="MCQs + answer key + marking scheme + HOTS questions" />
            <Input label="Topic" value={qTopic} onChange={setQTopic} />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Select label="Level" value={qLevel} onChange={setQLevel} options={LEVELS.map(l => ({ label: l, value: l }))} />
              <Input label="No. of Questions" value={qNum} onChange={setQNum} type="number" />
            </div>
            <Input label="Question Types" value={qTypes} onChange={setQTypes} />
            <Input label="Difficulty Mix" value={qDiff} onChange={setQDiff} />
            <Btn onClick={() => quizApi.call(() => edtechAction('quiz_generator', { topic: qTopic, level: qLevel, num_questions: qNum, q_types: qTypes, difficulty: qDiff }))} loading={quizApi.loading}>
              ❓ Generate Quiz
            </Btn>
          </Card>
          <ResultBox data={quizApi.data ? { quiz: (quizApi.data as any).result } : null} loading={quizApi.loading} error={quizApi.error} title="Quiz + Answer Key" />
        </TwoCol>
      )}

      {tab === 'lesson' && (
        <TwoCol>
          <Card>
            <SectionHead title="Lesson Plan" sub="Objectives, lesson flow with timings, differentiation, assessment" />
            <Input label="Topic" value={lTopic} onChange={setLTopic} />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Select label="Grade/Level" value={lLevel} onChange={setLLevel} options={LEVELS.map(l => ({ label: l, value: l }))} />
              <Input label="Duration" value={lDur} onChange={setLDur} />
            </div>
            <Input label="Class Context" value={lCtx} onChange={setLCtx} rows={2} />
            <Btn onClick={() => lessonApi.call(() => edtechAction('lesson_plan', { topic: lTopic, level: lLevel, duration: lDur, context: lCtx }))} loading={lessonApi.loading}>
              📋 Build Lesson Plan
            </Btn>
          </Card>
          <ResultBox data={lessonApi.data ? { plan: (lessonApi.data as any).result } : null} loading={lessonApi.loading} error={lessonApi.error} title="Lesson Plan" />
        </TwoCol>
      )}

      {tab === 'progress' && (
        <TwoCol>
          <Card>
            <SectionHead title="Student Progress Report" sub="Parent-facing report — strengths, improvements, next steps" />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Input label="Student" value={pStudent} onChange={setPStudent} />
              <Select label="Class" value={pLevel} onChange={setPLevel} options={LEVELS.map(l => ({ label: l, value: l }))} />
            </div>
            <Input label="Subject(s)" value={pSubject} onChange={setPSubject} />
            <Input label="Marks / Scores" value={pMarks} onChange={setPMarks} rows={2} />
            <Input label="Teacher Observations" value={pObs} onChange={setPObs} rows={3} />
            <Btn onClick={() => progressApi.call(() => edtechAction('progress_report', { student: pStudent, level: pLevel, subject: pSubject, marks: pMarks, observations: pObs }))} loading={progressApi.loading}>
              📊 Generate Report
            </Btn>
          </Card>
          <ResultBox data={progressApi.data ? { report: (progressApi.data as any).result } : null} loading={progressApi.loading} error={progressApi.error} title="Progress Report" />
        </TwoCol>
      )}

      {tab === 'doubt' && (
        <TwoCol>
          <Card>
            <SectionHead title="Doubt Solver" sub="Step-by-step pedagogical explanation + practice question" />
            <Select label="Subject / Level" value={dLevel} onChange={setDLevel} options={LEVELS.map(l => ({ label: l, value: l }))} />
            <Input label="Question / Doubt" value={dDoubt} onChange={setDDoubt} rows={4} />
            <Btn onClick={() => doubtApi.call(() => edtechAction('doubt_solver', { level: dLevel, doubt: dDoubt }))} loading={doubtApi.loading}>
              💡 Explain
            </Btn>
          </Card>
          <ResultBox data={doubtApi.data ? { explanation: (doubtApi.data as any).result } : null} loading={doubtApi.loading} error={doubtApi.error} title="Explanation" />
        </TwoCol>
      )}
    </PageShell>
  )
}
