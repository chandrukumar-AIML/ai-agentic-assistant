// frontend/src/App.tsx — Full dashboard with sidebar navigation + auth guard
import { useState } from 'react'
import Sidebar from './components/Sidebar'
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
import KnowledgeBasePage from './pages/KnowledgeBasePage'
import SettingsPage from './pages/SettingsPage'

export type PageId =
  | 'dashboard' | 'chat' | 'agri' | 'legal' | 'cybersec'
  | 'ab-test' | 'receptionist' | 'form-reader' | 'email'
  | 'sales' | 'accountant' | 'hr' | 'social'
  | 'hitl' | 'scheduler' | 'billing' | 'compliance' | 'output'
  | 'analyst' | 'devops' | 'knowledge-base' | 'settings'

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
  'knowledge-base': <KnowledgeBasePage />,
  settings:        <SettingsPage />,
}

export default function App() {
  const [authed, setAuthed] = useState(!!sessionStorage.getItem('aaa_token'))
  const [page, setPage] = useState<PageId>('dashboard')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  // Show login screen if not authenticated
  if (!authed) {
    return <LoginPage onLogin={() => setAuthed(true)} />
  }

  return (
    <div style={{ display: 'flex', height: '100vh', background: '#0f1117', overflow: 'hidden' }}>
      <Sidebar current={page} onNavigate={setPage} collapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed(c => !c)} />
      <main style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {PAGE_MAP[page]}
      </main>
    </div>
  )
}
