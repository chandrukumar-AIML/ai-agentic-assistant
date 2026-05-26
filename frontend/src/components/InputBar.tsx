// FIXED: Removed duplicate Phase original definition — Phase D is canonical
import React, { useState, useRef, useCallback, KeyboardEvent, ChangeEvent } from 'react'
import { UploadedImage } from '../types'
import VoiceButton       from './VoiceButton'
import { useVoice, VoiceState } from '../hooks/useVoice'

const MAX_IMAGE_BYTES = 20 * 1024 * 1024

interface Props {
  onSend:         (content: string, image?: UploadedImage) => void
  onSendAudio:    (audioB64: string, durationMs: number) => void
  onAudioChunk:   (chunkB64: string, chunkIdx: number) => void
  onTranscript:   (text: string, confidence: number) => void
  onTTSDone:      () => void
  disabled:       boolean
  status:         string
  isVoiceMode:    boolean
  onToggleVoice:  () => void
}

export default function InputBar({
  onSend, onSendAudio, onAudioChunk, onTranscript, onTTSDone,
  disabled, status, isVoiceMode, onToggleVoice,
}: Props) {
  const [text,     setText]    = useState('')
  const [preview,  setPreview] = useState<UploadedImage | null>(null)
  const [imgError, setImgError] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)
  const textRef = useRef<HTMLTextAreaElement>(null)

  const {
    state:       voiceState,
    transcript,
    duration,
    audioLevel,
    startRecording,
    stopRecording,
    enqueueAudioChunk,
    handleTranscript: handleVoiceTranscript,
    reset:       resetVoice,
  } = useVoice({
    onSendAudio,
    onAudioChunk,
    onTranscript: (text, conf) => {
      handleVoiceTranscript(text, conf)
      onTranscript(text, conf)
    },
    onTTSDone: () => {
      resetVoice()
      onTTSDone()
    },
  })

  const handleFileChange = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (file.size > MAX_IMAGE_BYTES) {
      setImgError(`Too large (${(file.size/1024/1024).toFixed(1)}MB). Max 20MB.`)
      e.target.value = ''
      return
    }
    setImgError(null)
    const objectURL = URL.createObjectURL(file)
    const reader    = new FileReader()
    reader.onload   = () => {
      const base64 = (reader.result as string).split(',')[1]
      setPreview({ file, preview: objectURL, base64 })
    }
    reader.readAsDataURL(file)
    e.target.value = ''
  }, [])

  const removeImage = useCallback(() => {
    if (preview) URL.revokeObjectURL(preview.preview)
    setPreview(null)
    setImgError(null)
  }, [preview])

  const handleSend = useCallback(() => {
    const trimmed = text.trim()
    if (!trimmed && !preview) return
    if (disabled) return
    onSend(trimmed || 'Analyse this image.', preview ?? undefined)
    setText('')
    if (preview) { URL.revokeObjectURL(preview.preview); setPreview(null) }
    textRef.current?.focus()
  }, [text, preview, disabled, onSend])

  const handleKeyDown = useCallback((e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }, [handleSend])

  const handleTextChange = useCallback((e: ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px'
  }, [])

  const isStreaming = status === 'streaming'
  const canSend     = (text.trim() || preview) && !disabled && !isStreaming

  // ── Voice mode UI ────────────────────────────────────────────────────────
  if (isVoiceMode) {
    return (
      <div style={{
        borderTop: '0.5px solid var(--color-border-tertiary)',
        background: 'var(--color-background-primary)',
        padding: '16px',
        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px',
      }}>
        <VoiceButton
          voiceState={voiceState}
          audioLevel={audioLevel}
          transcript={transcript}
          duration={duration}
          onStart={startRecording}
          onStop={stopRecording}
          disabled={disabled || isStreaming}
        />

        {/* Switch to text mode */}
        <button
          onClick={onToggleVoice}
          style={{
            fontSize: '11px', color: 'var(--color-text-tertiary)',
            background: 'none', border: 'none', cursor: 'pointer',
            textDecoration: 'underline',
          }}
        >
          Switch to text mode
        </button>
      </div>
    )
  }

  // ── Text mode UI ─────────────────────────────────────────────────────────
  return (
    <div style={{
      borderTop: '0.5px solid var(--color-border-tertiary)',
      background: 'var(--color-background-primary)',
      padding: '12px 16px',
    }}>
      {imgError && (
        <p style={{ fontSize: '11px', color: '#ef4444', marginBottom: '8px' }}>{imgError}</p>
      )}

      {preview && (
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: '8px',
          background: 'var(--color-background-secondary)',
          borderRadius: '8px', padding: '8px 12px',
          border: '0.5px solid var(--color-border-tertiary)',
          marginBottom: '8px',
        }}>
          <img src={preview.preview} alt="preview"
               style={{ width: '40px', height: '40px', borderRadius: '6px', objectFit: 'cover' }} />
          <span style={{ fontSize: '11px', color: 'var(--color-text-tertiary)',
                         maxWidth: '120px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {preview.file.name}
          </span>
          <button onClick={removeImage}
                  style={{ background: 'none', border: 'none', cursor: 'pointer',
                           color: 'var(--color-text-tertiary)', fontSize: '14px' }}>✕</button>
        </div>
      )}

      <div style={{ display: 'flex', alignItems: 'flex-end', gap: '8px' }}>
        {/* Attach image */}
        <button onClick={() => fileRef.current?.click()}
                disabled={disabled || isStreaming}
                style={{
                  width: '36px', height: '36px', borderRadius: '8px', border: 'none',
                  background: 'none', cursor: 'pointer',
                  color: 'var(--color-text-tertiary)', flexShrink: 0,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  opacity: disabled ? 0.4 : 1,
                }}
                title="Attach image">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48"/>
          </svg>
        </button>
        <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/gif,image/webp"
               onChange={handleFileChange} style={{ display: 'none' }} />

        {/* Text area */}
        <textarea
          ref={textRef} value={text} onChange={handleTextChange} onKeyDown={handleKeyDown}
          disabled={disabled || isStreaming}
          aria-label="Message input"
          placeholder={isStreaming ? 'Waiting...' : 'Ask anything... (Shift+Enter for newline)'}
          rows={1}
          style={{
            flex: 1, resize: 'none', borderRadius: '12px',
            border: '0.5px solid var(--color-border-tertiary)',
            background: 'var(--color-background-secondary)',
            padding: '10px 14px', fontSize: '13px',
            color: 'var(--color-text-primary)',
            outline: 'none', maxHeight: '200px',
            fontFamily: 'inherit', lineHeight: 1.5,
            opacity: disabled ? 0.5 : 1,
          }}
        />

        {/* Voice toggle button */}
        <button onClick={onToggleVoice}
                disabled={disabled}
                title="Switch to voice mode"
                style={{
                  width: '36px', height: '36px', borderRadius: '8px', border: 'none',
                  background: 'none', cursor: 'pointer',
                  color: 'var(--color-text-tertiary)', flexShrink: 0,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  opacity: disabled ? 0.4 : 1,
                }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
            <line x1="12" y1="19" x2="12" y2="23"/>
            <line x1="8"  y1="23" x2="16" y2="23"/>
          </svg>
        </button>

        {/* Send button */}
        <button onClick={handleSend} disabled={!canSend}
                style={{
                  width: '36px', height: '36px', borderRadius: '10px',
                  background: canSend ? '#534AB7' : 'var(--color-background-secondary)',
                  border: 'none', cursor: canSend ? 'pointer' : 'not-allowed',
                  color: canSend ? '#fff' : 'var(--color-text-tertiary)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0, transition: 'all 0.2s',
                  opacity: !canSend ? 0.4 : 1,
                }}>
          {isStreaming ? (
            <span style={{ display: 'flex', gap: '2px' }}>
              {[0,1,2].map(i => (
                <span key={i} style={{
                  width: '4px', height: '4px', borderRadius: '50%',
                  background: 'currentColor', animation: 'bounce 1s infinite',
                  animationDelay: `${i*100}ms`,
                }} />
              ))}
            </span>
          ) : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <line x1="12" y1="19" x2="12" y2="5"/>
              <polyline points="5 12 12 5 19 12"/>
            </svg>
          )}
        </button>
      </div>

      <p style={{
        fontSize: '11px', color: 'var(--color-text-tertiary)',
        textAlign: 'center', marginTop: '6px', minHeight: '16px',
      }}>
        {status === 'connecting' && 'Connecting...'}
        {status === 'error'      && 'Connection error — retrying'}
        {status === 'streaming'  && 'Agent is thinking...'}
      </p>
    </div>
  )
}
