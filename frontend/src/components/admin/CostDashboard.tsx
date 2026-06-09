// frontend/src/components/admin/CostDashboard.tsx
import React, { useState, useEffect, useCallback } from 'react'

interface DailyBreakdown {
  [date: string]: { cost: number; calls: number; tokens: number }
}

interface ModelBreakdown {
  [model: string]: { cost: number; calls: number }
}

interface CostReport {
  period_days:     number
  total_cost_usd:  number
  total_tokens:    number
  total_calls:     number
  daily_breakdown: DailyBreakdown
  model_breakdown: ModelBreakdown
}

interface BudgetStatus {
  monthly_budget:  number
  monthly_spend:   number
  remaining:       number
  pct_used:        number
  alert_triggered: boolean
  hard_limit_hit:  boolean
  plan_tier:       string
  active_alert:    { message: string } | null
}

interface CacheStats {
  hits:       number
  misses:     number
  hit_rate:   number
  cost_saved: number
}

const API_BASE   = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
const authHeader = () => ({ Authorization: `Bearer ${sessionStorage.getItem('aaa_token') || 'dev'}` })

const MODEL_COLORS: Record<string, string> = {
  'gpt-4o':       '#534AB7',
  'gpt-4o-mini':  '#22c55e',
  'ollama':        '#f59e0b',
  'ollama/llama3': '#f59e0b',
  'unknown':       '#9ca3af',
}

function MetricCard({
  label, value, sub, alert
}: {
  label: string; value: string; sub?: string; alert?: boolean
}) {
  return (
    <div style={{
      padding: '14px 16px',
      background: alert ? '#fff0f0' : 'var(--color-background-secondary)',
      borderRadius: '10px',
      border: `0.5px solid ${alert ? '#fca5a5' : 'var(--color-border-tertiary)'}`,
    }}>
      <p style={{ fontSize: '11px', color: 'var(--color-text-tertiary)', margin: '0 0 4px' }}>
        {label}
      </p>
      <p style={{
        fontSize: '20px', fontWeight: 500, margin: 0,
        color: alert ? '#dc2626' : 'var(--color-text-primary)',
      }}>
        {value}
      </p>
      {sub && (
        <p style={{ fontSize: '10px', color: 'var(--color-text-tertiary)', margin: '3px 0 0' }}>
          {sub}
        </p>
      )}
    </div>
  )
}

function BudgetBar({ pct, alert: _alert }: { pct: number; alert: boolean }) {
  const color = pct >= 1.0 ? '#dc2626' : pct >= 0.8 ? '#f59e0b' : '#22c55e'
  return (
    <div>
      <div style={{
        display: 'flex', justifyContent: 'space-between',
        fontSize: '11px', color: 'var(--color-text-tertiary)', marginBottom: '4px',
      }}>
        <span>Monthly budget used</span>
        <span style={{ fontWeight: 500, color }}>{(pct * 100).toFixed(1)}%</span>
      </div>
      <div style={{
        height: '8px', borderRadius: '4px',
        background: 'var(--color-border-tertiary)', overflow: 'hidden',
      }}>
        <div style={{
          width: `${Math.min(pct * 100, 100)}%`, height: '100%',
          background: color, borderRadius: '4px',
          transition: 'width 0.5s',
        }} />
      </div>
    </div>
  )
}

export default function CostDashboard() {
  const [report,  setReport]  = useState<CostReport | null>(null)
  const [budget,  setBudget]  = useState<BudgetStatus | null>(null)
  const [cache,   setCache]   = useState<CacheStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [days,    setDays]    = useState(30)
  const [testQuery, setTestQuery] = useState('')
  // FIXED: replaced `any` with explicit shape matching API response
  const [classResult, setClassResult] = useState<{
    complexity: string
    model:      string
    confidence: number
    reasons?:   string[]
  } | null>(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const [rRes, bRes, cRes] = await Promise.all([
        fetch(`${API_BASE}/cost/report?days=${days}`,  { headers: authHeader() }),
        fetch(`${API_BASE}/cost/budget`,               { headers: authHeader() }),
        fetch(`${API_BASE}/cost/cache-stats`,          { headers: authHeader() }),
      ])
      const [r, b, c] = await Promise.all([rRes.json(), bRes.json(), cRes.json()])
      setReport(r)
      setBudget(b)
      setCache(c)
    } catch (e) {
      void e // FIXED: removed console.error production log
    } finally {
      setLoading(false)
    }
  }, [days])

  useEffect(() => { fetchData() }, [fetchData])

  const testClassify = async () => {
    if (!testQuery) return
    try { // FIXED: unhandled Promise rejection — wrapped in try/catch
      const res  = await fetch(
        `${API_BASE}/cost/classify?query=${encodeURIComponent(testQuery)}`,
        { method: 'POST', headers: authHeader() }
      )
      const data = await res.json()
      setClassResult(data)
    } catch {
      // network/parse errors silently ignored — classResult stays as-is
    }
  }

  return (
    <div style={{ padding: '20px', maxWidth: '900px' }}>
      {/* Budget alert banner */}
      {budget?.active_alert && (
        <div style={{
          marginBottom: '16px', padding: '10px 14px', borderRadius: '8px',
          background: '#fff7ed', border: '0.5px solid #fdba74',
          fontSize: '12px', color: '#c2410c', fontWeight: 500,
        }}>
          ⚠️ {budget.active_alert.message}
        </div>
      )}

      {/* Period selector */}
      <div style={{ display: 'flex', gap: '6px', marginBottom: '16px' }}>
        {[7, 30, 90].map(d => (
          <button key={d} onClick={() => setDays(d)}
            style={{
              padding: '5px 12px', fontSize: '11px', borderRadius: '20px',
              background: days === d ? '#534AB7' : 'var(--color-background-secondary)',
              color: days === d ? '#fff' : 'var(--color-text-secondary)',
              border: `0.5px solid ${days === d ? '#534AB7' : 'var(--color-border-tertiary)'}`,
              cursor: 'pointer', fontWeight: days === d ? 500 : 400,
            }}
          >
            {d}d
          </button>
        ))}
        <button onClick={fetchData}
          style={{
            marginLeft: 'auto', padding: '5px 12px', fontSize: '11px',
            background: 'var(--color-background-secondary)',
            border: '0.5px solid var(--color-border-tertiary)',
            borderRadius: '20px', cursor: 'pointer',
            color: 'var(--color-text-secondary)',
          }}
        >
          Refresh
        </button>
      </div>

      {loading ? (
        <p style={{ fontSize: '12px', color: 'var(--color-text-tertiary)' }}>Loading...</p>
      ) : (
        <>
          {/* Summary metrics */}
          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '10px', marginBottom: '20px',
          }}>
            <MetricCard
              label="Total Cost"
              value={`$${report?.total_cost_usd.toFixed(4) || '0'}`}
              sub={`last ${days} days`}
              alert={budget?.alert_triggered}
            />
            <MetricCard
              label="API Calls"
              value={(report?.total_calls || 0).toLocaleString()}
              sub={`avg $${report ? (report.total_cost_usd / Math.max(report.total_calls, 1)).toFixed(5) : '0'}/call`}
            />
            <MetricCard
              label="Tokens Used"
              value={(report?.total_tokens || 0).toLocaleString()}
            />
            <MetricCard
              label="Cache Savings"
              value={`$${cache?.cost_saved.toFixed(4) || '0'}`}
              sub={`${((cache?.hit_rate || 0) * 100).toFixed(1)}% hit rate`}
            />
          </div>

          {/* Budget progress */}
          {budget && (
            <div style={{
              padding: '16px', marginBottom: '20px',
              background: 'var(--color-background-secondary)',
              borderRadius: '12px',
              border: '0.5px solid var(--color-border-tertiary)',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                <p style={{ fontSize: '12px', fontWeight: 500, margin: 0, color: 'var(--color-text-primary)' }}>
                  Monthly Budget · {budget.plan_tier} plan
                </p>
                <p style={{ fontSize: '11px', color: 'var(--color-text-tertiary)', margin: 0 }}>
                  ${budget.monthly_spend.toFixed(4)} / ${budget.monthly_budget.toFixed(2)}
                  · ${budget.remaining.toFixed(4)} remaining
                </p>
              </div>
              <BudgetBar pct={budget.pct_used} alert={budget.alert_triggered} />
            </div>
          )}

          {/* Model breakdown */}
          {report?.model_breakdown && Object.keys(report.model_breakdown).length > 0 && (
            <div style={{
              padding: '16px', marginBottom: '20px',
              background: 'var(--color-background-secondary)',
              borderRadius: '12px',
              border: '0.5px solid var(--color-border-tertiary)',
            }}>
              <p style={{
                fontSize: '12px', fontWeight: 500, marginBottom: '12px',
                color: 'var(--color-text-primary)',
              }}>
                Cost by Model
              </p>
              {Object.entries(report.model_breakdown)
                .sort(([,a], [,b]) => b.cost - a.cost)
                .map(([model, stats]) => {
                  const pct = report.total_cost_usd > 0
                    ? stats.cost / report.total_cost_usd
                    : 0
                  const color = MODEL_COLORS[model] || '#9ca3af'
                  return (
                    <div key={model} style={{ marginBottom: '8px' }}>
                      <div style={{
                        display: 'flex', justifyContent: 'space-between',
                        fontSize: '11px', marginBottom: '3px',
                      }}>
                        <span style={{ fontFamily: 'var(--font-mono)', color }}>
                          {model}
                        </span>
                        <span style={{ color: 'var(--color-text-tertiary)' }}>
                          ${stats.cost.toFixed(4)} · {stats.calls} calls · {(pct*100).toFixed(1)}%
                        </span>
                      </div>
                      <div style={{
                        height: '6px', borderRadius: '3px',
                        background: 'var(--color-border-tertiary)', overflow: 'hidden',
                      }}>
                        <div style={{
                          width: `${pct * 100}%`, height: '100%',
                          background: color, borderRadius: '3px',
                        }} />
                      </div>
                    </div>
                  )
                })}
            </div>
          )}

          {/* Daily cost chart (simple bar) */}
          {report?.daily_breakdown && Object.keys(report.daily_breakdown).length > 0 && (
            <div style={{
              padding: '16px', marginBottom: '20px',
              background: 'var(--color-background-secondary)',
              borderRadius: '12px',
              border: '0.5px solid var(--color-border-tertiary)',
            }}>
              <p style={{
                fontSize: '12px', fontWeight: 500, marginBottom: '12px',
                color: 'var(--color-text-primary)',
              }}>
                Daily Cost (last {days} days)
              </p>
              <div style={{
                display: 'flex', alignItems: 'flex-end', gap: '3px',
                height: '80px', overflowX: 'auto',
              }}>
                {Object.entries(report.daily_breakdown)
                  .sort(([a], [b]) => a.localeCompare(b))
                  .slice(-30)
                  .map(([date, stats]) => {
                    const maxCost = Math.max(
                      ...Object.values(report.daily_breakdown).map(d => d.cost)
                    )
                    const height = maxCost > 0
                      ? Math.max(4, (stats.cost / maxCost) * 72)
                      : 4
                    return (
                      <div
                        key={date}
                        title={`${date}: $${stats.cost.toFixed(5)} (${stats.calls} calls)`}
                        style={{
                          flex: '1', minWidth: '8px', maxWidth: '24px',
                          height: `${height}px`, borderRadius: '2px 2px 0 0',
                          background: '#534AB7', opacity: 0.8,
                          cursor: 'help',
                        }}
                      />
                    )
                  })}
              </div>
              <div style={{
                display: 'flex', justifyContent: 'space-between',
                fontSize: '10px', color: 'var(--color-text-tertiary)',
                marginTop: '4px',
              }}>
                <span>Older</span>
                <span>Today</span>
              </div>
            </div>
          )}

          {/* Classifier tester */}
          <div style={{
            padding: '16px',
            background: 'var(--color-background-secondary)',
            borderRadius: '12px',
            border: '0.5px solid var(--color-border-tertiary)',
          }}>
            <p style={{
              fontSize: '12px', fontWeight: 500, marginBottom: '10px',
              color: 'var(--color-text-primary)',
            }}>
              Test Query Classifier
            </p>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '10px' }}>
              <input
                value={testQuery}
                onChange={e => setTestQuery(e.target.value)}
                placeholder="Enter a query to see which model would be selected..."
                style={{
                  flex: 1, padding: '7px 10px', borderRadius: '6px', fontSize: '12px',
                  border: '0.5px solid var(--color-border-tertiary)',
                  background: 'var(--color-background-primary)',
                  color: 'var(--color-text-primary)', outline: 'none',
                }}
                onKeyDown={e => e.key === 'Enter' && testClassify()}
              />
              <button onClick={testClassify}
                style={{
                  padding: '7px 14px', fontSize: '12px', fontWeight: 500,
                  background: '#534AB7', color: '#fff', border: 'none',
                  borderRadius: '6px', cursor: 'pointer',
                }}
              >
                Classify
              </button>
            </div>
            {classResult && (
              <div style={{
                padding: '10px 12px',
                background: 'var(--color-background-primary)',
                borderRadius: '8px',
                border: '0.5px solid var(--color-border-tertiary)',
                fontSize: '12px',
              }}>
                <div style={{ display: 'flex', gap: '8px', marginBottom: '6px' }}>
                  <span style={{
                    padding: '2px 8px', borderRadius: '20px', fontSize: '11px',
                    background: '#EEEDFE', color: '#534AB7', fontWeight: 500,
                  }}>
                    {classResult.complexity}
                  </span>
                  <span style={{
                    padding: '2px 8px', borderRadius: '20px', fontSize: '11px',
                    background: '#c8f0dc', color: '#1a6b4a', fontWeight: 500,
                    fontFamily: 'var(--font-mono)',
                  }}>
                    → {classResult.model}
                  </span>
                  <span style={{ fontSize: '11px', color: 'var(--color-text-tertiary)', marginLeft: 'auto' }}>
                    {(classResult.confidence * 100).toFixed(0)}% confident
                  </span>
                </div>
                <p style={{ margin: 0, color: 'var(--color-text-tertiary)' }}>
                  {classResult.reasons?.join(' · ')}
                </p>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}