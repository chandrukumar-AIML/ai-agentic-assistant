// frontend/src/components/admin/PromptEditor.tsx
import React, { useState, useEffect, useCallback } from 'react'

interface PromptVersion {
  id:                number
  version:           string
  is_active:         boolean
  performance_score: number
  query_count:       number
  thumbs_up:         number
  thumbs_down:       number
  description:       string
  created_at:        string
  content_preview:   string
}

interface PromptsData {
  [promptName: string]: PromptVersion[]
}

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
const authHeader = () => ({ Authorization: `Bearer ${sessionStorage.getItem('aaa_token') || 'dev'}` })

export default function PromptEditor() {
  const [prompts,     setPrompts]     = useState<PromptsData>({})
  const [selected,    setSelected]    = useState<string | null>(null)
  const [loading,     setLoading]     = useState(true)
  const [editContent, setEditContent] = useState('')
  const [newVersion,  setNewVersion]  = useState('')
  const [description, setDescription] = useState('')
  const [saving,      setSaving]      = useState(false)
  const [message,     setMessage]     = useState<{text: string; ok: boolean} | null>(null)

  const fetchPrompts = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/prompts`, { headers: authHeader() })
      const data = await res.json()
      setPrompts(data)
      if (!selected && Object.keys(data).length > 0) {
        setSelected(Object.keys(data)[0])
      }
    } catch (e) {
      void e // FIXED: removed console.error production log
    } finally {
      setLoading(false)
    }
  }, [selected])

  useEffect(() => { fetchPrompts() }, [fetchPrompts]) // FIXED: stale closure — added fetchPrompts to dep array

  const handleActivate = async (promptName: string, versionId: number) => {
    try { // FIXED: unhandled Promise rejection — wrapped in try/catch
      await fetch(
        `${API_BASE}/prompts/${promptName}/activate/${versionId}`,
        { method: 'POST', headers: authHeader() }
      )
      setMessage({ text: 'Version activated', ok: true })
      await fetchPrompts()
    } catch {
      setMessage({ text: 'Activation failed', ok: false })
    }
    setTimeout(() => setMessage(null), 3000)
  }

  const handleSaveNew = async () => {
    if (!selected || !editContent || !newVersion) return
    setSaving(true)
    try {
      const res = await fetch(
        `${API_BASE}/prompts/${selected}?content=${encodeURIComponent(editContent)}&version=${newVersion}&description=${encodeURIComponent(description)}`,
        { method: 'POST', headers: authHeader() }
      )
      if (res.ok) {
        setMessage({ text: `Version ${newVersion} created`, ok: true })
        setNewVersion('')
        setDescription('')
        await fetchPrompts()
      } else {
        setMessage({ text: 'Save failed', ok: false })
      }
    } finally {
      setSaving(false)
      setTimeout(() => setMessage(null), 3000)
    }
  }

  const selectedVersions = selected ? (prompts[selected] || []) : []
  const activeVersion    = selectedVersions.find(v => v.is_active)

  return (
    <div style={{ display: 'flex', height: '100%', gap: '0' }}>

      {/* Sidebar — prompt list */}
      <div style={{
        width: '200px', flexShrink: 0,
        borderRight: '0.5px solid var(--color-border-tertiary)',
        background: 'var(--color-background-secondary)',
        padding: '12px 0',
      }}>
        <p style={{
          fontSize: '10px', fontWeight: 500, letterSpacing: '0.08em',
          textTransform: 'uppercase', color: 'var(--color-text-tertiary)',
          padding: '0 12px', marginBottom: '8px',
        }}>
          Prompts
        </p>
        {loading ? (
          <p style={{ padding: '12px', fontSize: '12px', color: 'var(--color-text-tertiary)' }}>
            Loading...
          </p>
        ) : (
          Object.keys(prompts).map(name => (
            <button
              key={name}
              onClick={() => setSelected(name)}
              style={{
                width: '100%', padding: '8px 12px', textAlign: 'left',
                background: selected === name ? 'var(--color-background-primary)' : 'none',
                border: 'none', cursor: 'pointer',
                fontSize: '12px', fontWeight: selected === name ? 500 : 400,
                color: selected === name ? 'var(--color-text-primary)' : 'var(--color-text-secondary)',
                borderLeft: selected === name ? '2px solid #534AB7' : '2px solid transparent',
              }}
            >
              {name}
              <span style={{
                marginLeft: '6px', fontSize: '10px',
                color: 'var(--color-text-tertiary)',
              }}>
                v{prompts[name]?.find(v => v.is_active)?.version || '?'}
              </span>
            </button>
          ))
        )}
      </div>

      {/* Main area */}
      <div style={{ flex: 1, padding: '20px', overflowY: 'auto' }}>
        {message && (
          <div style={{
            marginBottom: '12px', padding: '8px 12px', borderRadius: '8px',
            background: message.ok ? '#f0fdf4' : '#fef2f2',
            color: message.ok ? '#166534' : '#991b1b',
            fontSize: '12px', fontWeight: 500,
          }}>
            {message.ok ? '✓' : '✗'} {message.text}
          </div>
        )}

        {selected && (
          <>
            <div style={{ marginBottom: '20px' }}>
              <h3 style={{
                fontSize: '14px', fontWeight: 500, marginBottom: '4px',
                color: 'var(--color-text-primary)',
              }}>
                {selected}
              </h3>
              {activeVersion && (
                <p style={{ fontSize: '11px', color: 'var(--color-text-tertiary)' }}>
                  Active: v{activeVersion.version} ·
                  Score: {(activeVersion.performance_score * 100).toFixed(1)}% ·
                  {activeVersion.query_count} queries ·
                  👍 {activeVersion.thumbs_up} 👎 {activeVersion.thumbs_down}
                </p>
              )}
            </div>

            {/* Version history */}
            <div style={{ marginBottom: '24px' }}>
              <p style={{
                fontSize: '11px', fontWeight: 500, color: 'var(--color-text-tertiary)',
                marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.06em',
              }}>
                Version History
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {selectedVersions.map(v => (
                  <div key={v.id} style={{
                    padding: '10px 12px',
                    background: v.is_active
                      ? '#EEEDFE'
                      : 'var(--color-background-secondary)',
                    borderRadius: '8px',
                    border: `0.5px solid ${v.is_active ? '#534AB7' : 'var(--color-border-tertiary)'}`,
                    display: 'flex', alignItems: 'center', gap: '10px',
                  }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{
                          fontSize: '12px', fontWeight: 500,
                          color: v.is_active ? '#534AB7' : 'var(--color-text-primary)',
                        }}>
                          v{v.version}
                        </span>
                        {v.is_active && (
                          <span style={{
                            fontSize: '10px', padding: '1px 6px', borderRadius: '20px',
                            background: '#534AB7', color: '#fff',
                          }}>
                            ACTIVE
                          </span>
                        )}
                        <span style={{ fontSize: '11px', color: 'var(--color-text-tertiary)' }}>
                          {(v.performance_score * 100).toFixed(0)}% · {v.query_count} queries
                        </span>
                      </div>
                      <p style={{
                        fontSize: '11px', color: 'var(--color-text-tertiary)',
                        margin: '2px 0 4px',
                      }}>
                        {v.description || 'No description'}
                      </p>
                      <p style={{
                        fontSize: '11px', color: 'var(--color-text-secondary)',
                        fontFamily: 'var(--font-mono)', lineHeight: 1.4,
                        whiteSpace: 'pre-wrap',
                      }}>
                        {v.content_preview}
                      </p>
                    </div>
                    {!v.is_active && (
                      <button
                        onClick={() => handleActivate(selected, v.id)}
                        style={{
                          padding: '5px 10px', fontSize: '11px', fontWeight: 500,
                          background: 'var(--color-background-primary)',
                          border: '0.5px solid var(--color-border-tertiary)',
                          borderRadius: '6px', cursor: 'pointer',
                          color: 'var(--color-text-secondary)',
                          flexShrink: 0,
                        }}
                      >
                        Activate
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* New version editor */}
            <div style={{
              padding: '16px',
              background: 'var(--color-background-secondary)',
              borderRadius: '12px',
              border: '0.5px solid var(--color-border-tertiary)',
            }}>
              <p style={{
                fontSize: '12px', fontWeight: 500, marginBottom: '12px',
                color: 'var(--color-text-primary)',
              }}>
                Create New Version
              </p>
              <div style={{ display: 'flex', gap: '8px', marginBottom: '10px' }}>
                <input
                  placeholder="Version (e.g. 1.2.0)"
                  value={newVersion}
                  onChange={e => setNewVersion(e.target.value)}
                  style={{
                    flex: 1, padding: '7px 10px', borderRadius: '6px', fontSize: '12px',
                    border: '0.5px solid var(--color-border-tertiary)',
                    background: 'var(--color-background-primary)',
                    color: 'var(--color-text-primary)', outline: 'none',
                  }}
                />
                <input
                  placeholder="Description"
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  style={{
                    flex: 2, padding: '7px 10px', borderRadius: '6px', fontSize: '12px',
                    border: '0.5px solid var(--color-border-tertiary)',
                    background: 'var(--color-background-primary)',
                    color: 'var(--color-text-primary)', outline: 'none',
                  }}
                />
              </div>
              <textarea
                value={editContent}
                onChange={e => setEditContent(e.target.value)}
                placeholder={activeVersion?.content_preview || 'Enter prompt content...'}
                rows={10}
                style={{
                  width: '100%', padding: '10px', borderRadius: '8px', fontSize: '12px',
                  fontFamily: 'var(--font-mono)', lineHeight: 1.6,
                  border: '0.5px solid var(--color-border-tertiary)',
                  background: 'var(--color-background-primary)',
                  color: 'var(--color-text-primary)', outline: 'none',
                  resize: 'vertical', boxSizing: 'border-box',
                }}
              />
              <div style={{ display: 'flex', gap: '8px', marginTop: '10px' }}>
                <button
                  onClick={handleSaveNew}
                  disabled={saving || !editContent || !newVersion}
                  style={{
                    padding: '7px 14px', fontSize: '12px', fontWeight: 500,
                    background: '#534AB7', color: '#fff', border: 'none',
                    borderRadius: '6px', cursor: 'pointer', opacity: saving ? 0.6 : 1,
                  }}
                >
                  {saving ? 'Saving...' : 'Save Version'}
                </button>
                <button
                  onClick={() => setEditContent(activeVersion?.content_preview || '')}
                  style={{
                    padding: '7px 14px', fontSize: '12px',
                    background: 'var(--color-background-primary)',
                    border: '0.5px solid var(--color-border-tertiary)',
                    borderRadius: '6px', cursor: 'pointer',
                    color: 'var(--color-text-secondary)',
                  }}
                >
                  Load active version
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}