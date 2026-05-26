// frontend/src/components/admin/AuditLogViewer.tsx
import React, { useState, useEffect, useCallback } from 'react'

interface AuditEntry {
  id:                  number
  user_id:             string
  session_id:          string
  trace_id:            string
  timestamp:           string
  action:              string
  tool_called:         string | null
  worker_agents:       string[]
  input_tokens:        number
  output_tokens:       number
  cost_usd:            number
  latency_ms:          number
  guardrail_triggered: boolean
  guardrail_type:      string | null
  pii_detected:        boolean
  reflection_loops:    number
  model_used:          string | null
  error:               string | null
}

interface AuditSummary {
  period_days:     number
  total_queries:   number
  total_tokens:    number
  total_cost_usd:  number
  avg_latency_ms:  number
  guardrail_count: number
  pii_count:       number
  error_count:     number
}

const API_BASE   = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
const authHeader = () => ({ Authorization: `Bearer ${sessionStorage.getItem('aaa_token') || 'dev'}` })

function SummaryCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div style={{
      padding: '12px 16px',
      background: 'var(--color-background-secondary)',
      borderRadius: '10px',
      border: '0.5px solid var(--color-border-tertiary)',
    }}>
      <p style={{ fontSize: '11px', color: 'var(--color-text-tertiary)', margin: '0 0 4px' }}>{label}</p>
      <p style={{ fontSize: '18px', fontWeight: 500, color: 'var(--color-text-primary)', margin: 0 }}>{value}</p>
      {sub && <p style={{ fontSize: '10px', color: 'var(--color-text-tertiary)', margin: '2px 0 0' }}>{sub}</p>}
    </div>
  )
}

export default function AuditLogViewer() {
  const [entries,  setEntries]  = useState<AuditEntry[]>([])
  const [summary,  setSummary]  = useState<AuditSummary | null>(null)
  const [loading,  setLoading]  = useState(true)
  const [action,   setAction]   = useState<string>('')
  const [days,     setDays]     = useState(7)

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const [logRes, sumRes] = await Promise.all([
        fetch(
          `${API_BASE}/admin/audit${action ? `?action=${action}` : ''}`,
          { headers: authHeader() }
        ),
        fetch(
          `${API_BASE}/admin/audit/summary?days=${days}`,
          { headers: authHeader() }
        ),
      ])
      const logData = await logRes.json()
      const sumData = await sumRes.json()
      setEntries(logData.entries || [])
      setSummary(sumData)
    } catch (e) {
      void e // FIXED: removed console.error production log
    } finally {
      setLoading(false)
    }
  }, [action, days])

  useEffect(() => { fetchData() }, [fetchData])

  const formatTs = (ts: string) =>
    new Date(ts).toLocaleString('en-US', {
      month: 'short', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
    })

  return (
    <div style={{ padding: '20px' }}>
      {/* Summary cards */}
      {summary && (
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)',
          gap: '10px', marginBottom: '20px',
        }}>
          <SummaryCard label="Total Queries" value={summary.total_queries} sub={`last ${days} days`} />
          <SummaryCard label="Total Cost" value={`$${summary.total_cost_usd.toFixed(4)}`} sub="USD" />
          <SummaryCard label="Avg Latency" value={`${summary.avg_latency_ms.toFixed(0)}ms`} />
          <SummaryCard
            label="Guardrail Triggers"
            value={summary.guardrail_count}
            sub={`${summary.pii_count} PII · ${summary.error_count} errors`}
          />
        </div>
      )}

      {/* Filters */}
      <div style={{
        display: 'flex', gap: '8px', marginBottom: '14px', alignItems: 'center',
      }}>
        <select
          value={action}
          onChange={e => setAction(e.target.value)}
          style={{
            padding: '6px 10px', fontSize: '12px', borderRadius: '6px',
            border: '0.5px solid var(--color-border-tertiary)',
            background: 'var(--color-background-secondary)',
            color: 'var(--color-text-primary)', outline: 'none',
          }}
        >
          <option value="">All actions</option>
          <option value="query">query</option>
          <option value="ingest">ingest</option>
          <option value="delete_memory">delete_memory</option>
          <option value="admin_create_user">admin_create_user</option>
        </select>

        <select
          value={days}
          onChange={e => setDays(Number(e.target.value))}
          style={{
            padding: '6px 10px', fontSize: '12px', borderRadius: '6px',
            border: '0.5px solid var(--color-border-tertiary)',
            background: 'var(--color-background-secondary)',
            color: 'var(--color-text-primary)', outline: 'none',
          }}
        >
          <option value={1}>Last 24h</option>
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
        </select>

        <button
          onClick={fetchData}
          style={{
            padding: '6px 12px', fontSize: '12px', borderRadius: '6px',
            background: '#534AB7', color: '#fff', border: 'none', cursor: 'pointer',
          }}
        >
          Refresh
        </button>

        <span style={{ fontSize: '11px', color: 'var(--color-text-tertiary)', marginLeft: 'auto' }}>
          {entries.length} entries
        </span>
      </div>

      {/* Log table */}
      {loading ? (
        <p style={{ fontSize: '12px', color: 'var(--color-text-tertiary)' }}>Loading...</p>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{
            width: '100%', borderCollapse: 'collapse',
            fontSize: '11px',
          }}>
            <thead>
              <tr style={{ background: 'var(--color-background-secondary)' }}>
                {['Timestamp', 'User', 'Action', 'Workers', 'Tokens', 'Cost', 'Latency', 'Flags'].map(h => (
                  <th key={h} style={{
                    padding: '8px 10px', textAlign: 'left', fontWeight: 500,
                    color: 'var(--color-text-tertiary)',
                    borderBottom: '0.5px solid var(--color-border-tertiary)',
                  }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {entries.map(entry => (
                <tr
                  key={entry.id}
                  style={{
                    borderBottom: '0.5px solid var(--color-border-tertiary)',
                    background: entry.error
                      ? '#fff0f0'
                      : entry.guardrail_triggered
                      ? '#fffbeb'
                      : 'var(--color-background-primary)',
                  }}
                >
                  <td style={{ padding: '7px 10px', color: 'var(--color-text-tertiary)', whiteSpace: 'nowrap' }}>
                    {formatTs(entry.timestamp)}
                  </td>
                  <td style={{ padding: '7px 10px', fontFamily: 'var(--font-mono)' }}>
                    {entry.user_id?.slice(0, 12) || '—'}
                  </td>
                  <td style={{ padding: '7px 10px' }}>
                    <span style={{
                      padding: '2px 6px', borderRadius: '4px', fontSize: '10px',
                      background: 'var(--color-background-secondary)',
                    }}>
                      {entry.action}
                    </span>
                  </td>
                  <td style={{ padding: '7px 10px', color: 'var(--color-text-secondary)', maxWidth: '160px' }}>
                    {(entry.worker_agents || []).join(', ') || entry.tool_called || '—'}
                  </td>
                  <td style={{ padding: '7px 10px', color: 'var(--color-text-secondary)' }}>
                    {(entry.input_tokens + entry.output_tokens).toLocaleString()}
                  </td>
                  <td style={{ padding: '7px 10px', color: 'var(--color-text-secondary)' }}>
                    ${entry.cost_usd.toFixed(5)}
                  </td>
                  <td style={{ padding: '7px 10px', color: 'var(--color-text-secondary)' }}>
                    {entry.latency_ms}ms
                  </td>
                  <td style={{ padding: '7px 10px' }}>
                    <div style={{ display: 'flex', gap: '3px', flexWrap: 'wrap' }}>
                      {entry.guardrail_triggered && (
                        <span style={{ fontSize: '10px', padding: '1px 5px', borderRadius: '4px', background: '#fef3c7', color: '#92400e' }}>🛡️ guard</span>
                      )}
                      {entry.pii_detected && (
                        <span style={{ fontSize: '10px', padding: '1px 5px', borderRadius: '4px', background: '#dbeafe', color: '#1e40af' }}>🔒 PII</span>
                      )}
                      {entry.error && (
                        <span style={{ fontSize: '10px', padding: '1px 5px', borderRadius: '4px', background: '#fee2e2', color: '#991b1b' }}>✗ err</span>
                      )}
                      {entry.reflection_loops > 1 && (
                        <span style={{ fontSize: '10px', padding: '1px 5px', borderRadius: '4px', background: '#f3e8ff', color: '#7c3aed' }}>✦×{entry.reflection_loops}</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {entries.length === 0 && (
            <p style={{
              textAlign: 'center', padding: '24px',
              fontSize: '12px', color: 'var(--color-text-tertiary)',
            }}>
              No audit entries found
            </p>
          )}
        </div>
      )}
    </div>
  )
}