"""Customer Support constants — language labels, SLA tiers, categories, templates."""
from __future__ import annotations

# ── Language labels ───────────────────────────────────────────────────────────
LANG_LABELS: dict[str, dict] = {
    "en": {"yes": "Yes",  "no": "No",    "na": "N/A"},
    "ta": {"yes": "ஆம்", "no": "இல்லை", "na": "பொருந்தாது"},
    "hi": {"yes": "हाँ", "no": "नहीं",  "na": "लागू नहीं"},
}

LANG_SYSTEM: dict[str, str] = {
    "en": "You are a friendly and professional customer support AI assistant. Be concise and helpful.",
    "ta": "நீங்கள் ஒரு நட்பான மற்றும் தொழில்முறை வாடிக்கையாளர் ஆதரவு AI உதவியாளர். தமிழில் பதிலளியுங்கள்.",
    "hi": "आप एक मित्रवत और पेशेवर ग्राहक सहायता AI सहायक हैं। हिंदी में उत्तर दें।",
}

# ── Ticket priority tiers ─────────────────────────────────────────────────────
PRIORITY_TIERS = {
    "P1": {"label": "Critical",  "response_sla": "1 hour",   "resolution_sla": "4 hours",  "color": "#ef4444"},
    "P2": {"label": "High",      "response_sla": "4 hours",  "resolution_sla": "24 hours", "color": "#f97316"},
    "P3": {"label": "Medium",    "response_sla": "8 hours",  "resolution_sla": "48 hours", "color": "#eab308"},
    "P4": {"label": "Low",       "response_sla": "24 hours", "resolution_sla": "72 hours", "color": "#22c55e"},
}

# ── Ticket categories ─────────────────────────────────────────────────────────
TICKET_CATEGORIES = [
    "billing",
    "technical_issue",
    "product_question",
    "complaint",
    "refund_request",
    "delivery_tracking",
    "account_access",
    "feature_request",
    "general_inquiry",
    "cancellation",
]

# ── CSAT ratings ──────────────────────────────────────────────────────────────
CSAT_SCALE = {
    5: {"label": "Very Satisfied",  "emoji": "😄"},
    4: {"label": "Satisfied",       "emoji": "🙂"},
    3: {"label": "Neutral",         "emoji": "😐"},
    2: {"label": "Dissatisfied",    "emoji": "😞"},
    1: {"label": "Very Dissatisfied","emoji": "😠"},
}

# ── Lead qualification BANT weights ──────────────────────────────────────────
BANT_WEIGHTS = {
    "budget":    0.30,
    "authority": 0.25,
    "need":      0.30,
    "timeline":  0.15,
}

# ── Sentiment thresholds ──────────────────────────────────────────────────────
SENTIMENT_THRESHOLDS = {
    "positive": 0.6,
    "neutral":  0.4,
    "negative": 0.0,
}

# ── WhatsApp message types ────────────────────────────────────────────────────
WHATSAPP_MESSAGE_TYPES = [
    "promotional", "transactional", "follow_up",
    "appointment_reminder", "feedback_request", "re_engagement",
]

# ── Support industries ────────────────────────────────────────────────────────
SUPPORT_INDUSTRIES = [
    "ecommerce", "saas", "retail", "healthcare", "education",
    "fintech", "logistics", "real_estate", "hospitality", "manufacturing",
]
