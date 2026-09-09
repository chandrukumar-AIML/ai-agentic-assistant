import { motion, AnimatePresence } from 'framer-motion'
import { useState } from 'react'

interface Props {
  onSignIn: () => void
  onSignUp: () => void
}

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
  { value: '135', suffix: '+', label: 'AI Features' },
  { value: '3',   suffix: '',  label: 'Languages' },
  { value: '19',  suffix: '+', label: 'Unit Tests' },
  { value: '₹0',  suffix: '',  label: 'Free Tier' },
]

const PLANS = [
  {
    name: 'Free',
    price: '₹0',
    period: 'forever',
    desc: 'Perfect for trying the platform.',
    accent: '#10B981',
    cta: 'Start Free',
    featured: false,
    features: [
      '50 AI generations / month',
      '3 agents (SM, CA, CS)',
      'English language only',
      'SQLite history (7 days)',
      'Community support',
    ],
  },
  {
    name: 'Starter',
    price: '₹999',
    period: '/month',
    desc: 'For freelancers & small teams.',
    accent: '#6366F1',
    cta: 'Get Started',
    featured: true,
    features: [
      '500 AI generations / month',
      'All 3 agents unlocked',
      'English + Tamil + Hindi',
      'History storage (90 days)',
      'Email support',
      'API access',
    ],
  },
  {
    name: 'Pro',
    price: '₹2,999',
    period: '/month',
    desc: 'For agencies & growing businesses.',
    accent: '#F59E0B',
    cta: 'Go Pro',
    featured: false,
    features: [
      'Unlimited AI generations',
      'All 3 agents + priority queue',
      'All 3 languages',
      'Unlimited history',
      'WhatsApp support',
      'Custom branding',
      'Multi-user workspace',
    ],
  },
]

const PRIVACY_TEXT = `Last updated: September 2026

**What we collect**
We collect your email address, name, and the prompts you send to our AI agents. We also store the AI-generated outputs in your history.

**What we don't do**
We do not sell your data to third parties. We do not use your prompts to train AI models. We do not store payment card numbers (handled by Razorpay).

**Data storage**
Your data is stored on Render (backend) and Neon (database) servers located in the United States. We apply encryption in transit (HTTPS).

**Your rights**
You can delete your account and all associated data by contacting admin@agentic.local. We will process deletion requests within 7 business days.

**PDPB compliance**
This product is designed to comply with India's Personal Data Protection Bill (PDPB). We process only the minimum data required to provide the service.

**Contact**
For privacy questions: admin@agentic.local`

const TERMS_TEXT = `Last updated: September 2026

**1. Acceptance**
By using AI Agentic, you agree to these Terms of Service. If you do not agree, do not use the platform.

**2. Service description**
AI Agentic provides AI-powered tools for Social Media, Customer Support, and CA & Accounting tasks. AI outputs are suggestions only — not professional legal, financial, or tax advice.

**3. CA / Accounting disclaimer**
GST rates, TDS percentages, and tax advice generated by the CA agent are based on publicly available data and AI interpretation. Always verify with a licensed Chartered Accountant before acting on any output.

**4. Acceptable use**
You may not use AI Agentic to generate spam, misinformation, or content that violates Indian law. Accounts violating this policy will be suspended.

**5. Billing**
Paid plans are billed monthly in INR. Cancellation takes effect at the end of the current billing period. No refunds for partial months.

**6. Limitation of liability**
AI Agentic is provided "as is." We are not liable for decisions made based on AI-generated output.

**7. Governing law**
These terms are governed by the laws of India. Disputes shall be resolved in courts located in Tamil Nadu.

**Contact**
Legal questions: admin@agentic.local`

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.5, ease: 'easeOut' as const } },
}
const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } }

function Modal({ title, text, onClose }: { title: string; text: string; onClose: () => void }) {
  return (
    <div onClick={onClose} style={{
      position: 'fixed', inset: 0, zIndex: 999,
      background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24,
    }}>
      <div onClick={e => e.stopPropagation()} className="card" style={{
        maxWidth: 600, width: '100%', maxHeight: '80vh', overflow: 'hidden',
        display: 'flex', flexDirection: 'column', borderRadius: 20, padding: 0,
      }}>
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '20px 28px', borderBottom: '1px solid var(--border)',
        }}>
          <span style={{ fontWeight: 700, fontSize: 16 }}>{title}</span>
          <button onClick={onClose} style={{
            background: 'none', border: 'none', cursor: 'pointer', fontSize: 20,
            color: 'var(--text-3)', lineHeight: 1, padding: 4,
          }}>×</button>
        </div>
        <div style={{ padding: '24px 28px', overflowY: 'auto', flex: 1 }}>
          {text.split('\n\n').map((para, i) => {
            if (para.startsWith('**') && para.endsWith('**')) {
              return <h3 key={i} style={{ fontSize: 14, fontWeight: 700, marginBottom: 8, marginTop: i > 0 ? 20 : 0 }}>{para.replace(/\*\*/g, '')}</h3>
            }
            if (para.startsWith('**')) {
              const bold = para.match(/\*\*(.+?)\*\*/)?.[1] || ''
              const rest = para.replace(/\*\*(.+?)\*\*/, '')
              return <p key={i} style={{ fontSize: 13, color: 'var(--text-2)', lineHeight: 1.7, marginBottom: 0 }}><strong style={{ color: 'var(--text)' }}>{bold}</strong>{rest}</p>
            }
            return <p key={i} style={{ fontSize: 13, color: 'var(--text-2)', lineHeight: 1.7, marginBottom: 0 }}>{para}</p>
          })}
        </div>
      </div>
    </div>
  )
}

const HOW_STEPS = [
  { n: '01', icon: '✍️', title: 'Create your account', desc: 'Sign up in 30 seconds. No credit card required for the free tier.' },
  { n: '02', icon: '⚙️', title: 'Set up your workspace', desc: 'Tell each agent about your business — name, industry, tone. One-time setup.' },
  { n: '03', icon: '🚀', title: 'Generate AI content instantly', desc: 'Click any of the 115+ tools and get structured, ready-to-use output in seconds.' },
]

export default function LandingPage({ onSignIn, onSignUp }: Props) {
  const [showPrivacy, setShowPrivacy] = useState(false)
  const [showTerms,   setShowTerms]   = useState(false)

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
            <a href="#pricing"
              className="btn btn-ghost"
              style={{ padding: '7px 14px', fontSize: 13, textDecoration: 'none' }}
            >Pricing</a>
            <a
              href="https://github.com/chandrukumar-AIML/ai-agentic-assistant"
              target="_blank" rel="noopener noreferrer"
              className="btn btn-ghost"
              style={{ padding: '7px 14px', fontSize: 13 }}
            >GitHub</a>
            <button onClick={onSignIn} className="btn btn-ghost" style={{ padding: '7px 14px', fontSize: 13 }}>
              Sign In
            </button>
            <button onClick={onSignUp} className="btn btn-primary" style={{ padding: '7px 18px', fontSize: 13 }}>
              Start Free →
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
              135+ AI Features · 3 Agents · Live Demo
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
            Customer Support · CA Accounting · Social Media — 135 AI-powered tools
            in English, Tamil, and Hindi. Free tier. No setup required.
          </motion.p>

          <motion.div variants={fadeUp} style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
            <button onClick={onSignUp} className="btn btn-primary" style={{ padding: '13px 32px', fontSize: 15 }}>
              Start Free — No card needed
            </button>
            <button onClick={onSignIn} className="btn btn-outline" style={{ padding: '13px 32px', fontSize: 15 }}>
              Sign In →
            </button>
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

      {/* ── How it works ── */}
      <section style={{ padding: '96px 24px', borderTop: '1px solid var(--border)' }}>
        <div style={{ maxWidth: 900, margin: '0 auto' }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }} transition={{ duration: 0.5 }}
            style={{ textAlign: 'center', marginBottom: 56 }}
          >
            <p style={{ fontSize: 12, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 12 }}>Getting Started</p>
            <h2 style={{ fontSize: 'clamp(28px, 4vw, 42px)', fontWeight: 700, letterSpacing: '-0.02em' }}>
              Up and running in 2 minutes
            </h2>
          </motion.div>
          <motion.div
            initial="hidden" whileInView="show" viewport={{ once: true }} variants={stagger}
            style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 24 }}
          >
            {HOW_STEPS.map((step, i) => (
              <motion.div key={step.n} variants={fadeUp} style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>
                <div style={{
                  flexShrink: 0, width: 48, height: 48, borderRadius: 14,
                  background: 'var(--surface-2)', border: '1px solid var(--border)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22,
                }}>{step.icon}</div>
                <div>
                  <div style={{ fontSize: 11, color: 'var(--text-3)', fontWeight: 700, letterSpacing: '0.08em', marginBottom: 4 }}>STEP {step.n}</div>
                  <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 6 }}>{step.title}</div>
                  <div style={{ fontSize: 13, color: 'var(--text-2)', lineHeight: 1.7 }}>{step.desc}</div>
                </div>
                {i < HOW_STEPS.length - 1 && (
                  <div style={{
                    display: 'none', // shown on desktop via grid, arrow between cards
                  }} />
                )}
              </motion.div>
            ))}
          </motion.div>
          <motion.div
            initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }}
            style={{ textAlign: 'center', marginTop: 48 }}
          >
            <button onClick={onSignUp} className="btn btn-primary" style={{ padding: '12px 36px', fontSize: 15 }}>
              Create Free Account →
            </button>
          </motion.div>
        </div>
      </section>

      {/* ── Pricing ── */}
      <section id="pricing" style={{ padding: '96px 24px', borderTop: '1px solid var(--border)' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }} transition={{ duration: 0.5 }}
            style={{ textAlign: 'center', marginBottom: 56 }}
          >
            <p style={{ fontSize: 12, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 12 }}>Pricing</p>
            <h2 style={{ fontSize: 'clamp(28px, 4vw, 42px)', fontWeight: 700, letterSpacing: '-0.02em', marginBottom: 12 }}>
              Simple pricing for Indian SMBs
            </h2>
            <p style={{ color: 'var(--text-2)', fontSize: 15 }}>Billed in INR. No USD surprises. Cancel any time.</p>
          </motion.div>

          <motion.div
            initial="hidden" whileInView="show" viewport={{ once: true }} variants={stagger}
            style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 20, alignItems: 'stretch' }}
          >
            {PLANS.map(plan => (
              <motion.div key={plan.name} variants={fadeUp}
                className="card"
                style={{
                  padding: 28, display: 'flex', flexDirection: 'column', gap: 0,
                  border: plan.featured ? `1.5px solid ${plan.accent}55` : '1px solid var(--border)',
                  boxShadow: plan.featured ? `0 0 32px ${plan.accent}20` : 'none',
                  position: 'relative', overflow: 'hidden',
                }}
              >
                {plan.featured && (
                  <div style={{
                    position: 'absolute', top: 16, right: 16,
                    background: plan.accent, color: '#fff',
                    fontSize: 10, fontWeight: 700, letterSpacing: '0.08em',
                    padding: '3px 10px', borderRadius: 20, textTransform: 'uppercase',
                  }}>Popular</div>
                )}
                <div style={{ marginBottom: 20 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: plan.accent, marginBottom: 6 }}>{plan.name}</div>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 4, marginBottom: 6 }}>
                    <span style={{ fontSize: 36, fontWeight: 800, letterSpacing: '-0.02em' }}>{plan.price}</span>
                    <span style={{ fontSize: 13, color: 'var(--text-3)' }}>{plan.period}</span>
                  </div>
                  <p style={{ fontSize: 13, color: 'var(--text-2)' }}>{plan.desc}</p>
                </div>
                <div style={{ flex: 1, marginBottom: 24 }}>
                  {plan.features.map(f => (
                    <div key={f} style={{ display: 'flex', alignItems: 'flex-start', gap: 10, padding: '6px 0', borderBottom: '1px solid var(--border)' }}>
                      <span style={{ color: plan.accent, fontSize: 13, lineHeight: 1.6, flexShrink: 0 }}>✓</span>
                      <span style={{ fontSize: 13, color: 'var(--text-2)', lineHeight: 1.6 }}>{f}</span>
                    </div>
                  ))}
                </div>
                <button onClick={onSignUp} className="btn"
                  style={{
                    width: '100%', padding: '11px',
                    background: plan.featured ? plan.accent : 'transparent',
                    border: `1.5px solid ${plan.accent}`,
                    color: plan.featured ? '#fff' : plan.accent,
                    fontWeight: 600, fontSize: 14, borderRadius: 10, cursor: 'pointer',
                    transition: 'all 0.2s',
                  }}
                  onMouseEnter={e => { if (!plan.featured) { e.currentTarget.style.background = plan.accent; e.currentTarget.style.color = '#fff' } }}
                  onMouseLeave={e => { if (!plan.featured) { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = plan.accent } }}
                >
                  {plan.cta} →
                </button>
              </motion.div>
            ))}
          </motion.div>

          <motion.p
            initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }}
            style={{ textAlign: 'center', marginTop: 24, color: 'var(--text-3)', fontSize: 12 }}
          >
            Razorpay payments · UPI, cards, netbanking accepted · GST invoice provided
          </motion.p>
        </div>
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
            Start building smarter today
          </h2>
          <p style={{ color: 'var(--text-2)', fontSize: 16, marginBottom: 40 }}>
            Free tier available. No credit card. Works in English, Tamil, and Hindi.
          </p>
          <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
            <button onClick={onSignUp} className="btn btn-primary" style={{ padding: '14px 40px', fontSize: 16 }}>
              Start Free →
            </button>
            <button onClick={onSignIn} className="btn btn-outline" style={{ padding: '14px 32px', fontSize: 16 }}>
              Sign In
            </button>
          </div>
          <div style={{ marginTop: 20, color: 'var(--text-3)', fontSize: 12 }}>
            Demo: <code style={{ color: 'var(--text-2)' }}>admin@agentic.local</code> / <code style={{ color: 'var(--text-2)' }}>admin123</code>
          </div>
        </motion.div>
      </section>

      {/* ── Footer ── */}
      <footer style={{
        borderTop: '1px solid var(--border)',
        padding: '24px 24px',
        maxWidth: 1100, margin: '0 auto',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
          <span style={{ color: 'var(--text-3)', fontSize: 12 }}>AI Agentic · FastAPI + React 18 · © 2026 Chandru</span>
          <div style={{ display: 'flex', gap: 20, alignItems: 'center' }}>
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
            {[
              { label: 'Privacy Policy', onClick: () => setShowPrivacy(true) },
              { label: 'Terms of Service', onClick: () => setShowTerms(true) },
              { label: 'Sign In', onClick: onSignIn },
            ].map(item => (
              <button key={item.label} onClick={item.onClick}
                style={{ background: 'none', border: 'none', color: 'var(--text-3)', fontSize: 12, cursor: 'pointer', padding: 0 }}
                onMouseEnter={e => (e.currentTarget.style.color = 'var(--text-2)')}
                onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-3)')}
              >{item.label}</button>
            ))}
          </div>
        </div>
        <div style={{ marginTop: 12, fontSize: 11, color: 'var(--text-3)', textAlign: 'center' }}>
          AI outputs are for guidance only. Verify CA/tax advice with a licensed Chartered Accountant.
        </div>
      </footer>

      {/* ── WhatsApp Support Button ── */}
      <a
        href="https://wa.me/919999999999?text=Hi%2C%20I%27m%20interested%20in%20AI%20Agentic%20for%20my%20business"
        target="_blank" rel="noopener noreferrer"
        title="Chat with us on WhatsApp"
        style={{
          position: 'fixed', bottom: 24, right: 24, zIndex: 200,
          width: 52, height: 52, borderRadius: '50%',
          background: '#25D366',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 4px 20px rgba(37,211,102,0.5)',
          textDecoration: 'none', fontSize: 26,
          transition: 'transform 0.2s, box-shadow 0.2s',
        }}
        onMouseEnter={e => { e.currentTarget.style.transform = 'scale(1.1)'; e.currentTarget.style.boxShadow = '0 6px 28px rgba(37,211,102,0.65)' }}
        onMouseLeave={e => { e.currentTarget.style.transform = 'scale(1)'; e.currentTarget.style.boxShadow = '0 4px 20px rgba(37,211,102,0.5)' }}
      >
        💬
      </a>

      {/* ── Modals ── */}
      <AnimatePresence>
        {showPrivacy && (
          <motion.div key="privacy" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <Modal title="Privacy Policy" text={PRIVACY_TEXT} onClose={() => setShowPrivacy(false)} />
          </motion.div>
        )}
        {showTerms && (
          <motion.div key="terms" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <Modal title="Terms of Service" text={TERMS_TEXT} onClose={() => setShowTerms(false)} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
