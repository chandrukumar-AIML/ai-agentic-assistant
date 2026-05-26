// frontend/src/pages/AgriPage.tsx — Feature 9: AgriTech
import { useState } from 'react'
import { PageShell, Card, Btn, Input, Select, ResultBox, Tabs, TwoCol, useApi, SectionHead } from '../components/ui'
import { agriQuery, getMandiPrices, getWeather, getSchemes } from '../lib/api'

const SAMPLE_QUERIES = [
  'What is the best time to plant tomatoes in Tamil Nadu?',
  'How to treat leaf curl disease in chili?',
  'Paddy cultivation tips for kharif season',
  'How to apply drip irrigation for cotton?',
]

export default function AgriPage() {
  const [tab, setTab] = useState('query')
  const [query, setQuery]       = useState(SAMPLE_QUERIES[0])
  const [language, setLanguage] = useState('en')
  const [district, setDistrict] = useState('Coimbatore')
  const [state, setState]       = useState('Tamil Nadu')
  const [commodity, setCommodity] = useState('tomato')
  const [schemeQ, setSchemeQ]   = useState('crop insurance')

  const genApi  = useApi()
  const mandi   = useApi()
  const weather = useApi()
  const schemes = useApi()

  return (
    <PageShell icon="🌾" title="AgriTech Domain Agent" subtitle="Feature 9 — Tamil/Hindi/English • Crop disease, Mandi prices, Weather, Govt schemes">
      <Tabs
        tabs={[
          { id: 'query',   label: 'AI Query',       icon: '🤖' },
          { id: 'mandi',   label: 'Mandi Prices',   icon: '💰' },
          { id: 'weather', label: 'Weather',         icon: '🌤️' },
          { id: 'schemes', label: 'Govt Schemes',   icon: '📜' },
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
              options={['tomato','onion','rice','wheat','cotton','sugarcane','potato'].map(c => ({ label: c.charAt(0).toUpperCase()+c.slice(1), value: c }))} />
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
            <Input label="State" value={state} onChange={setState} />
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
                  background: '#1e2535', border: '1px solid #374151',
                  color: '#9ca3af', fontSize: 11, cursor: 'pointer',
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
    </PageShell>
  )
}
