import { motion } from 'framer-motion'

interface Props { onSignIn: () => void }

const AGENTS = [
  {
    icon: '💬', tag: 'CS',
    gradient: 'linear-gradient(135deg, #10B981, #059669)',
    glow: 'rgba(16,185,129,0.2)',
    name: 'Customer Support',
    desc: 'WhatsApp-first AI. Auto-draft replies, triage tickets, CSAT surveys, churn prediction.',
    count: '38 features',
    tools: ['FAQ Bot', 'Sentiment Analysis', 'Ticket Triage', 'CSAT Survey', 'Churn Risk', 'Escalation Manager'],
  },
  {
    icon: '🧮', tag: 'CA',
    gradient: 'linear-gradient(135deg, #F59E0B, #D97706)',
    glow: 'rgba(245,158,11,0.2)',
    name: 'CA & Accounting',
    desc: 'India-first tax AI. GST engine, TDS calc, GSTR filing, ITR advice, business valuation.',
    count: '40 features',
    tools: ['GST Query', 'TDS Calculator', 'GSTR Prep', 'ITR Advisor', 'Business Valuation', 'Payroll'],
  },
  {
    icon: '📱', tag: 'SM',
    gradient: 'linear-gradient(135deg, #8B5CF6, #6366F1)',
    glow: 'rgba(139,92,246,0.2)',
    name: 'Social Media',
    desc: 'Content AI for Instagram, LinkedIn, Twitter. Posts, captions, hashtags, campaigns.',
    count: '37 features',
    tools: ['Post Generator', 'Caption Writer', 'Hashtag Research', 'Content Calendar', 'SEO Audit', 'Competitor Analysis'],
  },
]

const BENTO = [
  { size: 'wide', icon: '🇮🇳', title: 'India-First AI', desc: 'GST, TDS, Tamil & Hindi, UPI billing — built for Indian rules, not just translated.', accent: '#F59E0B' },
  { size: 'tall', icon: '⚡', title: 'Instant Results', desc: 'Every AI action returns structured output in seconds. No waiting, no prompting.', accent: '#6366F1' },
  { size: 'normal', icon: '🛡️', title: 'PII-Safe', desc: 'Personal data detection and redaction before every LLM call.', accent: '#10B981' },
  { size: 'normal', icon: '☁️', title: '$0/month', desc: 'Runs on Render + Vercel free tiers. Demo mode needs zero API keys.', accent: '#06B6D4' },
  { size: 'normal', icon: '🔌', title: 'Multi-LLM', desc: 'Groq → Gemini → OpenAI → Ollama fallback chain. Never stuck on one vendor.', accent: '#8B5CF6' },
  { size: 'normal', icon: '🏢', title: 'Multi-Tenant', desc: 'Per-client tool entitlements. Admin panel assigns exactly which tools each client sees.', accent: '#F97316' },
]

const STATS = [
  { value: '115', suffix: '+', label: 'AI Features' },
  { value: '3',   suffix: '',  label: 'Languages' },
  { value: '38',  suffix: 'ms', label: 'Avg Latency' },
  { value: '$0',  suffix: '',  label: 'Monthly Cost' },
]

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] } },
}
const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } }

export default function LandingPage({ onSignIn }: Props) {
  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)', color: 'var(--text)', overflowX: 'hidden' }}>

      {/* ── Floating Nav ── */}
      <nav style={{
        position: 'fixed', top: 16, left: '50%', transform: 'translateX(-50%)',
        zIndex: 100, width: 'min(900px, calc(100vw - 32px))',
      }}>
        <div className="glass" style={{
          borderRadius: 'var(--r-xl)',
          padding: '12px 20px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 32, height: 32, borderRadius: 10,
              background: 'linear-gradient(135deg, #10B981, #6366F1)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 16, fontWeight: 800, color: '#fff', flexShrink: 0,
            }}>A</div>
            <span style={{ fontWeight: 700, fontSize: 15 }}>AI Agentic</span>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <a
              href="https://github.com/chandrukumar-AIML/ai-agentic-assistant"
              target="_blank" rel="noopener noreferrer"
              className="btn btn-ghost"
              style={{ padding: '7px 14px', fontSize: 13 }}
            >GitHub</a>
            <button onClick={onSignIn} className="btn btn-primary" style={{ padding: '7px 18px', fontSize: 13 }}>
              Sign In →
            </button>
          </div>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section style={{
        minHeight: '100vh', display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        padding: '100px 24px 80px', textAlign: 'center',
        background: 'radial-gradient(ellipse 80% 50% at 50% 0%, rgba(99,102,241,0.12) 0%, transparent 60%)',
        position: 'relative',
      }}>
        {/* Ambient orbs */}
        <div style={{
          position: 'absolute', top: '20%', left: '15%', width: 400, height: 400,
          borderRadius: '50%', background: 'radial-gradient(circle, rgba(99,102,241,0.06) 0%, transparent 70%)',
          pointerEvents: 'none',
        }} />
        <div style={{
          position: 'absolute', top: '30%', right: '10%', width: 300, height: 300,
          borderRadius: '50%', background: 'radial-gradient(circle, rgba(16,185,129,0.06) 0%, transparent 70%)',
          pointerEvents: 'none',
        }} />

        <motion.div initial="hidden" animate="show" variants={stagger}>

          <motion.div variants={fadeUp}>
            <span className="badge badge-accent" style={{ marginBottom: 28, display: 'inline-flex' }}>
              <span className="dot-live" />
              115+ AI Features · 3 Agents · Live Demo
            </span>
          </motion.div>

          <motion.h1 variants={fadeUp} style={{
            fontSize: 'clamp(36px, 6vw, 72px)', fontWeight: 800,
            lineHeight: 1.05, letterSpacing: '-0.03em', marginBottom: 24,
          }}>
            <span className="grad-text">Every Business AI Tool</span>
            <br />
            <span style={{ color: 'var(--text-2)', fontWeight: 500, fontSize: '0.72em', letterSpacing: '-0.01em' }}>
              your Indian SMB needs — in one login
            </span>
          </motion.h1>

          <motion.p variants={fadeUp} style={{
            fontSize: 18, color: 'var(--text-2)', maxWidth: 560, margin: '0 auto 40px', lineHeight: 1.7,
          }}>
            Customer Support · CA Accounting · Social Media — three production-ready AI agents
            in English, Tamil, and Hindi. No setup required.
          </motion.p>

          <motion.div variants={fadeUp} style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
            <button onClick={onSignIn} className="btn btn-primary" style={{ padding: '13px 32px', fontSize: 15 }}>
              Launch Dashboard
            </button>
            <a
              href="https://github.com/chandrukumar-AIML/ai-agentic-assistant"
              target="_blank" rel="noopener noreferrer"
              className="btn btn-outline" style={{ padding: '13px 32px', fontSize: 15, textDecoration: 'none' }}
            >
              View Source
            </a>
          </motion.div>

          <motion.div variants={fadeUp} style={{ marginTop: 20, color: 'var(--text-3)', fontSize: 12 }}>
            Demo: <code style={{ color: 'var(--text-2)' }}>admin@agentic.local</code> / <code style={{ color: 'var(--text-2)' }}>admin123</code>
          </motion.div>

        </motion.div>
      </section>

      {/* ── Stats Bar ── */}
      <motion.section
        initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }}
        style={{
          borderTop: '1px solid var(--border)', borderBottom: '1px solid var(--border)',
          background: 'var(--surface)',
        }}
      >
        <div style={{ maxWidth: 900, margin: '0 auto', display: 'flex', flexWrap: 'wrap' }}>
          {STATS.map((s, i) => (
            <div key={s.label} style={{
              flex: '1 1 160px', padding: '28px 24px', textAlign: 'center',
              borderRight: i < STATS.length - 1 ? '1px solid var(--border)' : 'none',
            }}>
              <div style={{ fontSize: 36, fontWeight: 800, color: 'var(--text)', lineHeight: 1, letterSpacing: '-0.02em' }}>
                {s.value}<span style={{ fontSize: 22, color: 'var(--accent-2)' }}>{s.suffix}</span>
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 6, fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{s.label}</div>
            </div>
          ))}
        </div>
      </motion.section>

      {/* ── 3 Core Agents ── */}
      <section style={{ padding: '96px 24px', maxWidth: 1100, margin: '0 auto' }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }} transition={{ duration: 0.5 }}
          style={{ textAlign: 'center', marginBottom: 56 }}
        >
          <p style={{ fontSize: 12, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 12 }}>Core Agents</p>
          <h2 style={{ fontSize: 'clamp(28px, 4vw, 42px)', fontWeight: 700, letterSpacing: '-0.02em' }}>
            Three agents. One platform.
          </h2>
        </motion.div>

        <motion.div
          initial="hidden" whileInView="show" viewport={{ once: true }} variants={stagger}
          style={{ display: 'flex', flexDirection: 'column', gap: 16 }}
        >
          {AGENTS.map((agent) => (
            <motion.div key={agent.name} variants={fadeUp}
              className="card card-glow"
              style={{ padding: '28px', display: 'flex', gap: 24, alignItems: 'flex-start', flexWrap: 'wrap' }}
            >
              <div style={{
                width: 56, height: 56, borderRadius: 16, flexShrink: 0,
                background: agent.gradient,
                boxShadow: `0 0 24px ${agent.glow}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 26,
              }}>{agent.icon}</div>

              <div style={{ flex: 1, minWidth: 220 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                  <span style={{ fontWeight: 700, fontSize: 18 }}>{agent.name}</span>
                  <span className="badge badge-success" style={{ fontSize: 10 }}>{agent.count}</span>
                </div>
                <p style={{ color: 'var(--text-2)', fontSize: 14, lineHeight: 1.7, marginBottom: 14 }}>{agent.desc}</p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {agent.tools.map(t => <span key={t} className="chip">{t}</span>)}
                </div>
              </div>

              <div style={{
                padding: '8px 16px', borderRadius: 'var(--r-md)',
                background: agent.glow, border: `1px solid ${agent.glow}`,
                fontSize: 11, fontWeight: 700, color: '#fff', letterSpacing: '0.05em',
                alignSelf: 'flex-start', flexShrink: 0,
              }}>{agent.tag}</div>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* ── Bento Grid Features ── */}
      <section style={{ padding: '0 24px 96px', maxWidth: 1100, margin: '0 auto' }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }} transition={{ duration: 0.5 }}
          style={{ textAlign: 'center', marginBottom: 56 }}
        >
          <p style={{ fontSize: 12, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 12 }}>Platform</p>
          <h2 style={{ fontSize: 'clamp(28px, 4vw, 42px)', fontWeight: 700, letterSpacing: '-0.02em' }}>
            Built for production, not demos
          </h2>
        </motion.div>

        <motion.div
          initial="hidden" whileInView="show" viewport={{ once: true }} variants={stagger}
          style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}
        >
          {BENTO.map((item) => (
            <motion.div key={item.title} variants={fadeUp}
              className="card card-glow"
              style={{ padding: '28px' }}
            >
              <div style={{
                width: 44, height: 44, borderRadius: 12,
                background: `${item.accent}18`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 22, marginBottom: 16,
                border: `1px solid ${item.accent}30`,
              }}>{item.icon}</div>
              <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 8 }}>{item.title}</div>
              <div style={{ fontSize: 13, color: 'var(--text-2)', lineHeight: 1.7 }}>{item.desc}</div>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* ── CTA ── */}
      <section style={{
        padding: '96px 24px',
        background: 'radial-gradient(ellipse 60% 80% at 50% 100%, rgba(99,102,241,0.1) 0%, transparent 70%)',
        textAlign: 'center',
        borderTop: '1px solid var(--border)',
      }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }} transition={{ duration: 0.5 }}
        >
          <h2 style={{ fontSize: 'clamp(28px, 4vw, 48px)', fontWeight: 700, letterSpacing: '-0.02em', marginBottom: 16 }}>
            Ready to explore?
          </h2>
          <p style={{ color: 'var(--text-2)', fontSize: 16, marginBottom: 40 }}>
            Log in with demo credentials — no setup, no API keys needed.
          </p>
          <button onClick={onSignIn} className="btn btn-primary" style={{ padding: '14px 48px', fontSize: 16 }}>
            Launch Dashboard →
          </button>
          <div style={{ marginTop: 20, color: 'var(--text-3)', fontSize: 12 }}>
            demo@agentic.local / demo123 &nbsp;·&nbsp; admin@agentic.local / admin123
          </div>
        </motion.div>
      </section>

      {/* ── Footer ── */}
      <footer style={{
        borderTop: '1px solid var(--border)',
        padding: '24px',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        flexWrap: 'wrap', gap: 12, maxWidth: 1100, margin: '0 auto',
      }}>
        <span style={{ color: 'var(--text-3)', fontSize: 12 }}>AI Agentic · FastAPI + React 18 · 2026</span>
        <div style={{ display: 'flex', gap: 20 }}>
          {[
            { label: 'GitHub', href: 'https://github.com/chandrukumar-AIML/ai-agentic-assistant' },
            { label: 'API Docs', href: 'https://ai-agentic-backend-ywdx.onrender.com/docs' },
          ].map(l => (
            <a key={l.label} href={l.href} target="_blank" rel="noopener noreferrer"
              style={{ color: 'var(--text-3)', fontSize: 12, textDecoration: 'none' }}
              onMouseEnter={e => (e.currentTarget.style.color = 'var(--text-2)')}
              onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-3)')}
            >{l.label}</a>
          ))}
          <button onClick={onSignIn}
            style={{ background: 'none', border: 'none', color: 'var(--text-3)', fontSize: 12, cursor: 'pointer', padding: 0 }}
            onMouseEnter={e => (e.currentTarget.style.color = 'var(--text-2)')}
            onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-3)')}
          >Sign In</button>
        </div>
      </footer>
    </div>
  )
}
