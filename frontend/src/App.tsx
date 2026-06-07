// frontend/src/App.tsx — Full dashboard with sidebar navigation + auth guard
import { useEffect, useState } from 'react'
import Sidebar from './components/Sidebar'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import ChatPage from './pages/ChatPage'
import AgriPage from './pages/AgriPage'
import LegalPage from './pages/LegalPage'
import CybersecPage from './pages/CybersecPage'
import ABTestPage from './pages/ABTestPage'
import ReceptionistPage from './pages/ReceptionistPage'
import FormReaderPage from './pages/FormReaderPage'
import SalesPage from './pages/SalesPage'
import AccountantPage from './pages/AccountantPage'
import HRPage from './pages/HRPage'
import SocialPage from './pages/SocialPage'
import HITLPage from './pages/HITLPage'
import SchedulerPage from './pages/SchedulerPage'
import BillingPage from './pages/BillingPage'
import CompliancePage from './pages/CompliancePage'
import OutputPage from './pages/OutputPage'
import EmailPage from './pages/EmailPage'
import AnalystPage from './pages/AnalystPage'
import DevopsPage from './pages/DevopsPage'
import QAPage from './pages/QAPage'
import ProjectPage from './pages/ProjectPage'
import CodePage from './pages/CodePage'
import MLPage from './pages/MLPage'
import DBAPage from './pages/DBAPage'
import TechLeadPage from './pages/TechLeadPage'
import HealthcarePage from './pages/HealthcarePage'
import RealEstatePage from './pages/RealEstatePage'
import EdTechPage from './pages/EdTechPage'
import AdminPage from './pages/AdminPage'
import IntegrationsPage from './pages/IntegrationsPage'
import KnowledgeBasePage from './pages/KnowledgeBasePage'
import SettingsPage from './pages/SettingsPage'
import WebhooksPage from './pages/WebhooksPage'
import { getMe, UserProfile } from './lib/api'

export type PageId =
  | 'dashboard' | 'chat' | 'agri' | 'legal' | 'cybersec'
  | 'ab-test' | 'receptionist' | 'form-reader' | 'email'
  | 'sales' | 'accountant' | 'hr' | 'social'
  | 'hitl' | 'scheduler' | 'billing' | 'compliance' | 'output'
  | 'analyst' | 'devops' | 'qa' | 'project' | 'code' | 'ml' | 'dba' | 'techlead'
  | 'healthcare' | 'realestate' | 'edtech' | 'admin' | 'integrations'
  | 'knowledge-base' | 'settings' | 'webhooks'

const PAGE_MAP: Record<PageId, React.ReactNode> = {
  dashboard:       <DashboardPage />,
  chat:            <ChatPage />,
  agri:            <AgriPage />,
  legal:           <LegalPage />,
  cybersec:        <CybersecPage />,
  'ab-test':       <ABTestPage />,
  receptionist:    <ReceptionistPage />,
  'form-reader':   <FormReaderPage />,
  email:           <EmailPage />,
  sales:           <SalesPage />,
  accountant:      <AccountantPage />,
  hr:              <HRPage />,
  social:          <SocialPage />,
  hitl:            <HITLPage />,
  scheduler:       <SchedulerPage />,
  billing:         <BillingPage />,
  compliance:      <CompliancePage />,
  output:          <OutputPage />,
  analyst:         <AnalystPage />,
  devops:          <DevopsPage />,
  qa:              <QAPage />,
  project:         <ProjectPage />,
  code:            <CodePage />,
  ml:              <MLPage />,
  dba:             <DBAPage />,
  techlead:        <TechLeadPage />,
  healthcare:      <HealthcarePage />,
  realestate:      <RealEstatePage />,
  edtech:          <EdTechPage />,
  admin:           <AdminPage />,
  integrations:    <IntegrationsPage />,
  'knowledge-base': <KnowledgeBasePage />,
  settings:        <SettingsPage />,
  webhooks:        <WebhooksPage />,
}

// Pages every authenticated user can always reach (not gated by entitlements)
const ALWAYS_ALLOWED: PageId[] = ['dashboard', 'chat', 'billing', 'settings', 'integrations']

function readCachedProfile(): UserProfile | null {
  try {
    const raw = sessionStorage.getItem('aaa_profile')
    return raw ? JSON.parse(raw) as UserProfile : null
  } catch { return null }
}

export default function App() {
  const [authed,    setAuthed]    = useState(!!sessionStorage.getItem('aaa_token'))
  const [showLogin, setShowLogin] = useState(false)
  const [page,      setPage]      = useState<PageId>('dashboard')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => typeof window !== 'undefined' && window.innerWidth < 860)

  // Auto-collapse the sidebar to an icon rail on small screens
  useEffect(() => {
    const onResize = () => { if (window.innerWidth < 860) setSidebarCollapsed(true) }
    onResize()
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])
  const [profile,   setProfile]   = useState<UserProfile | null>(readCachedProfile())
  const [demoMode,  setDemoMode]  = useState(false)

  // After auth, fetch the authoritative profile + entitlements from the backend
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
      .catch(() => { /* keep cached profile / dev fallback */ })
    return () => { active = false }
  }, [authed])

  const isAdmin = profile?.role === 'admin'
  const allowedTools = profile?.allowed_tools ?? []

  const canAccess = (id: PageId): boolean =>
    isAdmin || ALWAYS_ALLOWED.includes(id) || allowedTools.includes(id)

  // Guard: if the active page is no longer permitted, fall back to dashboard
  useEffect(() => {
    if (authed && profile && page !== 'admin' && !canAccess(page)) setPage('dashboard')
  }, [authed, profile, page])  // eslint-disable-line react-hooks/exhaustive-deps

  const handleLogout = () => {
    sessionStorage.removeItem('aaa_token')
    sessionStorage.removeItem('aaa_profile')
    setProfile(null); setAuthed(false); setShowLogin(true); setPage('dashboard')
  }

  // Not authenticated: show Landing → then Login
  if (!authed) {
    if (showLogin) {
      return <LoginPage onLogin={() => setAuthed(true)} />
    }
    return <LandingPage onSignIn={() => setShowLogin(true)} />
  }

  // 'admin' is admin-only; everything else respects entitlements
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
            color: '#0f1117', background: 'linear-gradient(90deg, #fbbf24, #f59e0b)',
            letterSpacing: '0.02em',
          }}>
            🎭 DEMO MODE — AI responses are instant sample data (no live model cost). Add an API key to switch on real generation.
          </div>
        )}
        {PAGE_MAP[activePage]}
      </main>
    </div>
  )
}
