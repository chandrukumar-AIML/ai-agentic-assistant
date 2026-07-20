// frontend/src/pages/LandingPage.tsx
interface Props {
  onSignIn: () => void
}

const AGENTS = [
  {
    icon: 'SM', gradient: 'linear-gradient(135deg, #8b5cf6, #6366f1)',
    name: 'Social Media Agent',
    desc: 'Generate posts, hashtags, captions, and campaign briefs for Instagram, LinkedIn, and Twitter.',
    tools: ['Post Generator', 'Caption Writer', 'Hashtag Research', 'SEO Audit', 'Campaign Planner', 'Competitor Analysis'],
  },
  {
    icon: 'CA', gradient: 'linear-gradient(135deg, #f59e0b, #d97706)',
    name: 'CA & Accounting Agent',
    desc: 'India-focused accounting AI. GST queries, TDS, invoice drafting, ITR advice, audit checklists.',
    tools: ['GST Query Bot', 'TDS Calculator', 'Invoice Drafter', 'Compliance Deadlines', 'ITR Advisor', 'Audit Checklist'],
  },
  {
    icon: 'CS', gradient: 'linear-gradient(135deg, #10b981, #059669)',
    name: 'Customer Support Agent',
    desc: 'WhatsApp-first support AI. Handle FAQs, qualify leads, analyze sentiment, auto-draft replies.',
    tools: ['FAQ Bot', 'WhatsApp Drafter', 'Sentiment Analyzer', 'Complaint Handler', 'Lead Qualifier', 'Weekly Report'],
  },
]

const FEATURES = [
  { icon: '🌐', color: '#06b6d4', title: '3 Languages', desc: 'Every agent responds in English, Tamil, and Hindi — built for Indian businesses.' },
  { icon: '🛡️', color: '#f59e0b', title: 'PII-Safe & Compliant', desc: 'Personal data detection and redaction. Full audit trail of every AI action.' },
  { icon: '⚡', color: '#10b981', title: 'No Setup Required', desc: 'Open a tool, fill a form, get a polished result in seconds. Nothing to install.' },
  { icon: '🤝', color: '#a855f7', title: 'Sells as Combo or Solo', desc: 'License each agent separately or bundle all three — flexible for any client.' },
  { icon: '☁️', color: '#3b82f6', title: 'Cloud-Hosted 24/7', desc: 'FastAPI backend on Render, React frontend on Vercel. Always on, always fast.' },
  { icon: '🔄', color: '#f97316', title: 'Groq + Gemini + Ollama', desc: 'Free-tier LLM chain: Groq primary, Gemini fallback, Ollama for local models.' },
]

const STATS = [
  { value: '3',    label: 'Core Agents' },
  { value: '3',    label: 'Languages' },
  { value: '24/7', label: 'Availability' },
  { value: '100%', label: 'PII-Safe' },
]

export default function LandingPage({ onSignIn }: Props) {
  return (
    <div style={{
      minHeight: '100vh',
      background: '#0f1117',
      color: '#e2e8f0',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      overflowX: 'hidden',
    }}>

      {/* Navbar */}
      <nav style={{
        position: 'sticky', top: 0, zIndex: 50,
        background: 'rgba(15,17,23,0.85)', backdropFilter: 'blur(12px)',
        borderBottom: '1px solid #1e2535',
        padding: '0 32px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: 56,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 32, height: 32, borderRadius: 10,
            background: 'linear-gradient(135deg, #10b981, #06b6d4)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 16, fontWeight: 800, color: '#fff',
          }}>A</div>
          <span style={{ fontWeight: 700, fontSize: 15, color: '#fff' }}>AI Agentic</span>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <a
            href="https://github.com/chandrukumar-AIML/ai-agentic-assistant"
            target="_blank" rel="noopener noreferrer"
            style={{
              padding: '7px 16px', borderRadius: 8, fontSize: 13,
              background: '#1e2535', color: '#9ca3af', textDecoration: 'none', border: '1px solid #374151',
            }}>GitHub</a>
          <button onClick={onSignIn} style={{
            padding: '7px 20px', borderRadius: 8, fontSize: 13, fontWeight: 600,
            background: 'linear-gradient(90deg, #10b981, #06b6d4)',
            color: '#fff', border: 'none', cursor: 'pointer',
          }}>Sign In</button>
        </div>
      </nav>

      {/* Hero */}
      <section style={{
        padding: '80px 32px 60px', textAlign: 'center',
        background: 'radial-gradient(ellipse 80% 60% at 50% -10%, rgba(16,185,129,0.15) 0%, transparent 60%)',
      }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          padding: '5px 14px', borderRadius: 20,
          background: 'rgba(16,185,129,0.12)', border: '1px solid rgba(16,185,129,0.3)',
          fontSize: 12, color: '#5eead4', marginBottom: 28,
        }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#22c55e', display: 'inline-block' }} />
          3 Core Agents · 3 Languages · Live Demo
        </div>

        <h1 style={{
          fontSize: 'clamp(32px, 6vw, 60px)', fontWeight: 800, lineHeight: 1.1,
          margin: '0 0 20px',
          background: 'linear-gradient(135deg, #fff 40%, #5eead4)',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
        }}>
          AI Agents Built for<br />Indian Businesses
        </h1>

        <p style={{ fontSize: 18, color: '#9ca3af', maxWidth: 600, margin: '0 auto 36px', lineHeight: 1.7 }}>
          Social Media, CA & Accounting, and Customer Support — three production-ready AI
          agents in English, Tamil, and Hindi. No setup, works instantly.
        </p>

        <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
          <button onClick={onSignIn} style={{
            padding: '13px 32px', borderRadius: 10, fontSize: 15, fontWeight: 600,
            background: 'linear-gradient(90deg, #10b981, #06b6d4)',
            color: '#fff', border: 'none', cursor: 'pointer',
            boxShadow: '0 0 30px rgba(16,185,129,0.35)',
          }}>Launch Dashboard</button>
          <a
            href="https://github.com/chandrukumar-AIML/ai-agentic-assistant"
            target="_blank" rel="noopener noreferrer"
            style={{
              padding: '13px 32px', borderRadius: 10, fontSize: 15, fontWeight: 600,
              background: 'rgba(255,255,255,0.06)', color: '#e2e8f0',
              border: '1px solid #374151', textDecoration: 'none', display: 'inline-block',
            }}>View on GitHub</a>
        </div>
      </section>

      {/* Stats */}
      <section style={{
        display: 'flex', justifyContent: 'center',
        borderTop: '1px solid #1e2535', borderBottom: '1px solid #1e2535',
        background: '#161b27', flexWrap: 'wrap',
      }}>
        {STATS.map((s, i) => (
          <div key={s.label} style={{
            padding: '28px 40px', textAlign: 'center', flex: '1 1 150px',
            borderRight: i < STATS.length - 1 ? '1px solid #1e2535' : 'none',
          }}>
            <div style={{ fontSize: 36, fontWeight: 800, color: '#5eead4', lineHeight: 1 }}>{s.value}</div>
            <div style={{ fontSize: 12, color: '#6b7280', marginTop: 6, fontWeight: 500 }}>{s.label}</div>
          </div>
        ))}
      </section>

      {/* 3 Core Agents */}
      <section style={{ padding: '64px 32px', maxWidth: 1100, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <h2 style={{ fontSize: 30, fontWeight: 700, margin: '0 0 12px', color: '#fff' }}>3 Core Agents</h2>
          <p style={{ color: '#6b7280', fontSize: 15, margin: 0 }}>
            Each agent is fully functional, multi-language, and deployable independently.
          </p>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {AGENTS.map(agent => (
            <div key={agent.name} style={{
              background: '#161b27', border: '1px solid #1e2535',
              borderRadius: 14, padding: '22px 24px',
              display: 'flex', gap: 20, alignItems: 'flex-start',
            }}>
              <div style={{
                width: 52, height: 52, borderRadius: 14, flexShrink: 0,
                background: agent.gradient,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 13, fontWeight: 800, color: '#fff', letterSpacing: 0.5,
              }}>{agent.icon}</div>
              <div style={{ flex: 1 }}>
                <div style={{ color: '#e2e8f0', fontSize: 16, fontWeight: 700, marginBottom: 6 }}>{agent.name}</div>
                <div style={{ color: '#9ca3af', fontSize: 13, lineHeight: 1.6, marginBottom: 12 }}>{agent.desc}</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {agent.tools.map(t => (
                    <span key={t} style={{
                      fontSize: 11, padding: '3px 10px', borderRadius: 20,
                      background: '#1e2535', color: '#6b7280',
                    }}>{t}</span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section style={{ padding: '0 32px 64px', maxWidth: 1100, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <h2 style={{ fontSize: 30, fontWeight: 700, margin: '0 0 12px', color: '#fff' }}>What you get</h2>
          <p style={{ color: '#6b7280', fontSize: 15, margin: 0 }}>
            Production-ready, multilingual, and deployable at zero monthly cost.
          </p>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 16 }}>
          {FEATURES.map(f => (
            <div key={f.title} style={{
              background: '#161b27', border: '1px solid #1e2535',
              borderRadius: 12, padding: '20px 22px',
            }}>
              <div style={{
                width: 40, height: 40, borderRadius: 10,
                background: `${f.color}22`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 20, marginBottom: 14,
              }}>{f.icon}</div>
              <div style={{ fontWeight: 600, fontSize: 14, color: '#e2e8f0', marginBottom: 8 }}>{f.title}</div>
              <div style={{ fontSize: 12, color: '#6b7280', lineHeight: 1.6 }}>{f.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section style={{
        textAlign: 'center', padding: '56px 32px 80px',
        background: 'radial-gradient(ellipse 60% 80% at 50% 100%, rgba(16,185,129,0.12) 0%, transparent 70%)',
      }}>
        <h2 style={{ fontSize: 30, fontWeight: 700, marginBottom: 12, color: '#fff' }}>Ready to explore?</h2>
        <p style={{ color: '#6b7280', fontSize: 15, marginBottom: 32 }}>
          Login with demo credentials — no setup needed.
        </p>
        <button onClick={onSignIn} style={{
          padding: '14px 40px', borderRadius: 10, fontSize: 16, fontWeight: 700,
          background: 'linear-gradient(90deg, #10b981, #06b6d4)',
          color: '#fff', border: 'none', cursor: 'pointer',
          boxShadow: '0 0 40px rgba(16,185,129,0.4)',
        }}>Launch Dashboard</button>
        <div style={{ marginTop: 20, color: '#374151', fontSize: 12 }}>
          Demo: <code style={{ color: '#6b7280' }}>admin@agentic.local</code> / <code style={{ color: '#6b7280' }}>admin123</code>
        </div>
      </section>

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid #1e2535', padding: '20px 32px',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12,
      }}>
        <div style={{ color: '#374151', fontSize: 12 }}>AI Agentic · FastAPI + React · 2026</div>
        <div style={{ display: 'flex', gap: 20 }}>
          {[
            { label: 'GitHub', href: 'https://github.com/chandrukumar-AIML/ai-agentic-assistant' },
            { label: 'API Docs', href: 'https://ai-agentic-backend-ywdx.onrender.com/docs' },
          ].map(l => (
            <a key={l.label} href={l.href} target="_blank" rel="noopener noreferrer"
              style={{ color: '#4b5563', fontSize: 12, textDecoration: 'none' }}>{l.label}</a>
          ))}
          <a href="#" onClick={e => { e.preventDefault(); onSignIn() }}
            style={{ color: '#4b5563', fontSize: 12, textDecoration: 'none' }}>Sign In</a>
        </div>
      </footer>
    </div>
  )
}
