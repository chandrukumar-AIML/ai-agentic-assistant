// frontend/src/pages/BillingPage.tsx — Feature 8: Billing & Subscriptions
import { useEffect, useState } from 'react'
import { PageShell, Card, Btn, ResultBox, TwoCol, useApi, SectionHead, StatCard } from '../components/ui'
import { getBillingStatus, getUsageStats, upgradePlan, upgradePlanRazorpay } from '../lib/api'

const PLANS = [
  { id: 'free', name: 'FREE', price: '₹0', sub: 'forever', features: ['50 queries/day','Core verticals','Chat + RAG','Community support'], color: '#6b7280' },
  { id: 'pro',  name: 'PRO',  price: '₹2,499', sub: '/month', features: ['500 queries/day','All 27 features','Priority support','Image + audio gen','MLflow dashboard'], color: '#10b981', popular: true },
  { id: 'enterprise', name: 'ENTERPRISE', price: 'Custom', sub: 'contact us', features: ['Unlimited queries','Dedicated infra','Custom models','SLA + compliance','Dedicated CSM'], color: '#06b6d4' },
]

export default function BillingPage() {
  const statusApi  = useApi()
  const usageApi   = useApi()
  const [provider, setProvider] = useState<'razorpay' | 'stripe'>('razorpay')
  const [busy, setBusy]   = useState('')
  const [msg, setMsg]     = useState('')
  const [err, setErr]     = useState('')

  useEffect(() => {
    statusApi.call(() => getBillingStatus())
    usageApi.call(() => getUsageStats())
  }, [])  // eslint-disable-line react-hooks/exhaustive-deps

  const choose = async (planId: string) => {
    setMsg(''); setErr('')
    if (planId === 'free') { setMsg('You are on the Free plan by default.'); return }
    if (planId === 'enterprise') { setMsg('Enterprise is custom-priced — contact sales@agentic.local to set up your plan.'); return }
    setBusy(planId)
    try {
      if (provider === 'razorpay') {
        const res = await upgradePlanRazorpay(planId)
        const url = res?.short_url || res?.payment_url
        if (url) { window.location.href = url; return }
        setMsg('Razorpay subscription created. Check your email/SMS for the payment link.')
      } else {
        const res = await upgradePlan(planId)
        const url = res?.checkout_url
        if (url) { window.location.href = url; return }
        setMsg('Stripe checkout session created.')
      }
    } catch (e: any) {
      const m = String(e?.message || '')
      if (/not configured/i.test(m)) {
        setErr(`${provider === 'razorpay' ? 'Razorpay' : 'Stripe'} is not configured on this server yet. Add the API keys in the backend environment to enable live checkout.`)
      } else {
        setErr(m || 'Checkout failed')
      }
    } finally { setBusy('') }
  }

  const sub   = statusApi.data || {}
  const usage = (usageApi.data?.usage || {}) as Record<string, number>
  const limits = (usageApi.data?.limits || sub.limits || {}) as Record<string, number>
  const apiCalls = usage.api_calls ?? 0
  const apiLimit = limits.api_calls ?? 0

  return (
    <PageShell icon="💳" title="Billing & Subscription Plans" subtitle="Feature 8 — Stripe (global) + Razorpay (India · UPI/NetBanking) · FREE / PRO / ENTERPRISE">
      {/* Usage Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 14, marginBottom: 24 }}>
        <StatCard label="Current Plan"  value={(sub.plan_tier || 'free').toUpperCase()} icon="💎" />
        <StatCard label="API Calls (mo)" value={apiCalls} icon="🔌" />
        <StatCard label="Monthly Limit" value={apiLimit > 0 ? apiLimit.toLocaleString() : '∞'} icon="📊" />
        <StatCard label="Status"        value={(sub.status || 'active').toUpperCase()} icon="✅" />
      </div>

      {/* Payment provider selector */}
      <Card style={{ marginBottom: 20 }}>
        <SectionHead title="Payment Method" sub="India customers: Razorpay supports UPI, NetBanking & cards in INR" />
        <div style={{ display: 'flex', gap: 12 }}>
          {([
            { id: 'razorpay', title: 'Razorpay', desc: 'India • INR • UPI • NetBanking', accent: '#22c55e' },
            { id: 'stripe',   title: 'Stripe',   desc: 'Global • USD / EUR / GBP',       accent: '#10b981' },
          ] as const).map(p => (
            <button key={p.id} onClick={() => setProvider(p.id)} style={{
              flex: 1, textAlign: 'left', padding: '12px 16px', borderRadius: 10, cursor: 'pointer',
              background: provider === p.id ? 'rgba(16,185,129,0.1)' : '#0f1117',
              border: `1px solid ${provider === p.id ? p.accent : '#1e2535'}`,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ width: 10, height: 10, borderRadius: '50%', background: p.accent, display: 'inline-block' }} />
                <span style={{ color: p.accent, fontWeight: 700, fontSize: 14 }}>{p.title}</span>
                {provider === p.id && <span style={{ marginLeft: 'auto', fontSize: 10, color: '#5eead4' }}>SELECTED</span>}
              </div>
              <div style={{ color: '#6b7280', fontSize: 11, marginTop: 4 }}>{p.desc}</div>
            </button>
          ))}
        </div>
      </Card>

      {/* Status messages */}
      {msg && <div style={{ padding: '10px 14px', marginBottom: 16, background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)', borderRadius: 8, color: '#5eead4', fontSize: 13 }}>{msg}</div>}
      {err && <div style={{ padding: '10px 14px', marginBottom: 16, background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 8, color: '#fca5a5', fontSize: 13 }}>⚠ {err}</div>}

      {/* Plans */}
      <SectionHead title="Subscription Plans" sub="Choose the right plan for your team" />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 24 }}>
        {PLANS.map(plan => {
          const isCurrent = (sub.plan_tier || 'free') === plan.id
          return (
            <div key={plan.id} style={{
              background: '#161b27',
              border: `1px solid ${plan.popular ? plan.color : '#1e2535'}`,
              borderRadius: 14, padding: 24, position: 'relative',
              boxShadow: plan.popular ? `0 0 20px rgba(16,185,129,0.2)` : 'none',
            }}>
              {plan.popular && (
                <div style={{
                  position: 'absolute', top: -10, left: '50%', transform: 'translateX(-50%)',
                  background: plan.color, color: '#fff', fontSize: 10, fontWeight: 700,
                  padding: '2px 12px', borderRadius: 20,
                }}>MOST POPULAR</div>
              )}
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <div style={{ width: 10, height: 10, borderRadius: '50%', background: plan.color }} />
                <span style={{ color: '#e2e8f0', fontSize: 16, fontWeight: 700 }}>{plan.name}</span>
                {isCurrent && <span style={{ marginLeft: 'auto', fontSize: 10, color: '#86efac', border: '1px solid rgba(34,197,94,0.3)', borderRadius: 4, padding: '1px 6px' }}>CURRENT</span>}
              </div>
              <div style={{ marginBottom: 16 }}>
                <span style={{ color: plan.color, fontSize: 24, fontWeight: 700 }}>{plan.price}</span>
                <span style={{ color: '#6b7280', fontSize: 12, marginLeft: 6 }}>{plan.sub}</span>
              </div>
              <div style={{ marginBottom: 20 }}>
                {plan.features.map(f => (
                  <div key={f} style={{ display: 'flex', gap: 6, marginBottom: 6, fontSize: 12 }}>
                    <span style={{ color: plan.color }}>✓</span>
                    <span style={{ color: '#9ca3af' }}>{f}</span>
                  </div>
                ))}
              </div>
              <Btn
                variant={plan.popular ? 'primary' : 'secondary'}
                onClick={() => choose(plan.id)}
                loading={busy === plan.id}
                disabled={isCurrent}
                style={{ width: '100%', justifyContent: 'center' }}
              >
                {isCurrent ? 'Current Plan' : plan.id === 'enterprise' ? 'Contact Sales' : plan.id === 'free' ? 'Free Forever' : `Upgrade to ${plan.name}`}
              </Btn>
            </div>
          )
        })}
      </div>

      <TwoCol>
        <ResultBox data={statusApi.data} loading={statusApi.loading} error={statusApi.error} title="Billing Status" />
        <ResultBox data={usageApi.data} loading={usageApi.loading} error={usageApi.error} title="Usage Stats" />
      </TwoCol>
    </PageShell>
  )
}
