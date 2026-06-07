// frontend/src/pages/HealthcarePage.tsx — Healthcare / Clinic vertical
import { useState } from 'react'
import { PageShell, Card, Btn, Input, ResultBox, Tabs, TwoCol, useApi, SectionHead } from '../components/ui'
import { healthcareAction } from '../lib/api'

export default function HealthcarePage() {
  const [tab, setTab] = useState('intake')

  // Patient Intake
  const [pName, setPName]       = useState('Ramesh Kumar')
  const [pAgeSex, setPAgeSex]   = useState('54 / Male')
  const [pComplaint, setPComp]  = useState('Chest discomfort and breathlessness since morning')
  const [pNotes, setPNotes]     = useState('Known diabetic (10 yrs), on Metformin. Smoker. Pain radiating to left arm.')
  const [pVitals, setPVitals]   = useState('BP 150/95, HR 102, SpO2 96%, Temp 98.4F')
  const intakeApi = useApi()

  // Report Summary
  const [rType, setRType]       = useState('Complete Blood Count (CBC)')
  const [rText, setRText]       = useState('Hb 9.2 g/dL, WBC 14,500, Platelets 1.1L, ESR 48, Fasting glucose 168 mg/dL')
  const reportApi = useApi()

  // Prescription Notes
  const [dxDiag, setDxDiag]     = useState('Community-acquired pneumonia, mild')
  const [dxAgeSex, setDxAgeSex] = useState('34 / Female')
  const [dxWeight, setDxWeight] = useState('62 kg')
  const [dxAllergy, setDxAllergy] = useState('Penicillin allergy')
  const [dxComorb, setDxComorb] = useState('None')
  const rxApi = useApi()

  // Insurance Claim
  const [icName, setIcName]     = useState('Lakshmi Narayan')
  const [icInsurer, setIcIns]   = useState('Star Health (TPA: MediAssist)')
  const [icPolicy, setIcPolicy] = useState('SH-2291-4471')
  const [icDiag, setIcDiag]     = useState('Acute appendicitis')
  const [icTreat, setIcTreat]   = useState('Laparoscopic appendectomy')
  const [icAdm, setIcAdm]       = useState('2 days inpatient')
  const [icCost, setIcCost]     = useState('₹85,000')
  const claimApi = useApi()

  // Symptom Triage
  const [tSymptoms, setTSym]    = useState('Sudden severe headache, vomiting, neck stiffness')
  const [tDuration, setTDur]    = useState('3 hours')
  const [tAgeSex, setTAgeSex]   = useState('41 / Female')
  const [tVitals, setTVitals]   = useState('BP 160/100, Temp 101F')
  const triageApi = useApi()

  return (
    <PageShell icon="🏥" title="AI Healthcare Assistant" subtitle="Clinic documentation support — intake, reports, Rx notes, insurance claims, triage">
      <Tabs
        tabs={[
          { id: 'intake',  label: 'Patient Intake',   icon: '📝' },
          { id: 'report',  label: 'Report Summary',   icon: '🧪' },
          { id: 'rx',      label: 'Rx Notes',         icon: '💊' },
          { id: 'claim',   label: 'Insurance Claim',  icon: '🧾' },
          { id: 'triage',  label: 'Symptom Triage',   icon: '🚑' },
        ]}
        active={tab} onChange={setTab}
      />

      <div style={{ padding: '8px 12px', marginBottom: 12, background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 8, fontSize: 11, color: '#fca5a5' }}>
        ⚠️ Decision-support only — every output must be reviewed by a licensed physician. Not a substitute for professional medical advice.
      </div>

      {tab === 'intake' && (
        <TwoCol>
          <Card>
            <SectionHead title="Patient Intake → Clinical Summary" sub="Free-text intake → structured SOAP-style note with red-flag detection" />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Input label="Patient Name" value={pName} onChange={setPName} />
              <Input label="Age / Sex"    value={pAgeSex} onChange={setPAgeSex} />
            </div>
            <Input label="Chief Complaint" value={pComplaint} onChange={setPComp} />
            <Input label="History / Notes" value={pNotes} onChange={setPNotes} rows={3} />
            <Input label="Vitals" value={pVitals} onChange={setPVitals} />
            <Btn onClick={() => intakeApi.call(() => healthcareAction('patient_intake', { patient_name: pName, age_sex: pAgeSex, complaint: pComplaint, notes: pNotes, vitals: pVitals }))} loading={intakeApi.loading}>
              📝 Structure Intake
            </Btn>
          </Card>
          <ResultBox data={intakeApi.data ? { summary: (intakeApi.data as any).result } : null} loading={intakeApi.loading} error={intakeApi.error} title="Clinical Summary" />
        </TwoCol>
      )}

      {tab === 'report' && (
        <TwoCol>
          <Card>
            <SectionHead title="Lab/Diagnostic Report Summary" sub="Plain-language + clinical interpretation with abnormal-value flags" />
            <Input label="Report Type" value={rType} onChange={setRType} />
            <Input label="Report Values / Content" value={rText} onChange={setRText} rows={6} />
            <Btn onClick={() => reportApi.call(() => healthcareAction('report_summary', { report_type: rType, report_text: rText }))} loading={reportApi.loading}>
              🧪 Summarise Report
            </Btn>
          </Card>
          <ResultBox data={reportApi.data ? { summary: (reportApi.data as any).result } : null} loading={reportApi.loading} error={reportApi.error} title="Report Interpretation" />
        </TwoCol>
      )}

      {tab === 'rx' && (
        <TwoCol>
          <Card>
            <SectionHead title="Prescription Draft Notes" sub="Doctor-review draft — medications, doses, interactions, follow-up" />
            <Input label="Diagnosis / Impression" value={dxDiag} onChange={setDxDiag} />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Input label="Age / Sex" value={dxAgeSex} onChange={setDxAgeSex} />
              <Input label="Weight"    value={dxWeight} onChange={setDxWeight} />
            </div>
            <Input label="Known Allergies" value={dxAllergy} onChange={setDxAllergy} />
            <Input label="Comorbidities"   value={dxComorb} onChange={setDxComorb} />
            <Btn onClick={() => rxApi.call(() => healthcareAction('prescription_notes', { diagnosis: dxDiag, age_sex: dxAgeSex, weight: dxWeight, allergies: dxAllergy, comorbidities: dxComorb }))} loading={rxApi.loading}>
              💊 Draft Rx Notes
            </Btn>
          </Card>
          <ResultBox data={rxApi.data ? { prescription: (rxApi.data as any).result } : null} loading={rxApi.loading} error={rxApi.error} title="Prescription Draft" />
        </TwoCol>
      )}

      {tab === 'claim' && (
        <TwoCol>
          <Card>
            <SectionHead title="Insurance Claim Drafting" sub="Medical-necessity narrative + pre-auth letter + document checklist" />
            <Input label="Patient Name" value={icName} onChange={setIcName} />
            <Input label="Insurer / TPA" value={icInsurer} onChange={setIcIns} />
            <Input label="Policy No." value={icPolicy} onChange={setIcPolicy} />
            <Input label="Diagnosis" value={icDiag} onChange={setIcDiag} />
            <Input label="Treatment / Procedure" value={icTreat} onChange={setIcTreat} />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Input label="Hospitalisation" value={icAdm} onChange={setIcAdm} />
              <Input label="Estimated Cost" value={icCost} onChange={setIcCost} />
            </div>
            <Btn onClick={() => claimApi.call(() => healthcareAction('insurance_claim', { patient_name: icName, insurer: icInsurer, policy_no: icPolicy, diagnosis: icDiag, treatment: icTreat, admission: icAdm, cost: icCost }))} loading={claimApi.loading}>
              🧾 Draft Claim
            </Btn>
          </Card>
          <ResultBox data={claimApi.data ? { claim: (claimApi.data as any).result } : null} loading={claimApi.loading} error={claimApi.error} title="Insurance Claim Pack" />
        </TwoCol>
      )}

      {tab === 'triage' && (
        <TwoCol>
          <Card>
            <SectionHead title="Symptom Triage" sub="Front-desk / nurse triage — urgency level + next steps before doctor" />
            <Input label="Symptoms" value={tSymptoms} onChange={setTSym} rows={2} />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Input label="Duration" value={tDuration} onChange={setTDur} />
              <Input label="Age / Sex" value={tAgeSex} onChange={setTAgeSex} />
            </div>
            <Input label="Vitals (if any)" value={tVitals} onChange={setTVitals} />
            <Btn onClick={() => triageApi.call(() => healthcareAction('symptom_triage', { symptoms: tSymptoms, duration: tDuration, age_sex: tAgeSex, vitals: tVitals }))} loading={triageApi.loading}>
              🚑 Triage
            </Btn>
          </Card>
          <div>
            <Card style={{ marginBottom: 12 }}>
              <SectionHead title="Triage Levels" sub="" />
              {[['🔴','Emergency','Call ambulance / resuscitate now'],['🟠','Urgent','See doctor within the hour'],['🟡','Semi-urgent','Same-day appointment'],['🟢','Routine','Book a normal appointment']].map(([e,l,d]) => (
                <div key={l} style={{ display: 'flex', gap: 8, padding: '4px 0', borderBottom: '1px solid #1e2535' }}>
                  <span>{e}</span>
                  <span style={{ color: '#e2e8f0', fontSize: 12, fontWeight: 600, width: 90 }}>{l}</span>
                  <span style={{ color: '#6b7280', fontSize: 12 }}>{d}</span>
                </div>
              ))}
            </Card>
            <ResultBox data={triageApi.data ? { triage: (triageApi.data as any).result } : null} loading={triageApi.loading} error={triageApi.error} title="Triage Assessment" />
          </div>
        </TwoCol>
      )}
    </PageShell>
  )
}
