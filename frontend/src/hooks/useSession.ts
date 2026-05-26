// FIXED: Removed typo re-export (useSeesion → useSession). Implementation lives here now.
import { useState } from 'react'

const SESSION_KEY = 'aaa_session_id'

function createSessionId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return `session-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
}

export function useSession(): string {
  const [sessionId] = useState<string>(() => {
    const stored = sessionStorage.getItem(SESSION_KEY)
    if (stored) return stored
    const fresh = createSessionId()
    sessionStorage.setItem(SESSION_KEY, fresh)
    return fresh
  })
  return sessionId
}
