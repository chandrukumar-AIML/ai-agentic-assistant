// FIXED: Removed dead Phase A chatStore and code snippets — Phase L is canonical
// frontend/src/store/chatStore.ts
import { create }       from 'zustand'
import { persist }      from 'zustand/middleware'
import { Message, AgentStep, BrowserScreenshot, Theme } from '../types'
import { v4 as uuid }   from 'uuid'

type Status = 'idle' | 'connecting' | 'connected' | 'streaming' | 'error'

interface ChatStore {
  messages:     Message[]
  status:       Status
  wsError:      string | null
  pendingImage: any | null
  theme:        Theme

  // Message mutations
  addMessage:             (msg: Omit<Message, 'id' | 'timestamp'>) => string
  appendToken:            (id: string, token: string) => void
  finaliseMessage:        (id: string, meta: Partial<Message>) => void
  appendAgentStep:        (id: string, step: AgentStep) => void
  appendBrowserScreenshot:(id: string, ss: BrowserScreenshot) => void
  setStatus:              (status: Status) => void
  setWsError:             (err: string | null) => void
  clearMessages:          () => void
  setPendingImage:        (img: any | null) => void

  // Branching
  branchFrom:             (messageId: string) => string   // returns new branchId
  getBranch:              (branchId: string) => Message[]

  // Theme
  setTheme:               (theme: Theme) => void
}

export const useChatStore = create<ChatStore>()(
  persist(
    (set, get) => ({
      messages:     [],
      status:       'idle',
      wsError:      null,
      pendingImage: null,
      theme:        'system',

      addMessage: (msg) => {
        const id = uuid()
        set((state) => ({
          messages: [
            ...state.messages,
            { ...msg, id, timestamp: Date.now(), agentSteps: [] },
          ],
        }))
        return id
      },

      appendToken: (id, token) =>
        set((state) => ({
          messages: state.messages.map((m) =>
            m.id === id ? { ...m, content: m.content + token } : m
          ),
        })),

      finaliseMessage: (id, meta) =>
        set((state) => ({
          messages: state.messages.map((m) =>
            m.id === id ? { ...m, ...meta, isStreaming: false } : m
          ),
        })),

      appendAgentStep: (id, step) =>
        set((state) => ({
          messages: state.messages.map((m) =>
            m.id === id
              ? { ...m, agentSteps: [...(m.agentSteps || []), step] }
              : m
          ),
        })),

      appendBrowserScreenshot: (id, ss) =>
        set((state) => ({
          messages: state.messages.map((m) =>
            m.id === id
              ? { ...m, browserScreenshots: [...(m.browserScreenshots || []), ss] }
              : m
          ),
        })),

      setStatus:  (status)  => set({ status }),
      setWsError: (wsError) => set({ wsError }),
      clearMessages: ()     => set({ messages: [] }),
      setPendingImage: (pendingImage) => set({ pendingImage }),

      branchFrom: (messageId: string) => {
        const messages = get().messages
        const idx      = messages.findIndex(m => m.id === messageId)
        if (idx === -1) return ''

        const branchId = uuid()
        // Keep messages up to and including the branch point
        const branchMessages = messages.slice(0, idx + 1).map(m => ({
          ...m,
          branchId,
        }))
        set({ messages: branchMessages })
        return branchId
      },

      getBranch: (branchId: string) => {
        return get().messages.filter(m => m.branchId === branchId)
      },

      setTheme: (theme) => set({ theme }),
    }),
    {
      name:    'chat-store',
      partialize: (state) => ({
        theme: state.theme,
        // Don't persist messages — loaded from Redis session on reconnect
      }),
    }
  )
)