// frontend/src/components/KeyboardShortcutsModal.tsx
import React, { useEffect, useState } from 'react'

const SHORTCUTS = [
  { key: '⌘K',     description: 'Focus input' },
  { key: '⌘/',     description: 'Open keyboard shortcuts' },
  { key: '⌘⇧C',   description: 'Clear conversation' },
  { key: '⌘⇧M',   description: 'Toggle memory panel' },
  { key: '⌘⇧V',   description: 'Toggle voice mode' },
  { key: '⌘⇧E',   description: 'Export conversation' },
  { key: 'Esc',    description: 'Close panels / cancel' },
  { key: 'Enter',  description: 'Send message' },
  { key: '⇧Enter', description: 'New line in message' },
]

interface Props {
  isOpen:  boolean
  onClose: () => void
}

export default function KeyboardShortcutsModal({ isOpen, onClose }: Props) {
  if (!isOpen) return null

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 200,
      background: 'rgba(0,0,0,0.4)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
    }}
      onClick={onClose}
    >
      <div
        style={{
          background: 'var(--color-background-primary)',
          borderRadius: '16px', padding: '24px',
          width: '380px', maxWidth: '90vw',
          border: '0.5px solid var(--color-border-tertiary)',
          boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
        }}
        onClick={e => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
          <p style={{ fontSize: '14px', fontWeight: 500, margin: 0,
                      color: 'var(--color-text-primary)' }}>
            Keyboard Shortcuts
          </p>
          <button onClick={onClose}
            style={{ background: 'none', border: 'none', cursor: 'pointer',
                     fontSize: '18px', color: 'var(--color-text-tertiary)' }}>
            ×
          </button>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {SHORTCUTS.map(s => (
            <div key={s.key} style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '7px 10px', borderRadius: '8px',
              background: 'var(--color-background-secondary)',
            }}>
              <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                {s.description}
              </span>
              <kbd style={{
                fontSize: '11px', padding: '2px 8px', borderRadius: '5px',
                background: 'var(--color-background-primary)',
                border: '0.5px solid var(--color-border-tertiary)',
                fontFamily: 'var(--font-mono)',
                color: 'var(--color-text-primary)',
              }}>
                {s.key}
              </kbd>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}