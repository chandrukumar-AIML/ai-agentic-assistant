// frontend/src/components/AgentStatusBar.tsx
// Shows which agent is active during streaming
import React from 'react'

interface ActiveAgent {
  name:   string
  status: 'running' | 'done' | 'failed'
}

interface Props {
  agents:    ActiveAgent[]
  isVisible: boolean
}

const AGENT_CONFIG: Record<string, { icon: string; color: string; bg: string }> = {
  supervisor:      { icon: '🎯', color: '#534AB7', bg: '#EEEDFE' },
  research_agent:  { icon: '🔍', color: '#1a3a8f', bg: '#c0d4f8' },
  code_agent:      { icon: '💻', color: '#1a6b4a', bg: '#c8f0dc' },
  vision_agent:    { icon: '👁️', color: '#600070', bg: '#e8c0f8' },
  memory_agent:    { icon: '🧠', color: '#7a4a00', bg: '#ffe0a0' },
  planning_agent:  { icon: '📋', color: '#2a5200', bg: '#c4e8a0' },
  aggregator:      { icon: '⚡', color: '#004a70', bg: '#b8e4f8' },
  reflection_node: { icon: '✦',  color: '#4a1a00', bg: '#f8d0b0' },
}

export default function AgentStatusBar({ agents, isVisible }: Props) {
  if (!isVisible || agents.length === 0) return null

  return (
    <div style={{
      padding: '8px 16px',
      borderBottom: '0.5px solid var(--color-border-tertiary)',
      background: 'var(--color-background-secondary)',
      display: 'flex', alignItems: 'center', gap: '6px',
      flexWrap: 'wrap',
      fontSize: '11px',
    }}>
      <span style={{ color: 'var(--color-text-tertiary)', marginRight: '4px' }}>
        Active:
      </span>
      {agents.map((agent) => { // FIXED: replaced index key with agent.name for stable identity
        const cfg = AGENT_CONFIG[agent.name] || { icon: '🤖', color: '#666', bg: '#eee' }
        return (
          <span key={agent.name} style={{
            display: 'inline-flex', alignItems: 'center', gap: '4px',
            padding: '3px 8px', borderRadius: '20px',
            background: cfg.bg, color: cfg.color,
            fontWeight: 500,
            opacity: agent.status === 'done' ? 0.5 : 1,
          }}>
            <span>{cfg.icon}</span>
            <span style={{ textTransform: 'capitalize' }}>
              {agent.name.replace('_agent', '').replace('_', ' ')}
            </span>
            {agent.status === 'running' && (
              <span style={{
                width: '6px', height: '6px', borderRadius: '50%',
                background: cfg.color, opacity: 0.7,
                animation: 'pulse 1s infinite',
              }} />
            )}
            {agent.status === 'done'   && <span>✓</span>}
            {agent.status === 'failed' && <span>✗</span>}
          </span>
        )
      })}
    </div>
  )
}