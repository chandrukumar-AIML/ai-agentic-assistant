// frontend/src/pages/BillingPage.tsx — Feature 8
import { useEffect } from 'react'
import { PageShell, Card, Btn, ResultBox, TwoCol, useApi, SectionHead, Badge, StatCard } from '../components/ui'
import { getBillingStatus, getUsageStats, upgradePlan } from '../lib/api'

const PLANS = [
  { id: 'free', name: 'FREE', price: '₹0', features: ['100 queries/day','Basic RAG','Chat only','Community support'], color: '#6b7280' },
  { id: 'pro',  name: 'PRO',  price: '₹2,499/mo', features: ['5,000 queries/day','All 19 features','Priority support','MLflow dashboard'], color: '#6366f1', popular: true },
  { id: 'enterprise', name: 'ENTERPRISE', price: 'Custom', features: ['Unlimited queries','Dedicated infra','Custom models','SLA + compliance'], color: '#8b5cf6' },
]

export default function BillingPage() {
  const statusApi  = useApi()
  const usageApi   = useApi()
  const upgradeApi = useApi()

  useEffect(() => {
    statusApi.call(() => getBillingStatus())
    usageApi.call(() => getUsageStats())
  }, [])

  return (
    <PageShell icon="💳" title="Billing & Subscription Plans" subtitle="Feature 8 — Stripe + Razorpay + FREE/PRO/ENTERPRISE tiers">
      {/* Usage Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 14, marginBottom: 24 }}>
        <StatCard label="Current Plan"    value={statusApi.data?.plan_tier?.toUpperCase() || 'ENTERPRISE'} icon="💎" />
        <StatCard label="Queries Today"   value={usageApi.data?.today || 0}  icon="🔌" />
        <StatCard label="Daily Limit"     value={usageApi.data?.limit || '∞'} icon="📊" />
        <StatCard label="Resets At"       value="Midnight UTC" icon="⏰" />
      </div>

      {/* Plans */}
      <SectionHead title="Subscription Plans" sub="Choose the right plan for your team" />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 24 }}>
        {PLANS.map(plan => (
          <div key={plan.id} style={{
            background: '#161b27',
            border: `1px solid ${plan.popular ? plan.color : '#1e2535'}`,
            borderRadius: 14, padding: 24,
            position: 'relative',
            boxShadow: plan.popular ? `0 0 20px rgba(99,102,241,0.2)` : 'none',
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
            </div>
            <div style={{ color: plan.color, fontSize: 24, fontWeight: 700, marginBottom: 16 }}>{plan.price}</div>
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
              onClick={() => upgradeApi.call(() => upgradePlan(plan.id))}
              loading={upgradeApi.loading}
              style={{ width: '100%', justifyContent: 'center' }}
            >
              {plan.id === 'enterprise' ? 'Contact Sales' : `Choose ${plan.name}`}
            </Btn>
          </div>
        ))}
      </div>

      {/* Payment providers */}
      <Card style={{ marginBottom: 20 }}>
        <SectionHead title="Payment Providers" sub="Stripe (global) + Razorpay (India)" />
        <div style={{ display: 'flex', gap: 20 }}>
          <div style={{ background: '#0f1117', borderRadius: 8, padding: '10px 20px', border: '1px solid #1e2535' }}>
            <div style={{ color: '#6366f1', fontWeight: 700 }}>Stripe</div>
            <div style={{ color: '#6b7280', fontSize: 11 }}>Global • USD/EUR/GBP</div>
          </div>
          <div style={{ background: '#0f1117', borderRadius: 8, padding: '10px 20px', border: '1px solid #1e2535' }}>
            <div style={{ color: '#22c55e', fontWeight: 700 }}>Razorpay</div>
            <div style={{ color: '#6b7280', fontSize: 11 }}>India • INR • UPI • NetBanking</div>
          </div>
        </div>
      </Card>

      <TwoCol>
        <ResultBox data={statusApi.data} loading={statusApi.loading} error={statusApi.error} title="Billing Status" />
        <ResultBox data={usageApi.data} loading={usageApi.loading} error={usageApi.error} title="Usage Stats" />
      </TwoCol>
    </PageShell>
  )
}
