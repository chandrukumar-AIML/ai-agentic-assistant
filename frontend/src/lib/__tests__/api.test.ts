import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock fetch globally
const mockFetch = vi.fn()
globalThis.fetch = mockFetch

// Mock import.meta.env
vi.stubEnv('VITE_API_URL', 'http://localhost:8001/api')

beforeEach(() => {
  mockFetch.mockReset()
  sessionStorage.clear()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('apiFetch', () => {
  it('sends Authorization header from session token', async () => {
    sessionStorage.setItem('aaa_token', 'test-token-123')
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: 'ok' }),
    })

    const { apiFetch } = await import('../api')
    const result = await apiFetch('/health')

    expect(mockFetch).toHaveBeenCalledOnce()
    const [, options] = mockFetch.mock.calls[0]
    expect((options?.headers as Record<string, string>)['Authorization']).toBe('Bearer test-token-123')
    expect(result).toEqual({ status: 'ok' })
  })

  it('throws on non-ok HTTP status', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
      json: async () => ({ detail: 'Not authenticated' }),
    })

    const { apiFetch } = await import('../api')
    await expect(apiFetch('/auth/me')).rejects.toThrow('Not authenticated')
  })

  it('throws with statusText when body is not JSON', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: async () => { throw new Error('not json') },
    })

    const { apiFetch } = await import('../api')
    await expect(apiFetch('/crash')).rejects.toThrow('Internal Server Error')
  })
})
