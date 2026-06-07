// frontend/src/pages/LandingPage.tsx — Marketing / portfolio landing page
// First thing employers, clients, and collaborators see

interface Props {
  onSignIn: () => void
}

const FEATURES = [
  {
    icon: '🧰', color: '#10b981',
    title: '24+ ready-made assistants',
    desc: 'Pre-built AI for finance, legal, HR, sales, healthcare, agriculture, education and more — ready the moment you log in.',
  },
  {
    icon: '📚', color: '#22c55e',
    title: 'Answers from your documents',
    desc: 'Upload your files and get instant, accurate answers grounded in your own data — no more digging through folders.',
  },
  {
    icon: '🛡️', color: '#f59e0b',
    title: 'Your data stays safe',
    desc: 'Automatic detection & redaction of personal data, access control per user, and a full audit trail of every action.',
  },
  {
    icon: '🌐', color: '#06b6d4',
    title: 'Works in your language',
    desc: 'English, தமிழ் and हिन्दी across the verticals that need it — built for Indian businesses and beyond.',
  },
  {
    icon: '👁️', color: '#ec4899',
    title: 'You stay in control',
    desc: 'Sensitive actions — like sending an email or an offer letter — pause for your approval before anything happens.',
  },
  {
    icon: '🤝', color: '#06b6d4',
    title: 'Connects to your tools',
    desc: 'Plugs into Gmail, HubSpot, Salesforce, Twilio, Razorpay and more — turn on what you need with a single key.',
  },
  {
    icon: '⚡', color: '#f97316',
    title: 'No setup, instant results',
    desc: 'Nothing to install. Open a tool, fill a short form, and get a polished result in seconds.',
  },
  {
    icon: '💳', color: '#10b981',
    title: 'Per-client access & billing',
    desc: 'Give each client exactly the tools they need, on Free / Pro / Enterprise plans — paid via Stripe or UPI.',
  },
]

const VERTICALS = [
  { icon: '🌾', name: 'AgriTech',     badge: 'Agriculture' },
  { icon: '⚖️', name: 'Legal',        badge: 'Research' },
  { icon: '🔐', name: 'Cybersec',     badge: 'Security' },
  { icon: '☎️', name: 'Receptionist', badge: 'Support' },
  { icon: '📋', name: 'Form Reader',  badge: 'OCR' },
  { icon: '📧', name: 'Email Mgr',    badge: 'Gmail' },
  { icon: '💼', name: 'Sales & CRM',  badge: 'Revenue' },
  { icon: '🧮', name: 'Accountant',   badge: 'Finance' },
  { icon: '👥', name: 'HR Assistant', badge: 'People' },
  { icon: '📱', name: 'Social Media', badge: 'Marketing' },
  { icon: '📊', name: 'Data Analyst', badge: 'Insights' },
  { icon: '🏥', name: 'Healthcare',   badge: 'Clinics' },
  { icon: '🏘️', name: 'Real Estate',  badge: 'Property' },
  { icon: '📚', name: 'EdTech',        badge: 'Education' },
]

const TECH = [
  { name: 'FastAPI',       color: '#009688' },
  { name: 'LangGraph',     color: '#10b981' },
  { name: 'OpenAI GPT-4o', color: '#10a37f' },
  { name: 'Ollama llama3', color: '#f59e0b' },
  { name: 'React 18',      color: '#61dafb' },
  { name: 'TypeScript',    color: '#3178c6' },
  { name: 'FAISS',         color: '#4c90e8' },
  { name: 'ChromaDB',      color: '#e879f9' },
  { name: 'PostgreSQL',    color: '#336791' },
  { name: 'Redis',         color: '#dc2626' },
  { name: 'Neo4j',         color: '#00b4cc' },
  { name: 'LangSmith',     color: '#10b981' },
  { name: 'MLflow',        color: '#0194e2' },
  { name: 'Prometheus',    color: '#e6522c' },
  { name: 'Docker',        color: '#2496ed' },
  { name: 'Whisper STT',   color: '#22c55e' },
]

const STATS = [
  { value: '24+',  label: 'AI Tools' },
  { value: '11',   label: 'Business Domains' },
  { value: '3',    label: 'Languages' },
  { value: '100%', label: 'PII-Safe & Compliant' },
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

      {/* ── Navbar ─────────────────────────────────────────────────── */}
      <nav style={{
        position: 'sticky', top: 0, zIndex: 50,
        background: 'rgba(15,17,23,0.85)',
        backdropFilter: 'blur(12px)',
        borderBottom: '1px solid #1e2535',
        padding: '0 32px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        height: 56,
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
              background: '#1e2535', color: '#9ca3af',
              textDecoration: 'none', border: '1px solid #374151',
            }}>
            GitHub
          </a>
          <button onClick={onSignIn} style={{
            padding: '7px 20px', borderRadius: 8, fontSize: 13, fontWeight: 600,
            background: 'linear-gradient(90deg, #10b981, #06b6d4)',
            color: '#fff', border: 'none', cursor: 'pointer',
          }}>
            Sign In →
          </button>
        </div>
      </nav>

      {/* ── Hero ────────────────────────────────────────────────────── */}
      <section style={{
        padding: '80px 32px 60px',
        textAlign: 'center',
        background: 'radial-gradient(ellipse 80% 60% at 50% -10%, rgba(16,185,129,0.15) 0%, transparent 60%)',
      }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          padding: '5px 14px', borderRadius: 20,
          background: 'rgba(16,185,129,0.12)', border: '1px solid rgba(16,185,129,0.3)',
          fontSize: 12, color: '#5eead4', marginBottom: 28,
        }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#22c55e', display: 'inline-block' }} />
          Live demo · No setup · Try every tool free
        </div>

        <h1 style={{
          fontSize: 'clamp(32px, 6vw, 64px)',
          fontWeight: 800, lineHeight: 1.1,
          margin: '0 0 20px',
          background: 'linear-gradient(135deg, #fff 40%, #5eead4)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
        }}>
          One AI Workspace<br />for Your Whole Business
        </h1>

        <p style={{
          fontSize: 18, color: '#9ca3af', maxWidth: 620, margin: '0 auto 36px',
          lineHeight: 1.7,
        }}>
          24+ ready-to-use AI assistants for finance, legal, HR, sales, healthcare,
          agriculture and more — in English, Tamil & Hindi. No setup, works instantly,
          and your data stays private.
        </p>

        <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
          <button onClick={onSignIn} style={{
            padding: '13px 32px', borderRadius: 10, fontSize: 15, fontWeight: 600,
            background: 'linear-gradient(90deg, #10b981, #06b6d4)',
            color: '#fff', border: 'none', cursor: 'pointer',
            boxShadow: '0 0 30px rgba(16,185,129,0.35)',
          }}>
            🚀 Launch Dashboard
          </button>
          <a
            href="https://github.com/chandrukumar-AIML/ai-agentic-assistant"
            target="_blank" rel="noopener noreferrer"
            style={{
              padding: '13px 32px', borderRadius: 10, fontSize: 15, fontWeight: 600,
              background: 'rgba(255,255,255,0.06)', color: '#e2e8f0',
              border: '1px solid #374151', textDecoration: 'none',
              display: 'inline-block',
            }}>
            ⭐ View on GitHub
          </a>
        </div>
      </section>

      {/* ── Stats ───────────────────────────────────────────────────── */}
      <section style={{
        display: 'flex', justifyContent: 'center', gap: 0,
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

      {/* ── Features Grid ───────────────────────────────────────────── */}
      <section style={{ padding: '64px 32px', maxWidth: 1100, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 48 }}>
          <h2 style={{ fontSize: 32, fontWeight: 700, margin: '0 0 12px', color: '#fff' }}>
            Every Feature, Fully Integrated
          </h2>
          <p style={{ color: '#6b7280', fontSize: 15, margin: 0 }}>
            Not a demo — a real platform with backend, frontend, tests, and deploy config.
          </p>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
          gap: 16,
        }}>
          {FEATURES.map(f => (
            <div key={f.title} style={{
              background: '#161b27',
              border: '1px solid #1e2535',
              borderRadius: 12, padding: '20px 22px',
              transition: 'border-color 0.2s, transform 0.2s',
            }}
              onMouseEnter={e => {
                (e.currentTarget as HTMLDivElement).style.borderColor = f.color
                ;(e.currentTarget as HTMLDivElement).style.transform = 'translateY(-2px)'
              }}
              onMouseLeave={e => {
                (e.currentTarget as HTMLDivElement).style.borderColor = '#1e2535'
                ;(e.currentTarget as HTMLDivElement).style.transform = 'translateY(0)'
              }}
            >
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

      {/* ── Verticals ───────────────────────────────────────────────── */}
      <section style={{
        background: '#161b27',
        borderTop: '1px solid #1e2535', borderBottom: '1px solid #1e2535',
        padding: '56px 32px',
      }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 40 }}>
            <h2 style={{ fontSize: 28, fontWeight: 700, margin: '0 0 10px', color: '#fff' }}>
              A tool for every part of your business
            </h2>
            <p style={{ color: '#6b7280', fontSize: 14, margin: 0 }}>
              From accounting to agriculture — a dedicated AI assistant for each.
            </p>
          </div>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))',
            gap: 10,
          }}>
            {VERTICALS.map(v => (
              <div key={v.name} style={{
                background: '#0f1117', border: '1px solid #1e2535',
                borderRadius: 10, padding: '14px 16px',
                display: 'flex', alignItems: 'center', gap: 10,
              }}>
                <span style={{ fontSize: 20 }}>{v.icon}</span>
                <div>
                  <div style={{ fontWeight: 500, fontSize: 13, color: '#e2e8f0' }}>{v.name}</div>
                  <div style={{ fontSize: 10, color: '#4b5563', marginTop: 2 }}>{v.badge}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Tech Stack ──────────────────────────────────────────────── */}
      <section style={{ padding: '56px 32px', maxWidth: 1100, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 36 }}>
          <h2 style={{ fontSize: 26, fontWeight: 700, margin: '0 0 10px', color: '#fff' }}>
            Built With Best-in-Class Tech
          </h2>
          <p style={{ color: '#6b7280', fontSize: 14, margin: 0 }}>
            Reliable, production-grade technology you can trust
          </p>
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, justifyContent: 'center' }}>
          {TECH.map(t => (
            <span key={t.name} style={{
              padding: '6px 14px', borderRadius: 20,
              background: `${t.color}18`,
              border: `1px solid ${t.color}44`,
              color: t.color,
              fontSize: 12, fontWeight: 600,
            }}>{t.name}</span>
          ))}
        </div>
      </section>

      {/* ── What makes it different ─────────────────────────────────── */}
      <section style={{
        background: '#161b27',
        border: '1px solid #1e2535',
        borderRadius: 16,
        margin: '0 32px 64px',
        padding: '48px 40px',
        maxWidth: 1040, marginLeft: 'auto', marginRight: 'auto',
      }}>
        <h2 style={{ fontSize: 26, fontWeight: 700, marginBottom: 28, color: '#fff', textAlign: 'center' }}>
          Why This Platform Stands Out
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 20 }}>
          {[
            { title: '🏗️ Portfolio-Ready',    text: 'Full project — not a Jupyter notebook. CI/CD, Docker, tests, README, deploy guides included.' },
            { title: '🏢 Enterprise-Grade',   text: 'JWT+RBAC, PII/PHI detection, audit logs, HITL approvals — features real companies pay for.' },
            { title: '💰 100% Free to Deploy', text: 'Vercel (frontend) + Render (backend) + Neon (DB) + Upstash (Redis) = $0/month.' },
            { title: '🔌 Extensible',          text: 'MCP + A2A protocols, webhook manager, API keys — plug into any existing business stack.' },
            { title: '🌐 Multi-domain',        text: '12 vertical agents cover agriculture to DevOps — show any client their exact use case.' },
            { title: '📈 Observable',           text: 'LangSmith + MLflow + Prometheus + cost tracking — production monitoring from day one.' },
          ].map(p => (
            <div key={p.title} style={{ display: 'flex', gap: 14 }}>
              <div style={{ flexShrink: 0 }}>
                <div style={{ fontSize: 22 }}>{p.title.slice(0,2)}</div>
              </div>
              <div>
                <div style={{ fontWeight: 600, fontSize: 14, color: '#e2e8f0', marginBottom: 6 }}>{p.title.slice(3)}</div>
                <div style={{ fontSize: 12, color: '#6b7280', lineHeight: 1.6 }}>{p.text}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Final CTA ───────────────────────────────────────────────── */}
      <section style={{
        textAlign: 'center', padding: '56px 32px 80px',
        background: 'radial-gradient(ellipse 60% 80% at 50% 100%, rgba(16,185,129,0.12) 0%, transparent 70%)',
      }}>
        <h2 style={{ fontSize: 32, fontWeight: 700, marginBottom: 12, color: '#fff' }}>
          Ready to explore?
        </h2>
        <p style={{ color: '#6b7280', fontSize: 15, marginBottom: 32 }}>
          Login with demo credentials — no setup needed.
        </p>
        <button onClick={onSignIn} style={{
          padding: '14px 40px', borderRadius: 10, fontSize: 16, fontWeight: 700,
          background: 'linear-gradient(90deg, #10b981, #06b6d4)',
          color: '#fff', border: 'none', cursor: 'pointer',
          boxShadow: '0 0 40px rgba(16,185,129,0.4)',
        }}>
          🚀 Launch the Dashboard
        </button>
        <div style={{ marginTop: 20, color: '#374151', fontSize: 12 }}>
          Demo: <code style={{ color: '#6b7280' }}>admin@agentic.local</code> / <code style={{ color: '#6b7280' }}>admin123</code>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────────────────── */}
      <footer style={{
        borderTop: '1px solid #1e2535',
        padding: '20px 32px',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        flexWrap: 'wrap', gap: 12,
      }}>
        <div style={{ color: '#374151', fontSize: 12 }}>
AI Agentic · Built with FastAPI + React · © 2026
        </div>
        <div style={{ display: 'flex', gap: 20 }}>
          {[
            { label: 'GitHub', href: 'https://github.com/chandrukumar-AIML/ai-agentic-assistant' },
            { label: 'API Docs', href: 'http://localhost:8000/docs' },
            { label: 'Sign In', href: '#', onClick: onSignIn },
          ].map(l => (
            <a key={l.label}
              href={l.href}
              onClick={l.onClick ? (e) => { e.preventDefault(); l.onClick!() } : undefined}
              target={l.href !== '#' ? '_blank' : undefined}
              rel="noopener noreferrer"
              style={{ color: '#4b5563', fontSize: 12, textDecoration: 'none' }}>
              {l.label}
            </a>
          ))}
        </div>
      </footer>
    </div>
  )
}
