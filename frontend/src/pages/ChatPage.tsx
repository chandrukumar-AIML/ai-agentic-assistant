// frontend/src/pages/ChatPage.tsx — Full chat with WebSocket
import { useCallback, useState, useRef } from 'react'
import { useChatStore }        from '../store/chatStore'
import { useWebSocket }        from '../hooks/useWebSocket'
import { useSession }          from '../hooks/useSession'
import ChatWindow              from '../components/ChatWindow'
import InputBar                from '../components/InputBar'
import MemoryPanel             from '../components/MemoryPanel'
import { UploadedImage }       from '../types'
import { clearHistory, submitFeedback } from '../lib/api'

const DEV_USER_ID = 'dev-user-001'

export default function ChatPage() {
  const sessionId     = useSession()
  const status        = useChatStore(s => s.status)
  const wsError       = useChatStore(s => s.wsError)
  const messages      = useChatStore(s => s.messages)
  const addMessage    = useChatStore(s => s.addMessage)
  const clearMessages = useChatStore(s => s.clearMessages)
  const branchFrom    = useChatStore(s => s.branchFrom)

  const [memoryOpen, setMemoryOpen] = useState(false)
  const [isVoiceMode, setIsVoiceMode] = useState(false)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const { send, sendRaw } = useWebSocket(sessionId)

  const statusColor = {
    connected: '#22c55e', streaming: '#10b981', connecting: '#eab308',
    error: '#ef4444', idle: '#6b7280',
  }[status] || '#6b7280'

  const handleSend = useCallback((content: string, image?: UploadedImage) => {
    addMessage({
      role: 'human', content, isStreaming: false,
      sources: [], model: '', traceId: '', intent: '', latencyMs: {},
      imageData: image?.base64, agentSteps: [],
    })
    send({ type: image ? 'vision' : 'text', content, session_id: sessionId, image: image?.base64, user_id: DEV_USER_ID })
  }, [addMessage, send, sessionId])

  const handleSendAudio = useCallback((audioB64: string, _duration: number) => {
    sendRaw({ type: 'audio_chunk', data: audioB64, session_id: sessionId, user_id: DEV_USER_ID })
  }, [sendRaw, sessionId])

  const handleClear = useCallback(async () => {
    clearMessages()
    await clearHistory(sessionId).catch(() => {})
  }, [clearMessages, sessionId])

  return (
    <div style={{ display: 'flex', height: '100%', background: '#0f1117', overflow: 'hidden' }}>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <header style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '12px 20px', borderBottom: '1px solid #1e2535',
          background: '#161b27', flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 18 }}>💬</span>
            <span style={{ fontWeight: 600, fontSize: 14, color: '#e2e8f0' }}>AI Chat</span>
            <span style={{ width: 7, height: 7, borderRadius: '50%', background: statusColor }} />
            <span style={{ fontSize: 11, color: '#6b7280', textTransform: 'capitalize' }}>{status}</span>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            {isVoiceMode && <span style={{ fontSize: 11, padding: '3px 8px', borderRadius: 20, background: 'rgba(16,185,129,0.15)', color: '#5eead4' }}>🎙️ Voice</span>}
            <button onClick={() => setMemoryOpen(o => !o)} style={{
              fontSize: 12, padding: '5px 10px', borderRadius: 20, cursor: 'pointer', border: 'none',
              background: memoryOpen ? 'rgba(16,185,129,0.2)' : '#1e2535',
              color: memoryOpen ? '#5eead4' : '#6b7280',
            }}>🧠 Memory</button>
            <button onClick={handleClear} style={{
              fontSize: 12, color: '#6b7280', background: 'none', border: 'none', cursor: 'pointer', padding: '5px 8px',
            }}>Clear</button>
          </div>
        </header>

        {wsError && (
          <div style={{ background: 'rgba(239,68,68,0.1)', borderBottom: '1px solid #7f1d1d', padding: '6px 16px', fontSize: 12, color: '#fca5a5' }}>
            {wsError}
          </div>
        )}

        <ChatWindow />

        <InputBar
          onSend={handleSend}
          onSendAudio={handleSendAudio}
          onAudioChunk={() => {}}
          onTranscript={() => {}}
          onTTSDone={() => {}}
          disabled={status === 'idle' || status === 'error'}
          status={status}
          isVoiceMode={isVoiceMode}
          onToggleVoice={() => setIsVoiceMode(v => !v)}
        />
      </div>

      <MemoryPanel userId={DEV_USER_ID} isOpen={memoryOpen} onClose={() => setMemoryOpen(false)} />
    </div>
  )
}
