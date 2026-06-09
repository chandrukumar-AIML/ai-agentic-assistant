// frontend/src/components/WorkerStatusBar.tsx
import React from 'react'
import { WorkerSummary } from '../types'

interface Props {
  workers:    WorkerSummary[]
  isStreaming: boolean
  activeStep?: string   // from last agent_step event
}

const WORKER_COLORS: Record<string, { bg: string; text: string; icon: string }> = {
  research_agent: { bg: '#c0d4f8', text: '#1a3a8f', icon: '🔍' },
  code_agent:     { bg: '#c8f0dc', text: '#1a6b4a', icon: '💻' },
  vision_agent:   { bg: '#e8c0f8', text: '#600070', icon: '👁️' },
  memory_agent:   { bg: '#ffe0a0', text: '#7a4a00', icon: '🧠' },
  planning_agent: { bg: '#c4e8a0', text: '#2a5200', icon: '📋' },
}

export default function WorkerStatusBar({ workers, isStreaming, activeStep: _activeStep }: Props) {
  if (workers.length === 0 && !isStreaming) return null

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: '5px',
      flexWrap: 'wrap', margin: '4px 0',
    }}>
      {workers.map((w) => { // FIXED: replaced index key with w.name for stable identity
        const cfg = WORKER_COLORS[w.name] || { bg: '#f3f4f6', text: '#374151', icon: '🤖' }
        const label = w.name.replace('_agent', '').replace('_', ' ')
        return (
          <span key={w.name} style={{
            display: 'inline-flex', alignItems: 'center', gap: '3px',
            padding: '3px 8px', borderRadius: '20px',
            background: cfg.bg, color: cfg.text,
            fontSize: '11px', fontWeight: 500,
            opacity: isStreaming ? 0.7 : 1,
          }}>
            <span>{cfg.icon}</span>
            <span style={{ textTransform: 'capitalize' }}>{label}</span>
            {!isStreaming && (
              <>
                <span style={{ opacity: 0.6, fontSize: '10px' }}>
                  {w.confidence ? ` ${(w.confidence * 100).toFixed(0)}%` : ''}
                </span>
                <span style={{
                  fontSize: '10px', marginLeft: '2px',
                  color: '#22c55e',
                }}>
                  ✓
                </span>
              </>
            )}
            {isStreaming && (
              <span style={{
                width: '5px', height: '5px', borderRadius: '50%',
                background: cfg.text,
                animation: 'pulse 1s infinite',
                display: 'inline-block',
              }} />
            )}
          </span>
        )
      })}
    </div>
  )
}