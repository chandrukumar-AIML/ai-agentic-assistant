// frontend/src/hooks/useVoice.ts
/**
 * Voice recording hook.
 * Uses AudioWorklet to capture Float32 PCM at 16kHz.
 * Sends base64-encoded audio over WebSocket when recording stops.
 */
import { useState, useRef, useCallback, useEffect } from 'react'

export type VoiceState =
  | 'idle'
  | 'requesting_permission'
  | 'recording'
  | 'processing'
  | 'speaking'
  | 'error'

interface UseVoiceOptions {
  onSendAudio:    (audioB64: string, durationMs: number) => void
  onAudioChunk:   (chunkB64: string, chunkIdx: number) => void
  onTranscript:   (text: string, confidence: number) => void
  onTTSDone:      () => void
  maxDurationMs?: number   // auto-stop after N ms (default 60s)
}

const SAMPLE_RATE    = 16000
const MAX_DURATION   = 60_000   // 60 seconds

// PCM Float32 worklet — processes audio in 128-sample chunks
const WORKLET_CODE = `
class PCMCapture extends AudioWorkletProcessor {
  constructor() {
    super()
    this._buf = []
  }
  process(inputs) {
    const ch = inputs[0][0]
    if (ch) {
      this._buf.push(...ch)
      // Send 4096 samples (~256ms) at a time
      if (this._buf.length >= 4096) {
        this.port.postMessage(new Float32Array(this._buf.splice(0, 4096)))
      }
    }
    return true
  }
}
registerProcessor('pcm-capture', PCMCapture)
`

export function useVoice({
  onSendAudio,
  onAudioChunk: _onAudioChunk,
  onTranscript,
  onTTSDone,
  maxDurationMs = MAX_DURATION,
}: UseVoiceOptions) {
  const [state,        setState]        = useState<VoiceState>('idle')
  const [transcript,   setTranscript]   = useState('')
  const [duration,     setDuration]     = useState(0)
  const [audioLevel,   setAudioLevel]   = useState(0)

  const streamRef      = useRef<MediaStream | null>(null)
  const contextRef     = useRef<AudioContext | null>(null)
  const workletRef     = useRef<AudioWorkletNode | null>(null)
  const chunksRef      = useRef<Float32Array[]>([])
  const startTimeRef   = useRef<number>(0)
  const timerRef       = useRef<ReturnType<typeof setInterval> | null>(null)
  const audioQueueRef  = useRef<Uint8Array[]>([])
  const isPlayingRef   = useRef(false)

  // ── Microphone capture ───────────────────────────────────────────────────
  const startRecording = useCallback(async () => {
    if (state === 'recording') return

    setState('requesting_permission')
    chunksRef.current = []

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate:    SAMPLE_RATE,
          channelCount:  1,
          echoCancellation:  true,
          noiseSuppression:  true,
          autoGainControl:   true,
        },
      })
      streamRef.current = stream
      setState('recording')
      startTimeRef.current = Date.now()

      // Create AudioContext + Worklet
      const ctx    = new AudioContext({ sampleRate: SAMPLE_RATE })
      const blob   = new Blob([WORKLET_CODE], { type: 'application/javascript' })
      const url    = URL.createObjectURL(blob)

      await ctx.audioWorklet.addModule(url)
      URL.revokeObjectURL(url)

      const source  = ctx.createMediaStreamSource(stream)
      const worklet = new AudioWorkletNode(ctx, 'pcm-capture')

      // Level meter via AnalyserNode
      const analyser = ctx.createAnalyser()
      analyser.fftSize = 256
      source.connect(analyser)
      source.connect(worklet)
      worklet.connect(ctx.destination)

      // Collect PCM chunks
      worklet.port.onmessage = (e: MessageEvent<Float32Array>) => {
        chunksRef.current.push(e.data)

        // Update audio level (for waveform visualisation)
        const rms = Math.sqrt(e.data.reduce((s, v) => s + v * v, 0) / e.data.length)
        setAudioLevel(Math.min(rms * 5, 1))
      }

      contextRef.current = ctx
      workletRef.current = worklet

      // Duration counter
      timerRef.current = setInterval(() => {
        const elapsed = Date.now() - startTimeRef.current
        setDuration(elapsed)
        if (elapsed >= maxDurationMs) stopRecording()
      }, 100)

    } catch (e: unknown) { // FIXED: replaced `any` with `unknown`; removed console.error production log
      void e
      setState('error')
    }
  }, [state, maxDurationMs])

  const stopRecording = useCallback(() => {
    if (state !== 'recording') return

    // Stop timers + stream
    if (timerRef.current)  clearInterval(timerRef.current)
    streamRef.current?.getTracks().forEach(t => t.stop())
    contextRef.current?.close()
    contextRef.current = null

    // Merge all Float32 chunks into one buffer
    const totalLength = chunksRef.current.reduce((s, c) => s + c.length, 0)
    if (totalLength === 0) {
      setState('idle')
      return
    }

    const merged = new Float32Array(totalLength)
    let offset   = 0
    for (const chunk of chunksRef.current) {
      merged.set(chunk, offset)
      offset += chunk.length
    }

    // Convert to base64
    const bytes  = new Uint8Array(merged.buffer)
    const b64    = btoa(String.fromCharCode(...bytes))
    const durationMs = Date.now() - startTimeRef.current

    setState('processing')
    setAudioLevel(0)
    onSendAudio(b64, durationMs)

  }, [state, onSendAudio])

  // ── TTS audio playback ───────────────────────────────────────────────────
  // playNextChunk must be defined BEFORE enqueueAudioChunk to avoid TDZ error
  const playNextChunk = useCallback(() => {
    const queue = audioQueueRef.current
    if (queue.length === 0) {
      isPlayingRef.current = false
      setState('idle')
      onTTSDone()
      return
    }

    isPlayingRef.current = true
    setState('speaking')
    const chunk = queue.shift()!

    const ctx   = new AudioContext()
    ctx.decodeAudioData(chunk.buffer.slice(0) as ArrayBuffer, (audioBuffer) => {
      const source = ctx.createBufferSource()
      source.buffer = audioBuffer
      source.connect(ctx.destination)
      source.onended = () => {
        ctx.close()
        playNextChunk()
      }
      source.start(0)
    }, (_err) => {
      ctx.close()
      playNextChunk()
    })
  }, [onTTSDone])

  const enqueueAudioChunk = useCallback((chunkB64: string) => {
    const bytes = Uint8Array.from(atob(chunkB64), c => c.charCodeAt(0))
    audioQueueRef.current.push(bytes)
    if (!isPlayingRef.current) {
      playNextChunk()
    }
  }, [playNextChunk])

  const handleTranscript = useCallback((text: string, confidence: number) => {
    setTranscript(text)
    onTranscript(text, confidence)
  }, [onTranscript])

  const reset = useCallback(() => {
    setState('idle')
    setTranscript('')
    setDuration(0)
    setAudioLevel(0)
    audioQueueRef.current = []
    isPlayingRef.current  = false
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
      streamRef.current?.getTracks().forEach(t => t.stop())
      contextRef.current?.close()
    }
  }, [])

  return {
    state,
    transcript,
    duration,
    audioLevel,
    startRecording,
    stopRecording,
    enqueueAudioChunk,
    handleTranscript,
    reset,
  }
}