// FIXED: Removed duplicate Phase original/B/E definitions — Phase L is canonical
// FIXED: Replaced `any` with explicit types in code component props
import React, { memo }      from 'react'
import ReactMarkdown         from 'react-markdown'
import remarkGfm             from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark }           from 'react-syntax-highlighter/dist/esm/styles/prism'
import { Message }           from '../types'
import SourceCard            from './SourceCard'
import StreamingDot          from './StreamingDot'
import ReflectionBadge       from './ReflectionBadge'
import GuardBadge            from './GuardBadge'
import ReasoningSteps        from './ReasoningSteps'
import WorkerStatusBar       from './WorkerStatusBar'
import BrowserView           from './BrowserView'

interface Props {
  message:    Message
  onFeedback: (traceId: string, score: number, abLogId?: number) => void
  onBranch?:  (messageId: string) => void
}

function detectMimeType(b64: string): string {
  try {
    const h = atob(b64.slice(0, 16))
    if (h.startsWith('\x89PNG'))               return 'image/png'
    if (h.startsWith('GIF87') || h.startsWith('GIF89')) return 'image/gif'
    if (h.startsWith('RIFF'))                  return 'image/webp'
  } catch {} // FIXED: swallowed intentionally — fall through to jpeg
  return 'image/jpeg'
}

// FIXED: Replaced `any` with specific ReactMarkdown code component prop types
interface CodeProps {
  node?: unknown
  inline?: boolean
  className?: string
  children?: React.ReactNode
}

function MessageBubble({ message, onFeedback, onBranch }: Props) {
  const isHuman = message.role === 'human'

  return (
    <div style={{
      display: 'flex', width: '100%', marginBottom: '16px',
      justifyContent: isHuman ? 'flex-end' : 'flex-start',
    }}>
      <div style={{ maxWidth: '82%' }}>
        <div style={{
          display: 'flex', alignItems: 'flex-end', gap: '8px',
          flexDirection: isHuman ? 'row-reverse' : 'row',
        }}>
          {/* Avatar */}
          <div style={{
            width: '28px', height: '28px', borderRadius: '50%', flexShrink: 0,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '11px', fontWeight: 600,
            background: isHuman ? '#534AB7' : 'var(--color-background-secondary)',
            color:      isHuman ? '#fff'     : 'var(--color-text-secondary)',
          }}>
            {isHuman ? 'U' : 'A'}
          </div>

          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '4px' }}>

            {/* Phase L: Reasoning steps (AI only, while streaming or after) */}
            {!isHuman && (message.agentSteps?.length ?? 0) > 0 && (
              <ReasoningSteps
                steps={message.agentSteps || []}
                isStreaming={message.isStreaming}
              />
            )}

            {/* Phase L: Worker status bar */}
            {!isHuman && (
              <WorkerStatusBar
                workers={message.workersUsed || []}
                isStreaming={message.isStreaming}
              />
            )}

            {/* Image preview */}
            {message.imageData && (
              <img
                src={`data:${detectMimeType(message.imageData)};base64,${message.imageData}`}
                alt="uploaded"
                style={{ maxWidth: '280px', maxHeight: '200px', borderRadius: '12px',
                         objectFit: 'cover', border: '0.5px solid var(--color-border-tertiary)' }}
              />
            )}

            {/* Message bubble */}
            <div style={{
              borderRadius: isHuman ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
              padding: '12px 16px', fontSize: '13px', lineHeight: 1.6,
              background: isHuman
                ? '#534AB7'
                : message.error ? '#fef2f2' : 'var(--color-background-primary)',
              color: isHuman
                ? '#fff'
                : message.error ? '#dc2626' : 'var(--color-text-primary)',
              border: isHuman ? 'none' : `0.5px solid ${message.error ? '#fca5a5' : 'var(--color-border-tertiary)'}`,
            }}>
              {isHuman ? (
                <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{message.content}</p>
              ) : (
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    code({ inline, className, children, ...props }: CodeProps) { // FIXED: removed `node` and `any`
                      const match = /language-(\w+)/.exec(className || '')
                      return !inline && match ? (
                        <SyntaxHighlighter style={oneDark} language={match[1]} PreTag="div"
                          className="rounded-lg text-xs my-2" {...props}>
                          {String(children).replace(/\n$/, '')}
                        </SyntaxHighlighter>
                      ) : (
                        <code style={{
                          background: 'var(--color-background-secondary)',
                          borderRadius: '4px', padding: '1px 5px', fontSize: '12px',
                        }} {...props}>
                          {children}
                        </code>
                      )
                    },
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              )}
              {message.isStreaming && <StreamingDot />}
            </div>

            {/* Browser view (Phase I) */}
            {!isHuman && (message.browserScreenshots?.length ?? 0) > 0 && (
              <BrowserView
                screenshots={message.browserScreenshots || []}
                isActive={message.isStreaming}
                finalUrl={message.browserFinalUrl || ''}
              />
            )}

            {/* Footer: sources, badges, feedback, branch */}
            {!isHuman && !message.isStreaming && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>

                {/* Sources */}
                {message.sources.length > 0 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                    {message.sources.map((src, i) => (
                      <SourceCard key={i} index={i + 1} source={src} />
                    ))}
                  </div>
                )}

                {/* Reflection badge */}
                {(message.reflectionHistory?.length ?? 0) > 0 && (
                  <ReflectionBadge
                    score={message.reflectionScore ?? 0}
                    attempts={message.reflectionAttempts ?? 0}
                    history={message.reflectionHistory || []}
                  />
                )}

                {/* Guard badge */}
                <GuardBadge
                  inputFlag={message.guardInputFlag}
                  outputFlag={message.guardOutputFlag}
                  piiMasked={message.piiMasked}
                  hallucination={message.hallucinationFlag}
                />

                {/* Metadata row */}
                <div style={{
                  display: 'flex', alignItems: 'center', gap: '8px',
                  fontSize: '11px', color: 'var(--color-text-tertiary)',
                }}>
                  {message.model && (
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px' }}>
                      {message.model}
                    </span>
                  )}
                  {message.intent && (
                    <span style={{
                      padding: '1px 6px', borderRadius: '20px', fontSize: '10px',
                      background: 'var(--color-background-secondary)',
                    }}>
                      {message.intent}
                    </span>
                  )}

                  <div style={{ marginLeft: 'auto', display: 'flex', gap: '4px' }}>
                    {/* Branch button */}
                    {onBranch && (
                      <button
                        onClick={() => onBranch(message.id)}
                        title="Fork conversation from here"
                        style={{
                          background: 'none', border: 'none', cursor: 'pointer',
                          padding: '2px 6px', borderRadius: '4px', fontSize: '12px',
                          color: 'var(--color-text-tertiary)',
                        }}
                        onMouseEnter={e => (e.currentTarget.style.color = '#534AB7')}
                        onMouseLeave={e => (e.currentTarget.style.color = 'var(--color-text-tertiary)')}
                      >
                        ⎇
                      </button>
                    )}

                    {/* Feedback */}
                    {message.traceId && (
                      <>
                        <button
                          onClick={() => onFeedback(message.traceId, 1.0, message.abLogEntryId)}
                          style={{
                            background: 'none', border: 'none', cursor: 'pointer',
                            padding: '2px 4px', fontSize: '13px',
                            color: 'var(--color-text-tertiary)',
                          }}
                          title="Good response"
                          onMouseEnter={e => (e.currentTarget.style.color = '#22c55e')}
                          onMouseLeave={e => (e.currentTarget.style.color = 'var(--color-text-tertiary)')}
                        >
                          ↑
                        </button>
                        <button
                          onClick={() => onFeedback(message.traceId, 0.0, message.abLogEntryId)}
                          style={{
                            background: 'none', border: 'none', cursor: 'pointer',
                            padding: '2px 4px', fontSize: '13px',
                            color: 'var(--color-text-tertiary)',
                          }}
                          title="Bad response"
                          onMouseEnter={e => (e.currentTarget.style.color = '#ef4444')}
                          onMouseLeave={e => (e.currentTarget.style.color = 'var(--color-text-tertiary)')}
                        >
                          ↓
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default memo(MessageBubble)
