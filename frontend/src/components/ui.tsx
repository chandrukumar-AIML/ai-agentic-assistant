// frontend/src/components/ui.tsx — Shared UI primitives
import { ReactNode, useState } from 'react'

// ── Page Shell ────────────────────────────────────────────────────────────────
export function PageShell({ title, subtitle, icon, children }: {
  title: string; subtitle?: string; icon: string; children: ReactNode
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#0f1117', overflow: 'hidden' }}>
      <div style={{
        padding: '16px 24px', borderBottom: '1px solid #1e2535',
        background: '#161b27', flexShrink: 0,
        display: 'flex', alignItems: 'center', gap: 12,
      }}>
        <span style={{ fontSize: 22 }}>{icon}</span>
        <div>
          <div style={{ color: '#e2e8f0', fontSize: 16, fontWeight: 600 }}>{title}</div>
          {subtitle && <div style={{ color: '#4b5563', fontSize: 12, marginTop: 1 }}>{subtitle}</div>}
        </div>
      </div>
      <div style={{ flex: 1, overflow: 'auto', padding: '20px 24px' }}>
        {children}
      </div>
    </div>
  )
}

// ── Card ──────────────────────────────────────────────────────────────────────
export function Card({ children, style }: { children: ReactNode; style?: React.CSSProperties }) {
  return (
    <div style={{
      background: '#161b27', border: '1px solid #1e2535',
      borderRadius: 12, padding: 20, ...style,
    }}>{children}</div>
  )
}

// ── Button ────────────────────────────────────────────────────────────────────
export function Btn({ children, onClick, loading, variant = 'primary', disabled, style }: {
  children: ReactNode; onClick?: () => void; loading?: boolean;
  variant?: 'primary' | 'secondary' | 'danger' | 'success'; disabled?: boolean;
  style?: React.CSSProperties
}) {
  const bg = {
    primary:   loading || disabled ? '#3730a3' : '#10b981',
    secondary: '#1e2535',
    danger:    '#dc2626',
    success:   '#16a34a',
  }[variant]
  return (
    <button onClick={onClick} disabled={loading || disabled} style={{
      background: bg, color: variant === 'secondary' ? '#9ca3af' : '#fff',
      border: '1px solid ' + (variant === 'secondary' ? '#374151' : 'transparent'),
      padding: '8px 16px', borderRadius: 8, fontSize: 13, fontWeight: 500,
      cursor: loading || disabled ? 'not-allowed' : 'pointer',
      display: 'inline-flex', alignItems: 'center', gap: 6,
      transition: 'all 0.15s', ...style,
    }}>
      {loading && <span style={{ animation: 'spin 1s linear infinite', display: 'inline-block' }}>⏳</span>}
      {children}
    </button>
  )
}

// ── Input ─────────────────────────────────────────────────────────────────────
export function Input({ value, onChange, placeholder, label, type = 'text', rows }: {
  value: string; onChange: (v: string) => void; placeholder?: string;
  label?: string; type?: string; rows?: number
}) {
  const common = {
    width: '100%', background: '#0f1117', border: '1px solid #1e2535',
    borderRadius: 8, padding: '10px 12px', color: '#e2e8f0',
    fontSize: 13, outline: 'none', boxSizing: 'border-box' as const,
    fontFamily: 'inherit',
  }
  return (
    <div style={{ marginBottom: 14 }}>
      {label && <label style={{ display: 'block', fontSize: 12, color: '#9ca3af', marginBottom: 5, fontWeight: 500 }}>{label}</label>}
      {rows ? (
        <textarea rows={rows} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder} style={{ ...common, resize: 'vertical' }} />
      ) : (
        <input type={type} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder} style={common} />
      )}
    </div>
  )
}

// ── Select ────────────────────────────────────────────────────────────────────
export function Select({ value, onChange, options, label }: {
  value: string; onChange: (v: string) => void;
  options: { label: string; value: string }[]; label?: string
}) {
  return (
    <div style={{ marginBottom: 14 }}>
      {label && <label style={{ display: 'block', fontSize: 12, color: '#9ca3af', marginBottom: 5, fontWeight: 500 }}>{label}</label>}
      <select value={value} onChange={e => onChange(e.target.value)} style={{
        width: '100%', background: '#0f1117', border: '1px solid #1e2535',
        borderRadius: 8, padding: '10px 12px', color: '#e2e8f0', fontSize: 13,
        outline: 'none', boxSizing: 'border-box', cursor: 'pointer',
        fontFamily: 'inherit',
      }}>
        {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </div>
  )
}

// ── Result Box ────────────────────────────────────────────────────────────────
export function ResultBox({ data, loading, error, title }: {
  data?: any; loading?: boolean; error?: string; title?: string
}) {
  if (loading) return (
    <div style={{ background: '#0f1117', border: '1px solid #1e2535', borderRadius: 8, padding: 20, textAlign: 'center', color: '#6b7280' }}>
      <span style={{ fontSize: 24 }}>⏳</span>
      <p style={{ marginTop: 8, fontSize: 13 }}>Processing...</p>
    </div>
  )
  if (error) return (
    <div style={{ background: '#1a0a0a', border: '1px solid #7f1d1d', borderRadius: 8, padding: 16 }}>
      <span style={{ color: '#ef4444', fontSize: 12, fontWeight: 600 }}>⚠ Error</span>
      <p style={{ color: '#fca5a5', fontSize: 13, marginTop: 4 }}>{error}</p>
    </div>
  )
  if (!data) return null
  return (
    <div style={{ background: '#0a0f1a', border: '1px solid #1e3a5f', borderRadius: 8, overflow: 'hidden' }}>
      {title && (
        <div style={{ padding: '8px 14px', background: '#0d1b2e', borderBottom: '1px solid #1e3a5f' }}>
          <span style={{ color: '#60a5fa', fontSize: 11, fontWeight: 600 }}>{title}</span>
        </div>
      )}
      <pre style={{
        margin: 0, padding: 16, color: '#93c5fd',
        fontSize: 12, lineHeight: 1.6,
        overflowX: 'auto', maxHeight: 400, overflowY: 'auto',
        whiteSpace: 'pre-wrap', wordBreak: 'break-word',
        fontFamily: 'Monaco, Consolas, monospace',
      }}>
        {typeof data === 'string' ? data : JSON.stringify(data, null, 2)}
      </pre>
    </div>
  )
}

// ── Badge ─────────────────────────────────────────────────────────────────────
export function Badge({ text, color = 'blue' }: { text: string; color?: 'blue' | 'green' | 'red' | 'yellow' | 'purple' }) {
  const colors = {
    blue:   { bg: 'rgba(16,185,129,0.15)', color: '#5eead4' },
    green:  { bg: 'rgba(34,197,94,0.15)',  color: '#86efac' },
    red:    { bg: 'rgba(239,68,68,0.15)',   color: '#fca5a5' },
    yellow: { bg: 'rgba(234,179,8,0.15)',   color: '#fde047' },
    purple: { bg: 'rgba(168,85,247,0.15)',  color: '#d8b4fe' },
  }[color]
  return (
    <span style={{
      fontSize: 11, padding: '2px 8px', borderRadius: 20,
      background: colors.bg, color: colors.color, fontWeight: 600,
    }}>{text}</span>
  )
}

// ── Stat Card ─────────────────────────────────────────────────────────────────
export function StatCard({ label, value, icon, trend }: { label: string; value: string | number; icon: string; trend?: string }) {
  return (
    <div style={{
      background: '#161b27', border: '1px solid #1e2535', borderRadius: 12,
      padding: 20, display: 'flex', flexDirection: 'column', gap: 8,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <span style={{ fontSize: 24 }}>{icon}</span>
        {trend && <span style={{ fontSize: 11, color: '#22c55e' }}>{trend}</span>}
      </div>
      <div style={{ color: '#e2e8f0', fontSize: 22, fontWeight: 700 }}>{value}</div>
      <div style={{ color: '#6b7280', fontSize: 12 }}>{label}</div>
    </div>
  )
}

// ── Tabs ──────────────────────────────────────────────────────────────────────
export function Tabs({ tabs, active, onChange }: {
  tabs: { id: string; label: string; icon?: string }[]
  active: string; onChange: (id: string) => void
}) {
  return (
    <div style={{
      display: 'flex', gap: 2, background: '#0f1117',
      borderRadius: 10, padding: 4, marginBottom: 20, flexWrap: 'wrap',
    }}>
      {tabs.map(t => (
        <button key={t.id} onClick={() => onChange(t.id)} style={{
          padding: '7px 14px', borderRadius: 7, fontSize: 12, fontWeight: 500,
          border: 'none', cursor: 'pointer',
          background: active === t.id ? '#10b981' : 'none',
          color: active === t.id ? '#fff' : '#6b7280',
          display: 'flex', alignItems: 'center', gap: 5, transition: 'all 0.15s',
        }}>
          {t.icon && <span>{t.icon}</span>}
          {t.label}
        </button>
      ))}
    </div>
  )
}

// ── Two columns ───────────────────────────────────────────────────────────────
export function TwoCol({ children, gap = 20 }: { children: ReactNode; gap?: number }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap, alignItems: 'start' }}>
      {children}
    </div>
  )
}

// ── Section heading ───────────────────────────────────────────────────────────
export function SectionHead({ title, sub }: { title: string; sub?: string }) {
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ color: '#e2e8f0', fontSize: 14, fontWeight: 600 }}>{title}</div>
      {sub && <div style={{ color: '#6b7280', fontSize: 12, marginTop: 2 }}>{sub}</div>}
    </div>
  )
}

// useApiCall hook
export function useApi<T = any>() {
  const [data, setData] = useState<T | undefined>()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | undefined>()

  async function call(fn: () => Promise<T>) {
    setLoading(true); setError(undefined); setData(undefined)
    try {
      const result = await fn()
      setData(result)
    } catch (e: any) {
      setError(e.message || 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  return { data, loading, error, call }
}
