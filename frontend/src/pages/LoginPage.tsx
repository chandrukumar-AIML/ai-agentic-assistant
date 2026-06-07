// frontend/src/pages/LoginPage.tsx
import { useState, FormEvent } from 'react'

interface Props { onLogin: () => void }

const API = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api')

export default function LoginPage({ onLogin }: Props) {
  const [mode,     setMode]     = useState<'login' | 'signup'>('login')
  const [email,    setEmail]    = useState('admin@agentic.local')
  const [fullName, setFullName] = useState('')
  const [password, setPassword] = useState('')
  const [error,    setError]    = useState('')
  const [loading,  setLoading]  = useState(false)

  const isSignup = mode === 'signup'

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(''); setLoading(true)
    try {
      const path = isSignup ? '/auth/signup' : '/auth/login'
      const body = isSignup
        ? { email, password, full_name: fullName }
        : { email, password }
      const res = await fetch(`${API}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || data.message || `${isSignup ? 'Signup' : 'Login'} failed`)
      sessionStorage.setItem('aaa_token', data.access_token)
      // Cache profile so the app can gate tools immediately (App also re-fetches /auth/me)
      if (data.profile) sessionStorage.setItem('aaa_profile', JSON.stringify(data.profile))
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
            background: 'linear-gradient(135deg, #10b981, #06b6d4)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 26, fontWeight: 800, color: '#fff',
          }}>A</div>
          <h1 style={{ color: '#fff', fontSize: 22, fontWeight: 700, margin: 0 }}>AI Agentic</h1>
          <p style={{ color: '#6b7280', fontSize: 13, margin: '6px 0 0' }}>Your all-in-one AI workspace for business</p>
        </div>

        {/* Card */}
        <div style={{
          background: '#161b27', border: '1px solid #1e2535',
          borderRadius: 16, padding: 32,
        }}>
          <h2 style={{ color: '#e2e8f0', fontSize: 17, fontWeight: 600, margin: '0 0 24px' }}>
            {isSignup ? 'Create your account' : 'Sign in to your workspace'}
          </h2>

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

            {isSignup && (
              <label style={{ display: 'block', marginBottom: 16 }}>
                <span style={{ color: '#9ca3af', fontSize: 12, fontWeight: 500 }}>Full name</span>
                <input
                  type="text" value={fullName} onChange={e => setFullName(e.target.value)}
                  placeholder="e.g. Acme Corp"
                  style={{
                    display: 'block', width: '100%', marginTop: 6, padding: '10px 12px',
                    background: '#0f1117', border: '1px solid #1e2535', borderRadius: 8,
                    color: '#e2e8f0', fontSize: 14, outline: 'none', boxSizing: 'border-box',
                  }}
                />
              </label>
            )}

            <label style={{ display: 'block', marginBottom: 20 }}>
              <span style={{ color: '#9ca3af', fontSize: 12, fontWeight: 500 }}>Password</span>
              <input
                type="password" value={password} onChange={e => setPassword(e.target.value)}
                required placeholder={isSignup ? 'Min 8 characters' : 'Enter password'}
                minLength={isSignup ? 8 : undefined}
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
              background: loading ? '#047857' : 'linear-gradient(90deg, #10b981, #06b6d4)',
              color: '#fff', fontSize: 14, fontWeight: 600, cursor: loading ? 'default' : 'pointer',
            }}>
              {loading ? (isSignup ? 'Creating…' : 'Signing in…') : (isSignup ? 'Create Account →' : 'Sign In →')}
            </button>
          </form>

          {/* Mode toggle */}
          <div style={{ textAlign: 'center', marginTop: 18, fontSize: 13, color: '#6b7280' }}>
            {isSignup ? 'Already have an account?' : "Don't have an account?"}{' '}
            <button
              type="button"
              onClick={() => { setMode(isSignup ? 'login' : 'signup'); setError('') }}
              style={{ background: 'none', border: 'none', color: '#5eead4', fontSize: 13, fontWeight: 600, cursor: 'pointer', padding: 0 }}
            >
              {isSignup ? 'Sign in' : 'Sign up free'}
            </button>
          </div>

          {/* Demo credentials hint */}
          {!isSignup && (
            <div style={{
              marginTop: 18, padding: '12px 14px', background: '#0f1117',
              borderRadius: 8, border: '1px solid #1e2535',
            }}>
              <div style={{ color: '#6b7280', fontSize: 11, fontWeight: 600, marginBottom: 6 }}>DEMO CREDENTIALS</div>
              <div style={{ color: '#9ca3af', fontSize: 12 }}>Admin: <code style={{ color: '#5eead4' }}>admin@agentic.local</code> / <code style={{ color: '#5eead4' }}>admin123</code></div>
              <div style={{ color: '#9ca3af', fontSize: 12 }}>Client: <code style={{ color: '#5eead4' }}>demo@agentic.local</code> / <code style={{ color: '#5eead4' }}>demo123</code></div>
            </div>
          )}
        </div>

        <p style={{ textAlign: 'center', color: '#374151', fontSize: 11, marginTop: 20 }}>
          AI Agentic · © 2026
        </p>
      </div>
    </div>
  )
}
