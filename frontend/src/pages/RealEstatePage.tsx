// frontend/src/pages/RealEstatePage.tsx — Real Estate vertical
import { useState } from 'react'
import { PageShell, Card, Btn, Input, Select, ResultBox, Tabs, TwoCol, useApi, SectionHead } from '../components/ui'
import { realestateAction } from '../lib/api'

const PROP_TYPES = ['1BHK Apartment','2BHK Apartment','3BHK Apartment','Villa','Independent House','Plot/Land','Commercial Office','Retail Shop','Warehouse']

export default function RealEstatePage() {
  const [tab, setTab] = useState('listing')

  // Listing
  const [lType, setLType]       = useState('2BHK Apartment')
  const [lFor, setLFor]         = useState('Sale')
  const [lLoc, setLLoc]         = useState('Whitefield, Bengaluru')
  const [lArea, setLArea]       = useState('1180 sqft (carpet 980)')
  const [lPrice, setLPrice]     = useState('₹95 Lakh')
  const [lFeat, setLFeat]       = useState('East facing, 3rd floor, semi-furnished, covered parking, 2 balconies')
  const [lAmen, setLAmen]       = useState('Gym, pool, clubhouse, 24x7 security, kids play area, power backup')
  const listingApi = useApi()

  // Lease
  const [leLandlord, setLeLandlord] = useState('Suresh Rao')
  const [leTenant, setLeTenant]     = useState('Priya Menon')
  const [leProp, setLeProp]         = useState('2BHK, Flat 402, Lake View Apartments, HSR Layout, Bengaluru')
  const [leRent, setLeRent]         = useState('₹35,000/month')
  const [leDep, setLeDep]           = useState('₹2,10,000 (6 months)')
  const [leTerm, setLeTerm]         = useState('11 months')
  const [leCity, setLeCity]         = useState('Bengaluru, Karnataka')
  const leaseApi = useApi()

  // ROI
  const [roPrice, setRoPrice]   = useState('₹95,00,000')
  const [roDown, setRoDown]     = useState('₹20,00,000')
  const [roRate, setRoRate]     = useState('8.6%')
  const [roTenure, setRoTenure] = useState('20 years')
  const [roRent, setRoRent]     = useState('₹32,000/month')
  const [roApp, setRoApp]       = useState('7% p.a.')
  const [roCosts, setRoCosts]   = useState('Maintenance ₹3,500/mo, property tax ₹18,000/yr')
  const roiApi = useApi()

  // Lead
  const [ldType, setLdType]     = useState('Buyer')
  const [ldReq, setLdReq]       = useState('3BHK, ready-to-move, near tech park, Sarjapur Road')
  const [ldBudget, setLdBudget] = useState('₹1.2–1.4 Cr')
  const [ldTime, setLdTime]     = useState('Wants to close in 45 days')
  const [ldNotes, setLdNotes]   = useState('Has pre-approved home loan. Relocating from Pune. Decision maker is buyer + spouse.')
  const leadApi = useApi()

  // CMA
  const [cmProp, setCmProp]     = useState('3BHK apartment, 1650 sqft, 5 yrs old')
  const [cmLoc, setCmLoc]       = useState('Sarjapur Road, Bengaluru')
  const [cmArea, setCmArea]     = useState('1650 sqft built-up')
  const [cmCond, setCmCond]     = useState('Well-maintained, recently painted, 5 years old')
  const [cmComp, setCmComp]     = useState('')
  const cmaApi = useApi()

  return (
    <PageShell icon="🏘️" title="AI Real Estate Assistant" subtitle="Listings, lease drafts, investment ROI, lead qualification, market analysis">
      <Tabs
        tabs={[
          { id: 'listing', label: 'Listing Generator', icon: '📣' },
          { id: 'lease',   label: 'Lease Agreement',   icon: '📜' },
          { id: 'roi',     label: 'ROI Calculator',    icon: '📈' },
          { id: 'lead',    label: 'Lead Qualify',      icon: '🎯' },
          { id: 'cma',     label: 'Market Analysis',   icon: '🏷️' },
        ]}
        active={tab} onChange={setTab}
      />

      {tab === 'listing' && (
        <TwoCol>
          <Card>
            <SectionHead title="Property Listing Generator" sub="Portal + premium + WhatsApp copy with SEO tags" />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Select label="Property Type" value={lType} onChange={setLType} options={PROP_TYPES.map(t => ({ label: t, value: t }))} />
              <Select label="Listing For" value={lFor} onChange={setLFor} options={[{label:'Sale',value:'Sale'},{label:'Rent',value:'Rent'}]} />
            </div>
            <Input label="Location" value={lLoc} onChange={setLLoc} />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Input label="Area" value={lArea} onChange={setLArea} />
              <Input label="Price" value={lPrice} onChange={setLPrice} />
            </div>
            <Input label="Key Features" value={lFeat} onChange={setLFeat} rows={2} />
            <Input label="Amenities" value={lAmen} onChange={setLAmen} rows={2} />
            <Btn onClick={() => listingApi.call(() => realestateAction('listing_generator', { property_type: lType, listing_for: lFor, location: lLoc, area: lArea, price: lPrice, features: lFeat, amenities: lAmen }))} loading={listingApi.loading}>
              📣 Generate Listing
            </Btn>
          </Card>
          <ResultBox data={listingApi.data ? { listing: (listingApi.data as any).result } : null} loading={listingApi.loading} error={listingApi.error} title="Listing Copy" />
        </TwoCol>
      )}

      {tab === 'lease' && (
        <TwoCol>
          <Card>
            <SectionHead title="Lease Agreement Draft" sub="11-month rental agreement template (for lawyer review)" />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Input label="Landlord" value={leLandlord} onChange={setLeLandlord} />
              <Input label="Tenant"   value={leTenant} onChange={setLeTenant} />
            </div>
            <Input label="Property" value={leProp} onChange={setLeProp} rows={2} />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Input label="Monthly Rent" value={leRent} onChange={setLeRent} />
              <Input label="Deposit"      value={leDep} onChange={setLeDep} />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Input label="Lease Term" value={leTerm} onChange={setLeTerm} />
              <Input label="City/State" value={leCity} onChange={setLeCity} />
            </div>
            <Btn onClick={() => leaseApi.call(() => realestateAction('lease_agreement', { landlord: leLandlord, tenant: leTenant, property: leProp, rent: leRent, deposit: leDep, term: leTerm, city: leCity }))} loading={leaseApi.loading}>
              📜 Draft Lease
            </Btn>
          </Card>
          <ResultBox data={leaseApi.data ? { lease: (leaseApi.data as any).result } : null} loading={leaseApi.loading} error={leaseApi.error} title="Lease Agreement (Draft)" />
        </TwoCol>
      )}

      {tab === 'roi' && (
        <TwoCol>
          <Card>
            <SectionHead title="Investment ROI Calculator" sub="EMI, rental yield, break-even, 10-year wealth projection" />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Input label="Purchase Price" value={roPrice} onChange={setRoPrice} />
              <Input label="Down Payment"   value={roDown} onChange={setRoDown} />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Input label="Loan Rate" value={roRate} onChange={setRoRate} />
              <Input label="Tenure"    value={roTenure} onChange={setRoTenure} />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Input label="Expected Rent" value={roRent} onChange={setRoRent} />
              <Input label="Appreciation"  value={roApp} onChange={setRoApp} />
            </div>
            <Input label="Other Costs" value={roCosts} onChange={setRoCosts} rows={2} />
            <Btn onClick={() => roiApi.call(() => realestateAction('roi_calculator', { price: roPrice, down_payment: roDown, loan_rate: roRate, tenure: roTenure, rent: roRent, appreciation: roApp, costs: roCosts }))} loading={roiApi.loading}>
              📈 Calculate ROI
            </Btn>
          </Card>
          <ResultBox data={roiApi.data ? { roi: (roiApi.data as any).result } : null} loading={roiApi.loading} error={roiApi.error} title="Investment Analysis" />
        </TwoCol>
      )}

      {tab === 'lead' && (
        <TwoCol>
          <Card>
            <SectionHead title="Lead Qualification" sub="BANT score + classification + next actions + follow-up message" />
            <Select label="Lead Type" value={ldType} onChange={setLdType} options={['Buyer','Seller','Tenant','Investor'].map(t => ({ label: t, value: t }))} />
            <Input label="Requirement" value={ldReq} onChange={setLdReq} rows={2} />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Input label="Budget"   value={ldBudget} onChange={setLdBudget} />
              <Input label="Timeline" value={ldTime} onChange={setLdTime} />
            </div>
            <Input label="Notes from Call" value={ldNotes} onChange={setLdNotes} rows={3} />
            <Btn onClick={() => leadApi.call(() => realestateAction('lead_qualify', { lead_type: ldType, requirement: ldReq, budget: ldBudget, timeline: ldTime, notes: ldNotes }))} loading={leadApi.loading}>
              🎯 Qualify Lead
            </Btn>
          </Card>
          <ResultBox data={leadApi.data ? { lead: (leadApi.data as any).result } : null} loading={leadApi.loading} error={leadApi.error} title="Lead Assessment" />
        </TwoCol>
      )}

      {tab === 'cma' && (
        <TwoCol>
          <Card>
            <SectionHead title="Comparative Market Analysis" sub="Pricing recommendation + strategy + days-on-market estimate" />
            <Input label="Subject Property" value={cmProp} onChange={setCmProp} rows={2} />
            <Input label="Location / Micro-market" value={cmLoc} onChange={setCmLoc} />
            <Input label="Area" value={cmArea} onChange={setCmArea} />
            <Input label="Condition / Age" value={cmCond} onChange={setCmCond} />
            <Input label="Recent Comparables (optional)" value={cmComp} onChange={setCmComp} rows={3} placeholder="Paste recent sale/listing prices nearby, or leave blank" />
            <Btn onClick={() => cmaApi.call(() => realestateAction('market_cma', { property: cmProp, location: cmLoc, area: cmArea, condition: cmCond, comparables: cmComp }))} loading={cmaApi.loading}>
              🏷️ Run CMA
            </Btn>
          </Card>
          <ResultBox data={cmaApi.data ? { cma: (cmaApi.data as any).result } : null} loading={cmaApi.loading} error={cmaApi.error} title="Market Analysis" />
        </TwoCol>
      )}
    </PageShell>
  )
}
