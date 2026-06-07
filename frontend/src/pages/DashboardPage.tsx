// frontend/src/pages/DashboardPage.tsx
import { StatCard } from '../components/ui'

// Client-facing tool catalogue — friendly names + outcome-focused descriptions.
const TOOLS = [
  { name: 'AgriTech',        icon: '🌾', desc: 'Crop advisory, mandi prices & weather — Tamil/Hindi/English', color: '#84cc16' },
  { name: 'Legal',           icon: '⚖️', desc: 'Contract review, NDAs & Indian case-law research',          color: '#f59e0b' },
  { name: 'Accountant',      icon: '🧮', desc: 'GST, TDS, invoices & financial analysis',                  color: '#ec4899' },
  { name: 'HR Assistant',    icon: '👥', desc: 'Resume screening, JDs, offers & onboarding',               color: '#a855f7' },
  { name: 'Sales & CRM',     icon: '💼', desc: 'Lead scoring, outreach & meeting prep',                    color: '#f59e0b' },
  { name: 'Social & Marketing', icon: '📱', desc: 'Posts, hashtags, SEO audits & campaign briefs',         color: '#06b6d4' },
  { name: 'Healthcare',      icon: '🏥', desc: 'Patient intake, report summaries & triage',                color: '#ef4444' },
  { name: 'Real Estate',     icon: '🏘️', desc: 'Listings, lease drafts & investment ROI',                 color: '#10b981' },
  { name: 'EdTech',          icon: '📚', desc: 'Course outlines, quizzes & lesson plans',                  color: '#3b82f6' },
  { name: 'Receptionist',    icon: '☎️', desc: '24/7 chat, FAQs & appointment booking',                   color: '#06b6d4' },
  { name: 'Cybersecurity',   icon: '🔐', desc: 'Log analysis, CVE lookup & security review',               color: '#ef4444' },
  { name: 'Data Analyst',    icon: '📊', desc: 'Ask in plain English — get charts & insights',             color: '#10b981' },
  { name: 'Form Reader',     icon: '📋', desc: 'Extract data from PAN / Aadhaar / GST forms',              color: '#06b6d4' },
  { name: 'Email Manager',   icon: '📧', desc: 'Draft, summarise & manage your inbox',                     color: '#22c55e' },
  { name: 'Code Assistant',  icon: '💻', desc: 'Generate, debug & review code',                            color: '#3b82f6' },
  { name: 'DevOps',          icon: '⚙️', desc: 'CI/CD, Docker, Kubernetes & incident debugging',           color: '#10b981' },
  { name: 'QA Engineer',     icon: '🧪', desc: 'Test cases, bug analysis & test plans',                    color: '#a855f7' },
  { name: 'Project Manager', icon: '🗂️', desc: 'User stories, sprint plans & roadmaps',                   color: '#f59e0b' },
  { name: 'ML Engineer',     icon: '🤖', desc: 'Experiment design, model eval & drift analysis',           color: '#06b6d4' },
  { name: 'Database (DBA)',  icon: '🗄️', desc: 'Query optimisation, schema design & migrations',          color: '#84cc16' },
  { name: 'Tech Lead',       icon: '🏗️', desc: 'Architecture decisions, API design & reviews',            color: '#a855f7' },
  { name: 'Compliance Guard',icon: '🛡️', desc: 'Automatic PII redaction & policy checks',                 color: '#10b981' },
  { name: 'Document Export', icon: '📄', desc: 'One-click export to PDF, Excel & PowerPoint',              color: '#06b6d4' },
  { name: 'Billing & Plans', icon: '💳', desc: 'Subscriptions via Stripe & Razorpay (UPI)',               color: '#22c55e' },
]

export default function DashboardPage() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#0f1117', overflow: 'hidden' }}>
      {/* Header */}
      <div style={{
        padding: '20px 28px', borderBottom: '1px solid #1e2535',
        background: 'linear-gradient(135deg, #161b27 0%, #0f1117 100%)',
        flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 40, height: 40, borderRadius: 11,
            background: 'linear-gradient(135deg, #10b981, #06b6d4)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20,
          }}>⚡</div>
          <div>
            <div style={{ color: '#e2e8f0', fontSize: 21, fontWeight: 700 }}>AI Agentic</div>
            <div style={{ color: '#6b7280', fontSize: 13 }}>Your all-in-one AI workspace for business</div>
          </div>
        </div>
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: '20px 28px' }}>
        {/* Value stats — client-meaningful, not dev metrics */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 24 }}>
          <StatCard label="AI Tools"      value="24+"   icon="🧰" trend="Ready to use" />
          <StatCard label="Languages"     value="3"     icon="🌐" trend="EN · தமிழ் · हिन्दी" />
          <StatCard label="Availability"  value="24/7"  icon="☁️" trend="Cloud-hosted" />
          <StatCard label="Data Security" value="100%"  icon="🔒" trend="PII-safe & compliant" />
        </div>

        {/* Tools — the thing clients actually care about, shown first */}
        <div style={{ color: '#e2e8f0', fontSize: 15, fontWeight: 600, marginBottom: 4 }}>Your AI Tools</div>
        <div style={{ color: '#6b7280', fontSize: 12, marginBottom: 14 }}>
          Pick a tool from the sidebar to get started — every assistant is ready to use.
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12 }}>
          {TOOLS.map(t => (
            <div key={t.name} style={{
              background: '#161b27', border: '1px solid #1e2535',
              borderRadius: 10, padding: 14, display: 'flex', gap: 12,
              borderLeft: `3px solid ${t.color}`,
            }}>
              <span style={{ fontSize: 24, flexShrink: 0 }}>{t.icon}</span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 600, marginBottom: 3 }}>{t.name}</div>
                <div style={{ color: '#6b7280', fontSize: 11.5, lineHeight: 1.45 }}>{t.desc}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Built with — credibility footer (kept subtle, below the tools) */}
        <div style={{ marginTop: 28 }}>
          <div style={{ color: '#4b5563', fontSize: 11, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 10 }}>
            Built with
          </div>
          <div style={{
            background: 'rgba(16,185,129,0.05)', border: '1px solid #1e2535',
            borderRadius: 12, padding: '14px 20px',
            display: 'flex', alignItems: 'center', gap: 20, flexWrap: 'wrap',
          }}>
            {[
              { label: 'FastAPI', icon: '⚡' },
              { label: 'LangGraph', icon: '🕸️' },
              { label: 'OpenAI GPT-4o', icon: '🤖' },
              { label: 'Ollama (local LLM)', icon: '🦙' },
              { label: 'FAISS + ChromaDB', icon: '🗃️' },
              { label: 'Redis + Postgres', icon: '💾' },
              { label: 'Presidio (PII)', icon: '🔒' },
            ].map(tech => (
              <div key={tech.label} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                <span style={{ fontSize: 14 }}>{tech.icon}</span>
                <span style={{ color: '#6b7280', fontSize: 12, fontWeight: 500 }}>{tech.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
