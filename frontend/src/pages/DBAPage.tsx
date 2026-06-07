// frontend/src/pages/DBAPage.tsx — Database Administrator Vertical
import { useState } from 'react'
import { PageShell, Card, Btn, Input, Select, ResultBox, Tabs, TwoCol, useApi, SectionHead } from '../components/ui'
import { apiFetch } from '../lib/api'

const dbaAction = (action: string, payload: object) =>
  apiFetch('/verticals/dba/action', { method: 'POST', body: JSON.stringify({ action, payload }) }, 360_000)

const DB_TYPES = ['postgresql', 'mysql', 'sqlite', 'mongodb', 'mssql']
const SCALES   = ['small', 'medium', 'large']

export default function DBAPage() {
  const [tab, setTab] = useState('optimize')

  // Query Optimizer tab
  const [sql, setSql]               = useState(`SELECT u.*, COUNT(o.id) as order_count, SUM(o.total) as lifetime_value
FROM users u
LEFT JOIN orders o ON o.user_id = u.id
LEFT JOIN order_items oi ON oi.order_id = o.id
LEFT JOIN products p ON p.id = oi.product_id
WHERE u.created_at > '2024-01-01'
  AND u.country = 'IN'
  AND o.status = 'completed'
GROUP BY u.id
ORDER BY lifetime_value DESC
LIMIT 100;`)
  const [explainOut, setExplainOut] = useState('')
  const [dbType, setDbType]         = useState('postgresql')
  const optApi                      = useApi()

  // Schema Design tab
  const [schemaReqs, setSchemaReqs]     = useState('Multi-tenant SaaS platform. Each organization has users, projects, and tasks. Users can belong to multiple organizations with different roles. Tasks have comments, attachments, labels, and due dates. Support soft delete and full audit trail.')
  const [entities, setEntities]         = useState('Organization\nUser\nProject\nTask\nComment\nAttachment\nLabel\nAuditLog')
  const [schemaDb, setSchemaDb]         = useState('postgresql')
  const [scale, setScale]               = useState('medium')
  const schemaApi                       = useApi()

  // Index Advisor tab
  const [indexQueries, setIndexQueries] = useState(`SELECT * FROM tasks WHERE project_id = $1 AND status = $2 AND due_date < NOW() ORDER BY priority DESC;

SELECT u.email, COUNT(t.id) FROM users u JOIN task_assignments ta ON ta.user_id = u.id JOIN tasks t ON t.id = ta.task_id WHERE t.status != 'done' GROUP BY u.id;

SELECT * FROM audit_logs WHERE entity_type = $1 AND entity_id = $2 AND created_at > $3 ORDER BY created_at DESC LIMIT 50;`)
  const [tableSchema, setTableSchema]   = useState('')
  const [indexDb, setIndexDb]           = useState('postgresql')
  const indexApi                        = useApi()

  // Migration tab
  const [changeDesc, setChangeDesc]     = useState('Add a full_text_search column of type tsvector to the tasks table, populate it from title + description, add GIN index, and set up a trigger to auto-update on INSERT/UPDATE.')
  const [currentSchema, setCurrSchema]  = useState('')
  const [migDb, setMigDb]               = useState('postgresql')
  const migApi                          = useApi()

  // Health Analysis tab
  const [healthMetrics, setHealthMetrics] = useState(`cache_hit_ratio: 0.87
connections_active: 95
connections_max: 100
deadlocks_per_hour: 3
seq_scans_per_min: 450
index_scans_per_min: 2800
dead_tuples_total: 4200000
last_vacuum_hours_ago: 168
replication_lag_seconds: 8
disk_usage_pct: 78
avg_query_time_ms: 340
p99_query_time_ms: 4200
slow_queries_per_min: 12`)
  const [healthDb, setHealthDb] = useState('postgresql')
  const healthApi               = useApi()

  const parseMetrics = (raw: string): Record<string, string> =>
    Object.fromEntries(
      raw.split('\n')
        .map(l => l.split(':').map(s => s.trim()))
        .filter(p => p.length === 2)
    )

  return (
    <PageShell
      icon="🗄️"
      title="AI Database Administrator"
      subtitle="Query optimization, schema design, index recommendations, migrations, and health analysis"
    >
      <Tabs
        tabs={[
          { id: 'optimize', label: 'Query Optimizer',   icon: '⚡' },
          { id: 'schema',   label: 'Schema Design',     icon: '📐' },
          { id: 'index',    label: 'Index Advisor',     icon: '🔑' },
          { id: 'migrate',  label: 'Migration Script',  icon: '🔄' },
          { id: 'health',   label: 'Health Analysis',   icon: '💊' },
        ]}
        active={tab} onChange={setTab}
      />

      {/* ── Query Optimizer ── */}
      {tab === 'optimize' && (
        <TwoCol>
          <Card>
            <SectionHead title="SQL Query Optimizer" sub="Slow query → optimized SQL + index recommendations" />
            <Select
              label="Database"
              value={dbType}
              onChange={setDbType}
              options={DB_TYPES.map(d => ({ value: d, label: d.toUpperCase() }))}
            />
            <Input label="SQL Query"                    value={sql}        onChange={setSql}        rows={10} />
            <Input label="EXPLAIN ANALYZE output (optional)" value={explainOut} onChange={setExplainOut} rows={5} />
            <Btn
              onClick={() => optApi.call(() => dbaAction('optimize_query', {
                sql, explain_output: explainOut, db_type: dbType,
              }))}
              loading={optApi.loading}
            >
              ⚡ Optimize Query
            </Btn>
          </Card>
          <ResultBox
            data={optApi.data ? { optimization: (optApi.data as any).optimization } : null}
            loading={optApi.loading}
            error={optApi.error}
            title="Query Optimization Report"
          />
        </TwoCol>
      )}

      {/* ── Schema Design ── */}
      {tab === 'schema' && (
        <TwoCol>
          <Card>
            <SectionHead title="Database Schema Designer" sub="Requirements → normalized schema with CREATE TABLE SQL" />
            <Input label="Business Requirements" value={schemaReqs} onChange={setSchemaReqs} rows={5} />
            <Input label="Entities (one per line)" value={entities} onChange={setEntities} rows={6} />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 14 }}>
              <Select
                label="Database"
                value={schemaDb}
                onChange={setSchemaDb}
                options={DB_TYPES.map(d => ({ value: d, label: d.toUpperCase() }))}
              />
              <Select
                label="Scale"
                value={scale}
                onChange={setScale}
                options={SCALES.map(s => ({ value: s, label: s.charAt(0).toUpperCase() + s.slice(1) }))}
              />
            </div>
            <Btn
              onClick={() => schemaApi.call(() => dbaAction('design_schema', {
                requirements: schemaReqs,
                entities:     entities.split('\n').map(l => l.trim()).filter(Boolean),
                db_type:      schemaDb,
                scale,
              }))}
              loading={schemaApi.loading}
            >
              📐 Design Schema
            </Btn>
          </Card>
          <ResultBox
            data={schemaApi.data ? { schema: (schemaApi.data as any).schema } : null}
            loading={schemaApi.loading}
            error={schemaApi.error}
            title="Database Schema"
          />
        </TwoCol>
      )}

      {/* ── Index Advisor ── */}
      {tab === 'index' && (
        <TwoCol>
          <Card>
            <SectionHead title="Index Advisor" sub="Query workload → optimal index strategy with CREATE INDEX SQL" />
            <Select
              label="Database"
              value={indexDb}
              onChange={setIndexDb}
              options={DB_TYPES.map(d => ({ value: d, label: d.toUpperCase() }))}
            />
            <Input
              label="Queries (paste all critical queries)"
              value={indexQueries}
              onChange={setIndexQueries}
              rows={10}
            />
            <Input
              label="Table Schema (optional — for context)"
              value={tableSchema}
              onChange={setTableSchema}
              rows={4}
            />
            <Btn
              onClick={() => indexApi.call(() => dbaAction('index_recommend', {
                queries:      indexQueries.split('\n\n').map(q => q.trim()).filter(Boolean),
                table_schema: tableSchema,
                db_type:      indexDb,
              }))}
              loading={indexApi.loading}
            >
              🔑 Recommend Indexes
            </Btn>
          </Card>
          <ResultBox
            data={indexApi.data ? { recommendations: (indexApi.data as any).recommendations } : null}
            loading={indexApi.loading}
            error={indexApi.error}
            title="Index Recommendations"
          />
        </TwoCol>
      )}

      {/* ── Migration Script ── */}
      {tab === 'migrate' && (
        <TwoCol>
          <Card>
            <SectionHead title="Migration Generator" sub="Change description → safe up/down SQL + Alembic script" />
            <Select
              label="Database"
              value={migDb}
              onChange={setMigDb}
              options={DB_TYPES.map(d => ({ value: d, label: d.toUpperCase() }))}
            />
            <Input
              label="Describe the database change"
              value={changeDesc}
              onChange={setChangeDesc}
              rows={4}
            />
            <Input
              label="Current Schema (optional)"
              value={currentSchema}
              onChange={setCurrSchema}
              rows={5}
            />
            <div style={{ padding: 10, background: 'rgba(239,68,68,0.08)', borderRadius: 8, marginBottom: 14, border: '1px solid rgba(239,68,68,0.2)' }}>
              <div style={{ fontSize: 11, color: '#ef4444', fontWeight: 600, marginBottom: 4 }}>⚠️ Safety First</div>
              <div style={{ fontSize: 11, color: '#6b7280' }}>
                Always review and test migrations on staging before running in production.
                The AI will flag lock-acquiring operations and suggest zero-downtime alternatives.
              </div>
            </div>
            <Btn
              onClick={() => migApi.call(() => dbaAction('migration_script', {
                change_description: changeDesc,
                current_schema:     currentSchema,
                db_type:            migDb,
              }))}
              loading={migApi.loading}
            >
              🔄 Generate Migration
            </Btn>
          </Card>
          <ResultBox
            data={migApi.data ? { migration: (migApi.data as any).migration } : null}
            loading={migApi.loading}
            error={migApi.error}
            title="Migration Script"
          />
        </TwoCol>
      )}

      {/* ── Health Analysis ── */}
      {tab === 'health' && (
        <TwoCol>
          <Card>
            <SectionHead title="Database Health Analyzer" sub="Paste pg_stat metrics → health score + action plan" />
            <Select
              label="Database"
              value={healthDb}
              onChange={setHealthDb}
              options={DB_TYPES.map(d => ({ value: d, label: d.toUpperCase() }))}
            />
            <Input
              label="Metrics (key: value, one per line)"
              value={healthMetrics}
              onChange={setHealthMetrics}
              rows={14}
            />
            <Btn
              onClick={() => healthApi.call(() => dbaAction('health_analysis', {
                metrics: parseMetrics(healthMetrics),
                db_type: healthDb,
              }))}
              loading={healthApi.loading}
            >
              💊 Analyze Health
            </Btn>
          </Card>
          <div>
            <Card style={{ marginBottom: 12 }}>
              <SectionHead title="Key Metrics to Watch" sub="" />
              {[
                { metric: 'cache_hit_ratio',       target: '> 0.95',  unit: '' },
                { metric: 'connections_active/max', target: '< 80%',   unit: '' },
                { metric: 'replication_lag',        target: '< 1s',    unit: '' },
                { metric: 'dead_tuples',            target: '< 1M',    unit: '' },
                { metric: 'p99_query_time',         target: '< 500ms', unit: '' },
              ].map(({ metric, target }) => (
                <div key={metric} style={{ display: 'flex', justifyContent: 'space-between', padding: '5px 0', borderBottom: '1px solid #1e2535' }}>
                  <code style={{ color: '#5eead4', fontSize: 11 }}>{metric}</code>
                  <span style={{ color: '#6b7280', fontSize: 11 }}>Target: {target}</span>
                </div>
              ))}
            </Card>
            <ResultBox
              data={healthApi.data ? { analysis: (healthApi.data as any).analysis } : null}
              loading={healthApi.loading}
              error={healthApi.error}
              title="Health Analysis Report"
            />
          </div>
        </TwoCol>
      )}
    </PageShell>
  )
}
