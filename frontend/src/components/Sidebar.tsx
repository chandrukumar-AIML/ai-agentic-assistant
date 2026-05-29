// frontend/src/components/Sidebar.tsx
import { PageId } from '../App'

interface NavItem {
  id: PageId
  label: string
  icon: string
  badge?: string
  group?: string
}

const NAV: NavItem[] = [
  { id: 'dashboard',    label: 'Dashboard',        icon: '⚡', group: 'Overview' },
  { id: 'chat',         label: 'AI Chat',           icon: '💬', group: 'Overview' },
  { id: 'compliance',   label: 'Guardian',          icon: '🛡️', badge: 'F1', group: 'AI Core' },
  { id: 'hitl',         label: 'HITL Approvals',   icon: '👁️', badge: 'F6', group: 'AI Core' },
  { id: 'output',       label: 'Output Generator', icon: '📄', badge: 'F7', group: 'AI Core' },
  { id: 'ab-test',      label: 'A/B Testing',      icon: '⚗️', badge: 'F12', group: 'AI Core' },
  { id: 'scheduler',    label: 'Task Scheduler',   icon: '⏰', badge: 'F4', group: 'AI Core' },
  { id: 'agri',         label: 'AgriTech',         icon: '🌾', badge: 'F9',  group: 'Verticals' },
  { id: 'legal',        label: 'Legal Research',   icon: '⚖️', badge: 'F10', group: 'Verticals' },
  { id: 'cybersec',     label: 'Cybersecurity',    icon: '🔐', badge: 'F11', group: 'Verticals' },
  { id: 'receptionist', label: 'Receptionist',     icon: '☎️', badge: 'F13', group: 'Verticals' },
  { id: 'form-reader',  label: 'Form Reader',      icon: '📋', badge: 'F14', group: 'Verticals' },
  { id: 'email',        label: 'Email Manager',    icon: '📧', badge: 'F15', group: 'Verticals' },
  { id: 'sales',        label: 'Sales & CRM',      icon: '💼', badge: 'F16', group: 'Verticals' },
  { id: 'accountant',   label: 'Accountant',       icon: '🧮', badge: 'F17', group: 'Verticals' },
  { id: 'hr',           label: 'HR Assistant',     icon: '👥', badge: 'F18', group: 'Verticals' },
  { id: 'social',       label: 'Social Media',     icon: '📱', badge: 'F19', group: 'Verticals' },
  { id: 'analyst',      label: 'Data Analyst',     icon: '📊', badge: 'V1',  group: 'Verticals' },
  { id: 'devops',       label: 'DevOps Engineer',  icon: '⚙️', badge: 'V2',  group: 'Verticals' },
  { id: 'billing',        label: 'Billing & Plans',  icon: '💳', badge: 'F8',  group: 'Settings' },
  { id: 'knowledge-base', label: 'Knowledge Base',   icon: '🧠', badge: 'RAG', group: 'Settings' },
  { id: 'settings',       label: 'Settings',         icon: '⚙️',              group: 'Settings' },
]

interface Props {
  current: PageId
  onNavigate: (id: PageId) => void
  collapsed: boolean
  onToggle: () => void
}

export default function Sidebar({ current, onNavigate, collapsed, onToggle }: Props) {
  const groups = Array.from(new Set(NAV.map(n => n.group)))

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
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <span style={{ color: '#fff', fontSize: 12, fontWeight: 700 }}>A</span>
            </div>
            <div>
              <div style={{ color: '#fff', fontSize: 12, fontWeight: 600, lineHeight: 1.2 }}>AI Agentic</div>
              <div style={{ color: '#6366f1', fontSize: 10 }}>v2.0 • 23 Features</div>
            </div>
          </div>
        )}
        {collapsed && (
          <div style={{
            width: 28, height: 28, borderRadius: 8,
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <span style={{ color: '#fff', fontSize: 12, fontWeight: 700 }}>A</span>
          </div>
        )}
        <button onClick={onToggle} style={{
          background: 'none', border: 'none', cursor: 'pointer',
          color: '#4b5563', fontSize: 14, padding: 2,
          display: collapsed ? 'none' : 'block',
        }}>☰</button>
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
            {NAV.filter(n => n.group === group).map(item => {
              const active = current === item.id
              return (
                <button key={item.id} onClick={() => onNavigate(item.id)} style={{
                  width: '100%', display: 'flex', alignItems: 'center',
                  gap: collapsed ? 0 : 8,
                  padding: collapsed ? '10px 0' : '8px 14px',
                  justifyContent: collapsed ? 'center' : 'flex-start',
                  background: active ? 'rgba(99,102,241,0.15)' : 'none',
                  border: 'none', borderLeft: active ? '2px solid #6366f1' : '2px solid transparent',
                  cursor: 'pointer', color: active ? '#a5b4fc' : '#6b7280',
                  fontSize: 13, borderRadius: collapsed ? '0' : '0',
                  transition: 'all 0.15s',
                  textAlign: 'left',
                }}>
                  <span style={{ fontSize: 15, flexShrink: 0 }}>{item.icon}</span>
                  {!collapsed && (
                    <>
                      <span style={{ flex: 1, fontWeight: active ? 500 : 400 }}>{item.label}</span>
                      {item.badge && (
                        <span style={{
                          fontSize: 9, fontWeight: 600, padding: '1px 5px',
                          borderRadius: 4, background: active ? 'rgba(99,102,241,0.3)' : '#1e2535',
                          color: active ? '#a5b4fc' : '#4b5563',
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
        <div style={{
          padding: '10px 14px', borderTop: '1px solid #1e2535',
          fontSize: 10, color: '#374151',
        }}>
          <div style={{ color: '#22c55e', display: 'flex', alignItems: 'center', gap: 4, marginBottom: 2 }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#22c55e', display: 'inline-block' }} />
            Backend: port 8000
          </div>
          <div style={{ color: '#6b7280' }}>Ollama: llama3 active</div>
        </div>
      )}
    </aside>
  )
}
