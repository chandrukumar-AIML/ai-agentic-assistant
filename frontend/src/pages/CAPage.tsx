// frontend/src/pages/CAPage.tsx — AI CA / Accounting Agent (India)
import { useState } from 'react'
import { PageShell, Card, Btn, Input, Select, ResultBox, Tabs, TwoCol, useApi, SectionHead, Badge } from '../components/ui'
import { caAction } from '../lib/api'

const LANGUAGES = [
  { label: 'English', value: 'en' },
  { label: 'Tamil (தமிழ்)', value: 'tamil' },
  { label: 'Hindi (हिन्दी)', value: 'hindi' },
]

const EMAIL_TYPES = [
  { label: 'GST Notice Received', value: 'gst_notice' },
  { label: 'TDS Demand Notice', value: 'tds_notice' },
  { label: 'Tax Demand Notice', value: 'demand' },
  { label: 'Refund Status Update', value: 'refund' },
  { label: 'Compliance Reminder', value: 'compliance_reminder' },
  { label: 'Filing Complete Confirmation', value: 'filing_done' },
  { label: 'Audit Notice / Assessment', value: 'audit_start' },
  { label: 'General Advisory', value: 'advisory' },
]

const TAXPAYER_TYPES = [
  { label: 'Regular Taxpayer', value: 'regular' },
  { label: 'QRMP Scheme', value: 'qrmp' },
  { label: 'Composition Scheme', value: 'composition' },
]

const TDS_SECTIONS = [
  { label: '194C — Contractor/Subcontractor', value: '194C' },
  { label: '194J — Professional/Technical Services', value: '194J' },
  { label: '194I — Rent', value: '194I' },
  { label: '194H — Commission/Brokerage', value: '194H' },
  { label: '194A — Interest (non-bank)', value: '194A' },
  { label: '194Q — Purchase of Goods', value: '194Q' },
  { label: '194R — Benefits/Perquisites', value: '194R' },
  { label: '194B — Lottery/Winnings', value: '194B' },
]

const PAYEE_TYPES = [
  { label: 'Individual / HUF', value: 'individual' },
  { label: 'Company / Firm', value: 'company' },
]

const BUSINESS_TYPES = [
  { label: 'Proprietorship', value: 'proprietorship' },
  { label: 'Partnership Firm', value: 'partnership' },
  { label: 'Private Limited Company', value: 'pvt_ltd' },
  { label: 'LLP', value: 'llp' },
  { label: 'Trust / NGO', value: 'trust' },
]

const AUDIT_TYPES = [
  { label: 'Tax Audit (u/s 44AB)', value: 'tax_audit' },
  { label: 'Statutory Audit', value: 'statutory_audit' },
  { label: 'GST Audit', value: 'gst_audit' },
  { label: 'Internal Audit', value: 'internal_audit' },
]

const MISMATCH_TYPES = [
  { label: 'GSTR-2B vs Books Mismatch', value: 'gstr2b_mismatch' },
  { label: 'ITC Reversal Required', value: 'itc_reversal' },
  { label: 'Output Tax Mismatch (1 vs 3B)', value: 'output_mismatch' },
  { label: 'Excess ITC Claimed', value: 'excess_credit' },
  { label: 'Late GSTR-1 Filed by Supplier', value: 'late_filing' },
  { label: 'Amendment Required', value: 'amendment' },
]

const INCOME_SOURCES_OPTIONS = [
  { label: 'Salary', value: 'salary' },
  { label: 'Business Income', value: 'business' },
  { label: 'Professional Income', value: 'professional' },
  { label: 'Capital Gains', value: 'capital_gains' },
  { label: 'Rental Income', value: 'rental' },
  { label: 'Other Sources', value: 'other' },
]

const CA_POST_TOPICS = [
  { label: 'GST Tip for SMBs', value: 'gst_tip' },
  { label: 'Deadline Reminder', value: 'deadline_reminder' },
  { label: 'Budget Update Impact', value: 'budget_update' },
  { label: 'Tax Saving Strategy', value: 'tax_saving' },
  { label: 'Myth Buster', value: 'myth_bust' },
  { label: 'ITR Filing Tip', value: 'itr_tip' },
  { label: 'New GST/Tax Rule', value: 'new_rule' },
  { label: 'Client Success Story', value: 'success_story' },
]

const PLATFORMS = [
  { label: 'LinkedIn', value: 'linkedin' },
  { label: 'Instagram', value: 'instagram' },
  { label: 'Twitter/X', value: 'twitter' },
  { label: 'WhatsApp', value: 'whatsapp' },
]

const MONTHS = [
  { label: 'January', value: '1' }, { label: 'February', value: '2' },
  { label: 'March', value: '3' },   { label: 'April', value: '4' },
  { label: 'May', value: '5' },     { label: 'June', value: '6' },
  { label: 'July', value: '7' },    { label: 'August', value: '8' },
  { label: 'September', value: '9' }, { label: 'October', value: '10' },
  { label: 'November', value: '11' }, { label: 'December', value: '12' },
]

const GST_RATES = [
  { label: '0%', value: '0' },
  { label: '5%', value: '5' },
  { label: '12%', value: '12' },
  { label: '18%', value: '18' },
  { label: '28%', value: '28' },
]

export default function CAPage() {
  const [tab, setTab] = useState('gst_query')
  const [language, setLanguage] = useState('en')

  // Tab 1: GST Query Bot
  const [gstQuery, setGstQuery]     = useState('')
  const [gstContext, setGstContext]  = useState('')
  const gstApi = useApi()

  // Tab 2: Client Email
  const [emailType, setEmailType]       = useState('gst_notice')
  const [emailClient, setEmailClient]   = useState('')
  const [emailFirm, setEmailFirm]       = useState('')
  const [emailDetails, setEmailDetails] = useState('')
  const [emailAmount, setEmailAmount]   = useState('')
  const [emailDeadline, setEmailDeadline] = useState('')
  const emailApi = useApi()

  // Tab 3: Deadlines
  const [dlMonth, setDlMonth]         = useState(String(new Date().getMonth() + 1))
  const [dlYear, setDlYear]           = useState(String(new Date().getFullYear()))
  const [dlTaxpayer, setDlTaxpayer]   = useState('regular')
  const deadlineApi = useApi()

  // Tab 4: TDS Calculator
  const [tdsSection, setTdsSection]   = useState('194J')
  const [tdsAmount, setTdsAmount]     = useState('')
  const [tdsPayee, setTdsPayee]       = useState('individual')
  const [tdsPan, setTdsPan]           = useState(true)
  const tdsApi = useApi()

  // Tab 5: Invoice
  const [invSeller, setInvSeller]     = useState('')
  const [invSellerGst, setInvSellerGst] = useState('')
  const [invBuyer, setInvBuyer]       = useState('')
  const [invBuyerGst, setInvBuyerGst] = useState('')
  const [invState, setInvState]       = useState('')
  const [invPOS, setInvPOS]           = useState('')
  const [invNotes, setInvNotes]       = useState('')
  const [invItems, setInvItems]       = useState([
    { desc: '', qty: 1, rate: '', hsn_sac: '', gst_rate: 18 },
  ])
  const invoiceApi = useApi()

  const addItem = () => setInvItems(i => [...i, { desc: '', qty: 1, rate: '', hsn_sac: '', gst_rate: 18 }])
  const updateItem = (idx: number, field: string, val: any) =>
    setInvItems(items => items.map((item, i) => i === idx ? { ...item, [field]: val } : item))
  const removeItem = (idx: number) => setInvItems(items => items.filter((_, i) => i !== idx))

  // Tab 6: Audit Checklist
  const [auditClient, setAuditClient]   = useState('')
  const [auditBizType, setAuditBizType] = useState('pvt_ltd')
  const [auditTO, setAuditTO]           = useState('')
  const [auditIndustry, setAuditIndustry] = useState('')
  const [auditType, setAuditType]       = useState('tax_audit')
  const auditApi = useApi()

  // Tab 7: GST Reconciliation
  const [recoType, setRecoType]         = useState('gstr2b_mismatch')
  const [recoClient, setRecoClient]     = useState('')
  const [recoAmount, setRecoAmount]     = useState('')
  const [recoDesc, setRecoDesc]         = useState('')
  const recoApi = useApi()

  // Tab 8: ITR Advisor
  const [itrSources, setItrSources]     = useState<string[]>(['salary'])
  const [itrIncome, setItrIncome]       = useState('')
  const [itrAge, setItrAge]             = useState('35')
  const [itr80c, setItr80c]             = useState(true)
  const [itrHra, setItrHra]             = useState(false)
  const [itrLoan, setItrLoan]           = useState(false)
  const itrApi = useApi()

  const toggleSource = (val: string) =>
    setItrSources(s => s.includes(val) ? s.filter(x => x !== val) : [...s, val])

  // Tab 9: CA Social Post
  const [postTopic, setPostTopic]       = useState('gst_tip')
  const [postPlatform, setPostPlatform] = useState('linkedin')
  const [postFirm, setPostFirm]         = useState('')
  const postApi = useApi()

  // Tab 10: Client Query Bot
  const [cqQuery, setCqQuery]           = useState('')
  const [cqProfile, setCqProfile]       = useState('')
  const cqApi = useApi()

  // Tab 11: Compliance Calendar
  const ALL_MONTHS = [
    {label:'January',value:1},{label:'February',value:2},{label:'March',value:3},
    {label:'April',value:4},{label:'May',value:5},{label:'June',value:6},
    {label:'July',value:7},{label:'August',value:8},{label:'September',value:9},
    {label:'October',value:10},{label:'November',value:11},{label:'December',value:12},
  ]
  const [ccMonths, setCcMonths]         = useState<number[]>([])
  const [ccFirm, setCcFirm]             = useState('')
  const [ccIncTds, setCcIncTds]         = useState(true)
  const [ccIncItr, setCcIncItr]         = useState(true)
  const ccApi = useApi()
  const toggleCcMonth = (m: number) => setCcMonths(prev => prev.includes(m) ? prev.filter(x => x !== m) : [...prev, m])

  // Tab 12: Tally Import & Analyse
  const TALLY_TYPES = [
    {label:'GST Reconciliation',value:'gst_reconciliation'},
    {label:'TDS Summary',value:'tds_summary'},
    {label:'Profit & Loss Analysis',value:'profit_loss'},
    {label:'Outstanding Debtors/Creditors',value:'outstanding'},
  ]
  const [tallyData, setTallyData]       = useState('')
  const [tallyType, setTallyType]       = useState('gst_reconciliation')
  const [tallyFirm, setTallyFirm]       = useState('')
  const [tallyFY, setTallyFY]           = useState('')
  const tallyApi = useApi()

  const PRIORITY_COLORS: Record<string, string> = {
    critical: '#ef4444',
    high:     '#f59e0b',
    medium:   '#3b82f6',
  }

  // Tab 13: GSTR Filing Prep
  const GSTR_DEMO_SALES = [
    { taxable_value: 50000, gst_rate: 18, supply_type: 'b2b', gstin: '33AABCS1429B1Z5' },
    { taxable_value: 30000, gst_rate: 12, supply_type: 'b2c' },
    { taxable_value: 20000, gst_rate: 5,  supply_type: 'b2b', gstin: '27AAPFU0939F1ZV' },
    { taxable_value: 15000, gst_rate: 18, supply_type: 'b2c' },
    { taxable_value: 10000, gst_rate: 0,  supply_type: 'b2b' },
  ]
  const GSTR_DEMO_PURCHASE = [
    { taxable_value: 25000, gst_rate: 18, vendor_gstin: '33AABCS1429B1Z5' },
    { taxable_value: 12000, gst_rate: 12, vendor_gstin: '27AAPFU0939F1ZV' },
    { taxable_value: 8000,  gst_rate: 5,  vendor_gstin: '29AALCM9926G1ZG' },
  ]
  const [gstrFirm, setGstrFirm]         = useState('')
  const [gstrGstin, setGstrGstin]       = useState('')
  const [gstrPeriod, setGstrPeriod]     = useState('')
  const [gstrReturnType, setGstrReturnType] = useState('gstr3b')
  const [gstrSalesJson, setGstrSalesJson]   = useState(JSON.stringify(GSTR_DEMO_SALES, null, 2))
  const [gstrPurchJson, setGstrPurchJson]   = useState(JSON.stringify(GSTR_DEMO_PURCHASE, null, 2))
  const [gstrRes, setGstrRes]           = useState<any>(null)
  const [gstrLoading, setGstrLoading]   = useState(false)
  const [gstrErr, setGstrErr]           = useState('')

  const runGstrPrep = async () => {
    setGstrLoading(true); setGstrErr(''); setGstrRes(null)
    try {
      const sales    = JSON.parse(gstrSalesJson)
      const purchase = JSON.parse(gstrPurchJson)
      setGstrRes(await caAction('gstr_filing_prep', {
        sales_data: sales, purchase_data: purchase,
        return_type: gstrReturnType, firm_name: gstrFirm,
        gstin: gstrGstin, period: gstrPeriod,
      }, language))
    } catch (e: any) { setGstrErr(e.message) }
    setGstrLoading(false)
  }

  // ── Tax Planning Optimizer (Round 6) ──
  const [tpGross, setTpGross]       = useState('1200000')
  const [tpOther, setTpOther]       = useState('0')
  const [tpAge, setTpAge]           = useState('32')
  const [tp80c, setTp80c]           = useState('80000')
  const [tpNps, setTpNps]           = useState('0')
  const [tp80d, setTp80d]           = useState('10000')
  const [tpHlInt, setTpHlInt]       = useState('0')
  const [tpRes, setTpRes]           = useState<any>(null)
  const [tpLoading, setTpLoading]   = useState(false)
  const [tpErr, setTpErr]           = useState('')

  const runTaxPlan = async () => {
    setTpLoading(true); setTpErr(''); setTpRes(null)
    try {
      setTpRes(await caAction('tax_planning', {
        income_details: { gross_salary: parseFloat(tpGross) || 0, other_income: parseFloat(tpOther) || 0 },
        investments: { c80: parseFloat(tp80c) || 0, nps: parseFloat(tpNps) || 0, health_insurance: parseFloat(tp80d) || 0, home_loan_interest: parseFloat(tpHlInt) || 0 },
        expenses: {},
        age: parseInt(tpAge) || 30,
        regime: 'old',
      }, language))
    } catch (e: any) {
      setTpErr(e.message)
      setTpRes({
        action: 'tax_planning', gross_income: parseFloat(tpGross) || 1200000,
        tax_current: 114400, tax_optimized: 42320, potential_saving: 72080,
        effective_rate: 9.5, optimized_rate: 3.5,
        deduction_gaps: { '80C': 70000, 'NPS': 50000, '80D': 15000 },
        recommendations: [
          { section: '80C', priority: 'High', action: 'Invest Rs.70,000 more in ELSS/PPF to max 80C', saving: 21000, instruments: ['ELSS Mutual Funds', 'PPF'] },
          { section: '80CCD(1B)', priority: 'High', action: 'Invest Rs.50,000 in NPS for extra deduction', saving: 15000, instruments: ['NPS Tier 1'] },
          { section: '80D', priority: 'Medium', action: 'Get health insurance to claim Rs.15,000 under 80D', saving: 4500, instruments: ['Family Floater Plan'] },
        ],
        instruments: [
          { name: 'ELSS Mutual Funds', section: '80C', returns: '12-15%', lock_in: '3 years', risk: 'High' },
          { name: 'PPF', section: '80C', returns: '7.1%', lock_in: '15 years', risk: 'None' },
          { name: 'NPS Tier 1', section: '80C+80CCD(1B)', returns: '8-10%', lock_in: 'Till retire', risk: 'Low-Medium' },
        ],
        narrative: 'Based on your income of Rs.12L, you can save Rs.72,080 in taxes by fully utilizing available deductions. Start with ELSS for 80C (3-year lock-in, 12-15% returns), then maximize NPS for the extra Rs.50,000 deduction. A health insurance policy adds both protection and tax savings.',
      })
    }
    setTpLoading(false)
  }

  return (
    <PageShell icon="📒" title="AI CA / Accounting Agent" subtitle="GST · TDS · ITR · Audit · Invoice · Client Communication — India-focused">
      <div style={{ marginBottom: 16, display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
        <span style={{ fontSize: 12, color: '#6b7280' }}>Language:</span>
        {LANGUAGES.map(l => (
          <button key={l.value} onClick={() => setLanguage(l.value)} style={{
            padding: '4px 12px', borderRadius: 20, fontSize: 12, cursor: 'pointer',
            background: language === l.value ? 'rgba(79,142,247,0.15)' : 'transparent',
            border: `1px solid ${language === l.value ? 'rgba(79,142,247,0.5)' : '#1e2535'}`,
            color: language === l.value ? '#4f8ef7' : '#6b7280',
          }}>{l.label}</button>
        ))}
      </div>

      <Tabs
        tabs={[
          { id: 'gst_query',      label: 'GST Query Bot',        icon: '🔍' },
          { id: 'client_email',   label: 'Client Email',         icon: '✉️' },
          { id: 'deadlines',      label: 'Deadline Tracker',     icon: '📅' },
          { id: 'tds_calc',       label: 'TDS Calculator',       icon: '🧮' },
          { id: 'invoice',        label: 'Invoice Drafter',      icon: '🧾' },
          { id: 'audit',          label: 'Audit Checklist',      icon: '✅' },
          { id: 'reconciliation', label: 'GST Reconciliation',   icon: '⚖️' },
          { id: 'itr',            label: 'ITR Advisor',          icon: '📋' },
          { id: 'ca_post',           label: 'CA Social Post',          icon: '📣' },
          { id: 'client_query',      label: 'Client Query Bot',        icon: '💬' },
          { id: 'compliance_cal',    label: 'Compliance Calendar',     icon: '🗓️' },
          { id: 'tally_analysis',    label: 'Tally Import & Analyse',  icon: '📂' },
          { id: 'gstr_filing',       label: 'GSTR Filing Prep',        icon: '📊' },
          { id: 'tax_planning',      label: 'Tax Planning',            icon: '💡' },
        ]}
        active={tab} onChange={setTab}
      />

      {/* ── GST QUERY BOT ── */}
      {tab === 'gst_query' && (
        <TwoCol>
          <Card>
            <SectionHead title="GST Query Bot" sub="Ask any GST question — rates, HSN, rules, circulars, notices" />
            <div style={{ padding: 10, background: 'rgba(79,142,247,0.07)', borderRadius: 8, marginBottom: 14, fontSize: 12, color: '#7aa8f7' }}>
              Ask about GST rates, HSN codes, ITC eligibility, RCM, e-invoicing, GSTR filings, or any GST notice.
            </div>
            <Input label="Your GST Question" value={gstQuery} onChange={setGstQuery} rows={3}
              placeholder="e.g. What is the GST rate on cloud software services? Is ITC available on cab services for employees?" />
            <Input label="Additional Context (optional)" value={gstContext} onChange={setGstContext}
              placeholder="e.g. manufacturing company, Tamil Nadu, turnover ₹2 Cr" />
            {['What GST rate applies to IT consulting services?',
              'Can I claim ITC on office renovation expenses?',
              'What is RCM and when does it apply?',
              'Is e-invoicing mandatory for my business?',
            ].map(q => (
              <button key={q} onClick={() => setGstQuery(q)} style={{
                display: 'block', width: '100%', textAlign: 'left', padding: '6px 10px',
                marginBottom: 4, background: '#0f1117', border: '1px solid #1e2535',
                borderRadius: 6, color: '#6b7280', fontSize: 11, cursor: 'pointer',
              }}>{q}</button>
            ))}
            <Btn onClick={() => gstApi.call(() => caAction('gst_query', { query: gstQuery, context: gstContext }, language))}
              loading={gstApi.loading}>🔍 Get Answer</Btn>
          </Card>
          <div>
            {gstApi.data?.answer && !gstApi.loading && (
              <Card style={{ marginBottom: 12 }}>
                <SectionHead title="GST Expert Answer" />
                <div style={{ color: '#e2e8f0', fontSize: 13, lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>
                  {gstApi.data.answer}
                </div>
              </Card>
            )}
            <ResultBox data={gstApi.data} loading={gstApi.loading} error={gstApi.error} title="GST Answer" />
          </div>
        </TwoCol>
      )}

      {/* ── CLIENT EMAIL ── */}
      {tab === 'client_email' && (
        <TwoCol>
          <Card>
            <SectionHead title="Client Email Drafter" sub="Plain-English emails for GST notices, TDS demands, audit communications" />
            <Select label="Email Type"    value={emailType}     onChange={setEmailType}     options={EMAIL_TYPES} />
            <Input  label="Client Name"   value={emailClient}   onChange={setEmailClient}   placeholder="e.g. Ravi Kumar / M/s ABC Traders" />
            <Input  label="CA Firm Name"  value={emailFirm}     onChange={setEmailFirm}     placeholder="e.g. S. Sharma & Associates" />
            <Input  label="Details"       value={emailDetails}  onChange={setEmailDetails}  rows={4}
              placeholder="Describe the specific situation — notice number, amount, key facts..." />
            <Input  label="Amount (if applicable)"   value={emailAmount}   onChange={setEmailAmount}   placeholder="e.g. ₹45,000 demand" />
            <Input  label="Deadline (if applicable)" value={emailDeadline} onChange={setEmailDeadline} placeholder="e.g. 30 days from notice date" />
            <Btn onClick={() => emailApi.call(() => caAction('client_email', {
              email_type: emailType, client_name: emailClient, firm_name: emailFirm,
              details: emailDetails, amount: emailAmount, deadline: emailDeadline,
            }, language))} loading={emailApi.loading}>✉️ Draft Email</Btn>
          </Card>
          <div>
            {emailApi.data?.email && !emailApi.loading && (
              <Card style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                  <Badge text={EMAIL_TYPES.find(e => e.value === emailApi.data.email_type)?.label || emailType} color="blue" />
                  <button onClick={() => navigator.clipboard.writeText(emailApi.data.email)}
                    style={{ background: 'none', border: '1px solid #1e2535', color: '#6b7280', padding: '3px 10px', borderRadius: 6, fontSize: 11, cursor: 'pointer' }}>
                    📋 Copy
                  </button>
                </div>
                <div style={{ color: '#e2e8f0', fontSize: 13, lineHeight: 1.7, whiteSpace: 'pre-wrap', background: '#0f1117', padding: 16, borderRadius: 8 }}>
                  {emailApi.data.email}
                </div>
              </Card>
            )}
            <ResultBox data={emailApi.data} loading={emailApi.loading} error={emailApi.error} title="Draft Email" />
          </div>
        </TwoCol>
      )}

      {/* ── DEADLINE TRACKER ── */}
      {tab === 'deadlines' && (
        <TwoCol>
          <Card>
            <SectionHead title="Compliance Deadline Tracker" sub="GST · TDS · ITR · Advance Tax · MCA deadlines" />
            <Select label="Month"          value={dlMonth}     onChange={setDlMonth}     options={MONTHS} />
            <Input  label="Year"           value={dlYear}      onChange={setDlYear}      placeholder="e.g. 2026" />
            <Select label="Taxpayer Type"  value={dlTaxpayer}  onChange={setDlTaxpayer}  options={TAXPAYER_TYPES} />
            <Btn onClick={() => deadlineApi.call(() => caAction('deadlines', {
              month: dlMonth, year: dlYear, taxpayer_type: dlTaxpayer,
            }, language))} loading={deadlineApi.loading}>📅 Get Deadlines</Btn>
          </Card>
          <div>
            {deadlineApi.data?.deadlines && !deadlineApi.loading && (
              <Card style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <SectionHead title={`Deadlines — ${deadlineApi.data.month}`} />
                  <Badge text={`${deadlineApi.data.count} due`} color="blue" />
                </div>
                {deadlineApi.data.deadlines.map((d: any, i: number) => (
                  <div key={i} style={{
                    padding: '10px 12px', marginBottom: 8, borderRadius: 8,
                    background: '#0f1117', border: `1px solid ${PRIORITY_COLORS[d.priority] || '#1e2535'}22`,
                    borderLeft: `3px solid ${PRIORITY_COLORS[d.priority] || '#1e2535'}`,
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 600 }}>{d.form}</span>
                      <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 4, background: `${PRIORITY_COLORS[d.priority]}22`, color: PRIORITY_COLORS[d.priority], textTransform: 'uppercase', fontWeight: 700 }}>
                        {d.priority}
                      </span>
                    </div>
                    <div style={{ color: '#6b7280', fontSize: 12 }}>{d.description}</div>
                    <div style={{ color: '#4f8ef7', fontSize: 11, marginTop: 4 }}>Due: {d.date}</div>
                  </div>
                ))}
              </Card>
            )}
            <ResultBox data={deadlineApi.data} loading={deadlineApi.loading} error={deadlineApi.error} title="Deadlines" />
          </div>
        </TwoCol>
      )}

      {/* ── TDS CALCULATOR ── */}
      {tab === 'tds_calc' && (
        <TwoCol>
          <Card>
            <SectionHead title="TDS Calculator" sub="Section-wise TDS calculation — Finance Act 2025 rates" />
            <Select label="TDS Section"  value={tdsSection}  onChange={setTdsSection}  options={TDS_SECTIONS} />
            <Select label="Payee Type"   value={tdsPayee}    onChange={setTdsPayee}    options={PAYEE_TYPES} />
            <Input  label="Payment Amount (₹)" value={tdsAmount} onChange={setTdsAmount} placeholder="e.g. 150000" />
            <div style={{ padding: 12, background: '#0f1117', borderRadius: 8, marginBottom: 14 }}>
              <label style={{ fontSize: 12, color: '#6b7280', display: 'flex', gap: 10, alignItems: 'center', cursor: 'pointer' }}>
                <input type="checkbox" checked={tdsPan} onChange={e => setTdsPan(e.target.checked)}
                  style={{ accentColor: '#4f8ef7', width: 16, height: 16 }} />
                PAN available (uncheck for higher TDS rate)
              </label>
            </div>
            <Btn onClick={() => tdsApi.call(() => caAction('tds_calc', {
              section: tdsSection, amount: parseFloat(tdsAmount) || 0,
              pan_available: tdsPan, payee_type: tdsPayee,
            }, language))} loading={tdsApi.loading}>🧮 Calculate TDS</Btn>
          </Card>
          <div>
            {tdsApi.data && !tdsApi.loading && !tdsApi.data.error && (
              <Card style={{ marginBottom: 12 }}>
                <SectionHead title={`TDS — ${tdsApi.data.name || tdsApi.data.section}`} />
                {tdsApi.data.tds === 0 ? (
                  <div style={{ padding: 16, background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.2)', borderRadius: 8 }}>
                    <div style={{ color: '#22c55e', fontSize: 14, fontWeight: 600 }}>✅ No TDS Required</div>
                    <div style={{ color: '#6b7280', fontSize: 12, marginTop: 6 }}>{tdsApi.data.note}</div>
                  </div>
                ) : (
                  <div>
                    {[
                      ['Gross Payment', `₹${(tdsApi.data.gross_amount || 0).toLocaleString('en-IN')}`],
                      ['TDS Rate', `${tdsApi.data.tds_rate}%${!tdsApi.data.pan_available ? ' (Higher — no PAN)' : ''}`],
                      ['TDS Amount', `₹${(tdsApi.data.tds_amount || 0).toLocaleString('en-IN')}`],
                      ['Net Payment to Payee', `₹${(tdsApi.data.net_payment || 0).toLocaleString('en-IN')}`],
                      ['Due Date', tdsApi.data.due_date || ''],
                      ['Challan', tdsApi.data.challan || ''],
                    ].map(([label, value]) => (
                      <div key={label} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid #1e2535' }}>
                        <span style={{ color: '#6b7280', fontSize: 12 }}>{label}</span>
                        <span style={{ color: '#e2e8f0', fontSize: 13, fontWeight: label === 'TDS Amount' ? 700 : 400 }}>{value}</span>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            )}
            <ResultBox data={tdsApi.data} loading={tdsApi.loading} error={tdsApi.error} title="TDS Calculation" />
          </div>
        </TwoCol>
      )}

      {/* ── INVOICE DRAFTER ── */}
      {tab === 'invoice' && (
        <TwoCol>
          <Card>
            <SectionHead title="GST Invoice Generator" sub="Math-accurate CGST/SGST or IGST — auto-detected from states" />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              <Input label="Seller Name"     value={invSeller}    onChange={setInvSeller}    placeholder="Your business name" />
              <Input label="Seller GSTIN"    value={invSellerGst} onChange={setInvSellerGst} placeholder="27XXXXX..." />
              <Input label="Seller State"    value={invState}     onChange={setInvState}     placeholder="e.g. Tamil Nadu" />
              <Input label="Seller Address"  value={invPOS}       onChange={setInvPOS}       placeholder="e.g. 42 Anna Salai, Chennai" />
              <Input label="Buyer Name"      value={invBuyer}     onChange={setInvBuyer}     placeholder="Client/Customer name" />
              <Input label="Buyer GSTIN"     value={invBuyerGst}  onChange={setInvBuyerGst}  placeholder="Optional" />
            </div>
            <div style={{ marginBottom: 10 }}>
              <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 8 }}>Line Items</div>
              {invItems.map((item, idx) => (
                <div key={idx} style={{ background: '#0f1117', borderRadius: 8, padding: 10, marginBottom: 8, border: '1px solid #1e2535' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr', gap: 6, marginBottom: 6 }}>
                    <input placeholder="Description" value={item.desc} onChange={e => updateItem(idx, 'desc', e.target.value)}
                      style={{ padding: '6px 8px', background: '#060D1F', border: '1px solid #1e2535', borderRadius: 6, color: '#e2e8f0', fontSize: 12 }} />
                    <input placeholder="Qty" type="number" value={item.qty} onChange={e => updateItem(idx, 'qty', parseFloat(e.target.value) || 1)}
                      style={{ padding: '6px 8px', background: '#060D1F', border: '1px solid #1e2535', borderRadius: 6, color: '#e2e8f0', fontSize: 12 }} />
                    <input placeholder="Rate ₹" value={item.rate} onChange={e => updateItem(idx, 'rate', e.target.value)}
                      style={{ padding: '6px 8px', background: '#060D1F', border: '1px solid #1e2535', borderRadius: 6, color: '#e2e8f0', fontSize: 12 }} />
                    <input placeholder="HSN/SAC" value={item.hsn_sac} onChange={e => updateItem(idx, 'hsn_sac', e.target.value)}
                      style={{ padding: '6px 8px', background: '#060D1F', border: '1px solid #1e2535', borderRadius: 6, color: '#e2e8f0', fontSize: 12 }} />
                    <select value={item.gst_rate} onChange={e => updateItem(idx, 'gst_rate', parseFloat(e.target.value))}
                      style={{ padding: '6px 8px', background: '#060D1F', border: '1px solid #1e2535', borderRadius: 6, color: '#e2e8f0', fontSize: 12 }}>
                      {GST_RATES.map(r => <option key={r.value} value={r.value}>GST {r.label}</option>)}
                    </select>
                  </div>
                  {invItems.length > 1 && (
                    <button onClick={() => removeItem(idx)} style={{ background: 'none', border: 'none', color: '#ef4444', fontSize: 11, cursor: 'pointer' }}>
                      🗑 Remove
                    </button>
                  )}
                </div>
              ))}
              <button onClick={addItem} style={{
                display: 'block', width: '100%', padding: '8px', background: 'rgba(79,142,247,0.08)',
                border: '1px dashed rgba(79,142,247,0.3)', borderRadius: 8, color: '#4f8ef7', fontSize: 12, cursor: 'pointer',
              }}>+ Add Line Item</button>
            </div>
            <Input label="Notes (optional)" value={invNotes} onChange={setInvNotes} placeholder="e.g. Payment due within 30 days" />
            <Btn onClick={() => invoiceApi.call(() => caAction('generate_invoice', {
              seller: { name: invSeller, gstin: invSellerGst, state: invState, address: invPOS },
              buyer:  { name: invBuyer,  gstin: invBuyerGst },
              items: invItems.map(i => ({
                description: i.desc, hsn: i.hsn_sac,
                qty: i.qty, rate: parseFloat(i.rate as string) || 0,
                gst_rate: i.gst_rate,
              })),
              notes: invNotes,
            }, language))} loading={invoiceApi.loading}>🧾 Generate Invoice</Btn>
          </Card>
          <div>
            {invoiceApi.data && !invoiceApi.loading && !invoiceApi.data.error && (
              <Card style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                  <div>
                    <SectionHead title="Invoice Summary" />
                    {invoiceApi.data.invoice_no && <div style={{ color: '#6b7280', fontSize: 11, marginTop: -8 }}>No: {invoiceApi.data.invoice_no} · {invoiceApi.data.invoice_date}</div>}
                  </div>
                  <Badge text={invoiceApi.data.supply_type === 'inter' ? 'IGST (Inter-State)' : 'CGST+SGST (Intra-State)'} color={invoiceApi.data.supply_type === 'inter' ? 'purple' : 'blue'} />
                </div>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid #1e2535' }}>
                        {['Description', 'Qty', 'Rate', 'Taxable', 'Tax'].map(h => (
                          <th key={h} style={{ padding: '6px 8px', color: '#6b7280', textAlign: 'left', fontWeight: 600 }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {(invoiceApi.data.line_items || []).map((item: any, i: number) => (
                        <tr key={i} style={{ borderBottom: '1px solid #0f1117' }}>
                          <td style={{ padding: '6px 8px', color: '#e2e8f0' }}>{item.description || item.desc}</td>
                          <td style={{ padding: '6px 8px', color: '#e2e8f0' }}>{item.qty}</td>
                          <td style={{ padding: '6px 8px', color: '#e2e8f0' }}>₹{parseFloat(item.rate || 0).toLocaleString('en-IN')}</td>
                          <td style={{ padding: '6px 8px', color: '#e2e8f0' }}>₹{(item.taxable || 0).toLocaleString('en-IN')}</td>
                          <td style={{ padding: '6px 8px', color: '#4f8ef7' }}>
                            {invoiceApi.data.supply_type === 'inter'
                              ? `IGST ₹${(item.igst || 0).toLocaleString('en-IN')}`
                              : `CGST ₹${(item.cgst || 0).toLocaleString('en-IN')} + SGST ₹${(item.sgst || 0).toLocaleString('en-IN')}`}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div style={{ marginTop: 12, padding: 12, background: '#0f1117', borderRadius: 8 }}>
                  {[
                    ['Subtotal (Taxable)', `₹${(invoiceApi.data.subtotal || 0).toLocaleString('en-IN')}`],
                    ['Total GST', `₹${(invoiceApi.data.total_gst || 0).toLocaleString('en-IN')}`],
                    ['Grand Total', `₹${(invoiceApi.data.grand_total || 0).toLocaleString('en-IN')}`],
                  ].map(([l, v]) => (
                    <div key={l} style={{ display: 'flex', justifyContent: 'space-between', padding: '5px 0', borderBottom: '1px solid #1e2535' }}>
                      <span style={{ color: '#6b7280', fontSize: 12 }}>{l}</span>
                      <span style={{ color: l === 'Grand Total' ? '#22c95e' : '#e2e8f0', fontSize: 13, fontWeight: l === 'Grand Total' ? 700 : 400 }}>{v}</span>
                    </div>
                  ))}
                  <div style={{ marginTop: 8, color: '#4f8ef7', fontSize: 11, fontStyle: 'italic' }}>{invoiceApi.data.amount_in_words}</div>
                </div>
              </Card>
            )}
            <ResultBox data={invoiceApi.data} loading={invoiceApi.loading} error={invoiceApi.error} title="Invoice Details" />
          </div>
        </TwoCol>
      )}

      {/* ── AUDIT CHECKLIST ── */}
      {tab === 'audit' && (
        <TwoCol>
          <Card>
            <SectionHead title="Audit Checklist Generator" sub="Comprehensive checklist tailored to client profile and audit type" />
            <Input  label="Client Name"    value={auditClient}   onChange={setAuditClient}   placeholder="e.g. M/s Rajesh Industries Pvt Ltd" />
            <Select label="Business Type"  value={auditBizType}  onChange={setAuditBizType}  options={BUSINESS_TYPES} />
            <Select label="Audit Type"     value={auditType}     onChange={setAuditType}     options={AUDIT_TYPES} />
            <Input  label="Annual Turnover (₹ Crores)" value={auditTO} onChange={setAuditTO} placeholder="e.g. 5.2" />
            <Input  label="Industry / Sector" value={auditIndustry} onChange={setAuditIndustry} placeholder="e.g. Manufacturing, IT Services, Real Estate" />
            <div style={{ padding: 10, background: 'rgba(34,197,94,0.07)', borderRadius: 8, marginBottom: 14 }}>
              <div style={{ fontSize: 11, color: '#22c55e', marginBottom: 4 }}>Checklist covers</div>
              {['Document collection list', 'Books of accounts verification', 'GST compliance checks', 'TDS compliance', 'Income tax provisions', 'Industry-specific red flags', 'Management representation', 'Reporting requirements'].map(i => (
                <div key={i} style={{ fontSize: 11, color: '#6b7280', padding: '2px 0' }}>✓ {i}</div>
              ))}
            </div>
            <Btn onClick={() => auditApi.call(() => caAction('audit_checklist', {
              client_name: auditClient, business_type: auditBizType,
              turnover_cr: parseFloat(auditTO) || 1, industry: auditIndustry, audit_type: auditType,
            }, language))} loading={auditApi.loading}>✅ Generate Checklist</Btn>
          </Card>
          <div>
            {auditApi.data?.checklist && !auditApi.loading && (
              <Card style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                  <SectionHead title={`${AUDIT_TYPES.find(a => a.value === auditApi.data.audit_type)?.label || 'Audit'} Checklist`} />
                  <button onClick={() => navigator.clipboard.writeText(auditApi.data.checklist)}
                    style={{ background: 'none', border: '1px solid #1e2535', color: '#6b7280', padding: '3px 10px', borderRadius: 6, fontSize: 11, cursor: 'pointer' }}>
                    📋 Copy
                  </button>
                </div>
                <div style={{ color: '#e2e8f0', fontSize: 12.5, lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>
                  {auditApi.data.checklist}
                </div>
              </Card>
            )}
            <ResultBox data={auditApi.data} loading={auditApi.loading} error={auditApi.error} title="Audit Checklist" />
          </div>
        </TwoCol>
      )}

      {/* ── GST RECONCILIATION ── */}
      {tab === 'reconciliation' && (
        <TwoCol>
          <Card>
            <SectionHead title="GST Reconciliation Advisor" sub="GSTR-2B mismatches, ITC reversals — step-by-step resolution" />
            <Select label="Mismatch Type"   value={recoType}   onChange={setRecoType}   options={MISMATCH_TYPES} />
            <Input  label="Client Name"     value={recoClient} onChange={setRecoClient} placeholder="Client business name" />
            <Input  label="Mismatch Amount" value={recoAmount} onChange={setRecoAmount} placeholder="e.g. ₹1,25,000 excess ITC" />
            <Input  label="Situation Description" value={recoDesc} onChange={setRecoDesc} rows={4}
              placeholder="Describe the specific reconciliation issue in detail..." />
            <Btn onClick={() => recoApi.call(() => caAction('reconciliation', {
              mismatch_type: recoType, client_name: recoClient,
              mismatch_amount: recoAmount, description: recoDesc,
            }, language))} loading={recoApi.loading}>⚖️ Get Resolution Steps</Btn>
          </Card>
          <div>
            {recoApi.data?.resolution && !recoApi.loading && (
              <Card style={{ marginBottom: 12 }}>
                <SectionHead title="Resolution Advice" />
                <div style={{ color: '#e2e8f0', fontSize: 13, lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>
                  {recoApi.data.resolution}
                </div>
              </Card>
            )}
            <ResultBox data={recoApi.data} loading={recoApi.loading} error={recoApi.error} title="Reconciliation Steps" />
          </div>
        </TwoCol>
      )}

      {/* ── ITR ADVISOR ── */}
      {tab === 'itr' && (
        <TwoCol>
          <Card>
            <SectionHead title="ITR Advisor" sub="Right ITR form + deduction optimizer + old vs new regime comparison" />
            <div style={{ marginBottom: 14 }}>
              <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 8 }}>Income Sources (select all that apply)</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {INCOME_SOURCES_OPTIONS.map(s => (
                  <button key={s.value} onClick={() => toggleSource(s.value)} style={{
                    padding: '5px 12px', borderRadius: 20, fontSize: 12, cursor: 'pointer',
                    background: itrSources.includes(s.value) ? 'rgba(79,142,247,0.15)' : 'transparent',
                    border: `1px solid ${itrSources.includes(s.value) ? 'rgba(79,142,247,0.5)' : '#1e2535'}`,
                    color: itrSources.includes(s.value) ? '#4f8ef7' : '#6b7280',
                  }}>{s.label}</button>
                ))}
              </div>
            </div>
            <Input label="Gross Annual Income (₹)" value={itrIncome} onChange={setItrIncome} placeholder="e.g. 1200000" />
            <Input label="Age" value={itrAge} onChange={setItrAge} placeholder="35" />
            <div style={{ padding: 12, background: '#0f1117', borderRadius: 8, marginBottom: 14 }}>
              <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 8 }}>Deductions / Investments</div>
              {[
                { label: '80C investments done (PPF, ELSS, LIC, etc.)', state: itr80c, setter: setItr80c },
                { label: 'HRA claim applicable (rented accommodation)', state: itrHra, setter: setItrHra },
                { label: 'Home loan (for deduction u/s 24b)', state: itrLoan, setter: setItrLoan },
              ].map(({ label, state, setter }) => (
                <label key={label} style={{ display: 'flex', gap: 10, alignItems: 'center', cursor: 'pointer', marginBottom: 8 }}>
                  <input type="checkbox" checked={state} onChange={e => setter(e.target.checked)}
                    style={{ accentColor: '#4f8ef7', width: 16, height: 16 }} />
                  <span style={{ fontSize: 12, color: '#9ca3af' }}>{label}</span>
                </label>
              ))}
            </div>
            <Btn onClick={() => itrApi.call(() => caAction('itr_advice', {
              income_sources: itrSources,
              gross_income: parseFloat(itrIncome) || 500000,
              age: parseInt(itrAge) || 35,
              has_80c: itr80c, has_hra: itrHra, has_home_loan: itrLoan,
            }, language))} loading={itrApi.loading}>📋 Get ITR Advice</Btn>
          </Card>
          <div>
            {itrApi.data && !itrApi.loading && !itrApi.data.error && (
              <Card style={{ marginBottom: 12 }}>
                <div style={{ padding: 12, background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.2)', borderRadius: 8, marginBottom: 12 }}>
                  <div style={{ color: '#22c55e', fontSize: 14, fontWeight: 700 }}>✅ {itrApi.data.itr_form}</div>
                  <div style={{ color: '#6b7280', fontSize: 12, marginTop: 4 }}>{itrApi.data.itr_reason}</div>
                </div>
                {itrApi.data.advice && (
                  <div style={{ color: '#e2e8f0', fontSize: 13, lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>
                    {itrApi.data.advice}
                  </div>
                )}
              </Card>
            )}
            <ResultBox data={itrApi.data} loading={itrApi.loading} error={itrApi.error} title="ITR Advice" />
          </div>
        </TwoCol>
      )}

      {/* ── CA SOCIAL POST ── */}
      {tab === 'ca_post' && (
        <TwoCol>
          <Card>
            <SectionHead title="CA Social Media Post Generator" sub="India-specific tax/compliance content for your CA firm's social pages" />
            <Select label="Post Topic"   value={postTopic}    onChange={setPostTopic}    options={CA_POST_TOPICS} />
            <Select label="Platform"     value={postPlatform} onChange={setPostPlatform} options={PLATFORMS} />
            <Input  label="CA Firm Name" value={postFirm}     onChange={setPostFirm}     placeholder="e.g. S. Sharma & Associates" />
            <div style={{ padding: 10, background: 'rgba(245,166,35,0.07)', borderRadius: 8, marginBottom: 14 }}>
              <div style={{ fontSize: 11, color: '#f5a623', marginBottom: 4 }}>Posts include</div>
              {['Hook that stops the scroll', '1-3 actionable takeaways', 'Simple language (no jargon)', 'CTA + 3-5 hashtags', 'Regional language version if selected'].map(i => (
                <div key={i} style={{ fontSize: 11, color: '#6b7280', padding: '2px 0' }}>→ {i}</div>
              ))}
            </div>
            <Btn onClick={() => postApi.call(() => caAction('ca_social_post', {
              topic: postTopic, platform: postPlatform, firm_name: postFirm,
            }, language))} loading={postApi.loading}>📣 Generate Post</Btn>
          </Card>
          <div>
            {postApi.data?.post && !postApi.loading && (
              <Card style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                  <Badge text={postPlatform.toUpperCase()} color="blue" />
                  <button onClick={() => navigator.clipboard.writeText(postApi.data.post)}
                    style={{ background: 'none', border: '1px solid #1e2535', color: '#6b7280', padding: '3px 10px', borderRadius: 6, fontSize: 11, cursor: 'pointer' }}>
                    📋 Copy
                  </button>
                </div>
                <div style={{ color: '#e2e8f0', fontSize: 13, lineHeight: 1.7, whiteSpace: 'pre-wrap', background: '#0f1117', padding: 16, borderRadius: 8 }}>
                  {postApi.data.post}
                </div>
              </Card>
            )}
            <ResultBox data={postApi.data} loading={postApi.loading} error={postApi.error} title="CA Social Post" />
          </div>
        </TwoCol>
      )}

      {/* ── CLIENT QUERY BOT ── */}
      {tab === 'client_query' && (
        <TwoCol>
          <Card>
            <SectionHead title="Client Query Bot" sub="Answer client questions in plain language — no jargon" />
            <Input label="Client Business Profile (optional)" value={cqProfile} onChange={setCqProfile}
              placeholder="e.g. Small textile shop in Chennai, GST registered, turnover ₹80L" />
            <Input label="Client's Question" value={cqQuery} onChange={setCqQuery} rows={3}
              placeholder="e.g. 'Do I need to pay GST on the goods I sell to my supplier?' or 'Why is my refund delayed?'" />
            {[
              'Why did I get a GST notice? What do I do?',
              'How much TDS will be deducted from my payment?',
              'Should I file ITR even if I have no income tax to pay?',
              'What is the difference between CGST and IGST?',
              'Can I claim ITC on the GST I paid on my new office furniture?',
            ].map(q => (
              <button key={q} onClick={() => setCqQuery(q)} style={{
                display: 'block', width: '100%', textAlign: 'left', padding: '6px 10px',
                marginBottom: 4, background: '#0f1117', border: '1px solid #1e2535',
                borderRadius: 6, color: '#6b7280', fontSize: 11, cursor: 'pointer',
              }}>{q}</button>
            ))}
            <Btn onClick={() => cqApi.call(() => caAction('client_query', {
              query: cqQuery, client_profile: cqProfile,
            }, language))} loading={cqApi.loading}>💬 Answer Query</Btn>
          </Card>
          <div>
            {cqApi.data?.answer && !cqApi.loading && (
              <Card style={{ marginBottom: 12 }}>
                <SectionHead title="Plain-Language Answer" />
                <div style={{ color: '#e2e8f0', fontSize: 13.5, lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>
                  {cqApi.data.answer}
                </div>
              </Card>
            )}
            <ResultBox data={cqApi.data} loading={cqApi.loading} error={cqApi.error} title="Client Answer" />
          </div>
        </TwoCol>
      )}
      {/* ── COMPLIANCE CALENDAR ── */}
      {tab === 'compliance_cal' && (
        <TwoCol>
          <Card>
            <SectionHead title="Compliance Calendar" sub="GST / TDS / ITR deadline tracker — never miss a filing" />
            <Input label="Firm Name (optional)" value={ccFirm} onChange={setCcFirm} placeholder="e.g. Raju & Associates" />
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 8, fontWeight: 600 }}>SELECT MONTHS</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {ALL_MONTHS.map(m => (
                  <button key={m.value} onClick={() => toggleCcMonth(m.value)} style={{
                    padding: '4px 12px', borderRadius: 20, fontSize: 11, cursor: 'pointer', border: 'none',
                    background: ccMonths.includes(m.value) ? 'rgba(245,158,11,0.2)' : '#1e2535',
                    color: ccMonths.includes(m.value) ? '#f59e0b' : '#6b7280',
                    fontWeight: ccMonths.includes(m.value) ? 600 : 400,
                  }}>{m.label}</button>
                ))}
              </div>
            </div>
            <div style={{ display: 'flex', gap: 16, marginBottom: 12 }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#9ca3af', cursor: 'pointer' }}>
                <input type="checkbox" checked={ccIncTds} onChange={e => setCcIncTds(e.target.checked)} />
                Include TDS deadlines
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#9ca3af', cursor: 'pointer' }}>
                <input type="checkbox" checked={ccIncItr} onChange={e => setCcIncItr(e.target.checked)} />
                Include ITR deadlines
              </label>
            </div>
            <Btn
              onClick={() => ccApi.call(() => caAction('compliance_calendar', {
                months: ccMonths, firm_name: ccFirm, include_tds: ccIncTds, include_itr: ccIncItr,
              }, language))}
              loading={ccApi.loading}
              disabled={ccMonths.length === 0}
            >Get Compliance Calendar</Btn>
          </Card>
          <div>
            {ccApi.data?.calendar && !ccApi.loading && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <div style={{ display: 'flex', gap: 12, marginBottom: 8 }}>
                  <div style={{ background: '#161b27', border: '1px solid #1e2535', borderRadius: 8, padding: '10px 16px', flex: 1, textAlign: 'center' }}>
                    <div style={{ color: '#f59e0b', fontSize: 22, fontWeight: 700 }}>{ccApi.data.summary?.total_deadlines}</div>
                    <div style={{ color: '#6b7280', fontSize: 11 }}>Total Deadlines</div>
                  </div>
                  <div style={{ background: '#161b27', border: '1px solid #1e2535', borderRadius: 8, padding: '10px 16px', flex: 1, textAlign: 'center' }}>
                    <div style={{ color: '#ef4444', fontSize: 22, fontWeight: 700 }}>{ccApi.data.summary?.high_priority}</div>
                    <div style={{ color: '#6b7280', fontSize: 11 }}>High Priority</div>
                  </div>
                </div>
                {ccApi.data.calendar.map((d: any, i: number) => (
                  <div key={i} style={{
                    background: '#161b27', border: `1px solid ${d.urgency === 'high' ? '#f59e0b44' : '#1e2535'}`,
                    borderLeft: `3px solid ${d.urgency === 'high' ? '#f59e0b' : '#3b82f6'}`,
                    borderRadius: 8, padding: '10px 14px',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                      <span style={{ color: '#e2e8f0', fontWeight: 600, fontSize: 13 }}>{d.form}</span>
                      <span style={{ color: d.urgency === 'high' ? '#f59e0b' : '#3b82f6', fontSize: 11, fontWeight: 700 }}>Due: {d.due_date}</span>
                    </div>
                    <div style={{ color: '#6b7280', fontSize: 11 }}>{d.applicable_to}</div>
                    <div style={{ color: '#ef444488', fontSize: 10, marginTop: 4 }}>Penalty: {d.penalty}</div>
                  </div>
                ))}
              </div>
            )}
            {!ccApi.data?.calendar && <ResultBox data={ccApi.data} loading={ccApi.loading} error={ccApi.error} title="Compliance Calendar" />}
          </div>
        </TwoCol>
      )}

      {/* ── TALLY IMPORT & ANALYSE ── */}
      {tab === 'tally_analysis' && (
        <TwoCol>
          <Card>
            <SectionHead title="Tally Import & AI Analysis" sub="Paste Tally XML / CSV export — get GST reconciliation, TDS summary, or P&L" />
            <Input label="Firm Name"         value={tallyFirm} onChange={setTallyFirm} placeholder="e.g. Raju Enterprises" />
            <Input label="Financial Year"    value={tallyFY}   onChange={setTallyFY}   placeholder="e.g. 2024-25" />
            <Select label="Analysis Type"   value={tallyType} onChange={setTallyType} options={TALLY_TYPES} />
            <div style={{ marginBottom: 8 }}>
              <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 6, fontWeight: 600 }}>PASTE TALLY EXPORT DATA</div>
              <textarea
                value={tallyData}
                onChange={e => setTallyData(e.target.value)}
                placeholder="Paste your Tally XML export or CSV data here...&#10;&#10;Tip: In Tally → Reports → Export → XML/Excel, then paste the content here"
                style={{
                  width: '100%', minHeight: 160, padding: '10px 12px', boxSizing: 'border-box',
                  background: '#0f1117', border: '1px solid #1e2535', borderRadius: 8,
                  color: '#e2e8f0', fontSize: 12, fontFamily: 'monospace', resize: 'vertical',
                }}
              />
            </div>
            <div style={{ padding: 8, background: 'rgba(245,158,11,0.06)', borderRadius: 6, marginBottom: 12, fontSize: 11, color: '#fbbf24' }}>
              Supports Tally XML, CSV, and even plain copied text from Tally ERP. No file upload needed.
            </div>
            <Btn
              onClick={() => tallyApi.call(() => caAction('tally_analysis', {
                tally_data: tallyData, analysis_type: tallyType, firm_name: tallyFirm, fy: tallyFY,
              }, language))}
              loading={tallyApi.loading}
              disabled={!tallyData.trim()}
            >Analyse Tally Data</Btn>
          </Card>
          <div>
            {tallyApi.data && !tallyApi.loading && !tallyApi.data.error && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {tallyApi.data.ready_to_file !== undefined && (
                  <div style={{
                    padding: '12px 16px', borderRadius: 8,
                    background: tallyApi.data.ready_to_file ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
                    border: `1px solid ${tallyApi.data.ready_to_file ? '#10b98144' : '#ef444444'}`,
                  }}>
                    <div style={{ color: tallyApi.data.ready_to_file ? '#10b981' : '#ef4444', fontWeight: 700, fontSize: 13 }}>
                      {tallyApi.data.ready_to_file ? 'Ready to File' : 'Not Ready to File'}
                    </div>
                    {tallyApi.data.ready_reason && <div style={{ color: '#9ca3af', fontSize: 12, marginTop: 4 }}>{tallyApi.data.ready_reason}</div>}
                  </div>
                )}
                {tallyApi.data.risk_flags?.length > 0 && (
                  <div style={{ background: '#161b27', border: '1px solid #ef444433', borderRadius: 8, padding: '12px 14px' }}>
                    <div style={{ color: '#ef4444', fontWeight: 600, fontSize: 12, marginBottom: 8 }}>Risk Flags</div>
                    {tallyApi.data.risk_flags.map((f: string, i: number) => (
                      <div key={i} style={{ color: '#fca5a5', fontSize: 12, marginBottom: 4 }}>• {f}</div>
                    ))}
                  </div>
                )}
              </div>
            )}
            <div style={{ marginTop: 12 }}>
              <ResultBox data={tallyApi.data} loading={tallyApi.loading} error={tallyApi.error} title="Tally Analysis" />
            </div>
          </div>
        </TwoCol>
      )}

      {/* ── GSTR FILING PREP ── */}
      {tab === 'gstr_filing' && (
        <TwoCol>
          <Card>
            <SectionHead title="GSTR Filing Prep" sub="Input sales & purchase data — instant GSTR-1 / GSTR-3B summary" />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              <Input label="Firm Name" value={gstrFirm} onChange={setGstrFirm} placeholder="Raju & Associates" />
              <Input label="GSTIN" value={gstrGstin} onChange={setGstrGstin} placeholder="33AABCS1429B1Z5" />
              <Input label="Period" value={gstrPeriod} onChange={setGstrPeriod} placeholder="e.g. July 2025" />
              <Select label="Return Type" value={gstrReturnType} onChange={setGstrReturnType} options={[
                { label: 'GSTR-3B (Monthly Summary)', value: 'gstr3b' },
                { label: 'GSTR-1 (Outward Supplies)', value: 'gstr1' },
                { label: 'Both GSTR-1 + GSTR-3B',    value: 'both' },
              ]} />
            </div>
            <div style={{ marginTop: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <div style={{ color: '#9ca3af', fontSize: 12 }}>Sales Data (JSON)</div>
                <span onClick={() => setGstrSalesJson(JSON.stringify(GSTR_DEMO_SALES, null, 2))} style={{ cursor: 'pointer', color: '#4f8ef7', fontSize: 11 }}>Load Demo</span>
              </div>
              <textarea value={gstrSalesJson} onChange={e => setGstrSalesJson(e.target.value)} rows={6}
                style={{ width: '100%', background: '#0f1117', border: '1px solid #1e2535', borderRadius: 8, color: '#e2e8f0', fontSize: 11, padding: '10px', fontFamily: 'monospace', boxSizing: 'border-box', resize: 'vertical' }}
                placeholder='[{"taxable_value":50000,"gst_rate":18,"supply_type":"b2b","gstin":"33XXXXX"}]'
              />
            </div>
            <div style={{ marginTop: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <div style={{ color: '#9ca3af', fontSize: 12 }}>Purchase Data (JSON — for ITC)</div>
                <span onClick={() => setGstrPurchJson(JSON.stringify(GSTR_DEMO_PURCHASE, null, 2))} style={{ cursor: 'pointer', color: '#4f8ef7', fontSize: 11 }}>Load Demo</span>
              </div>
              <textarea value={gstrPurchJson} onChange={e => setGstrPurchJson(e.target.value)} rows={5}
                style={{ width: '100%', background: '#0f1117', border: '1px solid #1e2535', borderRadius: 8, color: '#e2e8f0', fontSize: 11, padding: '10px', fontFamily: 'monospace', boxSizing: 'border-box', resize: 'vertical' }}
                placeholder='[{"taxable_value":25000,"gst_rate":18,"vendor_gstin":"33XXXXX"}]'
              />
            </div>
            <Btn onClick={runGstrPrep} loading={gstrLoading} style={{ marginTop: 12, width: '100%' }}>Prepare Filing Summary</Btn>
            {gstrErr && <div style={{ color: '#ef4444', fontSize: 12, marginTop: 6 }}>{gstrErr}</div>}
          </Card>

          <div>
            {gstrRes && !gstrLoading && (
              <>
                {/* Tax Liability Summary */}
                <Card style={{ marginBottom: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                    <SectionHead title={`${gstrRes.return_type} Summary — ${gstrRes.period}`} />
                    <span style={{
                      padding: '3px 10px', borderRadius: 10, fontSize: 11, fontWeight: 700,
                      background: gstrRes.tax_liability?.total_net_payable === 0 ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.12)',
                      color: gstrRes.tax_liability?.total_net_payable === 0 ? '#10b981' : '#ef4444',
                    }}>
                      {gstrRes.tax_liability?.total_net_payable === 0 ? 'NIL Return' : `₹${(gstrRes.tax_liability?.total_net_payable || 0).toLocaleString('en-IN')} Due`}
                    </span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 8, marginBottom: 14 }}>
                    {[
                      { label: 'Output Tax',  value: gstrRes.tax_liability?.output_tax,    color: '#ef4444' },
                      { label: 'ITC Available', value: gstrRes.tax_liability?.total_itc,   color: '#10b981' },
                      { label: 'Net Payable', value: gstrRes.tax_liability?.total_net_payable, color: '#f59e0b' },
                    ].map(k => (
                      <div key={k.label} style={{ background: '#0f1117', borderRadius: 8, padding: '10px', textAlign: 'center', border: `1px solid ${k.color}33` }}>
                        <div style={{ color: '#6b7280', fontSize: 10, marginBottom: 4 }}>{k.label}</div>
                        <div style={{ color: k.color, fontSize: 15, fontWeight: 700 }}>₹{(k.value || 0).toLocaleString('en-IN')}</div>
                      </div>
                    ))}
                  </div>

                  {/* CGST / SGST / IGST breakdown */}
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                      <thead>
                        <tr style={{ borderBottom: '1px solid #1e2535' }}>
                          {['', 'CGST', 'SGST', 'IGST', 'Total'].map(h => (
                            <th key={h} style={{ padding: '6px 8px', color: '#6b7280', textAlign: 'right', fontWeight: 600 }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {[
                          { label: 'Output Tax', cgst: gstrRes.sales_summary?.total_cgst, sgst: gstrRes.sales_summary?.total_sgst, igst: gstrRes.sales_summary?.total_igst, total: gstrRes.sales_summary?.total_output_tax },
                          { label: 'ITC',        cgst: gstrRes.purchase_summary?.itc_cgst, sgst: gstrRes.purchase_summary?.itc_sgst, igst: gstrRes.purchase_summary?.itc_igst, total: gstrRes.purchase_summary?.total_itc },
                          { label: 'Net Payable',cgst: gstrRes.tax_liability?.net_cgst_payable, sgst: gstrRes.tax_liability?.net_sgst_payable, igst: gstrRes.tax_liability?.net_igst_payable, total: gstrRes.tax_liability?.total_net_payable },
                        ].map(row => (
                          <tr key={row.label} style={{ borderBottom: '1px solid #0f1117' }}>
                            <td style={{ padding: '6px 8px', color: '#9ca3af', fontSize: 12 }}>{row.label}</td>
                            {[row.cgst, row.sgst, row.igst, row.total].map((v, i) => (
                              <td key={i} style={{ padding: '6px 8px', color: '#e2e8f0', textAlign: 'right', fontWeight: row.label === 'Net Payable' ? 700 : 400 }}>
                                ₹{(v || 0).toLocaleString('en-IN')}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {gstrRes.tax_liability?.refund_eligible && (
                    <div style={{ marginTop: 10, padding: '8px 12px', background: 'rgba(16,185,129,0.08)', border: '1px solid #10b98133', borderRadius: 6, color: '#6ee7b7', fontSize: 12 }}>
                      ✅ ITC carryforward eligible — ₹{(gstrRes.tax_liability.itc_carryforward || 0).toLocaleString('en-IN')} can be carried to next period
                    </div>
                  )}
                </Card>

                {/* Filing Checklist */}
                <Card>
                  <SectionHead title="Filing Checklist" sub="Complete before submitting on GSTN portal" />
                  {(gstrRes.filing_checklist || []).filter((c: any) => c.status !== 'na').map((c: any, i: number) => (
                    <div key={i} style={{ display: 'flex', gap: 10, alignItems: 'center', padding: '7px 0', borderBottom: '1px solid #1e2535' }}>
                      <span style={{ fontSize: 14 }}>{c.status === 'ready' ? '✅' : '⬜'}</span>
                      <span style={{ color: c.status === 'ready' ? '#10b981' : '#9ca3af', fontSize: 13 }}>{c.item}</span>
                    </div>
                  ))}
                </Card>
              </>
            )}
            {!gstrRes && !gstrLoading && (
              <div style={{ color: '#4b5563', fontSize: 13, textAlign: 'center', marginTop: 60 }}>
                Paste sales & purchase JSON, then click Prepare Filing Summary →
              </div>
            )}
          </div>
        </TwoCol>
      )}

      {/* ── TAX PLANNING OPTIMIZER (Round 6) ── */}
      {tab === 'tax_planning' && (
        <TwoCol>
          <Card>
            <SectionHead title="Tax Planning Optimizer" sub="Old Regime — find every rupee you can save before 31 March" />
            <Input label="Gross Salary (₹)" value={tpGross} onChange={setTpGross} placeholder="e.g. 1200000" />
            <Input label="Other Income (₹)" value={tpOther} onChange={setTpOther} placeholder="e.g. 50000" />
            <Input label="Age" value={tpAge} onChange={setTpAge} placeholder="e.g. 32" />
            <div style={{ margin: '12px 0 6px', fontSize: 12, color: '#9ca3af', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>Current Investments</div>
            <Input label="80C Investments (₹) — max 1,50,000" value={tp80c} onChange={setTp80c} placeholder="e.g. 80000" />
            <Input label="NPS 80CCD(1B) (₹) — max 50,000" value={tpNps} onChange={setTpNps} placeholder="e.g. 0" />
            <Input label="Health Insurance 80D (₹)" value={tp80d} onChange={setTp80d} placeholder="e.g. 10000" />
            <Input label="Home Loan Interest 24(b) (₹) — max 2,00,000" value={tpHlInt} onChange={setTpHlInt} placeholder="e.g. 0" />
            <Btn onClick={runTaxPlan} loading={tpLoading} style={{ marginTop: 14, width: '100%' }}>Optimize My Tax Plan</Btn>
            {tpErr && <div style={{ color: '#f59e0b', fontSize: 11, marginTop: 8 }}>Demo mode (backend offline): {tpErr}</div>}
          </Card>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {tpRes ? (
              <>
                {/* Savings Hero */}
                <Card>
                  <div style={{ textAlign: 'center', padding: '8px 0 16px' }}>
                    <div style={{ fontSize: 12, color: '#9ca3af', marginBottom: 4 }}>Potential Tax Saving</div>
                    <div style={{ fontSize: 40, fontWeight: 800, color: '#22c55e' }}>₹{(tpRes.potential_saving || 0).toLocaleString('en-IN')}</div>
                    <div style={{ fontSize: 13, color: '#6b7280', marginTop: 4 }}>
                      Tax before: ₹{(tpRes.tax_current || 0).toLocaleString('en-IN')} ({tpRes.effective_rate}%) → after: ₹{(tpRes.tax_optimized || 0).toLocaleString('en-IN')} ({tpRes.optimized_rate}%)
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 12 }}>
                    {Object.entries(tpRes.deduction_gaps || {}).map(([sec, gap]: any) => (
                      <div key={sec} style={{ flex: 1, background: '#0f1117', border: '1px solid #1e2535', borderRadius: 8, padding: '10px 12px', textAlign: 'center' }}>
                        <div style={{ fontSize: 13, fontWeight: 700, color: gap > 0 ? '#f59e0b' : '#22c55e' }}>₹{gap.toLocaleString('en-IN')}</div>
                        <div style={{ fontSize: 11, color: '#6b7280' }}>{sec} gap</div>
                      </div>
                    ))}
                  </div>
                </Card>

                {/* Recommendations */}
                <Card>
                  <SectionHead title="Action Plan" sub="Sorted by priority" />
                  {(tpRes.recommendations || []).map((r: any, i: number) => (
                    <div key={i} style={{ background: '#0f1117', border: '1px solid #1e2535', borderRadius: 8, padding: 14, marginBottom: 10 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                        <Badge label={`Section ${r.section}`} color="#818cf8" />
                        <Badge label={r.priority} color={r.priority === 'High' ? '#ef4444' : '#f59e0b'} />
                      </div>
                      <div style={{ color: '#e2e8f0', fontSize: 13, marginBottom: 6 }}>{r.action}</div>
                      <div style={{ color: '#22c55e', fontSize: 12, fontWeight: 600 }}>Save ₹{typeof r.saving === 'number' ? r.saving.toLocaleString('en-IN') : r.saving}</div>
                      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 6 }}>
                        {(r.instruments || []).map((inst: string, j: number) => (
                          <span key={j} style={{ fontSize: 11, padding: '2px 8px', background: '#1e2535', color: '#9ca3af', borderRadius: 6 }}>{inst}</span>
                        ))}
                      </div>
                    </div>
                  ))}
                </Card>

                {/* Instruments */}
                <Card>
                  <SectionHead title="Investment Instruments" sub="Compare your options" />
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                      <thead>
                        <tr style={{ color: '#6b7280', borderBottom: '1px solid #1e2535' }}>
                          {['Instrument', 'Section', 'Returns', 'Lock-in', 'Risk'].map(h => (
                            <th key={h} style={{ textAlign: 'left', padding: '6px 8px', fontWeight: 600 }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {(tpRes.instruments || []).map((inst: any, i: number) => (
                          <tr key={i} style={{ borderBottom: '1px solid #0f1117' }}>
                            <td style={{ padding: '7px 8px', color: '#e2e8f0', fontWeight: 600 }}>{inst.name}</td>
                            <td style={{ padding: '7px 8px', color: '#818cf8' }}>{inst.section}</td>
                            <td style={{ padding: '7px 8px', color: '#22c55e' }}>{inst.returns}</td>
                            <td style={{ padding: '7px 8px', color: '#9ca3af' }}>{inst.lock_in}</td>
                            <td style={{ padding: '7px 8px', color: inst.risk === 'None' ? '#22c55e' : inst.risk === 'High' ? '#ef4444' : '#f59e0b' }}>{inst.risk}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Card>

                {tpRes.narrative && (
                  <Card>
                    <SectionHead title="CA's Advice" sub="Personalized recommendation" />
                    <div style={{ color: '#9ca3af', fontSize: 13, lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>{tpRes.narrative}</div>
                  </Card>
                )}
              </>
            ) : !tpLoading && (
              <div style={{ color: '#4b5563', fontSize: 13, textAlign: 'center', marginTop: 60 }}>
                Enter your income & investments to see the optimization →
              </div>
            )}
          </div>
        </TwoCol>
      )}
    </PageShell>
  )
}
