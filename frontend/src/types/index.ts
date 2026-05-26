// FIXED: Removed duplicate Phase original/B/E/I definitions — Phase L is canonical
export type MessageRole = 'human' | 'ai' | 'system'

export interface ReflectionEntry {
  attempt:        number
  answer_preview: string
  score:          number
  verdict:        'pass' | 'fail'
  critique:       string
  missing:        string[]
  hallucinations: string[]
  latency_ms:     number
}

export interface AgentStep {
  step:        string
  description: string
  metadata:    Record<string, unknown> // FIXED: replaced `any` with `unknown`
  timestamp:   number
}

export interface WorkerSummary {
  name:       string
  confidence: number
  latency_ms: number
}

export interface BrowserScreenshot {
  data:        string
  description: string
  timestamp:   number
}

export interface Message {
  id:                  string
  role:                MessageRole
  content:             string
  isStreaming:         boolean
  sources:             string[]
  model:               string
  traceId:             string
  intent:              string
  latencyMs:           Record<string, number>
  imageData?:          string
  timestamp:           number
  error?:              string
  // Phase B
  reflectionScore?:    number
  reflectionAttempts?: number
  reflectionHistory?:  ReflectionEntry[]
  // Phase C
  workersUsed?:        WorkerSummary[]
  supervisorDecision?: string
  // Phase E
  guardInputFlag?:     string
  guardOutputFlag?:    string
  piiMasked?:          boolean
  hallucinationFlag?:  boolean
  // Phase G
  abLogEntryId?:       number
  // Phase I
  browserScreenshots?: BrowserScreenshot[]
  browserFinalUrl?:    string
  // Phase L
  agentSteps?:         AgentStep[]
  branchParentId?:     string
  branchId?:           string
}

export interface StreamChunk {
  type:                 'token' | 'done' | 'error' | 'pong' | 'agent_step' | 'guard_event' | 'browser_screenshot' | 'transcript' | 'audio_chunk' | 'tts_done'
  // token
  data?:                string
  // done
  sources?:             string[]
  model?:               string
  latency_ms?:          Record<string, number>
  trace_id?:            string
  intent?:              string
  reflection_score?:    number
  reflection_attempts?: number
  reflection_history?:  ReflectionEntry[]
  supervisor_decision?: string
  workers_used?:        WorkerSummary[]
  guard_input_flag?:    string
  guard_output_flag?:   string
  pii_masked?:          boolean
  hallucination_flag?:  boolean
  ab_log_entry_id?:     number
  browser_final_url?:   string
  browser_actions_log?: unknown[] // FIXED: replaced `any[]` with `unknown[]`
  // agent_step
  step?:                string
  description?:         string
  metadata?:            Record<string, unknown> // FIXED: replaced `any` with `unknown`
  timestamp?:           number
  // error
  message?:             string
  code?:                number
  flag?:                string
  // audio
  chunk_idx?:           number
  // transcript
  language?:            string
  confidence?:          number
}

export interface ChatSession {
  messages: Message[]
  status:   'idle' | 'connecting' | 'connected' | 'streaming' | 'error'
  wsError:  string | null
}

export interface UploadedImage {
  file:    File
  preview: string
  base64:  string
}

export type Theme = 'light' | 'dark' | 'system'
