// frontend/src/components/MemoryPanel.tsx
import React, { useState, useEffect, useCallback } from 'react'

interface MemoryEntry {
  id:         string
  content:    string
  created_at: string
}

interface MemoryGroups {
  episodic:   MemoryEntry[]
  semantic:   MemoryEntry[]
  procedural: MemoryEntry[]
}

interface Props {
  userId:  string
  isOpen:  boolean
  onClose: () => void
}

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const TYPE_CONFIG = {
  episodic:   { label: 'Past Sessions',        color: '#c0d4f8', text: '#1a3a8f', icon: '🕐' },
  semantic:   { label: 'About You',            color: '#c4e8a0', text: '#2a5200', icon: '👤' },
  procedural: { label: 'Effective Strategies', color: '#ffe0a0', text: '#7a4a00', icon: '⚙️' },
}

export default function MemoryPanel({ userId, isOpen, onClose }: Props) {
  const [memories,  setMemories]  = useState<MemoryGroups | null>(null)
  const [loading,   setLoading]   = useState(false)
  const [deleting,  setDeleting]  = useState<string | null>(null)
  const [error,     setError]     = useState<string | null>(null)
  const [showClear, setShowClear] = useState(false)

  const fetchMemories = useCallback(async () => {
    if (!userId || !isOpen) return
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/memory/${userId}`, {
        headers: { Authorization: `Bearer ${sessionStorage.getItem('aaa_token') || 'dev'}` },
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setMemories(data.memories)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [userId, isOpen])

  useEffect(() => { fetchMemories() }, [fetchMemories])

  const deleteMemory = async (memoryId: string) => {
    setDeleting(memoryId)
    try {
      await fetch(`${API_BASE}/memory/${userId}/${memoryId}`, {
        method:  'DELETE',
        headers: { Authorization: `Bearer ${sessionStorage.getItem('aaa_token') || 'dev'}` },
      })
      await fetchMemories()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Delete failed') // FIXED: removed console.error, surface error to UI
    } finally {
      setDeleting(null)
    }
  }

  const clearAll = async () => {
    setLoading(true)
    try {
      await fetch(`${API_BASE}/memory/${userId}`, {
        method:  'DELETE',
        headers: { Authorization: `Bearer ${sessionStorage.getItem('aaa_token') || 'dev'}` },
      })
      setMemories({ episodic: [], semantic: [], procedural: [] })
      setShowClear(false)
    } catch (e) {
      setError('Failed to clear memories')
    } finally {
      setLoading(false)
    }
  }

  const totalCount = memories
    ? Object.values(memories).reduce((s, arr) => s + arr.length, 0)
    : 0

  if (!isOpen) return null

  return (
    <div style={{
      position: 'fixed', right: 0, top: 0, bottom: 0,
      width: '360px', zIndex: 50,
      background: 'var(--color-background-primary)',
      borderLeft: '0.5px solid var(--color-border-tertiary)',
      display: 'flex', flexDirection: 'column',
      boxShadow: '-4px 0 24px rgba(0,0,0,0.08)',
    }}>
      {/* Header */}
      <div style={{
        padding: '16px', borderBottom: '0.5px solid var(--color-border-tertiary)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <div>
          <p style={{ fontWeight: 500, fontSize: '14px', color: 'var(--color-text-primary)', margin: 0 }}>
            Agent Memory
          </p>
          <p style={{ fontSize: '11px', color: 'var(--color-text-tertiary)', margin: 0, marginTop: '2px' }}>
            {totalCount} memories stored
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button
            onClick={() => setShowClear(true)}
            style={{
              fontSize: '11px', color: '#a32d2d',
              background: 'none', border: 'none', cursor: 'pointer', padding: '4px 8px',
              borderRadius: '4px',
            }}
          >
            Clear all
          </button>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', cursor: 'pointer',
                     color: 'var(--color-text-tertiary)', fontSize: '18px', lineHeight: 1 }}
          >
            ×
          </button>
        </div>
      </div>

      {/* Clear confirmation */}
      {showClear && (
        <div style={{
          margin: '12px', padding: '12px',
          background: '#fff8f8', border: '0.5px solid #f5c0c0',
          borderRadius: '8px', fontSize: '12px',
        }}>
          <p style={{ margin: '0 0 10px', color: '#7a2020', fontWeight: 500 }}>
            Delete all memories? This cannot be undone.
          </p>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={clearAll}
              style={{
                padding: '6px 14px', fontSize: '12px',
                background: '#e24b4a', color: '#fff',
                border: 'none', borderRadius: '6px', cursor: 'pointer',
              }}
            >
              Yes, clear all
            </button>
            <button
              onClick={() => setShowClear(false)}
              style={{
                padding: '6px 14px', fontSize: '12px',
                background: 'var(--color-background-secondary)',
                border: '0.5px solid var(--color-border-tertiary)',
                borderRadius: '6px', cursor: 'pointer',
                color: 'var(--color-text-secondary)',
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Body */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '12px' }}>
        {loading && (
          <p style={{ fontSize: '12px', color: 'var(--color-text-tertiary)', textAlign: 'center', padding: '24px' }}>
            Loading memories...
          </p>
        )}
        {error && (
          <p style={{ fontSize: '12px', color: '#a32d2d', padding: '12px' }}>{error}</p>
        )}

        {memories && !loading && (
          Object.entries(TYPE_CONFIG).map(([type, cfg]) => {
            const entries = memories[type as keyof MemoryGroups] || []
            return (
              <div key={type} style={{ marginBottom: '16px' }}>
                {/* Section header */}
                <div style={{
                  display: 'flex', alignItems: 'center', gap: '6px',
                  marginBottom: '8px',
                }}>
                  <span style={{ fontSize: '14px' }}>{cfg.icon}</span>
                  <span style={{
                    fontSize: '11px', fontWeight: 500,
                    padding: '2px 8px', borderRadius: '20px',
                    background: cfg.color, color: cfg.text,
                  }}>
                    {cfg.label}
                  </span>
                  <span style={{ fontSize: '10px', color: 'var(--color-text-tertiary)' }}>
                    {entries.length}
                  </span>
                </div>

                {entries.length === 0 ? (
                  <p style={{ fontSize: '11px', color: 'var(--color-text-tertiary)', paddingLeft: '8px' }}>
                    No memories yet
                  </p>
                ) : (
                  entries.map((mem) => (
                    <div key={mem.id} style={{
                      padding: '8px 10px', marginBottom: '6px',
                      background: 'var(--color-background-secondary)',
                      borderRadius: '8px',
                      border: '0.5px solid var(--color-border-tertiary)',
                      display: 'flex', alignItems: 'flex-start', gap: '8px',
                    }}>
                      <p style={{
                        flex: 1, margin: 0,
                        fontSize: '12px', color: 'var(--color-text-secondary)',
                        lineHeight: 1.5,
                      }}>
                        {mem.content}
                      </p>
                      <button
                        onClick={() => deleteMemory(mem.id)}
                        disabled={deleting === mem.id}
                        style={{
                          background: 'none', border: 'none',
                          color: 'var(--color-text-tertiary)',
                          cursor: 'pointer', fontSize: '14px',
                          lineHeight: 1, padding: '0 2px', flexShrink: 0,
                          opacity: deleting === mem.id ? 0.4 : 1,
                        }}
                        title="Delete this memory"
                      >
                        ×
                      </button>
                    </div>
                  ))
                )}
              </div>
            )
          })
        )}
      </div>

      {/* Footer */}
      <div style={{
        padding: '12px 16px',
        borderTop: '0.5px solid var(--color-border-tertiary)',
        fontSize: '11px', color: 'var(--color-text-tertiary)',
      }}>
        <button
          onClick={fetchMemories}
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--color-text-tertiary)', fontSize: '11px',
            padding: 0, textDecoration: 'underline',
          }}
        >
          Refresh
        </button>
        {' · '}
        Memories update after each session
      </div>
    </div>
  )
}