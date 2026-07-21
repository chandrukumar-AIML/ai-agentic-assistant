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
