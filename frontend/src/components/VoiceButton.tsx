// frontend/src/components/VoiceButton.tsx
import React, { useCallback } from 'react'
import { VoiceState } from '../hooks/useVoice'

interface Props {
  voiceState:     VoiceState
  audioLevel:     number        // 0-1 for waveform
  transcript:     string
  duration:       number        // ms
  onStart:        () => void
  onStop:         () => void
  disabled:       boolean
}

function formatDuration(ms: number): string {
  const s = Math.floor(ms / 1000)
  const m = Math.floor(s / 60)
  return `${m}:${String(s % 60).padStart(2, '0')}`
}

function AudioWaveform({ level, isActive }: { level: number; isActive: boolean }) {
  const bars = 12
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: '2px',
      height: '24px',
    }}>
      {Array.from({ length: bars }).map((_, i) => {
        const barLevel = isActive
          ? Math.max(0.1, level * (0.5 + 0.5 * Math.sin(i * 0.8 + Date.now() / 200)))
          : 0.1
        return (
          <div
            key={i}
            style={{
              width:         '3px',
              height:        `${Math.max(4, barLevel * 24)}px`,
              background:    isActive ? '#534AB7' : 'var(--color-border-tertiary)',
              borderRadius:  '2px',
              transition:    'height 0.1s ease',
            }}
          />
        )
      })}
    </div>
  )
}

export default function VoiceButton({
  voiceState, audioLevel, transcript, duration, onStart, onStop, disabled,
}: Props) {
  const isRecording = voiceState === 'recording'
  const isProcessing = voiceState === 'processing'
  const isSpeaking  = voiceState === 'speaking'
  const isError     = voiceState === 'error'

  const handleClick = useCallback(() => {
    if (isRecording) {
      onStop()
    } else if (!disabled && !isProcessing && !isSpeaking) {
      onStart()
    }
  }, [isRecording, isProcessing, isSpeaking, disabled, onStart, onStop])

  // Button ring color
  const ringColor = isRecording ? '#ef4444'
    : isSpeaking ? '#534AB7'
    : isError    ? '#f59e0b'
    : 'transparent'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
      {/* Main mic button */}
      <button
        onClick={handleClick}
        disabled={disabled || isProcessing}
        title={isRecording ? 'Click to stop' : 'Click to speak'}
        style={{
          width: '48px', height: '48px',
          borderRadius: '50%',
          background:   isRecording ? '#ef4444' : isSpeaking ? '#534AB7' : 'var(--color-background-secondary)',
          border:       `2px solid ${ringColor}`,
          cursor:       disabled || isProcessing ? 'not-allowed' : 'pointer',
          display:      'flex', alignItems: 'center', justifyContent: 'center',
          opacity:      disabled ? 0.4 : 1,
          transition:   'all 0.2s',
          boxShadow:    isRecording
            ? `0 0 0 ${4 + audioLevel * 8}px rgba(239,68,68,0.2)`
            : 'none',
        }}
      >
        {isProcessing ? (
          // Spinner
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 12a9 9 0 11-6.219-8.56" strokeLinecap="round"/>
          </svg>
        ) : isSpeaking ? (
          // Speaker icon
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
            <path d="M15.54 8.46a5 5 0 0 1 0 7.07M19.07 4.93a10 10 0 0 1 0 14.14"/>
          </svg>
        ) : (
          // Mic icon
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
               stroke={isRecording ? 'white' : 'var(--color-text-secondary)'}
               strokeWidth="2" strokeLinecap="round">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
            <line x1="12" y1="19" x2="12" y2="23"/>
            <line x1="8"  y1="23" x2="16" y2="23"/>
          </svg>
        )}
      </button>

      {/* Waveform — visible while recording */}
      {isRecording && (
        <AudioWaveform level={audioLevel} isActive={true} />
      )}

      {/* Status text */}
      <p style={{
        fontSize: '11px', margin: 0,
        color: isRecording ? '#ef4444'
             : isSpeaking  ? '#534AB7'
             : isProcessing ? 'var(--color-text-tertiary)'
             : 'var(--color-text-tertiary)',
      }}>
        {isRecording  && `Recording ${formatDuration(duration)} — click to stop`}
        {isProcessing && 'Transcribing...'}
        {isSpeaking   && 'Agent speaking...'}
        {voiceState === 'idle' && 'Click to speak'}
        {isError      && 'Mic error — check permissions'}
      </p>

      {/* Transcript preview */}
      {transcript && (
        <div style={{
          maxWidth: '240px', padding: '6px 10px',
          background: 'var(--color-background-secondary)',
          borderRadius: '8px', fontSize: '11px',
          color: 'var(--color-text-secondary)',
          lineHeight: 1.4, textAlign: 'center',
        }}>
          🎤 "{transcript}"
        </div>
      )}
    </div>
  )
}