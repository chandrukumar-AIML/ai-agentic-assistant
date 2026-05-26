// frontend/src/pages/HITLPage.tsx — Feature 6: Human-in-the-Loop
import { useEffect, useState } from 'react'
import { PageShell, Card, Btn, ResultBox, useApi, SectionHead, Badge, StatCard } from '../components/ui'
import { listApprovals, reviewApproval } from '../lib/api'

export default function HITLPage() {
  const [approvals, setApprovals] = useState<any[]>([])
  const [comment, setComment] = useState('')
  const listApi   = useApi()
  const reviewApi = useApi()

  const loadApprovals = () => listApi.call(() => listApprovals())

  useEffect(() => { loadApprovals() }, [])
  useEffect(() => {
    if (listApi.data?.approvals) setApprovals(listApi.data.approvals)
    else if (Array.isArray(listApi.data)) setApprovals(listApi.data)
  }, [listApi.data])

  const handleReview = async (id: string, action: 'approve' | 'reject') => {
    await reviewApi.call(() => reviewApproval(id, action, comment))
    loadApprovals()
  }

  const pending = approvals.filter(a => a.status === 'pending')
  const done    = approvals.filter(a => a.status !== 'pending')

  return (
    <PageShell icon="👁️" title="HITL Approval Dashboard" subtitle="Feature 6 — LangGraph interrupt, 30-min auto-reject, SendGrid+Slack notifications">
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 14, marginBottom: 20 }}>
        <StatCard label="Total"    value={approvals.length} icon="📋" />
        <StatCard label="Pending"  value={pending.length}   icon="⏳" />
        <StatCard label="Approved" value={approvals.filter(a => a.status === 'approved').length} icon="✅" />
        <StatCard label="Rejected" value={approvals.filter(a => a.status === 'rejected').length} icon="❌" />
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <SectionHead title={`Pending Approvals (${pending.length})`} sub="Actions requiring human review before execution" />
        <Btn variant="secondary" onClick={loadApprovals} loading={listApi.loading}>🔄 Refresh</Btn>
      </div>

      {pending.length === 0 && !listApi.loading && (
        <Card style={{ marginBottom: 20 }}>
          <div style={{ textAlign: 'center', padding: 30, color: '#6b7280' }}>
            <span style={{ fontSize: 36 }}>✅</span>
            <p style={{ marginTop: 8 }}>No pending approvals! All actions up to date.</p>
          </div>
        </Card>
      )}

      {pending.map((a: any) => (
        <Card key={a.id} style={{ marginBottom: 12, borderLeft: '3px solid #f59e0b' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
            <div>
              <div style={{ color: '#e2e8f0', fontSize: 14, fontWeight: 600 }}>{a.action_type || 'Approval Required'}</div>
              <div style={{ color: '#6b7280', fontSize: 11, marginTop: 2 }}>
                ID: {a.id?.slice(0, 8)}... • {a.requester_id || 'system'} • {new Date(a.created_at).toLocaleString()}
              </div>
            </div>
            <Badge text="PENDING" color="yellow" />
          </div>

          <div style={{ background: '#0f1117', borderRadius: 8, padding: 12, marginBottom: 10, fontSize: 12, color: '#9ca3af' }}>
            {typeof a.payload === 'object' ? JSON.stringify(a.payload, null, 2).slice(0, 300) : String(a.payload || 'No payload')}
          </div>

          <input value={comment} onChange={e => setComment(e.target.value)} placeholder="Add comment (optional)..."
            style={{ width: '100%', background: '#0f1117', border: '1px solid #1e2535', borderRadius: 6, padding: '8px 12px', color: '#e2e8f0', fontSize: 12, marginBottom: 8, boxSizing: 'border-box' as const }} />

          <div style={{ display: 'flex', gap: 8 }}>
            <Btn variant="success" onClick={() => handleReview(a.id, 'approve')} loading={reviewApi.loading}>✅ Approve</Btn>
            <Btn variant="danger" onClick={() => handleReview(a.id, 'reject')} loading={reviewApi.loading}>❌ Reject</Btn>
          </div>
        </Card>
      ))}

      {done.length > 0 && (
        <>
          <SectionHead title="History" sub="Completed approvals" />
          {done.slice(0, 5).map((a: any) => (
            <Card key={a.id} style={{ marginBottom: 8, opacity: 0.7 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div style={{ color: '#9ca3af', fontSize: 12 }}>{a.action_type || 'Action'} — {a.id?.slice(0, 8)}...</div>
                <Badge text={a.status?.toUpperCase()} color={a.status === 'approved' ? 'green' : 'red'} />
              </div>
            </Card>
          ))}
        </>
      )}

      <ResultBox data={listApi.data} loading={listApi.loading} error={listApi.error} title="Raw Approvals Data" />
    </PageShell>
  )
}
