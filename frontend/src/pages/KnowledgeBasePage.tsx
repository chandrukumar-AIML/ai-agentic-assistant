// frontend/src/pages/KnowledgeBasePage.tsx — RAG document management
import { useState, useEffect, useRef } from 'react'
import { PageShell, Card, Btn, SectionHead, Badge } from '../components/ui'
import { apiFetch } from '../lib/api'

interface DocEntry {
  id: string
  filename: string
  source: string
  chunk_count: number
  ingested_at: string
  size_bytes?: number
}

interface RagStats {
  total_vectors: number
  total_documents: number
  index_size_bytes: number
  embedding_model: string
  chunk_size: number
  chunk_overlap: number
}

export default function KnowledgeBasePage() {
  const [stats,      setStats]      = useState<RagStats | null>(null)
  const [docs,       setDocs]       = useState<DocEntry[]>([])
  const [url,        setUrl]        = useState('')
  const [status,     setStatus]     = useState<'idle'|'uploading'|'success'|'error'>('idle')
  const [message,    setMessage]    = useState('')
  const [tab,        setTab]        = useState<'docs'|'upload'>('docs')
  const fileRef = useRef<HTMLInputElement>(null)

  useEffect(() => { loadAll() }, [])

  async function loadAll() {
    try {
      const [s, d] = await Promise.all([
        apiFetch('/rag/stats'),
        apiFetch('/rag/documents').catch(() => ({ documents: [] })),
      ])
      setStats(s)
      setDocs(d.documents || [])
    } catch {}
  }

  async function uploadFile(file: File) {
    setStatus('uploading'); setMessage(`Uploading ${file.name}…`)
    const form = new FormData()
    form.append('file', file)
    try {
      const token = sessionStorage.getItem('aaa_token') || ''
      const res = await fetch(
        `${(import.meta.env.VITE_API_URL || 'http://localhost:8000/api')}/ingest`,
        { method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: form },
      )
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Upload failed')
      setStatus('success'); setMessage(`✓ ${data.chunks_added} chunks ingested from ${file.name}`)
      loadAll()
    } catch (e: any) {
      setStatus('error'); setMessage(`✗ ${e.message}`)
    }
  }

  async function ingestUrl() {
    if (!url.trim()) return
    setStatus('uploading'); setMessage(`Fetching ${url}…`)
    try {
      const data = await apiFetch('/ingest/url', { method: 'POST', body: JSON.stringify({ url }) })
      setStatus('success'); setMessage(`✓ ${data.chunks_added} chunks ingested from URL`)
      setUrl(''); loadAll()
    } catch (e: any) {
      setStatus('error'); setMessage(`✗ ${e.message}`)
    }
  }

  function fmt(bytes: number) {
    if (bytes > 1_000_000) return `${(bytes / 1_000_000).toFixed(1)} MB`
    if (bytes > 1_000)     return `${(bytes / 1_000).toFixed(1)} KB`
    return `${bytes} B`
  }

  const TAB_STYLE = (active: boolean): React.CSSProperties => ({
    padding: '7px 16px', borderRadius: 6, border: 'none', cursor: 'pointer', fontSize: 13,
    background: active ? 'rgba(16,185,129,0.2)' : 'none',
    color: active ? '#5eead4' : '#6b7280',
  })

  return (
    <PageShell icon="🧠" title="Knowledge Base" subtitle="Upload, manage and search your documents">

      {/* Stats bar */}
      {stats && (
        <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
          {[
            { label: 'Total Vectors',    value: stats.total_vectors.toLocaleString(), color: '#10b981' },
            { label: 'Documents',        value: stats.total_documents.toString(),      color: '#22c55e' },
            { label: 'Index Size',       value: fmt(stats.index_size_bytes),           color: '#f59e0b' },
            { label: 'Embedding Model',  value: stats.embedding_model,                 color: '#06b6d4' },
            { label: 'Chunk Size',       value: `${stats.chunk_size} tokens`,          color: '#06b6d4' },
          ].map(s => (
            <div key={s.label} style={{
              background: '#161b27', border: '1px solid #1e2535', borderRadius: 10,
              padding: '10px 16px', minWidth: 120,
            }}>
              <div style={{ color: '#6b7280', fontSize: 10, fontWeight: 600, marginBottom: 2 }}>{s.label.toUpperCase()}</div>
              <div style={{ color: s.color, fontSize: 15, fontWeight: 700 }}>{s.value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 16 }}>
        <button style={TAB_STYLE(tab === 'docs')}   onClick={() => setTab('docs')}>📑 Documents ({docs.length})</button>
        <button style={TAB_STYLE(tab === 'upload')} onClick={() => setTab('upload')}>⬆️ Upload New</button>
      </div>

      {/* Documents tab */}
      {tab === 'docs' && (
        <Card>
          <SectionHead title="Your Documents" sub="All documents available to search" />
          {docs.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 0', color: '#6b7280' }}>
              <div style={{ fontSize: 32, marginBottom: 12 }}>📂</div>
              <div>No documents ingested yet.</div>
              <div style={{ fontSize: 12, marginTop: 6 }}>Upload files or paste a URL to get started.</div>
              <Btn variant="primary" style={{ marginTop: 16 }} onClick={() => setTab('upload')}>Upload First Document →</Btn>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {docs.map(doc => (
                <div key={doc.id} style={{
                  display: 'flex', alignItems: 'center', gap: 12,
                  background: '#0f1117', borderRadius: 8, padding: '10px 14px',
                  border: '1px solid #1e2535',
                }}>
                  <span style={{ fontSize: 20 }}>
                    {doc.filename?.endsWith('.pdf') ? '📄' : doc.source?.startsWith('http') ? '🌐' : '📝'}
                  </span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {doc.filename || doc.source}
                    </div>
                    <div style={{ color: '#6b7280', fontSize: 11, marginTop: 2 }}>
                      {doc.chunk_count} chunks · {doc.ingested_at ? new Date(doc.ingested_at).toLocaleDateString() : '—'}
                      {doc.size_bytes ? ` · ${fmt(doc.size_bytes)}` : ''}
                    </div>
                  </div>
                  <Badge text={`${doc.chunk_count} chunks`} color="green" />
                </div>
              ))}
            </div>
          )}
          {docs.length > 0 && (
            <div style={{ marginTop: 16, display: 'flex', gap: 8 }}>
              <Btn variant="secondary" onClick={loadAll}>↻ Refresh</Btn>
              <Btn variant="primary" onClick={() => setTab('upload')}>+ Upload More</Btn>
            </div>
          )}
        </Card>
      )}

      {/* Upload tab */}
      {tab === 'upload' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

          {/* File upload */}
          <Card>
            <SectionHead title="Upload Document" sub="PDF, TXT, MD, DOCX, CSV — max 20MB" />
            <div
              onClick={() => fileRef.current?.click()}
              onDragOver={e => e.preventDefault()}
              onDrop={e => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) uploadFile(f) }}
              style={{
                border: '2px dashed #1e2535', borderRadius: 12, padding: '40px 20px',
                textAlign: 'center', cursor: 'pointer', transition: 'border-color 0.2s',
              }}
              onMouseEnter={e => (e.currentTarget.style.borderColor = '#10b981')}
              onMouseLeave={e => (e.currentTarget.style.borderColor = '#1e2535')}
            >
              <div style={{ fontSize: 36, marginBottom: 12 }}>📤</div>
              <div style={{ color: '#e2e8f0', fontSize: 14, fontWeight: 500 }}>Click or drag & drop a file</div>
              <div style={{ color: '#6b7280', fontSize: 12, marginTop: 6 }}>Supports PDF, TXT, DOCX, MD, CSV</div>
            </div>
            <input ref={fileRef} type="file" accept=".pdf,.txt,.md,.docx,.csv" style={{ display: 'none' }}
              onChange={e => { const f = e.target.files?.[0]; if (f) uploadFile(f) }} />
          </Card>

          {/* URL ingestion */}
          <Card>
            <SectionHead title="Add from URL" sub="Add any webpage or article to your knowledge base" />
            <div style={{ display: 'flex', gap: 8 }}>
              <input
                value={url} onChange={e => setUrl(e.target.value)}
                placeholder="https://example.com/article"
                onKeyDown={e => e.key === 'Enter' && ingestUrl()}
                style={{
                  flex: 1, padding: '10px 12px', background: '#0f1117',
                  border: '1px solid #1e2535', borderRadius: 8, color: '#e2e8f0',
                  fontSize: 13, outline: 'none',
                }}
              />
              <Btn variant="primary" onClick={ingestUrl} disabled={status === 'uploading' || !url.trim()}>
                {status === 'uploading' ? '…' : 'Upload'}
              </Btn>
            </div>
          </Card>

          {/* Status */}
          {message && (
            <div style={{
              padding: '12px 16px', borderRadius: 8,
              background: status === 'success' ? '#0a1f0a' : status === 'error' ? '#1f0a0a' : '#0f1117',
              border: `1px solid ${status === 'success' ? '#22c55e' : status === 'error' ? '#dc2626' : '#1e2535'}`,
              color: status === 'success' ? '#4ade80' : status === 'error' ? '#f87171' : '#9ca3af',
              fontSize: 13,
            }}>
              {status === 'uploading' && '⏳ '}{message}
            </div>
          )}
        </div>
      )}
    </PageShell>
  )
}
