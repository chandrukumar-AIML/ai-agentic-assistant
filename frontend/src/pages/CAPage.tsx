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

  // ── Business Valuation Calculator (Round 9) ──
  const BIZ_INDUSTRIES = [
    { label: 'Technology', value: 'technology' }, { label: 'SaaS / Cloud', value: 'saas' },
    { label: 'E-Commerce', value: 'ecommerce' }, { label: 'Manufacturing', value: 'manufacturing' },
    { label: 'Retail', value: 'retail' }, { label: 'Healthcare', value: 'healthcare' },
    { label: 'Fintech', value: 'fintech' }, { label: 'Education', value: 'education' },
    { label: 'Real Estate', value: 'real_estate' }, { label: 'Consulting', value: 'consulting' },
  ]
  const BIZ_STAGES = [
    { label: 'Pre-Revenue / Idea', value: 'pre_revenue' },
    { label: 'Early Stage (< 1 Cr revenue)', value: 'early' },
    { label: 'Growth Stage (1–50 Cr)', value: 'growth' },
    { label: 'Mature / Profitable', value: 'mature' },
  ]
  const [bvRevenue, setBvRevenue]       = useState('5000000')
  // P&L Statement Builder (Round 12)
  const [plCompany, setPlCompany]   = useState('Acme Pvt Ltd')
  const [plPeriod, setPlPeriod]     = useState('FY 2024-25')
  const [plIndustry, setPlIndustry] = useState('technology')
  const [plTaxRate, setPlTaxRate]   = useState('25')
  const [plPrevRev, setPlPrevRev]   = useState('4500000')
  const [plPrevProfit, setPlPrevProfit] = useState('400000')
  const [plRevJson, setPlRevJson]   = useState('')
  const [plCogJson, setPlCogJson]   = useState('')
  const [plOpexJson, setPlOpexJson] = useState('')
  const [plRes, setPlRes]           = useState<any>(null)
  const [plLoading, setPlLoading]   = useState(false)
  const [plErr, setPlErr]           = useState('')
  // MSME Loan Eligibility (Round 13)
  const [lnCompany, setLnCompany]   = useState('')
  const [lnBizType, setLnBizType]   = useState('service')
  const [lnTurnover, setLnTurnover] = useState('')
  const [lnPlant, setLnPlant]       = useState('')
  const [lnYears, setLnYears]       = useState('3')
  const [lnPurpose, setLnPurpose]   = useState('working_capital')
  const [lnAmount, setLnAmount]     = useState('')
  const [lnExisting, setLnExisting] = useState('0')
  const [lnRevenue, setLnRevenue]   = useState('')
  const [lnGst, setLnGst]           = useState(true)
  const [lnRes, setLnRes]           = useState<any>(null)
  const [lnLoading, setLnLoading]   = useState(false)
  const [lnErr, setLnErr]           = useState('')
  // TDS Compliance Tracker (Round 14)
  const [tdsCompany, setTdsCompany] = useState('')
  const [tdsMonth, setTdsMonth]     = useState(new Date().getMonth() + 1)
  const [tdsYear, setTdsYear]       = useState(new Date().getFullYear())
  const [tdsRes, setTdsRes]         = useState<any>(null)
  const [tdsLoading, setTdsLoading] = useState(false)
  const [tdsErr, setTdsErr]         = useState('')
  const [tdsActiveSection, setTdsActiveSection] = useState<string|null>(null)
  // Client Proposal Generator (Round 15)
  const [propFirm, setPropFirm]         = useState('')
  const [propClient, setPropClient]     = useState('')
  const [propIndustry, setPropIndustry] = useState('')
  const [propTurnover, setPropTurnover] = useState('')
  const [propCa, setPropCa]             = useState('')
  const [propStart, setPropStart]       = useState('')
  const [propFeeType, setPropFeeType]   = useState('monthly_retainer')
  const [propServices, setPropServices] = useState<string[]>(['bookkeeping','gst_filing','tds_compliance','income_tax'])
  const [propRes, setPropRes]           = useState<any>(null)
  const [propLoading, setPropLoading]   = useState(false)
  const [propErr, setPropErr]           = useState('')
  const [propView, setPropView]         = useState<'proposal'|'letter'|'checklist'>('proposal')
  const toggleService = (s: string) => setPropServices(prev => prev.includes(s) ? prev.filter(x => x !== s) : [...prev, s])
  const runProposal = async () => {
    setPropLoading(true); setPropErr(''); setPropRes(null)
    try {
      setPropRes(await caAction('client_proposal', {
        firm_name: propFirm, client_name: propClient, client_industry: propIndustry,
        client_turnover: propTurnover, ca_name: propCa, engagement_start: propStart,
        fee_type: propFeeType, services: propServices,
      }))
    } catch (e: any) { setPropErr(e.message) }
    finally { setPropLoading(false) }
  }
  const runTds = async () => {
    setTdsLoading(true); setTdsErr(''); setTdsRes(null)
    try {
      setTdsRes(await caAction('tds_compliance_tracker', {
        company_name: tdsCompany, month: tdsMonth, year: tdsYear,
        deductions: [], pan_verified: true,
      }))
    } catch (e: any) { setTdsErr(e.message) }
    finally { setTdsLoading(false) }
  }
  const runLoan = async () => {
    setLnLoading(true); setLnErr(''); setLnRes(null)
    try {
      setLnRes(await caAction('msme_loan_eligibility', {
        company_name: lnCompany, business_type: lnBizType,
        annual_turnover: parseFloat(lnTurnover) || 0,
        plant_machinery_value: parseFloat(lnPlant) || 0,
        years_in_business: parseInt(lnYears) || 1,
        loan_purpose: lnPurpose,
        loan_amount_requested: parseFloat(lnAmount) || 0,
        existing_loans: parseFloat(lnExisting) || 0,
        monthly_revenue: parseFloat(lnRevenue) || 0,
        gst_registered: lnGst,
      }))
    } catch (e: any) { setLnErr(e.message) }
    finally { setLnLoading(false) }
  }
  const runPL = async () => {
    setPlLoading(true); setPlErr(''); setPlRes(null)
    let rev: any[] = [], cogs: any[] = [], opex: any[] = []
    try {
      if (plRevJson.trim()) rev = JSON.parse(plRevJson)
      if (plCogJson.trim()) cogs = JSON.parse(plCogJson)
      if (plOpexJson.trim()) opex = JSON.parse(plOpexJson)
    } catch { setPlErr('Invalid JSON in one of the fields'); setPlLoading(false); return }
    try {
      setPlRes(await caAction('pl_statement', {
        company_name: plCompany, period: plPeriod, industry: plIndustry,
        tax_rate: parseFloat(plTaxRate) || 25, revenue_items: rev,
        cogs_items: cogs, opex_items: opex, other_income: 0,
        prev_period_revenue: parseFloat(plPrevRev) || 0,
        prev_period_profit: parseFloat(plPrevProfit) || 0,
      }, language))
    } catch (e: any) { setPlErr(e.message) }
    finally { setPlLoading(false) }
  }

  // Overdue Invoice Collector (Round 11)
  const [odCompany, setOdCompany]       = useState('Acme Pvt Ltd')
  const [odContact, setOdContact]       = useState('')
  const [odSender, setOdSender]         = useState('')
  const [odLateFee, setOdLateFee]       = useState('2')
  const [odInvoicesJson, setOdInvoicesJson] = useState('')
  const [odRes, setOdRes]               = useState<any>(null)
  const [odLoading, setOdLoading]       = useState(false)
  const [odErr, setOdErr]               = useState('')
  const [odSelected, setOdSelected]     = useState<number | null>(null)
  const runOverdueCollector = async () => {
    setOdLoading(true); setOdErr(''); setOdRes(null)
    let invoices: any[] = []
    try { if (odInvoicesJson.trim()) invoices = JSON.parse(odInvoicesJson) } catch { setOdErr('Invalid JSON in invoice list'); setOdLoading(false); return }
    try {
      setOdRes(await caAction('overdue_collector', {
        company_name: odCompany, contact_name: odContact, sender_name: odSender,
        late_fee_pct: parseFloat(odLateFee) || 2, invoices,
      }, language))
    } catch (e: any) { setOdErr(e.message) }
    finally { setOdLoading(false) }
  }

  // Cash Flow Forecaster (Round 10)
  const [cfCompany, setCfCompany]       = useState('Acme Pvt Ltd')
  const [cfRevenue, setCfRevenue]       = useState('500000')
  const [cfGrowth, setCfGrowth]         = useState('5')
  const [cfFixed, setCfFixed]           = useState('200000')
  const [cfVarPct, setCfVarPct]         = useState('25')
  const [cfOpenCash, setCfOpenCash]     = useState('1000000')
  const [cfIndustry, setCfIndustry]     = useState('technology')
  const [cfRes, setCfRes]               = useState<any>(null)
  const [cfLoading, setCfLoading]       = useState(false)
  const [cfErr, setCfErr]               = useState('')
  const runCashFlow = async () => {
    setCfLoading(true); setCfErr(''); setCfRes(null)
    try {
      setCfRes(await caAction('cash_flow_forecast', {
        company_name: cfCompany, monthly_revenue: parseFloat(cfRevenue) || 0,
        revenue_growth: parseFloat(cfGrowth) || 5, fixed_expenses: parseFloat(cfFixed) || 0,
        variable_expense_pct: parseFloat(cfVarPct) || 25, opening_cash: parseFloat(cfOpenCash) || 0,
        one_time_inflows: [], one_time_outflows: [], industry: cfIndustry,
      }, language))
    } catch (e: any) { setCfErr(e.message) }
    finally { setCfLoading(false) }
  }

  const [bvEbitda, setBvEbitda]         = useState('1000000')
  const [bvNetProfit, setBvNetProfit]   = useState('700000')
  const [bvAssets, setBvAssets]         = useState('2000000')
  const [bvLiab, setBvLiab]            = useState('500000')
  const [bvIndustry, setBvIndustry]     = useState('technology')
  const [bvStage, setBvStage]           = useState('growth')
  const [bvGrowth, setBvGrowth]         = useState('35')
  const [bvRes, setBvRes]               = useState<any>(null)
  const [bvLoading, setBvLoading]       = useState(false)
  const [bvErr, setBvErr]               = useState('')

  const runValuation = async () => {
    setBvLoading(true); setBvErr(''); setBvRes(null)
    try {
      setBvRes(await caAction('business_valuation', {
        revenue: parseFloat(bvRevenue) || 0, ebitda: parseFloat(bvEbitda) || 0,
        net_profit: parseFloat(bvNetProfit) || 0, assets: parseFloat(bvAssets) || 0,
        liabilities: parseFloat(bvLiab) || 0, industry: bvIndustry,
        stage: bvStage, growth_rate: parseFloat(bvGrowth) || 20,
      }, language))
    } catch (e: any) { setBvErr(e.message) }
    setBvLoading(false)
  }

  // ── GST Notice Reply Drafter (Round 8) ──
  const NOTICE_TYPES = [
    { label: 'GST Scrutiny Notice (Sec 61)', value: 'gst_scrutiny' },
    { label: 'GST Demand / SCN (Sec 73/74)', value: 'gst_demand' },
    { label: 'ITC Mismatch (GSTR-2B vs 3B)', value: 'itc_mismatch' },
    { label: 'E-Way Bill Non-Compliance', value: 'ewaybill' },
    { label: 'Annual Return GSTR-9 Notice', value: 'annual_return' },
    { label: 'TDS Demand Notice (Sec 200A)', value: 'tds_demand' },
  ]
  const [ntType, setNtType]           = useState('itc_mismatch')
  const [ntRef, setNtRef]             = useState('')
  const [ntGstin, setNtGstin]         = useState('')
  const [ntName, setNtName]           = useState('')
  const [ntDetails, setNtDetails]     = useState('')
  const [ntPoints, setNtPoints]       = useState('')
  const [ntRes, setNtRes]             = useState<any>(null)
  const [ntLoading, setNtLoading]     = useState(false)
  const [ntErr, setNtErr]             = useState('')

  const runNoticeReply = async () => {
    setNtLoading(true); setNtErr(''); setNtRes(null)
    try {
      setNtRes(await caAction('gst_notice_reply', {
        notice_type: ntType, notice_ref: ntRef, gstin: ntGstin,
        taxpayer_name: ntName, notice_details: ntDetails, reply_points: ntPoints,
      }, language))
    } catch (e: any) { setNtErr(e.message) }
    setNtLoading(false)
  }

  // ── Payroll & Salary Processor (Round 7) ──
  const DEMO_EMPLOYEES = [
    { name: 'Arjun Kumar', emp_id: 'E001', designation: 'Software Engineer', gross_salary: 85000, pf_applicable: true, esi_applicable: false, age: 28, state: 'karnataka', lop_days: 0 },
    { name: 'Priya Sharma', emp_id: 'E002', designation: 'Marketing Manager', gross_salary: 55000, pf_applicable: true, esi_applicable: true, age: 32, state: 'karnataka', lop_days: 1 },
    { name: 'Ravi Patel', emp_id: 'E003', designation: 'Support Executive', gross_salary: 22000, pf_applicable: true, esi_applicable: true, age: 25, state: 'maharashtra', lop_days: 0 },
  ]
  const [prCompany, setPrCompany] = useState('')
  const [prMonth, setPrMonth]     = useState('January 2025')
  const [prJson, setPrJson]       = useState(JSON.stringify(DEMO_EMPLOYEES, null, 2))
  const [prRes, setPrRes]         = useState<any>(null)
  const [prLoading, setPrLoading] = useState(false)
  const [prErr, setPrErr]         = useState('')

  const runPayroll = async () => {
    setPrLoading(true); setPrErr(''); setPrRes(null)
    try {
      let employees: any[]
      try { employees = JSON.parse(prJson) } catch { throw new Error('Invalid JSON') }
      setPrRes(await caAction('payroll', { employees, company_name: prCompany, month: prMonth }, language))
    } catch (e: any) {
      setPrErr(e.message)
      // demo fallback
      setPrRes({
        action: 'payroll', company_name: prCompany || 'Demo Company', month: prMonth,
        employee_count: 3,
        payslips: [
          { name: 'Arjun Kumar', emp_id: 'E001', designation: 'Software Engineer', gross_actual: 85000, pf_employee: 5400, esi_employee: 0, professional_tax: 200, tds: 4200, lop_deduction: 0, net_salary: 75200, ctc_monthly: 91600 },
          { name: 'Priya Sharma', emp_id: 'E002', designation: 'Marketing Manager', gross_actual: 52885, pf_employee: 3300, esi_employee: 397, professional_tax: 200, tds: 800, lop_deduction: 2115, net_salary: 48188, ctc_monthly: 58418 },
          { name: 'Ravi Patel', emp_id: 'E003', designation: 'Support Executive', gross_actual: 22000, pf_employee: 1320, esi_employee: 165, professional_tax: 175, tds: 0, lop_deduction: 0, net_salary: 20340, ctc_monthly: 23941 },
        ],
        summary: { total_gross: 159885, total_net: 143728, total_pf_employee: 10020, total_pf_employer: 10020, total_esi_employee: 562, total_esi_employer: 3960, total_tds: 5000, total_pt: 575, employer_liability: 173865 },
        compliance_reminders: ['PF challan due: 15th of next month via EPFO unified portal', 'ESI challan due: 15th of next month via ESIC portal', 'TDS (Form 24Q) due quarterly'],
      })
    }
    setPrLoading(false)
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
          { id: 'payroll',           label: 'Payroll Processor',       icon: '💰' },
          { id: 'notice_reply',      label: 'GST Notice Reply',        icon: '📨' },
          { id: 'valuation',         label: 'Business Valuation',      icon: '🏦' },
          { id: 'cashflow',          label: 'Cash Flow Forecast',       icon: '💰' },
          { id: 'overdue',           label: 'Overdue Collector',         icon: '📬' },
          { id: 'pl',                label: 'P&L Statement',              icon: '📊' },
          { id: 'loan',              label: 'MSME Loan Eligibility',      icon: '🏦' },
          { id: 'tds',               label: 'TDS Compliance Tracker',     icon: '📅' },
          { id: 'proposal',          label: 'Client Proposal',            icon: '📋' },
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
      {/* ── BUSINESS VALUATION (Round 9) ── */}
      {tab === 'valuation' && (
        <TwoCol>
          <Card>
            <SectionHead title="Business Valuation Calculator" sub="PE · EBITDA · Revenue Multiple — for fundraising & M&A" />
            <Select label="Industry" value={bvIndustry} onChange={setBvIndustry} options={BIZ_INDUSTRIES} />
            <Select label="Business Stage" value={bvStage} onChange={setBvStage} options={BIZ_STAGES} />
            <Input label="Annual Revenue (₹)" value={bvRevenue} onChange={setBvRevenue} placeholder="e.g. 5000000" />
            <Input label="EBITDA (₹)" value={bvEbitda} onChange={setBvEbitda} placeholder="e.g. 1000000" />
            <Input label="Net Profit / PAT (₹)" value={bvNetProfit} onChange={setBvNetProfit} placeholder="e.g. 700000" />
            <Input label="Total Assets (₹)" value={bvAssets} onChange={setBvAssets} placeholder="e.g. 2000000" />
            <Input label="Total Liabilities (₹)" value={bvLiab} onChange={setBvLiab} placeholder="e.g. 500000" />
            <Input label="Revenue Growth Rate (%)" value={bvGrowth} onChange={setBvGrowth} placeholder="e.g. 35" />
            <Btn onClick={runValuation} loading={bvLoading} style={{ marginTop: 14, width: '100%' }}>Calculate Valuation</Btn>
            {bvErr && <div style={{ color: '#f59e0b', fontSize: 11, marginTop: 8 }}>Demo mode: {bvErr}</div>}
          </Card>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {bvRes ? (
              <>
                {/* Hero valuation */}
                <Card>
                  <div style={{ textAlign: 'center', padding: '8px 0 16px' }}>
                    <div style={{ fontSize: 12, color: '#9ca3af', marginBottom: 4 }}>Blended Valuation</div>
                    <div style={{ fontSize: 44, fontWeight: 800, color: '#22c55e', fontVariantNumeric: 'tabular-nums' }}>{bvRes.formatted?.blended}</div>
                    <div style={{ fontSize: 13, color: '#6b7280', marginTop: 4 }}>Range: {bvRes.formatted?.low} – {bvRes.formatted?.high}</div>
                    <div style={{ display: 'flex', gap: 10, justifyContent: 'center', marginTop: 10 }}>
                      <Badge label={`${bvRes.industry}`} color="#818cf8" />
                      <Badge label={`${bvRes.stage}`} color="#6b7280" />
                      <Badge label={`${bvRes.growth_rate}% growth`} color="#22c55e" />
                    </div>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 8 }}>
                    {[
                      { label: 'EBITDA Margin', val: `${bvRes.financials?.ebitda_margin}%` },
                      { label: 'PAT Margin', val: `${bvRes.financials?.pat_margin}%` },
                      { label: 'Growth Premium', val: `${bvRes.growth_premium}x` },
                    ].map(k => (
                      <div key={k.label} style={{ background: '#0f1117', border: '1px solid #1e2535', borderRadius: 8, padding: '8px 10px', textAlign: 'center' }}>
                        <div style={{ fontSize: 15, fontWeight: 700, color: '#e2e8f0' }}>{k.val}</div>
                        <div style={{ fontSize: 11, color: '#6b7280' }}>{k.label}</div>
                      </div>
                    ))}
                  </div>
                </Card>

                {/* Method breakdown */}
                <Card>
                  <SectionHead title="Valuation by Method" sub="Each method gives a different lens" />
                  {Object.values(bvRes.valuations || {}).map((v: any, i: number) => (
                    <div key={i} style={{ background: '#0f1117', border: '1px solid #1e2535', borderRadius: 8, padding: 12, marginBottom: 8 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                        <span style={{ fontWeight: 600, color: '#e2e8f0', fontSize: 13 }}>{v.method}</span>
                        <span style={{ color: '#22c55e', fontWeight: 700, fontSize: 14, fontVariantNumeric: 'tabular-nums' }}>
                          ₹{(v.midpoint / 10000000).toFixed(2)} Cr
                        </span>
                      </div>
                      <div style={{ fontSize: 11, color: '#818cf8', marginBottom: 4 }}>{v.multiple_used}</div>
                      <div style={{ height: 4, background: '#1e2535', borderRadius: 2, marginBottom: 6 }}>
                        <div style={{ height: '100%', width: `${Math.min((v.midpoint / (bvRes.range?.high || 1)) * 100, 100)}%`, background: '#22c55e', borderRadius: 2 }} />
                      </div>
                      <div style={{ fontSize: 11, color: '#4b5563' }}>{v.note}</div>
                    </div>
                  ))}
                </Card>

                {/* Recommendations */}
                <Card>
                  <SectionHead title="CA's Recommendations" sub="For fundraising or M&A discussions" />
                  {(bvRes.recommendations || []).map((r: string, i: number) => (
                    <div key={i} style={{ display: 'flex', gap: 8, padding: '7px 0', borderBottom: '1px solid #0f1117', fontSize: 12, color: '#9ca3af' }}>
                      <span style={{ color: '#818cf8', flexShrink: 0 }}>→</span>{r}
                    </div>
                  ))}
                </Card>
              </>
            ) : !bvLoading && (
              <div style={{ color: '#4b5563', fontSize: 13, textAlign: 'center', marginTop: 60 }}>
                Demo data is pre-filled — click Calculate Valuation to see results →
              </div>
            )}
          </div>
        </TwoCol>
      )}

      {/* ── GST NOTICE REPLY (Round 8) ── */}
      {tab === 'notice_reply' && (
        <TwoCol>
          <Card>
            <SectionHead title="GST Notice Reply Drafter" sub="AI drafts a legally sound, section-referenced reply letter" />
            <Select label="Notice Type" value={ntType} onChange={setNtType} options={NOTICE_TYPES} />
            <Input label="Notice Reference Number" value={ntRef} onChange={setNtRef} placeholder="e.g. ACME/GST/2024/001" />
            <Input label="GSTIN" value={ntGstin} onChange={setNtGstin} placeholder="e.g. 29AABCU9603R1ZX" />
            <Input label="Taxpayer / Business Name" value={ntName} onChange={setNtName} placeholder="e.g. Acme Technologies Pvt Ltd" />
            <div style={{ marginBottom: 10 }}>
              <div style={{ fontSize: 12, color: '#9ca3af', marginBottom: 4 }}>Notice Details (what the officer observed)</div>
              <textarea value={ntDetails} onChange={e => setNtDetails(e.target.value)} rows={3} placeholder="e.g. ITC claimed in GSTR-3B is higher than GSTR-2B by Rs.45,000 for Q3 FY24"
                style={{ width: '100%', background: '#0f1117', color: '#e2e8f0', border: '1px solid #1e2535', borderRadius: 8, padding: 10, fontSize: 13, resize: 'vertical', boxSizing: 'border-box' }} />
            </div>
            <div style={{ marginBottom: 10 }}>
              <div style={{ fontSize: 12, color: '#9ca3af', marginBottom: 4 }}>Your Defence / Reply Points</div>
              <textarea value={ntPoints} onChange={e => setNtPoints(e.target.value)} rows={3} placeholder="e.g. Difference due to timing — supplier filed GSTR-1 late. ITC is valid and supplier is registered."
                style={{ width: '100%', background: '#0f1117', color: '#e2e8f0', border: '1px solid #1e2535', borderRadius: 8, padding: 10, fontSize: 13, resize: 'vertical', boxSizing: 'border-box' }} />
            </div>
            <Btn onClick={runNoticeReply} loading={ntLoading} style={{ marginTop: 4, width: '100%' }}>Draft Reply Letter</Btn>
            {ntErr && <div style={{ color: '#f59e0b', fontSize: 11, marginTop: 8 }}>Demo mode: {ntErr}</div>}
          </Card>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {ntRes ? (
              <>
                <Card>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                    <SectionHead title="Reply Letter" sub={ntRes.subject} />
                    <span onClick={() => navigator.clipboard?.writeText(ntRes.full_letter || '')}
                      style={{ cursor: 'pointer', fontSize: 11, padding: '4px 12px', background: '#374151', color: '#fff', borderRadius: 6, flexShrink: 0 }}>Copy Letter</span>
                  </div>
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
                    <Badge label={ntRes.section} color="#818cf8" />
                    <Badge label={`${ntRes.word_count} words`} color="#6b7280" />
                  </div>
                  <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 6 }}>Legal References:</div>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 14 }}>
                    {(ntRes.legal_references || []).map((r: string, i: number) => (
                      <span key={i} style={{ fontSize: 11, padding: '2px 8px', background: '#1e2535', color: '#818cf8', borderRadius: 6 }}>{r}</span>
                    ))}
                  </div>
                  <pre style={{ color: '#e2e8f0', fontSize: 12, whiteSpace: 'pre-wrap', background: '#0f1117', border: '1px solid #1e2535', borderRadius: 8, padding: 14, lineHeight: 1.8, fontFamily: 'inherit', margin: 0, maxHeight: 400, overflowY: 'auto' }}>{ntRes.full_letter}</pre>
                </Card>
                <Card>
                  <SectionHead title="Submission Tips" sub="Before you send this reply" />
                  {(ntRes.tips || []).map((t: string, i: number) => (
                    <div key={i} style={{ display: 'flex', gap: 8, padding: '7px 0', borderBottom: '1px solid #0f1117', fontSize: 12, color: '#9ca3af' }}>
                      <span style={{ color: '#f59e0b', flexShrink: 0 }}>📌</span>{t}
                    </div>
                  ))}
                </Card>
              </>
            ) : !ntLoading && (
              <div style={{ color: '#4b5563', fontSize: 13, textAlign: 'center', marginTop: 60 }}>
                Select notice type, fill in your details, and click Draft Reply Letter →
              </div>
            )}
          </div>
        </TwoCol>
      )}

      {/* ── PAYROLL PROCESSOR (Round 7) ── */}
      {tab === 'payroll' && (
        <TwoCol>
          <Card>
            <SectionHead title="Payroll & Salary Processor" sub="PF · ESI · PT · TDS — India-compliant payslips" />
            <Input label="Company Name" value={prCompany} onChange={setPrCompany} placeholder="e.g. Acme Pvt Ltd" />
            <Input label="Month" value={prMonth} onChange={setPrMonth} placeholder="e.g. January 2025" />
            <div style={{ marginBottom: 6, fontSize: 12, color: '#9ca3af' }}>Employees JSON</div>
            <textarea value={prJson} onChange={e => setPrJson(e.target.value)} rows={12}
              style={{ width: '100%', background: '#0f1117', color: '#e2e8f0', border: '1px solid #1e2535', borderRadius: 8, padding: 10, fontSize: 11, fontFamily: 'monospace', resize: 'vertical', boxSizing: 'border-box' }} />
            <Btn onClick={runPayroll} loading={prLoading} style={{ marginTop: 12, width: '100%' }}>Process Payroll</Btn>
            {prErr && <div style={{ color: '#f59e0b', fontSize: 11, marginTop: 8 }}>Demo mode: {prErr}</div>}
          </Card>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {prRes ? (
              <>
                {/* Summary KPIs */}
                <Card>
                  <SectionHead title={`${prRes.company_name || 'Company'} — ${prRes.month}`} sub={`${prRes.employee_count} employees processed`} />
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 10 }}>
                    {[
                      { label: 'Total Gross', val: `₹${(prRes.summary?.total_gross || 0).toLocaleString('en-IN')}`, color: '#e2e8f0' },
                      { label: 'Total Net Payout', val: `₹${(prRes.summary?.total_net || 0).toLocaleString('en-IN')}`, color: '#22c55e' },
                      { label: 'PF (Employer)', val: `₹${(prRes.summary?.total_pf_employer || 0).toLocaleString('en-IN')}`, color: '#818cf8' },
                      { label: 'Total TDS', val: `₹${(prRes.summary?.total_tds || 0).toLocaleString('en-IN')}`, color: '#f59e0b' },
                      { label: 'ESI (Employer)', val: `₹${(prRes.summary?.total_esi_employer || 0).toLocaleString('en-IN')}`, color: '#818cf8' },
                      { label: 'Total CTC Liability', val: `₹${(prRes.summary?.employer_liability || 0).toLocaleString('en-IN')}`, color: '#ef4444' },
                    ].map(k => (
                      <div key={k.label} style={{ background: '#0f1117', border: '1px solid #1e2535', borderRadius: 8, padding: '10px 12px' }}>
                        <div style={{ fontSize: 15, fontWeight: 700, color: k.color, fontVariantNumeric: 'tabular-nums' }}>{k.val}</div>
                        <div style={{ fontSize: 11, color: '#6b7280' }}>{k.label}</div>
                      </div>
                    ))}
                  </div>
                </Card>

                {/* Payslips table */}
                <Card>
                  <SectionHead title="Individual Payslips" sub="Click any row for detail" />
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                      <thead>
                        <tr style={{ color: '#6b7280', borderBottom: '1px solid #1e2535' }}>
                          {['Employee', 'Gross', 'PF', 'ESI', 'PT', 'TDS', 'Net'].map(h => (
                            <th key={h} style={{ textAlign: 'left', padding: '6px 8px', fontWeight: 600 }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {(prRes.payslips || []).map((p: any, i: number) => (
                          <tr key={i} style={{ borderBottom: '1px solid #0f1117' }}>
                            <td style={{ padding: '7px 8px' }}>
                              <div style={{ color: '#e2e8f0', fontWeight: 600 }}>{p.name}</div>
                              <div style={{ color: '#6b7280', fontSize: 11 }}>{p.designation}</div>
                            </td>
                            <td style={{ padding: '7px 8px', color: '#9ca3af', fontVariantNumeric: 'tabular-nums' }}>₹{(p.gross_actual || 0).toLocaleString('en-IN')}</td>
                            <td style={{ padding: '7px 8px', color: '#818cf8', fontVariantNumeric: 'tabular-nums' }}>₹{(p.pf_employee || 0).toLocaleString('en-IN')}</td>
                            <td style={{ padding: '7px 8px', color: '#818cf8', fontVariantNumeric: 'tabular-nums' }}>₹{(p.esi_employee || 0).toLocaleString('en-IN')}</td>
                            <td style={{ padding: '7px 8px', color: '#9ca3af', fontVariantNumeric: 'tabular-nums' }}>₹{(p.professional_tax || 0).toLocaleString('en-IN')}</td>
                            <td style={{ padding: '7px 8px', color: '#f59e0b', fontVariantNumeric: 'tabular-nums' }}>₹{(p.tds || 0).toLocaleString('en-IN')}</td>
                            <td style={{ padding: '7px 8px', color: '#22c55e', fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>₹{(p.net_salary || 0).toLocaleString('en-IN')}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Card>

                {/* Compliance */}
                <Card>
                  <SectionHead title="Compliance Reminders" sub="Statutory due dates" />
                  {(prRes.compliance_reminders || []).map((r: string, i: number) => (
                    <div key={i} style={{ display: 'flex', gap: 8, padding: '7px 0', borderBottom: '1px solid #0f1117', fontSize: 12, color: '#9ca3af' }}>
                      <span style={{ color: '#f59e0b' }}>📋</span>{r}
                    </div>
                  ))}
                </Card>
              </>
            ) : !prLoading && (
              <div style={{ color: '#4b5563', fontSize: 13, textAlign: 'center', marginTop: 60 }}>
                Demo data is pre-loaded — click Process Payroll to see results →
              </div>
            )}
          </div>
        </TwoCol>
      )}

      {/* ── CASH FLOW FORECASTER (Round 10) ── */}
      {tab === 'cashflow' && (
        <TwoCol>
          <Card>
            <SectionHead title="💰 12-Month Cash Flow Forecast" sub="Rolling projection with burn rate, runway & seasonality" />
            <Input label="Company Name" value={cfCompany} onChange={setCfCompany} placeholder="e.g. Acme Pvt Ltd" />
            <Select label="Industry (Seasonality)" value={cfIndustry} onChange={setCfIndustry} options={[
              { label: 'Technology / SaaS', value: 'technology' },
              { label: 'Retail', value: 'retail' },
              { label: 'E-Commerce', value: 'ecommerce' },
              { label: 'Education', value: 'education' },
              { label: 'Agriculture', value: 'agriculture' },
              { label: 'Hospitality', value: 'hospitality' },
              { label: 'Manufacturing', value: 'manufacturing' },
              { label: 'General', value: 'general' },
            ]} />
            <Input label="Monthly Revenue (₹)" value={cfRevenue} onChange={setCfRevenue} placeholder="e.g. 500000" />
            <Input label="Monthly Revenue Growth (%)" value={cfGrowth} onChange={setCfGrowth} placeholder="e.g. 5" />
            <Input label="Fixed Expenses / Month (₹)" value={cfFixed} onChange={setCfFixed} placeholder="e.g. 200000 (rent, salaries, subscriptions)" />
            <Input label="Variable Expenses (% of Revenue)" value={cfVarPct} onChange={setCfVarPct} placeholder="e.g. 25" />
            <Input label="Opening Cash Balance (₹)" value={cfOpenCash} onChange={setCfOpenCash} placeholder="e.g. 1000000" />
            <Btn onClick={runCashFlow} loading={cfLoading} style={{ marginTop: 14, width: '100%' }}>Generate 12-Month Forecast</Btn>
            {cfErr && <div style={{ color: '#ef4444', fontSize: 12, marginTop: 8 }}>{cfErr}</div>}
          </Card>
          <div>
            {cfRes ? (() => {
              const r = cfRes
              const maxVal = Math.max(...(r.months || []).map((m: any) => m.closing_cash), 1)
              return (
                <>
                  {/* KPI Hero */}
                  <Card style={{ marginBottom: 12 }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, marginBottom: 12 }}>
                      {[
                        { label: 'Annual Revenue', val: `₹${((r.annual_revenue || 0) / 100000).toFixed(1)}L`, color: '#22c55e' },
                        { label: 'Annual Profit', val: `₹${((r.annual_profit || 0) / 100000).toFixed(1)}L`, color: (r.annual_profit || 0) >= 0 ? '#22c55e' : '#ef4444' },
                        { label: 'Cash Runway', val: `${r.runway_months}m`, color: r.runway_months >= 12 ? '#22c55e' : r.runway_months >= 6 ? '#f59e0b' : '#ef4444' },
                      ].map(k => (
                        <div key={k.label} style={{ background: '#0f1117', borderRadius: 8, padding: '10px 12px', textAlign: 'center' }}>
                          <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 4 }}>{k.label}</div>
                          <div style={{ fontSize: 20, fontWeight: 800, color: k.color, fontVariantNumeric: 'tabular-nums' }}>{k.val}</div>
                        </div>
                      ))}
                    </div>
                    <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                      <Badge label={`Burn: ₹${((r.avg_monthly_burn || 0) / 1000).toFixed(0)}K/mo`} color="#f59e0b" />
                      <Badge label={`Peak: ₹${((r.highest_cash || 0) / 100000).toFixed(1)}L in ${r.highest_month}`} color="#22c55e" />
                      {r.deficit_months > 0 && <Badge label={`⚠️ ${r.deficit_months} deficit month(s)`} color="#ef4444" />}
                    </div>
                  </Card>

                  {/* Monthly Table */}
                  <Card style={{ marginBottom: 12 }}>
                    <SectionHead title="Monthly Breakdown" sub="Net cashflow and closing balance per month" />
                    <div style={{ overflowX: 'auto' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                        <thead>
                          <tr style={{ borderBottom: '1px solid #1e2535' }}>
                            {['Month', 'Revenue', 'Expenses', 'Net', 'Closing Cash', 'Status'].map(h => (
                              <th key={h} style={{ padding: '6px 8px', textAlign: 'right', color: '#6b7280', fontWeight: 600, fontSize: 11 }}>{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {(r.months || []).map((m: any) => (
                            <tr key={m.month} style={{ borderBottom: '1px solid #1e2535' }}>
                              <td style={{ padding: '6px 8px', color: '#e2e8f0', fontWeight: 600 }}>{m.month}</td>
                              <td style={{ padding: '6px 8px', textAlign: 'right', color: '#22c55e', fontVariantNumeric: 'tabular-nums' }}>₹{((m.total_inflow || 0) / 1000).toFixed(0)}K</td>
                              <td style={{ padding: '6px 8px', textAlign: 'right', color: '#ef4444', fontVariantNumeric: 'tabular-nums' }}>₹{((m.total_outflow || 0) / 1000).toFixed(0)}K</td>
                              <td style={{ padding: '6px 8px', textAlign: 'right', color: m.net_cashflow >= 0 ? '#22c55e' : '#ef4444', fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>
                                {m.net_cashflow >= 0 ? '+' : ''}₹{((m.net_cashflow || 0) / 1000).toFixed(0)}K
                              </td>
                              <td style={{ padding: '6px 8px', textAlign: 'right', color: '#e2e8f0', fontVariantNumeric: 'tabular-nums' }}>₹{((m.closing_cash || 0) / 1000).toFixed(0)}K</td>
                              <td style={{ padding: '6px 8px', textAlign: 'right' }}>
                                <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 10, background: m.status === 'surplus' ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)', color: m.status === 'surplus' ? '#22c55e' : '#ef4444' }}>{m.status}</span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </Card>

                  {/* Bar Chart */}
                  <Card style={{ marginBottom: 12 }}>
                    <SectionHead title="Cash Balance Trend" sub="Closing cash position each month" />
                    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 4, height: 80, marginTop: 8 }}>
                      {(r.months || []).map((m: any) => (
                        <div key={m.month} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
                          <div style={{ width: '100%', height: `${Math.max((m.closing_cash / maxVal) * 72, 4)}px`, background: m.closing_cash >= 0 ? '#22c55e' : '#ef4444', borderRadius: '2px 2px 0 0', minHeight: 4 }} title={`${m.month}: ₹${(m.closing_cash/1000).toFixed(0)}K`} />
                          <div style={{ fontSize: 9, color: '#6b7280' }}>{m.month.slice(0, 1)}</div>
                        </div>
                      ))}
                    </div>
                  </Card>

                  {/* Recommendations */}
                  {(r.recommendations || []).length > 0 && (
                    <Card>
                      <SectionHead title="Recommendations" sub="Based on your 12-month projection" />
                      {(r.recommendations || []).map((rec: string, i: number) => (
                        <div key={i} style={{ fontSize: 13, color: '#e2e8f0', background: '#0f1117', borderRadius: 6, padding: '8px 12px', marginBottom: 6, borderLeft: '3px solid #f59e0b' }}>{rec}</div>
                      ))}
                    </Card>
                  )}
                </>
              )
            })() : !cfLoading && (
              <Card>
                <div style={{ color: '#4b5563', fontSize: 13, textAlign: 'center', marginTop: 60 }}>
                  Demo values are pre-filled — click Generate 12-Month Forecast to see results →
                </div>
              </Card>
            )}
          </div>
        </TwoCol>
      )}
      {/* ── P&L STATEMENT BUILDER (Round 12) ── */}
      {tab === 'pl' && (
        <TwoCol>
          <Card>
            <SectionHead title="📊 P&L Statement Builder" sub="Generate profit & loss with industry benchmarks and insights" />
            <Input label="Company Name" value={plCompany} onChange={setPlCompany} placeholder="e.g. Acme Pvt Ltd" />
            <Input label="Period" value={plPeriod} onChange={setPlPeriod} placeholder="e.g. FY 2024-25 or Q3 FY25" />
            <Select label="Industry (for benchmarks)" value={plIndustry} onChange={setPlIndustry} options={[
              { label: 'Technology / SaaS', value: 'technology' },
              { label: 'E-Commerce', value: 'ecommerce' },
              { label: 'Manufacturing', value: 'manufacturing' },
              { label: 'Retail', value: 'retail' },
              { label: 'Services / Consulting', value: 'services' },
              { label: 'Healthcare', value: 'healthcare' },
              { label: 'Food & Beverage', value: 'food_beverage' },
            ]} />
            <Input label="Tax Rate %" value={plTaxRate} onChange={setPlTaxRate} placeholder="e.g. 25 (corporate tax rate)" />
            <Input label="Previous Period Revenue (₹)" value={plPrevRev} onChange={setPlPrevRev} placeholder="e.g. 4500000 (for YoY comparison)" />
            <Input label="Previous Period Net Profit (₹)" value={plPrevProfit} onChange={setPlPrevProfit} placeholder="e.g. 400000" />
            <div style={{ marginBottom: 10 }}>
              <label style={{ fontSize: 12, color: '#9ca3af', display: 'block', marginBottom: 4 }}>Revenue Items JSON (blank = demo)</label>
              <textarea value={plRevJson} onChange={e => setPlRevJson(e.target.value)} rows={3} placeholder={'[{"name":"Product Sales","amount":3500000}]'} style={{ width: '100%', background: '#1e2535', border: '1px solid #374151', borderRadius: 6, padding: '7px 10px', color: '#e2e8f0', fontSize: 11, fontFamily: 'monospace', boxSizing: 'border-box' }} />
            </div>
            <div style={{ marginBottom: 10 }}>
              <label style={{ fontSize: 12, color: '#9ca3af', display: 'block', marginBottom: 4 }}>COGS Items JSON (blank = demo)</label>
              <textarea value={plCogJson} onChange={e => setPlCogJson(e.target.value)} rows={3} placeholder={'[{"name":"Raw Materials","amount":1400000}]'} style={{ width: '100%', background: '#1e2535', border: '1px solid #374151', borderRadius: 6, padding: '7px 10px', color: '#e2e8f0', fontSize: 11, fontFamily: 'monospace', boxSizing: 'border-box' }} />
            </div>
            <div style={{ marginBottom: 14 }}>
              <label style={{ fontSize: 12, color: '#9ca3af', display: 'block', marginBottom: 4 }}>Operating Expenses JSON (blank = demo)</label>
              <textarea value={plOpexJson} onChange={e => setPlOpexJson(e.target.value)} rows={3} placeholder={'[{"name":"Salaries","amount":900000}]'} style={{ width: '100%', background: '#1e2535', border: '1px solid #374151', borderRadius: 6, padding: '7px 10px', color: '#e2e8f0', fontSize: 11, fontFamily: 'monospace', boxSizing: 'border-box' }} />
            </div>
            <Btn onClick={runPL} loading={plLoading} style={{ width: '100%' }}>Generate P&L Statement</Btn>
            {plErr && <div style={{ color: '#ef4444', fontSize: 12, marginTop: 8 }}>{plErr}</div>}
          </Card>
          <div>
            {plRes ? (() => {
              const r = plRes
              const rows = [
                { label: 'Total Revenue',    val: r.revenue?.formatted,    sub: r.revenue?.items?.length + ' line items', color: '#22c55e', bold: true },
                { label: 'Less: COGS',       val: '(' + r.cogs?.formatted + ')', sub: r.cogs?.items?.length + ' items', color: '#ef4444', bold: false },
                { label: 'Gross Profit',     val: r.gross_profit_fmt,      sub: `${r.gross_margin_pct}% margin`, color: '#22c55e', bold: true },
                { label: 'Less: OpEx',       val: '(' + r.opex?.formatted + ')', sub: r.opex?.items?.length + ' items', color: '#ef4444', bold: false },
                { label: 'EBITDA',           val: r.ebitda_fmt,            sub: `${r.ebitda_margin}% margin`, color: '#10b981', bold: true },
                { label: 'Less: Tax',        val: `(₹${((r.tax_amount||0)/100000).toFixed(1)}L)`, sub: `${r.tax_rate}% rate`, color: '#f59e0b', bold: false },
                { label: 'Net Profit (PAT)', val: r.pat_fmt,               sub: `${r.net_margin_pct}% margin`, color: r.pat >= 0 ? '#22c55e' : '#ef4444', bold: true },
              ]
              return (
                <>
                  {/* P&L table */}
                  <Card style={{ marginBottom: 12 }}>
                    <SectionHead title={`${r.company} — ${r.period}`} sub="Profit & Loss Statement" />
                    {rows.map((row, i) => (
                      <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid #1e2535' }}>
                        <div>
                          <div style={{ fontSize: row.bold ? 14 : 13, fontWeight: row.bold ? 700 : 400, color: row.bold ? '#e2e8f0' : '#9ca3af' }}>{row.label}</div>
                          {row.sub && <div style={{ fontSize: 11, color: '#4b5563' }}>{row.sub}</div>}
                        </div>
                        <div style={{ fontSize: row.bold ? 16 : 13, fontWeight: row.bold ? 800 : 400, color: row.color, fontVariantNumeric: 'tabular-nums' }}>{row.val}</div>
                      </div>
                    ))}
                    {(r.yoy_revenue_growth !== null && r.yoy_revenue_growth !== undefined) && (
                      <div style={{ display: 'flex', gap: 10, marginTop: 10 }}>
                        <Badge label={`Revenue YoY: ${r.yoy_revenue_growth > 0 ? '+' : ''}${r.yoy_revenue_growth}%`} color={r.yoy_revenue_growth >= 10 ? '#22c55e' : '#f59e0b'} />
                        {r.yoy_profit_growth !== null && r.yoy_profit_growth !== undefined && <Badge label={`Profit YoY: ${r.yoy_profit_growth > 0 ? '+' : ''}${r.yoy_profit_growth}%`} color={r.yoy_profit_growth >= 0 ? '#22c55e' : '#ef4444'} />}
                      </div>
                    )}
                  </Card>

                  {/* Benchmark comparison */}
                  <Card style={{ marginBottom: 12 }}>
                    <SectionHead title="Industry Benchmark" sub={`vs ${r.industry} sector averages`} />
                    {(r.benchmark_comparison || []).map((b: any, i: number) => (
                      <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid #1e2535' }}>
                        <span style={{ fontSize: 13, color: '#9ca3af' }}>{b.label}</span>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                          <span style={{ fontSize: 12, color: '#6b7280' }}>Bench: {b.benchmark}%</span>
                          <span style={{ fontSize: 14, fontWeight: 700, color: b.color }}>{b.actual}%</span>
                          <Badge label={`${b.diff > 0 ? '+' : ''}${b.diff}pp`} color={b.color} />
                        </div>
                      </div>
                    ))}
                  </Card>

                  {/* Insights */}
                  <Card>
                    <SectionHead title="CA Insights" sub="Actionable observations from your P&L" />
                    {(r.insights || []).map((ins: string, i: number) => (
                      <div key={i} style={{ fontSize: 13, color: '#e2e8f0', background: '#0f1117', borderRadius: 6, padding: '8px 12px', marginBottom: 6, borderLeft: '3px solid #818cf8' }}>{ins}</div>
                    ))}
                  </Card>
                </>
              )
            })() : !plLoading && (
              <Card>
                <div style={{ color: '#4b5563', fontSize: 13, textAlign: 'center', marginTop: 60 }}>
                  Leave JSON fields blank for demo data — click Generate P&L Statement →
                </div>
              </Card>
            )}
          </div>
        </TwoCol>
      )}

      {/* ── OVERDUE INVOICE COLLECTOR (Round 11) ── */}
      {tab === 'overdue' && (
        <TwoCol>
          <Card>
            <SectionHead title="📬 Overdue Invoice Collector" sub="4-stage escalating email sequence — gentle to legal notice" />
            <Input label="Your Company Name" value={odCompany} onChange={setOdCompany} placeholder="e.g. Acme Pvt Ltd" />
            <Input label="Default Contact Name" value={odContact} onChange={setOdContact} placeholder="e.g. Rahul (leave blank for Sir/Madam)" />
            <Input label="Sender Name / Designation" value={odSender} onChange={setOdSender} placeholder="e.g. Priya Sharma, Finance Manager" />
            <Input label="Late Fee % per Month" value={odLateFee} onChange={setOdLateFee} placeholder="e.g. 2" />
            <div style={{ marginBottom: 14 }}>
              <label style={{ fontSize: 12, color: '#9ca3af', display: 'block', marginBottom: 4 }}>Invoice List (JSON — leave blank for demo)</label>
              <textarea value={odInvoicesJson} onChange={e => setOdInvoicesJson(e.target.value)} rows={5} placeholder={`[\n  {"invoice_no":"INV-101","amount":85000,"due_date":"2024-11-15","days_overdue":45,"client":"ABC Ltd"}\n]`} style={{ width: '100%', background: '#1e2535', border: '1px solid #374151', borderRadius: 6, padding: '8px 10px', color: '#e2e8f0', fontSize: 12, fontFamily: 'monospace', boxSizing: 'border-box', resize: 'vertical' }} />
            </div>
            <Btn onClick={runOverdueCollector} loading={odLoading} style={{ width: '100%' }}>Generate Collection Emails</Btn>
            {odErr && <div style={{ color: '#ef4444', fontSize: 12, marginTop: 8 }}>{odErr}</div>}
          </Card>
          <div>
            {odRes ? (() => {
              const r = odRes
              const URGENCY_COLOR: Record<string, string> = { critical: '#ef4444', high: '#f97316', medium: '#f59e0b', low: '#22c55e' }
              const STAGE_LABEL: Record<string, string> = { gentle: 'Gentle Reminder', firm: 'Firm Notice', strong: 'Strong Warning', legal: 'Legal Notice' }
              return (
                <>
                  {/* KPI */}
                  <Card style={{ marginBottom: 12 }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
                      {[
                        { label: 'Total Overdue', val: `₹${((r.total_overdue || 0)/100000).toFixed(1)}L`, color: '#ef4444' },
                        { label: 'Late Fees', val: `₹${((r.total_late_fees || 0)/100000).toFixed(1)}L`, color: '#f97316' },
                        { label: 'Recoverable', val: `₹${((r.total_recoverable || 0)/100000).toFixed(1)}L`, color: '#22c55e' },
                      ].map(k => (
                        <div key={k.label} style={{ background: '#0f1117', borderRadius: 8, padding: '10px 12px', textAlign: 'center' }}>
                          <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 4 }}>{k.label}</div>
                          <div style={{ fontSize: 20, fontWeight: 800, color: k.color }}>{k.val}</div>
                        </div>
                      ))}
                    </div>
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 10 }}>
                      {Object.entries(r.urgency_count || {}).filter(([, v]: any) => v > 0).map(([k, v]: any) => (
                        <Badge key={k} label={`${k}: ${v}`} color={URGENCY_COLOR[k] || '#6b7280'} />
                      ))}
                    </div>
                  </Card>

                  {/* Invoice list */}
                  {(r.invoices || []).map((inv: any, i: number) => (
                    <div key={i} style={{ border: `1px solid ${URGENCY_COLOR[inv.urgency] || '#374151'}`, borderRadius: 8, marginBottom: 10, overflow: 'hidden' }}>
                      <div onClick={() => setOdSelected(odSelected === i ? null : i)} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: '#111827', cursor: 'pointer' }}>
                        <div>
                          <span style={{ color: '#e2e8f0', fontWeight: 600, fontSize: 13 }}>{inv.client} — {inv.invoice_no}</span>
                          <span style={{ marginLeft: 10, fontSize: 11, color: '#6b7280' }}>{inv.days_overdue} days overdue</span>
                        </div>
                        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                          <Badge label={STAGE_LABEL[inv.stage] || inv.stage} color={URGENCY_COLOR[inv.urgency] || '#6b7280'} />
                          <span style={{ color: '#22c55e', fontWeight: 700, fontSize: 13 }}>₹{(inv.total_due || 0).toLocaleString('en-IN')}</span>
                        </div>
                      </div>
                      {odSelected === i && (
                        <div style={{ padding: '12px 14px', background: '#0f1117' }}>
                          <div style={{ fontSize: 11, color: '#9ca3af', marginBottom: 6 }}>Subject: <span style={{ color: '#e2e8f0' }}>{inv.subject}</span></div>
                          <div style={{ fontSize: 12, color: '#e2e8f0', lineHeight: 1.7, whiteSpace: 'pre-wrap', maxHeight: 300, overflowY: 'auto', background: '#111827', borderRadius: 6, padding: '10px 12px', marginBottom: 8 }}>{inv.email_body}</div>
                          <span onClick={() => navigator.clipboard?.writeText(`Subject: ${inv.subject}\n\n${inv.email_body}`)} style={{ cursor: 'pointer', fontSize: 11, color: '#fff', padding: '4px 12px', background: '#374151', borderRadius: 6 }}>Copy Email</span>
                        </div>
                      )}
                    </div>
                  ))}

                  {/* Tips */}
                  {(r.collection_tips || []).length > 0 && (
                    <Card>
                      <SectionHead title="Collection Tips" sub="India-specific best practices" />
                      {r.collection_tips.map((t: string, i: number) => (
                        <div key={i} style={{ fontSize: 12, color: '#9ca3af', padding: '6px 0', borderBottom: '1px solid #1e2535' }}>• {t}</div>
                      ))}
                    </Card>
                  )}
                </>
              )
            })() : !odLoading && (
              <Card>
                <div style={{ color: '#4b5563', fontSize: 13, textAlign: 'center', marginTop: 60 }}>
                  Leave invoice list blank for demo data — click Generate Collection Emails →
                </div>
              </Card>
            )}
          </div>
        </TwoCol>
      )}
      {/* ── CLIENT PROPOSAL GENERATOR (Round 15) ── */}
      {tab === 'proposal' && (
        <TwoCol>
          <Card>
            <SectionHead title="📋 Client Proposal Generator" sub="Professional engagement proposal + letter template for CA firms" />
            <Input label="CA Firm Name" value={propFirm} onChange={setPropFirm} placeholder="e.g. Sharma & Associates, Chartered Accountants" />
            <Input label="Client Company Name" value={propClient} onChange={setPropClient} placeholder="e.g. ABC Manufacturing Pvt Ltd" />
            <Input label="Client Industry" value={propIndustry} onChange={setPropIndustry} placeholder="e.g. manufacturing, IT services, retail" />
            <Input label="Approx. Annual Turnover" value={propTurnover} onChange={setPropTurnover} placeholder="e.g. ₹5 Cr – ₹10 Cr" />
            <Input label="CA / Partner Name" value={propCa} onChange={setPropCa} placeholder="e.g. CA Rajesh Sharma" />
            <Input label="Engagement Start Date" value={propStart} onChange={setPropStart} placeholder="e.g. 1st August 2025" />
            <Select label="Fee Structure" value={propFeeType} onChange={setPropFeeType} options={[
              { label: 'Monthly Retainer', value: 'monthly_retainer' },
              { label: 'Annual Fee', value: 'annual_fee' },
            ]} />
            <div style={{ marginBottom: 14 }}>
              <label style={{ fontSize: 12, color: '#9ca3af', display: 'block', marginBottom: 6 }}>Services to Include</label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {[
                  ['bookkeeping','Bookkeeping'],['gst_filing','GST Filing'],['tds_compliance','TDS'],
                  ['income_tax','Income Tax'],['audit','Audit'],['roc_compliance','ROC'],
                  ['payroll','Payroll'],['virtual_cfo','Virtual CFO'],['msme_advisory','MSME Advisory'],
                ].map(([key, label]) => (
                  <span key={key} onClick={() => toggleService(key)} style={{
                    padding: '4px 10px', borderRadius: 20, fontSize: 11, cursor: 'pointer',
                    background: propServices.includes(key) ? '#4f46e5' : '#1e2535',
                    color: propServices.includes(key) ? '#fff' : '#6b7280',
                  }}>{label}</span>
                ))}
              </div>
            </div>
            <Btn onClick={runProposal} disabled={propLoading}>{propLoading ? 'Generating…' : '📋 Generate Proposal'}</Btn>
            {propErr && <div style={{ color: '#ef4444', fontSize: 12, marginTop: 8 }}>{propErr}</div>}
          </Card>
          <Card>
            {propRes ? (() => {
              const r = propRes
              const fs = r.fee_summary || {}
              return (
                <>
                  {/* Fee summary banner */}
                  <div style={{ background: '#0f172a', borderRadius: 10, padding: 14, marginBottom: 14, border: '1px solid #4f46e580' }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: '#e2e8f0', marginBottom: 4 }}>{r.firm_name}</div>
                    <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 8 }}>Proposal for {r.client_name} · {r.client_industry}</div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                      <div style={{ background: '#1e2535', borderRadius: 6, padding: 10, textAlign: 'center' }}>
                        <div style={{ fontSize: 18, fontWeight: 800, color: '#22c55e' }}>₹{fs.monthly_retainer_incl_gst?.toLocaleString()}</div>
                        <div style={{ fontSize: 10, color: '#6b7280' }}>per month incl GST</div>
                      </div>
                      <div style={{ background: '#1e2535', borderRadius: 6, padding: 10, textAlign: 'center' }}>
                        <div style={{ fontSize: 18, fontWeight: 800, color: '#60a5fa' }}>₹{fs.annual_value_incl_gst?.toLocaleString()}</div>
                        <div style={{ fontSize: 10, color: '#6b7280' }}>annual value incl GST</div>
                      </div>
                    </div>
                  </div>

                  {/* View switcher */}
                  <div style={{ display: 'flex', gap: 4, marginBottom: 12 }}>
                    {(['proposal','letter','checklist'] as const).map(v => (
                      <span key={v} onClick={() => setPropView(v)} style={{
                        padding: '4px 12px', borderRadius: 6, fontSize: 11, cursor: 'pointer',
                        background: propView === v ? '#4f46e5' : '#1e2535',
                        color: propView === v ? '#fff' : '#6b7280', fontWeight: propView === v ? 700 : 400,
                      }}>{v === 'proposal' ? '📋 Proposal' : v === 'letter' ? '📄 Eng. Letter' : '✅ Doc Checklist'}</span>
                    ))}
                  </div>

                  {/* Proposal view */}
                  {propView === 'proposal' && (
                    <div>
                      <div style={{ fontSize: 11, color: '#94a3b8', marginBottom: 12, lineHeight: 1.6 }}>{r.proposal_content?.executive_summary}</div>
                      <div style={{ fontSize: 11, fontWeight: 700, color: '#9ca3af', marginBottom: 6 }}>SCOPE OF WORK ({r.services_selected?.length} services)</div>
                      {(r.scope_items || []).map((svc: any, i: number) => (
                        <div key={i} style={{ background: '#0f172a', borderRadius: 6, padding: 10, marginBottom: 8 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                            <span style={{ fontSize: 12, fontWeight: 600, color: '#e2e8f0' }}>{svc.service}</span>
                            <span style={{ fontSize: 11, color: '#22c55e' }}>₹{svc.fee?.toLocaleString()} {svc.unit}</span>
                          </div>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                            {(svc.deliverables || []).map((d: string, j: number) => (
                              <span key={j} style={{ background: '#1e2535', borderRadius: 4, padding: '2px 6px', fontSize: 10, color: '#6b7280' }}>{d}</span>
                            ))}
                          </div>
                        </div>
                      ))}
                      <div style={{ fontSize: 11, fontWeight: 700, color: '#9ca3af', marginBottom: 6, marginTop: 12 }}>TIMELINE</div>
                      {(r.proposal_content?.timeline || []).map((t: any, i: number) => (
                        <div key={i} style={{ display: 'flex', gap: 10, padding: '6px 0', borderBottom: '1px solid #111827' }}>
                          <span style={{ fontSize: 10, color: '#4f46e5', minWidth: 55, fontWeight: 700 }}>{t.week}</span>
                          <span style={{ fontSize: 11, color: '#d1d5db' }}>{t.milestone}</span>
                        </div>
                      ))}
                      <div style={{ marginTop: 12 }}>
                        <div style={{ fontSize: 11, fontWeight: 700, color: '#9ca3af', marginBottom: 6 }}>WHY US</div>
                        {(r.proposal_content?.value_propositions || []).map((vp: string, i: number) => (
                          <div key={i} style={{ fontSize: 11, color: '#d1d5db', padding: '3px 0' }}>✓ {vp}</div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Engagement letter */}
                  {propView === 'letter' && (
                    <div>
                      <div style={{ fontSize: 10, color: '#f59e0b', marginBottom: 8 }}>ENGAGEMENT LETTER — copy, customise & print on letterhead</div>
                      <div style={{ background: '#0f172a', borderRadius: 6, padding: 14, fontSize: 11, color: '#d1d5db', whiteSpace: 'pre-wrap', lineHeight: 1.8, fontFamily: 'monospace', maxHeight: 500, overflowY: 'auto' }}>
                        {r.engagement_letter}
                      </div>
                    </div>
                  )}

                  {/* Document checklist */}
                  {propView === 'checklist' && (
                    <div>
                      <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 10 }}>Documents to collect from {r.client_name} at kick-off</div>
                      {(r.document_checklist || []).map((doc: string, i: number) => (
                        <div key={i} style={{ display: 'flex', gap: 8, padding: '6px 0', borderBottom: '1px solid #111827' }}>
                          <span style={{ color: '#f59e0b', fontSize: 12 }}>📌</span>
                          <span style={{ fontSize: 12, color: '#d1d5db' }}>{doc}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              )
            })() : <div style={{ color: '#4b5563', fontSize: 13, textAlign: 'center', marginTop: 60 }}>Fill details and click Generate Proposal →</div>}
          </Card>
        </TwoCol>
      )}

      {/* ── TDS COMPLIANCE TRACKER (Round 14) ── */}
      {tab === 'tds' && (
        <TwoCol>
          <Card>
            <SectionHead title="📅 TDS Compliance Tracker" sub="Section-wise TDS ledger, challan due dates, late fee calculator & filing checklist" />
            <Input label="Company Name" value={tdsCompany} onChange={setTdsCompany} placeholder="e.g. Sharma & Associates" />
            <Select label="Month" value={String(tdsMonth)} onChange={v => setTdsMonth(parseInt(v))} options={[
              {label:'January',value:'1'},{label:'February',value:'2'},{label:'March',value:'3'},
              {label:'April',value:'4'},{label:'May',value:'5'},{label:'June',value:'6'},
              {label:'July',value:'7'},{label:'August',value:'8'},{label:'September',value:'9'},
              {label:'October',value:'10'},{label:'November',value:'11'},{label:'December',value:'12'},
            ]} />
            <Select label="Year" value={String(tdsYear)} onChange={v => setTdsYear(parseInt(v))} options={[
              {label:'2024',value:'2024'},{label:'2025',value:'2025'},{label:'2026',value:'2026'},
            ]} />
            <div style={{ background: '#1e2535', borderRadius: 8, padding: 10, marginBottom: 14, fontSize: 11, color: '#6b7280' }}>
              Demo data pre-loaded with 5 TDS deductions across sections 192, 194C, 194I, 194J & 194Q
            </div>
            <Btn onClick={runTds} disabled={tdsLoading}>{tdsLoading ? 'Calculating…' : '📅 Generate TDS Report'}</Btn>
            {tdsErr && <div style={{ color: '#ef4444', fontSize: 12, marginTop: 8 }}>{tdsErr}</div>}
          </Card>
          <Card>
            {tdsRes ? (() => {
              const r = tdsRes
              const dueColor = r.due_status === 'overdue' ? '#ef4444' : r.due_status === 'urgent' ? '#f59e0b' : '#22c55e'
              const statusBadge = (s: string) => ({ deposited: '#22c55e', pending: '#f59e0b', overdue: '#ef4444' }[s] || '#6b7280')
              return (
                <>
                  {/* Summary cards */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, marginBottom: 14 }}>
                    {[
                      { label: 'Total TDS', value: `₹${(r.total_tds_deducted/1000).toFixed(0)}K`, color: '#60a5fa' },
                      { label: 'Deposited', value: `₹${(r.total_deposited/1000).toFixed(0)}K`,   color: '#22c55e' },
                      { label: 'Pending',   value: `₹${(r.total_pending/1000).toFixed(0)}K`,     color: r.total_pending > 0 ? '#ef4444' : '#22c55e' },
                    ].map((c, i) => (
                      <div key={i} style={{ background: '#0f172a', borderRadius: 8, padding: 10, textAlign: 'center' }}>
                        <div style={{ fontSize: 20, fontWeight: 800, color: c.color }}>{c.value}</div>
                        <div style={{ fontSize: 10, color: '#6b7280' }}>{c.label}</div>
                      </div>
                    ))}
                  </div>

                  {/* Challan due */}
                  <div style={{ background: '#0f172a', borderRadius: 8, padding: 12, marginBottom: 14, border: `1px solid ${dueColor}40` }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <div style={{ fontSize: 12, fontWeight: 700, color: dueColor }}>
                          {r.due_status === 'overdue' ? '⚠️ CHALLAN OVERDUE' : r.due_status === 'urgent' ? '⚡ DUE SOON' : '✅ CHALLAN DUE'}
                        </div>
                        <div style={{ fontSize: 11, color: '#d1d5db', marginTop: 2 }}>{r.challan_due_date}</div>
                      </div>
                      <div style={{ fontSize: 22, fontWeight: 800, color: dueColor }}>
                        {r.days_to_due >= 0 ? `${r.days_to_due}d` : `${Math.abs(r.days_to_due)}d late`}
                      </div>
                    </div>
                    {r.total_late_fee > 0 && (
                      <div style={{ fontSize: 11, color: '#ef4444', marginTop: 6 }}>
                        Late fee u/s 234E: ₹{r.total_late_fee.toLocaleString()} | Interest u/s 201: ₹{r.total_late_interest.toLocaleString()}
                      </div>
                    )}
                  </div>

                  {/* Deductions table */}
                  <div style={{ marginBottom: 14 }}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: '#9ca3af', marginBottom: 6 }}>TDS DEDUCTIONS — {r.month} {r.year}</div>
                    {(r.deductions || []).map((d: any, i: number) => (
                      <div key={i} style={{ background: '#0f172a', borderRadius: 6, padding: 10, marginBottom: 6, cursor: 'pointer', border: `1px solid ${tdsActiveSection === String(i) ? '#4f46e5' : '#1e2535'}` }}
                        onClick={() => setTdsActiveSection(tdsActiveSection === String(i) ? null : String(i))}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <div>
                            <span style={{ fontSize: 11, fontWeight: 700, color: '#60a5fa', marginRight: 8 }}>§{d.section}</span>
                            <span style={{ fontSize: 11, color: '#e2e8f0' }}>{d.payee}</span>
                          </div>
                          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                            <span style={{ fontSize: 12, fontWeight: 700, color: '#e2e8f0' }}>₹{d.tds_amount.toLocaleString()}</span>
                            <span style={{ background: statusBadge(d.status) + '20', color: statusBadge(d.status), borderRadius: 4, padding: '2px 6px', fontSize: 10 }}>{d.status}</span>
                          </div>
                        </div>
                        {tdsActiveSection === String(i) && (
                          <div style={{ marginTop: 8, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4, fontSize: 11, color: '#6b7280' }}>
                            <div>Nature: {d.nature}</div>
                            <div>Amount: ₹{d.amount.toLocaleString()}</div>
                            <div>Rate: {d.rate}%</div>
                            <div>Form: {d.form}</div>
                            {d.pan_issue && <div style={{ color: '#ef4444', gridColumn: '1/-1' }}>⚠️ PAN issue — 20% rate may apply</div>}
                            {d.late_fee_234E > 0 && <div style={{ color: '#ef4444', gridColumn: '1/-1' }}>Late fee: ₹{d.late_fee_234E} | Interest: ₹{d.late_interest_201}</div>}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Monthly deadlines */}
                  <div style={{ marginBottom: 14 }}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: '#9ca3af', marginBottom: 6 }}>KEY DEADLINES — {r.month}</div>
                    {(r.month_deadlines || []).map((dl: string, i: number) => (
                      <div key={i} style={{ fontSize: 11, color: '#d1d5db', padding: '4px 0', borderBottom: '1px solid #111827' }}>📌 {dl}</div>
                    ))}
                    <div style={{ fontSize: 11, color: '#60a5fa', marginTop: 6 }}>
                      {r.quarter} Return ({r.return_form}) due: {r.return_due}
                    </div>
                  </div>

                  {/* Common errors */}
                  <div>
                    <div style={{ fontSize: 11, fontWeight: 700, color: '#f59e0b', marginBottom: 6 }}>⚠️ COMMON TDS MISTAKES TO AVOID</div>
                    {(r.common_errors || []).map((err: string, i: number) => (
                      <div key={i} style={{ fontSize: 11, color: '#94a3b8', padding: '3px 0' }}>→ {err}</div>
                    ))}
                  </div>
                </>
              )
            })() : <div style={{ color: '#4b5563', fontSize: 13, textAlign: 'center', marginTop: 60 }}>Select month & year, click Generate TDS Report →</div>}
          </Card>
        </TwoCol>
      )}

      {/* ── MSME LOAN ELIGIBILITY (Round 13) ── */}
      {tab === 'loan' && (
        <TwoCol>
          <Card>
            <SectionHead title="🏦 MSME Loan Eligibility Checker" sub="Check eligibility, identify schemes & get a document checklist" />
            <Input label="Company Name" value={lnCompany} onChange={setLnCompany} placeholder="e.g. Sharma Textiles Pvt Ltd" />
            <Select label="Business Type" value={lnBizType} onChange={setLnBizType} options={[
              { label: 'Manufacturing', value: 'manufacturing' },
              { label: 'Service', value: 'service' },
            ]} />
            <Input label="Annual Turnover (₹)" value={lnTurnover} onChange={setLnTurnover} placeholder="e.g. 15000000 (1.5 Cr)" />
            <Input label="Plant & Machinery / Equipment Value (₹)" value={lnPlant} onChange={setLnPlant} placeholder="e.g. 3000000" />
            <Input label="Years in Business" value={lnYears} onChange={setLnYears} placeholder="e.g. 5" />
            <Select label="Loan Purpose" value={lnPurpose} onChange={setLnPurpose} options={[
              { label: 'Working Capital', value: 'working_capital' },
              { label: 'Term Loan / Expansion', value: 'term_loan' },
              { label: 'Machinery Purchase', value: 'machinery' },
              { label: 'Export Finance', value: 'export' },
              { label: 'Trade Receivables / Invoice Discounting', value: 'trade_receivables' },
            ]} />
            <Input label="Loan Amount Requested (₹)" value={lnAmount} onChange={setLnAmount} placeholder="e.g. 5000000 (50L)" />
            <Input label="Existing Loan Outstanding (₹)" value={lnExisting} onChange={setLnExisting} placeholder="e.g. 1000000 or 0" />
            <Input label="Monthly Revenue (₹)" value={lnRevenue} onChange={setLnRevenue} placeholder="e.g. 1200000 — used for DSCR calculation" />
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
              <input type="checkbox" checked={lnGst} onChange={e => setLnGst(e.target.checked)} id="gst_check" />
              <label htmlFor="gst_check" style={{ fontSize: 13, color: '#d1d5db', cursor: 'pointer' }}>GST Registered</label>
            </div>
            <Btn onClick={runLoan} disabled={lnLoading}>{lnLoading ? 'Checking…' : '🏦 Check Loan Eligibility'}</Btn>
            {lnErr && <div style={{ color: '#ef4444', fontSize: 12, marginTop: 8 }}>{lnErr}</div>}
          </Card>
          <Card>
            {lnRes ? (() => {
              const r = lnRes
              const verdictColor: Record<string, string> = { green: '#22c55e', yellow: '#f59e0b', red: '#ef4444' }
              const vc = verdictColor[r.verdict_color] || '#6b7280'
              const statusIcon = (s: string) => s === 'pass' ? '✅' : s === 'warn' ? '⚠️' : s === 'fail' ? '❌' : 'ℹ️'
              return (
                <>
                  {/* Score card */}
                  <div style={{ background: '#0f172a', borderRadius: 10, padding: 16, marginBottom: 14, border: `1px solid ${vc}40` }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                      <div>
                        <div style={{ fontSize: 15, fontWeight: 700, color: '#e2e8f0' }}>{r.company}</div>
                        <div style={{ fontSize: 11, color: '#6b7280' }}>{r.msme_category?.toUpperCase()} Enterprise • {r.business_type}</div>
                      </div>
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: 32, fontWeight: 800, color: vc }}>{r.eligibility_score}</div>
                        <div style={{ fontSize: 10, color: '#6b7280' }}>/ 100</div>
                      </div>
                    </div>
                    <div style={{ background: '#1e2535', borderRadius: 6, height: 8, marginBottom: 8 }}>
                      <div style={{ background: vc, borderRadius: 6, height: 8, width: `${r.eligibility_score}%`, transition: 'width 0.5s' }} />
                    </div>
                    <div style={{ fontSize: 12, color: vc, fontWeight: 600 }}>{r.verdict} — {r.verdict_message}</div>
                  </div>

                  {/* Score breakdown */}
                  <div style={{ marginBottom: 14 }}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: '#9ca3af', marginBottom: 6 }}>ELIGIBILITY FACTORS</div>
                    {(r.score_breakdown || []).map((s: any, i: number) => (
                      <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid #111827' }}>
                        <div style={{ fontSize: 12, color: '#d1d5db' }}>{statusIcon(s.status)} {s.factor}</div>
                        <div style={{ fontSize: 11, color: s.points > 0 ? '#22c55e' : '#6b7280' }}>+{s.points}pts</div>
                      </div>
                    ))}
                    {(r.score_breakdown || []).map((s: any, i: number) => s.note ? (
                      <div key={`n${i}`} style={{ fontSize: 10, color: '#6b7280', padding: '2px 0 2px 18px' }}>{s.note}</div>
                    ) : null)}
                  </div>

                  {/* Recommended schemes */}
                  <div style={{ marginBottom: 14 }}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: '#9ca3af', marginBottom: 6 }}>RECOMMENDED SCHEMES</div>
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 8 }}>
                      {(r.recommended_schemes || []).map((s: string, i: number) => (
                        <span key={i} style={{ background: '#1e2535', borderRadius: 20, padding: '3px 10px', fontSize: 11, color: '#60a5fa' }}>{s}</span>
                      ))}
                    </div>
                    <div style={{ fontSize: 11, color: '#d1d5db' }}>Max without collateral: <strong style={{ color: '#22c55e' }}>{r.max_without_collateral}</strong></div>
                    <div style={{ fontSize: 11, color: '#d1d5db' }}>Interest: {r.interest_range} | Tenure: {r.tenure}</div>
                    {r.dscr_estimate && <div style={{ fontSize: 11, color: '#d1d5db', marginTop: 4 }}>Est. DSCR: {r.dscr_estimate}</div>}
                  </div>

                  {/* Govt subsidies */}
                  <div style={{ marginBottom: 14 }}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: '#9ca3af', marginBottom: 6 }}>GOVERNMENT SCHEMES YOU QUALIFY FOR</div>
                    {(r.government_subsidies || []).map((s: any, i: number) => (
                      <div key={i} style={{ background: '#0f172a', borderRadius: 6, padding: 10, marginBottom: 8, border: '1px solid #1e2535' }}>
                        <div style={{ fontSize: 12, fontWeight: 700, color: '#22c55e', marginBottom: 4 }}>{s.name}</div>
                        <div style={{ fontSize: 11, color: '#d1d5db', marginBottom: 2 }}>{s.benefit}</div>
                        <div style={{ fontSize: 10, color: '#6b7280' }}>Apply: {s.apply_via}</div>
                      </div>
                    ))}
                  </div>

                  {/* Document checklist */}
                  <div style={{ marginBottom: 14 }}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: '#9ca3af', marginBottom: 6 }}>DOCUMENT CHECKLIST</div>
                    {(r.document_checklist || []).map((d: any, i: number) => (
                      <div key={i} style={{ display: 'flex', gap: 8, padding: '4px 0', borderBottom: '1px solid #111827' }}>
                        <span style={{ fontSize: 12 }}>{d.mandatory ? '📌' : '📎'}</span>
                        <div>
                          <div style={{ fontSize: 11, color: d.mandatory ? '#e2e8f0' : '#6b7280' }}>{d.doc}</div>
                          <div style={{ fontSize: 10, color: '#4b5563' }}>{d.note}</div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Recommendations */}
                  {r.recommendations?.length > 0 && (
                    <div>
                      <div style={{ fontSize: 11, fontWeight: 700, color: '#f59e0b', marginBottom: 6 }}>⚡ RECOMMENDATIONS TO IMPROVE ELIGIBILITY</div>
                      {r.recommendations.map((rec: string, i: number) => (
                        <div key={i} style={{ fontSize: 11, color: '#d1d5db', padding: '4px 0', borderBottom: '1px solid #111827' }}>→ {rec}</div>
                      ))}
                    </div>
                  )}
                </>
              )
            })() : <div style={{ color: '#4b5563', fontSize: 13, textAlign: 'center', marginTop: 60 }}>Fill in your business details and click Check Loan Eligibility →</div>}
          </Card>
        </TwoCol>
      )}
    </PageShell>
  )
}
