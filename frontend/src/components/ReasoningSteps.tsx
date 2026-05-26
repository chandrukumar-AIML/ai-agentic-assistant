// frontend/src/components/ReasoningSteps.tsx
import React, { useState } from 'react'
import { AgentStep } from '../types'

interface Props {
  steps:       AgentStep[]
  isStreaming: boolean
}

const STEP_CONFIG: Record<string, { icon: string; color: string; label: string }> = {
  guardrail_check:  { icon: '🛡️', color: '#1a6b4a', label: 'Safety check' },
  memory_load:      { icon: '🧠', color: '#534AB7', label: 'Loading memory' },
  supervisor:       { icon: '🎯', color: '#534AB7', label: 'Supervisor routing' },
  routing_decision: { icon: '→',  color: '#185FA5', label: 'Route decided' },
  worker_complete:  { icon: '✓',  color: '#1a6b4a', label: 'Worker complete' },
  reflection:       { icon: '✦',  color: '#7a4a00', label: 'Reflection' },
  rewrite:          { icon: '↺',  color: '#a32d2d', label: 'Rewriting' },
  output_check:     { icon: '🛡️', color: '#1a6b4a', label: 'Output verified' },
  tool_call:        { icon: '⚙️', color: '#185FA5', label: 'Tool call' },
  tool_result:      { icon: '📄', color: '#1a6b4a', label: 'Tool result' },
}

function StepRow({ step, isLast }: { step: AgentStep; isLast: boolean }) {
  const cfg   = STEP_CONFIG[step.step] || { icon: '·', color: '#9ca3af', label: step.step }
  const isErr = Boolean(step.metadata?.error) // FIXED: metadata is now `unknown`, Boolean() ensures boolean type

  return (
    <div style={{ display: 'flex', gap: '8px', paddingBottom: isLast ? 0 : '6px' }}>
      {/* Timeline dot + line */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
        <div style={{
          width: '20px', height: '20px', borderRadius: '50%',
          background: isErr ? '#fef2f2' : '#f8f7ff',
          border: `1.5px solid ${isErr ? '#fca5a5' : cfg.color}40`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '11px',
        }}>
          {cfg.icon}
        </div>
        {!isLast && (
          <div style={{
            width: '1px', flex: 1, minHeight: '12px',
            background: 'var(--color-border-tertiary)', marginTop: '3px',
          }} />
        )}
      </div>

      {/* Content */}
      <div style={{ flex: 1, paddingBottom: isLast ? 0 : '6px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{
            fontSize: '10px', fontWeight: 500,
            color: isErr ? '#dc2626' : cfg.color,
            textTransform: 'uppercase', letterSpacing: '0.05em',
          }}>
            {cfg.label}
          </span>
          {/* Worker badge */}
          {Boolean(step.metadata?.worker) && (
            <span style={{
              fontSize: '10px', padding: '1px 6px', borderRadius: '20px',
              background: '#EEEDFE', color: '#534AB7', fontWeight: 500,
            }}>
              {String(step.metadata!.worker).replace('_agent', '').replace('_', ' ')}
            </span>
          )}
          {/* Score badge for reflection */}
          {step.metadata?.score !== undefined && (
            <span style={{
              fontSize: '10px', padding: '1px 6px', borderRadius: '20px',
              background: step.metadata.verdict === 'pass' ? '#c8f0dc' : '#fef3c7', // FIXED: unknown comparison is safe at runtime
              color:      step.metadata.verdict === 'pass' ? '#1a6b4a'  : '#92400e',
              fontWeight: 500,
            }}>
              {Number(step.metadata.score).toFixed(1)}/10 {/* FIXED: Number() cast for unknown type */}
            </span>
          )}
        </div>
        <p style={{
          fontSize: '11px', margin: '2px 0 0',
          color: 'var(--color-text-tertiary)', lineHeight: 1.4,
        }}>
          {step.description}
        </p>
        {Boolean(step.metadata?.critique) && (
          <p style={{
            fontSize: '10px', margin: '3px 0 0',
            color: '#92400e', lineHeight: 1.4,
            fontStyle: 'italic',
          }}>
            "{String(step.metadata!.critique)}"
          </p>
        )}
      </div>
    </div>
  )
}

export default function ReasoningSteps({ steps, isStreaming }: Props) {
  const [isOpen, setIsOpen] = useState(false)

  if (steps.length === 0 && !isStreaming) return null

  return (
    <div style={{ marginBottom: '6px' }}>
      <button
        onClick={() => setIsOpen(o => !o)}
        style={{
          display: 'flex', alignItems: 'center', gap: '5px',
          background: 'none', border: 'none', cursor: 'pointer',
          padding: '3px 0', fontSize: '11px',
          color: 'var(--color-text-tertiary)',
        }}
      >
        <span style={{
          fontSize: '10px',
          animation: isStreaming ? 'spin 1s linear infinite' : 'none',
          display: 'inline-block',
        }}>
          {isStreaming ? '⟳' : '▸'}
        </span>
        <span>
          {isStreaming
            ? `Thinking... (${steps.length} steps)`
            : `${steps.length} reasoning steps`}
        </span>
        {!isStreaming && (
          <span>{isOpen ? '▲' : '▼'}</span>
        )}
      </button>

      {(isOpen || isStreaming) && steps.length > 0 && (
        <div style={{
          marginTop: '6px',
          padding: '10px 12px',
          background: 'var(--color-background-secondary)',
          borderRadius: '8px',
          border: '0.5px solid var(--color-border-tertiary)',
        }}>
          {steps.map((step, i) => (
            <StepRow key={i} step={step} isLast={i === steps.length - 1} />
          ))}
          {isStreaming && (
            <div style={{ display: 'flex', gap: '4px', marginTop: '8px', paddingLeft: '28px' }}>
              {[0,1,2].map(i => (
                <span key={i} style={{
                  width: '5px', height: '5px', borderRadius: '50%',
                  background: 'var(--color-text-tertiary)',
                  animation: 'bounce 1s infinite',
                  animationDelay: `${i * 150}ms`,
                  display: 'inline-block',
                }} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}