// frontend/src/pages/SchedulerPage.tsx — Feature 4
import { useEffect, useState } from 'react'
import { PageShell, Card, Btn, Input, Select, ResultBox, TwoCol, useApi, SectionHead, Badge, StatCard } from '../components/ui'
import { listTasks, createTask, pauseTask, resumeTask, deleteTask } from '../lib/api'

export default function SchedulerPage() {
  const [tasks, setTasks] = useState<any[]>([])
  const [newTask, setNewTask] = useState({ name: 'Daily Report', task_type: 'report', schedule_expr: '0 9 * * *', payload: {} })
  const listApi   = useApi()
  const createApi = useApi()

  const reload = () => listApi.call(() => listTasks())
  useEffect(() => { reload() }, [])
  useEffect(() => {
    if (listApi.data?.tasks) setTasks(listApi.data.tasks)
    else if (Array.isArray(listApi.data)) setTasks(listApi.data)
  }, [listApi.data])

  const handleCreate = async () => {
    await createApi.call(() => createTask(newTask))
    reload()
  }

  return (
    <PageShell icon="⏰" title="Agentic Task Scheduler" subtitle="Automate recurring tasks on your own schedule">
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 14, marginBottom: 20 }}>
        <StatCard label="Total Tasks"   value={tasks.length} icon="📋" />
        <StatCard label="Active"        value={tasks.filter(t => t.status === 'active' || t.enabled).length} icon="✅" />
        <StatCard label="Paused"        value={tasks.filter(t => t.status === 'paused').length} icon="⏸️" />
      </div>

      <TwoCol>
        <Card>
          <SectionHead title="Create New Task" sub="Schedule any AI agent task with cron syntax" />
          <Input label="Task Name" value={newTask.name} onChange={v => setNewTask(p => ({ ...p, name: v }))} />
          <Select label="Task Type" value={newTask.task_type} onChange={v => setNewTask(p => ({ ...p, task_type: v }))}
            options={[
              { label: 'Report Generation', value: 'report' },
              { label: 'Data Sync', value: 'sync' },
              { label: 'Email Digest', value: 'email_digest' },
              { label: 'Social Post', value: 'social_post' },
              { label: 'Lead Scrape', value: 'lead_scrape' },
              { label: 'Custom', value: 'custom' },
            ]} />
          <Input label="Cron Schedule (e.g. '0 9 * * *' = 9am daily)" value={newTask.schedule_expr} onChange={v => setNewTask(p => ({ ...p, schedule_expr: v }))} />
          <div style={{ marginBottom: 14 }}>
            <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 6 }}>Common schedules:</div>
            {[
              ['Every minute',    '* * * * *'],
              ['Every hour',      '0 * * * *'],
              ['Daily 9am',       '0 9 * * *'],
              ['Weekly Monday',   '0 9 * * 1'],
              ['Monthly 1st',     '0 9 1 * *'],
            ].map(([label, expr]) => (
              <button key={expr} onClick={() => setNewTask(p => ({ ...p, schedule_expr: expr }))} style={{
                marginRight: 6, marginBottom: 4, padding: '3px 8px', borderRadius: 5,
                background: newTask.schedule_expr === expr ? 'rgba(16,185,129,0.2)' : '#0f1117',
                border: `1px solid ${newTask.schedule_expr === expr ? '#10b981' : '#1e2535'}`,
                color: newTask.schedule_expr === expr ? '#5eead4' : '#6b7280', fontSize: 10, cursor: 'pointer',
              }}>
                {label} <span style={{ opacity: 0.5 }}>({expr})</span>
              </button>
            ))}
          </div>
          <Btn onClick={handleCreate} loading={createApi.loading}>⏰ Schedule Task</Btn>
        </Card>

        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
            <SectionHead title={`Tasks (${tasks.length})`} />
            <Btn variant="secondary" onClick={reload} loading={listApi.loading}>🔄</Btn>
          </div>
          {tasks.length === 0 && !listApi.loading && (
            <Card>
              <div style={{ textAlign: 'center', padding: 30, color: '#6b7280' }}>
                <span style={{ fontSize: 36 }}>⏰</span>
                <p>No scheduled tasks yet.</p>
              </div>
            </Card>
          )}
          {tasks.map((t: any) => (
            <Card key={t.id} style={{ marginBottom: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <div style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 600 }}>{t.name}</div>
                <Badge text={t.status?.toUpperCase() || 'ACTIVE'} color={t.status === 'paused' ? 'yellow' : 'green'} />
              </div>
              <div style={{ color: '#6b7280', fontSize: 11, marginBottom: 8 }}>
                {t.task_type} • {t.schedule_expr} • Next: {t.next_run ? new Date(t.next_run).toLocaleString() : 'N/A'}
              </div>
              <div style={{ display: 'flex', gap: 6 }}>
                {t.status !== 'paused' ? (
                  <Btn variant="secondary" onClick={() => pauseTask(t.id).then(reload)} style={{ fontSize: 11, padding: '4px 10px' }}>⏸ Pause</Btn>
                ) : (
                  <Btn variant="success" onClick={() => resumeTask(t.id).then(reload)} style={{ fontSize: 11, padding: '4px 10px' }}>▶ Resume</Btn>
                )}
                <Btn variant="danger" onClick={() => deleteTask(t.id).then(reload)} style={{ fontSize: 11, padding: '4px 10px' }}>🗑</Btn>
              </div>
            </Card>
          ))}
          <ResultBox data={createApi.data} loading={createApi.loading} error={createApi.error} title="Created Task" />
        </div>
      </TwoCol>
    </PageShell>
  )
}
