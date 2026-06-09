// frontend/src/components/BrowserView.tsx
/**
 * Displays browser screenshots streamed from the Playwright agent.
 * Shows as a side panel when the browser agent is active.
 */
import React, { useState, useEffect } from 'react'

interface Screenshot {
  data:        string   // base64 PNG
  description: string
  timestamp:   number
}

interface Props {
  screenshots: Screenshot[]
  isActive:    boolean
  finalUrl:    string
}

export default function BrowserView({ screenshots, isActive, finalUrl }: Props) {
  const [currentIdx, setCurrentIdx] = useState(0)
  const [isExpanded, setIsExpanded] = useState(true)


  // Auto-scroll to latest screenshot
  useEffect(() => {
    if (screenshots.length > 0) {
      setCurrentIdx(screenshots.length - 1)
    }
  }, [screenshots.length])

  if (screenshots.length === 0 && !isActive) return null

  const current = screenshots[currentIdx]

  return (
    <div style={{
      border: '0.5px solid var(--color-border-tertiary)',
      borderRadius: '12px',
      background: 'var(--color-background-primary)',
      overflow: 'hidden',
      margin: '8px 0',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '8px',
        padding: '10px 14px',
        background: 'var(--color-background-secondary)',
        borderBottom: '0.5px solid var(--color-border-tertiary)',
        cursor: 'pointer',
      }}
        onClick={() => setIsExpanded(e => !e)}
      >
        {/* Browser icon */}
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
             stroke="var(--color-text-tertiary)" strokeWidth="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="2" y1="12" x2="22" y2="12"/>
          <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
        </svg>
        <span style={{
          fontSize: '12px', fontWeight: 500,
          color: 'var(--color-text-primary)', flex: 1,
        }}>
          Browser Agent
          {isActive && (
            <span style={{
              marginLeft: '6px', fontSize: '10px',
              padding: '2px 7px', borderRadius: '20px',
              background: '#c8f0dc', color: '#1a6b4a',
            }}>
              LIVE
            </span>
          )}
        </span>
        {finalUrl && (
          <span style={{
            fontSize: '10px', color: 'var(--color-text-tertiary)',
            fontFamily: 'var(--font-mono)',
            maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}>
            {finalUrl}
          </span>
        )}
        <span style={{
          fontSize: '11px', color: 'var(--color-text-tertiary)',
        }}>
          {isExpanded ? '▲' : '▼'}
        </span>
      </div>

      {isExpanded && (
        <>
          {/* Screenshot display */}
          {current ? (
            <div style={{ position: 'relative' }}>
              <img
                src={`data:image/png;base64,${current.data}`}
                alt={current.description}
                style={{
                  width: '100%', display: 'block',
                  maxHeight: '400px', objectFit: 'contain',
                  background: '#f8f8f8',
                }}
              />
              {/* Description overlay */}
              <div style={{
                position: 'absolute', bottom: 0, left: 0, right: 0,
                padding: '6px 12px',
                background: 'rgba(0,0,0,0.6)',
                fontSize: '11px', color: '#fff',
              }}>
                {current.description}
              </div>
            </div>
          ) : (
            <div style={{
              height: '200px', display: 'flex', alignItems: 'center',
              justifyContent: 'center',
              background: 'var(--color-background-secondary)',
            }}>
              {isActive ? (
                <p style={{ fontSize: '12px', color: 'var(--color-text-tertiary)' }}>
                  Browser loading...
                </p>
              ) : (
                <p style={{ fontSize: '12px', color: 'var(--color-text-tertiary)' }}>
                  No screenshots yet
                </p>
              )}
            </div>
          )}

          {/* Screenshot timeline */}
          {screenshots.length > 1 && (
            <div style={{
              display: 'flex', gap: '4px', padding: '8px 12px',
              overflowX: 'auto',
              borderTop: '0.5px solid var(--color-border-tertiary)',
              background: 'var(--color-background-secondary)',
            }}>
              {screenshots.map((ss, i) => (
                <button
                  key={i}
                  onClick={() => setCurrentIdx(i)}
                  style={{
                    flexShrink: 0, padding: 0, border: 'none',
                    borderRadius: '4px', cursor: 'pointer',
                    outline: currentIdx === i ? '2px solid #534AB7' : 'none',
                    overflow: 'hidden',
                  }}
                >
                  <img
                    src={`data:image/png;base64,${ss.data}`}
                    alt={`step ${i+1}`}
                    style={{ width: '64px', height: '40px', objectFit: 'cover', display: 'block' }}
                  />
                </button>
              ))}
            </div>
          )}

          {/* Actions counter */}
          {screenshots.length > 0 && (
            <div style={{
              padding: '6px 12px',
              fontSize: '10px', color: 'var(--color-text-tertiary)',
              borderTop: '0.5px solid var(--color-border-tertiary)',
              display: 'flex', gap: '12px',
            }}>
              <span>{screenshots.length} screenshots captured</span>
              <span>Step {currentIdx + 1} of {screenshots.length}</span>
            </div>
          )}
        </>
      )}
    </div>
  )
}