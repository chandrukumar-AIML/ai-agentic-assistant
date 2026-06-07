// frontend/src/pages/AnalystPage.tsx — Data Analyst Vertical (SQL + Charts + Pandas)
import { useState } from 'react'
import { PageShell, Card, Btn, Input, Select, ResultBox, Tabs, TwoCol, useApi, SectionHead, Badge } from '../components/ui'
import { analystQuery, analystEnhance } from '../lib/api'

const SAMPLE_QUERIES = [
  'Show total revenue by product category for the last 30 days',
  'Find the top 10 customers by order value this quarter',
  'Count daily active users grouped by signup cohort',
  'Identify products with declining sales over the past 3 months',
  'Show average response time by API endpoint',
]

const AUDIENCES = ['Executive leadership', 'Board of directors', 'Sales team', 'Product team', 'Engineering team', 'Investors']
const FORMATS   = ['Board presentation', 'Executive memo', 'Slack summary', 'Weekly report', 'Dashboard narrative', 'Investor update']

export default function AnalystPage() {
  const [tab, setTab]       = useState('query')
  const [query, setQuery]   = useState(SAMPLE_QUERIES[0])
  const analystApi          = useApi()

  // Data Storytelling tab
  const [storyContext, setStoryCtx]     = useState('Q3 2025 performance review for a B2B SaaS platform with 500 enterprise customers')
  const [storyInsights, setStoryIns]    = useState('ARR grew 35% YoY to ₹5.04Cr\nChurn dropped from 8% to 4.2%\nNet Promoter Score increased from 32 to 61\nTop 20% of customers generate 78% of revenue\nAverage expansion revenue per account: ₹12L')
  const [storyAudience, setStoryAud]    = useState('Executive leadership')
  const [storyFormat, setStoryFormat]   = useState('Board presentation')
  const storyApi = useApi()

  // Anomaly Detection tab
  const [anomalyMetric, setAnomalyMetric] = useState('API response time (p95, ms)')
  const [anomalyData, setAnomalyData]     = useState('Mon: 145ms, Tue: 152ms, Wed: 149ms, Thu: 1240ms, Fri: 890ms, Sat: 167ms, Sun: 141ms\nWeek-2 Mon: 148ms, Tue: 155ms, Wed: 2300ms (outage), Thu: 160ms, Fri: 158ms')
  const [anomalyRange, setAnomalyRange]   = useState('Normal: 120–200ms (based on 30-day baseline)')
  const [anomalyCtx, setAnomalyCtx]       = useState('FastAPI backend, PostgreSQL, Redis. Deploy happened Thursday 2pm IST. Team size: 8 engineers.')
  const anomalyApi = useApi()

  const runQuery = () => { analystApi.call(() => analystQuery(query)) }
  const data = analystApi.data as any

  return (
    <PageShell
      icon="📊"
      title="AI Data Analyst"
      subtitle="SQL queries, Pandas analysis, data storytelling, anomaly detection"
    >
      <Tabs
        tabs={[
          { id: 'query',   label: 'Query & Charts',   icon: '📈' },
          { id: 'story',   label: 'Data Storytelling', icon: '📖' },
          { id: 'anomaly', label: 'Anomaly Detection', icon: '🚨' },
          { id: 'about',   label: 'Capabilities',      icon: '🔎' },
        ]}
        active={tab} onChange={setTab}
      />

      {tab === 'query' && (
        <TwoCol>
          <Card>
            <SectionHead
              title="Natural Language Query"
              sub="Ask any question about your data — the agent writes SQL, runs it, and generates charts"
            />
            <div style={{ marginBottom: 12 }}>
              <label style={{ display: 'block', fontSize: 12, color: '#9ca3af', marginBottom: 6, fontWeight: 500 }}>Quick Examples</label>
              {SAMPLE_QUERIES.map(q => (
                <button key={q} onClick={() => setQuery(q)} style={{
                  display: 'block', width: '100%', textAlign: 'left', padding: '6px 10px', marginBottom: 4,
                  background: query === q ? 'rgba(99,102,241,0.1)' : 'none',
                  border: `1px solid ${query === q ? '#6366f1' : '#1e2535'}`,
                  borderRadius: 7, color: query === q ? '#a5b4fc' : '#6b7280', fontSize: 12, cursor: 'pointer',
                }}>{q}</button>
              ))}
            </div>
            <Input label="Your Question" value={query} onChange={setQuery} rows={3} />
            <Btn onClick={runQuery} loading={analystApi.loading}>📊 Run Analysis</Btn>
          </Card>

          <div>
            {data?.charts?.length > 0 && !analystApi.loading && (
              <Card style={{ marginBottom: 12 }}>
                <SectionHead title="Generated Charts" sub={`${data.charts.length} chart(s) from query results`} />
                {data.charts.map((chart: string, i: number) => (
                  <div key={i} style={{ marginBottom: 12, borderRadius: 8, overflow: 'hidden' }}>
                    <img src={`data:image/png;base64,${chart}`} alt={`Chart ${i + 1}`} style={{ width: '100%', borderRadius: 8 }} />
                  </div>
                ))}
              </Card>
            )}
            {data?.metadata && !analystApi.loading && (
              <Card style={{ marginBottom: 12 }}>
                <SectionHead title="Query Details" sub="SQL and execution stats" />
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 8, marginBottom: 12 }}>
                  {[
                    { label: 'Rows Fetched',   value: data.metadata.rows_fetched ?? 0 },
                    { label: 'Charts Made',    value: data.metadata.charts_generated ?? 0 },
                    { label: 'Tables Scanned', value: (data.metadata.tables_available ?? []).length },
                  ].map(({ label, value }) => (
                    <div key={label} style={{ background: '#0f1117', borderRadius: 8, padding: 10, textAlign: 'center' }}>
                      <div style={{ color: '#e2e8f0', fontSize: 20, fontWeight: 700 }}>{value}</div>
                      <div style={{ color: '#6b7280', fontSize: 10 }}>{label}</div>
                    </div>
                  ))}
                </div>
                {data.metadata.sql_query && (
                  <div>
                    <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 4 }}>SQL Query Generated</div>
                    <pre style={{ background: '#0f1117', borderRadius: 8, padding: '10px 12px', fontSize: 11, color: '#a5b4fc', overflowX: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-all', margin: 0 }}>
                      {data.metadata.sql_query}
                    </pre>
                  </div>
                )}
              </Card>
            )}
            <ResultBox data={data?.content ? { analysis: data.content, sources: data.sources } : null} loading={analystApi.loading} error={analystApi.error} title="AI Analysis Report" />
          </div>
        </TwoCol>
      )}

      {/* ── Data Storytelling ── */}
      {tab === 'story' && (
        <TwoCol>
          <Card>
            <SectionHead title="Data Storytelling" sub="Transform raw data insights into compelling executive narratives" />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Select label="Target Audience" value={storyAudience} onChange={setStoryAud}
                options={AUDIENCES.map(a => ({ label: a, value: a }))} />
              <Select label="Format"          value={storyFormat}   onChange={setStoryFormat}
                options={FORMATS.map(f => ({ label: f, value: f }))} />
            </div>
            <Input label="Business Context"   value={storyContext}  onChange={setStoryCtx}  rows={3} />
            <Input label="Key Data Insights (one per line)" value={storyInsights} onChange={setStoryIns} rows={6} />
            <div style={{ padding: 10, background: 'rgba(99,102,241,0.08)', borderRadius: 8, marginBottom: 14 }}>
              <div style={{ fontSize: 11, color: '#a5b4fc', marginBottom: 4 }}>📖 Story structure</div>
              <div style={{ fontSize: 11, color: '#6b7280' }}>Hook → Context → Data journey → Key finding → Implication → Recommendation → Call to action</div>
            </div>
            <Btn
              onClick={() => storyApi.call(() => analystEnhance('data_story', {
                business_context: storyContext,
                key_insights:     storyInsights,
                audience:         storyAudience,
                format:           storyFormat,
              }))}
              loading={storyApi.loading}
            >
              📖 Build Data Story
            </Btn>
          </Card>
          <div>
            <Card style={{ marginBottom: 12 }}>
              <SectionHead title="Story Output Includes" sub="" />
              {['7-part narrative structure','Chart title recommendations','Annotation suggestions for key data points','Executive summary (3 bullet points)','Decision framework for stakeholders'].map(i => (
                <div key={i} style={{ display: 'flex', gap: 8, padding: '5px 0', borderBottom: '1px solid #1e2535' }}>
                  <span style={{ color: '#22c55e', fontSize: 12 }}>✓</span>
                  <span style={{ color: '#9ca3af', fontSize: 12 }}>{i}</span>
                </div>
              ))}
            </Card>
            <ResultBox data={storyApi.data ? { story: (storyApi.data as any).result } : null} loading={storyApi.loading} error={storyApi.error} title="Data Story" />
          </div>
        </TwoCol>
      )}

      {/* ── Anomaly Detection ── */}
      {tab === 'anomaly' && (
        <TwoCol>
          <Card>
            <SectionHead title="Anomaly Detection Analysis" sub="Statistical analysis + root cause hypotheses + alert recommendations" />
            <Input label="Metric Name"          value={anomalyMetric} onChange={setAnomalyMetric} />
            <Input label="Data Points (paste timeseries or summary)" value={anomalyData} onChange={setAnomalyData} rows={6} />
            <Input label="Expected Normal Range" value={anomalyRange} onChange={setAnomalyRange} />
            <Input label="System Context"        value={anomalyCtx}   onChange={setAnomalyCtx}   rows={2} />
            <Btn
              onClick={() => anomalyApi.call(() => analystEnhance('anomaly_detection', {
                metric_name:      anomalyMetric,
                data_points:      anomalyData,
                expected_range:   anomalyRange,
                business_context: anomalyCtx,
              }))}
              loading={anomalyApi.loading}
            >
              🚨 Detect Anomalies
            </Btn>
          </Card>
          <div>
            <Card style={{ marginBottom: 12 }}>
              <SectionHead title="Analysis Includes" sub="" />
              {['Statistical analysis (mean, std dev, Z-scores)','Anomaly identification with timestamps','Root cause hypotheses (3 ranked by probability)','Business impact assessment','Detection methodology recommendation','Alert threshold recommendations','Monitoring dashboard design'].map(i => (
                <div key={i} style={{ display: 'flex', gap: 8, padding: '4px 0', borderBottom: '1px solid #1e2535' }}>
                  <span style={{ color: '#22c55e', fontSize: 12 }}>✓</span>
                  <span style={{ color: '#9ca3af', fontSize: 12 }}>{i}</span>
                </div>
              ))}
            </Card>
            <ResultBox data={anomalyApi.data ? { analysis: (anomalyApi.data as any).result } : null} loading={anomalyApi.loading} error={anomalyApi.error} title="Anomaly Analysis" />
          </div>
        </TwoCol>
      )}

      {tab === 'about' && (
        <TwoCol>
          <Card>
            <SectionHead title="What the Analyst Agent Does" sub="Full SQL-to-insight pipeline" />
            {[
              { icon: '🗄️', title: 'SQL Generation',     desc: 'Converts your question to optimised SELECT queries with GROUP BY, aggregations, and aliases' },
              { icon: '📊', title: 'Chart Visualisation', desc: 'Auto-selects chart type (bar / line / scatter / pie / histogram) and generates Plotly figures' },
              { icon: '🐼', title: 'Pandas Analysis',     desc: 'Upload a CSV for describe(), isnull(), shape, and custom analysis code' },
              { icon: '🧠', title: 'Insight Report',      desc: 'Synthesises data into Key Insight → Analysis → Notable Findings → Recommendations' },
              { icon: '📖', title: 'Data Storytelling',   desc: 'Transforms insights into executive narratives with 7-part story structure' },
              { icon: '🚨', title: 'Anomaly Detection',   desc: 'Statistical analysis + root cause hypotheses + alert threshold recommendations' },
            ].map(({ icon, title, desc }) => (
              <div key={title} style={{ display: 'flex', gap: 10, marginBottom: 14 }}>
                <span style={{ fontSize: 22, flexShrink: 0 }}>{icon}</span>
                <div>
                  <div style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 600, marginBottom: 2 }}>{title}</div>
                  <div style={{ color: '#6b7280', fontSize: 12 }}>{desc}</div>
                </div>
              </div>
            ))}
          </Card>
          <Card>
            <SectionHead title="Available Tables" sub="Agent auto-discovers schema on every query" />
            <div style={{ background: '#0f1117', borderRadius: 8, padding: 14 }}>
              {['users','sessions','messages','tool_results','audit_logs','hitl_requests','billing_subscriptions','ab_experiments','scheduler_tasks'].map(t => (
                <div key={t} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '5px 0', borderBottom: '1px solid #1e2535', fontSize: 12, color: '#a5b4fc' }}>
                  <span style={{ color: '#4b5563' }}>▸</span>
                  <code>{t}</code>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 12 }}>
              <Badge text="Read-Only" color="blue" />
              <span style={{ marginLeft: 8, fontSize: 11, color: '#6b7280' }}>Agent can only run SELECT queries — no mutations</span>
            </div>
          </Card>
        </TwoCol>
      )}
    </PageShell>
  )
}
