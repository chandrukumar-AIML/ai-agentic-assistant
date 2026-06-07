// frontend/src/pages/DashboardPage.tsx
import { useEffect, useState } from 'react'
import { StatCard, Card } from '../components/ui'

const FEATURES = [
  { num: 1,  name: 'Guardian Agent',     icon: '🛡️', desc: 'HIPAA/GDPR/SOC2/EU AI Act compliance',  status: 'live', color: '#10b981' },
  { num: 2,  name: 'A2A Protocol',       icon: '🔗', desc: 'Google Agent-to-Agent SSE streaming',    status: 'live', color: '#06b6d4' },
  { num: 3,  name: 'Memory System',      icon: '🧠', desc: 'Redis + PostgreSQL long-term memory',    status: 'live', color: '#a855f7' },
  { num: 4,  name: 'Task Scheduler',     icon: '⏰', desc: 'APScheduler + Celery + 4 trigger types', status: 'live', color: '#10b981' },
  { num: 5,  name: 'Commerce',           icon: '🛒', desc: 'Calendly + DocuSign + Stripe',           status: 'live', color: '#06b6d4' },
  { num: 6,  name: 'HITL Approvals',     icon: '👁️', desc: 'LangGraph interrupt + 30min timeout',   status: 'live', color: '#ec4899' },
  { num: 7,  name: 'Output Generator',   icon: '📄', desc: 'PDF / PPTX / Excel / Image / Audio',    status: 'live', color: '#06b6d4' },
  { num: 8,  name: 'Billing & Plans',    icon: '💳', desc: 'Stripe + Razorpay + FREE/PRO/ENTERPRISE',status: 'live', color: '#22c55e' },
  { num: 9,  name: 'AgriTech',           icon: '🌾', desc: 'Tamil/Hindi crop disease + mandi prices',status: 'live', color: '#84cc16' },
  { num: 10, name: 'Legal Research',     icon: '⚖️', desc: 'IndianKanoon + IPC/CPC/CrPC RAG',       status: 'live', color: '#f59e0b' },
  { num: 11, name: 'Cybersecurity',      icon: '🔐', desc: 'Log anomaly + NVD CVE + PDF reports',   status: 'live', color: '#ef4444' },
  { num: 12, name: 'A/B Testing',        icon: '⚗️', desc: "Welch's t-test + auto-promote + MLflow", status: 'live', color: '#10b981' },
  { num: 13, name: 'Receptionist',       icon: '☎️', desc: 'Twilio Voice + WhatsApp + JS widget',   status: 'live', color: '#06b6d4' },
  { num: 14, name: 'Form Reader',        icon: '📋', desc: 'PAN/Aadhaar/GSTIN + GPT-4o Vision',     status: 'live', color: '#06b6d4' },
  { num: 15, name: 'Email Manager',      icon: '📧', desc: 'Gmail + Outlook OAuth + HITL send',      status: 'live', color: '#22c55e' },
  { num: 16, name: 'Sales & CRM',        icon: '💼', desc: 'BANT scoring + HubSpot + Salesforce',   status: 'live', color: '#f59e0b' },
  { num: 17, name: 'Accountant',         icon: '🧮', desc: 'GST/TDS/GSTR-1/GSTR-3B India',         status: 'live', color: '#ec4899' },
  { num: 18, name: 'HR Assistant',       icon: '👥', desc: 'Resume screen + JD + Offer + DocuSign', status: 'live', color: '#a855f7' },
  { num: 19, name: 'Social Media',       icon: '📱', desc: 'LinkedIn + Twitter + DALL-E 3 + Buffer', status: 'live', color: '#06b6d4' },
]

export default function DashboardPage() {
  const [serverInfo, setServerInfo] = useState<any>(null)
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    fetch((import.meta.env.VITE_API_URL?.replace('/api','') || 'http://localhost:8000') + '/').then(r => r.json()).then(setServerInfo).catch(() => {})
    const t = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(t)
  }, [])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#0f1117', overflow: 'hidden' }}>
      {/* Header */}
      <div style={{
        padding: '20px 28px', borderBottom: '1px solid #1e2535',
        background: 'linear-gradient(135deg, #161b27 0%, #0f1117 100%)',
        flexShrink: 0,
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
              <div style={{
                width: 36, height: 36, borderRadius: 10,
                background: 'linear-gradient(135deg, #10b981, #06b6d4)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 18,
              }}>⚡</div>
              <div>
                <div style={{ color: '#e2e8f0', fontSize: 20, fontWeight: 700 }}>AI Agentic Assistant V2</div>
                <div style={{ color: '#6b7280', fontSize: 12 }}>Your all-in-one AI workspace for business</div>
              </div>
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ color: '#6b7280', fontSize: 11 }}>{time.toLocaleDateString()}</div>
            <div style={{ color: '#4b5563', fontSize: 11 }}>{time.toLocaleTimeString()}</div>
            {serverInfo && (
              <div style={{ marginTop: 4, display: 'flex', alignItems: 'center', gap: 4, justifyContent: 'flex-end' }}>
                <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#22c55e', display: 'inline-block' }} />
                <span style={{ color: '#22c55e', fontSize: 11, fontWeight: 600 }}>Backend Online</span>
              </div>
            )}
          </div>
        </div>
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: '20px 28px' }}>
        {/* Stats Row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 24 }}>
          <StatCard label="Total Features"    value="19" icon="🚀" trend="All Live" />
          <StatCard label="API Endpoints"     value="80+" icon="🔌" trend="+8 this sprint" />
          <StatCard label="LLM Model"         value="Llama3" icon="🤖" trend="Ollama Active" />
          <StatCard label="Compliance Checks" value="100%" icon="🛡️" trend="HIPAA/GDPR" />
        </div>

        {/* Architecture Banner */}
        <div style={{
          background: 'linear-gradient(135deg, rgba(16,185,129,0.1) 0%, rgba(139,92,246,0.1) 100%)',
          border: '1px solid rgba(16,185,129,0.3)',
          borderRadius: 12, padding: '14px 20px', marginBottom: 24,
          display: 'flex', alignItems: 'center', gap: 20, flexWrap: 'wrap',
        }}>
          {[
            { label: 'FastAPI', icon: '⚡' },
            { label: 'LangGraph', icon: '🕸️' },
            { label: 'OpenAI GPT-4o', icon: '🤖' },
            { label: 'Ollama Llama3', icon: '🦙' },
            { label: 'FAISS + ChromaDB', icon: '🗃️' },
            { label: 'Redis + Postgres', icon: '💾' },
            { label: 'MLflow + LangSmith', icon: '📊' },
            { label: 'Presidio PII', icon: '🔒' },
          ].map(tech => (
            <div key={tech.label} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
              <span style={{ fontSize: 14 }}>{tech.icon}</span>
              <span style={{ color: '#5eead4', fontSize: 12, fontWeight: 500 }}>{tech.label}</span>
            </div>
          ))}
        </div>

        {/* Feature Grid */}
        <div style={{ marginBottom: 12 }}>
          <div style={{ color: '#e2e8f0', fontSize: 14, fontWeight: 600, marginBottom: 14 }}>
Your AI Tools
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12 }}>
          {FEATURES.map(f => (
            <div key={f.num} style={{
              background: '#161b27', border: '1px solid #1e2535',
              borderRadius: 10, padding: 14, display: 'flex', gap: 12,
              transition: 'border-color 0.15s', cursor: 'default',
              borderLeft: `3px solid ${f.color}`,
            }}>
              <span style={{ fontSize: 24, flexShrink: 0 }}>{f.icon}</span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
                  <span style={{ color: '#e2e8f0', fontSize: 12, fontWeight: 600 }}>{f.name}</span>
                </div>
                <div style={{ color: '#6b7280', fontSize: 11, lineHeight: 1.4 }}>{f.desc}</div>
                <div style={{ marginTop: 6, display: 'flex', alignItems: 'center', gap: 4 }}>
                  <span style={{ width: 5, height: 5, borderRadius: '50%', background: '#22c55e', display: 'inline-block' }} />
                  <span style={{ color: '#22c55e', fontSize: 10 }}>Live</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Server Info */}
        {serverInfo && (
          <div style={{ marginTop: 24 }}>
            <div style={{
              background: '#161b27', border: '1px solid #1e2535',
              borderRadius: 10, padding: 16, display: 'flex', gap: 20, flexWrap: 'wrap',
            }}>
              <div>
                <div style={{ color: '#6b7280', fontSize: 11 }}>API Version</div>
                <div style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 600 }}>{serverInfo.version}</div>
              </div>
              <div>
                <div style={{ color: '#6b7280', fontSize: 11 }}>Documentation</div>
                <a href={`${import.meta.env.VITE_API_URL?.replace('/api','') || 'http://localhost:8000'}/docs`} target="_blank" rel="noreferrer"
                  style={{ color: '#10b981', fontSize: 13, fontWeight: 500 }}>
                  API Docs ↗
                </a>
              </div>
              <div>
                <div style={{ color: '#6b7280', fontSize: 11 }}>Phases Complete</div>
                <div style={{ color: '#22c55e', fontSize: 13, fontWeight: 600 }}>{serverInfo.phases}</div>
              </div>
              <div>
                <div style={{ color: '#6b7280', fontSize: 11 }}>Swagger UI</div>
                <a href={`${import.meta.env.VITE_API_URL?.replace('/api','') || 'http://localhost:8000'}/redoc`} target="_blank" rel="noreferrer"
                  style={{ color: '#10b981', fontSize: 13, fontWeight: 500 }}>
                  ReDoc ↗
                </a>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
