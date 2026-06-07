// frontend/src/pages/AgriPage.tsx — Feature 9: AgriTech
import { useState } from 'react'
import { PageShell, Card, Btn, Input, Select, ResultBox, Tabs, TwoCol, useApi, SectionHead } from '../components/ui'
import { agriQuery, getMandiPrices, getWeather, getSchemes, agriEnhance } from '../lib/api'

const SAMPLE_QUERIES = [
  'What is the best time to plant tomatoes in Tamil Nadu?',
  'How to treat leaf curl disease in chili?',
  'Paddy cultivation tips for kharif season',
  'How to apply drip irrigation for cotton?',
]

const CROPS      = ['tomato','onion','rice','wheat','cotton','sugarcane','potato','chili','brinjal','groundnut','maize','soybean']
const SOIL_TYPES = ['Red loamy','Black cotton (vertisol)','Alluvial','Sandy loam','Clay loam','Laterite']
const SEASONS    = ['Kharif (June–Nov)','Rabi (Nov–Apr)','Zaid/Summer (Apr–Jun)','Year-round']
const COMMODITIES = ['tomato','onion','rice','wheat','cotton','sugarcane','potato']

export default function AgriPage() {
  const [tab, setTab] = useState('query')

  // Query tab
  const [query, setQuery]       = useState(SAMPLE_QUERIES[0])
  const [language, setLanguage] = useState('en')
  const [district, setDistrict] = useState('Coimbatore')
  const [state, setState]       = useState('Tamil Nadu')

  // Mandi tab
  const [commodity, setCommodity] = useState('tomato')
  const [schemeQ, setSchemeQ]     = useState('crop insurance')

  const genApi   = useApi()
  const mandi    = useApi()
  const weather  = useApi()
  const schemes  = useApi()

  // Yield Prediction tab
  const [yieldCrop, setYieldCrop]     = useState('tomato')
  const [yieldLoc, setYieldLoc]       = useState('Coimbatore, Tamil Nadu')
  const [acreage, setAcreage]         = useState('2 acres')
  const [season, setSeason]           = useState('Kharif (June–Nov)')
  const [soilType, setSoilType]       = useState('Red loamy')
  const [rainfall, setRainfall]       = useState('650')
  const yieldApi = useApi()

  // Market Intelligence tab
  const [mktCommodity, setMktComm]     = useState('tomato')
  const [mktRegion, setMktRegion]      = useState('Tamil Nadu')
  const [mktCurrPrice, setMktPrice]    = useState('₹25/kg at local mandi')
  const mktApi = useApi()

  return (
    <PageShell icon="🌾" title="AgriTech Domain Agent" subtitle="Feature 9 — Tamil/Hindi/English • Crop advisory, Mandi prices, Weather, Schemes, Yield prediction">
      <Tabs
        tabs={[
          { id: 'query',   label: 'AI Query',          icon: '🤖' },
          { id: 'mandi',   label: 'Mandi Prices',      icon: '💰' },
          { id: 'weather', label: 'Weather',            icon: '🌤️' },
          { id: 'schemes', label: 'Govt Schemes',       icon: '📜' },
          { id: 'yield',   label: 'Yield Prediction',   icon: '🌱' },
          { id: 'market',  label: 'Market Intelligence', icon: '📈' },
        ]}
        active={tab} onChange={setTab}
      />

      {tab === 'query' && (
        <TwoCol>
          <Card>
            <SectionHead title="Agricultural Query" sub="Ask in Tamil, Hindi, or English" />
            <Select label="Language" value={language} onChange={setLanguage}
              options={[{ label: 'English', value: 'en' }, { label: 'Hindi (हिंदी)', value: 'hi' }, { label: 'Tamil (தமிழ்)', value: 'ta' }]} />
            <div style={{ marginBottom: 10 }}>
              {SAMPLE_QUERIES.map(q => (
                <button key={q} onClick={() => setQuery(q)} style={{
                  display: 'block', width: '100%', textAlign: 'left', padding: '6px 10px', marginBottom: 4,
                  background: query === q ? 'rgba(99,102,241,0.15)' : '#0f1117', border: '1px solid #1e2535',
                  borderRadius: 6, color: query === q ? '#a5b4fc' : '#9ca3af', fontSize: 12, cursor: 'pointer',
                }}>{q}</button>
              ))}
            </div>
            <Input value={query} onChange={setQuery} placeholder="Custom query..." rows={3} label="Query" />
            <Btn onClick={() => genApi.call(() => agriQuery(query, language, district, state))} loading={genApi.loading}>
              🌾 Get Advisory
            </Btn>
          </Card>
          <ResultBox data={genApi.data} loading={genApi.loading} error={genApi.error} title="AgriTech Response" />
        </TwoCol>
      )}

      {tab === 'mandi' && (
        <TwoCol>
          <Card>
            <SectionHead title="Mandi (Market) Prices" sub="Agmarknet API — real prices per quintal" />
            <Select label="Commodity" value={commodity} onChange={setCommodity}
              options={COMMODITIES.map(c => ({ label: c.charAt(0).toUpperCase()+c.slice(1), value: c }))} />
            <Input label="State" value={state} onChange={setState} />
            <Input label="District (optional)" value={district} onChange={setDistrict} />
            <Btn onClick={() => mandi.call(() => getMandiPrices(commodity, state, district))} loading={mandi.loading}>
              💰 Fetch Prices
            </Btn>
          </Card>
          <ResultBox data={mandi.data} loading={mandi.loading} error={mandi.error} title="Mandi Prices" />
        </TwoCol>
      )}

      {tab === 'weather' && (
        <TwoCol>
          <Card>
            <SectionHead title="Weather Advisory" sub="OpenWeatherMap 5-day forecast + farming advisory" />
            <Input label="District" value={district} onChange={setDistrict} />
            <Input label="State"    value={state}    onChange={setState} />
            <Select label="Language" value={language} onChange={setLanguage}
              options={[{ label: 'English', value: 'en' }, { label: 'Hindi', value: 'hi' }, { label: 'Tamil', value: 'ta' }]} />
            <Btn onClick={() => weather.call(() => getWeather(district, state, language))} loading={weather.loading}>
              🌤️ Get Weather
            </Btn>
          </Card>
          <ResultBox data={weather.data} loading={weather.loading} error={weather.error} title="Weather Advisory" />
        </TwoCol>
      )}

      {tab === 'schemes' && (
        <TwoCol>
          <Card>
            <SectionHead title="Government Schemes" sub="PM-KISAN, PMFBY, KCC, PKVY, SMAM" />
            <Input label="Search (e.g. crop insurance, loan, organic)" value={schemeQ} onChange={setSchemeQ} />
            <div style={{ marginBottom: 14 }}>
              {['crop insurance','loan credit','organic farming','machinery subsidy','income support'].map(s => (
                <button key={s} onClick={() => setSchemeQ(s)} style={{
                  marginRight: 6, marginBottom: 6, padding: '4px 10px', borderRadius: 20,
                  background: '#1e2535', border: '1px solid #374151', color: '#9ca3af', fontSize: 11, cursor: 'pointer',
                }}>{s}</button>
              ))}
            </div>
            <Btn onClick={() => schemes.call(() => getSchemes(schemeQ))} loading={schemes.loading}>
              📜 Find Schemes
            </Btn>
          </Card>
          <ResultBox data={schemes.data} loading={schemes.loading} error={schemes.error} title="Matching Schemes" />
        </TwoCol>
      )}

      {/* ── Yield Prediction ── */}
      {tab === 'yield' && (
        <TwoCol>
          <Card>
            <SectionHead title="Yield Prediction & Optimization" sub="Crop + location + conditions → expected yield + input schedule + revenue" />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Select label="Crop" value={yieldCrop} onChange={setYieldCrop}
                options={CROPS.map(c => ({ label: c.charAt(0).toUpperCase()+c.slice(1), value: c }))} />
              <Select label="Season" value={season} onChange={setSeason}
                options={SEASONS.map(s => ({ label: s, value: s }))} />
            </div>
            <Input label="Location (District, State)" value={yieldLoc}   onChange={setYieldLoc} />
            <Input label="Land Area"                  value={acreage}    onChange={setAcreage} />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Select label="Soil Type" value={soilType} onChange={setSoilType}
                options={SOIL_TYPES.map(s => ({ label: s, value: s }))} />
              <Input label="Expected Rainfall (mm)" value={rainfall} onChange={setRainfall} type="number" />
            </div>
            <Btn
              onClick={() => yieldApi.call(() => agriEnhance('yield_prediction', {
                crop:       yieldCrop,
                location:   yieldLoc,
                acreage:    acreage,
                season:     season,
                soil_type:  soilType,
                rainfall_mm: rainfall,
              }, language))}
              loading={yieldApi.loading}
            >
              🌱 Predict Yield
            </Btn>
          </Card>
          <div>
            <Card style={{ marginBottom: 12 }}>
              <SectionHead title="Prediction Includes" sub="" />
              {['Expected yield (pessimistic/realistic/optimistic)','Fertilizer NPK schedule','Irrigation schedule','Pest & disease risk calendar','Revenue calculation at MSP','Break-even analysis'].map(i => (
                <div key={i} style={{ display: 'flex', gap: 8, padding: '4px 0', borderBottom: '1px solid #1e2535' }}>
                  <span style={{ color: '#22c55e', fontSize: 12 }}>✓</span>
                  <span style={{ color: '#9ca3af', fontSize: 12 }}>{i}</span>
                </div>
              ))}
            </Card>
            <ResultBox data={yieldApi.data ? { prediction: (yieldApi.data as any).result } : null} loading={yieldApi.loading} error={yieldApi.error} title="Yield Prediction Report" />
          </div>
        </TwoCol>
      )}

      {/* ── Market Intelligence ── */}
      {tab === 'market' && (
        <TwoCol>
          <Card>
            <SectionHead title="Market Intelligence" sub="Price trends, best selling time, top mandis, export opportunities" />
            <Select label="Commodity" value={mktCommodity} onChange={setMktComm}
              options={CROPS.map(c => ({ label: c.charAt(0).toUpperCase()+c.slice(1), value: c }))} />
            <Input label="Region / State"         value={mktRegion}    onChange={setMktRegion} />
            <Input label="Current Market Price"   value={mktCurrPrice} onChange={setMktPrice} />
            <Select label="Language" value={language} onChange={setLanguage}
              options={[{ label: 'English', value: 'en' }, { label: 'Hindi', value: 'hi' }, { label: 'Tamil', value: 'ta' }]} />
            <Btn
              onClick={() => mktApi.call(() => agriEnhance('market_intelligence', {
                commodity:     mktCommodity,
                region:        mktRegion,
                current_price: mktCurrPrice,
              }, language))}
              loading={mktApi.loading}
            >
              📈 Get Market Intelligence
            </Btn>
          </Card>
          <div>
            <Card style={{ marginBottom: 12 }}>
              <SectionHead title="Intelligence Includes" sub="" />
              {['Seasonal price trend analysis','Price drivers (supply/demand)','Best selling time recommendation','Top 5 nearby mandis + price range','Export opportunity assessment','Value-added product opportunities','3-month price outlook'].map(i => (
                <div key={i} style={{ display: 'flex', gap: 8, padding: '4px 0', borderBottom: '1px solid #1e2535' }}>
                  <span style={{ color: '#22c55e', fontSize: 12 }}>✓</span>
                  <span style={{ color: '#9ca3af', fontSize: 12 }}>{i}</span>
                </div>
              ))}
            </Card>
            <ResultBox data={mktApi.data ? { intelligence: (mktApi.data as any).result } : null} loading={mktApi.loading} error={mktApi.error} title="Market Intelligence Report" />
          </div>
        </TwoCol>
      )}
    </PageShell>
  )
}
