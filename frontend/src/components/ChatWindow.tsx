// FIXED: Removed duplicate Phase original definition — Phase I is canonical
import React, { useEffect, useRef } from 'react'
import { useChatStore }   from '../store/chatStore'
import MessageBubble      from './MessageBubble'
import BrowserView        from './BrowserView'
import { submitFeedback } from '../lib/api'

export default function ChatWindow() {
  const messages  = useChatStore((s) => s.messages)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.at(-1)?.content])

  const handleFeedback = async (traceId: string, score: number) => {
    await submitFeedback(traceId, score)
  }

  if (messages.length === 0) {
    return (
      <div style={{
        flex: 1, display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        color: 'var(--color-text-tertiary)',
      }}>
        <div style={{
          width: '64px', height: '64px', borderRadius: '16px',
          background: '#EEEDFE',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          marginBottom: '16px',
        }}>
          <span style={{ fontSize: '28px' }}>⚡</span>
        </div>
        <p style={{ fontSize: '15px', fontWeight: 500, color: 'var(--color-text-secondary)' }}>
          AI Agentic Assistant v2
        </p>
        <p style={{ fontSize: '13px', marginTop: '4px' }}>
          Chat · Code · Vision · Browser · Voice
        </p>
      </div>
    )
  }

  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: '16px 16px 8px' }}>
      {messages.map((msg) => (
        <React.Fragment key={msg.id}>
          <MessageBubble message={msg} onFeedback={handleFeedback} />

          {/* Show browser screenshots for AI messages that used browser */}
          {msg.role === 'ai' && msg.browserScreenshots && msg.browserScreenshots.length > 0 && (
            <div style={{ marginTop: '-8px', marginBottom: '16px', paddingLeft: '36px' }}>
              <BrowserView
                screenshots={msg.browserScreenshots}
                isActive={msg.isStreaming || false}
                finalUrl={msg.browserFinalUrl || ''}
              />
            </div>
          )}
        </React.Fragment>
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
