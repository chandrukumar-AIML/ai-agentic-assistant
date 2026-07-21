"""Customer Support Agent — WhatsApp-first, India SMB focused."""
from __future__ import annotations
import json
from datetime import datetime


def _llm(prompt: str, system: str = "") -> str:
    from backend.verticals.social_media.social_agent import ollama_chat_completion
    return ollama_chat_completion(prompt, system=system)


LANG_LABELS = {
    "en": {"yes": "Yes", "no": "No", "na": "N/A"},
    "ta": {"yes": "ஆம்", "no": "இல்லை", "na": "பொருந்தாது"},
    "hi": {"yes": "हाँ", "no": "नहीं", "na": "लागू नहीं"},
}

LANG_SYSTEM = {
    "en": "You are a friendly and professional customer support AI assistant. Be concise and helpful.",
    "ta": "நீங்கள் ஒரு நட்பான மற்றும் தொழில்முறை வாடிக்கையாளர் ஆதரவு AI உதவியாளர். தமிழில் பதிலளியுங்கள்.",
    "hi": "आप एक मित्रवत और पेशेवर ग्राहक सहायता AI सहायक हैं। हिंदी में उत्तर दें।",
}

ESCALATION_TRIGGERS = [
    "refund", "legal", "court", "fraud", "cheat", "scam", "police", "complaint",
    "angry", "frustrated", "escalate", "manager", "supervisor", "worst", "useless",
    "திரும்ப பணம்", "கோர்ட்", "மோசடி", "கோபம்",
    "वापसी", "धोखा", "कोर्ट", "गुस्सा",
]

SENTIMENT_MAP = {
    "positive": {"emoji": "😊", "color": "#10b981", "label": "Happy"},
    "neutral":  {"emoji": "😐", "color": "#3b82f6", "label": "Neutral"},
    "negative": {"emoji": "😤", "color": "#ef4444", "label": "Frustrated"},
    "critical": {"emoji": "🚨", "color": "#dc2626", "label": "Escalate Now"},
}


async def faq_bot(query: str, business_name: str, business_type: str, faq_context: str, language: str) -> dict:
    sys_prompt = LANG_SYSTEM.get(language, LANG_SYSTEM["en"])
    prompt = f"""You are the AI customer support bot for "{business_name}" ({business_type}).

FAQ / Knowledge Context:
{faq_context if faq_context else "No specific FAQ provided. Use general knowledge for this business type."}

Customer Question: {query}

Provide a helpful, accurate, friendly answer in 2-4 sentences. If you cannot answer from the context, say so politely and suggest contacting support directly."""

    answer = _llm(prompt, system=sys_prompt)

    # Check if escalation needed
    needs_escalation = any(t.lower() in query.lower() for t in ESCALATION_TRIGGERS)

    return {
        "answer": answer,
        "needs_escalation": needs_escalation,
        "escalation_reason": "Query contains sensitive keywords" if needs_escalation else None,
        "confidence": "high" if faq_context else "medium",
        "language": language,
    }


async def qualify_lead(
    customer_name: str, business_type: str, responses: dict, language: str
) -> dict:
    sys_prompt = LANG_SYSTEM.get(language, LANG_SYSTEM["en"])

    # Build qualification summary
    resp_text = "\n".join(f"- {k}: {v}" for k, v in responses.items())
    prompt = f"""Analyze this sales lead for a {business_type} business:

Customer: {customer_name}
Responses:
{resp_text}

Score this lead:
1. Lead quality: Hot / Warm / Cold
2. Estimated budget fit: Good / Maybe / Poor
3. Decision timeline: Immediate / 1-3 months / Long-term
4. Key buying signals (list 2-3)
5. Recommended next action (1 sentence)
6. Draft a short follow-up WhatsApp message to send (under 60 words, friendly, in the same language as this prompt)

Format as JSON with keys: quality, budget_fit, timeline, buying_signals, next_action, whatsapp_followup"""

    raw = _llm(prompt, system=sys_prompt)
    try:
        start = raw.index("{")
        end = raw.rindex("}") + 1
        result = json.loads(raw[start:end])
    except Exception:
        result = {
            "quality": "Warm",
            "budget_fit": "Maybe",
            "timeline": "1-3 months",
            "buying_signals": ["Showed interest", "Provided contact"],
            "next_action": "Schedule a demo call",
            "whatsapp_followup": f"Hi {customer_name}! Thanks for your interest. Can we schedule a quick call to discuss your needs?",
        }

    result["customer_name"] = customer_name
    result["language"] = language
    return result


async def draft_whatsapp(
    message_type: str, customer_name: str, business_name: str,
    context: str, language: str
) -> dict:
    sys_prompt = LANG_SYSTEM.get(language, LANG_SYSTEM["en"])

    type_instructions = {
        "welcome":        "Write a warm welcome message for a new customer",
        "follow_up":      "Write a friendly follow-up message after a purchase/inquiry",
        "payment_reminder": "Write a polite payment reminder (not aggressive)",
        "delivery_update": "Write a delivery/order status update message",
        "feedback_request": "Write a message requesting feedback/review after service",
        "apology":        "Write a sincere apology message for a service issue",
        "offer":          "Write a promotional offer message (not spammy)",
        "reactivation":   "Write a re-engagement message for an inactive customer",
    }

    instruction = type_instructions.get(message_type, f"Write a {message_type} message")

    prompt = f"""{instruction} for {business_name}.

Customer Name: {customer_name}
Context / Details: {context if context else "Standard message, no special context"}

Requirements:
- WhatsApp-friendly format (use *bold* for key info, emojis tastefully)
- Under 150 words
- Warm but professional tone
- End with a clear call to action
- Language: {"Tamil" if language == "ta" else "Hindi" if language == "hi" else "English"}

Write only the message, no explanation."""

    message = _llm(prompt, system=sys_prompt)

    return {
        "message": message,
        "message_type": message_type,
        "customer_name": customer_name,
        "channel": "WhatsApp",
        "word_count": len(message.split()),
        "language": language,
    }


async def analyze_sentiment(text: str, customer_name: str, language: str) -> dict:
    sys_prompt = "You are a sentiment analysis expert for customer support."
    prompt = f"""Analyze the sentiment of this customer message and classify it:

Customer: {customer_name}
Message: {text}

Respond ONLY with JSON:
{{
  "sentiment": "positive|neutral|negative|critical",
  "score": 0-100 (100 = most positive),
  "emotions": ["list", "of", "emotions"],
  "key_issues": ["main", "complaints", "or", "praises"],
  "urgency": "low|medium|high|critical",
  "suggested_tone": "how to respond (empathetic/apologetic/celebratory/etc)",
  "needs_human": true|false,
  "summary": "one sentence summary"
}}"""

    raw = _llm(prompt, system=sys_prompt)
    try:
        start = raw.index("{")
        end = raw.rindex("}") + 1
        result = json.loads(raw[start:end])
    except Exception:
        result = {
            "sentiment": "neutral",
            "score": 50,
            "emotions": ["unclear"],
            "key_issues": ["Unable to parse"],
            "urgency": "medium",
            "suggested_tone": "empathetic",
            "needs_human": False,
            "summary": "Customer sent a message requiring attention.",
        }

    sentiment_info = SENTIMENT_MAP.get(result.get("sentiment", "neutral"), SENTIMENT_MAP["neutral"])
    result["emoji"] = sentiment_info["emoji"]
    result["color"] = sentiment_info["color"]
    result["display_label"] = sentiment_info["label"]
    result["customer_name"] = customer_name
    result["language"] = language
    return result


async def handle_complaint(
    complaint: str, customer_name: str, order_id: str,
    business_name: str, category: str, language: str
) -> dict:
    sys_prompt = LANG_SYSTEM.get(language, LANG_SYSTEM["en"])

    prompt = f"""You are the customer support manager for {business_name}.

Customer: {customer_name}
Order/Reference: {order_id if order_id else "Not provided"}
Complaint Category: {category}
Complaint: {complaint}

Provide:
1. An empathetic acknowledgment (2-3 sentences)
2. The resolution steps you will take (3-5 bullet points)
3. Timeline for resolution
4. A final reassurance statement
5. Escalation required: Yes/No and reason

Format as JSON with keys: acknowledgment, resolution_steps, timeline, reassurance, escalate, escalate_reason"""

    raw = _llm(prompt, system=sys_prompt)
    try:
        start = raw.index("{")
        end = raw.rindex("}") + 1
        result = json.loads(raw[start:end])
    except Exception:
        result = {
            "acknowledgment": f"Dear {customer_name}, we sincerely apologize for the inconvenience. We take all complaints seriously.",
            "resolution_steps": ["Reviewing your case", "Contacting relevant team", "Following up within 24 hours"],
            "timeline": "24-48 hours",
            "reassurance": "We value your business and will resolve this to your satisfaction.",
            "escalate": category in ["refund", "legal", "fraud"],
            "escalate_reason": "Sensitive category" if category in ["refund", "legal", "fraud"] else None,
        }

    result["customer_name"] = customer_name
    result["order_id"] = order_id
    result["category"] = category
    result["language"] = language
    return result


async def summarize_ticket(
    conversation: str, customer_name: str, language: str
) -> dict:
    sys_prompt = "You are an expert at summarizing customer support conversations for internal handoffs."

    prompt = f"""Summarize this customer support conversation for an agent handoff:

Customer: {customer_name}
Conversation:
{conversation}

Provide a structured summary as JSON:
{{
  "issue_summary": "2-3 sentence summary of the core issue",
  "customer_mood": "positive|neutral|frustrated|angry",
  "what_was_tried": ["list", "of", "steps", "already", "taken"],
  "what_is_needed": ["list", "of", "pending", "actions"],
  "priority": "low|medium|high|critical",
  "category": "billing|technical|delivery|product|general",
  "suggested_resolution": "recommended next step",
  "tags": ["keyword", "tags"]
}}"""

    raw = _llm(prompt, system=sys_prompt)
    try:
        start = raw.index("{")
        end = raw.rindex("}") + 1
        result = json.loads(raw[start:end])
    except Exception:
        result = {
            "issue_summary": f"Customer {customer_name} reported an issue requiring follow-up.",
            "customer_mood": "neutral",
            "what_was_tried": ["Initial contact received"],
            "what_is_needed": ["Agent review", "Resolution"],
            "priority": "medium",
            "category": "general",
            "suggested_resolution": "Review and respond within SLA",
            "tags": ["support"],
        }

    result["customer_name"] = customer_name
    result["language"] = language
    result["summarized_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    return result


async def generate_response_template(
    scenario: str, business_type: str, tone: str, language: str
) -> dict:
    sys_prompt = LANG_SYSTEM.get(language, LANG_SYSTEM["en"])

    prompt = f"""Create 3 variations of a customer support response template for:

Business Type: {business_type}
Scenario: {scenario}
Tone: {tone} (formal/friendly/empathetic/direct)
Language: {"Tamil" if language == "ta" else "Hindi" if language == "hi" else "English"}

For each variation provide:
- Subject (for email) or Opening (for WhatsApp/chat)
- Body (use [CUSTOMER_NAME], [ORDER_ID], [DATE] as placeholders)
- Closing

Format as JSON array "templates" with objects having keys: variation, subject_or_opening, body, closing, use_case"""

    raw = _llm(prompt, system=sys_prompt)
    try:
        start = raw.index("{")
        end = raw.rindex("}") + 1
        result = json.loads(raw[start:end])
    except Exception:
        templates = [
            {
                "variation": "Formal",
                "subject_or_opening": f"Re: Your {scenario}",
                "body": f"Dear [CUSTOMER_NAME],\n\nThank you for reaching out regarding your {scenario}. We have received your inquiry and are working on it.\n\nReference: [ORDER_ID]",
                "closing": "Warm regards,\nSupport Team",
                "use_case": "Professional communication",
            },
            {
                "variation": "Friendly",
                "subject_or_opening": f"Hey [CUSTOMER_NAME]! 👋",
                "body": f"Thanks for getting in touch about your {scenario}. We're on it and will get back to you soon!",
                "closing": "Cheers! 😊\nSupport Team",
                "use_case": "Casual customer communication",
            },
        ]
        result = {"templates": templates}

    result["scenario"] = scenario
    result["business_type"] = business_type
    result["language"] = language
    return result


async def weekly_report(
    ticket_data: str, period: str, business_name: str, language: str
) -> dict:
    sys_prompt = "You are a customer support analytics expert."

    prompt = f"""Analyze this week's customer support data for {business_name}:

Period: {period}
Data:
{ticket_data}

Generate a weekly intelligence report as JSON:
{{
  "executive_summary": "3-4 sentence overview",
  "top_issues": [
    {{"issue": "issue name", "count": 0, "percentage": "0%", "trend": "up|down|stable"}}
  ],
  "sentiment_breakdown": {{
    "positive": "0%", "neutral": "0%", "negative": "0%", "critical": "0%"
  }},
  "avg_resolution_time": "estimate",
  "csat_score": "estimated 1-5",
  "key_wins": ["things that went well"],
  "action_items": ["things to improve"],
  "product_feedback": ["recurring product complaints or suggestions"],
  "recommended_faq_additions": ["questions to add to FAQ"]
}}"""

    raw = _llm(prompt, system=sys_prompt)
    try:
        start = raw.index("{")
        end = raw.rindex("}") + 1
        result = json.loads(raw[start:end])
    except Exception:
        result = {
            "executive_summary": f"Weekly support report for {business_name} for {period}. Data analysis complete.",
            "top_issues": [{"issue": "General inquiries", "count": 10, "percentage": "40%", "trend": "stable"}],
            "sentiment_breakdown": {"positive": "40%", "neutral": "35%", "negative": "20%", "critical": "5%"},
            "avg_resolution_time": "4-6 hours",
            "csat_score": "3.8/5",
            "key_wins": ["Timely responses"],
            "action_items": ["Improve FAQ coverage"],
            "product_feedback": ["N/A"],
            "recommended_faq_additions": ["Common billing questions"],
        }

    result["business_name"] = business_name
    result["period"] = period
    result["generated_at"] = datetime.now().strftime("%Y-%m-%d")
    result["language"] = language
    return result


async def knowledge_base_answer(
    question: str, kb_content: str, business_name: str, language: str
) -> dict:
    sys_prompt = LANG_SYSTEM.get(language, LANG_SYSTEM["en"])

    prompt = f"""You are the AI knowledge base assistant for {business_name}.

Knowledge Base Content:
{kb_content if kb_content else "No specific knowledge base. Use general best practices."}

Question: {question}

Answer precisely based on the knowledge base. If the answer is not in the KB, say so clearly.
Also identify if this question should be added to the FAQ.

Format as JSON:
{{
  "answer": "detailed answer",
  "found_in_kb": true|false,
  "confidence": "high|medium|low",
  "related_topics": ["list", "of", "related", "topics"],
  "should_add_to_faq": true|false,
  "suggested_faq_question": "cleaner version of the question for FAQ"
}}"""

    raw = _llm(prompt, system=sys_prompt)
    try:
        start = raw.index("{")
        end = raw.rindex("}") + 1
        result = json.loads(raw[start:end])
    except Exception:
        result = {
            "answer": "I was unable to find a specific answer in the knowledge base. Please contact support directly.",
            "found_in_kb": False,
            "confidence": "low",
            "related_topics": [],
            "should_add_to_faq": True,
            "suggested_faq_question": question,
        }

    result["question"] = question
    result["language"] = language
    return result


async def cs_agent(action: str, payload: dict, language: str = "en") -> dict:
    try:
        if action == "faq_bot":
            return await faq_bot(
                query=payload.get("query", ""),
                business_name=payload.get("business_name", "Our Business"),
                business_type=payload.get("business_type", "General"),
                faq_context=payload.get("faq_context", ""),
                language=language,
            )
        elif action == "qualify_lead":
            return await qualify_lead(
                customer_name=payload.get("customer_name", "Customer"),
                business_type=payload.get("business_type", "General"),
                responses=payload.get("responses", {}),
                language=language,
            )
        elif action == "draft_whatsapp":
            return await draft_whatsapp(
                message_type=payload.get("message_type", "follow_up"),
                customer_name=payload.get("customer_name", "Customer"),
                business_name=payload.get("business_name", "Our Business"),
                context=payload.get("context", ""),
                language=language,
            )
        elif action == "analyze_sentiment":
            return await analyze_sentiment(
                text=payload.get("text", ""),
                customer_name=payload.get("customer_name", "Customer"),
                language=language,
            )
        elif action == "handle_complaint":
            return await handle_complaint(
                complaint=payload.get("complaint", ""),
                customer_name=payload.get("customer_name", "Customer"),
                order_id=payload.get("order_id", ""),
                business_name=payload.get("business_name", "Our Business"),
                category=payload.get("category", "general"),
                language=language,
            )
        elif action == "summarize_ticket":
            return await summarize_ticket(
                conversation=payload.get("conversation", ""),
                customer_name=payload.get("customer_name", "Customer"),
                language=language,
            )
        elif action == "response_template":
            return await generate_response_template(
                scenario=payload.get("scenario", "general inquiry"),
                business_type=payload.get("business_type", "General"),
                tone=payload.get("tone", "friendly"),
                language=language,
            )
        elif action == "weekly_report":
            return await weekly_report(
                ticket_data=payload.get("ticket_data", "No data provided"),
                period=payload.get("period", "This week"),
                business_name=payload.get("business_name", "Our Business"),
                language=language,
            )
        elif action == "kb_answer":
            return await knowledge_base_answer(
                question=payload.get("question", ""),
                kb_content=payload.get("kb_content", ""),
                business_name=payload.get("business_name", "Our Business"),
                language=language,
            )

        elif action == "send_whatsapp":
            # Direct WhatsApp send via Twilio — requires TWILIO_ACCOUNT_SID env var
            to_number = payload.get("to_number", "").strip()
            message   = payload.get("message", "").strip()
            if not to_number:
                return {"error": "to_number is required (e.g. +919876543210)"}
            if not message:
                return {"error": "message is required"}
            # Normalise number — add country code if missing
            if not to_number.startswith("+"):
                to_number = "+91" + to_number.lstrip("0")
            from backend.commerce.commerce_agent import send_whatsapp as _send_wa
            result = await _send_wa(to_number=to_number, message=message)
            return {
                "action": "send_whatsapp",
                "to": to_number,
                "message_preview": message[:120],
                **result,
            }

        elif action == "suggest_canned_response":
            # AI suggests a canned response category + text based on incoming message
            incoming = payload.get("incoming_message", "")
            business = payload.get("business_name", "Our Business")
            existing = payload.get("existing_templates", [])
            if not incoming:
                return {"error": "incoming_message is required"}
            sys_prompt = LANG_SYSTEM.get(language, LANG_SYSTEM["en"])
            existing_str = "\n".join(f"- [{t.get('category','')}] {t.get('text','')}" for t in existing[:10]) if existing else "None yet"
            prompt = f"""Customer message: "{incoming}"
Business: {business}
Existing canned responses:\n{existing_str}

Suggest the best canned response for this message.
If an existing template fits well, recommend it.
If not, draft a new one.

Output JSON:
{{
  "matched_existing": true|false,
  "matched_template": "exact text if matched, else null",
  "suggested_text": "ready-to-send response text (under 200 chars for WhatsApp)",
  "category": "greeting|faq|pricing|complaint|follow_up|thank_you|escalation|other",
  "confidence": "high|medium|low",
  "reason": "why this response fits"
}}"""
            raw = _llm(prompt, system=sys_prompt)
            try:
                start = raw.index("{"); end = raw.rindex("}") + 1
                data = json.loads(raw[start:end])
            except Exception:
                data = {"suggested_text": raw[:200], "category": "other", "confidence": "low"}
            return {"action": "suggest_canned_response", "incoming": incoming, **data}

        elif action == "analyze_sla":
            return _analyze_sla(
                tickets=payload.get("tickets", []),
                sla_rules=payload.get("sla_rules", {}),
                business_name=payload.get("business_name", ""),
            )

        elif action == "winback_sequence":
            return _winback_sequence(
                business_name=payload.get("business_name", ""),
                product_name=payload.get("product_name", ""),
                churned_customers=payload.get("churned_customers", []),
                churn_reason=payload.get("churn_reason", "unknown"),
                offer_type=payload.get("offer_type", "discount"),
                offer_value=payload.get("offer_value", "20%"),
                industry=payload.get("industry", "saas"),
            )

        elif action == "customer_health_score":
            return _customer_health_score(
                customers=payload.get("customers", []),
                business_name=payload.get("business_name", ""),
                product_name=payload.get("product_name", ""),
                industry=payload.get("industry", "saas"),
            )

        elif action == "escalation_rule_builder":
            return _escalation_rule_builder(
                business_name=payload.get("business_name", ""),
                industry=payload.get("industry", "saas"),
                team_structure=payload.get("team_structure", []),
                products=payload.get("products", []),
                sla_tier=payload.get("sla_tier", "standard"),
            )

        elif action == "ticket_categorizer":
            return _ticket_categorizer(
                tickets=payload.get("tickets", []),
                business_name=payload.get("business_name", ""),
                custom_categories=payload.get("custom_categories", []),
                language=lang,
            )

        elif action == "onboarding_planner":
            return _onboarding_planner(
                customer_name=payload.get("customer_name", ""),
                product_name=payload.get("product_name", ""),
                industry=payload.get("industry", ""),
                tier=payload.get("tier", "standard"),
                goals=payload.get("goals", []),
                team_size=int(payload.get("team_size", 1) or 1),
                language=lang,
            )

        elif action == "churn_risk":
            return _churn_risk_analyzer(
                customers=payload.get("customers", []),
                business_name=payload.get("business_name", ""),
                industry=payload.get("industry", "saas"),
                language=lang,
            )

        elif action == "escalation_manager":
            return _escalation_manager(
                tickets=payload.get("tickets", []),
                rules=payload.get("rules", {}),
                business_name=payload.get("business_name", ""),
                escalation_email=payload.get("escalation_email", ""),
                language=lang,
            )

        elif action == "build_csat_survey":
            return _build_csat_survey(
                business_name=payload.get("business_name", ""),
                business_type=payload.get("business_type", ""),
                touchpoints=payload.get("touchpoints", []),
                language=lang,
            )

        elif action == "analyze_csat":
            return _analyze_csat(
                responses=payload.get("responses", []),
                business_name=payload.get("business_name", ""),
            )

        else:
            return {"error": f"Unknown action: {action}"}
    except Exception as e:
        return {"error": str(e), "action": action}


# ── SLA Tracker (Round 4) ─────────────────────────────────────────────────────

_DEFAULT_SLA = {
    "critical":  {"response_hrs": 1,  "resolution_hrs": 4},
    "high":      {"response_hrs": 4,  "resolution_hrs": 24},
    "medium":    {"response_hrs": 8,  "resolution_hrs": 48},
    "low":       {"response_hrs": 24, "resolution_hrs": 72},
}

_PRIORITY_COLOR = {"critical": "#ef4444", "high": "#f59e0b", "medium": "#3b82f6", "low": "#10b981"}


def _analyze_sla(tickets: list[dict], sla_rules: dict, business_name: str = "") -> dict:
    """
    Analyze ticket list against SLA rules.
    Each ticket: {id, subject, priority, created_at (ISO), first_response_at (ISO|null), resolved_at (ISO|null), assignee}
    sla_rules overrides _DEFAULT_SLA per priority.
    """
    from datetime import datetime, timezone, timedelta

    rules = {**_DEFAULT_SLA, **sla_rules}
    now   = datetime.now(timezone.utc)

    def parse_dt(s):
        if not s: return None
        try:
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            return datetime.fromisoformat(s)
        except Exception:
            return None

    breaches   = []
    at_risk    = []
    on_track   = []
    stats      = {"total": len(tickets), "breached": 0, "at_risk": 0, "on_track": 0, "resolved": 0}
    priority_counts = {}

    for t in tickets:
        tid      = t.get("id", "")
        subject  = t.get("subject", "Untitled")
        priority = (t.get("priority") or "medium").lower()
        assignee = t.get("assignee", "Unassigned")
        created  = parse_dt(t.get("created_at"))
        responded= parse_dt(t.get("first_response_at"))
        resolved = parse_dt(t.get("resolved_at"))

        rule = rules.get(priority, rules["medium"])
        resp_sla_hrs  = rule["response_hrs"]
        res_sla_hrs   = rule["resolution_hrs"]

        priority_counts[priority] = priority_counts.get(priority, 0) + 1
        if resolved:
            stats["resolved"] += 1

        if not created:
            on_track.append({"id": tid, "subject": subject, "priority": priority, "status": "unknown"})
            continue

        age_hrs          = (now - created).total_seconds() / 3600
        resp_sla_deadline= created + __import__("datetime").timedelta(hours=resp_sla_hrs)
        res_sla_deadline = created + __import__("datetime").timedelta(hours=res_sla_hrs)

        # Response SLA
        resp_breached = not responded and now > resp_sla_deadline
        resp_at_risk  = not responded and not resp_breached and (resp_sla_deadline - now).total_seconds() / 3600 < resp_sla_hrs * 0.25

        # Resolution SLA
        res_breached  = not resolved and now > res_sla_deadline
        res_at_risk   = not resolved and not res_breached and (res_sla_deadline - now).total_seconds() / 3600 < res_sla_hrs * 0.25

        entry = {
            "id":                tid,
            "subject":           subject,
            "priority":          priority,
            "assignee":          assignee,
            "age_hrs":           round(age_hrs, 1),
            "responded":         bool(responded),
            "resolved":          bool(resolved),
            "resp_sla_hrs":      resp_sla_hrs,
            "res_sla_hrs":       res_sla_hrs,
            "resp_breached":     resp_breached,
            "res_breached":      res_breached,
            "resp_time_hrs":     round((responded - created).total_seconds() / 3600, 1) if responded else None,
            "resolution_time_hrs": round((resolved - created).total_seconds() / 3600, 1) if resolved else None,
            "resp_sla_deadline": resp_sla_deadline.isoformat(),
            "res_sla_deadline":  res_sla_deadline.isoformat(),
            "color":             _PRIORITY_COLOR.get(priority, "#6b7280"),
        }

        if resp_breached or res_breached:
            entry["breach_reason"] = ("Response SLA" if resp_breached else "") + (" + " if resp_breached and res_breached else "") + ("Resolution SLA" if res_breached else "")
            breaches.append(entry)
            stats["breached"] += 1
        elif resp_at_risk or res_at_risk:
            entry["risk_reason"] = "Approaching SLA limit"
            at_risk.append(entry)
            stats["at_risk"] += 1
        else:
            on_track.append(entry)
            stats["on_track"] += 1

    # Assignee leaderboard
    assignee_map: dict = {}
    for t_list in [breaches, at_risk, on_track]:
        for t in t_list:
            a = t.get("assignee", "Unassigned")
            if a not in assignee_map:
                assignee_map[a] = {"assignee": a, "total": 0, "breached": 0, "resolved": 0}
            assignee_map[a]["total"] += 1
            if t.get("res_breached"): assignee_map[a]["breached"] += 1
            if t.get("resolved"):     assignee_map[a]["resolved"] += 1

    return {
        "action":           "analyze_sla",
        "business_name":    business_name,
        "stats":            stats,
        "priority_counts":  priority_counts,
        "breaches":         sorted(breaches, key=lambda x: x["priority"] in ("critical", "high"), reverse=True),
        "at_risk":          at_risk,
        "on_track":         on_track,
        "assignee_summary": sorted(assignee_map.values(), key=lambda x: -x["breached"]),
        "sla_health":       "Critical" if stats["breached"] > 0 else ("At Risk" if stats["at_risk"] > 0 else "Healthy"),
    }


# ── CSAT Survey Builder & Analyzer (Round 5) ──────────────────────────────────

_DEFAULT_TOUCHPOINTS = ["purchase experience", "delivery", "product quality", "customer service", "overall satisfaction"]

_CSAT_QUESTIONS = {
    "purchase experience": [
        "How easy was it to find what you were looking for?",
        "How satisfied are you with the checkout/ordering process?",
    ],
    "delivery": [
        "Was your order delivered on time?",
        "How would you rate the packaging quality?",
    ],
    "product quality": [
        "How satisfied are you with the quality of the product/service?",
        "Did the product/service meet your expectations?",
    ],
    "customer service": [
        "How quickly did our team respond to your query?",
        "How helpful was our customer support team?",
    ],
    "overall satisfaction": [
        "Overall, how satisfied are you with [Business Name]?",
        "How likely are you to recommend us to a friend or colleague? (0-10)",
    ],
}


def _build_csat_survey(
    business_name: str,
    business_type: str,
    touchpoints:   list[str],
    language:      str = "en",
) -> dict:
    """Generate a CSAT survey with NPS question and touchpoint-specific questions."""
    if not touchpoints:
        touchpoints = _DEFAULT_TOUCHPOINTS[:3]

    questions = []
    qid = 1

    # NPS always first
    questions.append({
        "id": qid, "type": "nps", "scale": "0-10",
        "text": f"How likely are you to recommend {business_name or 'us'} to a friend or colleague?",
        "required": True,
    })
    qid += 1

    # Overall CSAT
    questions.append({
        "id": qid, "type": "rating", "scale": "1-5",
        "text": f"Overall, how satisfied are you with your experience at {business_name or 'our business'}?",
        "required": True,
    })
    qid += 1

    # Touchpoint questions
    for tp in touchpoints:
        pool = _CSAT_QUESTIONS.get(tp.lower(), [f"How satisfied are you with our {tp}?"])
        for q in pool[:2]:
            questions.append({
                "id": qid, "type": "rating", "scale": "1-5",
                "text": q.replace("[Business Name]", business_name or "us"),
                "touchpoint": tp,
                "required": False,
            })
            qid += 1

    # Open ended
    questions.append({
        "id": qid, "type": "text",
        "text": "What is the ONE thing we could do better? (Optional)",
        "required": False,
    })

    return {
        "action":        "build_csat_survey",
        "business_name": business_name,
        "business_type": business_type,
        "language":      language,
        "survey_title":  f"How are we doing? — {business_name or 'Customer Survey'}",
        "estimated_time": f"{max(1, len(questions) // 3)} minute",
        "questions":     questions,
        "total_questions": len(questions),
        "touchpoints":   touchpoints,
        "share_tip":     "Send via WhatsApp, QR code at checkout, or post-purchase email for 30-60% higher response rates.",
    }


def _analyze_csat(responses: list[dict], business_name: str = "") -> dict:
    """
    Analyze CSAT survey responses.
    Each response: {nps: 0-10, overall_rating: 1-5, scores: {touchpoint: 1-5}, comment: str}
    """
    if not responses:
        return {"error": "No responses to analyze"}

    n = len(responses)

    # NPS
    nps_scores   = [r.get("nps", 0) for r in responses if r.get("nps") is not None]
    promoters    = sum(1 for s in nps_scores if s >= 9)
    passives     = sum(1 for s in nps_scores if 7 <= s <= 8)
    detractors   = sum(1 for s in nps_scores if s <= 6)
    nps_score    = round(((promoters - detractors) / len(nps_scores)) * 100) if nps_scores else 0

    # Overall CSAT %
    overall      = [r.get("overall_rating", 0) for r in responses if r.get("overall_rating")]
    csat_pct     = round(sum(1 for s in overall if s >= 4) / len(overall) * 100) if overall else 0
    avg_rating   = round(sum(overall) / len(overall), 1) if overall else 0

    # Per-touchpoint
    touchpoint_scores: dict = {}
    for r in responses:
        for tp, score in (r.get("scores") or {}).items():
            if tp not in touchpoint_scores:
                touchpoint_scores[tp] = []
            touchpoint_scores[tp].append(float(score))

    touchpoint_summary = []
    for tp, scores in touchpoint_scores.items():
        avg = round(sum(scores) / len(scores), 2)
        touchpoint_summary.append({
            "touchpoint": tp,
            "avg_score":  avg,
            "out_of":     5,
            "pct":        round(avg / 5 * 100),
            "status":     "Good" if avg >= 4 else ("Needs Work" if avg >= 3 else "Critical"),
        })
    touchpoint_summary.sort(key=lambda x: x["avg_score"])

    # Comments / pain points
    comments = [r.get("comment", "").strip() for r in responses if r.get("comment", "").strip()]

    # Pain areas
    pain_areas = [t for t in touchpoint_summary if t["avg_score"] < 3.5]
    strengths  = [t for t in touchpoint_summary if t["avg_score"] >= 4.5]

    return {
        "action":           "analyze_csat",
        "business_name":    business_name,
        "total_responses":  n,
        "csat_score":       csat_pct,
        "avg_rating":       avg_rating,
        "nps_score":        nps_score,
        "nps_breakdown":    {"promoters": promoters, "passives": passives, "detractors": detractors},
        "touchpoint_summary": touchpoint_summary,
        "pain_areas":       pain_areas,
        "strengths":        strengths,
        "comments":         comments[:20],
        "health":           "Excellent" if csat_pct >= 80 else ("Good" if csat_pct >= 65 else ("Needs Attention" if csat_pct >= 50 else "Critical")),
        "top_action":       f"Focus on '{pain_areas[0]['touchpoint']}' — lowest rated at {pain_areas[0]['avg_score']}/5" if pain_areas else "Maintain current quality across all touchpoints",
    }


# ── Escalation Manager (Round 6) ─────────────────────────────────────────────

# ── Churn Risk Analyzer (Round 7) ────────────────────────────────────────────

_CHURN_SIGNALS = {
    "no_login_days":       {"weight": 2.0, "threshold": 14,  "label": "No login > 14 days"},
    "support_tickets":     {"weight": 1.5, "threshold": 3,   "label": "3+ support tickets this month"},
    "payment_failed":      {"weight": 3.0, "threshold": 1,   "label": "Payment failure"},
    "nps_score":           {"weight": 2.5, "threshold": 6,   "label": "NPS <= 6 (detractor)"},
    "feature_usage_drop":  {"weight": 1.8, "threshold": 50,  "label": "Feature usage dropped 50%+"},
    "contract_days_left":  {"weight": 2.0, "threshold": 30,  "label": "Contract expiring < 30 days"},
    "competitor_mention":  {"weight": 2.5, "threshold": 1,   "label": "Mentioned competitor in ticket"},
    "downgrade_request":   {"weight": 3.5, "threshold": 1,   "label": "Requested downgrade"},
}


def _churn_score(c: dict) -> tuple[float, list[str]]:
    score = 0.0
    triggers = []
    no_login = int(c.get("no_login_days", 0) or 0)
    if no_login >= 14:
        score += _CHURN_SIGNALS["no_login_days"]["weight"] * min(no_login / 14, 3)
        triggers.append(f"No login for {no_login} days")
    tickets = int(c.get("support_tickets_month", 0) or 0)
    if tickets >= 3:
        score += _CHURN_SIGNALS["support_tickets"]["weight"] * (tickets / 3)
        triggers.append(f"{tickets} support tickets this month")
    if c.get("payment_failed"):
        score += _CHURN_SIGNALS["payment_failed"]["weight"]
        triggers.append("Payment failure on record")
    nps = c.get("nps_score")
    if nps is not None and int(nps) <= 6:
        score += _CHURN_SIGNALS["nps_score"]["weight"] * (7 - int(nps)) / 7
        triggers.append(f"NPS score {nps} (detractor)")
    usage_drop = float(c.get("feature_usage_drop_pct", 0) or 0)
    if usage_drop >= 50:
        score += _CHURN_SIGNALS["feature_usage_drop"]["weight"] * (usage_drop / 50)
        triggers.append(f"Feature usage dropped {usage_drop:.0f}%")
    contract_days = c.get("contract_days_left")
    if contract_days is not None and int(contract_days) <= 30:
        score += _CHURN_SIGNALS["contract_days_left"]["weight"]
        triggers.append(f"Contract renews in {contract_days} days")
    if c.get("competitor_mention"):
        score += _CHURN_SIGNALS["competitor_mention"]["weight"]
        triggers.append("Mentioned competitor in recent ticket")
    if c.get("downgrade_request"):
        score += _CHURN_SIGNALS["downgrade_request"]["weight"]
        triggers.append("Requested plan downgrade")
    return round(min(score / 15 * 100, 100), 1), triggers


def _winback_actions(score: float, triggers: list[str], tier: str, industry: str) -> list[str]:
    actions = []
    if score >= 75:
        actions.append("URGENT: Assign dedicated CSM — schedule call within 24 hours")
        actions.append("Offer 2-month extension or 30% discount to retain")
    elif score >= 50:
        actions.append("Send personalised check-in email from Account Manager within 48 hours")
        actions.append("Share relevant case study or ROI report for their industry")
    else:
        actions.append("Enroll in automated re-engagement drip (3-email sequence)")
    if any("login" in t.lower() for t in triggers):
        actions.append("Send 'What you missed' feature update email with quick-start guide")
    if any("ticket" in t.lower() for t in triggers):
        actions.append("Proactively resolve open tickets — assign senior support agent")
    if any("payment" in t.lower() for t in triggers):
        actions.append("Contact billing — offer flexible payment or EMI option")
    if any("competitor" in t.lower() for t in triggers):
        actions.append("Send competitive battle card highlighting your differentiators")
    if any("contract" in t.lower() for t in triggers):
        actions.append("Initiate renewal conversation — offer multi-year lock-in discount")
    if any("downgrade" in t.lower() for t in triggers):
        actions.append("Schedule product demo to show unused premium features before downgrade")
    return actions[:5]


def _churn_risk_analyzer(
    customers: list,
    business_name: str = "",
    industry: str = "saas",
    language: str = "en",
) -> dict:
    if not customers:
        customers = [
            {"id": "C001", "name": "TechCorp India", "tier": "Enterprise", "mrr": 45000, "no_login_days": 22, "support_tickets_month": 5, "nps_score": 4, "contract_days_left": 18, "feature_usage_drop_pct": 65},
            {"id": "C002", "name": "Sharma Exports", "tier": "Premium",    "mrr": 12000, "no_login_days": 8,  "support_tickets_month": 1, "nps_score": 8, "contract_days_left": 90, "feature_usage_drop_pct": 10},
            {"id": "C003", "name": "Ravi Consulting","tier": "Standard",   "mrr": 3500,  "no_login_days": 35, "payment_failed": True, "support_tickets_month": 4, "competitor_mention": True},
            {"id": "C004", "name": "Kiran Solutions","tier": "Standard",   "mrr": 4000,  "no_login_days": 3,  "support_tickets_month": 0, "nps_score": 9},
            {"id": "C005", "name": "PrimeRetail Ltd","tier": "Premium",    "mrr": 18000, "downgrade_request": True, "nps_score": 5, "feature_usage_drop_pct": 70},
        ]

    results = []
    for c in customers:
        score, triggers = _churn_score(c)
        risk = "Critical" if score >= 75 else ("High" if score >= 50 else ("Medium" if score >= 25 else "Low"))
        color = {"Critical": "red", "High": "orange", "Medium": "yellow", "Low": "green"}[risk]
        mrr   = float(c.get("mrr", 0) or 0)
        results.append({
            "id":           c.get("id", ""),
            "name":         c.get("name", "Unknown"),
            "tier":         c.get("tier", "Standard"),
            "mrr":          mrr,
            "churn_score":  score,
            "risk_level":   risk,
            "color":        color,
            "triggers":     triggers,
            "winback_actions": _winback_actions(score, triggers, c.get("tier", ""), industry),
            "revenue_at_risk": mrr * 12,
        })

    results.sort(key=lambda x: x["churn_score"], reverse=True)

    critical = [r for r in results if r["risk_level"] == "Critical"]
    high     = [r for r in results if r["risk_level"] == "High"]
    arr_risk = sum(r["revenue_at_risk"] for r in critical + high)

    return {
        "action":            "churn_risk",
        "business_name":     business_name,
        "total_analyzed":    len(results),
        "critical_count":    len(critical),
        "high_count":        len(high),
        "arr_at_risk":       round(arr_risk, 0),
        "customers":         results,
        "health":            "Critical" if critical else ("At Risk" if high else "Healthy"),
        "health_color":      "red" if critical else ("orange" if high else "green"),
        "top_priority":      results[0]["name"] if results else "",
    }


# ── Customer Onboarding Planner (Round 8) ────────────────────────────────────

_ONBOARDING_PHASES = {
    "standard": [
        {"phase": "Day 1 — Welcome", "days": "Day 1", "tasks": [
            "Send welcome email with login credentials and getting-started guide",
            "Schedule kickoff call with Customer Success Manager",
            "Share product documentation and video library link",
        ]},
        {"phase": "Week 1 — Setup", "days": "Days 2-7", "tasks": [
            "Complete account setup and profile configuration",
            "Import existing data / integrations",
            "Attend product walkthrough webinar",
            "Set up team members and assign roles",
        ]},
        {"phase": "Week 2 — First Value", "days": "Days 8-14", "tasks": [
            "Complete first core workflow end-to-end",
            "Review first week usage report with CSM",
            "Identify top 3 use cases to focus on",
            "Join community / Slack group",
        ]},
        {"phase": "Week 3-4 — Adoption", "days": "Days 15-30", "tasks": [
            "Train all team members on core features",
            "Set up automation / recurring workflows",
            "30-day check-in call to review progress and blockers",
            "Enable advanced features as needed",
        ]},
    ],
    "premium": [
        {"phase": "Day 1 — VIP Welcome", "days": "Day 1", "tasks": [
            "Dedicated CSM assigned — personal welcome call within 2 hours",
            "Custom onboarding plan shared based on business goals",
            "Slack/WhatsApp direct channel set up with support team",
            "Branded welcome kit / swag sent",
        ]},
        {"phase": "Days 2-3 — Deep Discovery", "days": "Days 2-3", "tasks": [
            "Discovery session: map current workflows to product capabilities",
            "Data migration plan created with timeline",
            "Custom integration requirements scoped",
            "Success metrics (KPIs) defined together",
        ]},
        {"phase": "Week 1 — Configured Setup", "days": "Days 4-7", "tasks": [
            "Product configured to match business workflows",
            "Team trained in 2 dedicated sessions",
            "All integrations live and tested",
            "Dashboard and reports customised",
        ]},
        {"phase": "Week 2-4 — Go Live", "days": "Days 8-30", "tasks": [
            "Parallel run: old system vs new product side-by-side",
            "Weekly check-ins with CSM",
            "Training refresher for power users",
            "30-day ROI review: time saved, productivity gains measured",
        ]},
    ],
    "enterprise": [
        {"phase": "Pre-Launch — Project Kick-off", "days": "Week -1 to Day 0", "tasks": [
            "Executive sponsor meeting: align on strategic goals and success criteria",
            "Dedicated project manager + CSM assigned",
            "Custom implementation plan (30/60/90 day roadmap) shared",
            "Security review and compliance documentation completed",
            "SSO / LDAP / API integration scoped",
        ]},
        {"phase": "Week 1-2 — Foundations", "days": "Days 1-14", "tasks": [
            "Pilot rollout: 10-20 power users as champions",
            "Custom data migration executed with zero downtime",
            "All integrations built, tested, and deployed",
            "Admin training for IT team",
            "SLA agreement confirmed and support escalation path set up",
        ]},
        {"phase": "Week 3-4 — Org-wide Rollout", "days": "Days 15-30", "tasks": [
            "Department-by-department rollout with dedicated training sessions",
            "Change management communication plan executed",
            "Help desk articles and internal FAQs created",
            "Usage dashboards live — track adoption by team",
        ]},
        {"phase": "Month 2-3 — Optimise", "days": "Days 31-90", "tasks": [
            "Monthly business reviews with executive stakeholders",
            "Advanced feature enablement for mature teams",
            "ROI report: quantified time saved, cost reduced, revenue impacted",
            "Expansion opportunities reviewed (seats, modules, integrations)",
        ]},
    ],
}


def _onboarding_planner(
    customer_name: str,
    product_name: str = "",
    industry: str = "",
    tier: str = "standard",
    goals: list | None = None,
    team_size: int = 1,
    language: str = "en",
) -> dict:
    goals = goals or ["improve efficiency", "reduce manual work", "scale operations"]
    tier_key = "enterprise" if tier.lower() in ("enterprise", "vip") else ("premium" if tier.lower() in ("premium", "pro") else "standard")
    phases = _ONBOARDING_PHASES[tier_key]

    # Personalise tasks based on inputs
    personalised_phases = []
    for phase in phases:
        tasks = list(phase["tasks"])
        if customer_name and tasks:
            tasks[0] = tasks[0].replace("welcome email", f"welcome email to {customer_name} team")
        if product_name and len(tasks) > 1:
            tasks = [t.replace("product", product_name) for t in tasks]
        personalised_phases.append({**phase, "tasks": tasks, "status": "pending"})

    # Success metrics based on goals
    metrics = []
    for g in goals[:3]:
        if "efficien" in g.lower() or "time" in g.lower():
            metrics.append({"metric": "Time Saved per Week", "baseline": "Measure in Week 1", "target": "20%+ reduction by Day 30"})
        elif "manual" in g.lower() or "automat" in g.lower():
            metrics.append({"metric": "Manual Tasks Automated", "baseline": "Count in Week 1", "target": "50%+ automated by Day 30"})
        elif "scale" in g.lower() or "growth" in g.lower():
            metrics.append({"metric": "Capacity Handled", "baseline": "Current throughput", "target": "30%+ increase by Day 60"})
        else:
            metrics.append({"metric": g.title(), "baseline": "To be measured", "target": "Defined in kickoff call"})

    total_tasks = sum(len(p["tasks"]) for p in personalised_phases)
    duration_days = 30 if tier_key == "standard" else (30 if tier_key == "premium" else 90)

    return {
        "action":          "onboarding_planner",
        "customer_name":   customer_name,
        "product_name":    product_name,
        "tier":            tier,
        "industry":        industry,
        "team_size":       team_size,
        "goals":           goals,
        "phases":          personalised_phases,
        "total_tasks":     total_tasks,
        "duration_days":   duration_days,
        "success_metrics": metrics,
        "health_check_schedule": [
            {"day": 7,  "type": "Check-in Call", "focus": "Setup completion, early blockers"},
            {"day": 14, "type": "Progress Review", "focus": "First value achieved, adoption rate"},
            {"day": 30, "type": "30-Day Review",  "focus": "ROI measurement, goals vs actuals"},
        ] + ([{"day": 60, "type": "60-Day Review", "focus": "Expansion opportunities, advanced features"}] if tier_key == "enterprise" else []),
        "assigned_csm":    "To be assigned" if tier_key == "standard" else "Dedicated CSM assigned",
    }


# ── Ticket Auto-Categorizer (Round 9) ────────────────────────────────────────

_TICKET_CATEGORIES = {
    "billing":      {"keywords": ["invoice", "payment", "charge", "refund", "billing", "subscription", "price", "fee", "overcharge", "receipt"], "team": "Finance/Billing", "sla_hours": 4,  "color": "#f59e0b"},
    "technical":    {"keywords": ["bug", "error", "crash", "broken", "not working", "glitch", "issue", "fail", "loading", "slow", "down", "500", "404"], "team": "Engineering", "sla_hours": 8, "color": "#818cf8"},
    "feature":      {"keywords": ["feature", "request", "wish", "add", "missing", "would love", "suggest", "improve", "enhancement", "new"], "team": "Product", "sla_hours": 72, "color": "#06b6d4"},
    "account":      {"keywords": ["login", "password", "access", "account", "profile", "reset", "two factor", "2fa", "locked", "username"], "team": "Support L1", "sla_hours": 2,  "color": "#22c55e"},
    "complaint":    {"keywords": ["terrible", "worst", "unacceptable", "disappointed", "angry", "frustrated", "useless", "scam", "cheat", "legal", "lawyer", "refund immediately"], "team": "Senior Support", "sla_hours": 2, "color": "#ef4444"},
    "onboarding":   {"keywords": ["how to", "setup", "getting started", "tutorial", "guide", "new user", "onboard", "walkthrough", "configure", "install"], "team": "Success", "sla_hours": 24, "color": "#10b981"},
    "integration":  {"keywords": ["api", "webhook", "integrate", "zapier", "sync", "connect", "third party", "import", "export", "oauth"], "team": "Engineering", "sla_hours": 24, "color": "#8b5cf6"},
    "general":      {"keywords": [], "team": "Support L1", "sla_hours": 24, "color": "#6b7280"},
}

_URGENCY_SIGNALS = {
    "critical": ["urgent", "immediately", "asap", "right now", "emergency", "critical", "production down", "data loss", "legal"],
    "high":     ["today", "frustrated", "angry", "unacceptable", "disappointed", "broken", "cant work"],
    "medium":   ["issue", "problem", "not working", "bug", "error"],
    "low":      ["question", "how to", "when", "feature", "suggest"],
}


def _categorize_ticket(text: str, custom_categories: list) -> tuple[str, str, str, int, str]:
    text_lower = text.lower()

    # Custom categories first
    for cc in custom_categories:
        if any(kw.lower() in text_lower for kw in cc.get("keywords", [])):
            return cc["name"], cc.get("team", "Support"), "medium", cc.get("sla_hours", 24), cc.get("color", "#6b7280")

    # Standard categories — scored
    scores: dict[str, int] = {}
    for cat, info in _TICKET_CATEGORIES.items():
        if cat == "general":
            continue
        scores[cat] = sum(1 for kw in info["keywords"] if kw in text_lower)

    best_cat = max(scores, key=lambda k: scores[k]) if any(scores.values()) else "general"
    if scores.get(best_cat, 0) == 0:
        best_cat = "general"

    # Urgency
    urgency = "low"
    for level in ["critical", "high", "medium", "low"]:
        if any(sig in text_lower for sig in _URGENCY_SIGNALS[level]):
            urgency = level
            break

    cat_info = _TICKET_CATEGORIES[best_cat]
    return best_cat, cat_info["team"], urgency, cat_info["sla_hours"], cat_info["color"]


def _ticket_categorizer(
    tickets: list,
    business_name: str = "",
    custom_categories: list | None = None,
    language: str = "en",
) -> dict:
    custom_categories = custom_categories or []
    if not tickets:
        tickets = [
            {"id": "T001", "subject": "Cannot login — password reset not working", "description": "I've tried resetting my password 3 times but the email never arrives. Urgent!"},
            {"id": "T002", "subject": "Invoice shows wrong amount", "description": "I was charged Rs.5,000 but my plan is Rs.2,500. Please refund the extra charge immediately."},
            {"id": "T003", "subject": "API webhook not firing", "description": "Our Zapier integration broke after the latest update. Webhooks not triggering at all."},
            {"id": "T004", "subject": "How do I export data to Excel?", "description": "New user here — just trying to figure out how to export my reports to Excel format."},
            {"id": "T005", "subject": "This product is absolutely terrible!", "description": "I've had 5 bugs in 3 days. This is completely unacceptable. I want a full refund or I'm going to social media."},
        ]

    categorized = []
    cat_counts: dict[str, int] = {}
    urgency_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

    for t in tickets:
        text = (t.get("subject", "") + " " + t.get("description", "")).strip()
        category, team, urgency, sla_hours, color = _categorize_ticket(text, custom_categories)

        cat_counts[category] = cat_counts.get(category, 0) + 1
        urgency_counts[urgency] = urgency_counts.get(urgency, 0) + 1

        resolution_steps = {
            "billing":   ["Verify transaction in payment gateway", "Check subscription plan details", "Process refund/adjustment if applicable", "Send confirmation to customer"],
            "technical": ["Reproduce the issue in staging", "Check error logs", "Assign to on-call engineer if P0", "Update customer with ETA"],
            "account":   ["Verify identity", "Force password reset from admin panel", "Check 2FA settings", "Confirm access restored"],
            "complaint": ["Escalate to Senior Support immediately", "Acknowledge within 30 min", "Offer goodwill gesture", "Loop in manager if legal threat"],
            "feature":   ["Log in Product backlog", "Send 'we hear you' response", "Add to roadmap discussion"],
            "onboarding":["Send relevant documentation", "Schedule a 15-min screen-share", "Add to onboarding email sequence"],
            "integration":["Check API changelog for breaking changes", "Test in sandbox environment", "Assign to integration specialist"],
            "general":   ["Acknowledge receipt", "Route to appropriate team", "Respond within SLA"],
        }.get(category, ["Acknowledge and triage"])

        categorized.append({
            "id":          t.get("id", ""),
            "subject":     t.get("subject", ""),
            "category":    category,
            "category_color": color,
            "team":        team,
            "urgency":     urgency,
            "sla_hours":   sla_hours,
            "priority_score": {"critical": 100, "high": 70, "medium": 40, "low": 15}[urgency],
            "resolution_steps": resolution_steps,
            "auto_reply":  f"Thank you for reaching out! Your ticket [{t.get('id','')}] has been received and routed to our {team} team. We'll respond within {sla_hours} hours.",
        })

    categorized.sort(key=lambda x: -x["priority_score"])

    return {
        "action":          "ticket_categorizer",
        "business_name":   business_name,
        "total_tickets":   len(categorized),
        "tickets":         categorized,
        "category_breakdown": [{"category": k, "count": v} for k, v in sorted(cat_counts.items(), key=lambda x: -x[1])],
        "urgency_breakdown":  urgency_counts,
        "critical_tickets":   [t for t in categorized if t["urgency"] == "critical"],
        "routing_summary":    {t["team"]: sum(1 for c in categorized if c["team"] == t["team"]) for t in categorized},
    }


_ESC_PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
_ESC_COLOR = {"critical": "red", "high": "orange", "medium": "yellow", "low": "green"}

_DEFAULT_ESC_RULES = {
    "vip_keywords":    ["vip", "premium", "enterprise", "ceo", "founder", "director"],
    "legal_keywords":  ["legal", "lawsuit", "court", "fraud", "cheat", "scam", "fir", "police"],
    "financial_keywords": ["refund", "payment", "billing", "overcharge", "double charge"],
    "auto_escalate_hours": 4,
    "breach_hours":    24,
}


def _escalation_manager(
    tickets:          list,
    rules:            dict,
    business_name:    str  = "",
    escalation_email: str  = "",
    language:         str  = "en",
) -> dict:
    import re
    from datetime import datetime, timezone

    r = {**_DEFAULT_ESC_RULES, **rules}
    vip_kw     = [k.lower() for k in r.get("vip_keywords", [])]
    legal_kw   = [k.lower() for k in r.get("legal_keywords", [])]
    fin_kw     = [k.lower() for k in r.get("financial_keywords", [])]
    auto_hrs   = float(r.get("auto_escalate_hours", 4))
    breach_hrs = float(r.get("breach_hours", 24))

    now = datetime.now(timezone.utc)

    def _hours_open(t: dict) -> float:
        try:
            created = datetime.fromisoformat(t.get("created_at", "").replace("Z", "+00:00"))
            return (now - created).total_seconds() / 3600
        except Exception:
            return 0.0

    def _reason(t: dict) -> tuple[str, str]:
        text = (t.get("subject", "") + " " + t.get("description", "") + " " + t.get("customer_tier", "")).lower()
        if any(k in text for k in legal_kw):
            return "legal_threat", "critical"
        if any(k in text for k in vip_kw) or t.get("customer_tier", "").lower() in ("vip", "enterprise", "premium"):
            return "vip_customer", "high"
        if any(k in text for k in fin_kw):
            return "financial_dispute", "high"
        hrs = _hours_open(t)
        if hrs >= breach_hrs:
            return "sla_breach", "critical"
        if hrs >= auto_hrs:
            return "auto_time", "medium"
        if t.get("sentiment", "").lower() in ("very negative", "angry"):
            return "angry_customer", "high"
        return "", ""

    escalated, monitored, resolved = [], [], []

    for t in tickets:
        tid    = t.get("id", "T000")
        hrs    = _hours_open(t)
        reason, pri = _reason(t)
        status = t.get("status", "open").lower()

        entry = {
            "id":           tid,
            "subject":      t.get("subject", "No subject"),
            "customer":     t.get("customer_name", "Unknown"),
            "customer_tier":t.get("customer_tier", "standard"),
            "status":       status,
            "priority":     pri or t.get("priority", "medium"),
            "hours_open":   round(hrs, 1),
            "reason":       reason,
            "color":        _ESC_COLOR.get(pri or t.get("priority", "medium"), "green"),
            "assignee":     t.get("assignee", "Unassigned"),
            "action_needed": "",
        }

        if status in ("closed", "resolved"):
            resolved.append(entry)
        elif reason:
            entry["action_needed"] = {
                "legal_threat":     "Immediately loop in Legal & Management. Do NOT respond without approval.",
                "vip_customer":     "Escalate to Senior Support / Account Manager within 1 hour.",
                "financial_dispute":"Escalate to Finance team. Prepare refund/waiver options.",
                "sla_breach":       f"SLA breached ({hrs:.0f}h open). Escalate and compensate.",
                "auto_time":        f"Open {hrs:.0f}h — escalate to senior agent now.",
                "angry_customer":   "High anger detected — senior agent should take over.",
            }.get(reason, "Review and escalate if needed.")
            escalated.append(entry)
        else:
            entry["action_needed"] = "Monitor — no escalation trigger yet."
            monitored.append(entry)

    escalated.sort(key=lambda x: _ESC_PRIORITY_ORDER.get(x["priority"], 9))

    stats = {
        "total":       len(tickets),
        "escalated":   len(escalated),
        "monitored":   len(monitored),
        "resolved":    len(resolved),
        "critical":    sum(1 for e in escalated if e["priority"] == "critical"),
        "high":        sum(1 for e in escalated if e["priority"] == "high"),
    }

    email_draft = ""
    if escalated and escalation_email:
        crit = [e for e in escalated if e["priority"] == "critical"]
        items = "\n".join(f"  - [{e['id']}] {e['subject']} ({e['customer']}) — {e['reason'].replace('_',' ').title()}" for e in crit[:5])
        email_draft = (
            f"To: {escalation_email}\n"
            f"Subject: [URGENT] {stats['critical']} Critical Escalations — {business_name}\n\n"
            f"Hi Team,\n\nThe following tickets require immediate attention:\n\n{items}\n\n"
            f"Total escalated: {stats['escalated']} | Critical: {stats['critical']} | High: {stats['high']}\n\n"
            f"Please action within the next 30 minutes.\n\nRegards,\nSupport System"
        )

    return {
        "action":         "escalation_manager",
        "business_name":  business_name,
        "stats":          stats,
        "escalated":      escalated,
        "monitored":      monitored[:20],
        "resolved":       resolved[:10],
        "email_draft":    email_draft,
        "health":         "Critical" if stats["critical"] > 0 else ("At Risk" if stats["escalated"] > 0 else "Healthy"),
        "health_color":   "red" if stats["critical"] > 0 else ("orange" if stats["escalated"] > 0 else "green"),
    }


# ── Escalation Rule Builder (Round 10) ───────────────────────────────────────

_SLA_TIERS = {
    "startup": {
        "critical":  {"first_response": "1h",  "resolution": "4h",  "breach_action": "CEO notified"},
        "high":      {"first_response": "4h",  "resolution": "24h", "breach_action": "Team lead escalated"},
        "medium":    {"first_response": "8h",  "resolution": "48h", "breach_action": "Queue priority bumped"},
        "low":       {"first_response": "24h", "resolution": "72h", "breach_action": "Auto-reminder sent"},
    },
    "standard": {
        "critical":  {"first_response": "30m", "resolution": "2h",  "breach_action": "On-call engineer paged"},
        "high":      {"first_response": "2h",  "resolution": "8h",  "breach_action": "Manager escalated"},
        "medium":    {"first_response": "4h",  "resolution": "24h", "breach_action": "Priority bumped"},
        "low":       {"first_response": "8h",  "resolution": "48h", "breach_action": "Follow-up scheduled"},
    },
    "enterprise": {
        "critical":  {"first_response": "15m", "resolution": "1h",  "breach_action": "VP Customer Success paged + war room opened"},
        "high":      {"first_response": "1h",  "resolution": "4h",  "breach_action": "Senior engineer + CSM assigned"},
        "medium":    {"first_response": "2h",  "resolution": "12h", "breach_action": "Dedicated agent assigned"},
        "low":       {"first_response": "4h",  "resolution": "24h", "breach_action": "Next-day batch resolved"},
    },
}

_TRIGGER_LIBRARY = {
    "keyword_triggers": {
        "critical": ["down", "outage", "data loss", "breach", "hacked", "stolen", "refund", "legal", "lawyer", "fraud", "payment failed", "production down"],
        "high":     ["error", "broken", "not working", "urgent", "ASAP", "escalate", "frustrated", "disappointed", "cancel", "cancellation"],
        "medium":   ["slow", "delay", "waiting", "missing", "confused", "help", "issue", "problem", "bug"],
        "low":      ["question", "how to", "feature request", "suggestion", "inquiry", "information"],
    },
    "channel_priority": {
        "phone":     "high",
        "live_chat": "high",
        "email":     "medium",
        "whatsapp":  "medium",
        "twitter":   "high",
        "facebook":  "low",
        "portal":    "medium",
    },
    "customer_tier_boost": {
        "enterprise": "+1 level (low to medium, medium to high, high to critical)",
        "premium":    "+1 level for high and above",
        "standard":   "No boost",
        "trial":      "Medium cap (max medium priority)",
    },
    "time_based": [
        {"rule": "After 2h no first response: auto-bump priority by 1 level", "applies_to": "all"},
        {"rule": "After 50% SLA elapsed with no update: assign to available agent", "applies_to": "all"},
        {"rule": "After 80% SLA elapsed: manager notification sent", "applies_to": "critical, high"},
        {"rule": "After SLA breach: automatic CSAT score penalized; flagged in reporting", "applies_to": "all"},
    ],
}

_ROUTING_TEMPLATES = {
    "saas": [
        {"name": "Tier 1 Frontline", "handles": ["billing", "account", "password", "how-to", "feature questions"], "max_priority": "medium"},
        {"name": "Tier 2 Technical", "handles": ["bugs", "integrations", "API errors", "data issues"], "max_priority": "high"},
        {"name": "Tier 3 Engineering", "handles": ["production outages", "data loss", "security incidents"], "max_priority": "critical"},
        {"name": "CSM Team", "handles": ["enterprise renewals", "churn risk", "upsell conversations"], "max_priority": "high"},
    ],
    "ecommerce": [
        {"name": "Order Team", "handles": ["order status", "tracking", "delivery issues"], "max_priority": "medium"},
        {"name": "Returns Team", "handles": ["returns", "refunds", "exchanges"], "max_priority": "high"},
        {"name": "Payments Team", "handles": ["payment failures", "billing disputes", "fraud"], "max_priority": "critical"},
        {"name": "VIP Team", "handles": ["high-value customers", "repeat complainers"], "max_priority": "high"},
    ],
    "default": [
        {"name": "General Support", "handles": ["general inquiries", "basic troubleshooting"], "max_priority": "medium"},
        {"name": "Senior Support", "handles": ["complex issues", "complaints", "account issues"], "max_priority": "high"},
        {"name": "Management", "handles": ["escalations", "refunds above limit", "legal threats"], "max_priority": "critical"},
    ],
}

_NOTIFICATION_TEMPLATES = {
    "critical_breach":       "CRITICAL SLA BREACH — Ticket #{ticket_id} | Customer: {customer} | Issue: {summary} | Breached by: {breach_time} | Assigned to: {agent} | ACTION REQUIRED",
    "high_at_risk":          "SLA AT RISK — Ticket #{ticket_id} | {customer} | {category} | {pct}% SLA used | Reassign if {agent} is unavailable",
    "escalation_triggered":  "ESCALATION — {customer} ({tier} tier) escalated from {from_team} to {to_team} | Reason: {reason} | Priority: {priority}",
    "customer_update":       "Hi {customer_name}, your request (#{ticket_id}) has been escalated to our senior team and is now top priority. We will update you within {next_update_time}. — {company_name} Support",
    "breach_report":         "Daily SLA Report | {date} | Total: {total} | Breached: {breached} ({pct}%) | Critical open: {critical} | Avg resolution: {avg_res}h",
}


def _escalation_rule_builder(
    business_name: str,
    industry: str,
    team_structure: list,
    products: list,
    sla_tier: str,
) -> dict:
    tier_key = sla_tier if sla_tier in _SLA_TIERS else "standard"
    sla_rules = _SLA_TIERS[tier_key]

    industry_key = industry.lower() if industry.lower() in _ROUTING_TEMPLATES else "default"
    routing = _ROUTING_TEMPLATES[industry_key]

    if team_structure:
        routing = [
            {
                "name": t.get("name", "Support Team"),
                "handles": t.get("handles", ["general"]),
                "max_priority": t.get("max_priority", "medium"),
            }
            for t in team_structure
        ]

    priority_colors = {"critical": "#ef4444", "high": "#f97316", "medium": "#f59e0b", "low": "#22c55e"}
    escalation_matrix = []
    for priority in ["critical", "high", "medium", "low"]:
        sla = sla_rules[priority]
        keywords = _TRIGGER_LIBRARY["keyword_triggers"].get(priority, [])
        escalation_matrix.append({
            "priority":        priority,
            "color":           priority_colors[priority],
            "first_response":  sla["first_response"],
            "resolution_sla":  sla["resolution"],
            "breach_action":   sla["breach_action"],
            "trigger_keywords": keywords[:6],
            "notify_channels": ["email", "slack"] if priority in ["critical", "high"] else ["email"],
            "auto_assign":     priority in ["critical", "high"],
        })

    company = business_name or "Your Company"
    notification_templates = {k: v.replace("{company_name}", company) for k, v in _NOTIFICATION_TEMPLATES.items()}

    product_list = products if products else [f"{company} Core Product"]
    product_rules = [
        {
            "product": prod,
            "critical_keywords": ["down", "error", f"{prod} not working"],
            "owner_team": routing[min(2, len(routing) - 1)]["name"] if routing else "Senior Support",
        }
        for prod in product_list
    ]

    best_practices = [
        "Set up a Slack channel for critical escalations — real-time beats email for P1s.",
        "Use a warm transfer protocol so the receiving team has full context before the customer call.",
        f"Review SLA compliance weekly — target less than 5% breach rate at {tier_key} tier.",
        "Auto-tag VIP/enterprise customers in your helpdesk so routing fires immediately on ticket creation.",
        "Run monthly escalation retrospectives to identify recurring root causes and prevent repeats.",
        "Build a knowledge base article for every P1 ticket resolved — it prevents the next one.",
    ]

    return {
        "action":                 "escalation_rule_builder",
        "business_name":          company,
        "industry":               industry,
        "sla_tier":               tier_key,
        "escalation_matrix":      escalation_matrix,
        "routing_teams":          routing,
        "trigger_library":        _TRIGGER_LIBRARY,
        "notification_templates": notification_templates,
        "product_rules":          product_rules,
        "time_based_rules":       _TRIGGER_LIBRARY["time_based"],
        "best_practices":         best_practices,
        "summary":                f"Built {len(escalation_matrix)}-tier escalation matrix for {company} with {tier_key} SLA profile and {len(routing)} routing teams.",
    }


# ── Win-back Email Sequence (Round 12) ───────────────────────────────────────

_CHURN_REASON_FRAMES = {
    "price":       {"frame": "We heard your feedback on pricing", "angle": "value justification + special offer"},
    "competitor":  {"frame": "We know you have options", "angle": "differentiation + honest comparison"},
    "feature_gap": {"frame": "You told us something was missing", "angle": "product update + what's new"},
    "no_use":      {"frame": "Life gets busy — we get it", "angle": "re-engagement + quick win offer"},
    "bad_support": {"frame": "We dropped the ball, and we own it", "angle": "apology + new support promise"},
    "unknown":     {"frame": "We miss you", "angle": "curiosity + value reminder + offer"},
}

_OFFER_INTROS = {
    "discount":      "As a welcome-back gesture, we're offering you {value} off your first {period} back.",
    "free_months":   "We'd love to offer you {value} free — no commitment, no catch.",
    "upgrade":       "We want you to experience the full power of {product}. We're offering you a complimentary upgrade to {value} for 60 days.",
    "personal_call": "I'd love to personally jump on a 20-minute call to understand what didn't work and show you what's changed.",
    "credits":       "We've added {value} in credits to your account — ready and waiting for when you come back.",
}


def _winback_sequence(
    business_name: str,
    product_name: str,
    churned_customers: list,
    churn_reason: str,
    offer_type: str,
    offer_value: str,
    industry: str,
) -> dict:
    company = business_name or "Your Company"
    product = product_name or "our product"
    reason_key = churn_reason if churn_reason in _CHURN_REASON_FRAMES else "unknown"
    reason_cfg = _CHURN_REASON_FRAMES[reason_key]
    offer_key = offer_type if offer_type in _OFFER_INTROS else "discount"
    offer_intro = (_OFFER_INTROS[offer_key]
        .replace("{value}", offer_value)
        .replace("{product}", product)
        .replace("{period}", "3 months")
    )

    if not churned_customers:
        churned_customers = [
            {"name": "Ravi Kumar", "company": "Ravi Textiles", "churned_months_ago": 2, "arr": 85000, "last_feature_used": "Invoice Manager"},
            {"name": "Priya Shah",  "company": "Shah Enterprises", "churned_months_ago": 5, "arr": 120000, "last_feature_used": "GST Filing"},
        ]

    emails = [
        {
            "sequence_day": 1,
            "label":        "Email 1 — The Check-in (Soft)",
            "subject":      f"We noticed you left, {'{first_name}'} — can we ask why?",
            "body":         f"""Hi {{first_name}},

{reason_cfg['frame']}.

I'm [Your Name], and I wanted to reach out personally — not with a sales pitch, but with a genuine question: what didn't work for you with {product}?

Your feedback directly shapes our roadmap. If you have 2 minutes, I'd love to hear what we could have done better.

And if there's any chance we can win you back, I'd love to explore that too.

Just hit reply — I read every response personally.

{company} Team
[Email] | [Phone]

P.S. If the timing just wasn't right before, we'd love to show you what's changed.""",
            "send_timing":  "Day 1 — send within 48h of identifying the churned customer",
            "goal":         "Open the door — get a reply or click",
        },
        {
            "sequence_day": 7,
            "label":        "Email 2 — The Value Reminder",
            "subject":      f"Remember when {product} helped you with [specific use case]?",
            "body":         f"""Hi {{first_name}},

Since you left, here's what's new at {company}:

✅ [New feature 1 — specific to their last used feature]
✅ [New feature 2 — addresses the gap they had]
✅ [Improvement — performance / speed / UX]

We've also heard feedback from customers like you and made [specific change] a priority.

{offer_intro}

This offer is exclusively for you — it expires in 7 days.

[CTA Button: Come Back and Try It →]

No long-term commitment. Just a chance to see what's different.

Warm regards,
[Your Name]
{company}""",
            "send_timing":  "Day 7 — after the soft check-in",
            "goal":         "Show what changed + introduce the offer",
        },
        {
            "sequence_day": 21,
            "label":        "Email 3 — The Offer + Social Proof",
            "subject":      f"[First name], other {industry} businesses are seeing [result] with {product}",
            "body":         f"""Hi {{first_name}},

I wanted to share something before I close the loop.

Since last year, here's what customers like you have achieved with {product}:

"[Customer quote about specific result — 1-2 sentences]" — [Customer Name, Company]

"[Another customer quote]" — [Name, Company]

If you've been on the fence, this might be the nudge you need.

Our offer ({offer_value}) is still available for you — but it expires at end of this week.

[CTA: Claim My Offer →]

If you've moved on for good, no hard feelings — just let me know and I'll stop reaching out. 🙏

[Your Name]
{company}""",
            "send_timing":  "Day 21 — social proof + urgency",
            "goal":         "Convert with social proof + scarcity",
        },
        {
            "sequence_day": 45,
            "label":        "Email 4 — The Breakup (Final)",
            "subject":      f"This is our last email, {{first_name}} — closing your file",
            "body":         f"""Hi {{first_name}},

I don't want to fill your inbox if {product} isn't right for you anymore.

This is the last email we'll send — promise.

But before we go, I'd love to know: is there anything we could have done differently? Even one line would mean a lot to our team.

[CTA: Tell us in 1 click →] (quick 2-question survey)

If you ever want to come back, we'll be here. Your data is kept safe for 90 days.

Thank you for the time you gave us, and I genuinely wish you the best.

[Your Name], {company}

P.S. If your situation changes and you want to try again, just reply to this email. We'll always have a spot for you.""",
            "send_timing":  "Day 45 — final email, close the loop",
            "goal":         "Exit survey + leave the door open",
        },
    ]

    per_customer = []
    for c in churned_customers[:10]:
        name = c.get("name", "Customer")
        first = name.split()[0]
        comp = c.get("company", "")
        months_ago = c.get("churned_months_ago", 3)
        arr = float(c.get("arr", 0))
        last_feat = c.get("last_feature_used", "")

        priority = "high" if arr > 100000 else ("medium" if arr > 50000 else "low")
        start_email = 1 if months_ago <= 3 else (2 if months_ago <= 6 else 3)

        per_customer.append({
            "name":           name,
            "first_name":     first,
            "company":        comp,
            "churned_months_ago": months_ago,
            "arr":            arr,
            "last_feature":   last_feat,
            "winback_priority": priority,
            "start_at_email": start_email,
            "personalization_note": f"Mention {last_feat} improvement in Email 2" if last_feat else "Highlight top 3 new features",
            "expected_winback_rate": "15-25%" if priority == "high" else "8-15%",
        })

    per_customer.sort(key=lambda x: x["arr"], reverse=True)

    best_practices = [
        "Win-back campaigns work best within 90 days of churn — after that, conversion rates drop significantly.",
        "Personalize the subject line with their first name AND their company — doubles open rates.",
        "Never start with the offer — build curiosity and empathy first (Email 1 is a check-in, not a pitch).",
        "High-ARR accounts deserve a phone call, not just email — pick up the phone for accounts over ₹1L ARR.",
        "Exit surveys from churned customers are your best product research — read every response.",
        f"Average B2B SaaS win-back rate is 10-20%. At {industry} industry rates, expect 8-18% with this sequence.",
    ]

    return {
        "action":             "winback_sequence",
        "business_name":      company,
        "product_name":       product,
        "churn_reason":       churn_reason,
        "offer_type":         offer_type,
        "offer_value":        offer_value,
        "email_sequence":     emails,
        "customer_queue":     per_customer,
        "total_arr_at_risk":  sum(c["arr"] for c in per_customer),
        "best_practices":     best_practices,
        "summary": f"Generated {len(emails)}-email win-back sequence for {len(per_customer)} churned customer(s). Total ARR at stake: ₹{sum(c['arr'] for c in per_customer)/100000:.1f}L. Churn reason: {churn_reason}.",
    }


# ── Customer Health Score (Round 11) ─────────────────────────────────────────

_HEALTH_SIGNALS = {
    "login_frequency":    {"weight": 20, "desc": "How often they log in / use the product"},
    "feature_adoption":   {"weight": 18, "desc": "% of core features actively used"},
    "support_tickets":    {"weight": -15, "desc": "High ticket volume = friction (negative signal)"},
    "nps_score":          {"weight": 15, "desc": "Net Promoter Score (0-10)"},
    "payment_history":    {"weight": 12, "desc": "On-time payments = commitment signal"},
    "engagement_score":   {"weight": 10, "desc": "Email opens, webinar attendance, community activity"},
    "contract_length":    {"weight": 8,  "desc": "Longer contract = higher commitment"},
    "expansion_revenue":  {"weight": 10, "desc": "Upsells, seat additions = growing value"},
    "last_activity_days": {"weight": -12, "desc": "Days since last login (negative — recency matters)"},
}

_SEGMENT_PLAYBOOKS = {
    "champion": {
        "label": "Champion",
        "color": "#22c55e",
        "score_range": "80-100",
        "description": "Highly engaged, expanding, likely to refer",
        "actions": [
            "Ask for a case study or testimonial — they will usually say yes",
            "Invite to your customer advisory board or beta program",
            "Identify upsell opportunity — they are ready to grow with you",
            "Create referral incentive — champions drive 40% of new pipeline in SaaS",
            "Feature them in marketing content (with permission)",
        ],
    },
    "healthy": {
        "label": "Healthy",
        "color": "#10b981",
        "score_range": "60-79",
        "description": "Good engagement, stable usage, renewal likely",
        "actions": [
            "Proactive check-in call every quarter to surface unmet needs",
            "Share new features relevant to their use case",
            "Identify a power user to champion internal adoption",
            "Send ROI report showing value delivered since onboarding",
        ],
    },
    "at_risk": {
        "label": "At Risk",
        "color": "#f59e0b",
        "score_range": "40-59",
        "description": "Declining engagement or friction detected",
        "actions": [
            "Immediate CSM outreach — do not wait for them to contact you",
            "Run a health review call to understand root cause of disengagement",
            "Offer a re-onboarding session if feature adoption is low",
            "Identify internal champion — key contact may have left",
            "Consider a temporary discount or service upgrade to re-engage",
        ],
    },
    "critical": {
        "label": "Critical",
        "color": "#f97316",
        "score_range": "20-39",
        "description": "High churn risk — needs urgent intervention",
        "actions": [
            "Escalate to senior CSM or VP Customer Success immediately",
            "Schedule an executive-to-executive call within 48 hours",
            "Prepare a save plan: address root cause, offer incentive, show roadmap",
            "Understand if a competitor is involved — address it directly",
            "If contract is ending within 90 days, start renewal conversation now",
        ],
    },
    "churned": {
        "label": "Churned / Inactive",
        "color": "#ef4444",
        "score_range": "0-19",
        "description": "Likely inactive or has churned",
        "actions": [
            "Run an exit interview — understanding why they left prevents future churn",
            "Pause all marketing emails — churned customers unsubscribe if pressured",
            "Start a win-back sequence at 60 and 90 days post-churn",
            "Flag account for product team — repeated churn patterns signal product gaps",
        ],
    },
}


def _customer_health_score(
    customers: list,
    business_name: str,
    product_name: str,
    industry: str,
) -> dict:
    if not customers:
        customers = [
            {"name": "Ravi Textiles", "login_frequency": 8, "feature_adoption": 75, "support_tickets": 2, "nps_score": 8, "payment_history": 100, "engagement_score": 7, "contract_length": 12, "expansion_revenue": 1, "last_activity_days": 2, "arr": 120000, "csm": "Priya"},
            {"name": "ABC Pharma Ltd", "login_frequency": 3, "feature_adoption": 40, "support_tickets": 8, "nps_score": 5, "payment_history": 80, "engagement_score": 4, "contract_length": 6, "expansion_revenue": 0, "last_activity_days": 18, "arr": 85000, "csm": "Arjun"},
            {"name": "Sharma & Sons", "login_frequency": 1, "feature_adoption": 20, "support_tickets": 12, "nps_score": 3, "payment_history": 60, "engagement_score": 2, "contract_length": 3, "expansion_revenue": 0, "last_activity_days": 45, "arr": 60000, "csm": "Meera"},
            {"name": "TechStart Solutions", "login_frequency": 10, "feature_adoption": 90, "support_tickets": 1, "nps_score": 10, "payment_history": 100, "engagement_score": 9, "contract_length": 24, "expansion_revenue": 3, "last_activity_days": 1, "arr": 240000, "csm": "Priya"},
            {"name": "Krishna Exports", "login_frequency": 5, "feature_adoption": 55, "support_tickets": 5, "nps_score": 6, "payment_history": 90, "engagement_score": 5, "contract_length": 12, "expansion_revenue": 1, "last_activity_days": 7, "arr": 95000, "csm": "Arjun"},
        ]

    scored = []
    for cust in customers:
        login = min(float(cust.get("login_frequency", 5)), 10) / 10
        feature = min(float(cust.get("feature_adoption", 50)), 100) / 100
        tickets = min(float(cust.get("support_tickets", 3)), 15) / 15
        nps = min(float(cust.get("nps_score", 5)), 10) / 10
        payment = min(float(cust.get("payment_history", 80)), 100) / 100
        engagement = min(float(cust.get("engagement_score", 5)), 10) / 10
        contract = min(float(cust.get("contract_length", 6)), 24) / 24
        expansion = min(float(cust.get("expansion_revenue", 0)), 5) / 5
        recency = min(float(cust.get("last_activity_days", 7)), 60) / 60

        raw = (
            login * 20
            + feature * 18
            - tickets * 15
            + nps * 15
            + payment * 12
            + engagement * 10
            + contract * 8
            + expansion * 10
            - recency * 12
        )
        score = max(0, min(100, int(raw)))

        if score >= 80:
            seg = "champion"
        elif score >= 60:
            seg = "healthy"
        elif score >= 40:
            seg = "at_risk"
        elif score >= 20:
            seg = "critical"
        else:
            seg = "churned"

        playbook = _SEGMENT_PLAYBOOKS[seg]

        risk_flags = []
        if float(cust.get("last_activity_days", 0)) > 14:
            risk_flags.append(f"No login for {int(cust.get('last_activity_days', 0))} days")
        if float(cust.get("support_tickets", 0)) > 6:
            risk_flags.append(f"{int(cust.get('support_tickets', 0))} open/recent tickets")
        if float(cust.get("feature_adoption", 100)) < 40:
            risk_flags.append(f"Low feature adoption ({int(cust.get('feature_adoption', 0))}%)")
        if float(cust.get("nps_score", 10)) < 5:
            risk_flags.append(f"Low NPS: {cust.get('nps_score')}/10")
        if float(cust.get("payment_history", 100)) < 80:
            risk_flags.append("Payment delays detected")

        scored.append({
            "name":          cust.get("name", "Customer"),
            "health_score":  score,
            "segment":       seg,
            "segment_label": playbook["label"],
            "color":         playbook["color"],
            "arr":           float(cust.get("arr", 0)),
            "csm":           cust.get("csm", "Unassigned"),
            "risk_flags":    risk_flags,
            "actions":       playbook["actions"][:3],
            "signals": {
                "login_frequency":  cust.get("login_frequency"),
                "feature_adoption": cust.get("feature_adoption"),
                "support_tickets":  cust.get("support_tickets"),
                "nps_score":        cust.get("nps_score"),
                "last_active_days": cust.get("last_activity_days"),
            },
        })

    scored.sort(key=lambda x: x["health_score"])

    seg_counts = {}
    arr_at_risk = 0.0
    for s in scored:
        seg_counts[s["segment"]] = seg_counts.get(s["segment"], 0) + 1
        if s["segment"] in ("at_risk", "critical", "churned"):
            arr_at_risk += s["arr"]

    avg_score = sum(s["health_score"] for s in scored) / len(scored) if scored else 0
    total_arr = sum(s["arr"] for s in scored)

    return {
        "action":           "customer_health_score",
        "business_name":    business_name or "Your Business",
        "product_name":     product_name or "Product",
        "total_customers":  len(scored),
        "avg_health_score": round(avg_score, 1),
        "total_arr":        round(total_arr, 0),
        "arr_at_risk":      round(arr_at_risk, 0),
        "segment_breakdown": seg_counts,
        "customers":        scored,
        "segment_playbooks": _SEGMENT_PLAYBOOKS,
        "summary": f"Scored {len(scored)} customers. Avg health: {avg_score:.0f}/100. ₹{arr_at_risk/100000:.1f}L ARR at risk ({len([s for s in scored if s['segment'] in ('at_risk','critical','churned')])} accounts need attention).",
    }
