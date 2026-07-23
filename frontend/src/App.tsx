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

const makePAGE_MAP = (onNavigate: (id: PageId) => void): Record<PageId, React.ReactNode> => ({
  dashboard:          <DashboardPage onNavigate={id => onNavigate(id as PageId)} />,
  social:             <SocialPage />,
  'ca-accounting':    <CAPage />,
  'customer-support': <CustomerSupportPage />,
  settings:           <SettingsPage />,
})

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

  const PAGE_MAP = makePAGE_MAP((id) => setPage(id as PageId))

  return (
    <div style={{ display: 'flex', height: '100vh', background: 'var(--bg)', overflow: 'hidden' }}>
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
            flexShrink: 0, padding: '6px 16px', textAlign: 'center', fontSize: 11, fontWeight: 700,
            color: '#000', background: 'linear-gradient(90deg, #F59E0B, #D97706)',
            letterSpacing: '0.06em', textTransform: 'uppercase',
          }}>
            Demo Mode — Instant sample output · Add an API key for real AI generation
          </div>
        )}
        {PAGE_MAP[page]}
      </main>
    </div>
  )
}
