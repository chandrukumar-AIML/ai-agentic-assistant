// frontend/src/pages/FormReaderPage.tsx — Feature 14
import { useState } from 'react'
import { PageShell, Card, Btn, Select, ResultBox, TwoCol, useApi, SectionHead, Badge } from '../components/ui'
import { extractForm } from '../lib/api'

const DOC_TYPES = [
  { label: 'Auto-detect', value: 'auto' }, { label: 'PAN Card', value: 'pan' },
  { label: 'Aadhaar Card', value: 'aadhaar' }, { label: 'GSTIN', value: 'gstin' },
  { label: 'Passport', value: 'passport' }, { label: 'Bank Statement', value: 'bank_statement' },
  { label: 'ITR Form', value: 'itr' },
]

export default function FormReaderPage() {
  const [docType, setDocType] = useState('auto')
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [preview, setPreview] = useState('')
  const api = useApi()

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setImageFile(file)
    const reader = new FileReader()
    reader.onload = ev => {
      const b64 = (ev.target?.result as string).split(',')[1]
      setPreview(ev.target?.result as string)
    }
    reader.readAsDataURL(file)
  }

  const handleExtract = async () => {
    if (!imageFile) return
    const reader = new FileReader()
    reader.onload = async (ev) => {
      const b64 = (ev.target?.result as string).split(',')[1]
      await api.call(() => extractForm(b64, docType))
    }
    reader.readAsDataURL(imageFile)
  }

  return (
    <PageShell icon="📋" title="AI Form Reader & Data Extractor" subtitle="Feature 14 — GPT-4o Vision • PAN/Aadhaar/GSTIN validation • Verhoeff check">
      <TwoCol>
        <div>
          <Card style={{ marginBottom: 16 }}>
            <SectionHead title="Upload Document" sub="PAN, Aadhaar, GSTIN, Passport, Bank Statement" />
            <Select label="Document Type" value={docType} onChange={setDocType} options={DOC_TYPES} />

            <div style={{
              border: '2px dashed #374151', borderRadius: 10, padding: 24, textAlign: 'center',
              cursor: 'pointer', marginBottom: 14, transition: 'border-color 0.15s',
            }} onClick={() => document.getElementById('formFile')?.click()}>
              {preview ? (
                <img src={preview} alt="Preview" style={{ maxHeight: 200, maxWidth: '100%', borderRadius: 8 }} />
              ) : (
                <>
                  <div style={{ fontSize: 36 }}>📄</div>
                  <div style={{ color: '#6b7280', fontSize: 13, marginTop: 8 }}>Click to upload document image</div>
                  <div style={{ color: '#4b5563', fontSize: 11, marginTop: 4 }}>PNG, JPG, PDF — max 20MB</div>
                </>
              )}
            </div>
            <input id="formFile" type="file" accept="image/*" onChange={handleFile} style={{ display: 'none' }} />
            {imageFile && <div style={{ color: '#6b7280', fontSize: 11, marginBottom: 10 }}>📎 {imageFile.name}</div>}

            <Btn onClick={handleExtract} loading={api.loading} disabled={!imageFile}>
              📋 Extract Data
            </Btn>
          </Card>

          <Card>
            <SectionHead title="India Document Validation" />
            {[
              { name: 'PAN Card', checks: ['Entity type from char 4', 'Format: XXXXX1234X'] },
              { name: 'Aadhaar', checks: ['Verhoeff check digit', '12-digit format'] },
              { name: 'GSTIN', checks: ['38-state prefix table', 'PAN cross-validation', '15-char format'] },
            ].map(doc => (
              <div key={doc.name} style={{ marginBottom: 10 }}>
                <div style={{ color: '#a5b4fc', fontSize: 12, fontWeight: 600, marginBottom: 3 }}>{doc.name}</div>
                {doc.checks.map(c => <div key={c} style={{ color: '#6b7280', fontSize: 11, marginBottom: 1 }}>✓ {c}</div>)}
              </div>
            ))}
          </Card>
        </div>

        <div>
          {api.data && !api.loading && (
            <Card style={{ marginBottom: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                <SectionHead title="Extracted Fields" />
                {api.data.doc_type && <Badge text={api.data.doc_type.toUpperCase()} color="blue" />}
              </div>
              {api.data.fields && Object.entries(api.data.fields).map(([key, val]: [string, any]) => (
                <div key={key} style={{ display: 'flex', gap: 10, padding: '7px 0', borderBottom: '1px solid #1e2535', alignItems: 'flex-start' }}>
                  <div style={{ color: '#6b7280', fontSize: 11, minWidth: 140, textTransform: 'capitalize' }}>
                    {key.replace(/_/g, ' ')}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ color: '#e2e8f0', fontSize: 12, fontWeight: 500 }}>{val?.value || val?.text || String(val)}</div>
                    {val?.confidence && (
                      <div style={{ marginTop: 2 }}>
                        <div style={{ height: 3, background: '#1e2535', borderRadius: 2 }}>
                          <div style={{ height: '100%', background: val.confidence > 0.8 ? '#22c55e' : '#f59e0b', borderRadius: 2, width: `${val.confidence * 100}%` }} />
                        </div>
                        <div style={{ color: '#6b7280', fontSize: 10, marginTop: 2 }}>{Math.round(val.confidence * 100)}% confidence</div>
                      </div>
                    )}
                  </div>
                  {api.data.validation?.[key] !== undefined && (
                    <Badge text={api.data.validation[key] ? '✓ Valid' : '✗ Invalid'} color={api.data.validation[key] ? 'green' : 'red'} />
                  )}
                </div>
              ))}
            </Card>
          )}
          <ResultBox data={api.data} loading={api.loading} error={api.error} title="Extraction Result" />
        </div>
      </TwoCol>
    </PageShell>
  )
}
