// frontend/src/pages/ABTestPage.tsx — Feature 12: A/B Testing
import { useState, useEffect } from 'react'
import { PageShell, Card, Btn, Input, Select, ResultBox, Tabs, TwoCol, useApi, SectionHead, Badge, StatCard } from '../components/ui'
import { listExperiments, createExperiment, runABTurn, getABSignificance, promoteWinner } from '../lib/api'

export default function ABTestPage() {
  const [tab, setTab]   = useState('list')
  const [experiments, setExperiments] = useState<any[]>([])
  const [selExp, setSelExp] = useState<string>('')
  const [query, setQuery] = useState('Explain quantum computing in simple terms')
  const [newExp, setNewExp] = useState({ name: 'GPT-4o vs Llama3', description: 'Quality vs speed tradeoff', model_a: 'gpt-4o-mini', model_b: 'ollama/llama3', min_turns: 10, traffic_split: 0.5 })

  const listApi = useApi()
  const runApi  = useApi()
  const sigApi  = useApi()
  const createApi = useApi()

  useEffect(() => {
    listApi.call(() => listExperiments()).then(() => {})
  }, [])

  useEffect(() => {
    if (listApi.data?.experiments) {
      setExperiments(listApi.data.experiments)
      if (listApi.data.experiments.length > 0 && !selExp) setSelExp(listApi.data.experiments[0].id)
    }
  }, [listApi.data])

  const handleCreate = async () => {
    await createApi.call(() => createExperiment(newExp))
    await listApi.call(() => listExperiments())
  }

  return (
    <PageShell icon="⚗️" title="Agent A/B Testing Framework" subtitle="Compare prompt versions and promote the winner with confidence">
      <Tabs
        tabs={[
          { id: 'list',   label: 'Experiments', icon: '📋' },
          { id: 'run',    label: 'Run Test',     icon: '▶️' },
          { id: 'stats',  label: 'Statistics',  icon: '📊' },
          { id: 'create', label: 'New Experiment', icon: '➕' },
        ]}
        active={tab} onChange={setTab}
      />

      {tab === 'list' && (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14, marginBottom: 20 }}>
            <StatCard label="Total Experiments" value={experiments.length} icon="⚗️" />
            <StatCard label="Running" value={experiments.filter(e => e.status === 'running').length} icon="▶️" />
            <StatCard label="Completed" value={experiments.filter(e => e.status === 'completed').length} icon="✅" />
          </div>
          {experiments.length === 0 ? (
            <Card>
              <div style={{ textAlign: 'center', padding: 40, color: '#6b7280' }}>
                <div style={{ fontSize: 36, marginBottom: 8 }}>⚗️</div>
                <div>No experiments yet. Create one to start!</div>
                <Btn onClick={() => setTab('create')} style={{ marginTop: 12 }}>➕ Create Experiment</Btn>
              </div>
            </Card>
          ) : (
            experiments.map((exp: any) => (
              <Card key={exp.id} style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <div style={{ color: '#e2e8f0', fontSize: 14, fontWeight: 600 }}>{exp.name}</div>
                    <div style={{ color: '#6b7280', fontSize: 12, marginTop: 2 }}>
                      Model A: <span style={{ color: '#5eead4' }}>{exp.model_a}</span> vs Model B: <span style={{ color: '#86efac' }}>{exp.model_b}</span>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <Badge text={exp.status?.toUpperCase() || 'RUNNING'} color={exp.status === 'completed' ? 'green' : exp.status === 'paused' ? 'yellow' : 'blue'} />
                    <Btn variant="secondary" onClick={() => { setSelExp(exp.id); setTab('run') }}>Run</Btn>
                  </div>
                </div>
                {exp.winner_model && (
                  <div style={{ marginTop: 8, padding: '6px 10px', background: 'rgba(34,197,94,0.1)', borderRadius: 6, fontSize: 12, color: '#86efac' }}>
                    🏆 Winner: {exp.winner_model} (p={exp.significance_p?.toFixed(4)}, d={exp.effect_size?.toFixed(3)})
                  </div>
                )}
              </Card>
            ))
          )}
          <ResultBox data={listApi.data} loading={listApi.loading} error={listApi.error} title="Raw Experiments Data" />
        </div>
      )}

      {tab === 'run' && (
        <TwoCol>
          <Card>
            <SectionHead title="Run A/B Turn" sub="Both models run in parallel — shadow traffic pattern" />
            <Select label="Experiment" value={selExp} onChange={setSelExp}
              options={[{ label: '-- select --', value: '' }, ...experiments.map(e => ({ label: e.name, value: e.id }))]} />
            <Input label="Query" value={query} onChange={setQuery} rows={3} />
            <div style={{ marginBottom: 12 }}>
              {['Explain quantum computing','Write a Python function to sort a list','What is blockchain?','Summarize the French Revolution'].map(q => (
                <button key={q} onClick={() => setQuery(q)} style={{
                  display: 'block', width: '100%', textAlign: 'left', padding: '6px 10px', marginBottom: 4,
                  background: '#0f1117', border: '1px solid #1e2535', borderRadius: 6, color: '#6b7280', fontSize: 12, cursor: 'pointer',
                }}>{q}</button>
              ))}
            </div>
            <Btn onClick={() => selExp && runApi.call(() => runABTurn(selExp, query))} loading={runApi.loading} disabled={!selExp}>
              ▶️ Run Comparison
            </Btn>
          </Card>
          <div>
            {runApi.data && (
              <div>
                {['A','B'].map(variant => (
                  <Card key={variant} style={{ marginBottom: 12, borderLeft: `3px solid ${variant === 'A' ? '#10b981' : '#22c55e'}` }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                      <Badge text={`Variant ${variant}`} color={variant === 'A' ? 'blue' : 'green'} />
                      <div style={{ color: '#6b7280', fontSize: 11 }}>
                        {runApi.data[`variant_${variant.toLowerCase()}`]?.latency_ms}ms • ${runApi.data[`variant_${variant.toLowerCase()}`]?.cost_usd?.toFixed(4)}
                      </div>
                    </div>
                    <div style={{ color: '#9ca3af', fontSize: 12, lineHeight: 1.5 }}>
                      {runApi.data[`variant_${variant.toLowerCase()}`]?.response?.slice(0, 200)}...
                    </div>
                  </Card>
                ))}
              </div>
            )}
            <ResultBox data={runApi.data} loading={runApi.loading} error={runApi.error} title="Full Turn Data" />
          </div>
        </TwoCol>
      )}

      {tab === 'stats' && (
        <TwoCol>
          <Card>
            <SectionHead title="Statistical Significance" sub="Welch's t-test + Cohen's d effect size" />
            <Select label="Experiment" value={selExp} onChange={setSelExp}
              options={[{ label: '-- select --', value: '' }, ...experiments.map(e => ({ label: e.name, value: e.id }))]} />
            <Btn onClick={() => selExp && sigApi.call(() => getABSignificance(selExp))} loading={sigApi.loading} disabled={!selExp}>
              📊 Compute Significance
            </Btn>
            {selExp && (
              <Btn variant="success" onClick={() => selExp && promoteWinner(selExp)} style={{ marginTop: 8 }}>
                🏆 Promote Winner
              </Btn>
            )}
          </Card>
          {sigApi.data && (
            <Card>
              <SectionHead title="Statistical Results" />
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
                {[
                  { label: 'p-value', value: sigApi.data.p_value?.toFixed(6), color: sigApi.data.p_value < 0.05 ? '#22c55e' : '#f59e0b' },
                  { label: "Cohen's d", value: sigApi.data.effect_size?.toFixed(3), color: '#5eead4' },
                  { label: 'Significant?', value: sigApi.data.significant ? 'YES ✓' : 'NO', color: sigApi.data.significant ? '#22c55e' : '#f59e0b' },
                  { label: 'Mean A vs B', value: `${sigApi.data.mean_a?.toFixed(3)} vs ${sigApi.data.mean_b?.toFixed(3)}`, color: '#e2e8f0' },
                ].map(s => (
                  <div key={s.label} style={{ background: '#0f1117', borderRadius: 8, padding: 12 }}>
                    <div style={{ color: s.color, fontSize: 16, fontWeight: 700 }}>{s.value}</div>
                    <div style={{ color: '#6b7280', fontSize: 11 }}>{s.label}</div>
                  </div>
                ))}
              </div>
              <ResultBox data={sigApi.data} title="Full Stats" />
            </Card>
          )}
          {!sigApi.data && <ResultBox data={sigApi.data} loading={sigApi.loading} error={sigApi.error} title="Statistics" />}
        </TwoCol>
      )}

      {tab === 'create' && (
        <TwoCol>
          <Card>
            <SectionHead title="Create New Experiment" sub="Compare two models with statistical rigor" />
            <Input label="Experiment Name" value={newExp.name} onChange={v => setNewExp(p => ({ ...p, name: v }))} />
            <Input label="Description" value={newExp.description} onChange={v => setNewExp(p => ({ ...p, description: v }))} />
            <Select label="Model A" value={newExp.model_a} onChange={v => setNewExp(p => ({ ...p, model_a: v }))}
              options={[{ label: 'GPT-4o', value: 'gpt-4o' }, { label: 'GPT-4o-mini', value: 'gpt-4o-mini' }, { label: 'Ollama Llama3', value: 'ollama/llama3' }, { label: 'Ollama Mistral', value: 'ollama/mistral' }]} />
            <Select label="Model B" value={newExp.model_b} onChange={v => setNewExp(p => ({ ...p, model_b: v }))}
              options={[{ label: 'Ollama Llama3', value: 'ollama/llama3' }, { label: 'GPT-4o-mini', value: 'gpt-4o-mini' }, { label: 'GPT-4o', value: 'gpt-4o' }, { label: 'Ollama Mistral', value: 'ollama/mistral' }]} />
            <Input label="Min Turns (for auto-promote)" value={String(newExp.min_turns)} onChange={v => setNewExp(p => ({ ...p, min_turns: Number(v) }))} type="number" />
            <Btn onClick={handleCreate} loading={createApi.loading}>➕ Create Experiment</Btn>
          </Card>
          <ResultBox data={createApi.data} loading={createApi.loading} error={createApi.error} title="Created Experiment" />
        </TwoCol>
      )}
    </PageShell>
  )
}
