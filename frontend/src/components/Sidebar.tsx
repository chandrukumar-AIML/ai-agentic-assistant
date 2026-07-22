// frontend/src/components/Sidebar.tsx
import { PageId } from '../App'
import { UserProfile } from '../lib/api'

interface NavItem {
  id: PageId
  label: string
  icon: string
  badge?: string
  group: string
}

const NAV: NavItem[] = [
  { id: 'dashboard',        label: 'Dashboard',        icon: 'D',  group: 'Overview' },
  { id: 'social',           label: 'Social Media',     icon: 'SM', group: 'Core Agents' },
  { id: 'ca-accounting',    label: 'CA & Accounting',  icon: 'CA', group: 'Core Agents' },
  { id: 'customer-support', label: 'Customer Support', icon: 'CS', group: 'Core Agents' },
  { id: 'settings',         label: 'Settings',         icon: 'S',  group: 'Settings' },
]

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
  const canSee = (item: NavItem): boolean => {
    if (isAdmin) return true
    return alwaysAllowed.includes(item.id) || allowedTools.includes(item.id)
  }

  const visible = NAV.filter(canSee)
  const groups  = Array.from(new Set(visible.map(n => n.group)))

  const AGENT_COLORS: Record<string, string> = {
    SM: 'linear-gradient(135deg, #8b5cf6, #6366f1)',
    CA: 'linear-gradient(135deg, #f59e0b, #d97706)',
    CS: 'linear-gradient(135deg, #10b981, #059669)',
  }

  return (
    <aside style={{
      width: collapsed ? 60 : 220,
      minWidth: collapsed ? 60 : 220,
      background: '#161b27',
      borderRight: '1px solid #1e2535',
      display: 'flex',
      flexDirection: 'column',
      transition: 'width 0.2s ease',
      overflow: 'hidden',
      zIndex: 10,
    }}>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center',
        justifyContent: collapsed ? 'center' : 'space-between',
        padding: collapsed ? '16px 0' : '16px 14px',
        borderBottom: '1px solid #1e2535', flexShrink: 0,
      }}>
        {!collapsed && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{
              width: 28, height: 28, borderRadius: 8,
              background: 'linear-gradient(135deg, #10b981, #06b6d4)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <span style={{ color: '#fff', fontSize: 12, fontWeight: 700 }}>A</span>
            </div>
            <div>
              <div style={{ color: '#fff', fontSize: 12, fontWeight: 600, lineHeight: 1.2 }}>AI Agentic</div>
              <div style={{ color: '#10b981', fontSize: 10 }}>Business AI Suite</div>
            </div>
          </div>
        )}
        {collapsed && (
          <div style={{
            width: 28, height: 28, borderRadius: 8,
            background: 'linear-gradient(135deg, #10b981, #06b6d4)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <span style={{ color: '#fff', fontSize: 12, fontWeight: 700 }}>A</span>
          </div>
        )}
        <div style={{ display: collapsed ? 'none' : 'flex', alignItems: 'center', gap: 4 }}>
          <button onClick={onToggle} style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: '#4b5563', fontSize: 14, padding: 2,
          }}>☰</button>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, overflowY: 'auto', padding: '8px 0' }}>
        {groups.map(group => (
          <div key={group}>
            {!collapsed && (
              <div style={{
                padding: '10px 14px 4px', fontSize: 10, fontWeight: 600,
                letterSpacing: '0.08em', color: '#374151', textTransform: 'uppercase',
              }}>{group}</div>
            )}
            {visible.filter(n => n.group === group).map(item => {
              const active = current === item.id
              const isAgent = item.group === 'Core Agents'
              const agentGradient = AGENT_COLORS[item.icon]

              return (
                <button key={item.id} onClick={() => onNavigate(item.id)} style={{
                  width: '100%', display: 'flex', alignItems: 'center',
                  gap: collapsed ? 0 : 10,
                  padding: collapsed ? '10px 0' : '9px 14px',
                  justifyContent: collapsed ? 'center' : 'flex-start',
                  background: active ? 'rgba(16,185,129,0.15)' : 'none',
                  border: 'none',
                  borderLeft: active ? '2px solid #10b981' : '2px solid transparent',
                  cursor: 'pointer',
                  color: active ? '#5eead4' : '#6b7280',
                  fontSize: 13, transition: 'all 0.15s', textAlign: 'left',
                }}>
                  {isAgent ? (
                    <div style={{
                      width: 24, height: 24, borderRadius: 6, flexShrink: 0,
                      background: agentGradient || '#1e2535',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 9, fontWeight: 700, color: '#fff',
                    }}>{item.icon}</div>
                  ) : (
                    <div style={{
                      width: 24, height: 24, borderRadius: 6, flexShrink: 0,
                      background: active ? 'rgba(16,185,129,0.2)' : '#1e2535',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 9, fontWeight: 700,
                      color: active ? '#5eead4' : '#4b5563',
                    }}>{item.icon}</div>
                  )}
                  {!collapsed && (
                    <>
                      <span style={{ flex: 1, fontWeight: active ? 500 : 400 }}>{item.label}</span>
                      {item.badge && (
                        <span style={{
                          fontSize: 9, fontWeight: 600, padding: '1px 5px', borderRadius: 4,
                          background: item.badge === 'NEW'
                            ? (isAgent ? 'rgba(16,185,129,0.25)' : '#1e2535')
                            : '#1e2535',
                          color: item.badge === 'NEW'
                            ? '#10b981'
                            : '#4b5563',
                        }}>{item.badge}</span>
                      )}
                    </>
                  )}
                </button>
              )
            })}
          </div>
        ))}
      </nav>

      {/* Footer */}
      {!collapsed && (
        <div style={{ padding: '10px 14px', borderTop: '1px solid #1e2535', fontSize: 10, color: '#374151' }}>
          {profile && (
            <div style={{ marginBottom: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: '#e2e8f0', fontSize: 12, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {profile.full_name || profile.email}
                </span>
                <span style={{
                  fontSize: 9, fontWeight: 700, padding: '1px 6px', borderRadius: 4,
                  background: 'rgba(16,185,129,0.2)', color: '#5eead4', textTransform: 'uppercase',
                }}>{profile.plan_tier}</span>
              </div>
              <div style={{ color: '#6b7280', fontSize: 10, marginTop: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{profile.email}</div>
              {onLogout && (
                <button onClick={onLogout} style={{
                  marginTop: 6, width: '100%', padding: '5px 0', borderRadius: 6, cursor: 'pointer',
                  background: '#1e2535', border: '1px solid #374151', color: '#9ca3af', fontSize: 11,
                }}>Sign out</button>
              )}
            </div>
          )}
          <div style={{ color: '#22c55e', display: 'flex', alignItems: 'center', gap: 5 }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#22c55e', display: 'inline-block' }} />
            All systems operational
          </div>
        </div>
      )}
    </aside>
  )
}
