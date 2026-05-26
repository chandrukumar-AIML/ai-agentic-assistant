// frontend/src/hooks/useWebSocket.ts — Phase L canonical (duplicate removed)
import { useEffect, useRef, useCallback } from 'react'
import { useChatStore } from '../store/chatStore'
import { StreamChunk }  from '../types'

const WS_URL      = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'
const MAX_RETRIES = 5
const BASE_DELAY  = 1000

interface SendPayload {
  type:       string
  content?:   string
  session_id: string
  image?:     string
  user_id?:   string
  [key: string]: any
}

export function useWebSocket(sessionId: string) {
  const ws         = useRef<WebSocket | null>(null)
  const retryCount = useRef(0)
  const retryTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const activeAiId = useRef<string | null>(null)

  const {
    addMessage, appendToken, finaliseMessage,
    appendAgentStep, appendBrowserScreenshot,
    setStatus, setWsError,
  } = useChatStore()

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return

    setStatus('connecting')
    const socket = new WebSocket(`${WS_URL}?session_id=${sessionId}`)
    ws.current   = socket

    socket.onopen = () => {
      retryCount.current = 0
      setStatus('connected')
      setWsError(null)
    }

    socket.onmessage = (event: MessageEvent) => {
      let chunk: StreamChunk
      try { chunk = JSON.parse(event.data) }
      catch { return }

      switch (chunk.type) {
        case 'agent_step': {
          if (activeAiId.current) {
            appendAgentStep(activeAiId.current, {
              step:        chunk.step        ?? '',
              description: chunk.description ?? '',
              metadata:    chunk.metadata    ?? {},
              timestamp:   chunk.timestamp   ?? Date.now(),
            })
          }
          break
        }
        case 'token': {
          if (activeAiId.current === null) {
            const id = addMessage({
              role: 'ai', content: '', isStreaming: true,
              sources: [], model: '', traceId: '', intent: '',
              latencyMs: {}, agentSteps: [],
            })
            activeAiId.current = id
            setStatus('streaming')
          }
          appendToken(activeAiId.current!, chunk.data ?? '')
          break
        }
        case 'done': {
          if (activeAiId.current) {
            finaliseMessage(activeAiId.current, {
              sources:            chunk.sources            ?? [],
              model:              chunk.model              ?? 'gpt-4o',
              traceId:            chunk.trace_id           ?? '',
              intent:             chunk.intent             ?? '',
              latencyMs:          chunk.latency_ms         ?? {},
              reflectionScore:    chunk.reflection_score,
              reflectionAttempts: chunk.reflection_attempts,
              reflectionHistory:  chunk.reflection_history,
              workersUsed:        chunk.workers_used,
              supervisorDecision: chunk.supervisor_decision,
              guardInputFlag:     chunk.guard_input_flag,
              guardOutputFlag:    chunk.guard_output_flag,
              piiMasked:          chunk.pii_masked,
              hallucinationFlag:  chunk.hallucination_flag,
              abLogEntryId:       chunk.ab_log_entry_id,
              browserFinalUrl:    chunk.browser_final_url,
            })
            activeAiId.current = null
          }
          setStatus('connected')
          break
        }
        case 'browser_screenshot': {
          if (activeAiId.current) {
            appendBrowserScreenshot(activeAiId.current, {
              data:        chunk.data        ?? '',
              description: chunk.description ?? '',
              timestamp:   chunk.timestamp   ?? Date.now(),
            })
          }
          break
        }
        case 'error': {
          if (activeAiId.current) {
            finaliseMessage(activeAiId.current, { error: chunk.message, isStreaming: false })
            activeAiId.current = null
          } else {
            addMessage({
              role: 'ai', content: chunk.message ?? 'Error.',
              isStreaming: false, sources: [], model: '',
              traceId: '', intent: '', latencyMs: {}, error: chunk.message,
            })
          }
          setStatus('error')
          break
        }
        case 'guard_event':
        case 'pong':
          break
      }
    }

    socket.onclose = (event) => {
      ws.current = null
      if (event.wasClean) { setStatus('idle'); return }
      if (retryCount.current < MAX_RETRIES) {
        const delay = BASE_DELAY * Math.pow(2, retryCount.current)
        retryCount.current++
        setStatus('connecting')
        setWsError(`Reconnecting in ${(delay/1000).toFixed(1)}s...`)
        retryTimer.current = setTimeout(() => connectRef.current(), delay)
      } else {
        setStatus('error')
        setWsError('Connection failed. Please refresh.')
      }
    }

    socket.onerror = () => {
      setWsError('WebSocket error — check that the backend is running.')
    }
  }, [sessionId, addMessage, appendToken, finaliseMessage,
      appendAgentStep, appendBrowserScreenshot, setStatus, setWsError])

  const connectRef = useRef(connect)
  useEffect(() => { connectRef.current = connect }, [connect])

  useEffect(() => {
    connectRef.current()
    const ping = setInterval(() => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30_000)
    return () => {
      clearInterval(ping)
      if (retryTimer.current) clearTimeout(retryTimer.current)
      ws.current?.close(1000, 'unmounted')
    }
  }, [])

  const send = useCallback((payload: SendPayload) => {
    if (ws.current?.readyState !== WebSocket.OPEN) {
      setWsError('Not connected.')
      return false
    }
    ws.current.send(JSON.stringify(payload))
    return true
  }, [setWsError])

  const sendRaw = useCallback((payload: object) => {
    if (ws.current?.readyState !== WebSocket.OPEN) return false
    ws.current.send(JSON.stringify(payload))
    return true
  }, [])

  return { send, sendRaw, reconnect: () => connectRef.current() }
}
