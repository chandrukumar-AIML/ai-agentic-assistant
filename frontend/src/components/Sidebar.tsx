// frontend/src/components/Sidebar.tsx
import { PageId } from '../App'
import { UserProfile } from '../lib/api'
import NotificationBell from './NotificationBell'

interface NavItem {
  id: PageId
  label: string
  icon: string
  badge?: string
  group?: string
  adminOnly?: boolean
}

const NAV: NavItem[] = [
  { id: 'dashboard',    label: 'Dashboard',        icon: '⚡', group: 'Overview' },
  { id: 'chat',         label: 'AI Chat',           icon: '💬', group: 'Overview' },
  { id: 'compliance',   label: 'Guardian',          icon: '🛡️', badge: 'F1', group: 'AI Core' },
  { id: 'hitl',         label: 'HITL Approvals',   icon: '👁️', badge: 'F6', group: 'AI Core' },
  { id: 'output',       label: 'Output Generator', icon: '📄', badge: 'F7', group: 'AI Core' },
  { id: 'ab-test',      label: 'A/B Testing',      icon: '⚗️', badge: 'F12', group: 'AI Core' },
  { id: 'scheduler',    label: 'Task Scheduler',   icon: '⏰', badge: 'F4', group: 'AI Core' },
  { id: 'social',       label: 'Social Media',     icon: '📱', badge: 'NEW', group: 'Core Agents' },
  { id: 'ca-accounting',label: 'CA & Accounting',  icon: '📒', badge: 'NEW', group: 'Core Agents' },
  { id: 'agri',         label: 'AgriTech',         icon: '🌾', badge: 'F9',  group: 'Verticals' },
  { id: 'legal',        label: 'Legal Research',   icon: '⚖️', badge: 'F10', group: 'Verticals' },
  { id: 'cybersec',     label: 'Cybersecurity',    icon: '🔐', badge: 'F11', group: 'Verticals' },
  { id: 'receptionist', label: 'Receptionist',     icon: '☎️', badge: 'F13', group: 'Verticals' },
  { id: 'form-reader',  label: 'Form Reader',      icon: '📋', badge: 'F14', group: 'Verticals' },
  { id: 'email',        label: 'Email Manager',    icon: '📧', badge: 'F15', group: 'Verticals' },
  { id: 'sales',        label: 'Sales & CRM',      icon: '💼', badge: 'F16', group: 'Verticals' },
  { id: 'accountant',   label: 'Accountant',       icon: '🧮', badge: 'F17', group: 'Verticals' },
  { id: 'hr',           label: 'HR Assistant',     icon: '👥', badge: 'F18', group: 'Verticals' },
  { id: 'analyst',      label: 'Data Analyst',     icon: '📊', badge: 'V1',  group: 'Verticals' },
  { id: 'devops',       label: 'DevOps Engineer',  icon: '⚙️', badge: 'V2',  group: 'Verticals' },
  { id: 'qa',           label: 'QA Engineer',      icon: '🧪', badge: 'V3',  group: 'Verticals' },
  { id: 'project',      label: 'Project Manager',  icon: '📋', badge: 'V4',  group: 'Verticals' },
  { id: 'code',         label: 'Code Assistant',   icon: '💻', badge: 'V5',  group: 'Verticals' },
  { id: 'ml',           label: 'ML Engineer',      icon: '🤖', badge: 'V6',  group: 'Verticals' },
  { id: 'dba',          label: 'DBA',              icon: '🗄️', badge: 'V7',  group: 'Verticals' },
  { id: 'techlead',     label: 'Tech Lead',        icon: '🏗️', badge: 'V8',  group: 'Verticals' },
  { id: 'healthcare',   label: 'Healthcare',       icon: '🏥', badge: 'V9',  group: 'Verticals' },
  { id: 'realestate',   label: 'Real Estate',      icon: '🏘️', badge: 'V10', group: 'Verticals' },
  { id: 'edtech',       label: 'EdTech',           icon: '📚', badge: 'V11', group: 'Verticals' },
  { id: 'billing',        label: 'Billing & Plans',  icon: '💳', badge: 'F8',  group: 'Settings' },
  { id: 'knowledge-base', label: 'Knowledge Base',   icon: '🧠', badge: 'RAG', group: 'Settings' },
  { id: 'integrations',   label: 'Integrations',     icon: '🔌', badge: 'LIVE', group: 'Settings' },
  { id: 'webhooks',       label: 'Webhooks',         icon: '🪝', badge: 'NEW', group: 'Settings' },
  { id: 'admin',          label: 'Admin Panel',      icon: '🛡️', badge: 'ADM', group: 'Settings', adminOnly: true },
  { id: 'settings',       label: 'Settings',         icon: '⚙️',              group: 'Settings' },
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
    if (item.adminOnly) return isAdmin
    if (isAdmin) return true
    return alwaysAllowed.includes(item.id) || allowedTools.includes(item.id)
  }
  const visible = NAV.filter(canSee)
  const groups  = Array.from(new Set(visible.map(n => n.group)))

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
        display: 'flex', alignItems: 'center', justifyContent: collapsed ? 'center' : 'space-between',
        padding: collapsed ? '16px 0' : '16px 14px',
        borderBottom: '1px solid #1e2535',
        flexShrink: 0,
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
          <NotificationBell />
          <button onClick={onToggle} style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: '#4b5563', fontSize: 14, padding: 2,
          }}>☰</button>
        </div>
      </div>

      {/* Nav Items */}
      <nav style={{ flex: 1, overflowY: 'auto', padding: '8px 0' }}>
        {groups.map(group => (
          <div key={group}>
            {!collapsed && (
              <div style={{
                padding: '10px 14px 4px',
                fontSize: 10, fontWeight: 600, letterSpacing: '0.08em',
                color: '#374151', textTransform: 'uppercase',
              }}>{group}</div>
            )}
            {visible.filter(n => n.group === group).map(item => {
              const active = current === item.id
              return (
                <button key={item.id} onClick={() => onNavigate(item.id)} style={{
                  width: '100%', display: 'flex', alignItems: 'center',
                  gap: collapsed ? 0 : 8,
                  padding: collapsed ? '10px 0' : '8px 14px',
                  justifyContent: collapsed ? 'center' : 'flex-start',
                  background: active ? 'rgba(16,185,129,0.15)' : 'none',
                  border: 'none', borderLeft: active ? '2px solid #10b981' : '2px solid transparent',
                  cursor: 'pointer', color: active ? '#5eead4' : '#6b7280',
                  fontSize: 13, borderRadius: collapsed ? '0' : '0',
                  transition: 'all 0.15s',
                  textAlign: 'left',
                }}>
                  <span style={{ fontSize: 15, flexShrink: 0 }}>{item.icon}</span>
                  {!collapsed && (
                    <>
                      <span style={{ flex: 1, fontWeight: active ? 500 : 400 }}>{item.label}</span>
                      {item.badge && !/^[FV]\d+$/.test(item.badge) && (
                        <span style={{
                          fontSize: 9, fontWeight: 600, padding: '1px 5px',
                          borderRadius: 4, background: active ? 'rgba(16,185,129,0.3)' : '#1e2535',
                          color: active ? '#5eead4' : '#4b5563',
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
