// frontend/src/components/MCPStatusBadge.tsx
/**
 * Shows MCP server connection status in the header.
 * Clicking opens the tool list.
 */
import React, { useState, useEffect } from 'react'

interface MCPTool {
  name:        string
  description: string
}

const API_BASE   = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
const MCP_BASE   = API_BASE.replace('/api', '/mcp')
const authHeader = () => ({ Authorization: `Bearer ${sessionStorage.getItem('aaa_token') || 'dev'}` })

export default function MCPStatusBadge() {
  const [tools,   setTools]   = useState<MCPTool[]>([])
  const [isOpen,  setIsOpen]  = useState(false)
  const [status,  setStatus]  = useState<'loading' | 'ok' | 'error'>('loading')

  useEffect(() => {
    fetch(`${MCP_BASE}/tools`, { headers: authHeader() })
      .then(r => r.json())
      .then(data => {
        setTools(data.tools || [])
        setStatus('ok')
      })
      .catch(() => setStatus('error'))
  }, [])

  const statusColor = status === 'ok' ? '#22c55e' : status === 'error' ? '#ef4444' : '#eab308'

  return (
    <div style={{ position: 'relative' }}>
      <button
        onClick={() => setIsOpen(o => !o)}
        style={{
          display: 'flex', alignItems: 'center', gap: '5px',
          padding: '4px 9px', borderRadius: '20px', border: 'none',
          background: 'var(--color-background-secondary)',
          cursor: 'pointer', fontSize: '11px', fontWeight: 500,
          color: 'var(--color-text-secondary)',
        }}
        title="MCP Server status"
      >
        {/* MCP icon */}
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" strokeWidth="2">
          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
        </svg>
        <span>MCP</span>
        <span style={{
          width: '6px', height: '6px', borderRadius: '50%',
          background: statusColor, flexShrink: 0,
        }} />
        {status === 'ok' && (
          <span style={{ color: 'var(--color-text-tertiary)' }}>
            {tools.length}
          </span>
        )}
      </button>

      {/* Tool list dropdown */}
      {isOpen && (
        <div style={{
          position: 'absolute', right: 0, top: '100%', marginTop: '4px',
          width: '320px', zIndex: 100,
          background: 'var(--color-background-primary)',
          border: '0.5px solid var(--color-border-tertiary)',
          borderRadius: '12px', boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
          overflow: 'hidden',
        }}>
          <div style={{
            padding: '12px 14px',
            borderBottom: '0.5px solid var(--color-border-tertiary)',
            display: 'flex', alignItems: 'center', gap: '8px',
          }}>
            <p style={{ fontSize: '12px', fontWeight: 500, margin: 0, flex: 1,
                        color: 'var(--color-text-primary)' }}>
              MCP Tools
            </p>
            <span style={{
              fontSize: '10px', padding: '2px 7px', borderRadius: '20px',
              background: '#c8f0dc', color: '#1a6b4a', fontWeight: 500,
            }}>
              {tools.length} available
            </span>
          </div>

          <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
            {status === 'error' ? (
              <p style={{ padding: '16px', fontSize: '12px', color: '#a32d2d' }}>
                MCP server unavailable
              </p>
            ) : (
              tools.map(tool => (
                <div key={tool.name} style={{
                  padding: '10px 14px',
                  borderBottom: '0.5px solid var(--color-border-tertiary)',
                }}>
                  <p style={{
                    fontSize: '11px', fontWeight: 500, margin: '0 0 2px',
                    fontFamily: 'var(--font-mono)',
                    color: '#534AB7',
                  }}>
                    {tool.name}
                  </p>
                  <p style={{
                    fontSize: '11px', margin: 0,
                    color: 'var(--color-text-tertiary)',
                    lineHeight: 1.4,
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden',
                  }}>
                    {tool.description}
                  </p>
                </div>
              ))
            )}
          </div>

          <div style={{
            padding: '10px 14px',
            borderTop: '0.5px solid var(--color-border-tertiary)',
            fontSize: '10px', color: 'var(--color-text-tertiary)',
          }}>
            Connect via Claude Desktop · Cursor · any MCP client
            <br />
            Endpoint: <code style={{ fontSize: '10px' }}>{MCP_BASE}</code>
          </div>
        </div>
      )}
    </div>
  )
}