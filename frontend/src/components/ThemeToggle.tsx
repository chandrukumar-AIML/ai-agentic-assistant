// frontend/src/components/ThemeToggle.tsx
import React, { useEffect } from 'react'
import { useChatStore } from '../store/chatStore'
import { Theme }        from '../types'

export default function ThemeToggle() {
  const theme    = useChatStore(s => s.theme)
  const setTheme = useChatStore(s => s.setTheme)

  useEffect(() => {
    const root       = document.documentElement
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches

    if (theme === 'dark' || (theme === 'system' && prefersDark)) {
      root.setAttribute('data-theme', 'dark')
    } else {
      root.setAttribute('data-theme', 'light')
    }
  }, [theme])

  const cycle = () => {
    const order: Theme[] = ['light', 'dark', 'system']
    const next = order[(order.indexOf(theme) + 1) % order.length]
    setTheme(next)
  }

  const icon = theme === 'light' ? '☀️' : theme === 'dark' ? '🌙' : '⚙️'

  return (
    <button
      onClick={cycle}
      title={`Theme: ${theme} (click to cycle)`}
      style={{
        background: 'none', border: 'none', cursor: 'pointer',
        fontSize: '14px', padding: '4px', borderRadius: '6px',
        color: 'var(--color-text-tertiary)',
      }}
    >
      {icon}
    </button>
  )
}