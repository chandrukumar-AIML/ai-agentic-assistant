"""Customer Support Agent — WhatsApp-first, India SMB focused."""
from __future__ import annotations

import json
from datetime import datetime


def _llm(prompt: str, system: str = "") -> str:
    import asyncio
    import concurrent.futures
    import time

    msgs: list[dict] = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})

    def _run_in_thread() -> str:
        from openai import AsyncOpenAI

        from backend.llm.ollama_openai import OLLAMA_API_KEY, OLLAMA_BASE_URL, OLLAMA_MODEL

        async def _call() -> str:
            client = AsyncOpenAI(base_url=OLLAMA_BASE_URL, api_key=OLLAMA_API_KEY, timeout=90.0, max_retries=0)
            try:
                resp = await client.chat.completions.create(model=OLLAMA_MODEL, messages=msgs, temperature=0.7, max_tokens=1024)
                return resp.choices[0].message.content or ""
            except BaseException:
                return ""

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_call())
        except BaseException:
            return ""
        finally:
            loop.close()

    for attempt in range(3):
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                result = pool.submit(_run_in_thread).result(timeout=120)
            if result:
                return result
        except BaseException:
            pass
        if attempt < 2:
            time.sleep(2)
    return ""


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

    try:
        message = _llm(prompt, system=sys_prompt)
    except Exception:
        message = ""

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

    try:
        raw = _llm(prompt, system=sys_prompt)
    except Exception:
        raw = ""
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
                "subject_or_opening": "Hey [CUSTOMER_NAME]! 👋",
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

    try:
        raw = _llm(prompt, system=sys_prompt)
    except Exception:
        raw = ""
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
                start = raw.index("{")
                end = raw.rindex("}") + 1
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

        elif action == "ticket_triage":
            return score_ticket_priority(
                ticket_text=payload.get("ticket_text", ""),
                customer_name=payload.get("customer_name", ""),
                channel=payload.get("channel", "email"),
                customer_tier=payload.get("customer_tier", "standard"),
                is_repeat_contact=payload.get("is_repeat_contact", False),
                language=language,
            )

        elif action == "voc_report":
            return generate_voc_report(
                company_name=payload.get("company_name", ""),
                period=payload.get("period", "Q1 FY 2025-26"),
                total_responses=payload.get("total_responses", 0),
                nps_score=payload.get("nps_score", 0.0),
                csat_score=payload.get("csat_score", 0.0),
                top_positive_themes=payload.get("top_positive_themes", []),
                top_negative_themes=payload.get("top_negative_themes", []),
                data_sources=payload.get("data_sources", []),
                verbatim_samples=payload.get("verbatim_samples", []),
                language=language,
            )

        elif action == "review_response":
            return generate_review_response_kit(
                business_name=payload.get("business_name", ""),
                product_name=payload.get("product_name", ""),
                platform=payload.get("platform", "google"),
                review_text=payload.get("review_text", ""),
                star_rating=payload.get("star_rating", 5),
                reviewer_name=payload.get("reviewer_name", "there"),
                support_email=payload.get("support_email", ""),
                language=language,
            )

        elif action == "sla_policy":
            return generate_sla_policy(
                company_name=payload.get("company_name", ""),
                plan_tiers=payload.get("plan_tiers", ["basic","standard","premium"]),
                support_channels=payload.get("support_channels", ["chat","email"]),
                business_hours=payload.get("business_hours", "Mon–Sat, 9am–6pm IST"),
                language=language,
            )

        elif action == "agent_training":
            return generate_agent_training_manual(
                company_name=payload.get("company_name", ""),
                industry=payload.get("industry", "general"),
                support_channels=payload.get("support_channels", ["chat", "email"]),
                tone=payload.get("tone", "friendly"),
                language=language,
            )

        elif action == "chatbot_script":
            return generate_chatbot_script(
                business_name=payload.get("business_name", ""),
                industry=payload.get("industry", "ecommerce"),
                bot_name=payload.get("bot_name", ""),
                top_faqs=payload.get("top_faqs", []),
                escalation_trigger=payload.get("escalation_trigger", ""),
                tone=payload.get("tone", "friendly"),
                platform=payload.get("platform", "whatsapp"),
                language=language,
            )
        elif action == "returns_policy":
            return generate_returns_policy(
                business_name=payload.get("business_name", ""),
                industry=payload.get("industry", "ecommerce"),
                custom_return_days=int(payload.get("return_days", 0)),
                custom_refund_days=int(payload.get("refund_days", 0)),
                refund_modes=payload.get("refund_modes", []),
                contact_email=payload.get("contact_email", ""),
                contact_phone=payload.get("contact_phone", ""),
                language=language,
            )
        elif action == "support_analytics":
            return generate_support_analytics(
                business_name=payload.get("business_name", ""),
                industry=payload.get("industry", "saas"),
                week_label=payload.get("week_label", "This Week"),
                total_tickets=payload.get("total_tickets", 0),
                resolved_tickets=payload.get("resolved_tickets", 0),
                avg_frt_hrs=payload.get("avg_frt_hrs", 4),
                avg_resolution_hrs=payload.get("avg_resolution_hrs", 24),
                csat_score=payload.get("csat_score", 4.0),
                ticket_categories=payload.get("ticket_categories", {}),
                agent_data=payload.get("agent_data", []),
                channel_data=payload.get("channel_data", {}),
                prev_week_tickets=payload.get("prev_week_tickets", 0),
                prev_week_csat=payload.get("prev_week_csat", 4.0),
            )

        elif action == "customer_360":
            return generate_customer_360(
                customer_name=payload.get("customer_name", ""),
                customer_email=payload.get("customer_email", ""),
                customer_since_months=payload.get("customer_since_months", 1),
                total_orders=payload.get("total_orders", 1),
                total_revenue=payload.get("total_revenue", 0),
                last_order_days_ago=payload.get("last_order_days_ago", 0),
                open_tickets=payload.get("open_tickets", 0),
                total_tickets=payload.get("total_tickets", 0),
                avg_resolution_hrs=payload.get("avg_resolution_hrs", 24),
                avg_csat=payload.get("avg_csat", 4.0),
                plan_type=payload.get("plan_type", "Standard"),
                has_referred=payload.get("has_referred", False),
                payment_status=payload.get("payment_status", "current"),
            )

        elif action == "csat_survey":
            return _csat_survey_builder(
                business_name=payload.get("business_name", ""),
                product_name=payload.get("product_name", ""),
                survey_goal=payload.get("survey_goal", "overall"),
                customer_segment=payload.get("customer_segment", "all"),
                industry=payload.get("industry", "saas"),
                max_questions=payload.get("max_questions", 8),
                include_nps=payload.get("include_nps", True),
            )

        elif action == "winback_campaign":
            return _winback_campaign_generator(
                business_name=payload.get("business_name", ""),
                product_name=payload.get("product_name", ""),
                customer_name=payload.get("customer_name", ""),
                churn_reason=payload.get("churn_reason", "unknown"),
                inactive_days=payload.get("inactive_days", 30),
                industry=payload.get("industry", "saas"),
                offer_type=payload.get("offer_type", "discount"),
                offer_value=payload.get("offer_value", "20%"),
                cs_rep_name=payload.get("cs_rep_name", ""),
            )

        elif action == "escalation_email":
            return _escalation_email_generator(
                business_name=payload.get("business_name", ""),
                customer_name=payload.get("customer_name", ""),
                ticket_id=payload.get("ticket_id", ""),
                issue_summary=payload.get("issue_summary", ""),
                sla_breached=payload.get("sla_breached", ""),
                priority=payload.get("priority", "high"),
                escalation_type=payload.get("escalation_type", "internal"),
                escalate_to=payload.get("escalate_to", ""),
                cs_rep_name=payload.get("cs_rep_name", ""),
                current_status=payload.get("current_status", ""),
                customer_tier=payload.get("customer_tier", "standard"),
            )

        elif action == "kb_article":
            return _kb_article_generator(
                business_name=payload.get("business_name", ""),
                product_name=payload.get("product_name", ""),
                article_topic=payload.get("article_topic", ""),
                article_type=payload.get("article_type", "how_to"),
                industry=payload.get("industry", "saas"),
                audience=payload.get("audience", "end_user"),
                tone=payload.get("tone", "friendly"),
            )

        elif action == "onboarding_sequence":
            return _onboarding_sequence_builder(
                business_name=payload.get("business_name", ""),
                product_name=payload.get("product_name", ""),
                industry=payload.get("industry", "saas"),
                customer_type=payload.get("customer_type", "smb"),
                key_features=payload.get("key_features", []),
                success_metric=payload.get("success_metric", ""),
                cs_rep_name=payload.get("cs_rep_name", ""),
            )

        elif action == "nps_campaign_builder":
            return _nps_campaign_builder(
                business_name=payload.get("business_name", ""),
                product_name=payload.get("product_name", ""),
                industry=payload.get("industry", "saas"),
                responses=payload.get("responses", []),
                survey_channel=payload.get("survey_channel", "email"),
            )

        elif action == "agent_performance_scorecard":
            return _agent_performance_scorecard(
                agents=payload.get("agents", []),
                business_name=payload.get("business_name", ""),
                period=payload.get("period", ""),
                team_targets=payload.get("team_targets", {}),
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
                language=language,
            )

        elif action == "onboarding_planner":
            return _onboarding_planner(
                customer_name=payload.get("customer_name", ""),
                product_name=payload.get("product_name", ""),
                industry=payload.get("industry", ""),
                tier=payload.get("tier", "standard"),
                goals=payload.get("goals", []),
                team_size=int(payload.get("team_size", 1) or 1),
                language=language,
            )

        elif action == "churn_risk":
            return _churn_risk_analyzer(
                customers=payload.get("customers", []),
                business_name=payload.get("business_name", ""),
                industry=payload.get("industry", "saas"),
                language=language,
            )

        elif action == "escalation_manager":
            return _escalation_manager(
                tickets=payload.get("tickets", []),
                rules=payload.get("rules", {}),
                business_name=payload.get("business_name", ""),
                escalation_email=payload.get("escalation_email", ""),
                language=language,
            )

        elif action == "build_csat_survey":
            return _build_csat_survey(
                business_name=payload.get("business_name", ""),
                business_type=payload.get("business_type", ""),
                touchpoints=payload.get("touchpoints", []),
                language=language,
            )

        elif action == "analyze_csat":
            return _analyze_csat(
                responses=payload.get("responses", []),
                business_name=payload.get("business_name", ""),
            )

        elif action == "support_command_center":
            return await generate_support_command_center(payload, language)
        elif action == "cx_goal_planner":
            return await generate_cx_goal_plan(
                goal=payload.get("goal", "improve_csat"),
                workspace=payload,
                timeline=payload.get("timeline", "30 days"),
                language=language,
            )
        elif action == "response_quality_score":
            return await score_response_quality(
                response_text=payload.get("response_text", ""),
                ticket_subject=payload.get("ticket_subject", ""),
                customer_tier=payload.get("customer_tier", "Standard"),
                language=language,
            )
        elif action == "cs_strategy_meeting":
            return await run_cs_strategy_meeting(
                workspace=payload,
                focus=payload.get("focus", "csat"),
                language=language,
            )

        else:
            return {"error": f"Unknown action: {action}"}
    except Exception as e:
        return {"error": str(e), "action": action}


async def call_llm(prompt: str, system: str = "") -> str:
    from backend.llm.llm_router import call_llm as _router
    return await _router(prompt, system)


# ── Support Command Center ────────────────────────────────────────────────────
async def generate_support_command_center(workspace: dict, language: str) -> dict:
    company   = workspace.get("company_name", "the company")
    btype     = workspace.get("business_type", "")
    tone      = workspace.get("support_tone", "professional")
    sla_resp  = workspace.get("sla_first_response", "4")
    prompt = f"""You are an expert Customer Support Director giving a daily command center briefing.

Company: {company} | Type: {btype} | Tone: {tone} | SLA First Response: {sla_resp}h

Generate a structured daily support briefing with these exact sections:
1. TICKET PULSE — Open tickets by priority (Critical/High/Medium/Low), SLA violations count
2. CSAT WATCH — Today's satisfaction score estimate, trend (up/down), key driver
3. TOP ISSUES — 3 most common complaint themes this week
4. AGENT PERFORMANCE — Team health: who's overloaded, who needs support
5. TOP 3 ACTIONS — The 3 most critical things for the support lead to do right now
6. SUPPORT HEALTH SCORE — Rate overall support operations 0-100 with one-line verdict

Format with bold headers. Be specific and actionable for an Indian SMB support team.
Language: {language}"""
    result = await call_llm(prompt, "You are an expert Customer Support Director.")
    return {"briefing": result, "company": company}


# ── CX Goal Planner ───────────────────────────────────────────────────────────
_CX_GOAL_LABELS = {
    "improve_csat":      "Improve CSAT Score",
    "reduce_response":   "Reduce First Response Time",
    "reduce_churn":      "Reduce Customer Churn",
    "handle_spike":      "Handle Ticket Spike / Peak Season",
    "launch_kb":         "Launch Knowledge Base",
    "improve_fcr":       "Improve First Contact Resolution",
    "agent_coaching":    "Agent Skill Improvement Program",
    "nps_campaign":      "NPS Improvement Campaign",
}

async def generate_cx_goal_plan(goal: str, workspace: dict, timeline: str, language: str) -> dict:
    company = workspace.get("company_name", "the company")
    btype   = workspace.get("business_type", "")
    tone    = workspace.get("support_tone", "professional")
    label   = _CX_GOAL_LABELS.get(goal, goal.replace("_", " ").title())
    prompt = f"""You are an expert CX Director building a full action plan.

Goal: {label}
Company: {company} | Type: {btype} | Tone: {tone} | Timeline: {timeline}

Generate a detailed CX action plan with:
1. GOAL SUMMARY — What success looks like in one sentence
2. WEEK-BY-WEEK PLAN — Break {timeline} into weekly milestones with specific tasks
3. QUICK WINS — 3 things you can do in the first 48 hours
4. METRICS TO TRACK — 5 KPIs with target values and how to measure them
5. AGENT ENABLEMENT — Training, tools, or process changes needed
6. CUSTOMER COMMUNICATION — Messages to send to customers as part of this initiative
7. RISK FLAGS — What could go wrong and how to handle it

Be specific and actionable for an Indian SMB. Language: {language}"""
    result = await call_llm(prompt, "You are an expert CX Director at an Indian company.")
    return {"campaign": result, "goal": label, "company": company}


# ── Response Quality Score ────────────────────────────────────────────────────
async def score_response_quality(response_text: str, ticket_subject: str, customer_tier: str, language: str) -> dict:
    prompt = f"""You are a CX quality expert scoring a customer support response.

Ticket Subject: {ticket_subject or 'General inquiry'}
Customer Tier: {customer_tier}
Draft Response:
---
{response_text}
---

Score this response on 6 dimensions (0-100 each):

1. EMPATHY — Does it acknowledge the customer's emotion and situation?
2. CLARITY — Is the response clear, concise, and easy to understand?
3. RESOLUTION — Does it actually solve or address the customer's problem?
4. TONE — Is the tone appropriate (not too formal, not too casual)?
5. COMPLETENESS — Does it cover all parts of the customer's issue?
6. BRAND_VOICE — Does it reflect a professional, trustworthy brand?

Return ONLY valid JSON in this exact format:
{{
  "scores": {{"empathy": 0-100, "clarity": 0-100, "resolution": 0-100, "tone": 0-100, "completeness": 0-100, "brand_voice": 0-100, "overall": 0-100}},
  "reasons": {{"empathy": "one line", "clarity": "one line", "resolution": "one line", "tone": "one line", "completeness": "one line", "brand_voice": "one line"}},
  "verdict": "one sentence overall verdict",
  "top_improvement": "single most impactful change to make"
}}"""
    raw = await call_llm(prompt, "You are a CX quality expert.")
    import json
    import re
    try:
        m = re.search(r'\{[\s\S]*\}', raw)
        parsed = json.loads(m.group()) if m else {}
    except Exception:
        parsed = {}
    if "scores" not in parsed:
        parsed = {
            "scores":  {"empathy": 70, "clarity": 70, "resolution": 70, "tone": 70, "completeness": 70, "brand_voice": 70, "overall": 70},
            "reasons": {"empathy": "", "clarity": "", "resolution": "", "tone": "", "completeness": "", "brand_voice": ""},
            "verdict": raw[:200], "top_improvement": "",
        }
    return parsed


# ── CS Strategy Meeting ───────────────────────────────────────────────────────
_CS_FOCUS_LABELS = {
    "csat":       "CSAT & Customer Satisfaction",
    "churn":      "Churn Prevention Strategy",
    "escalation": "Escalation Management",
    "capacity":   "Team Capacity & Hiring",
    "automation": "Automation & Self-Service",
    "voc":        "Voice of Customer Analysis",
}

async def run_cs_strategy_meeting(workspace: dict, focus: str, language: str) -> dict:
    company = workspace.get("company_name", "the company")
    btype   = workspace.get("business_type", "")
    tone    = workspace.get("support_tone", "professional")
    label   = _CS_FOCUS_LABELS.get(focus, focus.replace("_", " ").title())
    prompt = f"""You are running an AI Customer Support strategy meeting with 4 expert agents.

Company: {company} | Type: {btype} | Tone: {tone}
Meeting Focus: {label}

Each agent speaks in their own voice with their name prefix:

👩‍💼 KAVITHA (CX Director): Opens with the big picture — customer experience vision and metrics
🔍 ROHAN (Quality Lead): Highlights quality gaps, common failure points, coaching opportunities
💚 ANANYA (Retention Specialist): Focuses on churn signals, at-risk customers, win-back plays
⚡ DEV (Escalation Manager): Identifies systemic issues causing escalations and fixes needed

Then:
✅ DECISIONS: 3 concrete decisions the team agrees on
📋 ACTION ITEMS: 5 specific next steps with owner names and deadlines
🎯 MEETING VERDICT: One-sentence summary of the meeting outcome

Be specific and actionable for an Indian SMB support team. Language: {language}"""
    result = await call_llm(prompt, "You are a senior CX Director running a strategy meeting.")
    return {"meeting": result, "company": company, "focus": label}


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
    from datetime import datetime, timezone

    rules = {**_DEFAULT_SLA, **sla_rules}
    now   = datetime.now(timezone.utc)

    def parse_dt(s):
        if not s:
            return None
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
            if t.get("res_breached"):
                assignee_map[a]["breached"] += 1
            if t.get("resolved"):
                assignee_map[a]["resolved"] += 1

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

    # Custom categories first (support both string and dict entries)
    for cc in custom_categories:
        if isinstance(cc, str):
            if cc.lower() in text_lower:
                return cc, "Support", "medium", 24, "#6b7280"
        elif isinstance(cc, dict):
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
            "subject":      "This is our last email, {first_name} — closing your file",
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


# ── Agent Performance Scorecard (Round 13) ────────────────────────────────────

_DEFAULT_TARGETS = {
    "first_response_time_min": 60,
    "resolution_time_hours":   24,
    "csat_score":              4.2,
    "tickets_per_day":         20,
    "fcr_pct":                 75,
    "reopen_rate_pct":         5,
    "escalation_rate_pct":     8,
}

_PERFORMANCE_TIERS = {
    "star":       {"min": 85, "label": "Star Agent",      "color": "green",  "badge": "Star"},
    "solid":      {"min": 70, "label": "Solid Performer", "color": "blue",   "badge": "Good"},
    "developing": {"min": 55, "label": "Developing",      "color": "yellow", "badge": "Growing"},
    "needs_help": {"min": 0,  "label": "Needs Coaching",  "color": "red",    "badge": "Coach"},
}

_COACHING_LIBRARY = {
    "first_response_time_min": {
        "slow": "Set up canned responses for top 10 queries. Use keyboard shortcuts. Triage P1s first before starting on lower priority.",
        "fast": "Excellent first response time! Consider mentoring newer agents via shadow sessions.",
    },
    "csat_score": {
        "low":  "Review last 20 low-CSAT tickets for patterns: tone, resolution quality, or empathy gaps. Schedule a listening session.",
        "high": "High CSAT — share your response templates with the team. Host a 'What Works' knowledge share session.",
    },
    "fcr_pct": {
        "low":  "Low FCR usually means product knowledge gaps. Build KB articles for your top 5 recurring issue types.",
        "high": "High FCR signals deep product knowledge. Candidate for tier-2 specialist or team lead track.",
    },
    "reopen_rate_pct": {
        "high": "High reopens indicate partial resolutions. Add 'Before I close — anything else?' as a mandatory closing phrase.",
        "low":  "Low reopen rate shows thorough resolutions. Your closing technique is a best practice — document it.",
    },
    "escalation_rate_pct": {
        "high": "High escalations suggest empowerment gaps. Review what was escalated — could 60% be resolved with better tools or authority?",
        "low":  "Low escalations show strong ownership. Ensure you are not under-escalating complex issues that need specialist eyes.",
    },
    "tickets_per_day": {
        "low":  "Throughput below target. Flag tickets over 30 minutes to TL. Use 2-minute rule: reply or escalate, do not sit on tickets.",
        "high": "High throughput! Monitor CSAT alongside — speed should not sacrifice quality.",
    },
}


def _agent_performance_scorecard(
    agents: list,
    business_name: str,
    period: str,
    team_targets: dict,
) -> dict:
    company = business_name or "Your Team"
    per = period or "This Month"
    targets = {**_DEFAULT_TARGETS, **(team_targets or {})}

    demo_agents = agents if agents else [
        {"name": "Priya S.",   "first_response_time_min": 18, "resolution_time_hours": 6,  "csat_score": 4.7, "tickets_per_day": 28, "fcr_pct": 88, "reopen_rate_pct": 2, "escalation_rate_pct": 4, "tenure_months": 18},
        {"name": "Rahul M.",   "first_response_time_min": 45, "resolution_time_hours": 14, "csat_score": 4.1, "tickets_per_day": 22, "fcr_pct": 71, "reopen_rate_pct": 7, "escalation_rate_pct": 9, "tenure_months": 7},
        {"name": "Ananya K.",  "first_response_time_min": 90, "resolution_time_hours": 28, "csat_score": 3.8, "tickets_per_day": 14, "fcr_pct": 58, "reopen_rate_pct": 12, "escalation_rate_pct": 18, "tenure_months": 3},
        {"name": "Vikram T.",  "first_response_time_min": 25, "resolution_time_hours": 9,  "csat_score": 4.5, "tickets_per_day": 24, "fcr_pct": 82, "reopen_rate_pct": 3, "escalation_rate_pct": 6, "tenure_months": 14},
        {"name": "Deepika R.", "first_response_time_min": 60, "resolution_time_hours": 20, "csat_score": 4.0, "tickets_per_day": 18, "fcr_pct": 65, "reopen_rate_pct": 9, "escalation_rate_pct": 11, "tenure_months": 5},
    ]

    def score_metric(actual, target, lower_is_better=False):
        if target == 0:
            return 100
        ratio = actual / target
        if lower_is_better:
            if ratio <= 0.5:
                return 100
            if ratio <= 0.75:
                return 90
            if ratio <= 1.0:
                return 75
            if ratio <= 1.5:
                return 50
            return 20
        else:
            if ratio >= 1.5:
                return 100
            if ratio >= 1.2:
                return 90
            if ratio >= 1.0:
                return 75
            if ratio >= 0.8:
                return 50
            return 20

    metric_defs = {
        "first_response_time_min": {"label": "First Response Time",     "unit": "min", "lower_is_better": True,  "weight": 20},
        "resolution_time_hours":   {"label": "Avg Resolution Time",     "unit": "hrs", "lower_is_better": True,  "weight": 15},
        "csat_score":              {"label": "CSAT Score",              "unit": "/5",  "lower_is_better": False, "weight": 30},
        "tickets_per_day":         {"label": "Tickets Resolved/Day",    "unit": "",    "lower_is_better": False, "weight": 15},
        "fcr_pct":                 {"label": "First Contact Resolution","unit": "%",   "lower_is_better": False, "weight": 10},
        "reopen_rate_pct":         {"label": "Ticket Reopen Rate",      "unit": "%",   "lower_is_better": True,  "weight": 5},
        "escalation_rate_pct":     {"label": "Escalation Rate",         "unit": "%",   "lower_is_better": True,  "weight": 5},
    }

    scored_agents = []
    for agent in demo_agents:
        name = agent.get("name", "Agent")
        total_score = 0.0
        metric_results = []
        coaching_tips = []

        for key, mdef in metric_defs.items():
            actual = float(agent.get(key, targets[key]))
            target = float(targets[key])
            s = score_metric(actual, target, mdef["lower_is_better"])
            weighted = s * mdef["weight"] / 100
            total_score += weighted
            status = "above" if s >= 75 else ("at" if s >= 50 else "below")
            metric_results.append({
                "key":    key, "label": mdef["label"], "actual": actual,
                "target": target, "unit": mdef["unit"],
                "score":  s, "weighted_points": round(weighted, 1), "status": status,
            })
            if key in _COACHING_LIBRARY:
                if status == "below":
                    tip_key = "slow" if mdef["lower_is_better"] else "low"
                    if key in ("reopen_rate_pct", "escalation_rate_pct"):
                        tip_key = "high"
                    coaching_tips.append({"area": mdef["label"], "tip": _COACHING_LIBRARY[key].get(tip_key, "")})
                elif status == "above":
                    tip_key = "fast" if mdef["lower_is_better"] else "high"
                    if key in ("reopen_rate_pct", "escalation_rate_pct"):
                        tip_key = "low"
                    coaching_tips.append({"area": mdef["label"], "tip": _COACHING_LIBRARY[key].get(tip_key, "")})

        final_score = round(total_score, 1)
        tier_key = "needs_help"
        for tk, tv in _PERFORMANCE_TIERS.items():
            if final_score >= tv["min"]:
                tier_key = tk
                break
        tier = _PERFORMANCE_TIERS[tier_key]

        scored_agents.append({
            "name":          name,
            "tenure_months": agent.get("tenure_months", 0),
            "overall_score": final_score,
            "tier":          tier["label"],
            "tier_key":      tier_key,
            "tier_color":    tier["color"],
            "tier_badge":    tier["badge"],
            "metrics":       metric_results,
            "strengths":     [m["label"] for m in metric_results if m["status"] == "above"],
            "gaps":          [m["label"] for m in metric_results if m["status"] == "below"],
            "coaching_tips": coaching_tips[:3],
        })

    scored_agents.sort(key=lambda a: a["overall_score"], reverse=True)
    team_avg = sum(a["overall_score"] for a in scored_agents) / len(scored_agents) if scored_agents else 0
    tier_distribution = {}
    for a in scored_agents:
        tier_distribution[a["tier_key"]] = tier_distribution.get(a["tier_key"], 0) + 1

    top_agent = scored_agents[0] if scored_agents else None
    bottom_agents = [a for a in scored_agents if a["tier_key"] == "needs_help"]

    return {
        "action":                    "agent_performance_scorecard",
        "business_name":             company,
        "period":                    per,
        "total_agents":              len(scored_agents),
        "team_avg_score":            round(team_avg, 1),
        "tier_distribution":         tier_distribution,
        "targets_used":              targets,
        "agents":                    scored_agents,
        "top_performer":             top_agent["name"] if top_agent else None,
        "agents_needing_coaching":   [a["name"] for a in bottom_agents],
        "team_insight":              f"Team avg {team_avg:.0f}/100. {tier_distribution.get('star',0)} Star agents, {tier_distribution.get('needs_help',0)} needing coaching.",
        "summary":                   f"Scored {len(scored_agents)} agents for {per}. Team avg: {team_avg:.0f}/100. Top: {top_agent['name'] if top_agent else 'N/A'} ({top_agent['overall_score'] if top_agent else 0}/100).",
    }


# ── NPS Campaign Builder (Round 14) ──────────────────────────────────────────

_NPS_SEGMENTS = {
    "promoter":  {"range": "9-10", "label": "Promoter",  "color": "green",  "pct_typical": 40, "action": "amplify"},
    "passive":   {"range": "7-8",  "label": "Passive",   "color": "yellow", "pct_typical": 35, "action": "convert"},
    "detractor": {"range": "0-6",  "label": "Detractor", "color": "red",    "pct_typical": 25, "action": "recover"},
}

_NPS_FOLLOW_UP = {
    "promoter": {
        "email_subject": "You made our day — can we ask one more thing?",
        "opening":       "Thank you so much for your {score}/10 score! It genuinely means a lot to us at {company}.",
        "ask":           "Would you be willing to leave us a review on G2/Capterra? It takes 3 minutes and helps others like you find {product}.",
        "cta":           "Leave a review →",
        "secondary_ask": "Also, do you know someone who could benefit from {product}? We'd love an introduction.",
        "tone":          "Warm, grateful, not pushy. They're fans — treat them like insiders.",
    },
    "passive": {
        "email_subject": "What would make {product} a 10/10 for you?",
        "opening":       "Thanks for taking the time to share your score of {score}/10. We really appreciate honest feedback.",
        "ask":           "We noticed you're not quite at a 10 yet — what's the one thing we could do better to get there?",
        "cta":           "Tell us in 2 minutes →",
        "secondary_ask": "If there's a specific feature or experience that fell short, our product team reviews every response personally.",
        "tone":          "Curious, improvement-focused. They like you but aren't committed — show you listen.",
    },
    "detractor": {
        "email_subject": "We need to make this right — {name}",
        "opening":       "Thank you for your honesty. A score of {score}/10 tells us we've let you down, and we take that seriously.",
        "ask":           "Would you be open to a 15-minute call with our customer success team? We want to understand exactly what went wrong and fix it.",
        "cta":           "Book a call →",
        "secondary_ask": "If a call isn't convenient, reply to this email with what went wrong. Our VP of CS reads every detractor response.",
        "tone":          "Apologetic, urgent, human. No corporate speak. Take ownership immediately.",
    },
}

_NPS_SURVEY_TEMPLATES = {
    "email": {
        "subject":     "Quick question about your {product} experience (30 seconds)",
        "body":        "Hi {name},\n\nYou've been using {product} for {tenure}, and we'd love to hear how it's going.\n\nOn a scale of 0-10, how likely are you to recommend {product} to a friend or colleague?\n\n[0 — Not at all] ........................ [10 — Absolutely]\n\n{survey_link}\n\nTake 30 seconds → {survey_link}\n\nThank you,\n{sender}\n{company}",
        "send_timing": "Send 30 days post-onboarding, then every 90 days",
        "open_rate_tip": "Best subject line open rates: personalized + short. Avoid 'survey' in subject line — reduces open rate by 20%.",
    },
    "in_app": {
        "trigger":     "Show after user completes 3+ key actions or on day 30/60/90",
        "question":    "How likely are you to recommend {product} to a friend or colleague?",
        "follow_up":   "What's the main reason for your score?",
        "design_tip":  "Show as a bottom banner, not a modal. Modal NPS gets 40% less response rate.",
        "dismiss_rule": "Suppress for 90 days after response. Never show to new users (<7 days).",
    },
    "whatsapp": {
        "message":     "Hi {name}! Quick question from the {company} team — on a scale of 0-10, how likely are you to recommend us to a friend? Reply with just a number. (Takes 5 seconds!)",
        "follow_up":   "Thank you! What's one thing we could do to make your experience better?",
        "send_timing": "After ticket closure or milestone. Avoid Monday mornings.",
    },
}

_INDUSTRY_NPS_BENCHMARKS = {
    "saas":       {"good": 30, "great": 50, "world_class": 70, "examples": "Slack: 51, Zoom: 49, Freshworks: 41"},
    "ecommerce":  {"good": 40, "great": 55, "world_class": 70, "examples": "Amazon: 62, Flipkart: 44"},
    "fintech":    {"good": 25, "great": 40, "world_class": 60, "examples": "Razorpay: 68, Zerodha: 72"},
    "healthcare": {"good": 40, "great": 60, "world_class": 75, "examples": "Practo: 52"},
    "logistics":  {"good": 20, "great": 35, "world_class": 55, "examples": "Delhivery: 38"},
    "general":    {"good": 30, "great": 45, "world_class": 65, "examples": "Top quartile B2B SaaS India"},
}


def _nps_campaign_builder(
    business_name: str,
    product_name: str,
    industry: str,
    responses: list,
    survey_channel: str,
) -> dict:
    company = business_name or "Your Company"
    product = product_name or "Your Product"
    ind_key = industry if industry in _INDUSTRY_NPS_BENCHMARKS else "general"
    channel = survey_channel if survey_channel in _NPS_SURVEY_TEMPLATES else "email"

    demo_responses = responses if responses else [
        {"name": "Rahul M.",   "score": 9,  "comment": "Love the product. Onboarding could be smoother.", "segment": "enterprise", "tenure": "6 months"},
        {"name": "Priya K.",   "score": 10, "comment": "Best tool in the market. Saves us 10 hours/week.", "segment": "startup",    "tenure": "12 months"},
        {"name": "Ananya S.",  "score": 5,  "comment": "Too many bugs in the mobile app. Support is slow.", "segment": "smb",        "tenure": "3 months"},
        {"name": "Vikram T.",  "score": 7,  "comment": "Good product but pricing is high compared to alternatives.", "segment": "enterprise", "tenure": "2 months"},
        {"name": "Deepika R.", "score": 3,  "comment": "Promised features not delivered. Feeling misled.", "segment": "startup",    "tenure": "1 month"},
        {"name": "Suresh N.",  "score": 8,  "comment": "Solid product. Would be 10 if the API docs were better.", "segment": "enterprise", "tenure": "8 months"},
        {"name": "Meera L.",   "score": 9,  "comment": "Our whole team uses it daily. Great customer success team.", "segment": "smb", "tenure": "18 months"},
        {"name": "Arun P.",    "score": 6,  "comment": "It works but I've seen better UX. Won't leave but won't recommend.", "segment": "smb", "tenure": "5 months"},
    ]

    # Classify and score
    scored = []
    promoters = passives = detractors = 0
    for r in demo_responses:
        s = int(r.get("score", 7))
        if s >= 9:
            seg = "promoter"
            promoters += 1
        elif s >= 7:
            seg = "passive"
            passives += 1
        else:
            seg = "detractor"
            detractors += 1

        follow_up_template = _NPS_FOLLOW_UP[seg]
        _name_parts = r.get("name","Customer").split()
        _first_name = _name_parts[0] if _name_parts else "Customer"
        email_subject = (follow_up_template["email_subject"]
            .replace("{product}", product).replace("{name}", _first_name))
        email_body = (
            follow_up_template["opening"].replace("{score}", str(s)).replace("{company}", company).replace("{product}", product) + "\n\n"
            + follow_up_template["ask"].replace("{product}", product) + "\n\n"
            + "[" + follow_up_template["cta"].replace("{product}", product) + "]\n\n"
            + follow_up_template["secondary_ask"].replace("{product}", product) + "\n\n"
            + f"Thank you,\nThe {company} Team"
        )
        scored.append({
            "name":          r.get("name", "Customer"),
            "score":         s,
            "segment":       seg,
            "segment_label": _NPS_SEGMENTS[seg]["label"],
            "segment_color": _NPS_SEGMENTS[seg]["color"],
            "comment":       r.get("comment", ""),
            "tenure":        r.get("tenure", ""),
            "customer_segment": r.get("segment", ""),
            "follow_up_subject": email_subject,
            "follow_up_body":    email_body,
            "tone_guidance": follow_up_template["tone"],
            "priority":      "high" if seg == "detractor" else ("medium" if seg == "passive" else "low"),
        })

    total = len(scored)
    nps_score = round(((promoters - detractors) / total * 100)) if total > 0 else 0
    benchmark = _INDUSTRY_NPS_BENCHMARKS[ind_key]
    vs_benchmark = "world_class" if nps_score >= benchmark["world_class"] else ("great" if nps_score >= benchmark["great"] else ("good" if nps_score >= benchmark["good"] else "below_average"))

    # Theme analysis from comments
    all_comments = " ".join([r.get("comment","") for r in scored]).lower()
    themes = []
    theme_keywords = {
        "Onboarding":      ["onboard", "setup", "getting started", "initial"],
        "Mobile App":      ["mobile", "app", "phone", "android", "ios"],
        "Pricing":         ["pric", "expensive", "cost", "value"],
        "Support Speed":   ["slow", "support", "response", "ticket"],
        "API/Docs":        ["api", "docs", "documentation", "developer"],
        "UX/UI":           ["ux", "ui", "interface", "design", "experience"],
        "Bugs/Stability":  ["bug", "crash", "error", "broken", "issue"],
        "Features":        ["feature", "missing", "request", "wish"],
    }
    for theme, keywords in theme_keywords.items():
        if any(kw in all_comments for kw in keywords):
            themes.append(theme)

    # Action plan
    action_plan = []
    if detractors > 0:
        action_plan.append({"priority": 1, "action": f"Contact all {detractors} detractors within 24 hours — assign to senior CS rep", "owner": "CS Lead", "timeline": "Today"})
    if themes:
        action_plan.append({"priority": 2, "action": f"Escalate top themes to Product team: {', '.join(themes[:3])}", "owner": "Product Manager", "timeline": "This week"})
    if passives > 0:
        action_plan.append({"priority": 3, "action": f"Run targeted outreach to {passives} passives — find the gap between 7/8 and a 10", "owner": "Customer Success", "timeline": "This week"})
    if promoters > 0:
        action_plan.append({"priority": 4, "action": f"Ask {promoters} promoters for G2/Capterra reviews and referrals", "owner": "Marketing", "timeline": "This week"})
    action_plan.append({"priority": 5, "action": "Set up automated NPS trigger at day 30, 90, 180 in your CRM/support tool", "owner": "CX Ops", "timeline": "Next sprint"})

    survey_template = _NPS_SURVEY_TEMPLATES[channel]

    return {
        "action":           "nps_campaign_builder",
        "business_name":    company,
        "product_name":     product,
        "industry":         ind_key,
        "survey_channel":   channel,
        "nps_score":        nps_score,
        "promoters":        promoters,
        "passives":         passives,
        "detractors":       detractors,
        "total_responses":  total,
        "promoter_pct":     round(promoters/total*100) if total else 0,
        "passive_pct":      round(passives/total*100) if total else 0,
        "detractor_pct":    round(detractors/total*100) if total else 0,
        "vs_benchmark":     vs_benchmark,
        "benchmark":        benchmark,
        "feedback_themes":  themes,
        "responses":        sorted(scored, key=lambda x: x["score"]),
        "action_plan":      action_plan,
        "survey_template":  survey_template,
        "segment_playbooks": {k: v for k, v in _NPS_FOLLOW_UP.items()},
        "summary":          f"{company} NPS: {nps_score} ({vs_benchmark.replace('_',' ').title()}). {promoters} promoters, {passives} passives, {detractors} detractors from {total} responses. Top themes: {', '.join(themes[:3]) if themes else 'none detected'}.",
    }


# ── Customer Onboarding Sequence Builder (Round 15) ───────────────────────────

_ONBOARDING_MILESTONES = {
    "day_0":  {"label": "Day 0 — Welcome",            "goal": "Make them feel great about their decision. First impression sets the tone for the whole relationship."},
    "day_1":  {"label": "Day 1 — Quick Win",           "goal": "Get them to their first moment of value in under 15 minutes. Aha moment = retention."},
    "day_7":  {"label": "Day 7 — Check-in",            "goal": "Catch early struggles before they become cancellation reasons. Most churn intent forms in week 1."},
    "day_14": {"label": "Day 14 — Depth",              "goal": "Introduce intermediate features. Customer has survived week 1 — now build habits."},
    "day_30": {"label": "Day 30 — Value Review",       "goal": "Show them what they have achieved. Quantify value delivered. Plant the expansion seed."},
    "day_60": {"label": "Day 60 — Expansion",          "goal": "Introduce upsell/cross-sell. Customer is now an established user — conversion rates are highest here."},
    "day_90": {"label": "Day 90 — Advocacy",           "goal": "Happy customers at 90 days stay for 2+ years. Ask for referrals, reviews, and case study participation."},
}

_CUSTOMER_TYPE_CONTEXT = {
    "smb":        {"tone": "friendly and direct", "channel": "email + WhatsApp", "response_sla": "4 hours", "check_in": "video call"},
    "enterprise": {"tone": "professional and thorough", "channel": "email + dedicated Slack", "response_sla": "2 hours", "check_in": "formal QBR"},
    "startup":    {"tone": "casual and fast-moving", "channel": "Slack + email", "response_sla": "1 hour", "check_in": "async Loom"},
    "individual": {"tone": "personal and encouraging", "channel": "email + in-app", "response_sla": "24 hours", "check_in": "email"},
}

_RISK_SIGNALS = [
    {"signal": "No login in 7 days after sign-up",         "risk": "high",   "action": "Day-8 personal email from CS rep + offer 30-min setup call"},
    {"signal": "Completed setup but never used core feature","risk": "high",   "action": "Targeted in-app prompt + how-to video for core feature"},
    {"signal": "Only 1 user active (for multi-seat plan)",  "risk": "medium", "action": "Send team invite email template + adoption guide"},
    {"signal": "Support ticket opened in first 7 days",     "risk": "medium", "action": "Priority resolve + CS manager follow-up after ticket closes"},
    {"signal": "Haven't exported/shared any output",        "risk": "medium", "action": "Show success story of similar customer + one-click share feature demo"},
    {"signal": "Downgrade or cancellation page visited",    "risk": "critical","action": "Immediate CS rep outreach — call first, email as backup"},
    {"signal": "No response to day-7 check-in email",       "risk": "medium", "action": "WhatsApp follow-up on day 9, then personal call on day 11"},
    {"signal": "NPS score 0-6 within first 30 days",        "risk": "critical","action": "Escalate to CS Lead within 24 hours. Recovery protocol."},
]

_SUCCESS_METRICS_BY_INDUSTRY = {
    "saas":       ["Daily Active Users", "Feature adoption rate (target: 3+ features used in 30 days)", "Time to first meaningful output", "Support tickets per user per month"],
    "ecommerce":  ["First order placed", "Catalogue items uploaded", "Payment gateway connected", "First sale via platform"],
    "fintech":    ["KYC completed", "First transaction processed", "Limit utilised %", "Reports downloaded"],
    "healthcare": ["Patient records entered", "First appointment booked", "Staff trained", "First billing processed"],
    "logistics":  ["First shipment created", "Integration connected", "Label printed", "Tracking shared with customer"],
    "general":    ["Core workflow completed", "Integration connected", "First output created", "Team member invited"],
}


_KB_ARTICLE_TYPES = {
    "how_to":       {"label": "How-To Guide",       "structure": ["Overview", "Prerequisites", "Step-by-Step Instructions", "Tips & Tricks", "Troubleshooting", "Related Articles"]},
    "troubleshoot": {"label": "Troubleshooting",    "structure": ["Problem Description", "Common Causes", "Quick Fix (Try First)", "Step-by-Step Fix", "When to Contact Support", "Related Articles"]},
    "faq":          {"label": "FAQ Article",         "structure": ["Top Questions", "Detailed Answers", "Still Need Help?", "Related Articles"]},
    "concept":      {"label": "Concept Explainer",  "structure": ["What Is It?", "Why It Matters", "How It Works", "Key Terms", "Examples", "Related Articles"]},
    "policy":       {"label": "Policy / Terms",     "structure": ["Policy Summary", "What This Means For You", "Exceptions", "How to Request Changes", "Contact Us"]},
    "release_note": {"label": "Release / Update Note", "structure": ["What's New", "Key Changes", "How to Access", "Known Issues", "Feedback"]},
}

_KB_TONES = {
    "friendly":     "Warm, helpful, conversational — like a knowledgeable friend explaining",
    "professional": "Clear, precise, formal — suitable for enterprise/B2B audiences",
    "simple":       "Plain English, minimal jargon — for non-technical users and India SMB audience",
}

_AUDIENCE_CONTEXT = {
    "end_user":  "Written for end users — avoid technical jargon, use screenshots/steps language",
    "admin":     "Written for admins/power users — can include technical detail, config options",
    "developer": "Written for developers — include code snippets, API references, technical specs",
    "business":  "Written for business owners / decision makers — focus on outcomes and ROI",
}

_INDUSTRY_KB_EXAMPLES = {
    "saas":      ["How to reset your password", "Setting up two-factor authentication", "How to invite team members", "Understanding your billing statement", "Exporting your data"],
    "ecommerce": ["How to track your order", "Return and refund policy", "How to update delivery address", "Payment methods accepted", "How to apply a coupon code"],
    "fintech":   ["How to add a bank account", "Understanding transaction fees", "KYC verification process", "How to raise a dispute", "Setting spending limits"],
    "healthcare":["Booking an appointment", "How to access your reports", "Insurance claim process", "Cancellation policy", "Telemedicine how-to guide"],
    "logistics": ["How to schedule a pickup", "Tracking your shipment", "What to do if your package is delayed", "How to file a damage claim", "Prohibited items list"],
    "retail":    ["Size guide and fit chart", "How to place a bulk order", "Loyalty points — how they work", "Store pickup process", "How to register for GST invoice"],
}

_RELATED_ARTICLE_TEMPLATES = {
    "saas":      ["Account Setup Guide", "Billing & Payments FAQ", "Integrations Overview", "Data Export & Privacy", "Team Management"],
    "ecommerce": ["Shipping Policy", "Returns & Refunds", "Payment Options", "Order Tracking Guide", "Loyalty Program FAQ"],
    "fintech":   ["Security & KYC", "Transaction Limits", "Support Escalation Process", "Dispute Resolution", "App Troubleshooting"],
    "healthcare":["Patient Privacy Policy", "Insurance Partners", "Emergency Contacts", "Prescription Uploads", "Lab Reports Access"],
    "logistics": ["Prohibited Items", "Insurance for Shipments", "International Shipping", "Business Account Benefits", "API Integration"],
    "retail":    ["Product Care Guide", "Authenticity Guarantee", "B2B / Bulk Orders", "Loyalty Program", "Store Locator"],
}

_SEO_TITLE_FORMULAS = [
    "How to {action} in {product} — Step-by-Step Guide",
    "{action}: Complete Guide for {audience}",
    "Why {problem} happens and how to fix it | {product} Help",
    "{action} — Everything you need to know",
    "How to fix {problem} in {product} [{year}]",
]


# ── Round 17: Escalation Email Generator ─────────────────────────────────────

_PRIORITY_CONFIG = {
    "critical": {"label": "CRITICAL", "color": "#dc2626", "response_target": "1 hour", "emoji": "🚨"},
    "high":     {"label": "HIGH",     "color": "#ea580c", "response_target": "4 hours", "emoji": "🔴"},
    "medium":   {"label": "MEDIUM",   "color": "#d97706", "response_target": "8 hours", "emoji": "🟡"},
    "low":      {"label": "LOW",      "color": "#059669", "response_target": "24 hours", "emoji": "🟢"},
}

_CUSTOMER_TIER_NOTES = {
    "enterprise": "Enterprise customer — requires C-level escalation visibility. Risk: contract renewal at stake.",
    "premium":    "Premium customer — expedited handling, dedicated CS manager must be looped in.",
    "standard":   "Standard tier — standard escalation flow applies.",
    "trial":      "Trial user — fast resolution critical for conversion.",
}

_INTERNAL_TEMPLATES = {
    "subject": "ESCALATION [{priority}] — {ticket_id}: {issue_summary} | {customer_name}",
    "body": """Hi {escalate_to},

I'm escalating {ticket_id} for your immediate attention.

──────────────────────────────────────
ESCALATION DETAILS
──────────────────────────────────────
Customer      : {customer_name} ({customer_tier})
Ticket        : {ticket_id}
Priority      : {priority_label} {priority_emoji}
Issue         : {issue_summary}
Current Status: {current_status}
SLA Breached  : {sla_breached}
Response Target: {response_target}
──────────────────────────────────────

WHY I'M ESCALATING
The ticket has exceeded our {sla_breached} SLA and the customer has followed up {followup_count} times. Given the {customer_tier_note}, this requires senior intervention.

WHAT'S BEEN TRIED
- Reviewed account and issue logs
- {attempted_steps}
- Customer notified of delay with apology

WHAT I NEED FROM YOU
1. Technical review / decision authority on {issue_summary}
2. Guidance on customer communication if root cause is complex
3. ETA for resolution to share with customer

I'll keep the ticket updated. Please acknowledge by {ack_deadline}.

Raised by: {cs_rep_name}
Ref: {ticket_id}
""",
}

_CUSTOMER_TEMPLATES = {
    "subject": "Update on Your Support Request — {ticket_id}",
    "body": """Dear {customer_name},

Thank you for your patience regarding your support request ({ticket_id}).

I want to personally assure you that your case has been escalated to our senior team and is now being handled with the highest priority.

YOUR CASE DETAILS
─────────────────
Ticket No.   : {ticket_id}
Issue        : {issue_summary}
Status       : Escalated to Senior Technical Team
Priority     : {priority_label}
Next Update  : {next_update_time}

WHAT HAPPENS NEXT
1. Our senior engineer is reviewing the case right now.
2. You will receive a detailed update by {next_update_time}.
3. If this is causing business impact, please reply to this email with details so we can prioritise further.

We sincerely apologise for the delay. Your experience matters to us and we are committed to resolving this as quickly as possible.

If you need to speak with someone immediately, please {immediate_contact}.

Warm regards,
{cs_rep_name}
{business_name} Customer Support
""",
}

_MANAGER_TEMPLATES = {
    "subject": "[FYI] Escalation Raised — {ticket_id} | {customer_name} ({customer_tier})",
    "body": """Hi {escalate_to},

FYI — I've raised a formal escalation on the following case. Copying you for visibility.

Ticket   : {ticket_id}
Customer : {customer_name} ({customer_tier})
Issue    : {issue_summary}
SLA Miss : {sla_breached}
Action   : Escalated to senior technical team

{customer_tier_risk}

I'll update you once resolved. No action needed unless the team requires your sign-off.

{cs_rep_name}
""",
}

_IMMEDIATE_CONTACT = {
    "enterprise": "call our dedicated enterprise line or contact your account manager directly",
    "premium":    "reply to this email marked URGENT or call our priority support line",
    "standard":   "reply to this email and we will prioritise your response",
    "trial":      "reply to this email and our team will get back to you shortly",
}


# ── Round 18: Customer Win-Back Campaign ─────────────────────────────────────

_CHURN_REASONS = {
    "price":       {"label": "Price / Budget Concerns",    "angle": "value and ROI"},
    "competitor":  {"label": "Switched to Competitor",     "angle": "what's new and improved"},
    "no_use":      {"label": "Not Using the Product",      "angle": "quick wins and ease of use"},
    "support":     {"label": "Bad Support Experience",     "angle": "improved support and personal attention"},
    "features":    {"label": "Missing Features",           "angle": "new features they asked for"},
    "unknown":     {"label": "Unknown / Lapsed",           "angle": "value and what they're missing"},
}

_OFFER_INTROS = {
    "discount":     "We'd like to offer you an exclusive returning customer discount",
    "free_trial":   "We'd love to give you a free extended trial — no strings attached",
    "free_month":   "We're offering you a complimentary month, completely on us",
    "upgrade":      "We'd like to upgrade your account for free for 3 months",
    "consultation": "We'd love to offer a free 1-on-1 session with our specialist",
    "credit":       "We've added account credits that you can use immediately",
}

_WINBACK_EMAIL_SEQUENCE = [
    {"step": 1, "day": 0,  "name": "The Breakup Email",    "tone": "warm, no pressure",    "cta": "See what's new"},
    {"step": 2, "day": 7,  "name": "The Value Reminder",   "tone": "helpful, educational", "cta": "Read success story"},
    {"step": 3, "day": 14, "name": "The Offer Email",      "tone": "generous, urgent",     "cta": "Claim your offer"},
    {"step": 4, "day": 21, "name": "The Last Chance",      "tone": "honest, final",        "cta": "Reclaim offer (expires soon)"},
    {"step": 5, "day": 30, "name": "The Goodbye (Optional)", "tone": "gracious, memorable", "cta": "Stay connected"},
]

_INDUSTRY_PAIN_POINTS = {
    "saas":     ["losing hours to manual work", "your team is still using spreadsheets", "your data is scattered across tools"],
    "ecomm":    ["missing out on sales", "your competitors are growing while your store sits idle", "customers are buying elsewhere"],
    "retail":   ["stock going unnoticed", "footfall dropping while costs rise", "losing regulars to online stores"],
    "finance":  ["leaving money on the table", "missing tax savings", "financial clarity slipping away"],
    "health":   ["your wellness goals are still waiting", "you were making progress — don't stop now", "your health goals deserve attention"],
    "education":["your skills gap is growing", "your competition keeps learning", "your career growth has paused"],
}

_WHATSAPP_WINBACK = {
    "day0":  "Hi {customer}! 👋 It's been a while since we've seen you on {product}. We miss you! 😊 We've made some big improvements and would love to show you. Can I take 5 minutes to catch up? — {rep}",
    "day7":  "Hey {customer}! Quick one — did you know we recently launched [new feature]? A lot of customers like you are using it to [key benefit]. Worth a look? 🚀 — {rep}, {business}",
    "day14": "Hi {customer}! 🎁 We have a special returning-customer offer just for you: {offer}. Valid for 7 days only. Want me to activate it for you right now? — {rep}",
    "day21": "Last chance, {customer}! Your exclusive {offer} expires tomorrow. Don't miss this — reply YES and I'll set it up in 2 minutes. — {rep}, {business} 🙏",
}


# ── Round 19: CSAT Survey Builder ────────────────────────────────────────────

_SURVEY_GOALS = {
    "overall":        {"label": "Overall Satisfaction",    "focus": "general experience"},
    "post_support":   {"label": "Post-Support Feedback",   "focus": "support interaction quality"},
    "onboarding":     {"label": "Onboarding Experience",   "focus": "first-30-days experience"},
    "product":        {"label": "Product Satisfaction",    "focus": "product usability and value"},
    "renewal":        {"label": "Renewal / Loyalty",       "focus": "likelihood to renew and recommend"},
    "post_purchase":  {"label": "Post-Purchase Feedback",  "focus": "purchase and delivery experience"},
}

_QUESTION_BANKS = {
    "overall": [
        {"id": "csat_main",  "type": "rating_5",   "question": "How satisfied are you with {product} overall?",                    "why": "Core CSAT metric"},
        {"id": "nps",        "type": "rating_10",  "question": "How likely are you to recommend {product} to a friend or colleague?", "why": "Net Promoter Score"},
        {"id": "value",      "type": "rating_5",   "question": "How would you rate the value for money of {product}?",              "why": "Value perception"},
        {"id": "ease",       "type": "rating_5",   "question": "How easy is {product} to use?",                                     "why": "Usability"},
        {"id": "support_q",  "type": "rating_5",   "question": "How satisfied are you with our customer support?",                  "why": "Support quality"},
        {"id": "improve",    "type": "open_text",  "question": "What is the one thing we could improve to make {product} better for you?", "why": "Qualitative insight"},
        {"id": "love",       "type": "open_text",  "question": "What do you love most about {product}?",                           "why": "Understand strengths"},
        {"id": "missing",    "type": "mcq",        "question": "Which feature do you wish {product} had?", "options": ["Better reporting", "Mobile app", "API integrations", "Faster performance", "Other"], "why": "Roadmap input"},
    ],
    "post_support": [
        {"id": "resolved",   "type": "binary",     "question": "Was your issue resolved?",                                          "why": "Resolution rate"},
        {"id": "csat_main",  "type": "rating_5",   "question": "How satisfied are you with the support you received today?",        "why": "Core support CSAT"},
        {"id": "speed",      "type": "rating_5",   "question": "How would you rate the speed of our response?",                     "why": "Response time perception"},
        {"id": "knowledge",  "type": "rating_5",   "question": "How knowledgeable was the support agent?",                         "why": "Agent quality"},
        {"id": "effort",     "type": "rating_5",   "question": "How easy was it to get your issue resolved? (1 = very difficult, 5 = very easy)", "why": "Customer Effort Score"},
        {"id": "improve",    "type": "open_text",  "question": "Is there anything we could have done better?",                     "why": "Improvement input"},
        {"id": "channel",    "type": "mcq",        "question": "How did you contact us?", "options": ["Email", "Chat", "Phone", "WhatsApp", "In-app"], "why": "Channel analysis"},
        {"id": "nps",        "type": "rating_10",  "question": "Based on this experience, how likely are you to recommend us?",     "why": "NPS"},
    ],
    "onboarding": [
        {"id": "csat_main",  "type": "rating_5",   "question": "How would you rate your onboarding experience with {product}?",     "why": "Onboarding CSAT"},
        {"id": "clarity",    "type": "rating_5",   "question": "How clear was the setup and getting-started process?",              "why": "Clarity of onboarding"},
        {"id": "time",       "type": "mcq",        "question": "How long did it take to get started?", "options": ["< 1 hour", "1–4 hours", "1–3 days", "More than 3 days"], "why": "Time to value"},
        {"id": "first_value","type": "binary",     "question": "Have you achieved your first goal using {product}?",                "why": "First value milestone"},
        {"id": "resources",  "type": "rating_5",   "question": "How helpful were our documentation and tutorials?",                 "why": "Self-serve resource quality"},
        {"id": "missing",    "type": "open_text",  "question": "What was missing from the onboarding that would have helped you?",  "why": "Gap analysis"},
        {"id": "nps",        "type": "rating_10",  "question": "How likely are you to recommend {product} to others after your first month?", "why": "Early NPS"},
    ],
    "product": [
        {"id": "csat_main",  "type": "rating_5",   "question": "How satisfied are you with {product}?",                            "why": "Core CSAT"},
        {"id": "reliability","type": "rating_5",   "question": "How reliable is {product}? (uptime, bugs, performance)",           "why": "Reliability perception"},
        {"id": "features",   "type": "rating_5",   "question": "Does {product} have all the features you need?",                   "why": "Feature completeness"},
        {"id": "top_feature","type": "open_text",  "question": "Which feature do you use most, and why?",                         "why": "Usage insights"},
        {"id": "missing",    "type": "open_text",  "question": "What feature would make {product} 10× more useful for you?",       "why": "Roadmap ideas"},
        {"id": "compare",    "type": "mcq",        "question": "Compared to alternatives, {product} is:", "options": ["Much better", "Somewhat better", "About the same", "Somewhat worse", "Much worse"], "why": "Competitive positioning"},
        {"id": "nps",        "type": "rating_10",  "question": "How likely are you to recommend {product}?",                       "why": "NPS"},
    ],
}

_SCALE_DESCRIPTIONS = {
    "rating_5":  {"scale": "1–5", "low": "1 = Very Dissatisfied", "high": "5 = Very Satisfied", "benchmark": "CSAT score = % respondents scoring 4 or 5"},
    "rating_10": {"scale": "0–10", "low": "0 = Not at all likely", "high": "10 = Extremely likely", "benchmark": "NPS = % Promoters (9-10) − % Detractors (0-6)"},
    "binary":    {"scale": "Yes / No", "low": "No", "high": "Yes", "benchmark": "Resolution rate = % Yes responses"},
    "open_text": {"scale": "Free text", "low": "—", "high": "—", "benchmark": "Analyse with word cloud / theme tagging"},
    "mcq":       {"scale": "Multiple choice", "low": "—", "high": "—", "benchmark": "Track distribution % per option"},
}

_DISTRIBUTION_CHANNELS = [
    {"channel": "Email", "timing": "Within 24h of interaction", "open_rate": "20-30%", "tip": "Send from rep's email, not noreply@"},
    {"channel": "In-App Prompt", "timing": "After key action (e.g., ticket closed)", "open_rate": "40-60%", "tip": "Keep it to 1-2 questions max for in-app"},
    {"channel": "WhatsApp", "timing": "Within 1h of support close", "open_rate": "70-85%", "tip": "Use WABA approved template for first message"},
    {"channel": "SMS", "timing": "Within 2h of support close", "open_rate": "60-80%", "tip": "Under 160 chars; include opt-out option"},
    {"channel": "QR Code (Physical)", "timing": "At POS / delivery", "open_rate": "5-15%", "tip": "Add incentive (10% off next purchase) to boost response"},
]


# ── Round 20: Customer 360 View ──────────────────────────────────────────────

_CHURN_SIGNALS = {
    "high":   ["No activity in 60+ days", "Multiple unresolved tickets", "Negative CSAT scores", "Downgrade request", "Billing disputes"],
    "medium": ["Reduced usage frequency", "Support tickets increasing", "No response to outreach", "Feature requests unanswered"],
    "low":    ["Active and engaged", "Positive CSAT", "Regular usage", "Referrals made", "Upsell opportunity"],
}

_HEALTH_SEGMENTS = {
    "champion":  {"min": 85, "label": "Champion", "color": "green",  "action": "Ask for referral/testimonial. Offer loyalty reward."},
    "healthy":   {"min": 70, "label": "Healthy",   "color": "green",  "action": "Keep engaging. Share new features. Upsell opportunity."},
    "at_risk":   {"min": 50, "label": "At Risk",   "color": "yellow", "action": "Reach out immediately. Assign senior CS rep. Find root cause."},
    "critical":  {"min": 0,  "label": "Critical",  "color": "red",    "action": "Escalate to CSM. Offer retention deal. CEO-level outreach if high-value."},
}

_SENTIMENT_MAP = {
    5: ("Very Positive", "#22c55e", "Customer is delighted. Prime time to upsell or ask for referral."),
    4: ("Positive",      "#86efac", "Good experience. Reinforce with value-add content."),
    3: ("Neutral",       "#fbbf24", "Satisfied but not excited. Find the gap and fill it."),
    2: ("Negative",      "#f97316", "Something went wrong. Proactively reach out with solution."),
    1: ("Very Negative", "#ef4444", "High churn risk. Immediate personal outreach required."),
}


# ── Round 21: Support Analytics Dashboard ────────────────────────────────────

_INDUSTRY_BENCHMARKS = {
    "saas":       {"csat": 85, "frt_hrs": 4,  "resolution_hrs": 24, "fcr": 75},
    "ecommerce":  {"csat": 80, "frt_hrs": 2,  "resolution_hrs": 12, "fcr": 70},
    "banking":    {"csat": 78, "frt_hrs": 6,  "resolution_hrs": 48, "fcr": 65},
    "healthcare": {"csat": 82, "frt_hrs": 8,  "resolution_hrs": 72, "fcr": 68},
    "retail":     {"csat": 79, "frt_hrs": 3,  "resolution_hrs": 24, "fcr": 72},
    "telecom":    {"csat": 75, "frt_hrs": 12, "resolution_hrs": 48, "fcr": 60},
}

_CATEGORY_ICONS = {
    "Billing":           "💳",
    "Technical Issue":   "🔧",
    "Feature Request":   "💡",
    "Account":           "👤",
    "Shipping/Delivery": "📦",
    "General Inquiry":   "❓",
    "Complaint":         "⚠️",
    "Returns/Refund":    "↩️",
}


# ── R22: Returns & Refund Policy Generator ───────────────────────────────────

_RETURNS_WINDOWS = {
    "ecommerce":     {"return_days": 7,  "refund_days": 5,  "exchange": True},
    "electronics":   {"return_days": 14, "refund_days": 7,  "exchange": True},
    "fashion":       {"return_days": 30, "refund_days": 7,  "exchange": True},
    "food_beverage": {"return_days": 1,  "refund_days": 2,  "exchange": False},
    "software_saas": {"return_days": 14, "refund_days": 7,  "exchange": False},
    "services":      {"return_days": 0,  "refund_days": 14, "exchange": False},
    "health_beauty": {"return_days": 7,  "refund_days": 5,  "exchange": True},
    "home_furniture": {"return_days": 14,"refund_days": 7,  "exchange": True},
}

_RETURNS_EXCLUSIONS = {
    "ecommerce":     ["Items used or damaged by customer", "Products missing original packaging", "Perishables and food items", "Digital downloads once accessed"],
    "electronics":   ["Software products once opened", "Items with tampered serial numbers", "Accessories if opened", "Damage due to misuse"],
    "fashion":       ["Innerwear and swimwear", "Altered or washed items", "Items without tags", "Gift cards"],
    "software_saas": ["Partially used subscription months", "Setup/onboarding fees", "Add-ons or integrations"],
    "services":      ["Completed services", "Partially rendered services"],
    "food_beverage": ["Opened or consumed items", "Items past best-before date"],
}

_WHATSAPP_TEMPLATES = {
    "return_request": "Hi {name}! 👋 Your return request for Order #{order_id} has been received. Our team will review it within 24 hours. For eligible returns, we'll share the pickup details shortly. Thank you for your patience! 🙏",
    "refund_initiated": "Good news, {name}! ✅ Your refund of ₹{amount} for Order #{order_id} has been initiated. It will reflect in your {payment_method} within {days} business days.",
    "return_rejected": "Hi {name}, we're unable to process a return for Order #{order_id} because {reason}. Please WhatsApp us if you have any questions — we're happy to help! 🙏",
}


# ── R23: Chatbot Script Builder ───────────────────────────────────────────────

_CHATBOT_GREETINGS = {
    "whatsapp": "Hi! 👋 I'm {bot_name}, your {business} assistant. How can I help you today?\n\nReply with a number:\n1️⃣ Track my order\n2️⃣ Returns & Refunds\n3️⃣ Product info\n4️⃣ Talk to a human",
    "website":  "Hello! 👋 Welcome to {business}. I'm {bot_name}. What can I help you with?\n• Order status\n• Returns\n• Product questions\n• Speak to support",
    "instagram":"Hey! 🌟 Thanks for reaching out to {business}. I'm {bot_name} — quick replies below!\n\n1. Track order\n2. Returns\n3. Products\n4. Human agent",
}

_CHATBOT_FALLBACKS = {
    "friendly":     "Hmm, I didn't quite get that 😅 Let me connect you with a team member who can help! Type HELP to speak with a human.",
    "professional": "I'm sorry, I didn't understand that request. Please choose from the menu options or type AGENT to speak with our support team.",
    "formal":       "We apologise for the inconvenience. Your query has been escalated to our customer care team who will respond within 4 business hours.",
}

_CHATBOT_INDUSTRY_FAQS = {
    "ecommerce":   [("Track my order", "Please share your Order ID and I'll check the status right away! 📦"), ("Return a product", "Returns are accepted within 7 days. Share your Order ID to start a return request."), ("Payment failed", "If your payment failed but amount was deducted, it will be refunded within 5–7 business days automatically.")],
    "services":    [("Book an appointment", "Sure! Please share your preferred date and time and I'll check availability."), ("Service charges", "Our pricing depends on your requirement. Can you share more details?"), ("Cancel booking", "To cancel, please share your booking ID. Note: cancellations must be done 24 hours before the appointment.")],
    "education":   [("Course fees", "Course fees vary by program. Which course are you interested in?"), ("Batch timings", "We have morning, afternoon, and evening batches. Which works best for you?"), ("Certificate", "Certificates are issued within 7 days of course completion.")],
    "health":      [("Book appointment", "Happy to help! Please share your preferred doctor, date, and time."), ("Report status", "Share your Patient ID or phone number to get your report status."), ("Insurance", "We accept most major insurance providers. Share your insurer name to confirm coverage.")],
    "real_estate": [("Site visit", "We'd love to show you around! Share your preferred date and our team will confirm."), ("Price", "Pricing starts at ₹X. Would you like a detailed brochure?"), ("EMI options", "We have tie-ups with 12+ banks. EMIs start from ₹X/month for a 20-year loan.")],
}

_CHATBOT_ESCALATION_TRIGGERS = ["human", "agent", "help", "manager", "complaint", "urgent", "problem", "issue", "not working", "refund stuck"]


# ── R24: Agent Training Manual Generator ─────────────────────────────────────

_ATM_MODULES = [
    "Company & Product Overview",
    "Communication Standards",
    "Handling Common Queries",
    "Escalation Protocol",
    "Tools & Systems",
    "Performance Metrics",
    "Role Play Scenarios",
    "Assessment & Certification",
]

_ATM_TONE_GUIDE = {
    "formal": {
        "greeting": "Good [morning/afternoon], thank you for contacting [Company]. My name is [Agent Name]. How may I assist you today?",
        "apology":  "I sincerely apologise for the inconvenience caused. Allow me to resolve this at the earliest.",
        "closing":  "Thank you for contacting us. Is there anything else I may assist you with today?",
    },
    "friendly": {
        "greeting": "Hi! Welcome to [Company] support. I'm [Agent Name]. What can I help you with today? 😊",
        "apology":  "Oh, I'm really sorry about that! Let me sort this out for you right away.",
        "closing":  "Great talking to you! Feel free to reach out anytime. Have a wonderful day! 🌟",
    },
    "neutral": {
        "greeting": "Hello, thank you for reaching out to [Company]. How can I help you?",
        "apology":  "I apologise for the trouble. Let me look into this for you.",
        "closing":  "Thank you for contacting support. Have a good day.",
    },
}

_ATM_SCENARIOS = {
    "ecommerce": [
        {"title": "Order not received", "customer": "I ordered 5 days ago but haven't received my package.", "ideal_response": "Apologise → Check order status → Confirm address → Initiate trace with courier → Give ETA or initiate replacement."},
        {"title": "Wrong item delivered", "customer": "I received the wrong product!", "ideal_response": "Apologise → Take photo evidence → Arrange reverse pickup → Dispatch correct item → Follow up."},
        {"title": "Refund not credited", "customer": "My refund hasn't come after 10 days.", "ideal_response": "Apologise → Check refund status → Verify bank details → Escalate to finance if TAT breached."},
    ],
    "saas": [
        {"title": "Login issue", "customer": "I can't log into my account.", "ideal_response": "Verify identity → Try password reset → Check account status → Escalate to tech if issue persists."},
        {"title": "Feature not working", "customer": "The export feature stopped working.", "ideal_response": "Reproduce the issue → Check known bugs → Provide workaround → Log ticket with ETA."},
        {"title": "Billing dispute", "customer": "I was charged twice this month.", "ideal_response": "Verify payment records → Confirm duplicate charge → Initiate refund → Send confirmation email."},
    ],
    "banking": [
        {"title": "Transaction failed but amount debited", "customer": "Money deducted but transaction shows failed.", "ideal_response": "Calm the customer → Check transaction logs → If confirmed debit without credit, raise reversal ticket → Give 3–5 working day timeline."},
        {"title": "Card blocked", "customer": "My debit card is not working.", "ideal_response": "Verify identity → Check card status → Unblock if low risk → Advise on re-PIN → Offer temp limit increase if needed."},
    ],
    "general": [
        {"title": "Angry customer", "customer": "This is absolutely pathetic service!", "ideal_response": "Stay calm → Acknowledge frustration → Do NOT argue → Offer solution → Escalate if needed."},
        {"title": "Request out of scope", "customer": "Can you do XYZ for me?", "ideal_response": "Politely explain scope → Suggest right channel → Do not leave customer without next step."},
    ],
}

_ATM_KPIs = {
    "FCR":    {"name": "First Contact Resolution", "target": ">80%", "description": "Issues resolved in the first interaction without follow-up"},
    "AHT":    {"name": "Average Handle Time",       "target": "<4 min (chat), <6 min (call)", "description": "Time from contact start to resolution"},
    "CSAT":   {"name": "Customer Satisfaction",     "target": ">4.2/5", "description": "Post-interaction survey score"},
    "QA":     {"name": "Quality Assurance Score",   "target": ">90%", "description": "Internal call/chat audit score"},
    "ABN":    {"name": "Abandonment Rate",          "target": "<5%", "description": "% of customers who leave before being served"},
    "TAT":    {"name": "Turnaround Time",           "target": "As per SLA", "description": "Time to resolve complex/escalated issues"},
}

_ATM_DO_DONTS = {
    "do": [
        "Always greet and introduce yourself",
        "Use the customer's name at least once",
        "Listen fully before responding",
        "Verify identity before accessing account details",
        "Set realistic expectations on timelines",
        "Confirm resolution before closing the chat",
        "Document all interactions in CRM",
        "Follow escalation matrix without hesitation",
    ],
    "dont": [
        "Don't promise what you cannot deliver",
        "Don't argue or become defensive",
        "Don't keep the customer on hold without updates",
        "Don't share sensitive data without proper verification",
        "Don't close a ticket without customer confirmation",
        "Don't use jargon the customer won't understand",
        "Don't let negative customer energy affect your tone",
        "Don't skip the greeting or closing scripts",
    ],
}

_ATM_ESCALATION_MATRIX = [
    {"level": "L1", "who": "Front-line Agent",     "handles": "Standard queries, FAQs, basic troubleshooting", "escalate_when": "Cannot resolve in 2 attempts or customer requests supervisor"},
    {"level": "L2", "who": "Senior Agent / TL",    "handles": "Complex issues, billing disputes, repeat contacts", "escalate_when": "Legal/compliance risk or unresolved after 24h"},
    {"level": "L3", "who": "Manager / Specialist", "handles": "Escalated complaints, fraud, SLA breach cases", "escalate_when": "Threat of legal action or media"},
    {"level": "L4", "who": "Leadership",           "handles": "PR risk, regulatory issues, executive escalations", "escalate_when": "Viral complaints or regulatory notice"},
]


# ── R25: SLA Policy Generator ────────────────────────────────────────────────

_SLA_PRIORITY_TIERS = {
    "critical": {
        "label":       "P1 — Critical",
        "description": "Complete service outage or data breach affecting all users",
        "first_response": "15 minutes",
        "resolution":    "2 hours",
        "escalation":    "Immediate — notify leadership within 30 min",
        "color":         "#ef4444",
    },
    "high": {
        "label":       "P2 — High",
        "description": "Major feature broken, affecting significant portion of users",
        "first_response": "1 hour",
        "resolution":    "8 hours",
        "escalation":    "L2 within 2 hours if unresolved",
        "color":         "#f97316",
    },
    "medium": {
        "label":       "P3 — Medium",
        "description": "Non-critical issue with workaround available",
        "first_response": "4 hours",
        "resolution":    "2 business days",
        "escalation":    "L2 on next business day if unresolved",
        "color":         "#eab308",
    },
    "low": {
        "label":       "P4 — Low",
        "description": "Minor issues, feature requests, how-to questions",
        "first_response": "8 hours",
        "resolution":    "5 business days",
        "escalation":    "Reviewed in weekly backlog",
        "color":         "#22c55e",
    },
}

_SLA_BY_CHANNEL = {
    "chat":      {"first_response": "under 2 minutes",   "resolution": "per priority tier"},
    "email":     {"first_response": "under 4 hours",     "resolution": "per priority tier"},
    "phone":     {"first_response": "under 3 minutes",   "resolution": "first call resolution target 80%"},
    "whatsapp":  {"first_response": "under 10 minutes",  "resolution": "per priority tier"},
    "social":    {"first_response": "under 30 minutes",  "resolution": "redirect to email/chat for resolution"},
    "self_serve":{"first_response": "Instant (bot)",     "resolution": "bot handles L0; escalates to agent for L1+"},
}

_SLA_BREACH_ACTIONS = [
    "System auto-alerts agent and TL via email/Slack when 75% of SLA time is consumed",
    "Automatic escalation to L2 when SLA is breached without resolution",
    "Breach logged in CRM against agent and ticket for QA review",
    "Customer receives proactive apology update at breach point",
    "Monthly SLA breach report reviewed by support manager",
    "Repeated breaches trigger root cause analysis (RCA) within 48 hours",
]

_SLA_EXCLUSIONS = [
    "Scheduled maintenance windows (communicated 48h in advance)",
    "Force majeure events (natural disaster, ISP outage, etc.)",
    "Customer-caused delays (incomplete information, unresponsive customer)",
    "Issues outside scope of support agreement",
    "Public holidays (unless 24×7 SLA contracted)",
]

_SLA_METRICS = {
    "FCR":   {"name": "First Contact Resolution",  "target": ">80%"},
    "AHT":   {"name": "Average Handle Time",       "target": "Chat <4 min | Email <8 min | Call <6 min"},
    "CSAT":  {"name": "Customer Satisfaction",     "target": ">4.2/5 or >85%"},
    "SLA_C": {"name": "SLA Compliance Rate",       "target": ">95%"},
    "RES":   {"name": "Reopen Rate",               "target": "<5%"},
    "ABAND": {"name": "Abandonment Rate",          "target": "<5% (chat/call)"},
}


# ── R26: Product Review Response Kit ────────────────────────────────────────

_REVIEW_SENTIMENTS = {
    "positive":  {"stars": [4, 5], "tone": "warm and grateful"},
    "neutral":   {"stars": [3],    "tone": "acknowledging and helpful"},
    "negative":  {"stars": [1, 2], "tone": "apologetic and solution-focused"},
}

_REVIEW_RESPONSE_STARTERS = {
    "positive": [
        "Thank you so much for your kind words, {name}! 🙏",
        "We're absolutely thrilled to hear this, {name}! ⭐",
        "This made our day, {name}! Thank you for taking the time to share this!",
        "Wow, reviews like this keep us going! Thank you, {name}! 🌟",
    ],
    "neutral": [
        "Thank you for your honest feedback, {name}.",
        "We appreciate you sharing your experience with us, {name}.",
        "Thank you for taking the time to review us, {name}.",
    ],
    "negative": [
        "We sincerely apologise for your experience, {name}.",
        "We're truly sorry to hear this, {name}, and we take full responsibility.",
        "Thank you for bringing this to our attention, {name}. We're very sorry.",
        "This is not the experience we want for our customers. We apologise, {name}.",
    ],
}

_REVIEW_CLOSERS = {
    "positive": [
        "We look forward to serving you again! 😊",
        "Hope to see you again soon!",
        "Your support means the world to us! 💙",
    ],
    "neutral": [
        "We hope to do better next time. Please reach out if you need anything.",
        "We'd love a chance to make it up to you. Please DM us anytime.",
        "We're always improving — your feedback helps us grow!",
    ],
    "negative": [
        "Please DM us or email {support_email} so we can make this right.",
        "We'd like to resolve this personally. Please reach out at {support_email}.",
        "Your satisfaction is our priority. Please contact us at {support_email}.",
    ],
}

_REVIEW_PLATFORMS = {
    "google":    {"char_limit": 4096, "tip": "Reply within 24h — Google surfaces recent replies in search"},
    "amazon":    {"char_limit": 1000, "tip": "Cannot offer refunds in reply — direct to seller support"},
    "flipkart":  {"char_limit": 500,  "tip": "Short replies work best — Flipkart customers scan quickly"},
    "zomato":    {"char_limit": 500,  "tip": "Be warm and personal — food is emotional; show you care"},
    "swiggy":    {"char_limit": 500,  "tip": "Acknowledge delivery issues separately from food quality"},
    "trustpilot":{"char_limit": 2000, "tip": "Professional tone; Trustpilot is B2B-facing"},
    "facebook":  {"char_limit": 2000, "tip": "Public reply visible to all — keep it brand-positive"},
    "instagram": {"char_limit": 2200, "tip": "Use emojis, keep it short and visual"},
    "playstore": {"char_limit": 350,  "tip": "Mention version fix if it's a bug report"},
    "appstore":  {"char_limit": 500,  "tip": "Cannot reply directly to individual reviews currently"},
    "general":   {"char_limit": 1000, "tip": "Adapt length to platform norms"},
}

_REVIEW_TEMPLATES = {
    "positive_feature": "{starter} We're so glad {feature} worked well for you! Your feedback motivates the whole team. {closer}",
    "positive_delivery": "{starter} We work hard to ensure fast and safe delivery — glad it reached you perfectly! {closer}",
    "positive_general":  "{starter} We put a lot of care into every {product}, and it means everything to hear that. {closer}",
    "neutral_service":   "{starter} We hear you — {concern} is something we're actively working to improve. Your feedback goes directly to our team. {closer}",
    "neutral_expectation": "{starter} We understand the experience didn't fully meet expectations. Could you DM us the details so we can look into it? {closer}",
    "negative_delay":    "{starter} A delay like this is unacceptable and we completely understand your frustration. {resolution} {closer}",
    "negative_quality":  "{starter} Quality is our #1 priority, and we failed here. We'd like to {resolution} immediately. {closer}",
    "negative_support":  "{starter} Our support team should have resolved this faster — that's on us. {resolution} {closer}",
}


# ── R27: Voice of Customer Report ────────────────────────────────────────────

_VOC_DATA_SOURCES = [
    "Customer support tickets (CRM)",
    "Post-purchase CSAT surveys",
    "NPS (Net Promoter Score) surveys",
    "Product reviews (Google, Amazon, Flipkart)",
    "Social media mentions and comments",
    "Live chat transcripts",
    "Return/refund reasons",
    "User interviews / focus groups",
    "App store reviews (Play Store / App Store)",
    "Exit surveys (cancelled subscribers)",
]

_VOC_THEMES = {
    "product_quality":    {"label": "Product Quality",      "examples": ["Durable", "Poor build", "Meets expectations", "Defective on arrival"]},
    "pricing":            {"label": "Pricing & Value",       "examples": ["Too expensive", "Worth the money", "Affordable", "Better alternatives exist"]},
    "delivery":           {"label": "Delivery & Logistics",  "examples": ["Late delivery", "Packaging damage", "Fast shipping", "Wrong item"]},
    "customer_support":   {"label": "Customer Support",      "examples": ["Unhelpful agent", "Quick resolution", "Rude staff", "Proactive follow-up"]},
    "onboarding":         {"label": "Onboarding Experience", "examples": ["Confusing setup", "Easy to start", "Poor documentation", "Great tutorial"]},
    "features":           {"label": "Features & Usability",  "examples": ["Missing feature X", "Intuitive UI", "Too complex", "Works as expected"]},
    "returns":            {"label": "Returns & Refunds",      "examples": ["Slow refund", "Easy return", "Refund denied", "Hassle-free"]},
    "communication":      {"label": "Communication",         "examples": ["Not informed of delay", "Good update emails", "Spam", "Timely reminders"]},
}

_VOC_NPS_BANDS = {
    "promoters":  {"range": "9–10", "action": "Ask for referrals and reviews; create advocacy program"},
    "passives":   {"range": "7–8",  "action": "Identify what would move them to 9–10; offer loyalty perks"},
    "detractors": {"range": "0–6",  "action": "Immediate outreach within 48h; understand root cause; recover relationship"},
}

_VOC_ACTION_FRAMEWORK = [
    {"priority": "P1 — Fix Now",    "criteria": "Recurring negative theme in >15% of feedback",   "owner": "Product / Ops",    "timeline": "2–4 weeks"},
    {"priority": "P2 — Plan",       "criteria": "Negative theme in 5–15% of feedback",             "owner": "Team Lead",        "timeline": "Next quarter"},
    {"priority": "P3 — Monitor",    "criteria": "Sporadic negative feedback or positive to amplify","owner": "CS Manager",       "timeline": "Ongoing"},
    {"priority": "P4 — Share",      "criteria": "Strong positive feedback / praise",               "owner": "Marketing",        "timeline": "Amplify immediately"},
]


# ── R28: Ticket Triage & Priority Scorer ─────────────────────────────────────

_TRIAGE_KEYWORDS = {
    "critical": {
        "keywords": ["down","outage","data loss","breach","hack","cannot login","payment failed","money deducted","refund urgent","legal","court","fraud","scam","all users","production down","critical"],
        "priority": "P1", "sla_response": "15 minutes", "sla_resolve": "2 hours",
        "color": "#ef4444", "auto_escalate": True,
    },
    "high": {
        "keywords": ["not working","broken","error","bug","cannot access","order not received","wrong item","duplicate charge","angry","urgent","asap","immediately","escalate","supervisor","manager"],
        "priority": "P2", "sla_response": "1 hour", "sla_resolve": "8 hours",
        "color": "#f97316", "auto_escalate": False,
    },
    "medium": {
        "keywords": ["slow","delay","issue","problem","update","where is","when will","how long","refund","return","question","help","need assistance"],
        "priority": "P3", "sla_response": "4 hours", "sla_resolve": "2 business days",
        "color": "#eab308", "auto_escalate": False,
    },
    "low": {
        "keywords": ["suggestion","feedback","nice to have","feature request","general inquiry","how to","tutorial","guide","wondering","curious","thank you","appreciate"],
        "priority": "P4", "sla_response": "8 hours", "sla_resolve": "5 business days",
        "color": "#22c55e", "auto_escalate": False,
    },
}

_TRIAGE_CATEGORIES = {
    "billing":        ["payment","invoice","charge","refund","receipt","billing","subscription","renewal","pricing","plan"],
    "technical":      ["bug","error","crash","not loading","broken","feature","integration","api","login","password","account"],
    "delivery":       ["shipping","delivery","tracking","order","package","courier","logistics","dispatch","not received","wrong item"],
    "account":        ["account","profile","settings","password","email","username","access","blocked","suspended"],
    "product":        ["product","quality","defective","damage","size","colour","specification","description","photo"],
    "feedback":       ["suggestion","feedback","review","rating","experience","improve","great","love","terrible","worst","best"],
    "general_inquiry":["how to","tutorial","guide","info","details","what is","when","where","contact"],
}

_TRIAGE_CHANNEL_WEIGHTS = {
    "social_media": 1.5,  # Social complaints spread — handle faster
    "whatsapp":     1.3,
    "phone":        1.2,
    "chat":         1.0,
    "email":        1.0,
    "app_review":   1.4,  # Public reviews need fast response
}

_TRIAGE_SENTIMENT_SIGNALS = {
    "very_negative": ["worst","terrible","horrible","pathetic","useless","disgusting","outrageous","never again","fraud","cheat","scam","police","court","legal"],
    "negative":      ["bad","disappointed","frustrated","angry","annoyed","unhappy","not satisfied","poor","slow","rude"],
    "neutral":       ["okay","average","decent","normal","expected","fine","alright"],
    "positive":      ["good","happy","satisfied","great","nice","helpful","quick","easy","smooth"],
    "very_positive": ["amazing","excellent","outstanding","fantastic","love","best","perfect","five star","recommend","superb"],
}


def score_ticket_priority(
    ticket_text: str,
    customer_name: str = "",
    channel: str = "email",
    customer_tier: str = "standard",
    is_repeat_contact: bool = False,
    language: str = "en",
) -> dict:
    text_lower = ticket_text.lower()

    # Detect priority level
    detected_priority = "low"
    matched_keywords  = []
    for level, config in _TRIAGE_KEYWORDS.items():
        hits = [kw for kw in config["keywords"] if kw in text_lower]
        if hits:
            detected_priority = level
            matched_keywords  = hits
            break  # first match wins (ordered critical→low)

    priority_config = _TRIAGE_KEYWORDS[detected_priority]

    # Detect category
    detected_category = "general_inquiry"
    for cat, kws in _TRIAGE_CATEGORIES.items():
        if any(kw in text_lower for kw in kws):
            detected_category = cat
            break

    # Detect sentiment
    detected_sentiment = "neutral"
    for sentiment, signals in _TRIAGE_SENTIMENT_SIGNALS.items():
        if any(s in text_lower for s in signals):
            detected_sentiment = sentiment
            break

    # Score calculation (0–100)
    base_score = {"critical": 90, "high": 70, "medium": 45, "low": 20}[detected_priority]
    channel_multiplier = _TRIAGE_CHANNEL_WEIGHTS.get(channel, 1.0)
    tier_boost = {"vip": 15, "premium": 10, "standard": 0, "new": -5}.get(customer_tier, 0)
    repeat_boost = 10 if is_repeat_contact else 0
    sentiment_boost = {"very_negative": 10, "negative": 5, "neutral": 0, "positive": -5, "very_positive": -10}.get(detected_sentiment, 0)

    final_score = min(100, int(base_score * channel_multiplier) + tier_boost + repeat_boost + sentiment_boost)

    # Suggested response
    if detected_priority == "critical":
        suggested_response = f"Hi {customer_name or 'there'}, we've received your message and are treating this as our top priority. Our team is investigating right now and will update you within 15 minutes."
    elif detected_priority == "high":
        suggested_response = f"Hi {customer_name or 'there'}, we understand this is urgent and are sorry for the trouble. We're looking into this right away and will get back to you within 1 hour."
    elif detected_priority == "medium":
        suggested_response = f"Hi {customer_name or 'there'}, thank you for reaching out. We've noted your concern and our team will look into this and respond within 4 hours."
    else:
        suggested_response = f"Hi {customer_name or 'there'}, thanks for writing in! We'll review your message and get back to you within 8 business hours."

    return {
        "ticket_text":         ticket_text,
        "customer_name":       customer_name,
        "channel":             channel,
        "customer_tier":       customer_tier,
        "is_repeat_contact":   is_repeat_contact,
        "priority":            priority_config["priority"],
        "priority_level":      detected_priority,
        "priority_color":      priority_config["color"],
        "priority_score":      final_score,
        "sla_first_response":  priority_config["sla_response"],
        "sla_resolution":      priority_config["sla_resolve"],
        "auto_escalate":       priority_config["auto_escalate"],
        "category":            detected_category,
        "sentiment":           detected_sentiment,
        "matched_keywords":    matched_keywords[:5],
        "suggested_response":  suggested_response,
        "routing_suggestion": {
            "team":   "L2 / Senior Agent" if detected_priority in ("critical","high") else "L1 Agent",
            "action": "Escalate immediately to team lead" if priority_config["auto_escalate"] else "Assign to next available agent",
        },
        "cs_notes": [
            f"Respond within {priority_config['sla_response']} — SLA breach risk if delayed",
            "Log this ticket with correct priority tag in CRM for reporting accuracy",
            "If repeat contact, review prior ticket history before responding",
            "For billing/payment issues, always verify account before committing to resolution",
        ],
    }


def generate_voc_report(
    company_name: str,
    period: str = "Q1 FY 2025-26",
    total_responses: int = 0,
    nps_score: float = 0.0,
    csat_score: float = 0.0,
    top_positive_themes: list = None,
    top_negative_themes: list = None,
    data_sources: list = None,
    verbatim_samples: list = None,
    language: str = "en",
) -> dict:
    top_positive_themes = top_positive_themes or ["product_quality", "delivery"]
    top_negative_themes = top_negative_themes or ["customer_support", "pricing"]
    data_sources = data_sources or ["Customer support tickets (CRM)", "Post-purchase CSAT surveys"]
    verbatim_samples = verbatim_samples or []

    # NPS breakdown
    nps_band = "promoters" if nps_score >= 9 else ("passives" if nps_score >= 7 else "detractors")
    nps_label = "Excellent" if nps_score >= 50 else ("Good" if nps_score >= 30 else ("Needs Improvement" if nps_score >= 0 else "Critical"))

    # Build theme analysis
    theme_analysis = []
    for theme_key in top_positive_themes:
        td = _VOC_THEMES.get(theme_key, {"label": theme_key, "examples": []})
        theme_analysis.append({
            "theme":     td["label"],
            "sentiment": "positive",
            "examples":  td["examples"][:2],
            "action":    "Amplify in marketing — use as proof point",
        })
    for theme_key in top_negative_themes:
        td = _VOC_THEMES.get(theme_key, {"label": theme_key, "examples": []})
        theme_analysis.append({
            "theme":     td["label"],
            "sentiment": "negative",
            "examples":  td["examples"][:2],
            "action":    f"Escalate to {['Product','Ops','CS','Logistics'][hash(theme_key)%4]} team for root cause analysis",
        })

    # Prioritised action items
    action_items = []
    for i, neg in enumerate(top_negative_themes):
        td = _VOC_THEMES.get(neg, {"label": neg})
        priority = _VOC_ACTION_FRAMEWORK[min(i, 1)]  # first two get P1/P2
        action_items.append({
            "theme":    td["label"],
            "priority": priority["priority"],
            "owner":    priority["owner"],
            "timeline": priority["timeline"],
            "action":   f"Investigate and resolve root cause of '{td['label']}' complaints",
        })
    for pos in top_positive_themes[:1]:
        td = _VOC_THEMES.get(pos, {"label": pos})
        action_items.append({
            "theme":    td["label"],
            "priority": "P4 — Share",
            "owner":    "Marketing",
            "timeline": "Immediately",
            "action":   f"Feature '{td['label']}' praise in social proof, ads, and website",
        })

    return {
        "company_name":       company_name,
        "period":             period,
        "total_responses":    total_responses,
        "data_sources_used":  data_sources,
        "executive_summary": {
            "nps_score":     nps_score,
            "nps_label":     nps_label,
            "nps_action":    _VOC_NPS_BANDS[nps_band]["action"],
            "csat_score":    csat_score,
            "csat_label":    "Strong" if csat_score >= 4.2 else ("Acceptable" if csat_score >= 3.5 else "Needs Urgent Attention"),
            "top_praise":    [_VOC_THEMES.get(t, {"label":t})["label"] for t in top_positive_themes],
            "top_concerns":  [_VOC_THEMES.get(t, {"label":t})["label"] for t in top_negative_themes],
        },
        "nps_breakdown":      _VOC_NPS_BANDS,
        "theme_analysis":     theme_analysis,
        "verbatim_samples":   verbatim_samples,
        "action_plan":        action_items,
        "action_framework":   _VOC_ACTION_FRAMEWORK,
        "data_sources_all":   _VOC_DATA_SOURCES,
        "recommended_metrics": {
            "NPS":   {"desc":"Net Promoter Score", "target":">40 (Good) / >70 (World class)"},
            "CSAT":  {"desc":"Customer Satisfaction Score", "target":">4.2/5 or >85%"},
            "CES":   {"desc":"Customer Effort Score", "target":"<3 (lower is easier)"},
            "FCR":   {"desc":"First Contact Resolution", "target":">80%"},
            "Churn": {"desc":"Monthly churn rate", "target":"<2% for SaaS / <5% for e-com"},
        },
        "next_steps": [
            "Share report with all department heads within 3 days",
            "Assign owners to each action item in the plan",
            "Schedule follow-up VOC review in 90 days",
            "Close the loop with Detractors (NPS 0–6) within 48 hours",
            f"Publish internal highlights — what customers love about {company_name}",
        ],
        "cs_notes": [
            "VOC reports are most powerful when shared cross-functionally — not just CS",
            "Segment VOC by customer tier (new vs loyal vs churned) for richer insights",
            "NPS alone is not enough — always pair with open-ended 'why' question",
            "Run VOC quarterly at minimum; monthly for high-growth or high-churn businesses",
            "Close the loop with every Detractor — personal outreach recovers ~30% of at-risk customers",
        ],
    }


def generate_review_response_kit(
    business_name: str,
    product_name: str = "",
    platform: str = "google",
    review_text: str = "",
    star_rating: int = 5,
    reviewer_name: str = "there",
    support_email: str = "",
    language: str = "en",
) -> dict:
    # Determine sentiment
    if star_rating >= 4:
        sentiment = "positive"
    elif star_rating == 3:
        sentiment = "neutral"
    else:
        sentiment = "negative"

    platform_info = _REVIEW_PLATFORMS.get(platform, _REVIEW_PLATFORMS["general"])
    char_limit = platform_info["char_limit"]

    starters = _REVIEW_RESPONSE_STARTERS[sentiment]
    closers  = _REVIEW_CLOSERS[sentiment]
    starter  = starters[hash(review_text) % len(starters)].replace("{name}", reviewer_name)
    closer   = closers[hash(review_text) % len(closers)].replace("{support_email}", support_email or f"support@{business_name.lower().replace(' ','')}.com")

    # Build 3 response variants
    responses = []

    if sentiment == "positive":
        bodies = [
            f"It's wonderful to know that {product_name or 'our product'} met your expectations.",
            "Reviews like yours remind us why we do what we do every day.",
            "We've shared your feedback with the team — they'll be absolutely delighted!",
        ]
    elif sentiment == "neutral":
        bodies = [
            "We're glad parts of your experience were positive, and we're sorry we fell short in some areas.",
            f"We've noted your feedback about {product_name or 'your experience'} and are working to improve.",
            "Your 3-star experience tells us we have room to grow, and we take that seriously.",
        ]
    else:
        resolutions = [
            "Please reach out to us directly so we can arrange a replacement or full refund",
            "We'd like to offer you a complimentary replacement at no charge",
            "Our team will personally follow up to make this right",
        ]
        bodies = resolutions

    for i, body in enumerate(bodies):
        full_response = f"{starter} {body} {closer}"
        responses.append({
            "variant":       i + 1,
            "response_text": full_response,
            "char_count":    len(full_response),
            "within_limit":  len(full_response) <= char_limit,
        })

    # Short version (always within platform limit)
    short_resp = f"{starter} {closer}"

    # DO / DON'T for the platform
    dos = [
        "Respond within 24 hours — speed signals you care",
        "Use the reviewer's name to personalise",
        "Acknowledge specific details from their review",
        "Keep negative responses brief and move to private channel",
        "Thank them even for negative reviews — it's public goodwill",
    ]
    donts = [
        "Never argue with a negative reviewer publicly",
        "Don't use generic copy-paste replies — customers notice",
        "Don't ignore any review, even if it's just a star with no text",
        "Don't offer refunds/discounts publicly — DM instead",
        "Don't use overly formal language on casual platforms",
    ]

    return {
        "business_name":    business_name,
        "product_name":     product_name,
        "platform":         platform,
        "star_rating":      star_rating,
        "sentiment":        sentiment,
        "reviewer_name":    reviewer_name,
        "platform_tip":     platform_info["tip"],
        "char_limit":       char_limit,
        "response_variants": responses,
        "short_response":   short_resp,
        "dos":              dos,
        "donts":            donts,
        "response_sla": {
            "positive": "Within 48 hours",
            "neutral":  "Within 24 hours",
            "negative": "Within 2–4 hours — urgency matters",
        },
        "cs_notes": [
            "Set up Google Alerts / brand monitoring to catch reviews in real time",
            "Designate a 'Review Owner' in your team — don't let reviews go unanswered",
            "Track star rating trends monthly — sudden drops indicate a product/process issue",
            "For Amazon/Flipkart: flag fake/abusive reviews using the platform's 'Report' feature",
            "Aim for >4.3 average rating — below 4.0 significantly impacts purchase intent",
        ],
    }


def generate_sla_policy(
    company_name: str,
    plan_tiers: list = None,
    support_channels: list = None,
    business_hours: str = "Mon–Sat, 9am–6pm IST",
    language: str = "en",
) -> dict:
    plan_tiers = plan_tiers or ["basic", "standard", "premium"]
    support_channels = support_channels or ["chat", "email"]

    # Build per-plan SLA
    plan_slas = {}
    tier_configs = {
        "basic":    {"channels": ["email"],            "hours": "Business hours only", "priorities": ["medium","low"],            "response_boost": 1.0},
        "standard": {"channels": ["chat","email"],     "hours": "Mon–Sat 9am–9pm",     "priorities": ["high","medium","low"],     "response_boost": 0.75},
        "premium":  {"channels": ["chat","email","phone","whatsapp"], "hours": "24×7", "priorities": ["critical","high","medium","low"], "response_boost": 0.5},
        "enterprise":{"channels": ["chat","email","phone","whatsapp","dedicated_csm"], "hours": "24×7 + dedicated", "priorities": ["critical","high","medium","low"], "response_boost": 0.25},
    }

    for plan in plan_tiers:
        cfg = tier_configs.get(plan, tier_configs["standard"])
        plan_sla = {}
        for pri in cfg["priorities"]:
            tier = _SLA_PRIORITY_TIERS[pri]
            plan_sla[pri] = {
                "first_response": tier["first_response"],
                "resolution":     tier["resolution"],
                "channels":       [c for c in cfg["channels"] if c in (support_channels + ["email","chat","phone","whatsapp"])],
                "support_hours":  cfg["hours"],
            }
        plan_slas[plan] = plan_sla

    channel_slas = {ch: _SLA_BY_CHANNEL[ch] for ch in support_channels if ch in _SLA_BY_CHANNEL}

    return {
        "company_name":      company_name,
        "plan_tiers":        plan_tiers,
        "support_channels":  support_channels,
        "business_hours":    business_hours,
        "priority_tiers":    _SLA_PRIORITY_TIERS,
        "plan_slas":         plan_slas,
        "channel_slas":      channel_slas,
        "breach_actions":    _SLA_BREACH_ACTIONS,
        "sla_exclusions":    _SLA_EXCLUSIONS,
        "kpi_targets":       _SLA_METRICS,
        "review_cadence":    {
            "weekly":   "SLA compliance & breach count reviewed in team standup",
            "monthly":  "Full SLA report to management with trend analysis",
            "quarterly":"SLA targets reviewed and revised based on team capacity",
        },
        "cs_notes": [
            "Publish SLA policy on your website/help centre — customers should know what to expect",
            "Set up automated alerts at 75% SLA consumption — don't wait for breaches",
            "Define 'business hours' clearly — Indian holidays vary by state",
            "WhatsApp SLA is increasingly important for Indian SMBs — prioritise it",
            "Review SLA targets every 6 months as team scales",
        ],
    }


def generate_agent_training_manual(
    company_name: str,
    industry: str,
    support_channels: list = None,
    tone: str = "friendly",
    language: str = "en",
) -> dict:
    support_channels = support_channels or ["chat", "email"]
    scenarios = _ATM_SCENARIOS.get(industry, _ATM_SCENARIOS["general"])
    tone_guide = _ATM_TONE_GUIDE.get(tone, _ATM_TONE_GUIDE["neutral"])

    module_content = {}
    for mod in _ATM_MODULES:
        if mod == "Company & Product Overview":
            module_content[mod] = {
                "description": "Agents must know the company, its products, pricing, and policies before taking any live interactions.",
                "checklist": [
                    f"Read {company_name} company overview document",
                    "Complete product walkthrough / demo",
                    "Study pricing tiers and key plans",
                    "Memorise top 10 FAQs for the product",
                    "Understand refund and return policy",
                ],
            }
        elif mod == "Communication Standards":
            module_content[mod] = {
                "description": "All agents must maintain consistent, professional, and brand-aligned communication.",
                "tone": tone,
                "scripts": tone_guide,
                "channels": support_channels,
            }
        elif mod == "Handling Common Queries":
            module_content[mod] = {
                "description": "Use standard resolution flows for the most frequent query types.",
                "resolution_steps": ["Greet → Verify → Understand → Solve → Confirm → Close"],
                "industry_scenarios": scenarios[:2],
            }
        elif mod == "Escalation Protocol":
            module_content[mod] = {
                "description": "Follow the escalation matrix strictly. Never promise what cannot be delivered.",
                "matrix": _ATM_ESCALATION_MATRIX,
                "triggers": ["Legal threat", "Fraud", "Regulatory", "Media risk", "3 unresolved contacts"],
            }
        elif mod == "Tools & Systems":
            module_content[mod] = {
                "description": "Agents must be proficient in all tools before going live.",
                "tools": ["CRM / Helpdesk (e.g. Freshdesk, Zoho Desk)", "Live chat platform", "Knowledge base", "Ticketing system", "Internal escalation tracker"],
                "tip": "Always update ticket status in real time — never in bulk at end of shift.",
            }
        elif mod == "Performance Metrics":
            module_content[mod] = {
                "description": "Agents are measured on these KPIs weekly.",
                "kpis": _ATM_KPIs,
            }
        elif mod == "Role Play Scenarios":
            module_content[mod] = {
                "description": "Practice the following scenarios before going live. TL will evaluate and sign off.",
                "scenarios": scenarios,
            }
        elif mod == "Assessment & Certification":
            module_content[mod] = {
                "description": "Agents must pass assessment before handling live customers.",
                "assessment": [
                    "Written test: 20 MCQs on policy + product (pass mark: 70%)",
                    "Role play: 2 scenarios evaluated by TL",
                    "Shadow: 2 hours of listening to senior agent",
                    "Supervised: First 5 live chats reviewed by TL",
                ],
                "certification_validity": "6 months — refresher required after that",
            }

    return {
        "company_name": company_name,
        "industry": industry,
        "support_channels": support_channels,
        "tone": tone,
        "modules": module_content,
        "dos": _ATM_DO_DONTS["do"],
        "donts": _ATM_DO_DONTS["dont"],
        "kpis": _ATM_KPIs,
        "escalation_matrix": _ATM_ESCALATION_MATRIX,
        "onboarding_timeline": [
            {"day": "Day 1–2",   "activity": "Company & product overview, policy study"},
            {"day": "Day 3",     "activity": "Tool training and system access setup"},
            {"day": "Day 4",     "activity": "Role play and scenario practice"},
            {"day": "Day 5",     "activity": "Written assessment + TL role play evaluation"},
            {"day": "Day 6–7",   "activity": "Shadow listening (2h) + supervised live chats"},
            {"day": "Day 8+",    "activity": "Independent handling with weekly QA review"},
        ],
        "ca_notes": [
            "Keep signed copy of training completion for compliance and audit trail",
            "Update manual every quarter or on major policy change",
            "Maintain training register with agent name, date, and TL signature",
        ],
    }


def generate_chatbot_script(
    business_name: str,
    industry: str,
    bot_name: str = "",
    top_faqs: list = None,
    escalation_trigger: str = "",
    tone: str = "friendly",
    platform: str = "whatsapp",
    language: str = "en",
) -> dict:
    bot_name = bot_name or f"{business_name.split()[0]}Bot"
    industry_key = industry.lower().replace(" ", "_")
    default_faqs = _CHATBOT_INDUSTRY_FAQS.get(industry_key, _CHATBOT_INDUSTRY_FAQS["ecommerce"])

    # Merge custom FAQs with defaults
    faq_list = []
    if top_faqs:
        for faq in top_faqs[:5]:
            if isinstance(faq, dict):
                faq_list.append((faq.get("question", ""), faq.get("answer", "")))
            elif isinstance(faq, str):
                faq_list.append((faq, "Our team will get back to you on this shortly."))
    if len(faq_list) < 3:
        faq_list.extend(default_faqs[:3 - len(faq_list)])

    greeting = _CHATBOT_GREETINGS.get(platform, _CHATBOT_GREETINGS["whatsapp"]).format(
        bot_name=bot_name, business=business_name
    )
    fallback = _CHATBOT_FALLBACKS.get(tone, _CHATBOT_FALLBACKS["friendly"])
    escalation_msg = (
        f"Connecting you with our team now 🤝 Please hold — a support agent will respond within 2 hours.\n\n"
        f"Business hours: Mon–Sat, 10 AM – 7 PM IST\nFor urgent issues: {escalation_trigger or 'Type AGENT anytime'}"
    )

    # Build decision tree nodes
    nodes = [
        {
            "id": "start",
            "trigger": ["Hi", "Hello", "Hey", "Start", "1", "help"],
            "message": greeting,
            "next_nodes": ["faq_" + str(i) for i in range(len(faq_list))] + ["escalate"],
        }
    ]

    for i, (question, answer) in enumerate(faq_list):
        nodes.append({
            "id": f"faq_{i}",
            "trigger": [str(i + 1), question[:30]],
            "message": answer,
            "next_nodes": ["start", "escalate"],
            "quick_replies": ["Main Menu 🏠", "Talk to Human 🙋"],
        })

    nodes.append({
        "id": "escalate",
        "trigger": _CHATBOT_ESCALATION_TRIGGERS + ([escalation_trigger] if escalation_trigger else []),
        "message": escalation_msg,
        "next_nodes": [],
        "is_terminal": True,
    })

    nodes.append({
        "id": "fallback",
        "trigger": ["*"],
        "message": fallback,
        "next_nodes": ["start", "escalate"],
        "quick_replies": ["Main Menu 🏠", "Talk to Human 🙋"],
    })

    # WhatsApp-ready script format
    wa_script = f"=== {bot_name} — WhatsApp Bot Script ===\n\n"
    wa_script += f"GREETING:\n{greeting}\n\n"
    for i, (q, a) in enumerate(faq_list):
        wa_script += f"IF user says '{i+1}' or '{q[:25]}':\n→ {a}\n→ Quick replies: [Main Menu] [Talk to Human]\n\n"
    wa_script += f"IF user says AGENT/HUMAN/HELP:\n→ {escalation_msg}\n\n"
    wa_script += f"FALLBACK (anything else):\n→ {fallback}\n"

    return {
        "business": business_name,
        "bot_name": bot_name,
        "platform": platform,
        "tone": tone,
        "faq_count": len(faq_list),
        "decision_tree": nodes,
        "wa_ready_script": wa_script,
        "faqs_covered": [{"question": q, "answer": a} for q, a in faq_list],
        "escalation_triggers": _CHATBOT_ESCALATION_TRIGGERS,
        "setup_tips": [
            "Upload this script to your WhatsApp Business API provider (Interakt, Wati, AiSensy)",
            "Set business hours so customers know when humans are available",
            "Test every flow before going live — use a separate test number",
            "Add your most common complaint keywords to escalation triggers",
            "Review bot conversations weekly and add new FAQs to reduce escalations",
        ],
        "platforms_supported": ["WhatsApp Business API", "Instagram DM", "Website chat widget", "Telegram Bot"],
    }


def generate_returns_policy(
    business_name: str,
    industry: str,
    custom_return_days: int = 0,
    custom_refund_days: int = 0,
    refund_modes: list = None,
    contact_email: str = "",
    contact_phone: str = "",
    language: str = "en",
) -> dict:
    industry_key = industry.lower().replace(" ", "_")
    cfg = _RETURNS_WINDOWS.get(industry_key, _RETURNS_WINDOWS["ecommerce"])
    exclusions = _RETURNS_EXCLUSIONS.get(industry_key, _RETURNS_EXCLUSIONS["ecommerce"])

    ret_days = custom_return_days or cfg["return_days"]
    ref_days = custom_refund_days or cfg["refund_days"]
    refund_modes = refund_modes or ["Original payment method", "Store credit / wallet"]

    policy_sections = [
        {
            "section": "Return Window",
            "content": (
                f"We accept returns within {ret_days} days of delivery for eligible items. "
                "Items must be unused, in original condition, and with all original packaging and tags intact."
            ) if ret_days > 0 else "All sales are final. Returns are not accepted except in case of defective or wrongly shipped items.",
        },
        {
            "section": "Refund Policy",
            "content": (
                f"Once we receive and inspect your return, refunds are processed within {ref_days} business days. "
                f"Refunds are issued via: {', '.join(refund_modes)}."
            ),
        },
        {
            "section": "Exchange Policy",
            "content": (
                f"We offer exchanges within {ret_days} days of delivery, subject to stock availability. "
                "Size or colour exchanges can be requested via WhatsApp or email."
            ) if cfg["exchange"] else "Exchanges are not available. Please return and reorder.",
        },
        {
            "section": "Non-Returnable Items",
            "content": "The following items are not eligible for return or refund:\n" + "\n".join(f"• {e}" for e in exclusions),
        },
        {
            "section": "How to Initiate a Return",
            "content": (
                f"1. Contact us within {ret_days} days of delivery\n"
                f"2. Email: {contact_email or 'support@' + business_name.lower().replace(' ', '') + '.com'}\n"
                f"3. WhatsApp: {contact_phone or '+91-XXXXXXXXXX'}\n"
                "4. Share your order number and reason for return\n"
                "5. We will arrange pickup (no self-shipping needed for eligible returns)"
            ),
        },
        {
            "section": "Defective or Wrong Product",
            "content": "If you receive a defective, damaged, or incorrect item, please contact us within 48 hours of delivery with photos. We will arrange a replacement or full refund at no cost to you.",
        },
        {
            "section": "GST on Refunds",
            "content": "GST included in the original price will be refunded proportionally. Credit note will be issued as per GST regulations (Rule 53 of CGST Rules).",
        },
    ]

    faq_pairs = [
        {"q": "How long will my refund take?", "a": f"Refunds are processed within {ref_days} business days after we receive the returned item."},
        {"q": "Can I return a sale or discounted item?", "a": "Sale items are eligible for exchange only, not refunds, unless defective."},
        {"q": "What if I received the wrong item?", "a": "Contact us within 48 hours with your order number and a photo. We'll send the correct item immediately."},
        {"q": "Do I need to pay for return shipping?", "a": "No — we arrange free pickup for all eligible returns."},
        {"q": "Can I cancel my order?", "a": "Orders can be cancelled before dispatch. Contact us immediately and we'll process a full refund."},
    ]

    return {
        "business": business_name,
        "industry": industry,
        "policy_title": f"{business_name} — Returns & Refund Policy",
        "summary_badge": {
            "return_window": f"{ret_days} days" if ret_days > 0 else "No returns",
            "refund_timeline": f"{ref_days} business days",
            "exchange": "Yes" if cfg["exchange"] else "No",
            "free_pickup": "Yes",
        },
        "policy_sections": policy_sections,
        "whatsapp_snippets": _WHATSAPP_TEMPLATES,
        "faq_pairs": faq_pairs,
        "legal_note": "This policy is governed by the Consumer Protection Act, 2019 and the Consumer Protection (E-Commerce) Rules, 2020.",
    }


def generate_support_analytics(
    business_name: str,
    industry: str,
    week_label: str,
    total_tickets: int,
    resolved_tickets: int,
    avg_frt_hrs: float,
    avg_resolution_hrs: float,
    csat_score: float,
    ticket_categories: dict,
    agent_data: list,
    channel_data: dict,
    prev_week_tickets: int,
    prev_week_csat: float,
) -> dict:
    biz = business_name or "Your Team"
    bench = _INDUSTRY_BENCHMARKS.get(industry, _INDUSTRY_BENCHMARKS["saas"])

    # Core metrics
    open_tickets = max(0, total_tickets - resolved_tickets)
    resolution_rate = round((resolved_tickets / max(total_tickets, 1)) * 100, 1)
    csat_pct = round(csat_score * 20, 1)  # Convert 5-scale to %

    # WoW change
    ticket_change = round(((total_tickets - prev_week_tickets) / max(prev_week_tickets, 1)) * 100, 1)
    csat_change = round(csat_score - prev_week_csat, 2)
    ticket_trend = "up" if ticket_change > 0 else "down"
    csat_trend = "up" if csat_change > 0 else "down"

    # Benchmark comparison
    frt_vs_bench = "better" if avg_frt_hrs <= bench["frt_hrs"] else "worse"
    res_vs_bench = "better" if avg_resolution_hrs <= bench["resolution_hrs"] else "worse"
    csat_vs_bench = "better" if csat_pct >= bench["csat"] else "worse"

    # SLA health
    sla_health = "green"
    if avg_frt_hrs > bench["frt_hrs"] * 1.5 or avg_resolution_hrs > bench["resolution_hrs"] * 1.5:
        sla_health = "red"
    elif avg_frt_hrs > bench["frt_hrs"] or avg_resolution_hrs > bench["resolution_hrs"]:
        sla_health = "yellow"

    # Top categories
    sorted_cats = sorted(ticket_categories.items(), key=lambda x: x[1], reverse=True)
    category_breakdown = [
        {
            "category": cat,
            "count": count,
            "pct": round((count / max(total_tickets, 1)) * 100, 1),
            "icon": _CATEGORY_ICONS.get(cat, "📋"),
        }
        for cat, count in sorted_cats[:6]
    ]

    # Agent leaderboard
    agent_board = []
    for agent in (agent_data or []):
        score = 0
        score += min(agent.get("csat", 0) * 20, 40)   # max 40 pts from CSAT
        score += min(agent.get("resolved", 0), 30)      # max 30 pts from volume
        score += max(0, 20 - agent.get("avg_res_hrs", 24))  # faster = more pts
        score += 10 if agent.get("fcr", 0) >= 70 else 0     # bonus for good FCR
        agent_board.append({
            "name": agent.get("name", "Agent"),
            "tickets_resolved": agent.get("resolved", 0),
            "avg_csat": agent.get("csat", 0),
            "avg_resolution_hrs": agent.get("avg_res_hrs", 24),
            "fcr_pct": agent.get("fcr", 0),
            "performance_score": min(100, round(score)),
        })
    agent_board.sort(key=lambda x: x["performance_score"], reverse=True)

    # Channel breakdown
    channel_breakdown = [
        {"channel": ch, "count": cnt, "pct": round((cnt / max(total_tickets, 1)) * 100, 1)}
        for ch, cnt in (channel_data or {}).items()
    ]
    channel_breakdown.sort(key=lambda x: x["count"], reverse=True)

    # Insights & actions
    insights = []
    if ticket_trend == "up" and ticket_change > 20:
        insights.append(f"⚠️ Ticket volume up {ticket_change}% WoW — investigate root cause, likely a product/process issue.")
    if csat_vs_bench == "worse":
        insights.append(f"📉 CSAT ({csat_pct}%) below {industry} benchmark ({bench['csat']}%) — review low-scoring tickets this week.")
    if frt_vs_bench == "worse":
        insights.append(f"⏱ First response time ({avg_frt_hrs}h) exceeds benchmark ({bench['frt_hrs']}h) — consider auto-acknowledgement emails.")
    if res_vs_bench == "better":
        insights.append(f"✅ Resolution time ({avg_resolution_hrs}h) is better than {industry} benchmark ({bench['resolution_hrs']}h) — great work!")
    if category_breakdown and category_breakdown[0]["pct"] > 30:
        top = category_breakdown[0]
        insights.append(f"🔁 {top['category']} is {top['pct']}% of all tickets — consider a self-serve FAQ or automation for this category.")
    if not insights:
        insights.append("✅ All metrics within benchmark range — maintain the momentum!")

    # Weekly summary text
    summary = f"Week of {week_label}: {total_tickets} tickets ({ticket_change:+.1f}% WoW), {resolution_rate}% resolution rate, CSAT {csat_pct}% ({csat_change:+.2f} vs last week). SLA health: {sla_health.upper()}."

    return {
        "action": "support_analytics",
        "business_name": biz,
        "industry": industry,
        "week": week_label or "This Week",
        "summary": summary,
        "kpis": {
            "total_tickets": total_tickets,
            "resolved_tickets": resolved_tickets,
            "open_tickets": open_tickets,
            "resolution_rate_pct": resolution_rate,
            "avg_frt_hrs": avg_frt_hrs,
            "avg_resolution_hrs": avg_resolution_hrs,
            "csat_pct": csat_pct,
            "sla_health": sla_health,
        },
        "wow_change": {
            "ticket_change_pct": ticket_change,
            "ticket_trend": ticket_trend,
            "csat_change": csat_change,
            "csat_trend": csat_trend,
        },
        "benchmark_comparison": {
            "industry": industry,
            "frt": {"yours": avg_frt_hrs, "benchmark": bench["frt_hrs"], "status": frt_vs_bench},
            "resolution": {"yours": avg_resolution_hrs, "benchmark": bench["resolution_hrs"], "status": res_vs_bench},
            "csat": {"yours": csat_pct, "benchmark": bench["csat"], "status": csat_vs_bench},
        },
        "category_breakdown": category_breakdown,
        "agent_leaderboard": agent_board,
        "channel_breakdown": channel_breakdown,
        "insights": insights,
        "action_items": [
            "Send this week's CSAT report to all agents by Monday morning.",
            f"Investigate the top ticket category ({category_breakdown[0]['category'] if category_breakdown else 'N/A'}) — can it be automated?",
            f"{'Reward' if agent_board else 'Track'} the top-performing agent this week — recognition drives performance.",
            "Review all CSAT < 3 tickets personally — find the pattern.",
        ],
    }


def generate_customer_360(
    customer_name: str,
    customer_email: str,
    customer_since_months: int,
    total_orders: int,
    total_revenue: float,
    last_order_days_ago: int,
    open_tickets: int,
    total_tickets: int,
    avg_resolution_hrs: float,
    avg_csat: float,
    plan_type: str,
    has_referred: bool,
    payment_status: str,
) -> dict:
    name = customer_name or "Customer"

    # Health score calculation
    score = 100
    # Recency
    if last_order_days_ago > 90:
        score -= 30
    elif last_order_days_ago > 30:
        score -= 15
    elif last_order_days_ago > 14:
        score -= 5
    # Support load
    if open_tickets > 3:
        score -= 20
    elif open_tickets > 1:
        score -= 10
    # CSAT
    if avg_csat < 3:
        score -= 25
    elif avg_csat < 4:
        score -= 10
    # Resolution time
    if avg_resolution_hrs > 48:
        score -= 10
    elif avg_resolution_hrs > 24:
        score -= 5
    # Payment
    if payment_status == "overdue":
        score -= 20
    elif payment_status == "at_risk":
        score -= 10
    # Positive signals
    if has_referred:
        score += 10
    if total_orders > 10:
        score += 5
    score = max(0, min(100, score))

    # Segment
    segment = "critical"
    for seg, data in _HEALTH_SEGMENTS.items():
        if score >= data["min"]:
            segment = seg
            break

    seg_data = _HEALTH_SEGMENTS[segment]

    # Churn risk
    churn_risk = "high" if score < 50 else ("medium" if score < 70 else "low")
    churn_signals = _CHURN_SIGNALS[churn_risk]

    # Sentiment
    csat_int = max(1, min(5, round(avg_csat)))
    sentiment_label, sentiment_color, sentiment_action = _SENTIMENT_MAP[csat_int]

    # LTV estimate (simple)
    avg_order_value = total_revenue / max(total_orders, 1)
    monthly_orders = total_orders / max(customer_since_months, 1)
    ltv_estimate = avg_order_value * monthly_orders * 24  # 24-month projection

    # Next best actions
    actions = []
    if open_tickets > 0:
        actions.append(f"Resolve {open_tickets} open ticket(s) within 4 hours — customer is waiting")
    if churn_risk == "high":
        actions.append("Send personal outreach email from CS manager within 24 hours")
        actions.append("Offer 1-month extension or discount as retention gesture")
    if churn_risk == "medium":
        actions.append("Schedule a 15-min check-in call this week")
        actions.append("Share 3 tips to get more value from the product")
    if has_referred:
        actions.append("Send a thank-you gift or loyalty reward — they've referred you")
    if avg_csat >= 4.5 and churn_risk == "low":
        actions.append("Ask for a Google/G2 review — high CSAT, right time")
        actions.append("Introduce upsell: premium plan or add-on feature")
    if payment_status == "overdue":
        actions.append("Follow up on overdue payment — escalate to finance if no response in 48h")

    # Timeline summary (last 5 interactions simulated)
    timeline = [
        {"event": "Customer joined", "days_ago": customer_since_months * 30, "type": "onboarding"},
        {"event": "Last order placed", "days_ago": last_order_days_ago, "type": "purchase"},
        {"event": f"{total_tickets} support ticket(s) raised (total)", "days_ago": 0, "type": "support"},
    ]
    if open_tickets > 0:
        timeline.append({"event": f"{open_tickets} ticket(s) still open", "days_ago": 0, "type": "alert"})

    return {
        "action": "customer_360",
        "customer_name": name,
        "customer_email": customer_email or "—",
        "plan_type": plan_type or "Standard",
        "customer_since_months": customer_since_months,
        "health_score": score,
        "health_label": seg_data["label"],
        "health_color": seg_data["color"],
        "recommended_action": seg_data["action"],
        "churn_risk": churn_risk,
        "churn_signals": churn_signals,
        "sentiment": {"label": sentiment_label, "color": sentiment_color, "action": sentiment_action, "avg_csat": avg_csat},
        "financials": {
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "avg_order_value": round(avg_order_value, 2),
            "ltv_24m_estimate": round(ltv_estimate, 2),
            "payment_status": payment_status,
        },
        "support_metrics": {
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "avg_resolution_hrs": avg_resolution_hrs,
            "support_load": "High" if open_tickets > 2 else ("Normal" if open_tickets > 0 else "Clear"),
        },
        "loyalty_signals": {
            "has_referred": has_referred,
            "tenure_months": customer_since_months,
            "repeat_buyer": total_orders > 3,
        },
        "next_best_actions": actions[:5],
        "timeline": sorted(timeline, key=lambda x: x["days_ago"], reverse=True),
        "outreach_templates": {
            "at_risk_email": f"Subject: We noticed you've been quiet, {name} — can we help?\n\nHi {name},\n\nWe noticed it's been a while and wanted to reach out personally. Is there anything we can do better? Your feedback means everything to us.\n\nI'd love to schedule a quick 10-min call — reply with your availability.\n\nWarm regards,\n[Your Name]\nCustomer Success",
            "champion_ask": f"Hi {name}! 🎉 You've been one of our most valued customers. Would you be open to sharing a quick review? It takes 2 minutes and means the world to us. [Link] — Thank you!",
            "win_back_wa": f"Hi {name} 👋 We miss you! It's been a while. Here's something special just for you — reply YES to claim your exclusive offer. 🎁",
        },
    }


def _csat_survey_builder(
    business_name: str,
    product_name: str,
    survey_goal: str,
    customer_segment: str,
    industry: str,
    max_questions: int,
    include_nps: bool,
) -> dict:
    biz     = business_name or "Our Company"
    product = product_name or "our product"
    goal    = _SURVEY_GOALS.get(survey_goal, _SURVEY_GOALS["overall"])
    bank    = _QUESTION_BANKS.get(survey_goal, _QUESTION_BANKS["overall"])
    mq      = int(max_questions) if max_questions else 8

    # Build question list
    questions = []
    for q in bank[:mq]:
        qtext = q["question"].replace("{product}", product).replace("{company}", biz)
        scale = _SCALE_DESCRIPTIONS.get(q["type"], {})
        entry = {
            "id": q["id"],
            "order": len(questions) + 1,
            "question": qtext,
            "type": q["type"],
            "scale": scale.get("scale", ""),
            "scale_low": scale.get("low", ""),
            "scale_high": scale.get("high", ""),
            "why_this_question": q["why"],
            "benchmark": scale.get("benchmark", ""),
        }
        if "options" in q:
            entry["options"] = q["options"]
        questions.append(entry)

    # NPS question if not already included and flag is set
    nps_included = any(q["id"] == "nps" for q in questions)
    if include_nps and not nps_included and len(questions) < mq:
        nps_q = next((q for q in bank if q["id"] == "nps"), None)
        if nps_q:
            scale = _SCALE_DESCRIPTIONS["rating_10"]
            questions.append({
                "id": "nps", "order": len(questions) + 1,
                "question": nps_q["question"].replace("{product}", product),
                "type": "rating_10", "scale": scale["scale"],
                "scale_low": scale["low"], "scale_high": scale["high"],
                "why_this_question": "Net Promoter Score",
                "benchmark": scale["benchmark"],
            })

    # Intro & outro
    intro = f"Hi! We'd love your feedback on your experience with {product}. This takes less than 2 minutes and helps us improve for you. Thank you 🙏 — Team {biz}"
    outro = f"Thank you for your feedback! Your responses help us make {product} better every day. If you have any urgent issues, please contact us at [support email]. — Team {biz}"

    # Scoring guide
    scoring_guide = {
        "csat_formula": "CSAT (%) = (Number of satisfied responses [4+5]) / (Total responses) × 100",
        "csat_benchmark": "Industry average: 75–85%. World-class: 90%+",
        "nps_formula":    "NPS = % Promoters (9-10) − % Detractors (0-6)",
        "nps_benchmark":  "Good: >20. Excellent: >50. World-class: >70",
        "ces_formula":    "CES (Customer Effort Score) = Average score on 'ease' question",
        "ces_benchmark":  "Low effort (4-5) is the goal — correlates strongly with loyalty",
        "response_rate":  "Aim for >20% response rate. <10% = biased data risk.",
    }

    # Analysis tips
    analysis_tips = [
        "Segment responses by customer tier (Enterprise vs Standard) to spot gaps.",
        "Track CSAT trend monthly — a 5-point drop month-on-month needs immediate attention.",
        "Open-text responses: use word frequency analysis to find top themes.",
        "Follow up personally with all detractors (NPS 0-6) within 48 hours.",
        "Share weekly CSAT score with the whole CS team — transparency drives improvement.",
        "A/B test survey timing (immediate vs 24h after) to see which gets better quality responses.",
    ]

    return {
        "action": "csat_survey",
        "business_name": biz,
        "product_name": product,
        "survey_goal": goal["label"],
        "survey_focus": goal["focus"],
        "total_questions": len(questions),
        "estimated_time": f"{max(1, len(questions) // 3)} minute{'s' if len(questions) > 3 else ''}",
        "intro_message": intro,
        "questions": questions,
        "outro_message": outro,
        "distribution_channels": _DISTRIBUTION_CHANNELS,
        "scoring_guide": scoring_guide,
        "analysis_tips": analysis_tips,
        "pro_tips": [
            "Keep surveys under 5 questions for >40% completion rate.",
            "Always ask the open-text question last — don't lead with it.",
            "Personalise the greeting with customer's name for +15% open rate.",
            "Never send a survey more than once per customer per quarter.",
            "Close the loop: tell customers what changed because of their feedback.",
        ],
    }


def _winback_campaign_generator(
    business_name: str,
    product_name: str,
    customer_name: str,
    churn_reason: str,
    inactive_days: int,
    industry: str,
    offer_type: str,
    offer_value: str,
    cs_rep_name: str,
) -> dict:
    biz      = business_name or "Our Company"
    product  = product_name or "our platform"
    cust     = customer_name or "there"
    rep      = cs_rep_name or "The Team"
    offer_v  = offer_value or "20%"
    reason   = _CHURN_REASONS.get(churn_reason, _CHURN_REASONS["unknown"])
    angle    = reason["angle"]
    offer_intro = _OFFER_INTROS.get(offer_type, _OFFER_INTROS["discount"])
    pain_points = _INDUSTRY_PAIN_POINTS.get(industry, _INDUSTRY_PAIN_POINTS["saas"])
    offer_label = f"{offer_v} off" if offer_type == "discount" else f"{offer_type.replace('_',' ')} ({offer_v})"

    # Build 5-email sequence
    emails = []

    # Email 1 — The Breakup Email
    emails.append({
        "step": 1, "day": 0, "name": "The Breakup Email",
        "subject": f"We miss you, {cust} 💙",
        "body": f"""Hi {cust},

We noticed you haven't been around {product} in a while, and we just wanted to check in.

We know life gets busy. And we know {biz} may not have been perfect.

But here's what's changed since you left:
• [New feature 1 — address {angle}]
• [New feature 2 — improvement since they left]
• [Customer success story relevant to their use case]

No pitch, no pressure — we just wanted you to know the door is always open.

If there's anything we got wrong, I'd genuinely love to hear it. Hit reply and let's talk.

Warmly,
{rep}
{biz}

P.S. If you're just not interested anymore, no hard feelings. We'll always be here if you change your mind.""",
    })

    # Email 2 — Value Reminder
    emails.append({
        "step": 2, "day": 7, "name": "The Value Reminder",
        "subject": f"While you were away, here's what {product} helped others achieve",
        "body": f"""Hi {cust},

Quick story: one of our customers — a {industry} business just like yours — was {pain_points[0]}.

They came back to {product} and within 30 days:
✅ [Result 1 — specific and measurable]
✅ [Result 2 — specific and measurable]
✅ [Result 3 — specific and measurable]

Sound familiar? That's exactly what we want to help you achieve too.

We've put together a short guide just for returning customers: [link]

No login needed to read. Just 3 minutes that might change your mind.

{rep}
{biz}""",
    })

    # Email 3 — The Offer
    emails.append({
        "step": 3, "day": 14, "name": "The Offer Email",
        "subject": f"A special offer for you, {cust} — {offer_label} to come back",
        "body": f"""Hi {cust},

I'll get straight to the point.

{offer_intro}: {offer_label}.

This is exclusive for returning customers — we're not offering this publicly.

Here's how to claim it:
1. Click this link: [your reactivation link]
2. Your {offer_type.replace('_',' ')} is applied automatically
3. You're back in — with everything waiting for you exactly as you left it

This offer expires in 7 days, on [date].

We'd love to have you back. And if there's anything you need help with when you return, I'll personally make sure you're taken care of.

{rep}
{biz}

[CLAIM MY OFFER →]""",
    })

    # Email 4 — Last Chance
    emails.append({
        "step": 4, "day": 21, "name": "The Last Chance",
        "subject": f"Your {offer_label} expires tomorrow, {cust}",
        "body": f"""Hi {cust},

Just a quick heads-up — your exclusive {offer_label} expires tomorrow.

After that, I can't guarantee we'll be able to extend this offer.

If {pain_points[1]} is still something you're dealing with, {product} can help. Takes less than 5 minutes to reactivate.

[CLAIM MY {offer_type.upper().replace('_',' ')} →]

If the timing still isn't right, I completely understand. No pressure — ever.

{rep}
{biz}""",
    })

    # Email 5 — The Goodbye
    emails.append({
        "step": 5, "day": 30, "name": "The Goodbye (Optional)",
        "subject": f"Thank you, {cust} — and goodbye (for now)",
        "body": f"""Hi {cust},

I'm going to be honest: we're removing you from our win-back sequence today.

Not because we don't want you back — but because we respect your inbox and your decision.

If you ever decide you want to give {product} another shot, the door is always open. Just reply to this email or visit [your website].

And if there's anything we could have done differently — anything at all — I'd genuinely love to know. Your feedback helps us get better for everyone.

Thank you for the time you spent with us. We're rooting for you either way. 💙

{rep}
{biz}""",
    })

    # WhatsApp messages
    wa_messages = {
        "Day 0": _WHATSAPP_WINBACK["day0"].format(customer=cust, product=product, rep=rep, business=biz),
        "Day 7": _WHATSAPP_WINBACK["day7"].format(customer=cust, product=product, rep=rep, business=biz),
        "Day 14": _WHATSAPP_WINBACK["day14"].format(customer=cust, product=product, rep=rep, business=biz, offer=offer_label),
        "Day 21": _WHATSAPP_WINBACK["day21"].format(customer=cust, product=product, rep=rep, business=biz, offer=offer_label),
    }

    # Segmentation strategy
    segmentation = [
        {"segment": "Churned < 30 days",  "approach": "Soft check-in — no offer yet. Focus on what changed.", "offer_timing": "Day 14"},
        {"segment": "Churned 30-90 days", "approach": "Value reminder + offer. They're still warm.", "offer_timing": "Day 7"},
        {"segment": "Churned > 90 days",  "approach": "Lead with your biggest improvement. Offer immediately.", "offer_timing": "Day 0"},
        {"segment": "High-value churned", "approach": "Personal call first, then email. Don't lose them to templates.", "offer_timing": "Immediate phone call"},
    ]

    # Win-back metrics to track
    metrics = [
        {"metric": "Open Rate", "benchmark": "20-30% for win-back emails", "good": ">25%"},
        {"metric": "Click Rate", "benchmark": "5-10% for win-back emails", "good": ">7%"},
        {"metric": "Reactivation Rate", "benchmark": "5-15% of churned customers", "good": ">10%"},
        {"metric": "Revenue Recovered", "benchmark": "Track monthly", "good": "Positive ROI vs campaign cost"},
    ]

    return {
        "action": "winback_campaign",
        "business_name": biz,
        "product_name": product,
        "customer_name": cust,
        "churn_reason": reason["label"],
        "inactive_days": inactive_days,
        "offer": {"type": offer_type, "value": offer_v, "label": offer_label},
        "email_sequence": emails,
        "whatsapp_sequence": wa_messages,
        "segmentation_guide": segmentation,
        "metrics_to_track": metrics,
        "pro_tips": [
            "Personalise with the customer's actual name — win-back open rates jump 26% with personalisation.",
            "Send Email 1 from a real person's email (rep@company.com) — not noreply@.",
            "The offer email (Day 14) typically has the highest conversion — A/B test the subject line.",
            "WhatsApp messages have 3× the open rate of emails — use for high-value customers.",
            f"For {reason['label']}: lead every message with {angle}.",
            "Stop the sequence the moment they reactivate — nobody likes messages after they've already come back.",
        ],
    }


def _escalation_email_generator(
    business_name: str,
    customer_name: str,
    ticket_id: str,
    issue_summary: str,
    sla_breached: str,
    priority: str,
    escalation_type: str,
    escalate_to: str,
    cs_rep_name: str,
    current_status: str,
    customer_tier: str,
) -> dict:
    from datetime import datetime as _dt
    from datetime import timedelta as _td

    priority_cfg   = _PRIORITY_CONFIG.get(priority, _PRIORITY_CONFIG["high"])
    tier_note      = _CUSTOMER_TIER_NOTES.get(customer_tier, _CUSTOMER_TIER_NOTES["standard"])
    tier_risk      = f"⚠️ Note: {tier_note}"
    now            = _dt.now()
    ack_deadline   = (now + _td(hours=1)).strftime("%I:%M %p today")
    next_update    = (now + _td(hours=4)).strftime("%I:%M %p today")

    biz     = business_name or "Our Company"
    cust    = customer_name or "Customer"
    ticket  = ticket_id or "TKT-001"
    issue   = issue_summary or "Technical issue reported"
    status  = current_status or "Under investigation"
    rep     = cs_rep_name or "Support Team"
    esc_to  = escalate_to or "Senior Manager"
    sla     = sla_breached or "4-hour"

    # Internal escalation email
    internal_subject = _INTERNAL_TEMPLATES["subject"].format(
        priority=priority_cfg["label"], ticket_id=ticket,
        issue_summary=issue[:50], customer_name=cust,
    )
    internal_body = _INTERNAL_TEMPLATES["body"].format(
        escalate_to=esc_to, ticket_id=ticket, customer_name=cust,
        customer_tier=customer_tier.title(), priority_label=priority_cfg["label"],
        priority_emoji=priority_cfg["emoji"], issue_summary=issue,
        current_status=status, sla_breached=sla,
        response_target=priority_cfg["response_target"],
        followup_count="2+",
        customer_tier_note=tier_note,
        attempted_steps=f"Investigated root cause of: {issue}",
        ack_deadline=ack_deadline, cs_rep_name=rep,
    )

    # Customer-facing email
    customer_subject = _CUSTOMER_TEMPLATES["subject"].format(ticket_id=ticket)
    customer_body = _CUSTOMER_TEMPLATES["body"].format(
        customer_name=cust, ticket_id=ticket, issue_summary=issue,
        priority_label=priority_cfg["label"], next_update_time=next_update,
        immediate_contact=_IMMEDIATE_CONTACT.get(customer_tier, _IMMEDIATE_CONTACT["standard"]),
        cs_rep_name=rep, business_name=biz,
    )

    # Manager CC email
    manager_subject = _MANAGER_TEMPLATES["subject"].format(
        ticket_id=ticket, customer_name=cust, customer_tier=customer_tier.title()
    )
    manager_body = _MANAGER_TEMPLATES["body"].format(
        escalate_to=esc_to, ticket_id=ticket, customer_name=cust,
        customer_tier=customer_tier.title(), issue_summary=issue,
        sla_breached=sla, customer_tier_risk=tier_risk, cs_rep_name=rep,
    )

    # Escalation checklist
    checklist = [
        {"step": 1, "action": "Document all customer interactions so far in the ticket", "done": False},
        {"step": 2, "action": f"Send internal escalation email to {esc_to}", "done": False},
        {"step": 3, "action": "Send acknowledgment email to customer", "done": False},
        {"step": 4, "action": "Set ticket priority to " + priority_cfg["label"], "done": False},
        {"step": 5, "action": f"Follow up with {esc_to} if no response by {ack_deadline}", "done": False},
        {"step": 6, "action": f"Send resolution update to customer by {next_update}", "done": False},
        {"step": 7, "action": "Close loop — post-mortem if critical/high priority", "done": False},
    ]

    # SLA breach impact
    sla_impact = {
        "critical": "Immediate business impact — every minute counts. Skip email, call directly first.",
        "high":     "Significant customer frustration. Escalate now, email within 30 minutes.",
        "medium":   "Customer is waiting. Escalate today, email within 2 hours.",
        "low":      "Proactive escalation — good practice. Email within 4 hours.",
    }

    return {
        "action": "escalation_email",
        "ticket_id": ticket,
        "customer_name": cust,
        "priority": priority,
        "priority_config": priority_cfg,
        "customer_tier": customer_tier,
        "customer_tier_note": tier_note,
        "emails": {
            "internal": {
                "to": esc_to,
                "subject": internal_subject,
                "body": internal_body,
            },
            "customer": {
                "to": cust,
                "subject": customer_subject,
                "body": customer_body,
            },
            "manager_cc": {
                "to": esc_to,
                "subject": manager_subject,
                "body": manager_body,
            },
        },
        "escalation_checklist": checklist,
        "sla_breach_guidance": sla_impact.get(priority, sla_impact["high"]),
        "next_update_time": next_update,
        "ack_deadline": ack_deadline,
        "pro_tips": [
            "Always send the customer email within 15 minutes of deciding to escalate.",
            "CC your manager on every escalation — no surprises at the top.",
            f"Response target for {priority_cfg['label']} priority: {priority_cfg['response_target']}.",
            "Document root cause after resolution — prevents repeat escalations.",
            "For enterprise customers, a phone call before email shows urgency.",
        ],
    }


def _kb_article_generator(
    business_name: str,
    product_name: str,
    article_topic: str,
    article_type: str = "how_to",
    industry: str = "saas",
    audience: str = "end_user",
    tone: str = "friendly",
) -> dict:
    company   = business_name or "Your Business"
    product   = product_name  or "our platform"
    topic     = article_topic or "Getting Started"
    art_cfg   = _KB_ARTICLE_TYPES.get(article_type, _KB_ARTICLE_TYPES["how_to"])
    ind_exmpl = _INDUSTRY_KB_EXAMPLES.get(industry, _INDUSTRY_KB_EXAMPLES["saas"])
    rel_arts  = _RELATED_ARTICLE_TEMPLATES.get(industry, _RELATED_ARTICLE_TEMPLATES["saas"])
    tone_desc = _KB_TONES.get(tone, _KB_TONES["friendly"])
    aud_desc  = _AUDIENCE_CONTEXT.get(audience, _AUDIENCE_CONTEXT["end_user"])

    from datetime import date as _date
    year = _date.today().year

    # Generate sections with writing guides
    sections = []
    for i, section_name in enumerate(art_cfg["structure"]):
        if section_name == "Step-by-Step Instructions" or section_name == "Step-by-Step Fix":
            content_hint = f"Write 4-8 numbered steps. Start each step with a verb (Click, Navigate, Enter, Select). Be specific about where UI elements are located in {product}."
            sample = f"1. Log in to {product} and go to Settings\n2. Click on [Section Name] in the left sidebar\n3. Select [Option] from the dropdown\n4. Click Save to apply changes\n5. You'll see a confirmation message — your changes are live!"
        elif section_name == "Overview" or section_name == "What Is It?":
            content_hint = f"1-2 paragraph intro explaining what this feature does and why it matters. Speak directly to the {audience} — mention the benefit, not just the feature."
            sample = f"This guide explains how to {topic.lower()} in {product}. Whether you're a first-time user or looking to improve your workflow, this article walks you through everything you need."
        elif section_name == "Prerequisites":
            content_hint = "List what the user needs before starting — account permissions, feature access, other setup steps. Use a bullet list."
            sample = f"Before you begin, make sure you have:\n• An active {product} account\n• Admin or [Role] permissions\n• [Any other requirement]"
        elif section_name == "Troubleshooting" or section_name == "Quick Fix (Try First)":
            content_hint = "List the top 3-5 issues users face with this topic and a one-line fix for each. Use a table or numbered list."
            sample = "**Issue: Page not loading** → Clear browser cache and try again\n**Issue: Button missing** → Check your account permissions with your Admin\n**Issue: Error message showing** → Note the error code and contact support"
        elif section_name == "Related Articles":
            content_hint = "List 4-6 related help articles as bullet links. Pick titles that logically follow from this article."
            sample = "\n".join(f"• [{a}](#)" for a in rel_arts[:5])
        elif section_name == "Still Need Help?" or section_name == "Contact Us" or section_name == "When to Contact Support":
            content_hint = "Friendly closing section with support channels. Include WhatsApp number, email, chat, and response SLA."
            sample = f"Can't find what you're looking for? Our support team is here to help!\n\n💬 Live Chat: Available in-app (9 AM – 6 PM IST)\n📱 WhatsApp: [Your number]\n📧 Email: support@{company.lower().replace(' ','')}.com\nWe typically respond within 4 business hours."
        elif section_name == "Top Questions" or section_name == "Detailed Answers":
            content_hint = f"List 5-8 frequently asked questions about {topic}. For each, provide a clear 1-3 sentence answer."
            sample = f"**Q: How long does {topic.lower()} take?**\nA: Most users complete this in under 5 minutes.\n\n**Q: Can I undo this action?**\nA: Yes — go to Settings > History to revert changes."
        elif section_name == "Common Causes":
            content_hint = "List 3-5 root causes of the problem. Help users self-diagnose before following fix steps."
            sample = f"This issue usually happens because:\n• Incorrect permissions on your account\n• Browser cache / cookies conflict\n• {product} is undergoing maintenance\n• Network or connectivity issue"
        elif section_name == "Tips & Tricks":
            content_hint = "3-5 power-user tips that go beyond the basics. These delight users and reduce support volume."
            sample = f"💡 **Pro tip:** Bookmark the {topic.lower()} page for quick access\n💡 Use keyboard shortcut [Ctrl+K] to search faster\n💡 Set up notifications to get alerted when [event] happens"
        elif section_name == "Key Terms":
            content_hint = "Define 4-6 terms users might encounter. Use a simple glossary format."
            sample = "**[Term 1]:** [Simple definition in 1 sentence]\n**[Term 2]:** [Simple definition in 1 sentence]"
        elif section_name == "Examples":
            content_hint = "1-2 real-world examples showing the concept in action. Use an Indian SMB context."
            sample = f"**Example 1:** Ravi Textiles uses {topic.lower()} to [achieve outcome], saving 2 hours per week.\n**Example 2:** A Bengaluru SaaS startup sets up {topic.lower()} to automatically [action]."
        elif section_name == "What's New" or section_name == "Key Changes":
            content_hint = "Describe what changed and how it impacts users. Use before/after format where helpful."
            sample = "We've updated [Feature] to make it faster and easier to use:\n• **Before:** Users had to [old way]\n• **After:** Now you can [new way] in one click"
        else:
            content_hint = f"Write content for this section about {topic}. Keep it clear, scannable, and relevant to {audience} users."
            sample = f"[Content for {section_name} — tailored to your {product} and {topic}]"

        sections.append({
            "section":      section_name,
            "order":        i + 1,
            "writing_guide": content_hint,
            "sample_content": sample,
            "word_count_target": "80-120 words" if section_name not in ["Step-by-Step Instructions", "Step-by-Step Fix", "Troubleshooting", "Common Causes"] else "120-200 words",
        })

    # SEO titles
    seo_titles = [
        f"How to {topic} in {product} — Step-by-Step Guide [{year}]",
        f"{topic}: Complete Guide for {company} Users",
        f"{topic} — {product} Help Center",
        f"How to {topic} | {company} Support",
        f"{topic} Explained — {product} Knowledge Base",
    ]

    # Meta description
    meta_desc = f"Learn how to {topic.lower()} in {product}. This step-by-step guide covers everything {audience.replace('_',' ')} users need to know. Updated {year}."

    return {
        "action":        "kb_article",
        "business_name": company,
        "product_name":  product,
        "article_topic": topic,
        "article_type":  art_cfg["label"],
        "audience":      aud_desc,
        "tone":          tone_desc,
        "sections":      sections,
        "seo_titles":    seo_titles,
        "meta_description": meta_desc,
        "tags":          [topic.lower(), product.lower(), industry, audience.replace("_"," "), "help center", "support"],
        "related_articles": rel_arts,
        "industry_examples": ind_exmpl[:5],
        "publishing_checklist": [
            "Add screenshots or GIFs for each major step",
            "Test all links and ensure they open correctly",
            "Have a non-technical team member read and flag confusing parts",
            "Add the article to the correct help center category",
            "Update the 'Last reviewed' date at top of article",
            "Share the article link in your onboarding email sequence",
            "Set a reminder to review and update in 6 months",
        ],
        "writing_tips": [
            f"Tone: {tone_desc}",
            "Use short sentences — aim for Flesch Reading Ease score > 60",
            "Bold key terms and action words to aid scanning",
            "Add a TL;DR summary at the very top for busy readers",
            "Use numbered lists for steps, bullet lists for options/features",
            "India SMB tip: Add WhatsApp support option — most preferred support channel",
            "Avoid passive voice — say 'Click Save' not 'Save should be clicked'",
        ],
    }


def _onboarding_sequence_builder(
    business_name: str,
    product_name: str,
    industry: str,
    customer_type: str,
    key_features: list,
    success_metric: str,
    cs_rep_name: str,
) -> dict:
    company = business_name or "Your Company"
    product = product_name or "Your Product"
    ind_key = industry if industry in _SUCCESS_METRICS_BY_INDUSTRY else "general"
    ctype = customer_type if customer_type in _CUSTOMER_TYPE_CONTEXT else "smb"
    ctx = _CUSTOMER_TYPE_CONTEXT[ctype]
    cs_rep = cs_rep_name or "Your CS Team"

    demo_features = key_features if key_features else [
        "Core dashboard and reporting",
        "Team collaboration and sharing",
        "Integrations with existing tools",
        "Automated workflows",
        "Analytics and insights",
    ]

    default_metric = success_metric or _SUCCESS_METRICS_BY_INDUSTRY[ind_key][0]

    email_sequence = []

    email_templates = {
        "day_0": {
            "subject":   f"Welcome to {product}! Here's your quick-start guide 🚀",
            "body":      f"""Hi [First Name],

Welcome to {product}! We're genuinely excited to have {'{'}company{'}'} on board.

You made a great decision. Here's how to get the most out of your first 24 hours:

✅ Step 1: [Complete your profile / Set up your account]
✅ Step 2: [Do the core action that delivers first value — e.g., create your first project]
✅ Step 3: [Invite your team / Connect your first integration]

Your quick-start video (3 minutes): [Link]

I'm {cs_rep}, your dedicated success manager. I'm here to make sure {'{'}company{'}'} gets incredible value from {product}.

Reply to this email anytime — I read every message personally.

Let's make this work,
{cs_rep}
{company}

P.S. Most teams that get started in the first 24 hours see [key benefit] within their first week. Don't wait — the setup takes less than 15 minutes.""",
            "send_time": "Immediately on sign-up",
            "goal":      _ONBOARDING_MILESTONES["day_0"]["goal"],
            "checklist": ["Account created", "Welcome email sent", "CS rep assigned", "Slack/WhatsApp connected"],
        },
        "day_1": {
            "subject":   f"Your first [key action] in {product} — step by step",
            "body":      f"""Hi [First Name],

You've set up your account — great start!

Today's goal: Get to your first [key outcome] in under 15 minutes.

Here's exactly how:

1. Go to [Feature Name] → click [Button]
2. [Step 2 — specific action]
3. [Step 3 — complete the first core workflow]

When you've done this, you'll have [specific outcome]. That's when {product} really starts saving you time.

Here's a 2-minute video showing exactly how: [Link]

Stuck? Reply to this email or [WhatsApp/Slack] me directly.

{cs_rep}""",
            "send_time": "Day 1 — 9 AM customer timezone",
            "goal":      _ONBOARDING_MILESTONES["day_1"]["goal"],
            "checklist": ["First login confirmed", "Core feature introduced", "Tutorial link sent"],
        },
        "day_7": {
            "subject":   "Quick check-in — how's {product} working for you?",
            "body":      f"""Hi [First Name],

It's been a week — how are things going with {product}?

I wanted to check in personally because the first week is the most important. Teams that get set up properly in week 1 typically see [key metric] improve by [X%] within 30 days.

Quick question: What's one thing that's been unclear or frustrating so far?

Even if everything's going great, I'd love to know. It takes 30 seconds to reply and helps me make sure you're on the right track.

Also — here are 3 features most teams discover in week 2 that save hours:
→ {demo_features[1] if len(demo_features) > 1 else '[Feature 2]'}
→ {demo_features[2] if len(demo_features) > 2 else '[Feature 3]'}
→ {demo_features[3] if len(demo_features) > 3 else '[Feature 4]'}

Want a 15-minute call to walk through these? Pick a time here: [Calendly link]

{cs_rep}""",
            "send_time": "Day 7 — 10 AM customer timezone",
            "goal":      _ONBOARDING_MILESTONES["day_7"]["goal"],
            "checklist": ["Usage data reviewed", "Check-in email sent", "Risk signals checked"],
        },
        "day_14": {
            "subject":   f"The {product} features your team isn't using yet (but should be)",
            "body":      f"""Hi [First Name],

You've been using {product} for two weeks — you've got the basics down.

Now let's go deeper. Here are the features that teams like yours use to [get even more value]:

🔧 {demo_features[1] if len(demo_features) > 1 else 'Advanced Feature 1'}: [1-line benefit + link to guide]
⚡ {demo_features[2] if len(demo_features) > 2 else 'Advanced Feature 2'}: [1-line benefit + link to guide]
🔗 {demo_features[3] if len(demo_features) > 3 else 'Integration Feature'}: [1-line benefit + link to guide]

Most teams that activate these 3 features see [key metric] improve within 2 weeks.

I've prepared a personalised setup guide for {'{'}company{'}'} based on how you've been using {product}: [Personalised link]

{cs_rep}""",
            "send_time": "Day 14 — 9 AM customer timezone",
            "goal":      _ONBOARDING_MILESTONES["day_14"]["goal"],
            "checklist": ["Feature adoption reviewed", "Advanced features introduced", "Personal guide sent"],
        },
        "day_30": {
            "subject":   f"[First Name], your {product} impact report — Month 1",
            "body":      f"""Hi [First Name],

One month in — let's look at what {'{'}company{'}'} has achieved with {product}:

📊 [Key metric 1]: [value]
📊 [Key metric 2]: [value]
⏱️ Time saved: [estimated hours]
💰 Value delivered: [calculated ROI or outcome]

[Screenshot or data visual of their actual usage]

You're in the top [X%] of customers in your first month. Seriously — this is a great start.

For month 2, here's what I recommend focusing on:
1. [Next level goal based on their usage]
2. [Feature they haven't tried yet]
3. [Integration that would add value]

15-minute review call? I'll show you exactly what to focus on next: [Calendly link]

{cs_rep}""",
            "send_time": "Day 30 — 10 AM customer timezone",
            "goal":      _ONBOARDING_MILESTONES["day_30"]["goal"],
            "checklist": ["30-day usage report pulled", "ROI calculated", "Expansion opportunity identified"],
        },
        "day_60": {
            "subject":   f"Scaling {product} across your team — here's how",
            "body":      f"""Hi [First Name],

Two months in and {'{'}company{'}'} is clearly getting value from {product}.

A few teams similar to yours have recently expanded and seen [specific outcome]. Here's what they did differently:

1. [Expansion use case 1]
2. [Expansion use case 2]
3. [Add-on or higher tier benefit]

Would it make sense to explore this for {'{'}company{'}'} too?

I've prepared a quick expansion proposal: [Link] — it takes 2 minutes to review.

Happy to walk through it on a call: [Calendly]

{cs_rep}""",
            "send_time": "Day 60 — 10 AM customer timezone",
            "goal":      _ONBOARDING_MILESTONES["day_60"]["goal"],
            "checklist": ["Expansion opportunity qualified", "Proposal prepared", "Success story ready"],
        },
        "day_90": {
            "subject":   f"[First Name] — 3 months with {product}. Thank you 🙏",
            "body":      f"""Hi [First Name],

Three months. That's a milestone worth celebrating.

Here's a snapshot of {'{'}company{'}'}'s journey with {product}:
[90-day impact summary with key metrics]

You're now one of our established customers — and I have a small ask.

Would you be open to:
→ A 5-minute G2/Capterra review? [Link] — your words help others make better decisions
→ A quick case study? We'd love to feature {'{'}company{'}'}'s story (takes 20 minutes, we write the whole thing)
→ An introduction to someone in your network who might benefit from {product}?

Any one of these would mean a lot to us.

And of course — if you ever need anything, I'm always here.

Thank you for being a {product} customer,
{cs_rep}
{company}""",
            "send_time": "Day 90 — 10 AM customer timezone",
            "goal":      _ONBOARDING_MILESTONES["day_90"]["goal"],
            "checklist": ["90-day report prepared", "Review request sent", "Referral ask made", "Renewal date noted"],
        },
    }

    for day_key, milestone in _ONBOARDING_MILESTONES.items():
        template = email_templates.get(day_key, {})
        email_sequence.append({
            "day":       day_key,
            "milestone": milestone["label"],
            "goal":      milestone["goal"],
            "subject":   template.get("subject", f"[{milestone['label']}] — {product}"),
            "body":      template.get("body", f"Email body for {milestone['label']}"),
            "send_time": template.get("send_time", f"{day_key.replace('_',' ').title()} after sign-up"),
            "checklist": template.get("checklist", []),
            "channel":   ctx["channel"],
        })

    success_metrics = _SUCCESS_METRICS_BY_INDUSTRY[ind_key]

    return {
        "action":              "onboarding_sequence",
        "business_name":       company,
        "product_name":        product,
        "industry":            ind_key,
        "customer_type":       ctype,
        "cs_rep":              cs_rep,
        "total_touchpoints":   len(email_sequence),
        "email_sequence":      email_sequence,
        "risk_signals":        _RISK_SIGNALS,
        "success_metrics":     success_metrics,
        "primary_metric":      default_metric,
        "key_features":        demo_features,
        "channel":             ctx["channel"],
        "tone":                ctx["tone"],
        "response_sla":        ctx["response_sla"],
        "check_in_format":     ctx["check_in"],
        "onboarding_milestones": list(_ONBOARDING_MILESTONES.values()),
        "summary":             f"7-touchpoint onboarding sequence for {product} ({ctype} customers). Covers Day 0/1/7/14/30/60/90. Primary success metric: {default_metric}. {len(_RISK_SIGNALS)} risk signals monitored.",
    }
