// frontend/src/pages/DashboardPage.tsx
import { StatCard } from '../components/ui'

const AGENTS = [
  {
    id: 'social',
    name: 'Social Media Agent',
    icon: 'SM',
    gradient: 'linear-gradient(135deg, #8b5cf6, #6366f1)',
    desc: 'Generate posts, hashtags, captions, and campaign briefs for Instagram, LinkedIn, and Twitter — in English, Tamil, and Hindi.',
    features: ['Post Generator', 'Hashtag Research', 'Caption Writer', 'SEO Audit', 'Campaign Planner', 'Competitor Analysis'],
    badge: 'LIVE',
    badgeColor: '#10b981',
  },
  {
    id: 'ca-accounting',
    name: 'CA & Accounting Agent',
    icon: 'CA',
    gradient: 'linear-gradient(135deg, #f59e0b, #d97706)',
    desc: 'India-focused accounting AI. GST queries, TDS calculations, invoice drafting, ITR advice, audit checklists — all in one place.',
    features: ['GST Query Bot', 'TDS Calculator', 'Invoice Drafter', 'Compliance Deadlines', 'ITR Advisor', 'Audit Checklist'],
    badge: 'LIVE',
    badgeColor: '#10b981',
  },
  {
    id: 'customer-support',
    name: 'Customer Support Agent',
    icon: 'CS',
    gradient: 'linear-gradient(135deg, #10b981, #059669)',
    desc: 'WhatsApp-first customer support AI. Handle FAQs, qualify leads, analyze sentiment, and generate weekly intelligence reports.',
    features: ['FAQ Bot', 'WhatsApp Drafter', 'Sentiment Analyzer', 'Complaint Handler', 'Lead Qualifier', 'Weekly Report'],
    badge: 'LIVE',
    badgeColor: '#10b981',
  },
]

const STATS = [
  { label: 'Core Agents',   value: '3',    trend: 'Social · CA · Support' },
  { label: 'Languages',     value: '3',    trend: 'EN · Tamil · Hindi' },
  { label: 'Availability',  value: '24/7', trend: 'Cloud-hosted' },
  { label: 'Data Security', value: '100%', trend: 'PII-safe & compliant' },
]

export default function DashboardPage() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#0f1117', overflow: 'hidden' }}>
      {/* Header */}
      <div style={{
        padding: '20px 28px', borderBottom: '1px solid #1e2535',
        background: 'linear-gradient(135deg, #161b27 0%, #0f1117 100%)', flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 40, height: 40, borderRadius: 11,
            background: 'linear-gradient(135deg, #10b981, #06b6d4)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20,
          }}>A</div>
          <div>
            <div style={{ color: '#e2e8f0', fontSize: 21, fontWeight: 700 }}>AI Agentic</div>
            <div style={{ color: '#6b7280', fontSize: 13 }}>Business AI Suite for Indian SMBs</div>
          </div>
        </div>
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: '24px 28px' }}>
        {/* Stats */}
        <div className="aaa-statgrid" style={{ gap: 14, marginBottom: 28 }}>
          {STATS.map(s => (
            <StatCard key={s.label} label={s.label} value={s.value} icon="" trend={s.trend} />
          ))}
        </div>

        {/* Section heading */}
        <div style={{ color: '#e2e8f0', fontSize: 15, fontWeight: 600, marginBottom: 4 }}>Core Agents</div>
        <div style={{ color: '#6b7280', fontSize: 12, marginBottom: 20 }}>
          Three AI agents built for Indian businesses — click any agent in the sidebar to get started.
        </div>

        {/* Agent cards */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {AGENTS.map(agent => (
            <div key={agent.id} style={{
              background: '#161b27', border: '1px solid #1e2535',
              borderRadius: 14, padding: '20px 22px',
              display: 'flex', gap: 20, alignItems: 'flex-start',
            }}>
              {/* Icon */}
              <div style={{
                width: 52, height: 52, borderRadius: 14, flexShrink: 0,
                background: agent.gradient,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 13, fontWeight: 800, color: '#fff', letterSpacing: 0.5,
              }}>{agent.icon}</div>

              {/* Content */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                  <div style={{ color: '#e2e8f0', fontSize: 15, fontWeight: 700 }}>{agent.name}</div>
                  <span style={{
                    fontSize: 9, fontWeight: 700, padding: '2px 7px', borderRadius: 4,
                    background: 'rgba(16,185,129,0.15)', color: agent.badgeColor,
                  }}>{agent.badge}</span>
                </div>
                <div style={{ color: '#9ca3af', fontSize: 13, lineHeight: 1.6, marginBottom: 12 }}>
                  {agent.desc}
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {agent.features.map(f => (
                    <span key={f} style={{
                      fontSize: 11, padding: '3px 10px', borderRadius: 20,
                      background: '#1e2535', color: '#6b7280',
                    }}>{f}</span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Footer note */}
        <div style={{
          marginTop: 24, padding: '14px 18px',
          background: 'rgba(16,185,129,0.05)', border: '1px solid #1e2535',
          borderRadius: 10, color: '#4b5563', fontSize: 12, lineHeight: 1.6,
        }}>
          Powered by Groq (free tier) + Gemini fallback + Ollama for local models.
          All responses are AI-generated — review before sending to clients.
        </div>
      </div>
    </div>
  )
}
