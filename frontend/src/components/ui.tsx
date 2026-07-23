// frontend/src/components/ui.tsx — Shared UI primitives
import { Fragment, ReactNode, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

// ── Page Shell ────────────────────────────────────────────────────────────────
export function PageShell({ title, subtitle, icon, children }: {
  title: string; subtitle?: string; icon: string; children: ReactNode
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: 'var(--bg)', overflow: 'hidden' }}>
      <div className="aaa-page-head" style={{
        borderBottom: '1px solid var(--border)',
        background: 'var(--surface)', flexShrink: 0,
        display: 'flex', alignItems: 'center', gap: 12,
      }}>
        <span style={{ fontSize: 22 }}>{icon}</span>
        <div>
          <div style={{ color: 'var(--text)', fontSize: 16, fontWeight: 600 }}>{title}</div>
          {subtitle && <div style={{ color: 'var(--text-3)', fontSize: 12, marginTop: 1 }}>{subtitle}</div>}
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
      background: 'var(--surface)', border: '1px solid var(--border)',
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
  const variantStyle: React.CSSProperties = variant === 'primary'
    ? { background: 'var(--accent)', color: '#fff', border: '1px solid transparent', opacity: loading || disabled ? 0.6 : 1 }
    : variant === 'danger'
    ? { background: 'var(--danger)', color: '#fff', border: '1px solid transparent' }
    : variant === 'success'
    ? { background: 'var(--success)', color: '#fff', border: '1px solid transparent' }
    : { background: 'var(--surface-2)', color: 'var(--text-2)', border: '1px solid var(--border)' }

  return (
    <button onClick={onClick} disabled={loading || disabled} style={{
      ...variantStyle,
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
  const common: React.CSSProperties = {
    width: '100%', background: 'var(--bg)', border: '1px solid var(--border)',
    borderRadius: 8, padding: '10px 12px', color: 'var(--text)',
    fontSize: 13, outline: 'none', boxSizing: 'border-box',
    fontFamily: 'inherit',
  }
  return (
    <div style={{ marginBottom: 14 }}>
      {label && <label style={{ display: 'block', fontSize: 12, color: 'var(--text-2)', marginBottom: 5, fontWeight: 500 }}>{label}</label>}
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
      {label && <label style={{ display: 'block', fontSize: 12, color: 'var(--text-2)', marginBottom: 5, fontWeight: 500 }}>{label}</label>}
      <select value={value} onChange={e => onChange(e.target.value)} style={{
        width: '100%', background: 'var(--bg)', border: '1px solid var(--border)',
        borderRadius: 8, padding: '10px 12px', color: 'var(--text)', fontSize: 13,
        outline: 'none', boxSizing: 'border-box' as const, cursor: 'pointer',
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
    <div style={{
      background: 'var(--surface)', border: '1px solid var(--border)',
      borderRadius: 12, padding: 28, textAlign: 'center', color: 'var(--text-3)',
    }}>
      <div style={{
        width: 32, height: 32, borderRadius: '50%', margin: '0 auto 12px',
        border: '2px solid var(--border-2)', borderTop: '2px solid var(--accent)',
        animation: 'spin 0.8s linear infinite',
      }} />
      <p style={{ fontSize: 13, color: 'var(--text-2)' }}>Processing...</p>
    </div>
  )
  if (error) return (
    <div style={{
      background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.25)',
      borderRadius: 12, padding: 16,
    }}>
      <span style={{ color: 'var(--danger)', fontSize: 12, fontWeight: 600 }}>⚠ Error</span>
      <p style={{ color: 'var(--danger)', fontSize: 13, marginTop: 4, opacity: 0.8 }}>{error}</p>
    </div>
  )
  if (!data) return null
  return (
    <div style={{
      background: 'var(--surface)', border: '1px solid var(--border-2)',
      borderRadius: 12, overflow: 'hidden',
    }}>
      {title && (
        <div style={{
          padding: '8px 14px', background: 'var(--surface-2)',
          borderBottom: '1px solid var(--border)',
          display: 'flex', alignItems: 'center', gap: 8,
        }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--accent)', display: 'inline-block' }} />
          <span style={{ color: 'var(--accent-2)', fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{title}</span>
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
            <div style={{ marginBottom: 10, fontSize: 12, color: 'var(--text-2)' }}>
              {meta.map(k => <span key={k} style={{ marginRight: 14 }}><b style={{ color: 'var(--text)' }}>{prettyKey(k)}:</b> {String(data[k])}</span>)}
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
    <pre style={{
      margin: 0, color: 'var(--accent-2)', fontSize: 12, lineHeight: 1.6,
      whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontFamily: 'Monaco, Consolas, monospace',
    }}>
      {JSON.stringify(data, null, 2)}
    </pre>
  )
}

function prettyKey(k: string): string {
  return k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function Markdown({ text }: { text: string }) {
  return (
    <div style={{ color: 'var(--text)', fontSize: 13.5, lineHeight: 1.65 }} className="aaa-md">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          table: ({ node: _node, ...p }) => <table style={{ borderCollapse: 'collapse', width: '100%', margin: '8px 0', fontSize: 12.5 }} {...p} />,
          th:    ({ node: _node, ...p }) => <th style={{ border: '1px solid var(--border)', padding: '6px 10px', background: 'var(--surface-2)', color: 'var(--accent-2)', textAlign: 'left' }} {...p} />,
          td:    ({ node: _node, ...p }) => <td style={{ border: '1px solid var(--border)', padding: '6px 10px', color: 'var(--text-2)' }} {...p} />,
          code:  ({ node: _node, ...p }) => <code style={{ background: 'var(--surface-2)', padding: '1px 5px', borderRadius: 4, color: 'var(--success)', fontSize: 12 }} {...p} />,
          pre:   ({ node: _node, ...p }) => <pre style={{ background: 'var(--surface-2)', padding: 12, borderRadius: 8, overflowX: 'auto', fontSize: 12, border: '1px solid var(--border)' }} {...p} />,
          a:     ({ node: _node, ...p }) => <a style={{ color: 'var(--accent-2)' }} target="_blank" rel="noreferrer" {...p} />,
          h1:    ({ node: _node, ...p }) => <h3 style={{ color: 'var(--text)', fontSize: 16, margin: '10px 0 6px' }} {...p} />,
          h2:    ({ node: _node, ...p }) => <h4 style={{ color: 'var(--text)', fontSize: 14, margin: '10px 0 6px' }} {...p} />,
          h3:    ({ node: _node, ...p }) => <h5 style={{ color: 'var(--text)', fontSize: 13, margin: '8px 0 4px' }} {...p} />,
          strong:({ node: _node, ...p }) => <strong style={{ color: 'var(--text)' }} {...p} />,
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
          <tr>{cols.map(c => <th key={c} style={{ border: '1px solid var(--border)', padding: '7px 10px', background: 'var(--surface-2)', color: 'var(--accent-2)', textAlign: 'left', whiteSpace: 'nowrap' }}>{prettyKey(c)}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>{cols.map(c => <td key={c} style={{ border: '1px solid var(--border)', padding: '7px 10px', color: 'var(--text-2)' }}>{fmtCell(r?.[c])}</td>)}</tr>
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
          <div style={{ color: 'var(--text-3)', whiteSpace: 'nowrap' }}>{prettyKey(k)}</div>
          <div style={{ color: 'var(--text)', fontWeight: 500, wordBreak: 'break-word' }}>{fmtCell(v)}</div>
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
const BADGE_PALETTE: Record<string, { bg: string; color: string }> = {
  blue:   { bg: 'rgba(16,185,129,0.15)', color: '#5eead4' },
  green:  { bg: 'rgba(34,197,94,0.15)',  color: '#86efac' },
  red:    { bg: 'rgba(239,68,68,0.15)',   color: '#fca5a5' },
  yellow: { bg: 'rgba(234,179,8,0.15)',   color: '#fde047' },
  purple: { bg: 'rgba(168,85,247,0.15)',  color: '#d8b4fe' },
}
export function Badge({ text, label, children, color = 'blue' }: {
  text?: string; label?: string; children?: ReactNode; color?: string
}) {
  const content = text ?? label ?? children
  const preset = BADGE_PALETTE[color]
  const bg    = preset ? preset.bg    : color + '22'
  const fg    = preset ? preset.color : color
  return (
    <span style={{
      fontSize: 11, padding: '2px 8px', borderRadius: 20,
      background: bg, color: fg, fontWeight: 600,
    }}>{content}</span>
  )
}

// ── Stat Card ─────────────────────────────────────────────────────────────────
export function StatCard({ label, value, icon, trend }: { label: string; value: string | number; icon: string; trend?: string }) {
  return (
    <div style={{
      background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12,
      padding: 20, display: 'flex', flexDirection: 'column', gap: 8,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <span style={{ fontSize: 24 }}>{icon}</span>
        {trend && <span style={{ fontSize: 11, color: 'var(--success)' }}>{trend}</span>}
      </div>
      <div style={{ color: 'var(--text)', fontSize: 22, fontWeight: 700 }}>{value}</div>
      <div style={{ color: 'var(--text-3)', fontSize: 12 }}>{label}</div>
    </div>
  )
}

// ── Tabs ──────────────────────────────────────────────────────────────────────
export function Tabs({ tabs, active, onChange, accentColor, groups }: {
  tabs: { id: string; label: string; icon?: string }[]
  active: string
  onChange: (id: string) => void
  accentColor?: string
  groups?: { label: string; ids: string[] }[]
}) {
  const [search, setSearch] = useState('')
  const [activeGroup, setActiveGroup] = useState<string | null>(null)
  const accent = accentColor ?? 'var(--accent)'
  const showSearch = tabs.length > 8

  // Filter by group first, then by search query
  let visible = tabs
  if (!search && activeGroup && groups) {
    const g = groups.find(g => g.label === activeGroup)
    if (g) visible = tabs.filter(t => g.ids.includes(t.id))
  }
  if (search) {
    visible = tabs.filter(t => t.label.toLowerCase().includes(search.toLowerCase()))
  }
  // Always keep the active tab visible so it's not hidden by filters
  if (active && !visible.find(t => t.id === active)) {
    const activeTab = tabs.find(t => t.id === active)
    if (activeTab) visible = [activeTab, ...visible]
  }

  return (
    <div style={{ marginBottom: 16 }}>

      {/* Category group pills */}
      {groups && !search && (
        <div style={{ display: 'flex', gap: 6, marginBottom: 10, flexWrap: 'wrap' }}>
          <button
            onClick={() => setActiveGroup(null)}
            style={{
              padding: '4px 12px', borderRadius: 20, fontSize: 11, fontWeight: 600, border: 'none',
              cursor: 'pointer', transition: 'all 0.15s',
              background: activeGroup === null ? accent : 'var(--surface-3)',
              color: activeGroup === null ? '#fff' : 'var(--text-3)',
            }}
          >All</button>
          {groups.map(g => (
            <button key={g.label}
              onClick={() => setActiveGroup(g.label === activeGroup ? null : g.label)}
              style={{
                padding: '4px 12px', borderRadius: 20, fontSize: 11, fontWeight: 600, border: 'none',
                cursor: 'pointer', transition: 'all 0.15s',
                background: activeGroup === g.label ? accent + 'cc' : 'var(--surface-3)',
                color: activeGroup === g.label ? '#fff' : 'var(--text-3)',
              }}
            >{g.label}</button>
          ))}
        </div>
      )}

      {/* Search input — auto-shows when > 8 tabs */}
      {showSearch && (
        <div style={{ position: 'relative', marginBottom: 10 }}>
          <span style={{
            position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)',
            color: 'var(--text-3)', fontSize: 13, pointerEvents: 'none',
          }}>🔍</span>
          <input
            value={search}
            onChange={e => { setSearch(e.target.value); setActiveGroup(null) }}
            placeholder="Search features..."
            style={{
              width: '100%', boxSizing: 'border-box' as const,
              paddingLeft: 32, paddingRight: search ? 32 : 12,
              paddingTop: 7, paddingBottom: 7,
              background: 'var(--surface-2)', border: '1px solid var(--border)',
              borderRadius: 8, color: 'var(--text)', fontSize: 12, outline: 'none',
              fontFamily: 'inherit',
            }}
          />
          {search && (
            <button onClick={() => setSearch('')} style={{
              position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)',
              background: 'none', border: 'none', cursor: 'pointer',
              color: 'var(--text-3)', fontSize: 14, padding: 2, lineHeight: 1,
            }}>✕</button>
          )}
        </div>
      )}

      {/* Tab pills */}
      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
        {visible.length === 0 && (
          <span style={{ fontSize: 12, color: 'var(--text-3)', padding: '6px 4px' }}>No features match "{search}"</span>
        )}
        {visible.map(t => (
          <button key={t.id} onClick={() => { onChange(t.id); setSearch('') }} style={{
            padding: '6px 12px', borderRadius: 20, fontSize: 12, fontWeight: active === t.id ? 600 : 400,
            border: active === t.id ? 'none' : '1px solid var(--border)',
            cursor: 'pointer', transition: 'all 0.15s',
            background: active === t.id ? accent : 'var(--surface-2)',
            color: active === t.id ? '#fff' : 'var(--text-2)',
            display: 'flex', alignItems: 'center', gap: 5,
          }}>
            {t.icon && <span style={{ fontSize: 13 }}>{t.icon}</span>}
            {t.label}
          </button>
        ))}
      </div>
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
      <div style={{ color: 'var(--text)', fontSize: 14, fontWeight: 600 }}>{title}</div>
      {sub && <div style={{ color: 'var(--text-3)', fontSize: 12, marginTop: 2 }}>{sub}</div>}
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
