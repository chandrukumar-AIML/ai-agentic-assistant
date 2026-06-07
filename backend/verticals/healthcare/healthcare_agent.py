"""
Healthcare / Clinic Vertical — AI assistant for clinics and small hospitals.

Actions:
  patient_intake     — Structure free-text intake into a clean clinical summary
  report_summary     — Plain-language summary of a lab/diagnostic report
  prescription_notes — Draft prescription + dosage notes from a diagnosis
  insurance_claim    — Draft a cashless/reimbursement insurance claim narrative
  symptom_triage     — Triage symptoms into urgency level + next steps

DISCLAIMER: All output is decision-support only and must be reviewed by a
licensed medical practitioner. No content here is a substitute for professional
medical advice, diagnosis, or treatment.
"""
from __future__ import annotations

import logging
import time

from backend.llm.router import llm_router

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a clinical documentation assistant supporting licensed
doctors and clinic staff in India. You produce clear, structured, professional
medical documentation. You ALWAYS:
- Use standard clinical structure (SOAP, ICD-10 hints where useful).
- Flag any red-flag/emergency findings prominently at the top.
- End every output with: "⚠️ Decision-support only — must be verified by a licensed physician."
You NEVER give a definitive diagnosis as fact; you phrase clinical impressions as
"likely / consider / rule out". You are concise and avoid hallucinating drug doses —
when unsure about a dose you say "confirm dose per local formulary"."""

_DISCLAIMER = "⚠️ Decision-support only — must be verified by a licensed physician."


async def _llm(prompt: str, max_tokens: int = 700) -> str:
    text, _ = await llm_router.complete(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.2,
        max_tokens=max_tokens,
    )
    return text


async def patient_intake(payload: dict) -> dict:
    prompt = f"""Convert this patient intake into a structured clinical summary.

Patient: {payload.get('patient_name', 'Patient')} | Age/Sex: {payload.get('age_sex', 'N/A')}
Chief complaint: {payload.get('complaint', '')}
History / notes (free text): {payload.get('notes', '')}
Vitals: {payload.get('vitals', 'not recorded')}

Produce:
1. **Chief Complaint** (one line)
2. **History of Present Illness** (structured)
3. **Relevant Past History / Allergies / Medications**
4. **Vitals Summary** with any abnormal value flagged
5. **Provisional Impression** (likely / consider / rule out — with ICD-10 hints)
6. **Suggested Investigations**
7. **🚩 Red Flags** (emergency signs, if any)"""
    result = await _llm(prompt, 700)
    return {"action": "patient_intake", "result": result, "disclaimer": _DISCLAIMER}


async def report_summary(payload: dict) -> dict:
    prompt = f"""Summarise this medical/lab report in plain language a patient can understand,
then give a clinician-facing interpretation.

Report type: {payload.get('report_type', 'Lab report')}
Report content / values:
{payload.get('report_text', '')[:3000]}

Produce:
1. **Plain-language summary** (for the patient, 3-4 sentences)
2. **Abnormal values table** (Value | Result | Normal range | Flag)
3. **Clinical interpretation** (consider / rule out)
4. **Recommended follow-up**
5. **🚩 Any value needing urgent attention**"""
    result = await _llm(prompt, 700)
    return {"action": "report_summary", "result": result, "disclaimer": _DISCLAIMER}


async def prescription_notes(payload: dict) -> dict:
    prompt = f"""Draft prescription guidance notes for the treating doctor to review and edit.

Diagnosis / impression: {payload.get('diagnosis', '')}
Patient: Age/Sex {payload.get('age_sex', 'N/A')} | Weight: {payload.get('weight', 'N/A')}
Known allergies: {payload.get('allergies', 'none stated')}
Comorbidities: {payload.get('comorbidities', 'none stated')}

Produce a DRAFT (doctor must verify):
1. **Suggested medications** (Drug | Class | Typical adult dose | Frequency | Duration)
   - For any dose you are unsure of, write "confirm dose per local formulary".
2. **Drug interaction / allergy cautions**
3. **Non-pharmacological advice**
4. **Follow-up plan & warning signs to return**"""
    result = await _llm(prompt, 700)
    return {"action": "prescription_notes", "result": result, "disclaimer": _DISCLAIMER}


async def insurance_claim(payload: dict) -> dict:
    prompt = f"""Draft an Indian health-insurance claim narrative (cashless / reimbursement).

Patient: {payload.get('patient_name', 'Patient')}
Insurer / TPA: {payload.get('insurer', '')}
Policy no: {payload.get('policy_no', '')}
Diagnosis: {payload.get('diagnosis', '')}
Procedure / treatment: {payload.get('treatment', '')}
Hospitalisation: {payload.get('admission', 'N/A')} | Estimated cost: {payload.get('cost', 'N/A')}

Produce:
1. **Clinical justification narrative** (medical necessity, insurer-ready language)
2. **Document checklist** required for this claim
3. **Suggested ICD-10 & procedure codes**
4. **Pre-authorisation cover letter** (formal, addressed to TPA)
5. **Common rejection reasons to pre-empt**"""
    result = await _llm(prompt, 800)
    return {"action": "insurance_claim", "result": result, "disclaimer": _DISCLAIMER}


async def symptom_triage(payload: dict) -> dict:
    prompt = f"""Triage these symptoms for a front-desk / nurse before the doctor sees the patient.

Symptoms: {payload.get('symptoms', '')}
Duration: {payload.get('duration', 'N/A')}
Patient: Age/Sex {payload.get('age_sex', 'N/A')}
Vitals (if any): {payload.get('vitals', 'not recorded')}

Produce:
1. **Triage level**: 🔴 Emergency / 🟠 Urgent / 🟡 Semi-urgent / 🟢 Routine — with reason
2. **Recommended action** (call ambulance / see doctor now / book appointment / self-care)
3. **Likely systems involved** (consider / rule out)
4. **Questions the nurse should ask next**
5. **🚩 Red-flag symptoms to watch for**"""
    result = await _llm(prompt, 600)
    return {"action": "symptom_triage", "result": result, "disclaimer": _DISCLAIMER}


async def healthcare_agent(action: str, payload: dict, language: str = "en") -> dict:
    """Main Healthcare agent dispatcher."""
    action = (action or "").lower().strip()
    handlers = {
        "patient_intake":     patient_intake,
        "report_summary":     report_summary,
        "prescription_notes": prescription_notes,
        "insurance_claim":    insurance_claim,
        "symptom_triage":     symptom_triage,
    }
    handler = handlers.get(action)
    if not handler:
        return {"error": f"Unknown action '{action}'. Valid: {', '.join(handlers)}"}

    start  = time.monotonic()
    result = await handler(payload)
    result["latency_ms"] = round((time.monotonic() - start) * 1000)
    return result
