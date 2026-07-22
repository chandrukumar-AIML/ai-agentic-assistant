"""Social Media constants — platform limits, data tables, configs."""
from __future__ import annotations

# ── Platform character limits ─────────────────────────────────────────────────
PLATFORM_LIMITS: dict[str, int] = {
    "twitter":   280,
    "linkedin":  3000,
    "instagram": 2200,
    "facebook":  63206,
    "whatsapp":  4096,
    "youtube":   5000,
}

PLATFORM_HASHTAG_LIMITS: dict[str, int] = {
    "instagram": 30,
    "linkedin":  5,
    "twitter":   3,
    "facebook":  10,
    "youtube":   15,
}

# ── Post tones ────────────────────────────────────────────────────────────────
TONES = [
    "professional", "casual", "humorous", "inspirational",
    "educational", "urgent", "empathetic", "bold",
]

# ── Supported languages ───────────────────────────────────────────────────────
SUPPORTED_LANGUAGES = {
    "en": "English",
    "ta": "Tamil",
    "hi": "Hindi",
}

# ── Indian industries ─────────────────────────────────────────────────────────
INDIA_INDUSTRIES = [
    "retail", "restaurant", "healthcare", "education", "real_estate",
    "finance", "technology", "manufacturing", "agriculture", "logistics",
    "fashion", "beauty", "travel", "fitness", "legal", "ca_firm",
    "jewellery", "textile", "automobile", "insurance",
]

# ── Festive calendar (India) ──────────────────────────────────────────────────
FESTIVE_CALENDAR: dict[str, dict] = {
    "diwali":          {"name": "Diwali",           "month": "Oct/Nov",  "emoji": "🪔",  "vibe": "warm, prosperous, celebratory"},
    "holi":            {"name": "Holi",             "month": "Mar",      "emoji": "🌈",  "vibe": "colourful, joyful, playful"},
    "eid":             {"name": "Eid ul-Fitr",       "month": "Apr/May",  "emoji": "🌙",  "vibe": "grateful, festive, inclusive"},
    "christmas":       {"name": "Christmas",         "month": "Dec",      "emoji": "🎄",  "vibe": "warm, giving, joyful"},
    "new_year":        {"name": "New Year",          "month": "Jan",      "emoji": "🎆",  "vibe": "hopeful, fresh start, celebratory"},
    "independence_day":{"name": "Independence Day",  "month": "Aug",      "emoji": "🇮🇳", "vibe": "patriotic, proud, inspiring"},
    "republic_day":    {"name": "Republic Day",      "month": "Jan",      "emoji": "🇮🇳", "vibe": "patriotic, constitutional pride"},
    "pongal":          {"name": "Pongal",            "month": "Jan",      "emoji": "🌾",  "vibe": "harvest, gratitude, Tamil culture"},
    "onam":            {"name": "Onam",              "month": "Aug/Sep",  "emoji": "🌺",  "vibe": "prosperity, floral, Kerala culture"},
    "navratri":        {"name": "Navratri",          "month": "Oct",      "emoji": "💃",  "vibe": "devotion, dance, festive colours"},
    "raksha_bandhan":  {"name": "Raksha Bandhan",    "month": "Aug",      "emoji": "🪢",  "vibe": "sibling love, protection, warmth"},
    "ganesh_chaturthi":{"name": "Ganesh Chaturthi",  "month": "Aug/Sep",  "emoji": "🐘",  "vibe": "devotion, new beginnings, festive"},
    "mothers_day":     {"name": "Mother's Day",      "month": "May",      "emoji": "💐",  "vibe": "love, gratitude, appreciation"},
    "womens_day":      {"name": "Women's Day",       "month": "Mar",      "emoji": "👩",  "vibe": "empowering, inspiring, celebratory"},
    "teachers_day":    {"name": "Teacher's Day",     "month": "Sep",      "emoji": "📚",  "vibe": "respectful, grateful, educational"},
    "childrens_day":   {"name": "Children's Day",    "month": "Nov",      "emoji": "👶",  "vibe": "playful, fun, innocent joy"},
    "valentines":      {"name": "Valentine's Day",   "month": "Feb",      "emoji": "❤️",  "vibe": "love, romance, warmth"},
    "gst_day":         {"name": "GST Day",           "month": "Jul",      "emoji": "📋",  "vibe": "informative, professional, tax-aware"},
    "msme_day":        {"name": "MSME Day",          "month": "Jun",      "emoji": "🏭",  "vibe": "supportive, entrepreneurial, growth"},
    "custom":          {"name": "Custom Festival",   "month": "Any",      "emoji": "🎉",  "vibe": "celebratory, brand-aligned"},
}

# ── Post angles ───────────────────────────────────────────────────────────────
POST_ANGLES: dict[str, str] = {
    "brand_story":    "Share brand values + festival connection",
    "offer":          "Announce a festive sale or discount",
    "appreciation":   "Thank customers / celebrate with them",
    "behind_scenes":  "Show team celebrating the festival",
    "tip":            "Give a relevant tip tied to the festival",
    "contest":        "Run a festive giveaway or contest",
}

# ── Engagement benchmarks by industry ────────────────────────────────────────
INDUSTRY_BENCHMARKS: dict[str, dict] = {
    "retail":     {"instagram": 1.2, "linkedin": 0.5, "twitter": 0.3},
    "restaurant": {"instagram": 2.1, "linkedin": 0.4, "twitter": 0.5},
    "healthcare": {"instagram": 0.8, "linkedin": 1.2, "twitter": 0.4},
    "education":  {"instagram": 1.5, "linkedin": 1.8, "twitter": 0.6},
    "finance":    {"instagram": 0.6, "linkedin": 1.5, "twitter": 0.4},
    "default":    {"instagram": 1.0, "linkedin": 0.8, "twitter": 0.4},
}

# ── Thread types ──────────────────────────────────────────────────────────────
THREAD_TYPES = ["educational", "story", "tips_list", "case_study", "hot_take", "myth_busting"]

# ── Meme styles ───────────────────────────────────────────────────────────────
MEME_STYLES = ["relatable", "industry_joke", "before_after", "expectation_vs_reality", "trending_format"]
