// frontend/src/pages/EmailPage.tsx — Feature 15
import { useEffect, useState } from 'react'
import { PageShell, Card, Btn, Input, Select, ResultBox, Tabs, TwoCol, useApi, SectionHead, Badge } from '../components/ui'
import { listEmails, draftEmail } from '../lib/api'

export default function EmailPage() {
  const [tab, setTab]       = useState('inbox')
  const [provider, setProvider] = useState('gmail')
  const [to, setTo]         = useState('client@example.com')
  const [subject, setSubject] = useState('Follow-up: AI Platform Demo')
  const [context, setContext] = useState('Follow up on last week\'s product demo. Mention the 30-day trial offer and pricing.')
  const inboxApi = useApi()
  const draftApi = useApi()

  useEffect(() => {
    if (tab === 'inbox') inboxApi.call(() => listEmails(provider))
  }, [tab, provider])

  return (
    <PageShell icon="📧" title="AI Email Manager" subtitle="Draft, summarise & manage your Gmail and Outlook inbox">
      <Tabs
        tabs={[
          { id: 'inbox', label: 'Inbox',        icon: '📥' },
          { id: 'draft', label: 'AI Draft',     icon: '✍️' },
          { id: 'oauth', label: 'OAuth Setup',  icon: '🔑' },
        ]}
        active={tab} onChange={setTab}
      />

      {tab === 'inbox' && (
        <div>
          <div style={{ display: 'flex', gap: 10, marginBottom: 16 }}>
            <Select label="" value={provider} onChange={setProvider}
              options={[{ label: '📧 Gmail', value: 'gmail' }, { label: '📫 Outlook', value: 'outlook' }]} />
            <div style={{ paddingTop: 0 }}>
              <Btn onClick={() => inboxApi.call(() => listEmails(provider))} loading={inboxApi.loading}>🔄 Refresh</Btn>
            </div>
          </div>
          {inboxApi.data?.emails?.map((email: any, i: number) => (
            <Card key={i} style={{ marginBottom: 8 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <div style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 600 }}>{email.subject || 'No Subject'}</div>
                <div style={{ color: '#6b7280', fontSize: 11 }}>{email.date}</div>
              </div>
              <div style={{ color: '#9ca3af', fontSize: 12 }}>From: {email.from}</div>
              <div style={{ color: '#6b7280', fontSize: 11, marginTop: 4 }}>{email.snippet || email.body?.slice(0, 100)}...</div>
            </Card>
          )) || (
            inboxApi.loading ? null : (
              <Card>
                <div style={{ textAlign: 'center', padding: 40, color: '#6b7280' }}>
                  <span style={{ fontSize: 36 }}>📧</span>
                  <p style={{ marginTop: 8 }}>Connect your Gmail or Outlook to see inbox.</p>
                  <p style={{ fontSize: 11, marginTop: 4 }}>Configure OAuth credentials in .env file.</p>
                </div>
              </Card>
            )
          )}
          <ResultBox data={inboxApi.data} loading={inboxApi.loading} error={inboxApi.error} title="Inbox Data" />
        </div>
      )}

      {tab === 'draft' && (
        <TwoCol>
          <Card>
            <SectionHead title="AI Email Drafter" sub="LLM-composed emails — HITL approval required before send" />
            <Select label="Provider" value={provider} onChange={setProvider}
              options={[{ label: 'Gmail', value: 'gmail' }, { label: 'Outlook', value: 'outlook' }]} />
            <Input label="To" value={to} onChange={setTo} />
            <Input label="Subject" value={subject} onChange={setSubject} />
            <Input label="Context / Instructions" value={context} onChange={setContext} rows={4} />
            <div style={{ marginBottom: 12 }}>
              {['Follow up on demo','Send proposal','Thank you email','Meeting request'].map(c => (
                <button key={c} onClick={() => setContext(c)} style={{
                  marginRight: 6, marginBottom: 4, padding: '3px 9px', borderRadius: 20,
                  background: '#1e2535', border: '1px solid #374151', color: '#9ca3af', fontSize: 11, cursor: 'pointer',
                }}>{c}</button>
              ))}
            </div>
            <Btn onClick={() => draftApi.call(() => draftEmail(to, subject, context))} loading={draftApi.loading}>
              ✍️ Draft Email
            </Btn>
            <div style={{ marginTop: 8, padding: '8px 10px', background: 'rgba(234,179,8,0.1)', borderRadius: 6, fontSize: 11, color: '#fde047' }}>
              ⚠️ All sends require HITL approval — email will not send without human review
            </div>
          </Card>

          <div>
            {draftApi.data?.draft && (
              <Card style={{ marginBottom: 12 }}>
                <SectionHead title="Drafted Email" />
                <div style={{ background: '#0f1117', borderRadius: 8, padding: 14, marginBottom: 10 }}>
                  <div style={{ color: '#6b7280', fontSize: 11, marginBottom: 8 }}>
                    To: <span style={{ color: '#e2e8f0' }}>{to}</span> | Subject: <span style={{ color: '#e2e8f0' }}>{subject}</span>
                  </div>
                  <div style={{ color: '#e2e8f0', fontSize: 13, lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>{draftApi.data.draft}</div>
                </div>
                {draftApi.data.approval_id && (
                  <div style={{ padding: '8px 10px', background: 'rgba(234,179,8,0.1)', borderRadius: 6, fontSize: 11, color: '#fde047' }}>
                    📋 Pending HITL approval: {draftApi.data.approval_id?.slice(0,8)}...
                  </div>
                )}
              </Card>
            )}
            <ResultBox data={draftApi.data} loading={draftApi.loading} error={draftApi.error} title="Draft Response" />
          </div>
        </TwoCol>
      )}

      {tab === 'oauth' && (
        <TwoCol>
          <Card>
            <SectionHead title="Gmail OAuth 2.0 Setup" />
            <div style={{ marginBottom: 16 }}>
              {[
                '1. Go to Google Cloud Console',
                '2. Create OAuth 2.0 credentials',
                `3. Add redirect URI: ${(import.meta.env.VITE_API_URL || 'http://localhost:8000/api').replace('/api','')}/api/email/oauth/gmail/callback`,
                '4. Add GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET to .env',
                '5. Click "Connect Gmail" to authorize',
              ].map(s => <div key={s} style={{ color: '#9ca3af', fontSize: 12, marginBottom: 6 }}>{s}</div>)}
            </div>
            <a href={`${(import.meta.env.VITE_API_URL || 'http://localhost:8000/api').replace('/api','')}/api/verticals/email/oauth/gmail`} target="_blank" rel="noreferrer">
              <Btn variant="primary">Connect Gmail →</Btn>
            </a>
          </Card>
          <Card>
            <SectionHead title="Outlook OAuth Setup" />
            <div style={{ marginBottom: 16 }}>
              {[
                '1. Register app in Azure Portal',
                '2. Add OUTLOOK_CLIENT_ID and OUTLOOK_CLIENT_SECRET to .env',
                '3. Set redirect URI in Azure app registration',
                '4. Click "Connect Outlook" to authorize',
              ].map(s => <div key={s} style={{ color: '#9ca3af', fontSize: 12, marginBottom: 6 }}>{s}</div>)}
            </div>
            <a href={`${(import.meta.env.VITE_API_URL || 'http://localhost:8000/api').replace('/api','')}/api/verticals/email/oauth/outlook`} target="_blank" rel="noreferrer">
              <Btn variant="secondary">Connect Outlook →</Btn>
            </a>
          </Card>
        </TwoCol>
      )}
    </PageShell>
  )
}
