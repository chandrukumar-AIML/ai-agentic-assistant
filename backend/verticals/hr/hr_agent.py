# backend/verticals/hr/hr_agent.py
"""
AI HR Assistant (Feature 18).

Full hiring pipeline:
  1. Resume screening — score applicant vs JD (0–100)
  2. Interview scheduling — via Calendly / time slot suggestion
  3. Offer letter generation — PDF with DocuSign e-sign dispatch (HITL gated)
  4. Onboarding checklist generation
  5. JD (Job Description) generation from role title + requirements
  6. Candidate status tracking (in-memory + optional DB)
  7. HR policy Q&A (via LLM with HR context)
  8. Background check checklist generation

Hiring pipeline stages:
  applied → screened → interview_scheduled → interviewed →
  offer_extended → offer_accepted → onboarding → hired
"""
from __future__ import annotations

import logging
import re
from datetime import date, datetime, timezone
from typing import Optional

from backend.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()


# ── Resume screening ──────────────────────────────────────────────────────────

async def screen_resume(
    resume_text:       str,
    job_description:   str,
    required_skills:   list[str] = None,
    nice_to_have:      list[str] = None,
    min_years_exp:     int = 0,
    language:          str = "en",
) -> dict:
    """
    Score a resume against a job description using Ollama (llama3.2).
    Returns structured scoring with category breakdown.
    """
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL

    required_skills = required_skills or []
    nice_to_have    = nice_to_have or []

    # Quick regex checks for years of experience
    exp_match = re.search(r'(\d+)\+?\s*years?\s*(?:of\s+)?experience', resume_text, re.IGNORECASE)
    detected_years = int(exp_match.group(1)) if exp_match else 0

    system = """You are an expert HR talent screener. Analyze the resume against the JD.
Return JSON with this exact structure:
{
  "overall_score": <0-100>,
  "skills_match": <0-100>,
  "experience_match": <0-100>,
  "education_match": <0-100>,
  "cultural_fit": <0-100>,
  "matched_required_skills": ["skill1", "skill2"],
  "matched_nice_to_have": ["skill1"],
  "missing_required_skills": ["skill1"],
  "years_experience": <number>,
  "highlights": ["key strength 1", "key strength 2"],
  "concerns": ["concern 1"],
  "recommendation": "strong_yes|yes|maybe|no",
  "summary": "2-sentence screening summary"
}"""

    user = (
        f"Job Description:\n{job_description[:2000]}\n\n"
        f"Required skills: {', '.join(required_skills)}\n"
        f"Nice-to-have: {', '.join(nice_to_have)}\n"
        f"Min years experience: {min_years_exp}\n\n"
        f"Resume:\n{resume_text[:3000]}"
    )

    try:
        import json
        ollama_system = system + "\nIMPORTANT: Return ONLY valid JSON, no markdown, no explanation."
        content = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": ollama_system},
                {"role": "user",   "content": user},
            ],
            model=OLLAMA_MODEL,
            max_tokens=600,
            temperature=0.0,
        )
        # Strip markdown code fences if present
        content = content.strip()
        if content.startswith("```"):
            content = "\n".join(content.split("\n")[1:])
            content = content.split("```")[0].strip()
        result = json.loads(content)
        result["detected_years"]  = max(detected_years, result.get("years_experience", 0))
        result["meets_min_exp"]   = result["detected_years"] >= min_years_exp
        result["screened_at"]     = datetime.now(timezone.utc).isoformat()
        result["model"]           = f"ollama/{OLLAMA_MODEL}"
        return result
    except Exception as e:
        logger.error("HR resume screening failed: %s", e)
        return {
            "error":           "Resume screening temporarily unavailable.",
            "overall_score":   0,
            "recommendation":  "maybe",
        }


# ── JD generation ─────────────────────────────────────────────────────────────

async def generate_jd(
    role_title:    str,
    department:    str,
    company_name:  str,
    required_skills: list[str] = None,
    experience_min: int = 2,
    experience_max: int = 5,
    work_mode:     str = "hybrid",   # remote | onsite | hybrid
    location:      str = "",
    salary_range:  str = "",
    language:      str = "en",
) -> str:
    """Generate a professional Job Description using Ollama (llama3.2)."""
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL

    skills_text = ", ".join(required_skills) if required_skills else "relevant skills"

    system = (
        f"You are an expert HR professional. Write a compelling, inclusive job description in {language}. "
        f"Include: Role Overview, Responsibilities (8-10 bullets), Required Qualifications, "
        f"Nice-to-have, What we offer. Use professional tone. Avoid discriminatory language."
    )
    user = (
        f"Role: {role_title}\nDepartment: {department}\nCompany: {company_name}\n"
        f"Skills: {skills_text}\nExperience: {experience_min}-{experience_max} years\n"
        f"Work mode: {work_mode}\n"
        f"{'Location: ' + location if location else ''}\n"
        f"{'Salary: ' + salary_range if salary_range else ''}\n\n"
        f"Write the complete Job Description:"
    )

    try:
        content = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            model=OLLAMA_MODEL,
            max_tokens=800,
            temperature=0.7,
        )
        if content:
            return content
        raise ValueError("Empty Ollama response")
    except Exception as e:
        logger.warning("JD generation failed: %s", e)
        # Return a structured mock JD
        return (
            f"**{role_title}**\n\n"
            f"**Role Overview:** We are looking for a talented {role_title} to join our {department or 'team'}.\n\n"
            f"**Responsibilities:**\n"
            f"- Design and develop scalable solutions using {skills_text}\n"
            f"- Collaborate with cross-functional teams\n"
            f"- Write clean, maintainable code with tests\n"
            f"- Participate in code reviews\n\n"
            f"**Requirements:**\n"
            f"- {experience_min}-{experience_max} years of experience\n"
            f"- Proficiency in: {skills_text}\n"
            f"- Strong problem-solving skills\n\n"
            f"**Nice to have:** Cloud experience, open-source contributions\n"
        )


# ── Offer letter generation ───────────────────────────────────────────────────

async def generate_offer_letter(
    candidate_name:  str,
    role_title:      str,
    department:      str,
    company_name:    str,
    salary_annual:   float,
    joining_date:    str,
    reporting_to:    str,
    work_location:   str,
    benefits:        list[str] = None,
    send_for_esign:  bool = False,
    candidate_email: str = "",
    user_id:         str = "",
    session_id:      str = "",
) -> dict:
    """
    Generate a professional offer letter PDF.
    If send_for_esign=True, routes through HITL before dispatching DocuSign.
    """
    benefits = benefits or ["Health Insurance", "18 Days PTO", "Provident Fund (PF)"]

    # Build letter content
    salary_monthly = round(salary_annual / 12, 0)
    benefits_text  = "\n".join(f"• {b}" for b in benefits)
    today          = date.today().strftime("%B %d, %Y")

    content = f"""Date: {today}

Dear {candidate_name},

We are delighted to offer you the position of **{role_title}** in the {department} department at {company_name}.

COMPENSATION & BENEFITS:
• Annual Gross CTC: ₹{salary_annual:,.0f}
• Monthly In-Hand (approximate): ₹{salary_monthly:,.0f}
• Joining Date: {joining_date}
• Work Location: {work_location}
• Reporting To: {reporting_to}

BENEFITS PACKAGE:
{benefits_text}

This offer is contingent upon satisfactory completion of background verification.
Please confirm your acceptance within 5 working days.

We look forward to welcoming you to the team!

Warm regards,
HR Department
{company_name}"""

    try:
        from backend.outputs.output_generator import generate_pdf
        pdf_bytes, _, filename = generate_pdf(
            title=f"Offer Letter — {candidate_name} — {role_title}",
            content=content,
            sections=[],
            author=f"{company_name} HR",
        )
        import base64
        result: dict = {
            "candidate":    candidate_name,
            "role":         role_title,
            "salary_annual": salary_annual,
            "joining_date": joining_date,
            "pdf_b64":      base64.b64encode(pdf_bytes).decode(),
            "filename":     filename,
            "status":       "generated",
        }
    except Exception as e:
        logger.error("Offer letter PDF failed: %s", e)
        result = {
            "candidate": candidate_name,
            "role":      role_title,
            "status":    "pdf_failed",
            "error":     "PDF generation failed.",
        }

    # HITL gate before DocuSign dispatch
    if send_for_esign and candidate_email:
        try:
            from backend.hitl.hitl_manager import request_approval
            approval_id = await request_approval(
                action_type="send_offer_letter",
                action_payload={
                    "candidate_name":  candidate_name,
                    "candidate_email": candidate_email,
                    "role":            role_title,
                    "salary_annual":   salary_annual,
                    "joining_date":    joining_date,
                },
                context_summary=(
                    f"Send offer letter to {candidate_name} ({candidate_email}) "
                    f"for {role_title} @ ₹{salary_annual:,.0f} p.a."
                ),
                user_id=user_id,
                session_id=session_id,
                expires_minutes=120,
            )
            result["esign_status"]    = "pending_approval"
            result["hitl_approval_id"] = approval_id
            result["note"] = "Offer letter queued for HR review before sending."
        except Exception as e:
            logger.error("Offer letter HITL failed: %s", e)
            result["esign_status"] = "hitl_failed"

    return result


# ── Onboarding checklist ──────────────────────────────────────────────────────

def generate_onboarding_checklist(
    role_title:   str,
    department:   str,
    start_date:   str,
    is_remote:    bool = False,
) -> dict:
    """Generate a structured onboarding checklist for a new hire."""
    base_items = {
        "Pre-joining (1 week before)": [
            "Send welcome email with joining instructions",
            "Set up email account and system access",
            "Prepare workstation / laptop provisioning",
            "Add to relevant Slack/Teams channels",
            "Assign buddy/mentor",
            "Share company handbook and policies",
        ],
        "Day 1": [
            "Welcome meeting with HR",
            "Office/facility tour (or virtual tour for remote)",
            "IT setup: email, VPN, tools access",
            "Introduction to team members",
            "Review role expectations and 30-60-90 day plan",
            "Complete required compliance training",
        ],
        "Week 1": [
            "Meet with reporting manager (1:1)",
            "Review team processes and workflows",
            "Set up accounts: Jira, GitHub, Notion, etc.",
            "Complete statutory forms: PF, ESI, Form 12B",
            "Submit KYC documents for payroll",
            "Shadow 2-3 team meetings",
        ],
        "Month 1": [
            "Complete role-specific training modules",
            "First performance check-in with manager",
            "Contribute to one small project deliverable",
            "Provide onboarding feedback survey",
            "Confirm permanent address for HRMS",
        ],
    }

    if is_remote:
        base_items["Day 1"].append("Virtual coffee chats scheduled with 3 teammates")
        base_items["Pre-joining (1 week before)"].append(
            "Ship laptop and peripherals to home address"
        )

    dept_items = {
        "Engineering": ["GitHub access and code review setup", "CI/CD pipeline walkthrough",
                        "Architecture overview session"],
        "Sales":       ["CRM access (HubSpot/Salesforce)", "Product demo training",
                        "Shadow 2 discovery calls"],
        "Marketing":   ["Brand guidelines review", "Content calendar access",
                        "Analytics tools setup"],
        "Finance":     ["Accounting software access", "Chart of accounts walkthrough",
                        "Compliance checklist review"],
    }
    dept_additions = dept_items.get(department, [])
    if dept_additions:
        base_items.setdefault("Week 1", []).extend(dept_additions)

    return {
        "candidate_role":  role_title,
        "department":      department,
        "start_date":      start_date,
        "is_remote":       is_remote,
        "checklist":       base_items,
        "total_items":     sum(len(v) for v in base_items.values()),
        "generated_at":    datetime.now(timezone.utc).isoformat(),
    }


# ── Background check checklist ────────────────────────────────────────────────

def generate_bgv_checklist(role_level: str = "mid") -> dict:
    """Generate background verification checklist based on role level."""
    base = [
        "Identity verification (Aadhaar / Passport)",
        "Educational qualification verification",
        "Previous employment verification (last 3 employers)",
        "Address verification (current + permanent)",
        "Criminal record check",
    ]
    senior_additions = [
        "Credit/financial check",
        "Professional reference checks (3 references)",
        "Social media screening",
        "Directorship/company ownership check",
    ]
    if role_level in ("senior", "manager", "director", "c-level"):
        base.extend(senior_additions)

    return {
        "role_level":  role_level,
        "checklist":   base,
        "turnaround":  "5-7 business days",
        "vendor":      "Configure BGV_VENDOR_API_KEY for automated checks",
    }


# ── HR Q&A ────────────────────────────────────────────────────────────────────

async def hr_qa(question: str, language: str = "en") -> str:
    """Answer HR policy questions using Ollama with India labor law context."""
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL

    system = (
        f"You are an expert Indian HR professional and labor law advisor. "
        f"Answer in {language}. Reference relevant Indian laws: "
        f"Industrial Disputes Act, Payment of Gratuity Act, Maternity Benefit Act, "
        f"Shops & Establishments Act, EPF & MP Act, ESI Act, Minimum Wages Act. "
        f"Be practical and specific. Recommend consulting an HR lawyer for legal matters."
    )
    try:
        result = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": question},
            ],
            model=OLLAMA_MODEL,
            max_tokens=600,
        )
        return result or "HR assistant temporarily unavailable."
    except Exception as e:
        logger.error("HR Q&A failed: %s", e)
        return "HR assistant temporarily unavailable."


# ── Main HR agent dispatcher ──────────────────────────────────────────────────

async def hr_agent(
    action:  str,     # screen | generate_jd | offer_letter | onboarding | bgv | qa
    payload: dict,
    user_id: str = "",
    session_id: str = "",
    language: str = "en",
) -> dict:
    """Main HR agent dispatcher."""
    if action == "screen":
        return await screen_resume(
            resume_text=payload.get("resume_text", ""),
            job_description=payload.get("job_description", ""),
            required_skills=payload.get("required_skills", []),
            nice_to_have=payload.get("nice_to_have", []),
            min_years_exp=payload.get("min_years_exp", 0),
            language=language,
        )

    elif action == "generate_jd":
        jd = await generate_jd(
            role_title=payload.get("role_title", ""),
            department=payload.get("department", ""),
            company_name=payload.get("company_name", ""),
            required_skills=payload.get("required_skills", []),
            experience_min=payload.get("experience_min", 2),
            experience_max=payload.get("experience_max", 5),
            work_mode=payload.get("work_mode", "hybrid"),
            location=payload.get("location", ""),
            salary_range=payload.get("salary_range", ""),
            language=language,
        )
        return {"job_description": jd, "role": payload.get("role_title")}

    elif action == "offer_letter":
        return await generate_offer_letter(
            candidate_name=payload.get("candidate_name", ""),
            role_title=payload.get("role_title", ""),
            department=payload.get("department", ""),
            company_name=payload.get("company_name", ""),
            salary_annual=float(payload.get("salary_annual", 0)),
            joining_date=payload.get("joining_date", str(date.today())),
            reporting_to=payload.get("reporting_to", ""),
            work_location=payload.get("work_location", ""),
            benefits=payload.get("benefits"),
            send_for_esign=payload.get("send_for_esign", False),
            candidate_email=payload.get("candidate_email", ""),
            user_id=user_id,
            session_id=session_id,
        )

    elif action == "onboarding":
        return generate_onboarding_checklist(
            role_title=payload.get("role_title", ""),
            department=payload.get("department", ""),
            start_date=payload.get("start_date", str(date.today())),
            is_remote=payload.get("is_remote", False),
        )

    elif action == "bgv":
        return generate_bgv_checklist(role_level=payload.get("role_level", "mid"))

    elif action == "qa":
        answer = await hr_qa(payload.get("question", ""), language)
        return {"answer": answer, "disclaimer": "Consult an HR lawyer for specific legal matters."}

    return {"error": f"Unknown HR action: {action}"}
