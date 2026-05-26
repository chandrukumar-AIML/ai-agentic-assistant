// frontend/src/components/admin/ABTestDashboard.tsx
import React, { useState, useEffect, useCallback } from 'react'

interface ABTestStats {
  test_id:          number
  test_name:        string
  prompt_name:      string
  status:           string
  winner_id:        number | null
  min_queries:      number
  total_queries:    number
  completion_pct:   number
  variant_a: {
    variant:        string
    variant_id:     number
    total_served:   number
    total_rated:    number
    avg_score:      number
    thumbs_up:      number
    thumbs_down:    number
  }
  variant_b: {
    variant:        string
    variant_id:     number
    total_served:   number
    total_rated:    number
    avg_score:      number
    thumbs_up:      number
    thumbs_down:    number
  }
}

const API_BASE  = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
const authHeader = () => ({ Authorization: `Bearer ${sessionStorage.getItem('aaa_token') || 'dev'}` })

function ScoreBar({ a, b, label }: { a: number; b: number; label: string }) {
  const total = a + b || 1
  const pctA  = (a / total) * 100
  return (
    <div style={{ marginBottom: '8px' }}>
      <div style={{
        display: 'flex', justifyContent: 'space-between',
        fontSize: '11px', color: 'var(--color-text-tertiary)', marginBottom: '3px',
      }}>
        <span>Variant A</span>
        <span style={{ fontWeight: 500 }}>{label}</span>
        <span>Variant B</span>
      </div>
      <div style={{ display: 'flex', height: '8px', borderRadius: '4px', overflow: 'hidden' }}>
        <div style={{ width: `${pctA}%`, background: '#534AB7' }} />
        <div style={{ width: `${100 - pctA}%`, background: '#e24b4a' }} />
      </div>
      <div style={{
        display: 'flex', justifyContent: 'space-between',
        fontSize: '10px', color: 'var(--color-text-secondary)', marginTop: '2px',
      }}>
        <span>{(a * 100).toFixed(1)}%</span>
        <span>{(b * 100).toFixed(1)}%</span>
      </div>
    </div>
  )
}

export default function ABTestDashboard() {
  const [tests,   setTests]   = useState<ABTestStats[]>([])
  const [loading, setLoading] = useState(true)
  const [filter,  setFilter]  = useState<'all' | 'running' | 'completed'>('all')

  const fetchTests = useCallback(async () => {
    setLoading(true)
    try {
      const url = filter === 'all'
        ? `${API_BASE}/prompts/ab-tests`
        : `${API_BASE}/prompts/ab-tests?status=${filter}`
      const res  = await fetch(url, { headers: authHeader() })
      const data = await res.json()
      setTests(data.tests || [])
    } catch (e) {
      void e // FIXED: removed console.error production log
    } finally {
      setLoading(false)
    }
  }, [filter])

  useEffect(() => { fetchTests() }, [fetchTests])
  useEffect(() => {
    const interval = setInterval(fetchTests, 10_000)  // refresh every 10s
    return () => clearInterval(interval)
  }, [fetchTests])

  const handlePause = async (testId: number) => {
    await fetch(`${API_BASE}/prompts/ab-test/${testId}/pause`, {
      method: 'POST', headers: authHeader()
    }).catch(() => {}) // FIXED: unhandled Promise rejection — added .catch()
    fetchTests().catch(() => {}) // FIXED: fetchTests() was called without await or .catch()
  }

  return (
    <div style={{ padding: '20px', maxWidth: '900px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <h3 style={{ fontSize: '14px', fontWeight: 500, color: 'var(--color-text-primary)', margin: 0 }}>
          A/B Tests
        </h3>
        <div style={{ display: 'flex', gap: '4px' }}>
          {(['all', 'running', 'completed'] as const).map(f => (
            <button key={f} onClick={() => setFilter(f)}
              style={{
                padding: '4px 10px', fontSize: '11px', borderRadius: '20px',
                background: filter === f ? '#534AB7' : 'var(--color-background-secondary)',
                color: filter === f ? '#fff' : 'var(--color-text-secondary)',
                border: `0.5px solid ${filter === f ? '#534AB7' : 'var(--color-border-tertiary)'}`,
                cursor: 'pointer', fontWeight: filter === f ? 500 : 400,
                textTransform: 'capitalize',
              }}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <p style={{ fontSize: '12px', color: 'var(--color-text-tertiary)' }}>Loading tests...</p>
      ) : tests.length === 0 ? (
        <div style={{
          padding: '24px', textAlign: 'center',
          background: 'var(--color-background-secondary)',
          borderRadius: '12px', border: '0.5px solid var(--color-border-tertiary)',
        }}>
          <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)' }}>
            No A/B tests yet
          </p>
          <p style={{ fontSize: '11px', color: 'var(--color-text-tertiary)', marginTop: '4px' }}>
            Create two prompt versions, then start a test via POST /api/prompts/ab-test
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {tests.map(test => (
            <div key={test.test_id} style={{
              padding: '16px',
              background: 'var(--color-background-primary)',
              borderRadius: '12px',
              border: '0.5px solid var(--color-border-tertiary)',
            }}>
              {/* Header */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                <div style={{ flex: 1 }}>
                  <p style={{ fontSize: '13px', fontWeight: 500, margin: 0, color: 'var(--color-text-primary)' }}>
                    {test.test_name}
                  </p>
                  <p style={{ fontSize: '11px', color: 'var(--color-text-tertiary)', margin: '2px 0 0' }}>
                    Prompt: {test.prompt_name} ·
                    {test.total_queries} queries ·
                    {test.completion_pct}% to auto-promote
                  </p>
                </div>
                <span style={{
                  padding: '3px 8px', borderRadius: '20px', fontSize: '11px', fontWeight: 500,
                  background: test.status === 'running'   ? '#c8f0dc' :
                              test.status === 'completed' ? '#c0d4f8' : '#ffe0a0',
                  color:      test.status === 'running'   ? '#1a6b4a' :
                              test.status === 'completed' ? '#1a3a8f' : '#7a4a00',
                }}>
                  {test.status.toUpperCase()}
                </span>
                {test.status === 'running' && (
                  <button onClick={() => handlePause(test.test_id)}
                    style={{
                      padding: '4px 10px', fontSize: '11px',
                      background: 'var(--color-background-secondary)',
                      border: '0.5px solid var(--color-border-tertiary)',
                      borderRadius: '6px', cursor: 'pointer',
                      color: 'var(--color-text-secondary)',
                    }}
                  >
                    Pause
                  </button>
                )}
              </div>

              {/* Score comparison */}
              <ScoreBar
                a={test.variant_a.avg_score}
                b={test.variant_b.avg_score}
                label="Avg Score"
              />

              {/* Variant details */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginTop: '10px' }}>
                {[test.variant_a, test.variant_b].map(v => (
                  <div key={v.variant} style={{
                    padding: '10px 12px',
                    background: 'var(--color-background-secondary)',
                    borderRadius: '8px',
                    border: `0.5px solid ${
                      test.winner_id === v.variant_id ? '#534AB7' : 'var(--color-border-tertiary)'
                    }`,
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
                      <span style={{
                        fontSize: '11px', fontWeight: 500,
                        padding: '2px 8px', borderRadius: '20px',
                        background: v.variant === 'A' ? '#534AB7' : '#e24b4a',
                        color: '#fff',
                      }}>
                        Variant {v.variant}
                      </span>
                      {test.winner_id === v.variant_id && (
                        <span style={{
                          fontSize: '10px', color: '#534AB7', fontWeight: 500,
                        }}>
                          🏆 Winner
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>
                      <div>Score: <strong>{(v.avg_score * 100).toFixed(1)}%</strong></div>
                      <div>Served: {v.total_served} · Rated: {v.total_rated}</div>
                      <div>👍 {v.thumbs_up} · 👎 {v.thumbs_down}</div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Progress bar */}
              <div style={{ marginTop: '10px' }}>
                <div style={{
                  display: 'flex', justifyContent: 'space-between',
                  fontSize: '10px', color: 'var(--color-text-tertiary)', marginBottom: '3px',
                }}>
                  <span>Progress to auto-promote</span>
                  <span>{test.completion_pct}%</span>
                </div>
                <div style={{
                  height: '4px', borderRadius: '2px',
                  background: 'var(--color-border-tertiary)', overflow: 'hidden',
                }}>
                  <div style={{
                    width: `${test.completion_pct}%`, height: '100%',
                    background: test.completion_pct === 100 ? '#22c55e' : '#534AB7',
                    transition: 'width 0.5s',
                  }} />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}