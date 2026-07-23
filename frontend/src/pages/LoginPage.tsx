import { useState, FormEvent } from 'react'
import { motion } from 'framer-motion'

interface Props { onLogin: () => void }

const API = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api')

export default function LoginPage({ onLogin }: Props) {
  const [mode,     setMode]     = useState<'login' | 'signup'>('login')
  const [email,    setEmail]    = useState('admin@agentic.local')
  const [fullName, setFullName] = useState('')
  const [password, setPassword] = useState('admin123')
  const [showPw,   setShowPw]   = useState(false)
  const [error,    setError]    = useState('')
  const [loading,  setLoading]  = useState(false)

  const isSignup = mode === 'signup'
  const pwScore  = [/.{8,}/, /[A-Z]/, /[0-9]/, /[^A-Za-z0-9]/].filter(r => r.test(password)).length
  const pwLabel  = ['Too short', 'Weak', 'Fair', 'Good', 'Strong'][pwScore]
  const pwColor  = ['#ef4444', '#f59e0b', '#f59e0b', '#10b981', '#22c55e'][pwScore]
  const emailValid = /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)
  const formValid  = isSignup ? (emailValid && password.length >= 8) : (emailValid && password.length > 0)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(''); setLoading(true)
    try {
      const path = isSignup ? '/auth/signup' : '/auth/login'
      const body = isSignup ? { email, password, full_name: fullName } : { email, password }
      const res  = await fetch(`${API}${path}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || data.message || `${isSignup ? 'Signup' : 'Login'} failed`)
      sessionStorage.setItem('aaa_token', data.access_token)
      if (data.profile) sessionStorage.setItem('aaa_profile', JSON.stringify(data.profile))
      onLogin()
    } catch (err: any) {
      setError(err.message || 'Connection error')
    } finally { setLoading(false) }
  }

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'var(--bg)',
      backgroundImage: 'radial-gradient(ellipse 80% 60% at 50% -10%, rgba(99,102,241,0.1) 0%, transparent 60%)',
    }}>
      {/* Ambient orb */}
      <div style={{
        position: 'fixed', top: '50%', left: '50%', transform: 'translate(-50%,-50%)',
        width: 600, height: 600, borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(99,102,241,0.05) 0%, transparent 70%)',
        pointerEvents: 'none',
      }} />

      <motion.div
        initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        style={{ width: '100%', maxWidth: 400, padding: '0 16px', position: 'relative', zIndex: 1 }}
      >
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <div style={{
            width: 52, height: 52, borderRadius: 16, margin: '0 auto 16px',
            background: 'linear-gradient(135deg, #10B981, #6366F1)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 24, fontWeight: 800, color: '#fff',
            boxShadow: '0 0 32px rgba(99,102,241,0.3)',
          }}>A</div>
          <h1 style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-0.02em', marginBottom: 6 }}>AI Agentic</h1>
          <p style={{ color: 'var(--text-3)', fontSize: 14 }}>Your all-in-one AI workspace</p>
        </div>

        {/* Card */}
        <div className="card" style={{ padding: 32, borderRadius: 20 }}>

          {/* Tab switcher */}
          <div style={{
            display: 'flex', background: 'var(--surface-2)', borderRadius: 10, padding: 4, marginBottom: 28,
          }}>
            {(['login', 'signup'] as const).map(m => (
              <button key={m} onClick={() => { setMode(m); setError('') }}
                style={{
                  flex: 1, padding: '8px', border: 'none', borderRadius: 8, cursor: 'pointer', fontSize: 13, fontWeight: 600,
                  background: mode === m ? 'var(--surface-3)' : 'transparent',
                  color: mode === m ? 'var(--text)' : 'var(--text-3)',
                  transition: 'all 0.2s',
                }}>
                {m === 'login' ? 'Sign In' : 'Sign Up'}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

            {isSignup && (
              <div>
                <label className="label">Full Name</label>
                <input className="input" type="text" value={fullName} placeholder="Your name or company"
                  onChange={e => setFullName(e.target.value)} />
              </div>
            )}

            <div>
              <label className="label">Email</label>
              <input className="input" type="email" value={email} autoFocus
                onChange={e => setEmail(e.target.value)} required />
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <span className="label" style={{ margin: 0 }}>Password</span>
                {!isSignup && (
                  <span onClick={() => setError('Contact admin@agentic.local for password reset')}
                    style={{ fontSize: 12, color: 'var(--accent-2)', cursor: 'pointer' }}>
                    Forgot?
                  </span>
                )}
              </div>
              <div style={{ position: 'relative' }}>
                <input className="input" type={showPw ? 'text' : 'password'} value={password}
                  placeholder={isSignup ? 'Min 8 characters' : 'Password'}
                  onChange={e => setPassword(e.target.value)} required
                  style={{ paddingRight: 44 }} />
                <button type="button" onClick={() => setShowPw(s => !s)}
                  style={{
                    position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
                    background: 'none', border: 'none', cursor: 'pointer', fontSize: 16, padding: 0,
                    color: 'var(--text-3)',
                  }}>
                  {showPw ? '🙈' : '👁️'}
                </button>
              </div>
              {isSignup && password.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  <div style={{ display: 'flex', gap: 3, marginBottom: 4 }}>
                    {[0,1,2,3].map(i => (
                      <div key={i} style={{ flex: 1, height: 3, borderRadius: 2, background: i < pwScore ? pwColor : 'var(--surface-3)', transition: 'background 0.3s' }} />
                    ))}
                  </div>
                  <span style={{ fontSize: 11, color: pwColor }}>{pwLabel}</span>
                </div>
              )}
            </div>

            {error && (
              <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
                style={{
                  background: 'var(--danger-bg)', border: '1px solid rgba(239,68,68,0.3)',
                  borderRadius: 8, padding: '10px 14px', color: 'var(--danger)', fontSize: 13,
                }}>⚠ {error}</motion.div>
            )}

            <button type="submit" className="btn btn-primary" disabled={loading || !formValid}
              style={{ width: '100%', padding: '12px', fontSize: 14, marginTop: 4 }}>
              {loading
                ? <span style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'center' }}>
                    <span style={{ width: 14, height: 14, border: '2px solid rgba(255,255,255,0.3)', borderTop: '2px solid #fff', borderRadius: '50%', animation: 'spin 0.7s linear infinite' }} />
                    {isSignup ? 'Creating…' : 'Signing in…'}
                  </span>
                : isSignup ? 'Create Account →' : 'Sign In →'
              }
            </button>
          </form>
        </div>

        {/* Demo credentials */}
        {!isSignup && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}
            style={{
              marginTop: 16, padding: '14px 16px',
              background: 'var(--surface)', border: '1px solid var(--border)',
              borderRadius: 'var(--r-lg)',
            }}
          >
            <div style={{ fontSize: 10, color: 'var(--text-3)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>
              Demo Credentials
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {[
                { role: 'Admin', email: 'admin@agentic.local', pw: 'admin123' },
                { role: 'Client', email: 'demo@agentic.local',  pw: 'demo123' },
              ].map(c => (
                <button key={c.role} onClick={() => { setEmail(c.email); setPassword(c.pw); setMode('login') }}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 10, background: 'none', border: 'none',
                    cursor: 'pointer', padding: '4px 0', textAlign: 'left',
                  }}>
                  <span style={{ fontSize: 11, color: 'var(--text-3)', width: 40 }}>{c.role}</span>
                  <code style={{ fontSize: 12, color: 'var(--accent-2)' }}>{c.email}</code>
                  <span style={{ fontSize: 11, color: 'var(--text-3)' }}>/ {c.pw}</span>
                </button>
              ))}
            </div>
            <div style={{ marginTop: 8, fontSize: 11, color: 'var(--text-3)' }}>↑ Click to fill credentials</div>
          </motion.div>
        )}

        <p style={{ textAlign: 'center', color: 'var(--text-3)', fontSize: 11, marginTop: 20 }}>
          AI Agentic · © 2026
        </p>
      </motion.div>
    </div>
  )
}
