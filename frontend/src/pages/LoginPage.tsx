// frontend/src/pages/LoginPage.tsx
import { useState, FormEvent } from 'react'

interface Props { onLogin: () => void }

const API = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api')

export default function LoginPage({ onLogin }: Props) {
  const [email,    setEmail]    = useState('admin@agentic.local')
  const [password, setPassword] = useState('')
  const [error,    setError]    = useState('')
  const [loading,  setLoading]  = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(''); setLoading(true)
    try {
      const res = await fetch(`${API}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || data.message || 'Login failed')
      sessionStorage.setItem('aaa_token', data.access_token)
      onLogin()
    } catch (err: any) {
      setError(err.message || 'Connection error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'linear-gradient(135deg, #0f1117 0%, #161b27 100%)',
    }}>
      <div style={{ width: 380 }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 36 }}>
          <div style={{
            width: 56, height: 56, borderRadius: 16, margin: '0 auto 16px',
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 26, fontWeight: 800, color: '#fff',
          }}>A</div>
          <h1 style={{ color: '#fff', fontSize: 22, fontWeight: 700, margin: 0 }}>AI Agentic Assistant</h1>
          <p style={{ color: '#6b7280', fontSize: 13, margin: '6px 0 0' }}>v2.0 · Enterprise Multi-Agent Platform</p>
        </div>

        {/* Card */}
        <div style={{
          background: '#161b27', border: '1px solid #1e2535',
          borderRadius: 16, padding: 32,
        }}>
          <h2 style={{ color: '#e2e8f0', fontSize: 17, fontWeight: 600, margin: '0 0 24px' }}>Sign in to your workspace</h2>

          <form onSubmit={handleSubmit}>
            <label style={{ display: 'block', marginBottom: 16 }}>
              <span style={{ color: '#9ca3af', fontSize: 12, fontWeight: 500 }}>Email</span>
              <input
                type="email" value={email} onChange={e => setEmail(e.target.value)}
                required autoFocus
                style={{
                  display: 'block', width: '100%', marginTop: 6, padding: '10px 12px',
                  background: '#0f1117', border: '1px solid #1e2535', borderRadius: 8,
                  color: '#e2e8f0', fontSize: 14, outline: 'none', boxSizing: 'border-box',
                }}
              />
            </label>

            <label style={{ display: 'block', marginBottom: 20 }}>
              <span style={{ color: '#9ca3af', fontSize: 12, fontWeight: 500 }}>Password</span>
              <input
                type="password" value={password} onChange={e => setPassword(e.target.value)}
                required placeholder="Enter password"
                style={{
                  display: 'block', width: '100%', marginTop: 6, padding: '10px 12px',
                  background: '#0f1117', border: '1px solid #1e2535', borderRadius: 8,
                  color: '#e2e8f0', fontSize: 14, outline: 'none', boxSizing: 'border-box',
                }}
              />
            </label>

            {error && (
              <div style={{
                background: '#1f0a0a', border: '1px solid #dc2626', borderRadius: 8,
                padding: '10px 14px', marginBottom: 16, color: '#f87171', fontSize: 13,
              }}>⚠ {error}</div>
            )}

            <button type="submit" disabled={loading} style={{
              width: '100%', padding: '11px 0', borderRadius: 8, border: 'none',
              background: loading ? '#4338ca' : 'linear-gradient(90deg, #6366f1, #8b5cf6)',
              color: '#fff', fontSize: 14, fontWeight: 600, cursor: loading ? 'default' : 'pointer',
            }}>
              {loading ? 'Signing in…' : 'Sign In →'}
            </button>
          </form>

          {/* Demo credentials hint */}
          <div style={{
            marginTop: 20, padding: '12px 14px', background: '#0f1117',
            borderRadius: 8, border: '1px solid #1e2535',
          }}>
            <div style={{ color: '#6b7280', fontSize: 11, fontWeight: 600, marginBottom: 6 }}>DEMO CREDENTIALS</div>
            <div style={{ color: '#9ca3af', fontSize: 12 }}>Email: <code style={{ color: '#a5b4fc' }}>admin@agentic.local</code></div>
            <div style={{ color: '#9ca3af', fontSize: 12 }}>Password: <code style={{ color: '#a5b4fc' }}>admin123</code></div>
          </div>
        </div>

        <p style={{ textAlign: 'center', color: '#374151', fontSize: 11, marginTop: 20 }}>
          AI Agentic Assistant V2 · LangGraph + FastAPI · © 2026
        </p>
      </div>
    </div>
  )
}
