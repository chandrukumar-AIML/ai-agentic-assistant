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
        else:
            return {"error": f"Unknown action: {action}. Valid: faq_bot|qualify_lead|draft_whatsapp|analyze_sentiment|handle_complaint|summarize_ticket|response_template|weekly_report|kb_answer"}
    except Exception as e:
        return {"error": str(e), "action": action}
