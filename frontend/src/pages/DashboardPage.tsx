import { motion } from 'framer-motion'

const AGENTS = [
  {
    id: 'social',
    icon: '📱',
    name: 'Social Media Agent',
    desc: 'Generate posts, hashtags, captions, and campaign briefs for Instagram, LinkedIn, and Twitter.',
    features: ['Post Generator', 'Hashtag Research', 'Caption Writer', 'SEO Audit', 'Campaign Planner', 'Competitor Analysis'],
    from: '#8B5CF6', to: '#6366F1', glow: 'rgba(139,92,246,0.2)',
    count: 37,
  },
  {
    id: 'ca-accounting',
    icon: '🧮',
    name: 'CA & Accounting Agent',
    desc: 'India-focused accounting AI. GST queries, TDS calculations, invoice drafting, ITR advice.',
    features: ['GST Query Bot', 'TDS Calculator', 'Invoice Drafter', 'Compliance Deadlines', 'ITR Advisor', 'Business Valuation'],
    from: '#F59E0B', to: '#D97706', glow: 'rgba(245,158,11,0.2)',
    count: 40,
  },
  {
    id: 'customer-support',
    icon: '💬',
    name: 'Customer Support Agent',
    desc: 'WhatsApp-first AI. Handle FAQs, qualify leads, analyze sentiment, and build CS systems.',
    features: ['FAQ Bot', 'WhatsApp Drafter', 'Sentiment Analyzer', 'Ticket Triage', 'NPS Builder', 'Churn Risk'],
    from: '#10B981', to: '#059669', glow: 'rgba(16,185,129,0.2)',
    count: 38,
  },
]

const STATS = [
  { label: 'Core Agents',   value: '3',    sub: 'SM · CA · CS' },
  { label: 'AI Features',   value: '115',  sub: 'Across all agents' },
  { label: 'Languages',     value: '3',    sub: 'EN · Tamil · Hindi' },
  { label: 'Data Security', value: '100%', sub: 'PII-safe & compliant' },
]

const QUICK = [
  { label: 'Generate LinkedIn post',     agent: 'social',           icon: '📝' },
  { label: 'Calculate GST',              agent: 'ca-accounting',    icon: '🧾' },
  { label: 'Draft WhatsApp reply',       agent: 'customer-support', icon: '💬' },
  { label: 'TDS calculation',            agent: 'ca-accounting',    icon: '📊' },
  { label: 'Analyze customer sentiment', agent: 'customer-support', icon: '🔍' },
  { label: 'Create content calendar',    agent: 'social',           icon: '📅' },
]

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.45, ease: 'easeOut' as const } },
}
const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.07 } } }

interface Props { onNavigate?: (id: string) => void }

export default function DashboardPage({ onNavigate }: Props) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Header */}
      <div style={{
        padding: '20px 28px', borderBottom: '1px solid var(--border)',
        background: 'var(--surface)', flexShrink: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12,
      }}>
        <div>
          <h1 style={{ fontSize: 20, fontWeight: 700, letterSpacing: '-0.01em' }}>Dashboard</h1>
          <p style={{ color: 'var(--text-3)', fontSize: 13, marginTop: 2 }}>Business AI Suite for Indian SMBs</p>
        </div>
        <span className="badge badge-success">
          <span className="dot-live" />
          All agents live
        </span>
      </div>

      {/* Body */}
      <div className="aaa-page-body" style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>

        {/* Stats */}
        <motion.div initial="hidden" animate="show" variants={stagger}
          className="aaa-statgrid"
        >
          {STATS.map(s => (
            <motion.div key={s.label} variants={fadeUp}
              className="card"
              style={{ padding: '20px 22px' }}
            >
              <div style={{ fontSize: 28, fontWeight: 800, letterSpacing: '-0.02em', color: 'var(--text)', lineHeight: 1 }}>
                {s.value}
              </div>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-2)', marginTop: 6 }}>{s.label}</div>
              <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 2 }}>{s.sub}</div>
            </motion.div>
          ))}
        </motion.div>

        {/* Agent cards */}
        <motion.div initial="hidden" animate="show" variants={stagger}
          style={{ display: 'flex', flexDirection: 'column', gap: 12 }}
        >
          {AGENTS.map(agent => (
            <motion.div key={agent.id} variants={fadeUp}
              className="card card-glow"
              style={{ padding: '22px 24px', display: 'flex', gap: 20, alignItems: 'flex-start', flexWrap: 'wrap', cursor: 'pointer' }}
              onClick={() => onNavigate?.(agent.id)}
              whileHover={{ scale: 1.005 }}
              transition={{ duration: 0.15 }}
            >
              <div style={{
                width: 50, height: 50, borderRadius: 14, flexShrink: 0,
                background: `linear-gradient(135deg, ${agent.from}, ${agent.to})`,
                boxShadow: `0 0 20px ${agent.glow}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 24,
              }}>{agent.icon}</div>

              <div style={{ flex: 1, minWidth: 200 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6, flexWrap: 'wrap' }}>
                  <span style={{ fontWeight: 700, fontSize: 16 }}>{agent.name}</span>
                  <span className="badge badge-success">{agent.count} features</span>
                  <span className="badge badge-accent">LIVE</span>
                </div>
                <p style={{ color: 'var(--text-2)', fontSize: 13, lineHeight: 1.6, marginBottom: 12 }}>{agent.desc}</p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {agent.features.map(f => <span key={f} className="chip">{f}</span>)}
                </div>
              </div>

              <div style={{
                color: 'var(--text-3)', fontSize: 18, alignSelf: 'center', flexShrink: 0,
              }}>→</div>
            </motion.div>
          ))}
        </motion.div>

        {/* Quick actions */}
        <div>
          <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 12 }}>
            Quick Actions
          </h3>
          <motion.div initial="hidden" animate="show" variants={stagger}
            style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 8 }}
          >
            {QUICK.map(q => (
              <motion.button key={q.label} variants={fadeUp}
                className="card"
                onClick={() => onNavigate?.(q.agent)}
                style={{
                  padding: '14px 16px', display: 'flex', alignItems: 'center', gap: 12,
                  cursor: 'pointer', border: '1px solid var(--border)',
                  background: 'var(--surface)', width: '100%', textAlign: 'left',
                }}
                whileHover={{ borderColor: 'var(--border-2)', backgroundColor: 'var(--surface-2)' }}
                transition={{ duration: 0.15 }}
              >
                <span style={{ fontSize: 18 }}>{q.icon}</span>
                <span style={{ fontSize: 13, color: 'var(--text-2)', fontWeight: 500 }}>{q.label}</span>
                <span style={{ marginLeft: 'auto', color: 'var(--text-3)', fontSize: 14 }}>→</span>
              </motion.button>
            ))}
          </motion.div>
        </div>

        {/* Footer info */}
        <div style={{
          padding: '16px 20px', borderRadius: 'var(--r-lg)',
          background: 'var(--surface)', border: '1px solid var(--border)',
          display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap',
        }}>
          <span className="dot-live" />
          <span style={{ fontSize: 13, color: 'var(--text-2)' }}>
            All agents powered by <strong style={{ color: 'var(--text)' }}>Groq → Gemini → Ollama</strong> fallback chain.
            Demo mode uses instant canned output.
          </span>
          <a href="https://ai-agentic-backend-ywdx.onrender.com/docs" target="_blank" rel="noopener noreferrer"
            style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--accent-2)', textDecoration: 'none', flexShrink: 0 }}>
            API Docs →
          </a>
        </div>

      </div>
    </div>
  )
}
