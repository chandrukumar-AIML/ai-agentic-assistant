// frontend/src/components/NotificationBell.tsx — Real-time notification center
import { useState, useEffect, useRef } from 'react'
import { apiFetch } from '../lib/api'

interface Notification {
  id:         string
  title:      string
  message:    string
  type:       'info' | 'success' | 'warning' | 'error'
  source:     string
  read:       boolean
  created_at: string
}

const TYPE_ICON: Record<string, string> = {
  info:    'ℹ️',
  success: '✅',
  warning: '⚠️',
  error:   '❌',
}

const TYPE_COLOR: Record<string, string> = {
  info:    '#6366f1',
  success: '#22c55e',
  warning: '#f59e0b',
  error:   '#ef4444',
}

export default function NotificationBell() {
  const [open,         setOpen]         = useState(false)
  const [notifications, setNotifs]      = useState<Notification[]>([])
  const [unread,       setUnread]       = useState(0)
  const dropdownRef = useRef<HTMLDivElement>(null)

  async function load() {
    try {
      const data = await apiFetch('/notifications')
      setNotifs(data.notifications || [])
      setUnread(data.unread_count   || 0)
    } catch {}
  }

  async function markAllRead() {
    try {
      await apiFetch('/notifications/mark-read', { method: 'POST' })
      setNotifs(prev => prev.map(n => ({ ...n, read: true })))
      setUnread(0)
    } catch {}
  }

  async function deleteNotif(id: string, e: React.MouseEvent) {
    e.stopPropagation()
    try {
      await apiFetch(`/notifications/${id}`, { method: 'DELETE' })
      setNotifs(prev => prev.filter(n => n.id !== id))
    } catch {}
  }

  // Poll every 30 seconds
  useEffect(() => {
    load()
    const t = setInterval(load, 30_000)
    return () => clearInterval(t)
  }, [])

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  function timeAgo(iso: string): string {
    const diff = Date.now() - new Date(iso).getTime()
    const m = Math.floor(diff / 60000)
    if (m < 1)  return 'just now'
    if (m < 60) return `${m}m ago`
    const h = Math.floor(m / 60)
    if (h < 24) return `${h}h ago`
    return `${Math.floor(h / 24)}d ago`
  }

  return (
    <div ref={dropdownRef} style={{ position: 'relative' }}>
      {/* Bell Button */}
      <button
        onClick={() => { setOpen(o => !o); if (!open) load() }}
        style={{
          position: 'relative',
          background: 'none', border: 'none',
          cursor: 'pointer', padding: '4px',
          fontSize: 16, lineHeight: 1,
          color: unread > 0 ? '#f59e0b' : '#4b5563',
          transition: 'color 0.15s',
        }}
        title="Notifications"
      >
        🔔
        {unread > 0 && (
          <span style={{
            position: 'absolute', top: -2, right: -2,
            minWidth: 16, height: 16,
            background: '#ef4444', borderRadius: 8,
            fontSize: 9, fontWeight: 700, color: '#fff',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            padding: '0 3px',
          }}>
            {unread > 9 ? '9+' : unread}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {open && (
        <div style={{
          position: 'absolute',
          top: 'calc(100% + 8px)',
          left: '50%',
          transform: 'translateX(-50%)',
          width: 320,
          background: '#161b27',
          border: '1px solid #1e2535',
          borderRadius: 12,
          boxShadow: '0 20px 40px rgba(0,0,0,0.5)',
          zIndex: 1000,
          overflow: 'hidden',
        }}>
          {/* Header */}
          <div style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            padding: '12px 14px',
            borderBottom: '1px solid #1e2535',
          }}>
            <span style={{ fontWeight: 600, fontSize: 13, color: '#e2e8f0' }}>
              Notifications {unread > 0 && <span style={{ color: '#ef4444' }}>({unread})</span>}
            </span>
            {unread > 0 && (
              <button onClick={markAllRead} style={{
                background: 'none', border: 'none', cursor: 'pointer',
                color: '#6366f1', fontSize: 11, fontWeight: 600,
              }}>Mark all read</button>
            )}
          </div>

          {/* List */}
          <div style={{ maxHeight: 360, overflowY: 'auto' }}>
            {notifications.length === 0 ? (
              <div style={{
                padding: '32px 20px', textAlign: 'center',
                color: '#4b5563', fontSize: 13,
              }}>
                <div style={{ fontSize: 28, marginBottom: 10 }}>🔔</div>
                All caught up! No notifications.
              </div>
            ) : (
              notifications.map(n => (
                <div key={n.id} style={{
                  padding: '10px 14px',
                  borderBottom: '1px solid #0f1117',
                  background: n.read ? 'transparent' : 'rgba(99,102,241,0.05)',
                  display: 'flex', gap: 10, alignItems: 'flex-start',
                }}>
                  <span style={{ fontSize: 16, flexShrink: 0, marginTop: 1 }}>
                    {TYPE_ICON[n.type] || 'ℹ️'}
                  </span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
                      <span style={{
                        fontSize: 12, fontWeight: n.read ? 400 : 600,
                        color: n.read ? '#9ca3af' : '#e2e8f0',
                        flex: 1,
                      }}>{n.title}</span>
                      <button onClick={e => deleteNotif(n.id, e)} style={{
                        background: 'none', border: 'none', cursor: 'pointer',
                        color: '#374151', fontSize: 11, flexShrink: 0,
                        padding: '0 2px',
                      }}>✕</button>
                    </div>
                    <div style={{ fontSize: 11, color: '#6b7280', marginTop: 2, lineHeight: 1.5 }}>
                      {n.message}
                    </div>
                    <div style={{ display: 'flex', gap: 8, marginTop: 4, alignItems: 'center' }}>
                      <span style={{
                        fontSize: 9, fontWeight: 600, padding: '1px 6px',
                        borderRadius: 10,
                        background: `${TYPE_COLOR[n.type] || '#6366f1'}22`,
                        color: TYPE_COLOR[n.type] || '#6366f1',
                      }}>{n.source}</span>
                      <span style={{ fontSize: 10, color: '#374151' }}>{timeAgo(n.created_at)}</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          <div style={{
            padding: '8px 14px',
            borderTop: '1px solid #1e2535',
            textAlign: 'center',
          }}>
            <button onClick={load} style={{
              background: 'none', border: 'none', cursor: 'pointer',
              color: '#4b5563', fontSize: 11,
            }}>↻ Refresh</button>
          </div>
        </div>
      )}
    </div>
  )
}
