# backend/verticals/agri/agri_agent.py
"""
AgriTech Domain Agent (Feature 9).

Serves Indian farmers in Tamil, Hindi, and English.
Capabilities:
  1. Crop disease diagnosis (GPT-4o Vision from photo)
  2. Mandi (market) price lookup (Agmarknet API / mock)
  3. Weather advisory (OpenWeatherMap)
  4. Government scheme discovery (PM-KISAN, PMFBY, etc.)
  5. Voice I/O via existing TTS/STT pipeline

Language detection: auto-detect from query, respond in same language.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from backend.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()

# ── Translations for UI labels ────────────────────────────────────────────────
_GREET = {
    "ta": "வணக்கம்! நான் உங்கள் AI விவசாய உதவியாளர்.",
    "hi": "नमस्ते! मैं आपका AI कृषि सहायक हूँ।",
    "en": "Hello! I am your AI AgriTech assistant.",
}

# ── Weather advisory ─────────────────────────────────────────────────────────

async def get_weather_advisory(
    district: str,
    state:    str = "Tamil Nadu",
    language: str = "en",
) -> dict:
    """Fetch 5-day weather from OpenWeatherMap and return farming advisory."""
    api_key  = settings.openweather_api_key
    location = f"{district},{state},IN"

    if not api_key:
        # Mock response for development
        return {
            "location":   f"{district}, {state}",
            "forecast":   "Partly cloudy, 28-32°C, 60% humidity",
            "advisory":   {
                "en": f"Good conditions for irrigation in {district}. Expect light rain in 3 days.",
                "hi": f"{district} में सिंचाई के लिए अच्छी स्थिति। 3 दिन में हल्की बारिश संभव।",
                "ta": f"{district}ல் நீர்ப்பாசனத்திற்கு நல்ல நிலை. 3 நாளில் லேசான மழை.",
            }.get(language, f"Advisory for {district}: Check local weather updates."),
            "mock": True,
        }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.openweathermap.org/data/2.5/forecast",
                params={"q": location, "appid": api_key, "units": "metric", "cnt": 5},
            )
            resp.raise_for_status()
            data = resp.json()

        forecasts = data.get("list", [])
        if not forecasts:
            return {"error": "No forecast data available."}

        temp      = forecasts[0]["main"]["temp"]
        humidity  = forecasts[0]["main"]["humidity"]
        desc      = forecasts[0]["weather"][0]["description"]
        rain_days = sum(1 for f in forecasts if "rain" in f.get("weather", [{}])[0].get("main", "").lower())

        advisory_en = (
            f"Current: {desc}, {temp:.0f}°C, {humidity}% humidity. "
            f"Rain expected on {rain_days} of next 5 days. "
            + ("Consider harvesting soon." if rain_days >= 3 else "Good time for field operations.")
        )

        return {
            "location":  f"{district}, {state}",
            "temp_c":    temp,
            "humidity":  humidity,
            "description": desc,
            "rain_days": rain_days,
            "advisory":  advisory_en,
        }
    except Exception as e:
        logger.error("Weather API error for %s: %s", district, e)
        return {"error": "Weather service temporarily unavailable."}


# ── Mandi price lookup ───────────────────────────────────────────────────────

async def get_mandi_prices(
    commodity: str,
    state:     str = "Tamil Nadu",
    district:  Optional[str] = None,
) -> dict:
    """
    Fetch current mandi (wholesale market) prices.
    Uses data.gov.in Agmarknet API (public, no key needed for basic queries).
    """
    try:
        params: dict = {
            "api-key": "579b464db66ec23bdd000001cdd3946e44ce4aada1b6761b3b15c29",  # public demo key
            "format":  "json",
            "filters": json_filters(commodity, state, district),
            "limit":   10,
            "offset":  0,
        }
        # Agmarknet data.gov.in endpoint
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070",
                params=params,
            )
            if resp.status_code == 200:
                data   = resp.json()
                records = data.get("records", [])
                if records:
                    return {
                        "commodity": commodity,
                        "state":     state,
                        "prices":    [
                            {
                                "market":    r.get("Market Name", ""),
                                "min_price": r.get("Min Price", 0),
                                "max_price": r.get("Max Price", 0),
                                "modal_price": r.get("Modal Price", 0),
                                "date":      r.get("Arrival Date", ""),
                                "unit":      "per quintal (₹)",
                            }
                            for r in records[:5]
                        ],
                    }
    except Exception as e:
        logger.debug("Agmarknet API failed (using mock): %s", e)

    # Fallback mock prices for common crops
    mock_prices = {
        "tomato":  {"min": 800,  "max": 1200, "modal": 1000},
        "rice":    {"min": 1900, "max": 2100, "modal": 2000},
        "wheat":   {"min": 2015, "max": 2150, "modal": 2100},
        "onion":   {"min": 600,  "max": 1400, "modal": 1000},
        "cotton":  {"min": 6000, "max": 7000, "modal": 6500},
        "sugarcane": {"min": 290, "max": 305, "modal": 295},
    }
    key   = commodity.lower().strip()
    price = mock_prices.get(key, {"min": 500, "max": 800, "modal": 650})

    return {
        "commodity": commodity,
        "state":     state,
        "prices": [{
            "market":      f"Mock {district or state} APMC",
            "min_price":   price["min"],
            "max_price":   price["max"],
            "modal_price": price["modal"],
            "date":        datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "unit":        "per quintal (₹)",
        }],
        "note": "Mock data — configure Agmarknet API key for live prices",
    }


def json_filters(commodity: str, state: str, district: Optional[str]) -> str:
    import json
    f: dict = {"Commodity": commodity, "State": state}
    if district:
        f["District"] = district
    return json.dumps(f)


# ── Government schemes ───────────────────────────────────────────────────────

def get_govt_schemes(query: str, language: str = "en") -> list[dict]:
    """Return relevant government agricultural schemes based on query keywords."""
    schemes = [
        {
            "name":        "PM-KISAN",
            "full_name":   "Pradhan Mantri Kisan Samman Nidhi",
            "benefit":     "₹6,000/year in 3 instalments directly to farmer's bank account",
            "eligibility": "Small and marginal farmers with land up to 2 hectares",
            "apply_url":   "https://pmkisan.gov.in",
            "keywords":    ["income support", "money", "benefit", "cash"],
        },
        {
            "name":        "PMFBY",
            "full_name":   "Pradhan Mantri Fasal Bima Yojana",
            "benefit":     "Crop insurance: farmer pays 1.5–2% premium, rest covered by Govt",
            "eligibility": "All farmers growing notified crops in notified areas",
            "apply_url":   "https://pmfby.gov.in",
            "keywords":    ["insurance", "crop loss", "damage", "flood", "drought"],
        },
        {
            "name":        "KCC",
            "full_name":   "Kisan Credit Card",
            "benefit":     "Short-term credit up to ₹3 lakh at 4% interest",
            "eligibility": "All farmers, sharecroppers, self-help groups",
            "apply_url":   "https://www.nabard.org/content.aspx?id=572",
            "keywords":    ["loan", "credit", "money", "interest"],
        },
        {
            "name":        "PKVY",
            "full_name":   "Paramparagat Krishi Vikas Yojana",
            "benefit":     "₹50,000/ha over 3 years for organic farming clusters",
            "eligibility": "Farmers forming clusters of 20+ members (50 ha)",
            "apply_url":   "https://pgsindia-ncof.gov.in",
            "keywords":    ["organic", "natural farming", "chemical free"],
        },
        {
            "name":        "Sub-Mission on Agricultural Mechanization",
            "full_name":   "SMAM",
            "benefit":     "40–80% subsidy on farm machinery and equipment",
            "eligibility": "Small, marginal, SC/ST farmers get higher subsidy",
            "apply_url":   "https://agrimachinery.nic.in",
            "keywords":    ["tractor", "machine", "equipment", "mechanization"],
        },
    ]

    q = query.lower()
    matched = [s for s in schemes if any(kw in q for kw in s["keywords"])]
    return matched if matched else schemes[:3]   # return top 3 if no match


# ── Crop disease diagnosis ───────────────────────────────────────────────────

async def diagnose_crop_disease(
    image_b64: str,
    crop_name: str = "",
    language:  str = "en",
) -> dict:
    """
    Diagnose crop disease from a photo.
    Tries GPT-4o Vision first, falls back to text-based Ollama advice.
    """
    from backend.config import get_settings
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL
    cfg = get_settings()

    system_prompt = (
        f"You are an expert agricultural plant pathologist. "
        f"Analyze crop symptoms and identify any diseases, pests, or deficiencies. "
        f"Respond in {language}. "
        f"Provide: disease name, severity (low/medium/high), affected area %, "
        f"immediate treatment, and prevention. "
        f"Use practical advice for Indian farmers. Be concise."
    )

    # Try GPT-4o Vision if API key available
    try:
        key = cfg.openai_api_key
        if key and key.startswith("sk-"):
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=key)
            crop_label = f"{crop_name} " if crop_name else ""
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text",      "text": f"Diagnose this {crop_label}crop image:"},
                            {"type": "image_url", "image_url": {
                                "url":    f"data:image/jpeg;base64,{image_b64}",
                                "detail": "low",
                            }},
                        ],
                    },
                ],
                max_tokens=500,
            )
            diagnosis = response.choices[0].message.content
            return {
                "crop":      crop_name or "Unknown",
                "language":  language,
                "diagnosis": diagnosis,
                "model":     "gpt-4o-vision",
            }
    except Exception as vision_err:
        logger.warning("Vision diagnosis failed, using text fallback: %s", type(vision_err).__name__)

    # Ollama text fallback — ask for general guidance based on crop name
    try:
        crop_label = crop_name or "the crop"
        text = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": f"A farmer has uploaded a photo of {crop_label} showing signs of disease/stress. Without seeing the image, provide common diseases for {crop_label}, their symptoms, and recommended treatments for Indian farmers."},
            ],
            model=OLLAMA_MODEL,
            max_tokens=400,
        )
        return {
            "crop":      crop_name or "Unknown",
            "language":  language,
            "diagnosis": text or "Disease diagnosis temporarily unavailable.",
            "model":     f"ollama/{OLLAMA_MODEL}",
            "note":      "Text-based guidance — vision analysis unavailable.",
        }
    except Exception as e:
        logger.error("Crop disease diagnosis failed: %s", e)
        return {"error": "Disease diagnosis temporarily unavailable."}


# ── Main agent function ───────────────────────────────────────────────────────

async def agri_agent(
    query:     str,
    language:  str = "en",
    district:  Optional[str] = None,
    state:     str = "Tamil Nadu",
    image_b64: Optional[str] = None,
) -> dict:
    """
    Main AgriTech agent dispatcher.
    Auto-routes query to the appropriate tool.
    """
    q = query.lower()

    # Language detection (simple heuristics)
    if any(c in query for c in "அஆஇஈஉஊ"):
        language = "ta"
    elif any(c in query for c in "अआइईउऊ"):
        language = "hi"

    # Route to appropriate tool
    if image_b64:
        crop_name = next((w for w in ["tomato", "rice", "wheat", "cotton", "corn", "potato"] if w in q), "")
        return await diagnose_crop_disease(image_b64, crop_name, language)

    if any(kw in q for kw in ["price", "mandi", "market", "rate", "விலை", "कीमत"]):
        # Extract commodity name (simplified)
        commodity = next(
            (w for w in ["tomato", "onion", "rice", "wheat", "cotton", "sugarcane", "potato"] if w in q),
            query.split()[0],
        )
        return await get_mandi_prices(commodity, state, district)

    if any(kw in q for kw in ["weather", "rain", "wind", "temperature", "மழை", "बारिश"]):
        return await get_weather_advisory(district or "Chennai", state, language)

    if any(kw in q for kw in ["scheme", "yojana", "government", "subsidy", "loan", "insurance", "योजना"]):
        schemes = get_govt_schemes(query, language)
        return {"schemes": schemes, "language": language}

    # Generic agricultural query → Ollama
    system = (
        f"You are an expert Indian agricultural advisor. "
        f"Answer in {language}. Focus on practical, actionable advice for Indian farmers. "
        f"Consider Indian climate, soil types, and available resources."
    )
    try:
        from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL
        text = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": query},
            ],
            model=OLLAMA_MODEL,
            max_tokens=400,
        )
        if not text:
            raise ValueError("Empty response from Ollama")
        return {"response": text, "language": language, "model": f"ollama/{OLLAMA_MODEL}"}
    except Exception as e:
        logger.error("AgriTech Ollama query failed: %s", e)
        return {"error": "AgriTech assistant temporarily unavailable."}
