// frontend/src/components/ExportMenu.tsx
import React, { useState, useCallback } from 'react'
import { Message } from '../types'

interface Props {
  messages: Message[]
}

function messagestoMarkdown(messages: Message[]): string {
  const lines = ['# Conversation Export\n', `*Exported: ${new Date().toLocaleString()}*\n`]
  for (const msg of messages) {
    const role = msg.role === 'human' ? '**You**' : '**Assistant**'
    const time = new Date(msg.timestamp).toLocaleTimeString()
    lines.push(`\n---\n\n${role} *(${time})*\n\n${msg.content}`)
    if (msg.sources && msg.sources.length > 0) {
      lines.push('\n\n**Sources:**')
      msg.sources.forEach((s, i) => lines.push(`${i+1}. ${s}`))
    }
    if (msg.reflectionScore) {
      lines.push(`\n*Quality: ${msg.reflectionScore.toFixed(1)}/10*`)
    }
  }
  return lines.join('\n')
}

export default function ExportMenu({ messages }: Props) {
  const [isOpen, setIsOpen] = useState(false)

  const exportMarkdown = useCallback(() => {
    const md   = messagestoMarkdown(messages)
    const blob = new Blob([md], { type: 'text/markdown' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = `conversation-${Date.now()}.md`
    a.click()
    URL.revokeObjectURL(url)
    setIsOpen(false)
  }, [messages])

  const exportJSON = useCallback(() => {
    const json = JSON.stringify(messages.map(m => ({
      role:      m.role,
      content:   m.content,
      timestamp: m.timestamp,
      sources:   m.sources,
      model:     m.model,
      reflection_score: m.reflectionScore,
      workers:   m.workersUsed?.map(w => w.name),
    })), null, 2)
    const blob = new Blob([json], { type: 'application/json' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = `conversation-${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
    setIsOpen(false)
  }, [messages])

  if (messages.length === 0) return null

  return (
    <div style={{ position: 'relative' }}>
      <button
        onClick={() => setIsOpen(o => !o)}
        title="Export conversation"
        style={{
          background: 'none', border: 'none', cursor: 'pointer',
          padding: '5px', borderRadius: '6px', fontSize: '14px',
          color: 'var(--color-text-tertiary)',
          display: 'flex', alignItems: 'center',
        }}
      >
        ↓
      </button>

      {isOpen && (
        <div style={{
          position: 'absolute', right: 0, top: '100%', marginTop: '4px',
          background: 'var(--color-background-primary)',
          border: '0.5px solid var(--color-border-tertiary)',
          borderRadius: '8px', overflow: 'hidden',
          zIndex: 50, minWidth: '160px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
        }}>
          {[
            { label: '📝 Export Markdown', action: exportMarkdown },
            { label: '{ } Export JSON',    action: exportJSON },
          ].map(item => (
            <button
              key={item.label}
              onClick={item.action}
              style={{
                display: 'block', width: '100%', padding: '9px 14px',
                textAlign: 'left', background: 'none', border: 'none',
                cursor: 'pointer', fontSize: '12px',
                color: 'var(--color-text-secondary)',
                borderBottom: '0.5px solid var(--color-border-tertiary)',
              }}
              onMouseEnter={e => (e.currentTarget.style.background = 'var(--color-background-secondary)')}
              onMouseLeave={e => (e.currentTarget.style.background = 'none')}
            >
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}