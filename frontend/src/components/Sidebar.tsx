import { motion, AnimatePresence } from 'framer-motion'
import { PageId } from '../App'
import { UserProfile } from '../lib/api'

interface NavItem { id: PageId; label: string; group: string }

const NAV: NavItem[] = [
  { id: 'dashboard',        label: 'Dashboard',        group: 'Overview' },
  { id: 'social',           label: 'Social Media',     group: 'Agents' },
  { id: 'ca-accounting',    label: 'CA & Accounting',  group: 'Agents' },
  { id: 'customer-support', label: 'Customer Support', group: 'Agents' },
  { id: 'settings',         label: 'Settings',         group: 'Settings' },
]

const ICONS: Record<PageId, string> = {
  'dashboard':        '⊞',
  'social':           '📱',
  'ca-accounting':    '🧮',
  'customer-support': '💬',
  'settings':         '⚙',
}

const AGENT_ACCENT: Record<string, string> = {
  social:             '#8B5CF6',
  'ca-accounting':    '#F59E0B',
  'customer-support': '#10B981',
}

interface Props {
  current: PageId
  onNavigate: (id: PageId) => void
  collapsed: boolean
  onToggle: () => void
  isAdmin?: boolean
  allowedTools?: string[]
  alwaysAllowed?: PageId[]
  profile?: UserProfile | null
  onLogout?: () => void
}

export default function Sidebar({
  current, onNavigate, collapsed, onToggle,
  isAdmin = false, allowedTools = [], alwaysAllowed = [], profile = null, onLogout,
}: Props) {
  const canSee = (item: NavItem) =>
    isAdmin || alwaysAllowed.includes(item.id) || allowedTools.includes(item.id)

  const visible = NAV.filter(canSee)
  const groups  = Array.from(new Set(visible.map(n => n.group)))

  const initial = profile?.email?.charAt(0).toUpperCase() ?? 'U'

  return (
    <motion.aside
      animate={{ width: collapsed ? 60 : 220, minWidth: collapsed ? 60 : 220 }}
      transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
      style={{
        background: 'var(--surface)',
        borderRight: '1px solid var(--border)',
        display: 'flex', flexDirection: 'column',
        overflow: 'hidden', flexShrink: 0, height: '100vh',
      }}
    >
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: collapsed ? '16px 10px' : '16px 14px',
        borderBottom: '1px solid var(--border)', flexShrink: 0, height: 56,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, overflow: 'hidden' }}>
          <div style={{
            width: 32, height: 32, borderRadius: 9, flexShrink: 0,
            background: 'linear-gradient(135deg, #10B981, #6366F1)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 16, fontWeight: 800, color: '#fff',
          }}>A</div>
          <AnimatePresence>
            {!collapsed && (
              <motion.span
                initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -8 }}
                transition={{ duration: 0.2 }}
                style={{ fontWeight: 700, fontSize: 14, whiteSpace: 'nowrap', color: 'var(--text)' }}
              >
                AI Agentic
              </motion.span>
            )}
          </AnimatePresence>
        </div>
        <button onClick={onToggle} style={{
          background: 'none', border: 'none', cursor: 'pointer',
          color: 'var(--text-3)', fontSize: 16, padding: 4, flexShrink: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          borderRadius: 6, transition: 'color 0.15s, background 0.15s',
        }}
          onMouseEnter={e => { e.currentTarget.style.color = 'var(--text)'; e.currentTarget.style.background = 'var(--surface-2)' }}
          onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-3)'; e.currentTarget.style.background = 'transparent' }}
        >
          {collapsed ? '›' : '‹'}
        </button>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, overflowY: 'auto', overflowX: 'hidden', padding: '10px 8px' }}>
        {groups.map(group => (
          <div key={group}>
            <AnimatePresence>
              {!collapsed && (
                <motion.div
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                  style={{
                    fontSize: 10, fontWeight: 600, color: 'var(--text-3)',
                    textTransform: 'uppercase', letterSpacing: '0.08em',
                    padding: '12px 8px 6px',
                  }}
                >{group}</motion.div>
              )}
            </AnimatePresence>

            {visible.filter(n => n.group === group).map(item => {
              const isActive  = current === item.id
              const accent    = AGENT_ACCENT[item.id]
              return (
                <button key={item.id} onClick={() => onNavigate(item.id)}
                  title={collapsed ? item.label : undefined}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    width: '100%', padding: collapsed ? '9px 10px' : '9px 10px',
                    borderRadius: 8, border: 'none', cursor: 'pointer', marginBottom: 2,
                    background: isActive ? (accent ? `${accent}18` : 'var(--surface-2)') : 'transparent',
                    color: isActive ? (accent ?? 'var(--text)') : 'var(--text-3)',
                    transition: 'all 0.15s', textAlign: 'left', position: 'relative',
                  }}
                  onMouseEnter={e => { if (!isActive) { e.currentTarget.style.background = 'var(--surface-2)'; e.currentTarget.style.color = 'var(--text)' } }}
                  onMouseLeave={e => { if (!isActive) { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text-3)' } }}
                >
                  {/* Active indicator */}
                  {isActive && (
                    <span style={{
                      position: 'absolute', left: 0, top: '50%', transform: 'translateY(-50%)',
                      width: 3, height: 20, borderRadius: 3,
                      background: accent ?? 'var(--accent)',
                    }} />
                  )}

                  <span style={{ fontSize: 16, flexShrink: 0, width: 20, textAlign: 'center' }}>
                    {ICONS[item.id]}
                  </span>
                  <AnimatePresence>
                    {!collapsed && (
                      <motion.span
                        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                        transition={{ duration: 0.15 }}
                        style={{ fontSize: 13, fontWeight: isActive ? 600 : 400, whiteSpace: 'nowrap' }}
                      >{item.label}</motion.span>
                    )}
                  </AnimatePresence>
                </button>
              )
            })}
          </div>
        ))}
      </nav>

      {/* User / Logout */}
      <div style={{ borderTop: '1px solid var(--border)', padding: '10px 8px', flexShrink: 0 }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 10,
          padding: '8px 10px', borderRadius: 8,
          background: 'var(--surface-2)',
        }}>
          <div style={{
            width: 28, height: 28, borderRadius: 8, flexShrink: 0,
            background: 'var(--accent)', color: '#fff',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 12, fontWeight: 700,
          }}>{initial}</div>
          <AnimatePresence>
            {!collapsed && (
              <motion.div
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                style={{ flex: 1, minWidth: 0 }}
              >
                <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {profile?.email ?? 'User'}
                </div>
                <div style={{ fontSize: 10, color: 'var(--text-3)', textTransform: 'capitalize' }}>
                  {profile?.role ?? 'client'}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          <AnimatePresence>
            {!collapsed && onLogout && (
              <motion.button
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                onClick={onLogout}
                style={{
                  background: 'none', border: 'none', cursor: 'pointer',
                  color: 'var(--text-3)', fontSize: 14, padding: 2, flexShrink: 0,
                  borderRadius: 4, transition: 'color 0.15s',
                }}
                onMouseEnter={e => (e.currentTarget.style.color = 'var(--danger)')}
                onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-3)')}
                title="Sign out"
              >⏻</motion.button>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.aside>
  )
}
