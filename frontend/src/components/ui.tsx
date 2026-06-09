// frontend/src/components/ui.tsx — Shared UI primitives
import { Fragment, ReactNode, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

// ── Page Shell ────────────────────────────────────────────────────────────────
export function PageShell({ title, subtitle, icon, children }: {
  title: string; subtitle?: string; icon: string; children: ReactNode
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#0f1117', overflow: 'hidden' }}>
      <div className="aaa-page-head" style={{
        borderBottom: '1px solid #1e2535',
        background: '#161b27', flexShrink: 0,
        display: 'flex', alignItems: 'center', gap: 12,
      }}>
        <span style={{ fontSize: 22 }}>{icon}</span>
        <div>
          <div style={{ color: '#e2e8f0', fontSize: 16, fontWeight: 600 }}>{title}</div>
          {subtitle && <div style={{ color: '#4b5563', fontSize: 12, marginTop: 1 }}>{subtitle}</div>}
        </div>
      </div>
      <div className="aaa-page-body" style={{ flex: 1, overflow: 'auto' }}>
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
      <div style={{ padding: 16, maxHeight: 460, overflowY: 'auto', overflowX: 'auto' }}>
        {renderResult(data)}
      </div>
    </div>
  )
}

// Smart renderer: markdown for text, a table for arrays of records, a clean
// key/value list for flat objects, and JSON only as a last resort.
function renderResult(data: any): ReactNode {
  if (typeof data === 'string') return <Markdown text={data} />

  if (Array.isArray(data)) {
    if (data.length && typeof data[0] === 'object') return <DataTable rows={data} />
    return <Markdown text={data.map(String).join('\n')} />
  }

  if (data && typeof data === 'object') {
    const keys = Object.keys(data)
    // 1) single string field (e.g. { result: "## markdown ..." }) → render markdown
    if (keys.length === 1 && typeof data[keys[0]] === 'string') return <Markdown text={data[keys[0]]} />
    // 2) any field that is an array of records → table (+ scalar fields as context)
    const arrKey = keys.find(k => Array.isArray(data[k]) && data[k].length && typeof data[k][0] === 'object')
    if (arrKey) {
      const meta = keys.filter(k => k !== arrKey && typeof data[k] !== 'object')
      return (
        <div>
          {meta.length > 0 && (
            <div style={{ marginBottom: 10, fontSize: 12, color: '#9ca3af' }}>
              {meta.map(k => <span key={k} style={{ marginRight: 14 }}><b style={{ color: '#e2e8f0' }}>{prettyKey(k)}:</b> {String(data[k])}</span>)}
            </div>
          )}
          <DataTable rows={data[arrKey]} />
        </div>
      )
    }
    // 3) a longer markdown field mixed with scalars → render the longest string as markdown
    const strKeys = keys.filter(k => typeof data[k] === 'string')
    const longest = strKeys.sort((a, b) => (data[b].length - data[a].length))[0]
    if (longest && data[longest].length > 60) return <Markdown text={data[longest]} />
    // 4) flat scalar object → key/value list
    if (keys.every(k => typeof data[k] !== 'object')) return <KeyValueList obj={data} />
  }

  return (
    <pre style={{ margin: 0, color: '#93c5fd', fontSize: 12, lineHeight: 1.6, whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontFamily: 'Monaco, Consolas, monospace' }}>
      {JSON.stringify(data, null, 2)}
    </pre>
  )
}

function prettyKey(k: string): string {
  return k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function Markdown({ text }: { text: string }) {
  return (
    <div style={{ color: '#dbeafe', fontSize: 13.5, lineHeight: 1.65 }} className="aaa-md">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          table: ({ node: _node, ...p }) => <table style={{ borderCollapse: 'collapse', width: '100%', margin: '8px 0', fontSize: 12.5 }} {...p} />,
          th:    ({ node: _node, ...p }) => <th style={{ border: '1px solid #1e3a5f', padding: '6px 10px', background: '#0d1b2e', color: '#93c5fd', textAlign: 'left' }} {...p} />,
          td:    ({ node: _node, ...p }) => <td style={{ border: '1px solid #1e3a5f', padding: '6px 10px', color: '#cbd5e1' }} {...p} />,
          code:  ({ node: _node, ...p }) => <code style={{ background: '#0d1b2e', padding: '1px 5px', borderRadius: 4, color: '#5eead4', fontSize: 12 }} {...p} />,
          pre:   ({ node: _node, ...p }) => <pre style={{ background: '#0d1b2e', padding: 12, borderRadius: 8, overflowX: 'auto', fontSize: 12 }} {...p} />,
          a:     ({ node: _node, ...p }) => <a style={{ color: '#5eead4' }} target="_blank" rel="noreferrer" {...p} />,
          h1:    ({ node: _node, ...p }) => <h3 style={{ color: '#e2e8f0', fontSize: 16, margin: '10px 0 6px' }} {...p} />,
          h2:    ({ node: _node, ...p }) => <h4 style={{ color: '#e2e8f0', fontSize: 14, margin: '10px 0 6px' }} {...p} />,
          h3:    ({ node: _node, ...p }) => <h5 style={{ color: '#e2e8f0', fontSize: 13, margin: '8px 0 4px' }} {...p} />,
          strong:({ node: _node, ...p }) => <strong style={{ color: '#fff' }} {...p} />,
        }}
      >{text}</ReactMarkdown>
    </div>
  )
}

function DataTable({ rows }: { rows: any[] }) {
  const cols = Array.from(rows.reduce((s: Set<string>, r: any) => { Object.keys(r || {}).forEach(k => s.add(k)); return s }, new Set<string>()))
  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 12.5 }}>
        <thead>
          <tr>{cols.map(c => <th key={c} style={{ border: '1px solid #1e3a5f', padding: '7px 10px', background: '#0d1b2e', color: '#93c5fd', textAlign: 'left', whiteSpace: 'nowrap' }}>{prettyKey(c)}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>{cols.map(c => <td key={c} style={{ border: '1px solid #1e3a5f', padding: '7px 10px', color: '#cbd5e1' }}>{fmtCell(r?.[c])}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function KeyValueList({ obj }: { obj: Record<string, any> }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '6px 16px', fontSize: 13 }}>
      {Object.entries(obj).map(([k, v]) => (
        <Fragment key={k}>
          <div style={{ color: '#9ca3af', whiteSpace: 'nowrap' }}>{prettyKey(k)}</div>
          <div style={{ color: '#e2e8f0', fontWeight: 500, wordBreak: 'break-word' }}>{fmtCell(v)}</div>
        </Fragment>
      ))}
    </div>
  )
}

function fmtCell(v: any): string {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'boolean') return v ? '✓ Yes' : '✗ No'
  if (Array.isArray(v)) return v.join(', ')
  if (typeof v === 'object') return JSON.stringify(v)
  return String(v)
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
    <div className="aaa-twocol" style={{ gap }}>
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
