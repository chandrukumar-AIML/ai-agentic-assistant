// frontend/src/pages/OutputPage.tsx — Feature 7: Multi-modal Output
import { useState } from 'react'
import { PageShell, Card, Btn, Input, ResultBox, Tabs, TwoCol, useApi, SectionHead } from '../components/ui'
import { generatePDF, generateExcel, generatePPTX } from '../lib/api'

export default function OutputPage() {
  const [tab, setTab]         = useState('pdf')
  const [title, setTitle]     = useState('Quarterly Business Report')
  const [content, setContent] = useState('This report covers Q3 2024 performance metrics, revenue analysis, and strategic initiatives for the next quarter.')
  const [excelSheet, setExcelSheet] = useState('Monthly Sales')
  const pdfApi   = useApi()
  const xlApi    = useApi()
  const pptxApi  = useApi()

  const sampleSections = [
    { heading: 'Executive Summary', body: 'Revenue grew 23% YoY to $2.5M. Customer base expanded to 1,200 active accounts.' },
    { heading: 'Key Metrics', body: 'CAC: $450 | LTV: $3,200 | Churn: 2.1% | NPS: 72' },
    { heading: 'Next Steps', body: '1. Launch enterprise tier Q4\n2. Expand to 3 new markets\n3. Hire 15 engineers' },
  ]

  const sampleSheets = [
    {
      name: excelSheet,
      headers: ['Month', 'Revenue', 'Customers', 'Growth %'],
      rows: [
        ['January 2024', 180000, 850, '12%'],
        ['February 2024', 195000, 920, '8.3%'],
        ['March 2024', 220000, 1050, '12.8%'],
        ['April 2024', 248000, 1200, '12.7%'],
      ]
    }
  ]

  const sampleSlides = [
    { title: 'Q3 2024 Review', content: 'AI Agentic Assistant — Business Performance' },
    { title: 'Revenue', content: '$2.5M Total Revenue\n+23% Year-over-Year' },
    { title: 'Product Highlights', content: '19 Features Live\n80+ API Endpoints\nEnterprise Ready' },
    { title: 'Next Quarter', content: 'Enterprise launch\n3 new markets\n15 new hires' },
  ]

  return (
    <PageShell icon="📄" title="Multi-modal Output Generator" subtitle="Feature 7 — PDF (ReportLab) / PPTX (python-pptx) / Excel (openpyxl) / DALL-E 3 Images">
      <Tabs
        tabs={[
          { id: 'pdf',   label: 'PDF Report', icon: '📄' },
          { id: 'excel', label: 'Excel',       icon: '📊' },
          { id: 'pptx',  label: 'PowerPoint', icon: '📽️' },
        ]}
        active={tab} onChange={setTab}
      />

      {tab === 'pdf' && (
        <TwoCol>
          <Card>
            <SectionHead title="PDF Report Generator" sub="ReportLab — professional reports with sections" />
            <Input label="Report Title" value={title} onChange={setTitle} />
            <Input label="Executive Summary" value={content} onChange={setContent} rows={4} />
            <div style={{ marginBottom: 14 }}>
              <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 6 }}>Sections included:</div>
              {sampleSections.map(s => (
                <div key={s.heading} style={{ background: '#0f1117', border: '1px solid #1e2535', borderRadius: 6, padding: '6px 10px', marginBottom: 4 }}>
                  <div style={{ color: '#a5b4fc', fontSize: 11, fontWeight: 600 }}>{s.heading}</div>
                  <div style={{ color: '#6b7280', fontSize: 10 }}>{s.body.slice(0, 60)}...</div>
                </div>
              ))}
            </div>
            <Btn onClick={() => pdfApi.call(() => generatePDF(title, content, sampleSections))} loading={pdfApi.loading}>
              📄 Generate PDF
            </Btn>
          </Card>
          <div>
            {pdfApi.data?.download_url && (
              <Card style={{ marginBottom: 12 }}>
                <div style={{ color: '#22c55e', fontSize: 14, fontWeight: 600, marginBottom: 8 }}>✅ PDF Generated!</div>
                <a href={`${(import.meta.env.VITE_API_URL?.replace('/api','') || 'http://localhost:8000')}${pdfApi.data.download_url}`} target="_blank" rel="noreferrer"
                  style={{ color: '#6366f1', fontSize: 13, display: 'block', marginBottom: 4 }}>
                  📥 Download PDF →
                </a>
                <div style={{ color: '#6b7280', fontSize: 11 }}>Size: {pdfApi.data.size_kb}KB • Pages: {pdfApi.data.pages}</div>
              </Card>
            )}
            <ResultBox data={pdfApi.data} loading={pdfApi.loading} error={pdfApi.error} title="PDF Generation Result" />
          </div>
        </TwoCol>
      )}

      {tab === 'excel' && (
        <TwoCol>
          <Card>
            <SectionHead title="Excel Report Generator" sub="openpyxl — multi-sheet with headers" />
            <Input label="Sheet Name" value={excelSheet} onChange={setExcelSheet} />
            <div style={{ marginBottom: 14 }}>
              <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 6 }}>Sample Data Preview:</div>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
                  <thead>
                    <tr style={{ background: '#1e2535' }}>
                      {sampleSheets[0].headers.map(h => <th key={h} style={{ padding: '6px 10px', color: '#a5b4fc', textAlign: 'left', border: '1px solid #374151' }}>{h}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {sampleSheets[0].rows.map((row, i) => (
                      <tr key={i} style={{ background: i % 2 === 0 ? '#0f1117' : '#161b27' }}>
                        {row.map((cell, j) => <td key={j} style={{ padding: '5px 10px', color: '#9ca3af', border: '1px solid #1e2535' }}>{String(cell)}</td>)}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <Btn onClick={() => xlApi.call(() => generateExcel(sampleSheets))} loading={xlApi.loading}>
              📊 Generate Excel
            </Btn>
          </Card>
          <div>
            {xlApi.data?.download_url && (
              <Card style={{ marginBottom: 12 }}>
                <div style={{ color: '#22c55e', fontSize: 14, fontWeight: 600, marginBottom: 8 }}>✅ Excel Generated!</div>
                <a href={`${(import.meta.env.VITE_API_URL?.replace('/api','') || 'http://localhost:8000')}${xlApi.data.download_url}`} target="_blank" rel="noreferrer"
                  style={{ color: '#6366f1', fontSize: 13 }}>📥 Download Excel →</a>
              </Card>
            )}
            <ResultBox data={xlApi.data} loading={xlApi.loading} error={xlApi.error} title="Excel Result" />
          </div>
        </TwoCol>
      )}

      {tab === 'pptx' && (
        <TwoCol>
          <Card>
            <SectionHead title="PowerPoint Generator" sub="python-pptx — professional slide decks" />
            <Input label="Presentation Title" value={title} onChange={setTitle} />
            <div style={{ marginBottom: 14 }}>
              {sampleSlides.map((s, i) => (
                <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'center', background: '#0f1117', borderRadius: 6, padding: '7px 10px', marginBottom: 4 }}>
                  <span style={{ color: '#6366f1', fontSize: 11, fontWeight: 700, minWidth: 20 }}>#{i+1}</span>
                  <div>
                    <div style={{ color: '#e2e8f0', fontSize: 11, fontWeight: 600 }}>{s.title}</div>
                    <div style={{ color: '#6b7280', fontSize: 10 }}>{s.content.slice(0, 50)}...</div>
                  </div>
                </div>
              ))}
            </div>
            <Btn onClick={() => pptxApi.call(() => generatePPTX(title, sampleSlides))} loading={pptxApi.loading}>
              📽️ Generate PPTX
            </Btn>
          </Card>
          <div>
            {pptxApi.data?.download_url && (
              <Card style={{ marginBottom: 12 }}>
                <div style={{ color: '#22c55e', fontSize: 14, fontWeight: 600, marginBottom: 8 }}>✅ PPTX Generated!</div>
                <a href={`${(import.meta.env.VITE_API_URL?.replace('/api','') || 'http://localhost:8000')}${pptxApi.data.download_url}`} target="_blank" rel="noreferrer"
                  style={{ color: '#6366f1', fontSize: 13 }}>📥 Download PPTX →</a>
                <div style={{ color: '#6b7280', fontSize: 11, marginTop: 4 }}>{pptxApi.data.slide_count} slides</div>
              </Card>
            )}
            <ResultBox data={pptxApi.data} loading={pptxApi.loading} error={pptxApi.error} title="PPTX Result" />
          </div>
        </TwoCol>
      )}
    </PageShell>
  )
}
