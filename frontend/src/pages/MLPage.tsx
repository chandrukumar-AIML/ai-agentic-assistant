// frontend/src/pages/MLPage.tsx — ML Engineer Vertical
import { useState } from 'react'
import { PageShell, Card, Btn, Input, Select, ResultBox, Tabs, TwoCol, useApi, SectionHead, Badge } from '../components/ui'
import { apiFetch } from '../lib/api'

const mlAction = (action: string, payload: object) =>
  apiFetch('/verticals/ml/action', { method: 'POST', body: JSON.stringify({ action, payload }) }, 360_000)

const TASK_TYPES  = ['classification', 'regression', 'clustering', 'nlp', 'computer_vision', 'time_series', 'ranking']
const COMPUTE_OPT = ['GPU single', 'GPU multi', 'CPU only', 'TPU', 'A100 cluster']

export default function MLPage() {
  const [tab, setTab] = useState('experiment')

  // Experiment Design tab
  const [problem, setProblem]   = useState('Predict customer churn within the next 30 days based on usage patterns, support tickets, and payment history.')
  const [dataset, setDataset]   = useState('500K rows, 45 features: user_id, signup_date, daily_active_seconds, feature_usage_flags (20), support_ticket_count, payment_failures, plan_tier, last_login_days_ago. Target: churned_30d (binary).')
  const [taskType, setTaskType] = useState('classification')
  const [baseline, setBaseline] = useState('0.72')
  const expApi                  = useApi()

  // Model Eval tab
  const [modelName, setModelName]   = useState('XGBoost v2')
  const [evalTask, setEvalTask]     = useState('classification')
  const [threshold, setThreshold]   = useState('0.80')
  const [metricsRaw, setMetricsRaw] = useState('accuracy: 0.847\nprecision: 0.813\nrecall: 0.791\nf1_score: 0.802\nauc_roc: 0.891\nlog_loss: 0.342\ntrain_time_sec: 45\ninference_p99_ms: 12')
  const evalApi                     = useApi()

  // Feature Engineering tab
  const [featDataset, setFeatDataset]   = useState('E-commerce transaction data: user demographics, product catalog (category, price, rating), purchase history, browsing sessions, cart abandons, search queries, reviews written')
  const [targetVar, setTargetVar]       = useState('purchase_probability_next_7d')
  const [existingFeat, setExistingFeat] = useState('user_age\ndays_since_signup\ntotal_orders\navg_order_value\nlast_purchase_days_ago')
  const [domain, setDomain]             = useState('ecommerce')
  const featApi                         = useApi()

  // Drift Analysis tab
  const [driftModel, setDriftModel]   = useState('ChurnPredictor v1.2')
  const [daysSince, setDaysSince]     = useState('45')
  const [prodMetrics, setProdMetrics] = useState('accuracy: 0.791\nprecision: 0.744\nrecall: 0.812\nauc_roc: 0.841\npred_positive_rate: 0.183\navg_confidence: 0.67')
  const [baseMetrics, setBaseMetrics] = useState('accuracy: 0.847\nprecision: 0.813\nrecall: 0.791\nauc_roc: 0.891\npred_positive_rate: 0.142\navg_confidence: 0.79')
  const driftApi                      = useApi()

  // Prompt Eval tab
  const [promptText, setPromptText]   = useState('Classify the sentiment of this customer review as Positive, Negative, or Neutral. Review: {review}')
  const [promptTask, setPromptTask]   = useState('Sentiment classification of customer product reviews for e-commerce platform')
  const promptApi                     = useApi()

  const parseMetrics = (raw: string): Record<string, string> =>
    Object.fromEntries(
      raw.split('\n')
        .map(l => l.split(':').map(s => s.trim()))
        .filter(p => p.length === 2)
    )

  return (
    <PageShell
      icon="🤖"
      title="AI ML Engineer"
      subtitle="Experiment design, model evaluation, feature engineering, drift detection, and prompt evaluation"
    >
      <Tabs
        tabs={[
          { id: 'experiment', label: 'Experiment Design',    icon: '🧪' },
          { id: 'eval',       label: 'Model Evaluation',     icon: '📊' },
          { id: 'features',   label: 'Feature Engineering',  icon: '⚙️' },
          { id: 'drift',      label: 'Drift Analysis',       icon: '📉' },
          { id: 'prompt',     label: 'Prompt Evaluation',    icon: '💬' },
        ]}
        active={tab} onChange={setTab}
      />

      {/* ── Experiment Design ── */}
      {tab === 'experiment' && (
        <TwoCol>
          <Card>
            <SectionHead title="ML Experiment Designer" sub="Problem → complete experiment plan with metrics, splits, and MLflow config" />
            <Input label="Problem Statement" value={problem}  onChange={setProblem}  rows={3} />
            <Input label="Dataset Description" value={dataset} onChange={setDataset} rows={3} />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 14 }}>
              <Select
                label="Task Type"
                value={taskType}
                onChange={setTaskType}
                options={TASK_TYPES.map(t => ({ value: t, label: t.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase()) }))}
              />
              <Input label="Baseline Metric (0-1)" value={baseline} onChange={setBaseline} />
            </div>
            <Btn
              onClick={() => expApi.call(() => mlAction('experiment_design', {
                problem_statement:    problem,
                dataset_description:  dataset,
                model_type:           taskType,
                baseline_metric:      parseFloat(baseline) || 0,
              }))}
              loading={expApi.loading}
            >
              🧪 Design Experiment
            </Btn>
          </Card>
          <ResultBox
            data={expApi.data ? { experiment: (expApi.data as any).experiment } : null}
            loading={expApi.loading}
            error={expApi.error}
            title="Experiment Plan"
          />
        </TwoCol>
      )}

      {/* ── Model Evaluation ── */}
      {tab === 'eval' && (
        <TwoCol>
          <Card>
            <SectionHead title="Model Performance Evaluator" sub="Paste your metrics → get bottleneck analysis and improvement roadmap" />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Input label="Model Name"      value={modelName}  onChange={setModelName} />
              <Input label="Production Threshold" value={threshold} onChange={setThreshold} />
            </div>
            <Select
              label="Task Type"
              value={evalTask}
              onChange={setEvalTask}
              options={TASK_TYPES.map(t => ({ value: t, label: t.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase()) }))}
            />
            <Input
              label="Model Metrics (key: value, one per line)"
              value={metricsRaw}
              onChange={setMetricsRaw}
              rows={8}
            />
            <Btn
              onClick={() => evalApi.call(() => mlAction('model_eval', {
                metrics:    parseMetrics(metricsRaw),
                model_name: modelName,
                task_type:  evalTask,
                threshold:  parseFloat(threshold) || 0,
              }))}
              loading={evalApi.loading}
            >
              📊 Evaluate Model
            </Btn>
          </Card>
          <ResultBox
            data={evalApi.data ? { evaluation: (evalApi.data as any).evaluation } : null}
            loading={evalApi.loading}
            error={evalApi.error}
            title="Model Evaluation Report"
          />
        </TwoCol>
      )}

      {/* ── Feature Engineering ── */}
      {tab === 'features' && (
        <TwoCol>
          <Card>
            <SectionHead title="Feature Engineering Advisor" sub="Dataset description → ranked feature ideas with code snippets" />
            <Input label="Dataset Description" value={featDataset} onChange={setFeatDataset} rows={4} />
            <Input label="Target Variable"     value={targetVar}   onChange={setTargetVar} />
            <Input label="Domain"              value={domain}      onChange={setDomain} />
            <Input
              label="Existing Features (one per line)"
              value={existingFeat}
              onChange={setExistingFeat}
              rows={5}
            />
            <Btn
              onClick={() => featApi.call(() => mlAction('feature_engineering', {
                dataset_description: featDataset,
                target_variable:     targetVar,
                existing_features:   existingFeat.split('\n').map(l => l.trim()).filter(Boolean),
                domain,
              }))}
              loading={featApi.loading}
            >
              ⚙️ Suggest Features
            </Btn>
          </Card>
          <ResultBox
            data={featApi.data ? { features: (featApi.data as any).suggestions } : null}
            loading={featApi.loading}
            error={featApi.error}
            title="Feature Engineering Plan"
          />
        </TwoCol>
      )}

      {/* ── Drift Analysis ── */}
      {tab === 'drift' && (
        <TwoCol>
          <Card>
            <SectionHead title="Model Drift Detector" sub="Production vs baseline metrics → severity, root cause, retraining strategy" />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Input label="Model Name"            value={driftModel} onChange={setDriftModel} />
              <Input label="Days Since Training"   value={daysSince}  onChange={setDaysSince} />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Input
                label="Production Metrics (key: value)"
                value={prodMetrics}
                onChange={setProdMetrics}
                rows={7}
              />
              <Input
                label="Baseline Metrics (key: value)"
                value={baseMetrics}
                onChange={setBaseMetrics}
                rows={7}
              />
            </div>
            <Btn
              onClick={() => driftApi.call(() => mlAction('drift_analysis', {
                model_name:           driftModel,
                days_since_training:  parseInt(daysSince) || 0,
                production_metrics:   parseMetrics(prodMetrics),
                baseline_metrics:     parseMetrics(baseMetrics),
              }))}
              loading={driftApi.loading}
            >
              📉 Analyze Drift
            </Btn>
          </Card>
          <div>
            <Card style={{ marginBottom: 12 }}>
              <SectionHead title="Drift Severity" sub="" />
              {[
                { label: 'Critical', color: '#ef4444', desc: 'Retrain immediately, consider rollback' },
                { label: 'High',     color: '#f97316', desc: 'Retrain within 48 hours' },
                { label: 'Medium',   color: '#eab308', desc: 'Schedule retrain this sprint' },
                { label: 'Low',      color: '#22c55e', desc: 'Monitor, no immediate action' },
              ].map(s => (
                <div key={s.label} style={{ display: 'flex', gap: 10, marginBottom: 6, alignItems: 'center' }}>
                  <div style={{ width: 10, height: 10, borderRadius: '50%', background: s.color, flexShrink: 0 }} />
                  <span style={{ color: s.color, fontSize: 12, fontWeight: 600, minWidth: 60 }}>{s.label}</span>
                  <span style={{ color: '#6b7280', fontSize: 11 }}>{s.desc}</span>
                </div>
              ))}
            </Card>
            <ResultBox
              data={driftApi.data ? { analysis: (driftApi.data as any).analysis } : null}
              loading={driftApi.loading}
              error={driftApi.error}
              title="Drift Analysis Report"
            />
          </div>
        </TwoCol>
      )}

      {/* ── Prompt Evaluation ── */}
      {tab === 'prompt' && (
        <TwoCol>
          <Card>
            <SectionHead title="LLM Prompt Evaluator" sub="Prompt → clarity score, failure modes, improved version" />
            <Input label="Task Description" value={promptTask} onChange={setPromptTask} rows={2} />
            <Input
              label="Prompt to Evaluate"
              value={promptText}
              onChange={setPromptText}
              rows={7}
            />
            <div style={{ padding: 10, background: 'rgba(99,102,241,0.08)', borderRadius: 8, marginBottom: 14 }}>
              <div style={{ fontSize: 11, color: '#a5b4fc', fontWeight: 600, marginBottom: 4 }}>Tip</div>
              <div style={{ fontSize: 11, color: '#6b7280' }}>
                Use {'{variable}'} placeholders for dynamic parts. The evaluator will assess clarity,
                specificity, failure modes, and suggest Chain-of-Thought enhancements.
              </div>
            </div>
            <Btn
              onClick={() => promptApi.call(() => mlAction('prompt_eval', {
                prompt_text:      promptText,
                task_description: promptTask,
              }))}
              loading={promptApi.loading}
            >
              💬 Evaluate Prompt
            </Btn>
          </Card>
          <ResultBox
            data={promptApi.data ? { evaluation: (promptApi.data as any).evaluation } : null}
            loading={promptApi.loading}
            error={promptApi.error}
            title="Prompt Evaluation"
          />
        </TwoCol>
      )}
    </PageShell>
  )
}
