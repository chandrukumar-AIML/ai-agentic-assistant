import { useEffect, useState } from 'react'
import Sidebar from './components/Sidebar'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import SocialPage from './pages/SocialPage'
import CAPage from './pages/CAPage'
import CustomerSupportPage from './pages/CustomerSupportPage'
import SettingsPage from './pages/SettingsPage'
import { getMe, UserProfile } from './lib/api'

export type PageId =
  | 'dashboard'
  | 'social' | 'ca-accounting' | 'customer-support'
  | 'settings'

const PAGE_MAP: Record<PageId, React.ReactNode> = {
  dashboard:          <DashboardPage />,
  social:             <SocialPage />,
  'ca-accounting':    <CAPage />,
  'customer-support': <CustomerSupportPage />,
  settings:           <SettingsPage />,
}

function readCachedProfile(): UserProfile | null {
  try {
    const raw = sessionStorage.getItem('aaa_profile')
    return raw ? JSON.parse(raw) as UserProfile : null
  } catch { return null }
}

export default function App() {
  const [authed,           setAuthed]          = useState(!!sessionStorage.getItem('aaa_token'))
  const [showLogin,        setShowLogin]        = useState(false)
  const [page,             setPage]             = useState<PageId>('dashboard')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => typeof window !== 'undefined' && window.innerWidth < 860)
  const [profile,          setProfile]          = useState<UserProfile | null>(readCachedProfile())
  const [demoMode,         setDemoMode]         = useState(false)

  useEffect(() => {
    const onResize = () => { if (window.innerWidth < 860) setSidebarCollapsed(true) }
    onResize()
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  useEffect(() => {
    if (!authed) return
    let active = true
    getMe()
      .then(res => {
        if (!active) return
        setProfile(res.profile)
        setDemoMode(!!res.demo_mode)
        sessionStorage.setItem('aaa_profile', JSON.stringify(res.profile))
      })
      .catch(() => {})
    return () => { active = false }
  }, [authed])

  const handleLogout = () => {
    sessionStorage.removeItem('aaa_token')
    sessionStorage.removeItem('aaa_profile')
    setProfile(null); setAuthed(false); setShowLogin(true); setPage('dashboard')
  }

  if (!authed) {
    if (showLogin) return <LoginPage onLogin={() => setAuthed(true)} />
    return <LandingPage onSignIn={() => setShowLogin(true)} />
  }

  return (
    <div style={{ display: 'flex', height: '100vh', background: '#0f1117', overflow: 'hidden' }}>
      <Sidebar
        current={page}
        onNavigate={setPage}
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(c => !c)}
        isAdmin={profile?.role === 'admin'}
        allowedTools={profile?.allowed_tools ?? []}
        alwaysAllowed={['dashboard','social','ca-accounting','customer-support','settings']}
        profile={profile}
        onLogout={handleLogout}
      />
      <main style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {demoMode && (
          <div style={{
            flexShrink: 0, padding: '7px 16px', textAlign: 'center', fontSize: 12, fontWeight: 600,
            color: '#0f1117', background: 'linear-gradient(90deg, #fbbf24, #f59e0b)', letterSpacing: '0.02em',
          }}>
            DEMO MODE — AI responses are instant sample data. Add an API key to switch on real generation.
          </div>
        )}
        {PAGE_MAP[page]}
      </main>
    </div>
  )
}
