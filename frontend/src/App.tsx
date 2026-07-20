// frontend/src/App.tsx
import { useEffect, useState } from 'react'
import Sidebar from './components/Sidebar'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import ChatPage from './pages/ChatPage'
import SocialPage from './pages/SocialPage'
import CAPage from './pages/CAPage'
import CustomerSupportPage from './pages/CustomerSupportPage'
import BillingPage from './pages/BillingPage'
import IntegrationsPage from './pages/IntegrationsPage'
import KnowledgeBasePage from './pages/KnowledgeBasePage'
import SettingsPage from './pages/SettingsPage'
import WebhooksPage from './pages/WebhooksPage'
import AdminPage from './pages/AdminPage'
import { getMe, UserProfile } from './lib/api'

export type PageId =
  | 'dashboard' | 'chat'
  | 'social' | 'ca-accounting' | 'customer-support'
  | 'billing' | 'integrations' | 'knowledge-base' | 'settings' | 'webhooks' | 'admin'

const PAGE_MAP: Record<PageId, React.ReactNode> = {
  dashboard:          <DashboardPage />,
  chat:               <ChatPage />,
  social:             <SocialPage />,
  'ca-accounting':    <CAPage />,
  'customer-support': <CustomerSupportPage />,
  billing:            <BillingPage />,
  integrations:       <IntegrationsPage />,
  'knowledge-base':   <KnowledgeBasePage />,
  settings:           <SettingsPage />,
  webhooks:           <WebhooksPage />,
  admin:              <AdminPage />,
}

const ALWAYS_ALLOWED: PageId[] = [
  'dashboard', 'chat', 'billing', 'settings', 'integrations',
  'social', 'ca-accounting', 'customer-support',
]

function readCachedProfile(): UserProfile | null {
  try {
    const raw = sessionStorage.getItem('aaa_profile')
    return raw ? JSON.parse(raw) as UserProfile : null
  } catch { return null }
}

export default function App() {
  const [authed,           setAuthed]           = useState(!!sessionStorage.getItem('aaa_token'))
  const [showLogin,        setShowLogin]         = useState(false)
  const [page,             setPage]              = useState<PageId>('dashboard')
  const [sidebarCollapsed, setSidebarCollapsed]  = useState(() => typeof window !== 'undefined' && window.innerWidth < 860)
  const [profile,          setProfile]           = useState<UserProfile | null>(readCachedProfile())
  const [demoMode,         setDemoMode]          = useState(false)

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

  const isAdmin      = profile?.role === 'admin'
  const allowedTools = profile?.allowed_tools ?? []

  const canAccess = (id: PageId): boolean =>
    isAdmin || ALWAYS_ALLOWED.includes(id) || allowedTools.includes(id)

  useEffect(() => {
    if (authed && profile && page !== 'admin' && !canAccess(page)) setPage('dashboard')
  }, [authed, profile, page])

  const handleLogout = () => {
    sessionStorage.removeItem('aaa_token')
    sessionStorage.removeItem('aaa_profile')
    setProfile(null); setAuthed(false); setShowLogin(true); setPage('dashboard')
  }

  if (!authed) {
    if (showLogin) return <LoginPage onLogin={() => setAuthed(true)} />
    return <LandingPage onSignIn={() => setShowLogin(true)} />
  }

  const activePage: PageId =
    page === 'admin' ? (isAdmin ? 'admin' : 'dashboard')
    : canAccess(page) ? page
    : 'dashboard'

  return (
    <div style={{ display: 'flex', height: '100vh', background: '#0f1117', overflow: 'hidden' }}>
      <Sidebar
        current={activePage}
        onNavigate={setPage}
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(c => !c)}
        isAdmin={isAdmin}
        allowedTools={allowedTools}
        alwaysAllowed={ALWAYS_ALLOWED}
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
        {PAGE_MAP[activePage]}
      </main>
    </div>
  )
}
