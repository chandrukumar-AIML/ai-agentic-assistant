// frontend/src/pages/AccountantPage.tsx — Feature 17
import { useState } from 'react'
import { PageShell, Card, Btn, Input, Select, ResultBox, Tabs, TwoCol, useApi, SectionHead } from '../components/ui'
import { calcGST, calcTDS, accountantQuery } from '../lib/api'

export default function AccountantPage() {
  const [tab, setTab]           = useState('gst')
  const [amount, setAmount]     = useState('100000')
  const [gstRate, setGstRate]   = useState('18')
  const [interstate, setInterstate] = useState('false')
  const [payType, setPayType]   = useState('194J')
  const [tdsAmount, setTdsAmount] = useState('50000')
  const [panAvail, setPanAvail] = useState('true')
  const [query, setQuery]       = useState('How to file GSTR-3B?')

  const gstApi  = useApi()
  const tdsApi  = useApi()
  const qApi    = useApi()

  return (
    <PageShell icon="🧮" title="AI Accountant Assistant" subtitle="Feature 17 — GST/TDS calc, GSTR-1/3B export, India-specific tax rules">
      <Tabs
        tabs={[
          { id: 'gst',   label: 'GST Calculator', icon: '💰' },
          { id: 'tds',   label: 'TDS Calculator',  icon: '📋' },
          { id: 'query', label: 'Tax Query',        icon: '🤖' },
        ]}
        active={tab} onChange={setTab}
      />

      {tab === 'gst' && (
        <TwoCol>
          <Card>
            <SectionHead title="GST Calculation" sub="CGST+SGST (intra-state) or IGST (inter-state)" />
            <Input label="Invoice Amount (₹)" value={amount} onChange={setAmount} type="number" />
            <Select label="GST Rate" value={gstRate} onChange={setGstRate}
              options={[{ label: '0%', value: '0' }, { label: '5%', value: '5' }, { label: '12%', value: '12' }, { label: '18%', value: '18' }, { label: '28%', value: '28' }]} />
            <Select label="Transaction Type" value={interstate} onChange={setInterstate}
              options={[{ label: 'Intra-State (CGST + SGST)', value: 'false' }, { label: 'Inter-State (IGST)', value: 'true' }]} />
            <div style={{ marginBottom: 14 }}>
              {[['50000','5'],['200000','12'],['100000','18'],['75000','28']].map(([a, r]) => (
                <button key={a+r} onClick={() => { setAmount(a); setGstRate(r) }} style={{
                  marginRight: 6, marginBottom: 6, padding: '3px 9px', borderRadius: 20,
                  background: '#1e2535', border: '1px solid #374151', color: '#9ca3af', fontSize: 11, cursor: 'pointer',
                }}>₹{Number(a).toLocaleString()} @ {r}%</button>
              ))}
            </div>
            <Btn onClick={() => gstApi.call(() => calcGST(Number(amount), Number(gstRate), interstate === 'true'))} loading={gstApi.loading}>
              💰 Calculate GST
            </Btn>
          </Card>
          <div>
            {gstApi.data && (
              <Card style={{ marginBottom: 12 }}>
                <SectionHead title="GST Breakdown" />
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                  {[
                    { label: 'Base Amount', value: `₹${(gstApi.data.taxable_value ?? gstApi.data.base_amount)?.toLocaleString()}`, color: '#e2e8f0' },
                    { label: 'Total GST',   value: `₹${(gstApi.data.total_tax ?? gstApi.data.total_gst)?.toLocaleString()}`,   color: '#f59e0b' },
                    { label: gstApi.data.cgst ? 'CGST' : 'IGST', value: `₹${(gstApi.data.cgst || gstApi.data.igst)?.toLocaleString()}`, color: '#a5b4fc' },
                    { label: gstApi.data.sgst ? 'SGST' : 'IGST Rate', value: gstApi.data.sgst ? `₹${gstApi.data.sgst?.toLocaleString()}` : `${gstRate}%`, color: '#86efac' },
                    { label: 'Invoice Total', value: `₹${(gstApi.data.invoice_total ?? gstApi.data.total_with_gst)?.toLocaleString()}`, color: '#22c55e' },
                  ].map(s => (
                    <div key={s.label} style={{ background: '#0f1117', borderRadius: 8, padding: 12 }}>
                      <div style={{ color: s.color, fontSize: 16, fontWeight: 700 }}>{s.value}</div>
                      <div style={{ color: '#6b7280', fontSize: 11 }}>{s.label}</div>
                    </div>
                  ))}
                </div>
              </Card>
            )}
            <ResultBox data={gstApi.data} loading={gstApi.loading} error={gstApi.error} title="Full GST Data" />
          </div>
        </TwoCol>
      )}

      {tab === 'tds' && (
        <TwoCol>
          <Card>
            <SectionHead title="TDS Deduction Calculator" sub="Section 194C/J/I/H/A/192 as per IT Act" />
            <Select label="Payment Type (TDS Section)" value={payType} onChange={setPayType}
              options={[
                { label: '194C — Contractor/Subcontractor (1%/2%)', value: '194C' },
                { label: '194J — Professional/Technical Fees (10%)', value: '194J' },
                { label: '194I — Rent — Land/Building (10%)', value: '194I' },
                { label: '194H — Commission/Brokerage (5%)', value: '194H' },
                { label: '194A — Interest (10%)', value: '194A' },
                { label: '192 — Salary (slab rates)', value: '192' },
              ]} />
            <Input label="Payment Amount (₹)" value={tdsAmount} onChange={setTdsAmount} type="number" />
            <Select label="PAN Available?" value={panAvail} onChange={setPanAvail}
              options={[{ label: 'Yes — PAN available', value: 'true' }, { label: 'No — Higher TDS (20%)', value: 'false' }]} />
            <Btn onClick={() => tdsApi.call(() => calcTDS(payType, Number(tdsAmount), panAvail === 'true'))} loading={tdsApi.loading}>
              📋 Calculate TDS
            </Btn>
          </Card>
          <div>
            {tdsApi.data && (
              <Card style={{ marginBottom: 12 }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                  {[
                    { label: 'Gross Amount', value: `₹${(tdsApi.data.payment ?? tdsApi.data.gross_amount)?.toLocaleString()}`, color: '#e2e8f0' },
                    { label: 'TDS Rate',     value: `${tdsApi.data.applicable_rate ?? tdsApi.data.tds_rate}%`,    color: '#f59e0b' },
                    { label: 'TDS Deducted', value: `₹${(tdsApi.data.total_tds ?? tdsApi.data.tds_amount)?.toLocaleString()}`, color: '#ef4444' },
                    { label: 'Net Payment',  value: `₹${(tdsApi.data.net_payment ?? tdsApi.data.net_amount)?.toLocaleString()}`,  color: '#22c55e' },
                  ].map(s => (
                    <div key={s.label} style={{ background: '#0f1117', borderRadius: 8, padding: 12 }}>
                      <div style={{ color: s.color, fontSize: 18, fontWeight: 700 }}>{s.value}</div>
                      <div style={{ color: '#6b7280', fontSize: 11 }}>{s.label}</div>
                    </div>
                  ))}
                </div>
                <div style={{ marginTop: 10, padding: 10, background: 'rgba(99,102,241,0.1)', borderRadius: 8, fontSize: 12, color: '#a5b4fc' }}>
                  Section: {tdsApi.data.section} | Challan: {tdsApi.data.challan ?? tdsApi.data.challan_code}
                </div>
              </Card>
            )}
            <ResultBox data={tdsApi.data} loading={tdsApi.loading} error={tdsApi.error} title="TDS Calculation" />
          </div>
        </TwoCol>
      )}

      {tab === 'query' && (
        <TwoCol>
          <Card>
            <SectionHead title="Tax & Accounting Query" sub="GSTR-1, GSTR-3B, India-specific tax guidance" />
            {['How to file GSTR-3B?','What is reverse charge mechanism?','How to calculate advance tax?','What is TAN and how to apply?'].map(q => (
              <button key={q} onClick={() => setQuery(q)} style={{
                display: 'block', width: '100%', textAlign: 'left', padding: '7px 10px', marginBottom: 5,
                background: query === q ? 'rgba(99,102,241,0.1)' : 'none', border: `1px solid ${query === q ? '#6366f1' : '#1e2535'}`,
                borderRadius: 7, color: query === q ? '#a5b4fc' : '#6b7280', fontSize: 12, cursor: 'pointer',
              }}>{q}</button>
            ))}
            <Input label="Custom Query" value={query} onChange={setQuery} rows={3} />
            <Btn onClick={() => qApi.call(() => accountantQuery(query))} loading={qApi.loading}>🧮 Ask AI Accountant</Btn>
          </Card>
          <ResultBox data={qApi.data} loading={qApi.loading} error={qApi.error} title="Tax Advisory" />
        </TwoCol>
      )}
    </PageShell>
  )
}
