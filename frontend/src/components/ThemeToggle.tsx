import { useEffect, useState } from 'react'

type Theme = 'light' | 'dark' | 'system'

export default function ThemeToggle() {
  const [theme, setThemeState] = useState<Theme>(() =>
    (localStorage.getItem('aaa_theme') as Theme) || 'system'
  )

  useEffect(() => {
    const root = document.documentElement
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    if (theme === 'dark' || (theme === 'system' && prefersDark)) {
      root.setAttribute('data-theme', 'dark')
    } else {
      root.setAttribute('data-theme', 'light')
    }
    localStorage.setItem('aaa_theme', theme)
  }, [theme])

  const cycle = () => {
    const order: Theme[] = ['light', 'dark', 'system']
    setThemeState(prev => order[(order.indexOf(prev) + 1) % order.length])
  }

  const icon = theme === 'light' ? '☀️' : theme === 'dark' ? '🌙' : '⚙️'

  return (
    <button
      onClick={cycle}
      title={`Theme: ${theme} (click to cycle)`}
      style={{
        background: 'none', border: 'none', cursor: 'pointer',
        fontSize: '14px', padding: '4px', borderRadius: '6px',
        color: 'var(--text-2)',
      }}
    >
      {icon}
    </button>
  )
}
