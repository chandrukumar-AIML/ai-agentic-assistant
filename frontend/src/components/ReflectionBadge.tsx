// frontend/src/components/ReflectionBadge.tsx
import React, { useState } from 'react'
import { ReflectionEntry } from '../types'

interface Props {
  score:    number
  attempts: number
  history:  ReflectionEntry[]
}

function ScoreBar({ score }: { score: number }) {
  const pct   = (score / 10) * 100
  const color = score >= 8 ? '#22c55e' : score >= 6 ? '#eab308' : '#ef4444'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
      <div style={{
        flex: 1, height: '4px',
        background: 'var(--color-border-tertiary)',
        borderRadius: '2px', overflow: 'hidden',
      }}>
        <div style={{
          width: `${pct}%`, height: '100%',
          background: color, borderRadius: '2px',
          transition: 'width 0.3s',
        }} />
      </div>
      <span style={{ fontSize: '11px', fontWeight: 500, color, minWidth: '28px' }}>
        {score}/10
      </span>
    </div>
  )
}

export default function ReflectionBadge({ score, attempts, history }: Props) {
  const [open, setOpen] = useState(false)

  if (!score && !attempts) return null

  const color = score >= 8 ? '#22c55e' : score >= 6 ? '#eab308' : '#ef4444'
  const bg    = score >= 8 ? '#f0fdf4' : score >= 6 ? '#fefce8' : '#fef2f2'

  return (
    <div style={{ marginTop: '6px' }}>
      {/* Badge trigger */}
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          display: 'inline-flex', alignItems: 'center', gap: '5px',
          padding: '3px 8px', borderRadius: '20px',
          background: bg,
          border: `0.5px solid ${color}40`,
          cursor: 'pointer', fontSize: '11px',
          color, fontWeight: 500,
        }}
      >
        <span>✦</span>
        <span>Quality {score.toFixed(1)}/10</span>
        {attempts > 1 && (
          <span style={{ opacity: 0.7 }}>· {attempts} loops</span>
        )}
        <span style={{ opacity: 0.6, fontSize: '10px' }}>{open ? '▲' : '▼'}</span>
      </button>

      {/* Expanded reflection history */}
      {open && (
        <div style={{
          marginTop: '6px',
          border: '0.5px solid var(--color-border-tertiary)',
          borderRadius: '8px', overflow: 'hidden',
          background: 'var(--color-background-primary)',
        }}>
          {history.map((entry, i) => (
            <div key={i} style={{
              padding: '10px 12px',
              borderBottom: i < history.length - 1
                ? '0.5px solid var(--color-border-tertiary)'
                : 'none',
            }}>
              {/* Loop header */}
              <div style={{
                display: 'flex', alignItems: 'center',
                justifyContent: 'space-between', marginBottom: '6px',
              }}>
                <span style={{ fontSize: '11px', fontWeight: 500, color: 'var(--color-text-primary)' }}>
                  Loop {entry.attempt}
                </span>
                <span style={{
                  fontSize: '10px', padding: '2px 7px', borderRadius: '20px',
                  background: entry.verdict === 'pass' ? '#f0fdf4' : '#fef2f2',
                  color: entry.verdict === 'pass' ? '#22c55e' : '#ef4444',
                  fontWeight: 500,
                }}>
                  {entry.verdict === 'pass' ? '✓ Accepted' : '✗ Rewriting'}
                </span>
              </div>

              {/* Score bar */}
              <ScoreBar score={entry.score} />

              {/* Critique */}
              {entry.critique && entry.critique !== 'None' && (
                <div style={{ marginTop: '8px' }}>
                  <p style={{ fontSize: '10px', fontWeight: 500, color: 'var(--color-text-tertiary)', marginBottom: '3px' }}>
                    CRITIQUE
                  </p>
                  <p style={{ fontSize: '11px', color: 'var(--color-text-secondary)', lineHeight: 1.5, margin: 0 }}>
                    {entry.critique}
                  </p>
                </div>
              )}

              {/* Missing items */}
              {entry.missing.length > 0 && (
                <div style={{ marginTop: '8px' }}>
                  <p style={{ fontSize: '10px', fontWeight: 500, color: 'var(--color-text-tertiary)', marginBottom: '3px' }}>
                    NOT ADDRESSED
                  </p>
                  {entry.missing.map((m, j) => (
                    <p key={j} style={{ fontSize: '11px', color: 'var(--color-text-secondary)', margin: '2px 0' }}>
                      · {m}
                    </p>
                  ))}
                </div>
              )}

              {/* Hallucinations */}
              {entry.hallucinations.length > 0 && (
                <div style={{ marginTop: '8px' }}>
                  <p style={{ fontSize: '10px', fontWeight: 500, color: '#a32d2d', marginBottom: '3px' }}>
                    UNSUPPORTED CLAIMS
                  </p>
                  {entry.hallucinations.map((h, j) => (
                    <p key={j} style={{ fontSize: '11px', color: '#a32d2d', margin: '2px 0' }}>
                      · {h}
                    </p>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}