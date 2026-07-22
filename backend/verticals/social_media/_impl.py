# backend/verticals/social_media/social_agent.py
"""
AI Social Media Manager (Feature 19).

Capabilities:
  1. Content generation — platform-optimized posts (GPT-4o-mini)
  2. DALL-E 3 image generation for social visuals
  3. LinkedIn posting via LinkedIn API v2
  4. Twitter/X posting via Twitter API v2 (Tweepy)
  5. Instagram — generate caption + image (manual post or Buffer API)
  6. Buffer API — schedule posts across all platforms
  7. Hashtag research and optimization
  8. Post analytics summary (impressions, engagement rate)
  9. Content calendar planning

Platform character limits:
  Twitter:   280 chars
  LinkedIn:  3000 chars (post), 220 chars (preview)
  Instagram: 2200 chars caption, 30 hashtags max
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from backend.config import get_settings
from backend.verticals.social_media.constants import FESTIVE_CALENDAR

logger   = logging.getLogger(__name__)
settings = get_settings()

# alias for legacy references
_FESTIVE_CALENDAR = FESTIVE_CALENDAR

_FESTIVE_SCRIPTS: dict = {
    "generic": {
        "appreciation": "Happy {festival} {emoji} from {brand}! 🎊\n\nThis {festival}, we're grateful for your trust and support. {vibe}\n\nWishing you joy, prosperity, and success! ✨",
        "offer":        "🎊 {festival} Sale is LIVE at {brand}! {emoji}\n\n✅ {offer}\n\nShop now — limited time only! 🛍️",
        "contest":      "🎁 {festival} Giveaway! {emoji}\n\nWin {prize}!\n\nHow to enter:\n✅ Like this post\n✅ Follow @{brand}\n✅ Tag 2 friends\n\nWinner announced: {draw_date}",
    },
    "diwali": {
        "appreciation": "🪔 Shubh Deepawali from {brand}! ✨\n\nThis festival of lights, we celebrate YOU — our valued community. May this Diwali bring warmth, prosperity, and new beginnings.\n\nDiwali Cheers! 🎆 #HappyDiwali",
        "offer":        "🪔 Diwali Dhamaka at {brand}! 🎉\n\n✨ {offer} — celebrate in style!\n\nHurry, offer ends with the festival! 🛍️ #DiwaliSale #DiwaliOffer",
        "contest":      "🎁 Diwali Giveaway from {brand}! 🪔\n\nWin {prize}!\n\nEnter:\n✅ Like & Share\n✅ Follow us\n✅ Tag a friend\n\nWinner on {draw_date}! #DiwaliContest",
    },
    "holi": {
        "appreciation": "🌈 Happy Holi from {brand}! 🎨\n\nSpread colours, spread love! May this Holi fill your life with vibrant joy. {vibe} ✨",
        "offer":        "🎨 Holi Special Offers at {brand}! 🌈\n\n{offer} — celebrate the festival of colours!\n\n#HappyHoli #HoliSale",
        "contest":      "🎨 Holi Contest at {brand}!\n\nShare your Holi selfie & win {prize}!\n\n#HoliContest #PlayWithColours",
    },
}

# ── Platform constraints ──────────────────────────────────────────────────────

_PLATFORM_CONFIG = {
    "twitter": {
        "max_chars":    280,
        "hashtag_limit": 3,
        "media_types":  ["image", "gif", "video"],
        "tone":         "concise, punchy, conversational",
        "format":       "Short hook + value + CTA. Use threads for longer content.",
    },
    "linkedin": {
        "max_chars":    3000,
        "hashtag_limit": 5,
        "media_types":  ["image", "video", "document", "poll"],
        "tone":         "professional, insightful, thought leadership",
        "format":       "Hook (2 lines) + story/insight + actionable takeaway + CTA + hashtags.",
    },
    "instagram": {
        "max_chars":    2200,
        "hashtag_limit": 30,
        "media_types":  ["image", "reel", "carousel"],
        "tone":         "visual-first, engaging, authentic",
        "format":       "Caption: hook + value + CTA. Put hashtags in first comment or at end.",
    },
}


# ── Content generation ────────────────────────────────────────────────────────

async def generate_post(
    topic:        str,
    platform:     str,          # twitter | linkedin | instagram
    tone:         str = "professional",
    include_emoji: bool = True,
    brand_name:   str = "",
    language:     str = "en",
    extra_context: str = "",
) -> dict:
    """
    Generate platform-optimized social media post content (Ollama-first).
    Returns post text, hashtags, and image prompt.
    """
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL
    import json
    cfg     = _PLATFORM_CONFIG.get(platform, _PLATFORM_CONFIG["linkedin"])
    emoji   = "Use relevant emojis." if include_emoji else "No emojis."

    system = f"""You are an expert social media content strategist.
Generate platform-optimized content for {platform.upper()}.
Format: {cfg['format']}
Max characters: {cfg['max_chars']}
Tone: {tone} ({cfg['tone']})
Hashtag limit: {cfg['hashtag_limit']}
{emoji}
Language: {language}

Return JSON:
{{
  "post_text": "complete post text including line breaks",
  "hashtags": ["tag1", "tag2"],
  "char_count": <number>,
  "image_prompt": "Detailed DALL-E 3 prompt for a matching visual",
  "hook": "first sentence / hook line only",
  "cta": "call to action text"
}}"""

    user = (
        f"Topic: {topic}\n"
        f"{'Brand: ' + brand_name if brand_name else ''}\n"
        f"{'Additional context: ' + extra_context if extra_context else ''}\n"
        f"Generate the {platform} post:"
    )

    ollama_system = (
        f"You are a social media content expert. Write a {platform} post about the given topic. "
        f"Keep it under {min(cfg['max_chars'], 500)} chars. "
        f"Tone: {tone}. {emoji} Include {cfg['hashtag_limit']} relevant hashtags at the end. "
        f"Language: {language}."
    )
    try:
        text = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": ollama_system},
                {"role": "user",   "content": f"Write a {platform} post about: {topic}" + (f". Brand: {brand_name}" if brand_name else "") + (f". Context: {extra_context}" if extra_context else "")},
            ],
            model=OLLAMA_MODEL,
            max_tokens=400,
            temperature=0.8,
        )
        if not text:
            raise ValueError("LLM returned empty response — Gemini may be rate-limited (429). Wait 60s and retry.")
        # Extract hashtags from text
        words = text.strip().split()
        hashtags = [w.lstrip("#") for w in words if w.startswith("#")][:cfg["hashtag_limit"]]
        post_text = text.strip()
        if len(post_text) > cfg["max_chars"]:
            post_text = post_text[: cfg["max_chars"] - 3] + "..."
        return {
            "platform":     platform,
            "post_text":    post_text,
            "hashtags":     hashtags,
            "char_count":   len(post_text),
            "max_chars":    cfg["max_chars"],
            "within_limit": len(post_text) <= cfg["max_chars"],
            "image_prompt": f"Professional {platform} visual for: {topic}",
            "hook":         post_text.split("\n")[0][:100] if post_text else "",
            "cta":          "Follow for more insights.",
            "topic":        topic,
            "language":     language,
            "model":        f"ollama/{OLLAMA_MODEL}",
        }
    except Exception as e:
        logger.error("Social post generation failed (%s): %s", platform, e)
        return {"error": f"Content generation failed: {e}", "platform": platform}


# ── DALL-E 3 image generation ─────────────────────────────────────────────────

async def generate_social_image(
    prompt:    str,
    platform:  str = "linkedin",
    size:      str = "1024x1024",   # 1024x1024 | 1792x1024 | 1024x1792
    quality:   str = "standard",
    style:     str = "vivid",
) -> dict:
    """
    Generate a social media visual using DALL-E 3.
    Downloads the image and returns base64.
    """
    # Platform-optimal sizes
    size_map = {
        "twitter":   "1792x1024",   # 16:9 landscape
        "linkedin":  "1792x1024",   # 1200x627 aspect
        "instagram": "1024x1024",   # square
    }
    size = size_map.get(platform, size)

    try:
        key = settings.openai_api_key
        if not (key and key.startswith("sk-")):
            raise RuntimeError("OpenAI key not configured")
        from openai import AsyncOpenAI
        import httpx
        import base64

        client = AsyncOpenAI(api_key=key)

        # Enhance prompt for social media
        enhanced = (
            f"{prompt}. Professional quality, suitable for {platform} marketing. "
            f"Clean composition, brand-appropriate colors, modern design aesthetic."
        )

        resp = await client.images.generate(
            model="dall-e-3",
            prompt=enhanced[:1000],
            size=size,
            quality=quality,
            style=style,
            n=1,
        )
        image_url = resp.data[0].url

        # Download image
        async with httpx.AsyncClient(timeout=30.0) as http:
            img_resp = await http.get(image_url)
            img_resp.raise_for_status()
            img_bytes = img_resp.content

        return {
            "platform":    platform,
            "size":        size,
            "image_b64":   base64.b64encode(img_bytes).decode(),
            "image_url":   image_url,
            "revised_prompt": getattr(resp.data[0], "revised_prompt", enhanced),
        }
    except Exception as e:
        logger.warning("Social image generation not available: %s", type(e).__name__)
        return {
            "error":    "Image generation requires OpenAI DALL-E (not available in Ollama mode).",
            "platform": platform,
            "prompt":   prompt,
        }


# ── LinkedIn posting ──────────────────────────────────────────────────────────

async def post_to_linkedin(
    access_token: str,
    post_text:    str,
    image_b64:    Optional[str] = None,
) -> dict:
    """
    Post to LinkedIn via LinkedIn API v2.
    Supports text posts and image posts (single image).
    """
    import httpx

    linkedin_urn = settings.linkedin_author_urn
    if not linkedin_urn:
        return {
            "status": "mock",
            "note":   "Configure LINKEDIN_AUTHOR_URN (urn:li:person:xxxx) to post.",
            "text":   post_text[:100],
        }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type":  "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    payload: dict = {
        "author":     linkedin_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": post_text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                "https://api.linkedin.com/v2/ugcPosts",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            post_id = resp.headers.get("x-restli-id", "")
        return {
            "status":  "posted",
            "post_id": post_id,
            "platform": "linkedin",
        }
    except Exception as e:
        logger.error("LinkedIn post failed: %s", e)
        return {"error": "LinkedIn posting failed.", "detail": type(e).__name__}


# ── Twitter/X posting ─────────────────────────────────────────────────────────

async def post_to_twitter(tweet_text: str, image_b64: Optional[str] = None) -> dict:
    """
    Post to Twitter/X via Twitter API v2 (Tweepy).
    Supports text tweets. Images require media upload (v1.1).
    """
    bearer_token        = settings.twitter_bearer_token
    consumer_key        = settings.twitter_api_key
    consumer_secret     = settings.twitter_api_secret
    access_token        = settings.twitter_access_token
    access_token_secret = settings.twitter_access_token_secret

    if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
        return {
            "status": "mock",
            "note":   "Configure TWITTER_API_KEY/SECRET/ACCESS_TOKEN/SECRET to post.",
            "text":   tweet_text[:50],
        }

    try:
        import tweepy
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        def _post():
            auth   = tweepy.OAuthHandler(consumer_key, consumer_secret)
            auth.set_access_token(access_token, access_token_secret)
            client = tweepy.Client(
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                access_token=access_token,
                access_token_secret=access_token_secret,
            )
            resp = client.create_tweet(text=tweet_text[:280])
            return {"tweet_id": resp.data["id"], "text": resp.data["text"]}

        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=1) as pool:
            result = await loop.run_in_executor(pool, _post)

        return {"status": "posted", "platform": "twitter", **result}
    except Exception as e:
        logger.error("Twitter post failed: %s", e)
        return {"error": "Twitter posting failed.", "detail": type(e).__name__}


# ── Buffer API scheduling ─────────────────────────────────────────────────────

async def schedule_via_buffer(
    post_text:      str,
    platforms:      list[str],
    scheduled_at:   Optional[str] = None,   # ISO datetime string
    image_url:      Optional[str] = None,
) -> dict:
    """
    Schedule a post across multiple platforms via Buffer API.
    Returns Buffer update IDs.
    """
    buffer_token = settings.buffer_access_token
    if not buffer_token:
        return {
            "status": "mock",
            "platforms": platforms,
            "note": "Configure BUFFER_ACCESS_TOKEN to use Buffer scheduling.",
            "scheduled_at": scheduled_at,
        }

    try:
        import httpx
        headers = {"Authorization": f"Bearer {buffer_token}"}

        # Get profile IDs for requested platforms
        async with httpx.AsyncClient(timeout=15.0) as client:
            profiles_resp = await client.get(
                "https://api.bufferapp.com/1/profiles.json",
                headers=headers,
            )
            profiles_resp.raise_for_status()
            all_profiles = profiles_resp.json()

        matched_profiles = [
            p["id"] for p in all_profiles
            if p.get("service") in platforms
        ]

        if not matched_profiles:
            return {"error": "No Buffer profiles found for requested platforms."}

        # Create Buffer update
        form_data: dict = {
            "text":       post_text,
            "profile_ids[]": matched_profiles,
        }
        if scheduled_at:
            dt = datetime.fromisoformat(scheduled_at.replace("Z", "+00:00"))
            form_data["scheduled_at"] = str(int(dt.timestamp()))
            form_data["now"]          = "false"
        else:
            form_data["now"] = "true"

        if image_url:
            form_data["media[link]"]       = image_url
            form_data["media[picture]"]    = image_url

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.bufferapp.com/1/updates/create.json",
                headers=headers,
                data=form_data,
            )
            resp.raise_for_status()
            data = resp.json()

        return {
            "status":     "scheduled",
            "buffer_ids": [u.get("id") for u in data.get("updates", [])],
            "platforms":  platforms,
            "scheduled_at": scheduled_at or "immediate",
        }
    except Exception as e:
        logger.error("Buffer scheduling failed: %s", e)
        return {"error": "Buffer scheduling failed.", "detail": type(e).__name__}


# ── Hashtag research ──────────────────────────────────────────────────────────

async def research_hashtags(
    topic:    str,
    platform: str = "instagram",
    count:    int = 15,
) -> list[str]:
    """Generate optimized hashtags for a topic and platform using Ollama."""
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL

    limit = _PLATFORM_CONFIG.get(platform, {}).get("hashtag_limit", 10)
    count = min(count, limit)

    try:
        text = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": f"List {count} relevant hashtags for {platform} about the topic. Output ONLY hashtags like: #tag1 #tag2 #tag3. No other text."},
                {"role": "user",   "content": f"Topic: {topic}"},
            ],
            model=OLLAMA_MODEL,
            max_tokens=100,
            temperature=0.5,
        )
        if text:
            words = text.strip().split()
            tags = [w.lstrip("#").rstrip(".,;") for w in words if w.startswith("#")][:count]
            if tags:
                return tags
    except Exception as e:
        logger.debug("Hashtag Ollama failed: %s", e)

    # Return static hashtags based on topic as last resort
    topic_slug = topic.lower().replace(" ", "")
    return [topic_slug, "AI", "technology", "innovation", "digital",
            "future", "tech", "automation", "MachineLearning", "artificialintelligence"][:count]


# ── Content calendar ──────────────────────────────────────────────────────────

async def plan_content_calendar(
    brand_name:   str,
    industry:     str,
    platforms:    list[str],
    days:         int = 7,
    post_per_day: int = 1,
    language:     str = "en",
) -> list[dict]:
    """Generate a content calendar plan for the next N days (Ollama-first)."""
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL
    import json

    system = (
        f"You are an expert social media content strategist for {industry}. "
        f"Create a {days}-day content calendar for {brand_name}. "
        f"Platforms: {', '.join(platforms)}. {post_per_day} post(s) per day. "
        f"Language: {language}. "
        f"Return JSON array of daily plans: "
        f"[{{\"day\": 1, \"date\": \"Mon Dec 2\", \"topic\": \"...\", "
        f"\"post_type\": \"educational|promotional|engagement|story\", "
        f"\"platforms\": [...], \"brief\": \"2-3 sentence content brief\"}}]"
        f"\nReturn ONLY the JSON array, no other text."
    )

    try:
        raw = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": f"Create {days}-day calendar starting from tomorrow."},
            ],
            model=OLLAMA_MODEL,
            max_tokens=1000,
        )
        raw = raw.strip()
        # Extract JSON array from response
        if "[" in raw:
            raw = raw[raw.index("["):]
            if "]" in raw:
                raw = raw[:raw.rindex("]") + 1]
        calendar = json.loads(raw)
        if isinstance(calendar, dict):
            calendar = calendar.get("calendar", calendar.get("days", []))
        return calendar[:days]
    except Exception as e:
        logger.error("Content calendar generation failed: %s", e)
        # Return structured mock calendar
        from datetime import datetime, timezone, timedelta
        result = []
        types = ["educational", "promotional", "engagement", "story"]
        base = datetime.now(timezone.utc)
        for i in range(min(days, 7)):
            day_dt = base + timedelta(days=i + 1)
            result.append({
                "day": i + 1,
                "date": day_dt.strftime("%a %b %d"),
                "topic": f"{brand_name} — {industry} Insight #{i+1}",
                "post_type": types[i % len(types)],
                "platforms": platforms,
                "brief": f"Share insights about {industry} with your {brand_name} audience.",
            })
        return result


# ── Content repurposing engine ────────────────────────────────────────────────

async def repurpose_content(
    source_content: str,
    content_type:   str = "blog",   # blog | article | podcast | video
    brand_name:     str = "",
    tone:           str = "professional",
    language:       str = "en",
) -> dict:
    """One piece of content → 6 platform-ready formats."""
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL

    system = (
        f"You are a content repurposing expert. Transform the given {content_type} into "
        f"6 platform-ready formats. Brand: {brand_name or 'the brand'}. Tone: {tone}. Language: {language}.\n"
        "Return a JSON object with keys: linkedin_post, twitter_thread (3 tweets as array), "
        "instagram_caption, email_subject_and_preview, youtube_description, key_quotes (3 quotes as array)."
    )
    try:
        raw = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": f"Repurpose this {content_type}:\n\n{source_content[:2000]}"},
            ],
            model=OLLAMA_MODEL,
            max_tokens=1200,
            temperature=0.7,
        )
        import json, re
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return {"action": "repurpose", "formats": json.loads(match.group())}
        # Fallback: return raw split into sections
        return {"action": "repurpose", "formats": {"raw_output": raw}}
    except Exception as e:
        logger.error("Content repurposing failed: %s", e)
        return {"error": "Content repurposing failed.", "detail": str(e)}


# ── Competitor social audit ───────────────────────────────────────────────────

async def competitor_social_audit(
    competitor_name:  str,
    competitor_niche: str,
    our_brand:        str = "",
    platforms:        list[str] | None = None,
) -> dict:
    """Analyze competitor's social strategy and identify gaps we can exploit."""
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL

    plats = ", ".join(platforms or ["LinkedIn", "Twitter", "Instagram"])
    system = (
        "You are a competitive intelligence analyst specializing in social media strategy. "
        "Analyze the competitor and provide actionable intelligence."
    )
    prompt = (
        f"Competitor: {competitor_name} | Niche: {competitor_niche} | Platforms: {plats}\n"
        f"Our brand: {our_brand or 'us'}\n\n"
        "Provide a structured competitor social media audit covering:\n"
        "1. Estimated posting frequency per platform\n"
        "2. Top content types they likely use (educational/promotional/UGC/thought leadership)\n"
        "3. Tone and messaging style\n"
        "4. Hashtag strategy\n"
        "5. Engagement tactics (polls, carousels, threads)\n"
        "6. Gaps and weaknesses we can exploit\n"
        "7. Content angles they are NOT covering (our opportunity)\n"
        "8. Recommended counter-strategy for us (5 specific actions)"
    )
    try:
        result = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
            model=OLLAMA_MODEL,
            max_tokens=900,
            temperature=0.6,
        )
        return {"action": "competitor_audit", "competitor": competitor_name, "audit": result}
    except Exception as e:
        logger.error("Competitor audit failed: %s", e)
        return {"error": "Competitor audit failed.", "detail": str(e)}


# ── Ad copy generator ─────────────────────────────────────────────────────────

async def generate_ad_copy(
    product:      str,
    audience:     str,
    goal:         str,       # awareness | clicks | leads | conversions
    platform:     str,       # meta | google | linkedin | youtube
    budget_range: str = "",
    usp:          str = "",
    language:     str = "en",
) -> dict:
    """Generate platform-specific ad copy with headlines, descriptions, and CTAs."""
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL

    char_limits = {
        "meta":     {"headline": 40, "desc": 125, "cta_options": ["Learn More","Shop Now","Sign Up","Get Quote","Book Now"]},
        "google":   {"headline": 30, "desc": 90,  "cta_options": ["Learn More","Get Started","Contact Us","Buy Now","Get Quote"]},
        "linkedin": {"headline": 70, "desc": 150, "cta_options": ["Learn More","Sign Up","Register","Download","Request Demo"]},
        "youtube":  {"headline": 100,"desc": 200, "cta_options": ["Watch Now","Learn More","Sign Up","Get Started"]},
    }
    limits = char_limits.get(platform, char_limits["meta"])

    system = "You are a performance marketing expert specializing in paid social and search advertising."
    prompt = (
        f"Platform: {platform.upper()} | Goal: {goal} | Language: {language}\n"
        f"Product/Service: {product}\n"
        f"Target Audience: {audience}\n"
        f"Unique Selling Point: {usp or 'best in class'}\n"
        f"Budget range: {budget_range or 'not specified'}\n\n"
        f"Generate ad copy with:\n"
        f"- 3 headline variations (max {limits['headline']} chars each)\n"
        f"- 2 description variations (max {limits['desc']} chars each)\n"
        f"- Recommended CTA from: {limits['cta_options']}\n"
        f"- 1 hook variation for A/B testing\n"
        f"- Targeting suggestions for this platform\n"
        f"- Estimated CTR benchmark for this goal on {platform}"
    )
    try:
        result = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
            model=OLLAMA_MODEL,
            max_tokens=800,
            temperature=0.8,
        )
        return {"action": "ad_copy", "platform": platform, "goal": goal, "copy": result}
    except Exception as e:
        logger.error("Ad copy generation failed: %s", e)
        return {"error": "Ad copy generation failed.", "detail": str(e)}


# ── Influencer brief generator ────────────────────────────────────────────────

async def generate_influencer_brief(
    brand_name:       str,
    product:          str,
    campaign_goal:    str,
    influencer_niche: str,
    deliverables:     str,
    budget:           str = "",
    timeline:         str = "",
    dos_donts:        str = "",
) -> dict:
    """Generate a complete influencer campaign brief."""
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL

    system = "You are a brand partnerships manager who creates clear, comprehensive influencer briefs that drive authentic content and measurable results."
    prompt = (
        f"Brand: {brand_name} | Product: {product}\n"
        f"Campaign goal: {campaign_goal}\n"
        f"Influencer niche: {influencer_niche}\n"
        f"Deliverables required: {deliverables}\n"
        f"Budget: {budget or 'to be discussed'}\n"
        f"Timeline: {timeline or 'to be discussed'}\n"
        f"Brand dos/don'ts: {dos_donts or 'none specified'}\n\n"
        "Create a complete influencer campaign brief including:\n"
        "1. Campaign overview and objectives\n"
        "2. Brand voice and messaging guidelines\n"
        "3. Content requirements per deliverable (format, length, key messages)\n"
        "4. Mandatory inclusions (hashtags, @mentions, disclosure)\n"
        "5. What NOT to do (brand safety rules)\n"
        "6. Approval process and revision policy\n"
        "7. Payment terms and milestone schedule\n"
        "8. KPIs and reporting requirements\n"
        "9. Usage rights and exclusivity terms"
    )
    try:
        result = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
            model=OLLAMA_MODEL,
            max_tokens=900,
            temperature=0.6,
        )
        return {"action": "influencer_brief", "brand": brand_name, "brief": result}
    except Exception as e:
        logger.error("Influencer brief generation failed: %s", e)
        return {"error": "Influencer brief generation failed.", "detail": str(e)}


# ── Crisis response handler ───────────────────────────────────────────────────

async def generate_crisis_response(
    brand_name:    str,
    crisis_type:   str,   # negative_review | viral_complaint | product_issue | pr_controversy | data_breach
    crisis_detail: str,
    platform:      str = "all",
    severity:      str = "medium",  # low | medium | high | critical
) -> dict:
    """Draft calm, professional brand crisis response for different severity levels."""
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL

    system = (
        "You are a PR crisis communications expert. You draft measured, empathetic, "
        "legally safe responses that de-escalate situations and protect brand reputation."
    )
    prompt = (
        f"Brand: {brand_name} | Crisis type: {crisis_type} | Severity: {severity}\n"
        f"Platform: {platform}\n"
        f"Crisis details: {crisis_detail}\n\n"
        "Generate a crisis response package:\n"
        "1. Immediate holding statement (post within 1 hour) — 2 sentences max\n"
        "2. Full public response for social media (empathetic, non-defensive)\n"
        "3. Direct reply to the original complainant/post\n"
        "4. Internal team communication template\n"
        "5. Follow-up post (24-48 hours later) — resolution/update\n"
        "6. What NOT to say (legal and PR red flags to avoid)\n"
        "7. Monitoring keywords to track sentiment\n"
        "8. Escalation recommendation (handle internally / involve legal / issue press release)"
    )
    try:
        result = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
            model=OLLAMA_MODEL,
            max_tokens=900,
            temperature=0.4,
        )
        return {"action": "crisis_response", "severity": severity, "crisis_type": crisis_type, "response": result}
    except Exception as e:
        logger.error("Crisis response generation failed: %s", e)
        return {"error": "Crisis response generation failed.", "detail": str(e)}


# ── YouTube script writer ─────────────────────────────────────────────────────

async def generate_youtube_script(
    topic:       str,
    channel_niche: str,
    duration_min: int = 8,
    style:       str = "educational",  # educational | vlog | review | tutorial | shorts
    brand_name:  str = "",
    cta:         str = "",
    language:    str = "en",
) -> dict:
    """Generate a structured YouTube video script with timestamps."""
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL

    system = (
        f"You are a YouTube content strategist and scriptwriter. "
        f"Write scripts that hook viewers in the first 30 seconds and retain them till the end. "
        f"Language: {language}."
    )
    prompt = (
        f"Topic: {topic} | Niche: {channel_niche} | Duration: ~{duration_min} minutes\n"
        f"Style: {style} | Brand: {brand_name or 'the channel'}\n"
        f"CTA goal: {cta or 'subscribe and like'}\n\n"
        "Write a complete YouTube script with:\n"
        "1. HOOK (0:00-0:30) — pattern interrupt, bold claim, or compelling question\n"
        "2. INTRO (0:30-1:00) — who you are, what they'll learn, why it matters\n"
        "3. CHAPTER BREAKDOWN with timestamps and key talking points per section\n"
        "4. FULL SCRIPT for each chapter (conversational, not formal)\n"
        "5. B-ROLL suggestions for each section\n"
        "6. CTA integration (mid-roll at 40% mark + end screen)\n"
        "7. END SCREEN script (30 seconds)\n"
        "8. SEO: title options (3), description (500 chars), tags (15), thumbnail text"
    )
    try:
        result = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
            model=OLLAMA_MODEL,
            max_tokens=1400,
            temperature=0.7,
        )
        return {"action": "youtube_script", "topic": topic, "duration_min": duration_min, "script": result}
    except Exception as e:
        logger.error("YouTube script generation failed: %s", e)
        return {"error": "YouTube script generation failed.", "detail": str(e)}


# ── Email campaign sequence generator ────────────────────────────────────────

async def generate_email_sequence(
    sequence_type: str,   # welcome | drip | re_engagement | product_launch | nurture
    product:       str,
    audience:      str,
    num_emails:    int = 5,
    brand_name:    str = "",
    tone:          str = "friendly",
    language:      str = "en",
) -> dict:
    """Generate a multi-email campaign sequence with subject lines and body copy."""
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL

    system = (
        f"You are an email marketing specialist with expertise in lifecycle campaigns. "
        f"Write high-converting email sequences. Language: {language}. Tone: {tone}."
    )
    prompt = (
        f"Sequence type: {sequence_type} | Emails: {num_emails}\n"
        f"Product/Service: {product}\n"
        f"Audience: {audience}\n"
        f"Brand: {brand_name or 'the company'}\n\n"
        f"Generate a {num_emails}-email {sequence_type} sequence. For each email provide:\n"
        "- Email number and send timing (e.g., Day 1, Day 3, Day 7)\n"
        "- Subject line (A and B variant)\n"
        "- Preview text (90 chars max)\n"
        "- Full email body (HTML-ready structure with sections)\n"
        "- Primary CTA with button text\n"
        "- Key goal of this email in the sequence\n"
        "- Personalization tokens to use\n"
        "Separate each email with '---EMAIL N---'"
    )
    try:
        result = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
            model=OLLAMA_MODEL,
            max_tokens=1600,
            temperature=0.7,
        )
        return {"action": "email_sequence", "sequence_type": sequence_type, "num_emails": num_emails, "sequence": result}
    except Exception as e:
        logger.error("Email sequence generation failed: %s", e)
        return {"error": "Email sequence generation failed.", "detail": str(e)}


# ── Reel / Short video script ─────────────────────────────────────────────────

async def generate_reel_script(
    topic:      str,
    duration:   int = 30,   # 15 | 30 | 60 seconds
    platform:   str = "instagram",  # instagram | youtube_shorts | tiktok
    hook_style: str = "question",   # question | stat | bold_claim | story | listicle
    brand_name: str = "",
    language:   str = "en",
) -> dict:
    """Generate a punchy reel/short video script with visual direction notes."""
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL

    system = (
        f"You are a short-form video content creator. Write scripts that stop the scroll "
        f"in the first 2 seconds and deliver value before the viewer swipes away. Language: {language}."
    )
    prompt = (
        f"Platform: {platform} | Duration: {duration} seconds | Hook style: {hook_style}\n"
        f"Topic: {topic} | Brand: {brand_name or 'the creator'}\n\n"
        f"Write a {duration}-second {platform} script:\n"
        "FORMAT (use this structure):\n"
        "[0-3s] HOOK — Text on screen + spoken hook (stop-scroll moment)\n"
        "[3-Xs] BODY — Main content in punchy segments with visual direction\n"
        f"[{duration-5}-{duration}s] CTA — What to do next (follow/save/comment/link in bio)\n\n"
        "Also provide:\n"
        "- On-screen text overlays for each segment\n"
        "- Music/sound recommendation (vibe, not specific song)\n"
        "- Transition style between segments\n"
        "- Caption copy (first line is the hook, hashtags at end)\n"
        "- 3 thumbnail/cover frame options"
    )
    try:
        result = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
            model=OLLAMA_MODEL,
            max_tokens=700,
            temperature=0.8,
        )
        return {"action": "reel_script", "platform": platform, "duration": duration, "script": result}
    except Exception as e:
        logger.error("Reel script generation failed: %s", e)
        return {"error": "Reel script generation failed.", "detail": str(e)}


# ── Monthly performance report narrator ──────────────────────────────────────

async def generate_monthly_report(
    brand_name:  str,
    month:       str,
    metrics:     dict,  # {platform: {followers, posts, reach, engagement_rate, top_post}}
    goals:       str = "",
    language:    str = "en",
) -> dict:
    """Turn raw social media metrics into a written narrative report."""
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL
    import json

    system = (
        "You are a social media analyst. Transform raw metrics into a clear, insightful "
        f"monthly performance report. Language: {language}."
    )
    metrics_text = json.dumps(metrics, indent=2)
    prompt = (
        f"Brand: {brand_name} | Month: {month}\n"
        f"Goals set: {goals or 'not specified'}\n"
        f"Metrics:\n{metrics_text}\n\n"
        "Write a monthly social media performance report with:\n"
        "1. Executive Summary (3 bullets — what went well, what didn't, key number)\n"
        "2. Platform-by-platform breakdown with narrative (not just numbers)\n"
        "3. Top performing content analysis — why it worked\n"
        "4. Audience growth analysis — quality vs quantity\n"
        "5. Engagement rate interpretation — is it good/bad for the niche?\n"
        "6. Goals vs actuals — hit/miss analysis\n"
        "7. Insights and learnings (3 actionable takeaways)\n"
        "8. Recommendations for next month (5 specific actions)\n"
        "9. Next month targets (suggested based on trend)"
    )
    try:
        result = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
            model=OLLAMA_MODEL,
            max_tokens=1000,
            temperature=0.5,
        )
        return {"action": "monthly_report", "brand": brand_name, "month": month, "report": result}
    except Exception as e:
        logger.error("Monthly report generation failed: %s", e)
        return {"error": "Monthly report generation failed.", "detail": str(e)}


# ── SEO keyword cluster builder ───────────────────────────────────────────────

async def build_keyword_cluster(
    main_topic:  str,
    industry:    str,
    audience:    str,
    language:    str = "en",
    market:      str = "India",
) -> dict:
    """Build a full SEO topic cluster — pillar page + supporting articles + keyword intent mapping."""
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL

    system = (
        f"You are an SEO strategist specializing in topic clustering and content architecture. "
        f"Market: {market}. Language: {language}."
    )
    prompt = (
        f"Main topic: {main_topic}\n"
        f"Industry: {industry}\n"
        f"Target audience: {audience}\n\n"
        "Build a complete SEO topic cluster:\n"
        "1. PILLAR PAGE — main keyword, title, meta description, content outline (H2s)\n"
        "2. CLUSTER ARTICLES (8) — each with:\n"
        "   - Title\n"
        "   - Primary keyword + 3 secondary keywords\n"
        "   - Search intent (informational/commercial/transactional/navigational)\n"
        "   - Estimated monthly searches (low/medium/high/very high)\n"
        "   - Content brief (what to cover, what angle)\n"
        "   - Internal link suggestion (links to pillar + other cluster articles)\n"
        "3. KEYWORD INTENT MAP — group all keywords by funnel stage (TOFU/MOFU/BOFU)\n"
        "4. CONTENT CALENDAR — recommended publish order for maximum SEO impact\n"
        "5. FEATURED SNIPPET opportunities in this cluster"
    )
    try:
        result = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
            model=OLLAMA_MODEL,
            max_tokens=1200,
            temperature=0.5,
        )
        return {"action": "keyword_cluster", "main_topic": main_topic, "cluster": result}
    except Exception as e:
        logger.error("Keyword cluster generation failed: %s", e)
        return {"error": "Keyword cluster generation failed.", "detail": str(e)}


# ── Best time to post suggester ──────────────────────────────────────────────

async def suggest_best_post_time(
    platform:  str,
    industry:  str,
    audience:  str = "",
    timezone:  str = "IST",
) -> dict:
    """Suggest optimal posting times based on platform + industry + Indian audience patterns."""
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL

    system = "You are a social media analytics expert specializing in Indian B2B and B2C markets."
    prompt = (
        f"Platform: {platform} | Industry: {industry} | Audience: {audience or 'general'} | Timezone: {timezone}\n\n"
        "Provide optimal posting times for India:\n"
        "1. Top 3 best days of the week (ranked) with reason\n"
        "2. Top 3 best time slots per day with engagement data\n"
        "3. Times to AVOID and why\n"
        "4. Platform-specific notes (LinkedIn morning commute, Instagram evening, Twitter real-time)\n"
        "5. Festival/event calendar impact (IPL season, Diwali, Budget day)\n"
        "6. Frequency recommendation (posts per week) for this industry\n"
        "7. Quick posting schedule template: Mon-Sun with time slots"
    )
    try:
        result = await ollama_chat_completion(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            model=OLLAMA_MODEL, max_tokens=700, temperature=0.4,
        )
        return {"action": "best_post_time", "platform": platform, "industry": industry, "schedule": result}
    except Exception as e:
        logger.error("Best post time failed: %s", e)
        return {"error": "Best post time suggestion failed.", "detail": str(e)}


# ── Engagement rate benchmarker ───────────────────────────────────────────────

async def benchmark_engagement_rate(
    platform:        str,
    industry:        str,
    your_rate:       float,
    followers:       int = 0,
    content_type:    str = "mixed",
) -> dict:
    """Compare your engagement rate to industry benchmarks and give improvement plan."""
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL

    system = "You are a social media analyst with deep knowledge of industry engagement benchmarks."
    prompt = (
        f"Platform: {platform} | Industry: {industry}\n"
        f"Your engagement rate: {your_rate}% | Followers: {followers or 'not specified'} | Content mix: {content_type}\n\n"
        "Provide benchmark analysis:\n"
        "1. Industry average engagement rate for this platform\n"
        "2. Your rating: BELOW AVERAGE / AVERAGE / GOOD / EXCELLENT (with percentile)\n"
        "3. What's dragging your rate down (common culprits for this industry)\n"
        "4. Top 5 tactics to improve engagement rate in 30 days\n"
        "5. Engagement rate targets: 30-day goal, 90-day goal\n"
        "6. Content type that drives highest engagement in your industry\n"
        "7. India-specific engagement patterns vs global benchmarks"
    )
    try:
        result = await ollama_chat_completion(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            model=OLLAMA_MODEL, max_tokens=700, temperature=0.4,
        )
        return {"action": "benchmark_engagement", "platform": platform, "your_rate": your_rate, "analysis": result}
    except Exception as e:
        logger.error("Engagement benchmark failed: %s", e)
        return {"error": "Engagement benchmark failed.", "detail": str(e)}


# ── Content performance score ─────────────────────────────────────────────────

async def score_content_performance(
    post_text:      str,
    platform:       str,
    industry:       str = "",
    audience:       str = "",
) -> dict:
    """Predict if a post will perform well before posting — score 0-100 with improvement tips."""
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL

    system = "You are a social media performance analyst. You predict post engagement before it's published."
    prompt = (
        f"Platform: {platform} | Industry: {industry} | Audience: {audience}\n\n"
        f"POST TEXT:\n{post_text[:1000]}\n\n"
        "Score this post (0-100) across:\n"
        "1. HOOK STRENGTH (0-20): Does it stop the scroll in first line?\n"
        "2. VALUE DENSITY (0-20): How much actionable value is packed in?\n"
        "3. PLATFORM FIT (0-20): Format, length, tone match for this platform?\n"
        "4. ENGAGEMENT TRIGGERS (0-20): Questions, polls, CTAs, controversy?\n"
        "5. SHAREABILITY (0-20): Will people share/save this?\n\n"
        "Then:\n"
        "- TOTAL SCORE: X/100\n"
        "- VERDICT: (Won't perform / Below average / Good / Will go viral)\n"
        "- TOP 3 FIXES: Specific edits to improve score by 20+ points\n"
        "- REWRITTEN HOOK: Stronger opening line"
    )
    try:
        result = await ollama_chat_completion(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            model=OLLAMA_MODEL, max_tokens=600, temperature=0.4,
        )
        return {"action": "performance_score", "platform": platform, "analysis": result}
    except Exception as e:
        logger.error("Performance score failed: %s", e)
        return {"error": "Performance scoring failed.", "detail": str(e)}


# ── India trending topics feed ────────────────────────────────────────────────

async def generate_india_trends(
    industry:  str,
    language:  str = "en",
    month:     str = "",
) -> dict:
    """Generate India-specific trending content ideas — festivals, news, events, seasons."""
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL
    from datetime import datetime, timezone
    current_month = month or datetime.now(timezone.utc).strftime("%B %Y")

    system = "You are an India-focused content strategist. You create culturally relevant content tied to Indian events, festivals, and trends."
    prompt = (
        f"Industry: {industry} | Month: {current_month} | Language: {language}\n\n"
        "Generate India-specific trending content opportunities:\n"
        "1. CURRENT FESTIVALS & EVENTS (this month) — content angles for each\n"
        "2. INDIA BUSINESS CALENDAR — tax deadlines, regulatory dates, budget season relevant to industry\n"
        "3. SEASONAL TRENDS — what Indian audiences are searching/discussing right now\n"
        "4. CRICKET/SPORTS tie-ins if relevant to industry\n"
        "5. TRENDING TOPICS on Indian Twitter/LinkedIn this month\n"
        "6. 10 READY POST IDEAS — one-line brief for each, tied to a current trend\n"
        "7. BEST REGIONAL ANGLE — which state/city audience to target this month\n"
        "8. VIRAL FORMAT for Indian audience this month (meme trend, challenge, format)"
    )
    try:
        result = await ollama_chat_completion(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            model=OLLAMA_MODEL, max_tokens=900, temperature=0.6,
        )
        return {"action": "india_trends", "industry": industry, "month": current_month, "trends": result}
    except Exception as e:
        logger.error("India trends failed: %s", e)
        return {"error": "India trends generation failed.", "detail": str(e)}


# ── Regional language post generator ─────────────────────────────────────────

async def generate_regional_post(
    topic:            str,
    regional_language: str,   # tamil | hindi | telugu | kannada | malayalam | marathi
    platform:         str = "instagram",
    brand_name:       str = "",
    tone:             str = "professional",
) -> dict:
    """Generate social media post in Tamil, Hindi, or other Indian regional languages."""
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL

    lang_map = {
        "tamil":     "Tamil (தமிழ்)",
        "hindi":     "Hindi (हिन्दी)",
        "telugu":    "Telugu (తెలుగు)",
        "kannada":   "Kannada (ಕನ್ನಡ)",
        "malayalam": "Malayalam (മലയാളം)",
        "marathi":   "Marathi (मराठी)",
        "bengali":   "Bengali (বাংলা)",
    }
    lang_full = lang_map.get(regional_language.lower(), regional_language)
    cfg = _PLATFORM_CONFIG.get(platform, _PLATFORM_CONFIG["linkedin"])

    system = (
        f"You are a social media content expert who writes authentic, engaging content in {lang_full}. "
        f"Write in natural, colloquial {lang_full} that resonates with local audiences — not a direct translation. "
        f"Tone: {tone}."
    )
    prompt = (
        f"Platform: {platform} | Brand: {brand_name or 'the brand'}\n"
        f"Topic: {topic}\n\n"
        f"Write a {platform} post in {lang_full}:\n"
        f"1. POST TEXT in {lang_full} (max {min(cfg['max_chars'], 500)} chars)\n"
        f"2. HASHTAGS — mix of {lang_full} hashtags + English hashtags (max {cfg['hashtag_limit']})\n"
        f"3. TRANSLITERATION — Roman script version of the post for team review\n"
        f"4. ENGLISH TRANSLATION — so non-speakers can understand\n"
        f"5. CULTURAL NOTE — any idiom or reference used and why it works"
    )
    try:
        result = await ollama_chat_completion(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            model=OLLAMA_MODEL, max_tokens=600, temperature=0.7,
        )
        return {"action": "regional_post", "language": regional_language, "platform": platform, "post": result}
    except Exception as e:
        logger.error("Regional post failed: %s", e)
        return {"error": "Regional post generation failed.", "detail": str(e)}


# ── WhatsApp Business content generator ──────────────────────────────────────

async def generate_whatsapp_content(
    content_type: str,   # status | broadcast | catalogue | story | announcement
    topic:        str,
    brand_name:   str = "",
    language:     str = "en",
    audience:     str = "",
) -> dict:
    """Generate WhatsApp Business content — status, broadcast messages, catalogue copy."""
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL

    content_specs = {
        "status":       "WhatsApp Status (30 seconds max, very visual, single message, personal tone)",
        "broadcast":    "WhatsApp Broadcast message (max 1024 chars, one-to-many, feels personal, clear CTA)",
        "catalogue":    "WhatsApp Business Catalogue item (product name, description 500 chars max, clear price/offer)",
        "story":        "WhatsApp Story (24hr disappearing, attention-grabbing, visual description)",
        "announcement": "WhatsApp Channel announcement (factual, concise, shareable, with emoji for scannability)",
    }
    spec = content_specs.get(content_type, content_specs["broadcast"])

    system = (
        "You are a WhatsApp Business marketing expert. WhatsApp requires a different style than other platforms — "
        "it's personal, direct, conversational, and highly visual in text since no algorithm ranking exists. "
        "Messages that feel like they came from a friend (not a brand) perform best."
    )
    prompt = (
        f"Content type: {spec}\n"
        f"Topic/Offer: {topic}\n"
        f"Brand: {brand_name or 'the business'} | Language: {language} | Audience: {audience or 'customers'}\n\n"
        "Generate complete WhatsApp Business content:\n"
        "1. MAIN MESSAGE — ready to copy-paste\n"
        "2. HINDI VERSION (if language is en) — most WhatsApp users prefer Hindi in India\n"
        "3. WITH EMOJIS VERSION — emoji-heavy variant for casual audiences\n"
        "4. FORMAL VERSION — for professional services (CA/legal/clinic)\n"
        "5. QUICK REPLY BUTTONS — 3 suggested button labels\n"
        "6. FOLLOW-UP MESSAGE — if no response in 24 hours"
    )
    try:
        result = await ollama_chat_completion(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            model=OLLAMA_MODEL, max_tokens=700, temperature=0.7,
        )
        return {"action": "whatsapp_content", "content_type": content_type, "content": result}
    except Exception as e:
        logger.error("WhatsApp content failed: %s", e)
        return {"error": "WhatsApp content generation failed.", "detail": str(e)}


# ── Niche templates (CA / Legal / Clinic) ────────────────────────────────────

async def generate_niche_templates(
    niche:      str,   # ca_firm | legal_firm | clinic | school | restaurant | real_estate
    brand_name: str = "",
    month:      str = "",
    language:   str = "en",
    platform:   str = "all",
) -> dict:
    """Industry-specific social media template packs for Indian professional services."""
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL
    from datetime import datetime, timezone
    current_month = month or datetime.now(timezone.utc).strftime("%B %Y")

    niche_context = {
        "ca_firm":      "CA (Chartered Accountant) firm in India — GST, ITR, TDS, audit, compliance deadlines, budget season",
        "legal_firm":   "Law firm / Legal services in India — consumer rights, corporate law, family law, legal awareness",
        "clinic":       "Medical clinic / hospital in India — health tips, appointment booking, seasonal health, patient education",
        "school":       "School / coaching institute in India — admissions, exam tips, parent communication, results season",
        "restaurant":   "Restaurant / food business in India — daily specials, festival menus, delivery offers, food trends",
        "real_estate":  "Real estate agency in India — property listings, home buying tips, RERA compliance, market updates",
        "salon":        "Salon / beauty parlour in India — seasonal offers, bridal packages, product launches, beauty tips",
    }
    ctx = niche_context.get(niche, f"{niche} business in India")

    system = f"You are a social media content specialist for {ctx}. Create ready-to-use, professional templates."
    prompt = (
        f"Business type: {ctx}\n"
        f"Brand: {brand_name or 'the business'} | Month: {current_month} | Language: {language}\n\n"
        "Generate a complete social media template pack (10 ready-to-post templates):\n"
        "For each template provide:\n"
        "- TYPE (Educational/Promotional/Seasonal/Engagement/Awareness)\n"
        "- POST TEXT (ready to copy-paste with [BRAND] placeholders)\n"
        "- BEST PLATFORM for this template\n"
        "- SUGGESTED IMAGE TYPE (infographic/photo/carousel/reel)\n\n"
        "Make templates specific to the current month's events/deadlines for this niche.\n"
        "Include at least 2 templates in regional language (Tamil or Hindi).\n"
        "Include WhatsApp broadcast version for 2 templates."
    )
    try:
        result = await ollama_chat_completion(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            model=OLLAMA_MODEL, max_tokens=1200, temperature=0.6,
        )
        return {"action": "niche_templates", "niche": niche, "month": current_month, "templates": result}
    except Exception as e:
        logger.error("Niche templates failed: %s", e)
        return {"error": "Niche template generation failed.", "detail": str(e)}


# ── Bulk post generator ───────────────────────────────────────────────────────

async def generate_bulk_posts(
    topics:     list[str],
    platform:   str,
    tone:       str = "professional",
    brand_name: str = "",
    language:   str = "en",
) -> dict:
    """Generate multiple posts at once from a list of topics — week/month batch."""
    import asyncio
    results = []
    tasks = [
        generate_post(t, platform, tone, True, brand_name, language)
        for t in topics[:20]
    ]
    posts = await asyncio.gather(*tasks, return_exceptions=True)
    for i, (topic, post) in enumerate(zip(topics, posts)):
        if isinstance(post, Exception):
            results.append({"topic": topic, "error": str(post)})
        else:
            results.append({"topic": topic, "index": i + 1, **post})
    return {"action": "bulk_generate", "platform": platform, "count": len(results), "posts": results}


# ── Content pillar planner ────────────────────────────────────────────────────

async def build_content_pillar_plan(
    brand_name: str,
    industry:   str,
    audience:   str,
    pillars:    list[str] | None = None,
    language:   str = "en",
) -> dict:
    """Define content pillars, allocate % of posts, and generate topic ideas per pillar."""
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL

    custom_pillars = ""
    if pillars:
        custom_pillars = f"\nThe brand has defined these pillars: {', '.join(pillars)}. Build the plan around these."

    system = "You are a content strategy director specializing in B2B and professional services content pillars."
    prompt = (
        f"Brand: {brand_name} | Industry: {industry} | Audience: {audience} | Language: {language}\n"
        f"{custom_pillars}\n\n"
        "Build a complete content pillar strategy:\n"
        "1. RECOMMENDED PILLARS (5) — name, description, % of monthly posts, why this % makes sense\n"
        "2. POST TYPE MIX per pillar (educational/promotional/engagement/UGC)\n"
        "3. 10 TOPIC IDEAS per pillar (50 total) — specific, not generic\n"
        "4. MONTHLY BALANCE CHECK — what a healthy 30-post month looks like\n"
        "5. PILLAR CALENDAR — sample week showing pillar rotation\n"
        "6. INDIA-SPECIFIC PILLAR — recommended seasonal/regional pillar for Indian SMBs\n"
        "7. PILLAR HEALTH SIGNALS — how to know if a pillar is underperforming"
    )
    try:
        result = await ollama_chat_completion(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            model=OLLAMA_MODEL, max_tokens=1100, temperature=0.5,
        )
        return {"action": "content_pillars", "brand": brand_name, "plan": result}
    except Exception as e:
        logger.error("Content pillars failed: %s", e)
        return {"error": "Content pillar planning failed.", "detail": str(e)}


# ── Brand mention monitor ─────────────────────────────────────────────────────

async def monitor_brand_mentions(
    brand_name:  str,
    industry:    str,
    competitors: list[str] | None = None,
    language:    str = "en",
) -> dict:
    """Simulate brand monitoring intelligence — mention alerts, sentiment, competitor activity."""
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL

    comp_list = ", ".join(competitors or []) or "none specified"
    system = (
        "You are a social media brand monitoring analyst. You provide actionable intelligence "
        "about brand mentions, sentiment trends, and competitor activity across platforms."
    )
    prompt = (
        f"Brand: {brand_name} | Industry: {industry} | Competitors to watch: {comp_list}\n\n"
        "Generate a brand monitoring intelligence briefing:\n"
        "1. BRAND MENTION ANALYSIS\n"
        "   - Estimated mention volume (low/medium/high) on LinkedIn, Twitter, Reddit\n"
        "   - Sentiment breakdown (positive/neutral/negative %)\n"
        "   - Top 3 topics people mention when talking about this brand\n"
        "   - Potential viral risk keywords to watch\n\n"
        "2. COMPETITOR ACTIVITY INTEL (for each competitor)\n"
        "   - Estimated posting frequency this week\n"
        "   - Content themes they're pushing\n"
        "   - Engagement level compared to norm\n"
        "   - Any apparent campaigns or pushes\n\n"
        "3. OPPORTUNITY ALERTS\n"
        "   - Trending conversations in the industry to join NOW\n"
        "   - Gaps competitors are leaving (topics they're not covering)\n"
        "   - Best content type to post in next 48 hours\n\n"
        "4. ACTION ITEMS\n"
        "   - 3 immediate actions (next 24 hours)\n"
        "   - 2 things to monitor closely\n"
        "   - Alert threshold: at what point should escalation happen"
    )
    try:
        result = await ollama_chat_completion(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            model=OLLAMA_MODEL, max_tokens=900, temperature=0.5,
        )
        return {"action": "brand_monitor", "brand": brand_name, "intelligence": result}
    except Exception as e:
        logger.error("Brand monitor failed: %s", e)
        return {"error": "Brand monitoring failed.", "detail": str(e)}


# ── Competitor post tracker ────────────────────────────────────────────────────

async def track_competitor_posts(
    competitor_name: str,
    niche:           str,
    timeframe:       str = "last_week",
    our_brand:       str = "",
) -> dict:
    """Deep-dive competitor weekly posting analysis — content pillars, hooks, engagement tactics."""
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL

    system = "You are a competitive intelligence analyst. You reverse-engineer competitor social strategies."
    prompt = (
        f"Competitor: {competitor_name} | Niche: {niche} | Timeframe: {timeframe}\n"
        f"Our brand: {our_brand or 'us'}\n\n"
        "Generate a competitor post tracking report:\n"
        "1. POSTING PATTERN\n"
        "   - Estimated posts this week per platform\n"
        "   - Peak posting days/times\n"
        "   - Content mix (% educational / promotional / engagement)\n\n"
        "2. TOP PERFORMING CONTENT (estimated)\n"
        "   - Their likely best post this week (topic + format)\n"
        "   - Hook formula they're using\n"
        "   - Engagement tactics (polls, questions, carousels, threads)\n\n"
        "3. MESSAGING & POSITIONING\n"
        "   - Core narrative they're pushing this week\n"
        "   - Keywords and phrases repeated frequently\n"
        "   - Tone shift (more aggressive? more educational?)\n\n"
        "4. GAP ANALYSIS\n"
        "   - Topics they completely ignored this week\n"
        "   - Audience questions they're not answering\n"
        "   - Format they're not using (our opportunity)\n\n"
        "5. OUR COUNTER-STRATEGY (3 specific posts to create this week)\n"
        "   - Post idea 1: Topic + format + angle\n"
        "   - Post idea 2: Topic + format + angle\n"
        "   - Post idea 3: Topic + format + angle"
    )
    try:
        result = await ollama_chat_completion(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            model=OLLAMA_MODEL, max_tokens=800, temperature=0.5,
        )
        return {"action": "competitor_tracker", "competitor": competitor_name, "report": result}
    except Exception as e:
        logger.error("Competitor tracker failed: %s", e)
        return {"error": "Competitor tracking failed.", "detail": str(e)}


# ── Cross-agent content bridge ────────────────────────────────────────────────

async def generate_cross_agent_content(
    trigger_type: str,   # crm_deal_won | hr_hire | product_launch | milestone | event | award
    event_data:   dict,
    brand_name:   str = "",
    platform:     str = "linkedin",
    tone:         str = "professional",
    language:     str = "en",
) -> dict:
    """Convert business events from other agents into social media posts automatically."""
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL

    trigger_templates = {
        "crm_deal_won":    "A sales deal was just closed. Client: {client}, Value: {value}, Industry: {industry}",
        "hr_hire":         "A new team member just joined. Role: {role}, Department: {department}, Their expertise: {expertise}",
        "product_launch":  "A new product/feature was just launched. Product: {product}, Key benefit: {benefit}, Target audience: {audience}",
        "milestone":       "Company milestone achieved. Milestone: {milestone}, Impact: {impact}",
        "event":           "Event happening. Event: {name}, Date: {date}, Topic: {topic}",
        "award":           "Award or recognition received. Award: {award}, From: {organization}",
        "client_success":  "Client success story. Client: {client}, Problem solved: {problem}, Result: {result}",
    }
    event_desc = trigger_templates.get(trigger_type, "Business event: " + str(event_data))
    try:
        event_desc = event_desc.format(**{k: event_data.get(k, f"[{k}]") for k in event_data})
    except (KeyError, ValueError):
        event_desc = trigger_type + ": " + str(event_data)

    cfg = _PLATFORM_CONFIG.get(platform, _PLATFORM_CONFIG["linkedin"])
    system = (
        f"You are a social media ghostwriter who turns business events into compelling {platform} posts. "
        f"Tone: {tone}. Language: {language}. Max chars: {cfg['max_chars']}."
    )
    prompt = (
        f"Brand: {brand_name or 'the company'} | Platform: {platform}\n"
        f"Event: {event_desc}\n\n"
        "Create social media content from this business event:\n"
        "1. PRIMARY POST — ready to publish (storytelling format, not a press release)\n"
        "2. SHORT VERSION — 1-2 sentence variant for Twitter or Stories\n"
        "3. HOOK OPTIONS — 3 alternative opening lines to A/B test\n"
        "4. IMAGE/VISUAL SUGGESTION — what image would make this post pop\n"
        "5. HASHTAGS — 5 relevant hashtags\n"
        "6. TEAM TAG SUGGESTION — who from the team to tag (role, not name)\n"
        "7. REPURPOSE IDEAS — 2 other content formats from the same event"
    )
    try:
        result = await ollama_chat_completion(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            model=OLLAMA_MODEL, max_tokens=700, temperature=0.7,
        )
        return {"action": "cross_agent_content", "trigger_type": trigger_type, "platform": platform, "post": result}
    except Exception as e:
        logger.error("Cross-agent content failed: %s", e)
        return {"error": "Cross-agent content generation failed.", "detail": str(e)}


# ── Unified analytics narrative ───────────────────────────────────────────────

async def generate_unified_analytics(
    brand_name:   str,
    metrics:      dict,   # {linkedin: {...}, twitter: {...}, instagram: {...}}
    period:       str = "last_month",
    language:     str = "en",
) -> dict:
    """Generate unified cross-platform analytics narrative + recommendations."""
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL
    import json

    system = f"You are a cross-platform social media analyst. Language: {language}."
    prompt = (
        f"Brand: {brand_name} | Period: {period}\n"
        f"Metrics across platforms:\n{json.dumps(metrics, indent=2)}\n\n"
        "Generate a unified analytics report:\n"
        "1. CROSS-PLATFORM EXECUTIVE SUMMARY\n"
        "   - Best performing platform (and why)\n"
        "   - Worst performing platform (and fix)\n"
        "   - Overall brand reach and growth rate\n\n"
        "2. PLATFORM BREAKDOWN (for each platform with data)\n"
        "   - Follower growth %\n"
        "   - Engagement rate vs last period\n"
        "   - Top content type that worked\n"
        "   - One thing to fix\n\n"
        "3. CONTENT INTELLIGENCE\n"
        "   - Common themes that worked across all platforms\n"
        "   - Posting time that drove most engagement\n"
        "   - Format (video/carousel/text) that won this period\n\n"
        "4. NEXT PERIOD STRATEGY\n"
        "   - Double down on: (2 things working)\n"
        "   - Stop doing: (1 thing wasting effort)\n"
        "   - Experiment with: (1 new tactic)\n"
        "   - Platform to prioritize\n\n"
        "5. KPI TARGETS for next period (realistic, data-driven)"
    )
    try:
        result = await ollama_chat_completion(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            model=OLLAMA_MODEL, max_tokens=900, temperature=0.4,
        )
        return {"action": "unified_analytics", "brand": brand_name, "period": period, "report": result}
    except Exception as e:
        logger.error("Unified analytics failed: %s", e)
        return {"error": "Unified analytics failed.", "detail": str(e)}


# ── Platform post preview builder ─────────────────────────────────────────────

async def build_post_preview_tips(
    post_text: str,
    platform:  str,
    has_image: bool = False,
) -> dict:
    """Analyse a draft post and return platform-specific preview tips and fixes."""
    cfg = _PLATFORM_CONFIG.get(platform, _PLATFORM_CONFIG["linkedin"])
    char_count = len(post_text)
    within_limit = char_count <= cfg["max_chars"]
    words = post_text.strip().split()
    hashtag_count = sum(1 for w in words if w.startswith("#"))
    over_hashtags = hashtag_count > cfg["hashtag_limit"]

    issues = []
    tips   = []
    if not within_limit:
        issues.append(f"Over character limit: {char_count}/{cfg['max_chars']} — trim {char_count - cfg['max_chars']} chars")
    if over_hashtags:
        issues.append(f"Too many hashtags: {hashtag_count}/{cfg['hashtag_limit']} for {platform}")
    if platform == "linkedin" and not any(c in post_text for c in ["?", "!", "\n"]):
        tips.append("Add a line break after the first sentence for better readability on LinkedIn")
    if platform == "twitter" and char_count > 240:
        tips.append("Consider splitting into a thread for better engagement")
    if not has_image and platform == "instagram":
        issues.append("Instagram posts need an image/video — text-only won't be visible")
    if not post_text.strip().endswith("?") and not any(cta in post_text.lower() for cta in ["comment", "share", "like", "tag", "follow", "dm"]):
        tips.append("Add a call-to-action or question at the end to drive engagement")
    if len(words) < 5:
        issues.append("Post is too short — add more context or value")

    return {
        "action":        "post_preview",
        "platform":      platform,
        "char_count":    char_count,
        "max_chars":     cfg["max_chars"],
        "within_limit":  within_limit,
        "hashtag_count": hashtag_count,
        "hashtag_limit": cfg["hashtag_limit"],
        "issues":        issues,
        "tips":          tips,
        "score":         max(0, 100 - len(issues) * 20 - len(tips) * 5),
        "preview_text":  post_text[:cfg["max_chars"]] if not within_limit else post_text,
    }


# ── Indian Cultural Calendar Campaign Planner ────────────────────────────────

INDIAN_CALENDAR = {
    "January":  ["Pongal (14)", "Makar Sankranti (14)", "Republic Day (26)", "Lohri (13)"],
    "February": ["Valentine's Day (14)", "Maha Shivaratri (varies)"],
    "March":    ["Holi (varies)", "International Women's Day (8)", "Ugadi/Gudi Padwa (varies)"],
    "April":    ["Ram Navami (varies)", "Tamil New Year (14)", "Dr. Ambedkar Jayanti (14)", "Hanuman Jayanti (varies)"],
    "May":      ["Labour Day (1)", "Mother's Day (2nd Sun)", "Buddha Purnima (varies)", "Eid ul-Fitr (varies)"],
    "June":     ["World Environment Day (5)", "Father's Day (3rd Sun)", "Eid al-Adha (varies)"],
    "July":     ["Guru Purnima (varies)", "GST Day (1 — for CA/Finance brands)", "Muharram (varies)"],
    "August":   ["Independence Day (15)", "Raksha Bandhan (varies)", "Janmashtami (varies)", "Onam (varies)"],
    "September": ["Teachers' Day (5)", "Ganesh Chaturthi (varies)", "Navaratri begins (varies)"],
    "October":  ["Gandhi Jayanti (2)", "Dussehra (varies)", "Navaratri ends", "World Mental Health Day (10)"],
    "November": ["Diwali (varies)", "Bhai Dooj (varies)", "Guru Nanak Jayanti (varies)", "Children's Day (14)"],
    "December": ["Christmas (25)", "New Year's Eve (31)", "Year-end sales season"],
}

async def plan_cultural_calendar(
    brand_name:   str,
    industry:     str,
    months:       list,      # e.g. ["October", "November"]
    platforms:    list,      # e.g. ["instagram", "whatsapp"]
    tone:         str = "festive",
    language:     str = "en",
) -> dict:
    """Generate campaign briefs for Indian festivals and national days — months ahead."""
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL
    import json

    events_block = ""
    for m in months:
        evts = INDIAN_CALENDAR.get(m, [])
        if evts:
            events_block += f"\n{m}: {', '.join(evts)}"

    system = (
        f"You are a senior Indian social media strategist. "
        f"Tone: {tone}. Language: {language}. "
        "Deep knowledge of Indian festivals, regional variations, and how Indian brands leverage them."
    )
    prompt = (
        f"Brand: {brand_name} | Industry: {industry}\n"
        f"Platforms: {', '.join(platforms)}\n"
        f"Months requested: {', '.join(months)}\n"
        f"Indian events in these months:{events_block}\n\n"
        "For each relevant festival/event create a campaign brief:\n"
        "1. EVENT NAME + DATE + why it matters for this brand\n"
        "2. CAMPAIGN ANGLE — unique hook that fits the brand (not generic 'Happy Diwali')\n"
        "3. CONTENT IDEAS per platform (3 posts: feed, story/reel, WhatsApp broadcast)\n"
        "4. CAPTION (ready to post) in selected language\n"
        "5. HASHTAGS (10 — mix of trending + niche)\n"
        "6. VISUAL DIRECTION — color palette, imagery style, cultural elements to include\n"
        "7. POSTING SCHEDULE — best days & times in the lead-up to the event\n"
        "8. DO / DON'T — cultural sensitivities specific to this festival\n\n"
        "Skip events that have no logical connection to this brand/industry.\n"
        "Output as JSON array: [{event, date, angle, posts:{feed,story,whatsapp}, caption, hashtags, visual, schedule, dos_donts}]"
    )
    try:
        raw = await ollama_chat_completion(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            model=OLLAMA_MODEL, max_tokens=1500, temperature=0.7,
        )
        try:
            import re
            match = re.search(r'\[.*\]', raw, re.DOTALL)
            campaigns = json.loads(match.group()) if match else []
        except Exception:
            campaigns = []
        return {
            "action": "cultural_calendar",
            "brand": brand_name,
            "months": months,
            "events_found": events_block.strip(),
            "campaigns": campaigns,
            "raw": raw if not campaigns else None,
        }
    except Exception as e:
        logger.error("Cultural calendar failed: %s", e)
        return {"error": "Cultural calendar generation failed.", "detail": str(e)}


# ── WhatsApp Business Content Generator ──────────────────────────────────────

async def generate_whatsapp_content(
    content_type: str,   # broadcast | catalogue | welcome | abandoned_cart | review_request | reorder
    brand_name:   str,
    industry:     str,
    product_name: str = "",
    offer:        str = "",
    customer_name: str = "Customer",
    language:     str = "en",
    tone:         str = "friendly",
) -> dict:
    """Generate WhatsApp Business messages — broadcasts, catalogues, automations."""
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL

    TYPE_DESC = {
        "broadcast":       "promotional broadcast message to opted-in customers",
        "catalogue":       "product catalogue description and CTA message",
        "welcome":         "welcome message for new WhatsApp contacts",
        "abandoned_cart":  "recover abandoned cart with gentle nudge",
        "review_request":  "ask happy customers for a Google/review",
        "reorder":         "remind customer to reorder a product they bought before",
    }
    desc = TYPE_DESC.get(content_type, content_type)

    system = (
        f"You are a WhatsApp Business messaging expert for Indian SMBs. "
        f"Tone: {tone}. Language: {language}. "
        "Messages must be under 1024 chars, conversational, use emojis sparingly, respect WhatsApp policies."
    )
    prompt = (
        f"Brand: {brand_name} | Industry: {industry}\n"
        f"Message type: {desc}\n"
        f"Product/Service: {product_name or 'general'}\n"
        f"Offer/Context: {offer or 'none'}\n"
        f"Customer name variable: {customer_name}\n\n"
        "Generate:\n"
        "1. PRIMARY MESSAGE (ready to send, under 1024 chars, with emojis)\n"
        "2. ALTERNATE VERSION (different angle, same goal)\n"
        "3. QUICK REPLY BUTTONS (3 options customers can tap)\n"
        "4. FOLLOW-UP MESSAGE (if no reply in 24h)\n"
        "5. BEST TIME TO SEND for Indian audiences\n"
        "6. ESTIMATED OPEN RATE for this message type (India benchmark)\n"
        "7. COMPLIANCE CHECK — any WhatsApp policy issue? (yes/no + reason)\n\n"
        "Output as JSON: {primary, alternate, quick_replies, followup, best_time, open_rate_benchmark, compliance_ok, compliance_note}"
    )
    try:
        raw = await ollama_chat_completion(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            model=OLLAMA_MODEL, max_tokens=800, temperature=0.7,
        )
        import json, re
        try:
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            data = json.loads(match.group()) if match else {}
        except Exception:
            data = {}
        return {
            "action": "whatsapp_content",
            "brand": brand_name,
            "content_type": content_type,
            "language": language,
            **data,
            "raw": raw if not data else None,
        }
    except Exception as e:
        logger.error("WhatsApp content generation failed: %s", e)
        return {"error": "WhatsApp content generation failed.", "detail": str(e)}


# ── Main social media agent dispatcher ───────────────────────────────────────

async def social_agent(
    action:   str,      # generate | post | schedule | hashtags | calendar | image
    platform: str,      # twitter | linkedin | instagram | all
    payload:  dict,
    user_id:  str = "",
    session_id: str = "",
    language: str = "en",
) -> dict:
    """
    Main social media agent dispatcher.
    All actual posting actions require PRO plan (checked in route layer).
    """
    if action == "generate":
        posts: dict = {}
        target_platforms = (
            ["twitter", "linkedin", "instagram"] if platform == "all"
            else [platform]
        )
        for plat in target_platforms:
            post = await generate_post(
                topic=payload.get("topic", ""),
                platform=plat,
                tone=payload.get("tone", "professional"),
                include_emoji=payload.get("include_emoji", True),
                brand_name=payload.get("brand_name", ""),
                language=language,
                extra_context=payload.get("extra_context", ""),
            )
            posts[plat] = post
        return {"action": "generate", "posts": posts}

    elif action == "image":
        return await generate_social_image(
            prompt=payload.get("prompt", ""),
            platform=platform,
            quality=payload.get("quality", "standard"),
            style=payload.get("style", "vivid"),
        )

    elif action == "hashtags":
        tags = await research_hashtags(
            topic=payload.get("topic", ""),
            platform=platform,
            count=payload.get("count", 15),
        )
        return {"hashtags": tags, "platform": platform, "count": len(tags)}

    elif action == "calendar":
        calendar = await plan_content_calendar(
            brand_name=payload.get("brand_name", ""),
            industry=payload.get("industry", "Technology"),
            platforms=payload.get("platforms", ["linkedin", "twitter"]),
            days=payload.get("days", 7),
            post_per_day=payload.get("post_per_day", 1),
            language=language,
        )
        return {"calendar": calendar, "days": len(calendar)}

    elif action == "post":
        access_token = payload.get("access_token", "")
        post_text    = payload.get("post_text", "")
        image_b64    = payload.get("image_b64")

        if platform == "linkedin":
            return await post_to_linkedin(access_token, post_text, image_b64)
        elif platform == "twitter":
            return await post_to_twitter(post_text, image_b64)
        elif platform == "instagram":
            return {
                "status": "manual_required",
                "note":   "Instagram requires Business API approval. Use Buffer to schedule.",
                "caption": post_text,
            }
        return {"error": f"Platform '{platform}' not supported for direct posting."}

    elif action == "schedule":
        return await schedule_via_buffer(
            post_text=payload.get("post_text", ""),
            platforms=payload.get("platforms", [platform]),
            scheduled_at=payload.get("scheduled_at"),
            image_url=payload.get("image_url"),
        )

    elif action == "repurpose":
        return await repurpose_content(
            source_content=payload.get("source_content", ""),
            content_type=payload.get("content_type", "blog"),
            brand_name=payload.get("brand_name", ""),
            tone=payload.get("tone", "professional"),
            language=language,
        )

    elif action == "competitor_audit":
        return await competitor_social_audit(
            competitor_name=payload.get("competitor_name", ""),
            competitor_niche=payload.get("competitor_niche", ""),
            our_brand=payload.get("our_brand", ""),
            platforms=payload.get("platforms"),
        )

    elif action == "ad_copy":
        return await generate_ad_copy(
            product=payload.get("product", ""),
            audience=payload.get("audience", ""),
            goal=payload.get("goal", "leads"),
            platform=payload.get("ad_platform", "meta"),
            budget_range=payload.get("budget_range", ""),
            usp=payload.get("usp", ""),
            language=language,
        )

    elif action == "influencer_brief":
        return await generate_influencer_brief(
            brand_name=payload.get("brand_name", ""),
            product=payload.get("product", ""),
            campaign_goal=payload.get("campaign_goal", ""),
            influencer_niche=payload.get("influencer_niche", ""),
            deliverables=payload.get("deliverables", ""),
            budget=payload.get("budget", ""),
            timeline=payload.get("timeline", ""),
            dos_donts=payload.get("dos_donts", ""),
        )

    elif action == "crisis_response":
        return await generate_crisis_response(
            brand_name=payload.get("brand_name", ""),
            crisis_type=payload.get("crisis_type", "negative_review"),
            crisis_detail=payload.get("crisis_detail", ""),
            platform=platform,
            severity=payload.get("severity", "medium"),
        )

    elif action == "youtube_script":
        return await generate_youtube_script(
            topic=payload.get("topic", ""),
            channel_niche=payload.get("channel_niche", ""),
            duration_min=payload.get("duration_min", 8),
            style=payload.get("style", "educational"),
            brand_name=payload.get("brand_name", ""),
            cta=payload.get("cta", ""),
            language=language,
        )

    elif action == "email_sequence":
        return await generate_email_sequence(
            sequence_type=payload.get("sequence_type", "welcome"),
            product=payload.get("product", ""),
            audience=payload.get("audience", ""),
            num_emails=payload.get("num_emails", 5),
            brand_name=payload.get("brand_name", ""),
            tone=payload.get("tone", "friendly"),
            language=language,
        )

    elif action == "reel_script":
        return generate_reel_script(
            business_name=payload.get("brand_name", ""),
            business_type=payload.get("industry", payload.get("channel_niche", "")),
            reel_topic=payload.get("topic", ""),
            reel_goal=payload.get("reel_goal", "awareness"),
            target_audience=payload.get("target_audience", ""),
            duration=int(payload.get("duration", 30) or 30),
            style=payload.get("hook_style", "educational"),
            language=language,
        )

    elif action == "monthly_report":
        return await generate_monthly_report(
            brand_name=payload.get("brand_name", ""),
            month=payload.get("month", ""),
            metrics=payload.get("metrics", {}),
            goals=payload.get("goals", ""),
            language=language,
        )

    elif action == "keyword_cluster":
        return await build_keyword_cluster(
            main_topic=payload.get("main_topic", ""),
            industry=payload.get("industry", ""),
            audience=payload.get("audience", ""),
            language=language,
            market=payload.get("market", "India"),
        )

    elif action == "best_post_time":
        return await suggest_best_post_time(
            platform=platform,
            industry=payload.get("industry", ""),
            audience=payload.get("audience", ""),
            timezone=payload.get("timezone", "IST"),
        )

    elif action == "benchmark_engagement":
        return await benchmark_engagement_rate(
            platform=platform,
            industry=payload.get("industry", ""),
            your_rate=float(payload.get("your_rate", 0)),
            followers=int(payload.get("followers", 0)),
            content_type=payload.get("content_type", "mixed"),
        )

    elif action == "performance_score":
        return await score_content_performance(
            post_text=payload.get("post_text", ""),
            platform=platform,
            industry=payload.get("industry", ""),
            audience=payload.get("audience", ""),
        )

    elif action == "india_trends":
        return await generate_india_trends(
            industry=payload.get("industry", ""),
            language=language,
            month=payload.get("month", ""),
        )

    elif action == "regional_post":
        return await generate_regional_post(
            topic=payload.get("topic", ""),
            regional_language=payload.get("regional_language", "tamil"),
            platform=platform,
            brand_name=payload.get("brand_name", ""),
            tone=payload.get("tone", "professional"),
        )

    elif action == "whatsapp_content":
        return await generate_whatsapp_content(
            content_type=payload.get("content_type", "broadcast"),
            brand_name=payload.get("brand_name", ""),
            industry=payload.get("industry", payload.get("audience", "general")),
            product_name=payload.get("topic", payload.get("product_name", "")),
            offer=payload.get("offer", ""),
            customer_name=payload.get("customer_name", "Customer"),
            language=language,
            tone=payload.get("tone", "friendly"),
        )

    elif action == "niche_templates":
        return await generate_niche_templates(
            niche=payload.get("niche", "ca_firm"),
            brand_name=payload.get("brand_name", ""),
            month=payload.get("month", ""),
            language=language,
            platform=platform,
        )

    elif action == "bulk_generate":
        topics = payload.get("topics", [])
        brand = payload.get("brand_name", "")
        return generate_bulk_posts(
            company_name=brand,
            industry=payload.get("industry", "technology"),
            tone=payload.get("tone", "professional"),
            target_audience=payload.get("target_audience", "general audience"),
            platform=platform,
            count=len(topics) if topics else int(payload.get("count", 5)),
            brand_keywords=topics if topics else payload.get("brand_keywords", []),
            usp=payload.get("usp", ""),
        )

    elif action == "content_pillars":
        return await build_content_pillar_plan(
            brand_name=payload.get("brand_name", ""),
            industry=payload.get("industry", ""),
            audience=payload.get("audience", ""),
            pillars=payload.get("pillars"),
            language=language,
        )

    elif action == "brand_monitor":
        return await monitor_brand_mentions(
            brand_name=payload.get("brand_name", ""),
            industry=payload.get("industry", ""),
            competitors=payload.get("competitors"),
            language=language,
        )

    elif action == "competitor_tracker":
        return await track_competitor_posts(
            competitor_name=payload.get("competitor_name", ""),
            niche=payload.get("niche", ""),
            timeframe=payload.get("timeframe", "last_week"),
            our_brand=payload.get("our_brand", ""),
        )

    elif action == "cross_agent_content":
        return await generate_cross_agent_content(
            trigger_type=payload.get("trigger_type", "milestone"),
            event_data=payload.get("event_data", {}),
            brand_name=payload.get("brand_name", ""),
            platform=platform,
            tone=payload.get("tone", "professional"),
            language=language,
        )

    elif action == "unified_analytics":
        return await generate_unified_analytics(
            brand_name=payload.get("brand_name", ""),
            metrics=payload.get("metrics", {}),
            period=payload.get("period", "last_month"),
            language=language,
        )

    elif action == "post_preview":
        return await build_post_preview_tips(
            post_text=payload.get("post_text", ""),
            platform=platform,
            has_image=payload.get("has_image", False),
        )

    elif action == "cultural_calendar":
        return await plan_cultural_calendar(
            brand_name=payload.get("brand_name", ""),
            industry=payload.get("industry", ""),
            months=payload.get("months", []),
            platforms=payload.get("platforms", ["instagram"]),
            tone=payload.get("tone", "festive"),
            language=language,
        )

    elif action == "content_scheduler":
        return await plan_content_scheduler(
            brand_name=payload.get("brand_name", ""),
            industry=payload.get("industry", ""),
            platforms=payload.get("platforms", ["instagram", "linkedin"]),
            days=int(payload.get("days", 7)),
            goal=payload.get("goal", "brand awareness"),
            audience=payload.get("audience", "general"),
            language=language,
        )

    elif action == "festive_post":
        return generate_festive_post(
            brand_name=payload.get("brand_name", ""),
            festival=payload.get("festival", "diwali"),
            post_angle=payload.get("post_angle", "appreciation"),
            industry=payload.get("industry", "general"),
            offer_text=payload.get("offer_text", ""),
            tip_text=payload.get("tip_text", ""),
            prize_text=payload.get("prize_text", ""),
            custom_festival_name=payload.get("custom_festival_name", ""),
            language=language,
        )

    elif action == "twitter_thread":
        return generate_twitter_thread(
            brand_name=payload.get("brand_name", ""),
            topic=payload.get("topic", ""),
            thread_type=payload.get("thread_type", "educational"),
            industry=payload.get("industry", "general"),
            num_tweets=payload.get("num_tweets", 8),
            include_hook_variants=payload.get("include_hook_variants", True),
            language=language,
        )

    elif action == "story_highlights":
        return generate_story_highlights_plan(
            brand_name=payload.get("brand_name", ""),
            industry=payload.get("industry", "general"),
            brand_colors=payload.get("brand_colors", ""),
            num_highlights=payload.get("num_highlights", 8),
            cover_style=payload.get("cover_style", "minimal"),
            language=language,
        )

    elif action == "meme_caption":
        return generate_meme_caption(
            brand_name=payload.get("brand_name", ""),
            topic=payload.get("topic", ""),
            meme_template=payload.get("meme_template", "drake"),
            industry=payload.get("industry", "general"),
            tone=payload.get("tone", "relatable"),
            custom_panel_texts=payload.get("custom_panel_texts", []),
            language=language,
        )

    elif action == "facebook_post":
        return generate_facebook_post(
            brand_name=payload.get("brand_name", ""),
            post_topic=payload.get("post_topic", ""),
            post_type=payload.get("post_type", "engagement"),
            audience=payload.get("audience", "b2c"),
            post_format=payload.get("post_format", "text_post"),
            product_or_offer=payload.get("product_or_offer", ""),
            location=payload.get("location", ""),
            language=language,
        )

    elif action == "comment_replies":
        return generate_comment_replies(
            brand_name=payload.get("brand_name", ""),
            post_topic=payload.get("post_topic", ""),
            comments=payload.get("comments", []),
            brand_tone=payload.get("brand_tone", "friendly"),
            platform=platform,
            include_cta=payload.get("include_cta", True),
            language=language,
        )
    elif action == "bio_optimizer":
        return generate_bio_optimizer(
            name=payload.get("name", ""),
            current_bio=payload.get("current_bio", ""),
            profession=payload.get("profession", ""),
            industry=payload.get("industry", "technology"),
            target_audience=payload.get("target_audience", ""),
            cta_goal=payload.get("cta_goal", ""),
            tone=payload.get("tone", "professional"),
            achievements=payload.get("achievements", ""),
            platforms=payload.get("platforms", ["instagram", "linkedin", "twitter"]),
            language=language,
        )
    elif action == "product_launch_kit":
        return generate_product_launch_kit(
            product_name=payload.get("product_name", ""),
            product_description=payload.get("product_description", ""),
            target_audience=payload.get("target_audience", ""),
            launch_date=payload.get("launch_date", ""),
            platforms=payload.get("platforms", ["instagram", "linkedin"]),
            usp=payload.get("usp", ""),
            price_point=payload.get("price_point", ""),
            industry=payload.get("industry", "technology"),
            language=language,
        )
    elif action == "bulk_posts":
        return generate_bulk_posts(
            company_name=payload.get("company_name", ""),
            industry=payload.get("industry", "technology"),
            tone=payload.get("tone", "professional"),
            target_audience=payload.get("target_audience", ""),
            platform=payload.get("platform", "instagram"),
            count=payload.get("count", 15),
            brand_keywords=payload.get("brand_keywords", []),
            usp=payload.get("usp", ""),
        )

    elif action == "brand_voice_engine":
        return generate_brand_voice_engine(
            company_name=payload.get("company_name", ""),
            industry=payload.get("industry", "technology"),
            primary_tone=payload.get("primary_tone", "professional"),
            target_audience=payload.get("target_audience", ""),
            brand_keywords=payload.get("brand_keywords", []),
            avoid_words=payload.get("avoid_words", []),
            competitors=payload.get("competitors", []),
            usp=payload.get("usp", ""),
            language=payload.get("language", "English"),
        )

    elif action == "content_calendar":
        return generate_content_calendar(
            company_name=payload.get("company_name", ""),
            industry=payload.get("industry", "technology"),
            tone=payload.get("tone", "professional"),
            target_audience=payload.get("target_audience", ""),
            platforms=payload.get("platforms", ["instagram", "linkedin"]),
            week_label=payload.get("week_label", "This Week"),
            brand_keywords=payload.get("brand_keywords", []),
            usp=payload.get("usp", ""),
        )

    elif action == "linkedin_company_post":
        return generate_linkedin_company_post(
            company_name=payload.get("company_name", ""),
            industry=payload.get("industry", "technology"),
            post_type=payload.get("post_type", "thought_leadership"),
            topic=payload.get("topic", ""),
            key_message=payload.get("key_message", ""),
            tone=payload.get("tone", "professional"),
            include_cta=payload.get("include_cta", True),
            target_audience=payload.get("target_audience", ""),
        )

    elif action == "youtube_description":
        return generate_youtube_description(
            channel_name=payload.get("channel_name", ""),
            video_title=payload.get("video_title", ""),
            video_topic=payload.get("video_topic", ""),
            video_category=payload.get("video_category", "education"),
            target_audience=payload.get("target_audience", ""),
            key_points=payload.get("key_points", []),
            timestamps=payload.get("timestamps", []),
            website=payload.get("website", ""),
            social_handles=payload.get("social_handles", {}),
        )

    elif action == "ig_reel_script":
        return generate_reel_script(
            business_name=payload.get("business_name", ""),
            business_type=payload.get("business_type", ""),
            reel_topic=payload.get("reel_topic", ""),
            reel_goal=payload.get("reel_goal", "awareness"),
            target_audience=payload.get("target_audience", ""),
            duration=payload.get("duration", 30),
            style=payload.get("style", "educational"),
            language=payload.get("language", "en"),
        )

    elif action == "review_testimonial_kit":
        return generate_review_testimonial_kit(
            business_name=payload.get("business_name", ""),
            business_type=payload.get("business_type", ""),
            owner_name=payload.get("owner_name", ""),
            product_service=payload.get("product_service", ""),
            review_platform=payload.get("review_platform", "google"),
            customer_type=payload.get("customer_type", "b2c"),
            tone=payload.get("tone", "warm"),
        )

    elif action == "linkedin_article":
        return generate_linkedin_article(
            topic=payload.get("topic", ""),
            brand_name=payload.get("brand_name", ""),
            author_name=payload.get("author_name", ""),
            industry=payload.get("industry", ""),
            target_audience=payload.get("target_audience", ""),
            article_goal=payload.get("article_goal", "thought_leadership"),
            key_points=payload.get("key_points", []),
            word_count=int(payload.get("word_count", 1200) or 1200),
        )

    elif action == "podcast_content_kit":
        return generate_podcast_content_kit(
            episode_title=payload.get("episode_title", ""),
            brand_name=payload.get("brand_name", ""),
            host_name=payload.get("host_name", ""),
            key_points=payload.get("key_points", []),
            guest_name=payload.get("guest_name", ""),
            episode_url=payload.get("episode_url", ""),
            industry=payload.get("industry", ""),
            target_audience=payload.get("target_audience", ""),
        )

    elif action == "linkedin_carousel":
        return generate_linkedin_carousel(
            topic=payload.get("topic", ""),
            brand_name=payload.get("brand_name", ""),
            industry=payload.get("industry", ""),
            audience=payload.get("audience", "professionals"),
            num_slides=int(payload.get("num_slides", 8) or 8),
            goal=payload.get("goal", "thought leadership"),
            style=payload.get("style", "educational"),
        )

    elif action == "influencer_outreach":
        return generate_influencer_outreach(
            brand_name=payload.get("brand_name", ""),
            influencer_name=payload.get("influencer_name", ""),
            influencer_niche=payload.get("influencer_niche", ""),
            influencer_platform=payload.get("influencer_platform", "instagram"),
            follower_count=int(payload.get("follower_count", 50000) or 50000),
            campaign_goal=payload.get("campaign_goal", "brand awareness"),
            product_name=payload.get("product_name", ""),
            budget_range=payload.get("budget_range", ""),
            deliverables=payload.get("deliverables", []),
            industry=payload.get("industry", ""),
        )

    elif action == "viral_hook_generator":
        return generate_viral_hooks(
            topic=payload.get("topic", ""),
            brand_name=payload.get("brand_name", ""),
            industry=payload.get("industry", ""),
            platforms=payload.get("platforms", ["linkedin", "twitter"]),
            goal=payload.get("goal", "engagement"),
        )

    elif action == "employee_advocacy":
        return await generate_employee_advocacy(
            company_name=payload.get("company_name", ""),
            news_or_achievement=payload.get("news_or_achievement", ""),
            employee_role=payload.get("employee_role", ""),
            industry=payload.get("industry", ""),
            tone=payload.get("tone", "professional"),
            platforms=payload.get("platforms", ["linkedin"]),
            num_variants=int(payload.get("num_variants", 3) or 3),
            language=language,
        )

    elif action == "competitor_spy":
        return competitor_content_spy(
            brand_name=payload.get("brand_name", ""),
            competitors=payload.get("competitors", []),
            industry=payload.get("industry", ""),
            platforms=payload.get("platforms", ["instagram", "linkedin"]),
            language=language,
        )

    elif action == "social_roi":
        return calculate_social_roi(
            campaigns=payload.get("campaigns", []),
            brand_name=payload.get("brand_name", ""),
            period=payload.get("period", ""),
            language=language,
        )

    elif action == "mention_responder":
        return await respond_to_mentions(
            mentions=payload.get("mentions", []),
            brand_name=payload.get("brand_name", ""),
            brand_voice=payload.get("brand_voice", "professional"),
            industry=payload.get("industry", ""),
            language=language,
        )

    elif action == "ab_copy_test":
        return await generate_ab_copy(
            topic=payload.get("topic", ""),
            platform=platform,
            brand_name=payload.get("brand_name", ""),
            industry=payload.get("industry", ""),
            goal=payload.get("goal", "engagement"),
            variations=int(payload.get("variations", 4)),
            language=language,
        )

    return {"error": f"Unknown social action: {action}"}


# ── Twitter/X Thread Optimizer (Round 13) ────────────────────────────────────

_THREAD_STYLES = {
    "educational": {
        "hook_formula":    "Most {audience} don't know this about {topic}. A thread 🧵",
        "structure":       ["hook", "context", "point", "point", "point", "point", "example", "counterintuitive", "summary", "cta"],
        "tone":            "Clear, informative, scannable — one idea per tweet",
        "engagement_tip":  "Ask a question in tweet 2 — 'Which of these surprised you?' — drives early replies which boost the thread.",
    },
    "storytelling": {
        "hook_formula":    "6 months ago, I almost quit {topic}. Here's what happened (and what I learned) 🧵",
        "structure":       ["hook", "setup", "inciting_incident", "struggle", "turning_point", "resolution", "lesson", "apply_it", "takeaway", "cta"],
        "tone":            "Personal, vulnerable, narrative — read like a story not a list",
        "engagement_tip":  "End each tweet on a mini cliffhanger. Make them NEED to click 'Show this thread'.",
    },
    "listicle": {
        "hook_formula":    "{num} {topic} tips that took me years to learn. Save this 🧵",
        "structure":       ["hook", "tip", "tip", "tip", "tip", "tip", "tip", "tip", "bonus", "cta"],
        "tone":            "Punchy, actionable, one tip per tweet — no fluff",
        "engagement_tip":  "Number each tip clearly (1/ 2/ 3/). People save numbered threads to come back to.",
    },
    "contrarian": {
        "hook_formula":    "Hot take: everything you know about {topic} is wrong. Here's why 🧵",
        "structure":       ["hook", "bold_claim", "why_wrong", "evidence", "what_actually_works", "proof", "objection", "rebuttal", "new_framework", "cta"],
        "tone":            "Confident, provocative, but backed by evidence — not just rage-bait",
        "engagement_tip":  "Contrarian threads get 3x replies. Expect pushback — engage with it, it fuels the algorithm.",
    },
    "how_to": {
        "hook_formula":    "How to {topic} in {timeframe}. Step-by-step 🧵",
        "structure":       ["hook", "why_it_matters", "step", "step", "step", "step", "step", "common_mistake", "results", "cta"],
        "tone":            "Practical, specific, beginner-friendly — show the exact steps",
        "engagement_tip":  "Add 'Reply with your result after trying step 3' — creates accountability and replies.",
    },
}

_TWEET_TEMPLATES = {
    "hook":              "HOOK — stop the scroll. Bold claim, surprising stat, or emotional opener. Under 200 chars. End with '🧵' to signal a thread.",
    "context":           "CONTEXT — who is this for and why does it matter right now? 1-2 sentences max.",
    "point":             "INSIGHT — one idea, fully explained. Lead with the punchline, then explain. Add a stat or example if you have one.",
    "tip":               "TIP — state it directly, then explain the 'why'. Format: [The tip]. Here's why it works: [explanation]",
    "example":           "EXAMPLE — make it concrete. Name a real brand, person, or scenario. Numbers > adjectives always.",
    "counterintuitive":  "COUNTER-INTUITIVE TAKE — 'Most people think X. But actually Y.' This is the most saved tweet type.",
    "summary":           "SUMMARY — TL;DR of the whole thread in 3-5 bullet points. Design this to stand alone as a screenshot.",
    "cta":               "CTA — one clear action: Follow for more, RT if this helped, Reply with your experience, or Link to resource. Don't ask for multiple things.",
    "setup":             "SETUP — paint the before picture. Who were you / what was the situation before everything changed?",
    "inciting_incident": "INCITING INCIDENT — the moment that started the story. Be specific: date, place, what happened.",
    "struggle":          "STRUGGLE — what went wrong. Don't skip this — the struggle makes the resolution satisfying.",
    "turning_point":     "TURNING POINT — the insight, decision, or event that changed everything.",
    "resolution":        "RESOLUTION — what happened after. Specific results with numbers.",
    "lesson":            "THE LESSON — what would you do differently? What's the transferable insight?",
    "apply_it":          "APPLY IT — how can the reader use this lesson right now? Make it concrete.",
    "takeaway":          "TAKEAWAY — the one thing you want them to remember. Short. Memorable. Quotable.",
    "bold_claim":        "BOLD CLAIM — state your contrarian position clearly. No hedging. Own it.",
    "why_wrong":         "WHY THE CONVENTIONAL WISDOM IS WRONG — evidence, data, or logic that contradicts the mainstream view.",
    "evidence":          "EVIDENCE — back up your claim. Research, case study, or personal experience with numbers.",
    "what_actually_works": "WHAT ACTUALLY WORKS — your alternative framework or approach.",
    "proof":             "PROOF — results that validate your approach. Specifics only.",
    "objection":         "STEELMAN THE OBJECTION — 'I know what you're thinking...' Address the strongest counterargument honestly.",
    "rebuttal":          "YOUR REBUTTAL — why you still hold your position despite the objection.",
    "new_framework":     "THE NEW FRAMEWORK — distill your contrarian view into a memorable model or principle.",
    "why_it_matters":    "WHY IT MATTERS — the cost of NOT doing this. Make the stakes clear.",
    "step":              "STEP N — [action]. Be specific: what to do, how to do it, what good looks like.",
    "common_mistake":    "COMMON MISTAKE — what trips most people up at this stage. How to avoid it.",
    "results":           "RESULTS — what happens when you follow this correctly. Specific outcome + timeframe.",
    "bonus":             "BONUS TIP — the unexpected extra that makes them feel they got more than promised.",
}

_THREAD_RULES = [
    "Tweet 1 (hook) determines 80% of impressions — spend most time here.",
    "Keep each tweet under 240 characters when possible — easier to screenshot and share.",
    "Never end a tweet with a period before the last one — it signals 'keep reading'.",
    "Use line breaks liberally — wall-of-text tweets get skipped.",
    "The summary tweet (TL;DR) gets more saves than any other — design it to stand alone.",
    "Reply to every comment in the first hour — algorithm interprets replies as engagement signal.",
    "Post your thread as a reply to yourself, not as separate tweets — keeps it as one unit.",
    "Best time for Indian Twitter/X: 8-9 AM and 9-10 PM IST on weekdays.",
]


# ── LinkedIn Article Generator (Round 15) ────────────────────────────────────

_ARTICLE_GOALS = {
    "thought_leadership": {
        "intro_hook":   "Start with a bold, counterintuitive claim or a surprising industry statistic. Make the reader stop scrolling.",
        "structure":    ["hook_intro", "problem_framing", "insight_1", "insight_2", "insight_3", "case_example", "framework", "actionable_takeaway", "cta"],
        "cta_type":     "Follow for weekly insights + invite comment debate",
        "length_guide": "1200-1500 words. Long enough to be authoritative, short enough to be read.",
    },
    "lead_generation": {
        "intro_hook":   "Open with the pain point your ideal customer feels every day. Make them feel seen immediately.",
        "structure":    ["pain_hook", "why_it_happens", "common_mistakes", "the_better_way", "proof_point", "step_by_step", "result_promise", "soft_cta"],
        "cta_type":     "DM / link to lead magnet / free consultation offer",
        "length_guide": "900-1200 words. Enough depth to build trust, CTA before they lose interest.",
    },
    "brand_awareness": {
        "intro_hook":   "Tell a story — a client win, a failure, a behind-the-scenes moment. Human beats corporate every time.",
        "structure":    ["story_hook", "context", "challenge", "what_we_did", "result", "broader_lesson", "brand_values", "cta"],
        "cta_type":     "Share if this resonated / tag someone who needs to read this",
        "length_guide": "800-1000 words. Story-driven — doesn't need to be long, needs to be vivid.",
    },
    "seo_traffic": {
        "intro_hook":   "Use the target keyword naturally in the first sentence. Frame as a definitive guide or answer.",
        "structure":    ["keyword_intro", "what_is_it", "why_it_matters", "how_to_section_1", "how_to_section_2", "how_to_section_3", "common_questions", "summary_cta"],
        "cta_type":     "Download resource / visit website for deeper guide",
        "length_guide": "1500-2000 words for SEO. LinkedIn indexes long articles — use headers with keywords.",
    },
}

_SECTION_WRITERS = {
    "hook_intro":        "HOOK (150-200 words): Open with a bold claim or stat that challenges conventional wisdom. Example: 'Most {industry} leaders are optimizing for the wrong metric — and it's costing them 30% growth.' Then expand why this matters NOW, in this moment. End with: 'Here's what I've learned after [X years / working with Y companies]:'",
    "pain_hook":         "PAIN HOOK (100-150 words): Describe the exact pain your reader feels in their own words. 'You're doing everything right — posting consistently, running ads, attending events — and still not getting inbound leads. Here's why that's not your fault, and what actually works.'",
    "story_hook":        "STORY HOOK (150-200 words): 'Three months ago, we almost lost our biggest client. Here's what happened — and what it taught us about [topic].' Be specific: name the client type, the amount at risk, the exact moment of crisis. Specificity = credibility.",
    "problem_framing":   "PROBLEM FRAMING (100-150 words): Define the problem clearly. What's broken about the current approach? Include a specific stat or observation that proves it's widespread. This section validates the reader — they're not alone in struggling with this.",
    "why_it_happens":    "ROOT CAUSE (100-150 words): Explain WHY the problem exists — not just what it is. Most articles describe symptoms. Go one level deeper. This positions you as an expert, not just an observer.",
    "insight_1":         "KEY INSIGHT 1 (150-200 words): Your first core insight. Lead with the conclusion, then explain. Use the structure: 'Here's the thing most people miss: [insight]. Why? Because [explanation]. What this means practically: [application].'",
    "insight_2":         "KEY INSIGHT 2 (150-200 words): Second insight — build on the first, add a layer. Include a mini case study, quote, or example that makes this concrete. Abstract insights without proof don't convert readers to followers.",
    "insight_3":         "KEY INSIGHT 3 (150-200 words): Third insight — the most counterintuitive one. Save your boldest claim for here. Readers who make it this far are engaged — reward them with your best thinking.",
    "framework":         "FRAMEWORK (150-200 words): Give the reader a mental model they can take away. Name it if possible (e.g., 'The 3-Layer Revenue Model', 'The CSAT Flywheel'). A named framework is quotable, shareable, and memorable. Include a simple description of the 3-4 components.",
    "case_example":      "CASE EXAMPLE (100-150 words): One specific story that proves your point. Format: Situation → Problem → What we did → Result (with specific numbers). Don't be vague — '30% improvement' beats 'significant improvement' every time.",
    "proof_point":       "PROOF / CREDIBILITY (100-150 words): Specific results, client outcomes, or data that validates your approach. LinkedIn readers are skeptical — earn trust with evidence, not claims.",
    "step_by_step":      "HOW-TO STEPS (200-250 words): Number your steps. Start each with an action verb. Include enough detail that someone could actually do this. Vague advice ('just improve your onboarding') gets ignored. Specific steps get saved and shared.",
    "how_to_section_1":  "HOW-TO SECTION 1 (150-200 words): First major how-to block. Header with keyword where natural. Detailed enough to be genuinely useful — not just headlines.",
    "how_to_section_2":  "HOW-TO SECTION 2 (150-200 words): Second major block. Build on section 1. Include a tool recommendation, template, or resource.",
    "how_to_section_3":  "HOW-TO SECTION 3 (150-200 words): Third major block. This is where you address the hardest/most common obstacle readers face.",
    "common_mistakes":   "COMMON MISTAKES (150-200 words): List 3-5 mistakes. For each: what people do, why they do it, why it fails, what to do instead. Mistake lists get saved and shared because everyone recognizes themselves in them.",
    "actionable_takeaway":"TAKEAWAYS (100-150 words): 3-5 bullet points — the 'if you remember nothing else, remember this' section. Design this to stand alone as a screenshot. Bold the key phrase in each bullet.",
    "the_better_way":    "THE BETTER WAY (150-200 words): The alternative to the common mistakes above. Be prescriptive — 'Do X instead of Y.' Give people a clear direction, not just awareness.",
    "result_promise":    "RESULT (100 words): What does success look like? Be specific about the outcome the reader can expect if they follow your advice. Timeframe + metric where possible.",
    "broader_lesson":    "BROADER LESSON (100-150 words): Zoom out from your specific story to the universal principle it illustrates. This is where the article earns its place in a reader's saved posts.",
    "brand_values":      "BRAND VALUES (50-100 words): One short paragraph about how this story reflects what your company/team believes. Authentic, not salesy. 'This is why we built X the way we did' or 'This experience is what drives how we work with clients.'",
    "summary_cta":       "SUMMARY + CTA (100-150 words): Quick TL;DR of the whole article, then one clear call to action. Don't ask for multiple things. Pick one: follow, comment, share, DM, or click link.",
    "soft_cta":          "SOFT CTA (100-150 words): A value-led close: 'If you're dealing with this challenge, here's one thing you can do today: [specific action]. And if you want to go deeper, [offer/resource/conversation].' Low friction, high relevance.",
    "keyword_intro":     "SEO INTRO (100-150 words): Use your primary keyword in the first two sentences naturally. Define the topic clearly. LinkedIn indexes this article — treat it like a blog post. Include secondary keywords in the first paragraph too.",
    "what_is_it":        "DEFINITION (100-150 words): Clear, jargon-free definition of the core concept. Who is it for? Why does it exist? Link to a real example if you can.",
    "why_it_matters":    "WHY IT MATTERS (100-150 words): The business / career impact of getting this right (or wrong). Include a stat if you have one. Urgency + relevance.",
    "common_questions":  "FAQs (150-200 words): 3-4 questions your ideal reader actually Googles. Answer each in 2-3 sentences. This section drives SEO traffic because it matches search intent.",
    "context":           "CONTEXT (100 words): Set the scene for your story. When, where, who. Give enough detail that the reader can picture it.",
    "challenge":         "THE CHALLENGE (100-150 words): What went wrong, or what problem needed solving. Be honest — include your initial reaction, even if it wasn't your proudest moment.",
    "what_we_did":       "WHAT WE DID (150-200 words): Specific actions taken, in order. Not 'we improved our process' but 'we rebuilt the onboarding email sequence, cut it from 12 emails to 5, and added a video from the founder in email 2.'",
    "result":            "THE RESULT (100-150 words): Outcome with specific numbers. 'Within 60 days, NPS went from 32 to 58. Churn dropped from 8% to 3.2% monthly. And that client renewed at 2x the contract value.' Numbers + time frame = credibility.",
    "cta":               "CLOSING CTA (75-100 words): End with an invitation for engagement. Ask a specific question to drive comments: 'What's the biggest [topic] mistake you see in your industry? Drop it below.' Then: 'Follow me for weekly [topic] insights that actually work for Indian businesses.'",
}

_PULL_QUOTE_TEMPLATES = [
    '"{insight}" — this is the one line people screenshot and share. Design it to stand alone.',
    "The most-saved LinkedIn articles always have one quotable sentence. Make sure yours does too.",
    "Use pull quotes to break up long sections visually and give readers a reason to pause.",
]

_SEO_TIPS = [
    "Use your primary keyword in the article title and first paragraph",
    "Add 3-5 relevant hashtags at the end (LinkedIn indexes these)",
    "Write a compelling 160-character meta description in your intro paragraph",
    "Use H2-style subheadings (bold text in LinkedIn) every 200-300 words",
    "Internal link: mention other articles or posts you've written on related topics",
    "Optimal publish time for maximum indexing: Tuesday-Thursday 7-9 AM IST",
]


_REVIEW_CHANNELS = {
    "google":      {"name": "Google Reviews", "url_hint": "g.page/your-business/review", "emoji": "⭐", "impact": "Highest SEO impact — boosts local search ranking"},
    "justdial":    {"name": "JustDial", "url_hint": "justdial.com/your-listing", "emoji": "📋", "impact": "Critical for Indian B2C discovery — service & retail"},
    "indiamart":   {"name": "IndiaMart", "url_hint": "indiamart.com/your-profile", "emoji": "🏭", "impact": "Essential for B2B suppliers & manufacturers"},
    "facebook":    {"name": "Facebook Reviews", "url_hint": "facebook.com/your-page/reviews", "emoji": "👍", "impact": "Social proof for FB ads — boosts ad CTR"},
    "trustpilot":  {"name": "Trustpilot", "url_hint": "trustpilot.com/evaluate/your-domain", "emoji": "✅", "impact": "High-trust badge for D2C & SaaS brands"},
}

_REVIEW_TIMING = {
    "post_delivery":   "Send 24-48 hours after delivery/service completion — peak satisfaction window",
    "post_onboarding": "Send after first successful use — customer has experienced value",
    "milestone":       "Send after 30-day usage milestone — loyalty peak",
    "post_support":    "Send 2 hours after support ticket resolved — relief + gratitude combo",
}

_TESTIMONIAL_FORMATS = {
    "written":  "Short written testimonial (2-4 sentences) — share on website, social, proposals",
    "video":    "30-60 second video via WhatsApp — highest conversion impact, authentic",
    "case_study": "Structured before/after story — ideal for B2B sales conversations",
    "star_rating": "Quick 1-click star rating — maximum response rate, low friction",
}

_REVIEW_FOLLOW_UP = [
    {"step": 1, "timing": "Day 0",  "action": "Send initial request via WhatsApp (most opened channel in India)"},
    {"step": 2, "timing": "Day 3",  "action": "Follow-up SMS if no response — keep it short, add review link directly"},
    {"step": 3, "timing": "Day 7",  "action": "Personal call or voice note from owner — highest conversion"},
    {"step": 4, "timing": "Day 14", "action": "Final gentle reminder email — mention how much reviews help small businesses"},
]

_INCENTIVE_IDEAS = [
    "5-10% discount on next purchase (disclose per platform rules)",
    "Early access to new product/feature",
    "Free add-on service with next booking",
    "Entry into monthly lucky draw (keep the prize meaningful)",
    "Shoutout on your social media page (works well for proud SMB owners)",
]

_WHATSAPP_TEMPLATES = {
    "b2c_warm": """{greeting} {customer_name}! 🙏

Thank you for choosing {business_name} — we're so glad you loved your experience with {product_service}!

We'd be really grateful if you could spare 2 minutes to leave us a review on {platform_name}. Your words help other customers like you find us, and they mean the world to our small team 😊

👉 {review_link}

It takes less than 2 minutes and helps us grow!

With gratitude,
{owner_name}
{business_name}""",

    "b2b_professional": """Hi {customer_name},

Hope you're doing well! It was a pleasure working with {business_name} on {product_service}.

As we continue to grow, reviews from valued clients like you make a significant difference. Would you mind sharing your experience on {platform_name}?

👉 {review_link}

If you'd prefer to share detailed feedback privately, simply reply to this message — we read every response personally.

Thank you for your trust,
{owner_name}
{business_name}""",

    "post_support": """Hi {customer_name}!

Glad we could resolve your concern today 😊 Our team works hard to make sure every customer is happy.

If you had a good experience with our support, a quick review would mean a lot to us:
👉 {review_link}

Takes less than a minute! Thank you 🙏
{business_name} Team""",
}

_EMAIL_TEMPLATES = {
    "review_request": {
        "subject_options": [
            "Your opinion matters to us, {customer_name}!",
            "Quick favour? Tell others about your experience 🙏",
            "How was your experience with {business_name}?",
            "2 minutes to help {business_name} grow — thank you!",
        ],
        "body": """Hi {customer_name},

Thank you for being a valued customer of {business_name}!

We hope you're enjoying {product_service}. Your experience and feedback are incredibly important to us — and to other customers who are looking for trusted businesses like ours.

Would you mind leaving a quick review on {platform_name}? It only takes 2 minutes and helps us serve more customers like you.

⭐ Leave a Review: {review_link}

Your honest feedback helps us improve and helps other customers make informed decisions.

Warm regards,
{owner_name}
{business_name}
{owner_phone}""",
    },
    "testimonial_request": {
        "subject_options": [
            "Can we feature your success story, {customer_name}?",
            "Would you share what {business_name} did for you?",
            "Your story could help others — share your experience?",
        ],
        "body": """Hi {customer_name},

We love seeing our customers succeed, and we'd love to share YOUR story!

Would you be willing to share a short testimonial about your experience with {product_service}? It can be:

✍️ A written quote (2-4 sentences)
🎥 A short 30-second WhatsApp video
📝 A Google/JustDial review

Either way works perfectly for us! If you're open to it, simply:
- Reply to this email with your written testimonial, OR
- Send a WhatsApp voice note/video to {owner_phone}, OR
- Leave a review here: {review_link}

With much gratitude,
{owner_name}
{business_name}""",
    },
}

_SMS_TEMPLATES = {
    "review": "{business_name}: Hi {customer_name}! Thank you for choosing us 😊 We'd love your review: {review_link} — takes 1 min! Thank you 🙏",
    "reminder": "{business_name}: Quick reminder — your review would mean the world to us! {review_link} Thank you {customer_name} 🙏",
}


# ── Round 17: Instagram Reel Script Writer ────────────────────────────────────

_REEL_STYLES = {
    "educational": {
        "label": "Educational / Tips",
        "hook_formula": "Did you know [surprising fact about {topic}]?",
        "structure": ["Hook (0-3s)", "Problem (3-8s)", "Solution step 1 (8-15s)", "Solution step 2 (15-22s)", "CTA (22-30s)"],
        "tone": "informative, friendly",
    },
    "storytelling": {
        "label": "Storytelling / Journey",
        "hook_formula": "From [struggle] to [success] — here's my story.",
        "structure": ["Hook / before (0-3s)", "The struggle (3-10s)", "The turning point (10-20s)", "The result (20-27s)", "CTA (27-30s)"],
        "tone": "emotional, authentic",
    },
    "product_showcase": {
        "label": "Product Showcase",
        "hook_formula": "Wait until you see what [product] can do in 30 seconds.",
        "structure": ["Product reveal (0-3s)", "Feature 1 demo (3-10s)", "Feature 2 demo (10-18s)", "Result / transformation (18-26s)", "CTA + price/offer (26-30s)"],
        "tone": "exciting, benefit-focused",
    },
    "behind_scenes": {
        "label": "Behind the Scenes",
        "hook_formula": "Ever wondered how we make [product/service]? Watch this.",
        "structure": ["Curiosity hook (0-3s)", "Process step 1 (3-12s)", "Process step 2 (12-20s)", "Final reveal (20-27s)", "CTA (27-30s)"],
        "tone": "candid, transparent",
    },
    "testimonial": {
        "label": "Customer Testimonial",
        "hook_formula": "[Customer name] couldn't believe what happened after [action].",
        "structure": ["Customer intro (0-5s)", "Before state (5-12s)", "The experience (12-22s)", "Result / quote (22-28s)", "CTA (28-30s)"],
        "tone": "relatable, trust-building",
    },
    "trending": {
        "label": "Trending / Challenge",
        "hook_formula": "POV: You just discovered [brand/product] 🤯",
        "structure": ["Trend hook (0-2s)", "Brand connection (2-8s)", "Key message (8-22s)", "Punchline (22-28s)", "CTA (28-30s)"],
        "tone": "fun, energetic",
    },
}

_REEL_GOALS = {
    "awareness": {"cta": "Follow us for more tips!", "metric": "reach & saves"},
    "engagement": {"cta": "Comment your thoughts below 👇", "metric": "comments & shares"},
    "leads": {"cta": "DM us 'INFO' to get started", "metric": "DM inquiries"},
    "sales": {"cta": "Link in bio — limited offer!", "metric": "link clicks & conversions"},
    "trust": {"cta": "Save this for later 📌", "metric": "saves & profile visits"},
}

_REEL_HOOKS = {
    "educational": [
        "Nobody tells you this about {topic}...",
        "{number} things you didn't know about {topic}",
        "Stop doing this if you want {benefit}",
        "The truth about {topic} (that experts hide)",
    ],
    "storytelling": [
        "I almost quit, then this happened...",
        "We went from ₹0 to ₹{revenue} doing this one thing",
        "This mistake cost us ₹{loss}. Don't repeat it.",
        "How a small {business_type} from {city} changed everything",
    ],
    "product_showcase": [
        "You won't believe what this does in 30 seconds",
        "Before vs After using {product} 👀",
        "We just launched something that changes {topic} forever",
        "The only {product_type} you'll ever need",
    ],
    "behind_scenes": [
        "How we actually make {product} (no filters)",
        "A day in our {business_type} — unfiltered",
        "What really goes on behind the scenes at {business_name}",
        "This is how {product} is made (step by step)",
    ],
    "testimonial": [
        "She thought it wouldn't work. Then she tried {product}.",
        "Real customer. Real results. Watch this.",
        "We asked our customer to review us honestly. Here's what they said.",
        "{customer_name} couldn't believe the difference.",
    ],
    "trending": [
        "POV: You just found the best {business_type} in {city} 🤯",
        "Tell me you run a {business_type} without telling me 😂",
        "Things {business_type} owners know to be true #relatable",
        "Day in the life of a {business_type} owner in India 🇮🇳",
    ],
}

_CAPTION_TEMPLATES = {
    "educational": "✨ {hook}\n\nHere's what most {audience} don't realise about {topic}:\n\n1️⃣ {point1}\n2️⃣ {point2}\n3️⃣ {point3}\n\nSave this post so you don't forget! 📌\n\n{cta}\n\n{hashtags}",
    "storytelling": "📖 {hook}\n\n{story_line}\n\nThe lesson? {lesson}\n\nHave you experienced something similar? Drop it in the comments 👇\n\n{cta}\n\n{hashtags}",
    "product_showcase": "🔥 {hook}\n\n{product_name} — {usp}\n\n✅ {benefit1}\n✅ {benefit2}\n✅ {benefit3}\n\n{cta}\n\n{hashtags}",
    "behind_scenes": "👀 {hook}\n\nWe're pulling back the curtain on how {business_name} works.\n\nBecause transparency builds trust.\n\n{cta}\n\n{hashtags}",
    "testimonial": "❤️ Real words from a real customer.\n\n\"{quote}\"\n— {customer}, {customer_city}\n\nReady for results like these? {cta}\n\n{hashtags}",
    "trending": "😅 {hook}\n\n{business_name} keeping it real for all the {audience} out there.\n\nTag someone who needs to see this! 👇\n\n{cta}\n\n{hashtags}",
}

_HASHTAG_SETS = {
    "retail": ["#IndianRetail", "#ShopLocal", "#MadeInIndia", "#SmallBusiness", "#RetailIndia", "#IndianShopping"],
    "food": ["#FoodBusiness", "#IndianFood", "#FoodEntrepreneur", "#HomeChef", "#FoodStartup", "#FoodLoversIndia"],
    "services": ["#IndianServices", "#SMEIndia", "#BusinessIndia", "#Entrepreneur", "#StartupIndia", "#ServiceProvider"],
    "technology": ["#TechIndia", "#StartupIndia", "#IndianTech", "#SaaSIndia", "#TechEntrepreneur", "#DigitalIndia"],
    "education": ["#EdTech", "#LearningIndia", "#IndianEducation", "#SkillIndia", "#OnlineLearning", "#EduContent"],
    "health": ["#HealthIndia", "#Wellness", "#IndianHealth", "#FitIndia", "#HealthyLiving", "#WellnessIndia"],
    "finance": ["#FinanceIndia", "#MoneyTips", "#IndianFinance", "#PersonalFinance", "#FinancialFreedom", "#InvestIndia"],
    "fashion": ["#IndianFashion", "#FashionIndia", "#OOTD", "#StyleIndia", "#FashionBlogger", "#IndianDesigner"],
}

_VOICEOVER_GUIDES = {
    30: {"words": "75-90 words", "pace": "brisk — 2.5 words/second", "pauses": "1 pause after hook"},
    60: {"words": "130-150 words", "pace": "natural — 2 words/second", "pauses": "2-3 pauses at transitions"},
    90: {"words": "180-210 words", "pace": "relaxed — 2 words/second", "pauses": "3-4 pauses for emphasis"},
}

_VISUAL_DIRECTION = {
    "educational": ["Text overlay on each tip", "Clean background or workspace", "Point-to-camera moments", "Simple B-roll of product/process"],
    "storytelling": ["Before photo / throwback clip", "Behind-the-scenes footage", "Candid team moments", "Progress shots over time"],
    "product_showcase": ["Close-up product shots", "Usage demo clips", "Before vs after split screen", "Satisfied customer clip"],
    "behind_scenes": ["Raw footage — no heavy editing", "Process shots (hands at work)", "Candid team moments", "Time-lapse of production"],
    "testimonial": ["Customer video clip or photo", "Product in use", "Results / transformation shot", "Happy customer moment"],
    "trending": ["Trending audio synced to visuals", "Quick cuts every 2-3 seconds", "Text memes / POV overlay", "Reaction clips"],
}


# ── Round 18: YouTube Description & Tags Generator ───────────────────────────

_YT_CATEGORIES = {
    "education":    {"emoji": "📚", "tags": ["tutorial", "howto", "learn", "tips", "explained", "guide"]},
    "business":     {"emoji": "💼", "tags": ["business", "entrepreneur", "startup", "marketing", "growth", "strategy"]},
    "finance":      {"emoji": "💰", "tags": ["finance", "investing", "money", "savings", "tax", "wealth"]},
    "technology":   {"emoji": "💻", "tags": ["tech", "software", "coding", "AI", "digital", "gadgets"]},
    "health":       {"emoji": "🏥", "tags": ["health", "wellness", "fitness", "nutrition", "lifestyle", "yoga"]},
    "food":         {"emoji": "🍛", "tags": ["recipe", "cooking", "food", "indianfood", "homemade", "chef"]},
    "travel":       {"emoji": "✈️", "tags": ["travel", "india", "vlog", "explore", "tourism", "wanderlust"]},
    "entertainment":{"emoji": "🎬", "tags": ["entertainment", "funny", "comedy", "viral", "trending", "shorts"]},
}

_YT_END_SCREEN_TEMPLATES = [
    "📺 Watch next: [your most relevant video]",
    "🔔 Subscribe for weekly [topic] videos",
    "▶️ Playlist: [related playlist name]",
    "👍 If this helped, smash the like button!",
]

_YT_CHAPTER_INTRO = "⏱️ CHAPTERS (click to jump):\n"

_YT_DESCRIPTION_TEMPLATE = """{hook}

{body}

{chapters_section}
─────────────────────────────────
{about_section}
─────────────────────────────────
🔔 SUBSCRIBE for more {category} content: {subscribe_cta}
👍 LIKE if this video helped you
💬 COMMENT your questions below

{links_section}
─────────────────────────────────
📌 RELATED VIDEOS & PLAYLISTS
• [Add your related video here]
• [Add your playlist here]

─────────────────────────────────
{tags_section}
"""

_YT_SEO_TITLE_FORMULAS = [
    "{topic} — Complete Guide for {audience} ({year})",
    "How to {topic} | Step-by-Step for {audience}",
    "{topic}: Everything You Need to Know (Hindi + English)",
    "Best {topic} Tips for Indian {audience} | {channel}",
    "{topic} Explained Simply | {audience} Guide",
]


# ── Round 19: LinkedIn Company Post Generator ─────────────────────────────────

_COMPANY_POST_TYPES = {
    "thought_leadership": {
        "label": "Thought Leadership",
        "hook_styles": [
            "The {industry} industry is changing. Here's what smart companies are doing.",
            "Unpopular opinion: {topic}",
            "We've been thinking about {topic} — and we need to talk.",
            "3 years ago, we said {topic} would change everything. We were right.",
        ],
        "structure": ["Bold opinion/observation", "Supporting evidence (2-3 points)", "What this means for the industry", "CTA for discussion"],
        "emoji_palette": ["💡", "🔍", "📊", "🎯", "🚀"],
    },
    "product_launch": {
        "label": "Product / Feature Launch",
        "hook_styles": [
            "Introducing {topic} — built for {audience}.",
            "Today is the day. We're launching {topic}.",
            "You asked. We built. Announcing {topic}.",
            "{company} just changed the way {audience} does {topic}.",
        ],
        "structure": ["Announcement hook", "What it is + key benefit", "Who it's for", "How to get access / CTA"],
        "emoji_palette": ["🎉", "🚀", "✨", "🎯", "🔥"],
    },
    "hiring": {
        "label": "Hiring / Talent",
        "hook_styles": [
            "We're growing — and we want you on the team.",
            "Dream job alert: {company} is hiring a {topic}.",
            "We don't just offer jobs. We offer careers. {company} is hiring.",
            "Big things are happening at {company} — and we need more builders.",
        ],
        "structure": ["Culture hook", "Role / what you'll work on", "What we offer", "How to apply / CTA"],
        "emoji_palette": ["👥", "🌟", "💼", "🤝", "🏆"],
    },
    "milestone": {
        "label": "Milestone / Achievement",
        "hook_styles": [
            "{topic} — we couldn't have done it without you.",
            "From zero to {topic}. Thank you.",
            "We hit a milestone we're proud of: {topic}.",
            "{company} just crossed {topic}. Here's how we got here.",
        ],
        "structure": ["Milestone announcement", "The journey / what it took", "Thank you to team / customers", "What's next + CTA"],
        "emoji_palette": ["🎊", "🏆", "💙", "🙏", "🚀"],
    },
    "culture": {
        "label": "Culture & Values",
        "hook_styles": [
            "At {company}, we believe {topic}.",
            "Culture isn't what you say. It's what you do. At {company}, this means {topic}.",
            "Behind every great product is a great team. Here's a peek inside {company}.",
            "We talk a lot about values. Here's one we actually live by.",
        ],
        "structure": ["Value statement / story hook", "A real example from the team", "Why this matters to us", "Invite others to share their values"],
        "emoji_palette": ["❤️", "🌱", "🤝", "💙", "✨"],
    },
    "case_study": {
        "label": "Customer Success / Case Study",
        "hook_styles": [
            "How {topic} helped a customer achieve [result].",
            "Real results. Real customer. Here's what {topic} did for them.",
            "Our customer had a problem. {company} had the answer.",
            "Before {topic}: [struggle]. After {topic}: [result].",
        ],
        "structure": ["Customer challenge hook", "What they tried before", "How your solution helped", "Measurable result + CTA"],
        "emoji_palette": ["📈", "✅", "💡", "🎯", "🤝"],
    },
}

_LINKEDIN_COMPANY_HASHTAGS = {
    "technology": ["#Tech", "#Innovation", "#SaaS", "#DigitalTransformation", "#Startup", "#BuildingInPublic"],
    "finance":    ["#Finance", "#Fintech", "#MoneyMatters", "#Banking", "#Investment", "#FinancialServices"],
    "retail":     ["#Retail", "#ECommerce", "#ConsumerBrands", "#CustomerExperience", "#Shopping", "#Retail"],
    "health":     ["#Healthcare", "#HealthTech", "#Wellness", "#MedTech", "#HealthcareInnovation", "#Pharma"],
    "education":  ["#EdTech", "#Education", "#Learning", "#FutureOfWork", "#Skills", "#Training"],
    "manufacturing": ["#Manufacturing", "#MakeInIndia", "#Industry40", "#Operations", "#SupplyChain", "#Engineering"],
}

_COMPANY_TONES = {
    "professional": "authoritative, clear, confident",
    "warm":         "human, approachable, story-driven",
    "bold":         "direct, provocative, opinionated",
    "inspiring":    "motivational, forward-looking, aspirational",
}

_COMPANY_CTA_MAP = {
    "thought_leadership": ["Share your take in the comments 👇", "What's your experience with this? Comment below.", "Tag someone who needs to read this.", "Follow {company} for more industry insights."],
    "product_launch":     ["Try it free → [link in bio]", "Request early access → [link]", "DM us 'LAUNCH' to get started.", "Visit our website to learn more → [link]"],
    "hiring":             ["Apply here → [link]", "Know someone great? Tag them below 👇", "DM us your LinkedIn profile.", "See all open roles → [link in bio]"],
    "milestone":          ["Thank you for being part of this journey 💙", "Share this if you've been rooting for us! 🙌", "Follow us for what's coming next.", "Drop a 🎉 if you want to celebrate with us!"],
    "culture":            ["Follow {company} to see more behind-the-scenes.", "What does your company culture look like? Share below 👇", "Tag a teammate who embodies this value.", "Join us → [careers page link]"],
    "case_study":         ["Read the full case study → [link]", "Could this help your business? DM us.", "See how we can help → [link in bio]", "Share if you know someone facing the same challenge 👇"],
}


# ── Round 20: Brand Voice Engine ─────────────────────────────────────────────

_BRAND_TONE_GUIDES = {
    "professional":   {"voice": "Authoritative, clear, data-backed", "avoid": "slang, exclamation marks, casual phrases", "cta_style": "direct and action-oriented"},
    "casual":         {"voice": "Friendly, conversational, approachable", "avoid": "jargon, corporate speak, passive voice", "cta_style": "inviting and low-pressure"},
    "inspirational":  {"voice": "Uplifting, story-driven, emotionally resonant", "avoid": "negativity, dry statistics without context", "cta_style": "community-driven and aspirational"},
    "educational":    {"voice": "Informative, structured, expert", "avoid": "assumptions, unsupported claims", "cta_style": "curiosity-driven and helpful"},
    "witty":          {"voice": "Clever, playful, punchy", "avoid": "overexplaining, being too serious, boring openers", "cta_style": "unexpected and memorable"},
    "empathetic":     {"voice": "Warm, understanding, human", "avoid": "clinical language, generic advice", "cta_style": "supportive and relatable"},
}

_CONTENT_PILLARS_BY_INDUSTRY = {
    "technology":    ["Product Innovations", "Industry Insights", "Behind the Build", "Customer Success", "Thought Leadership", "Team Culture"],
    "finance":       ["Market Insights", "Financial Tips", "Regulatory Updates", "Client Success Stories", "Investment Trends", "Team Expertise"],
    "healthcare":    ["Health Education", "Patient Stories", "Medical Innovations", "Team Spotlights", "Wellness Tips", "Research & Evidence"],
    "education":     ["Learning Tips", "Student Success", "Curriculum Updates", "Faculty Expertise", "Career Guidance", "Industry Partnerships"],
    "ecommerce":     ["Product Showcase", "Customer Stories", "Deals & Offers", "Behind the Scenes", "Style Inspiration", "Sustainability"],
    "food":          ["Recipe & Inspiration", "Chef's Specials", "Farm to Table", "Customer Reviews", "Festival Specials", "Team Stories"],
    "real_estate":   ["Property Listings", "Market Trends", "Client Testimonials", "Investment Tips", "Neighbourhood Guides", "Team Milestones"],
    "consulting":    ["Case Studies", "Industry Reports", "Framework Explainers", "Team Thought Leadership", "Client Results", "Webinar Recaps"],
    "manufacturing": ["Product Quality", "Innovation Process", "CSR Initiatives", "Industry Standards", "Team Skills", "Supply Chain Insights"],
}

_POSTING_SCHEDULE = {
    "instagram": {"best_days": ["Tuesday", "Wednesday", "Friday"], "best_times": ["8–9 AM", "12–1 PM", "7–9 PM"], "frequency": "1–2 posts/day"},
    "linkedin":  {"best_days": ["Tuesday", "Wednesday", "Thursday"], "best_times": ["8–10 AM", "12 PM", "5–6 PM"], "frequency": "3–5 posts/week"},
    "twitter":   {"best_days": ["Tuesday", "Wednesday", "Thursday"], "best_times": ["9 AM", "12–1 PM", "5–6 PM"], "frequency": "3–5 tweets/day"},
    "facebook":  {"best_days": ["Wednesday", "Thursday", "Friday"], "best_times": ["1–4 PM"], "frequency": "1 post/day"},
    "whatsapp":  {"best_days": ["Monday", "Wednesday", "Saturday"], "best_times": ["10–11 AM", "7–8 PM"], "frequency": "2–3 broadcasts/week"},
}


# ── Round 21: Bulk Post Generator ────────────────────────────────────────────

_BULK_FORMATS = {
    "instagram": {
        "hooks": ["🔥", "💡", "✅", "🚀", "🎯", "👇", "⚡", "🌟", "💪", "🤔"],
        "structures": [
            "{hook} {headline}\n\n{body}\n\n{cta}\n\n{hashtags}",
            "{hook} {question}\n\n→ {point1}\n→ {point2}\n→ {point3}\n\n{cta}\n\n{hashtags}",
            "{hook} Here's what nobody tells you about {topic}:\n\n{body}\n\nSave this post 📌\n\n{hashtags}",
        ],
    },
    "linkedin": {
        "hooks": ["", "", "", "", ""],
        "structures": [
            "{headline}\n\n{body}\n\n{cta}\n\n#{tag1} #{tag2} #{tag3}",
            "Most people get {topic} wrong.\n\nHere's the truth:\n\n{body}\n\nWhat's your take? 👇\n\n#{tag1} #{tag2}",
            "I've seen {topic} transform businesses.\n\nHere's what works:\n\n→ {point1}\n→ {point2}\n→ {point3}\n\n{cta}\n\n#{tag1} #{tag2}",
        ],
    },
    "twitter": {
        "structures": [
            "{headline} 🧵\n\n{body}\n\n#{tag1}",
            "{hook} {headline}\n\n{body} (1/3)",
            "Hot take on {topic}: {body}\n\n#{tag1} #{tag2}",
        ],
    },
    "whatsapp": {
        "structures": [
            "Hi! 👋\n\n{headline}\n\n{body}\n\nReply YES to know more!",
            "Quick tip from {company}! 💡\n\n{body}\n\n{cta}",
        ],
    },
}

_BULK_TOPICS = {
    "technology":    ["AI automation", "cloud security", "digital transformation", "SaaS productivity", "remote team tools", "API integrations", "no-code platforms", "cybersecurity basics", "data privacy", "startup tech stack"],
    "finance":       ["tax planning tips", "investment basics", "GST compliance", "cash flow management", "working capital", "startup funding", "financial ratios", "budgeting hacks", "TDS rules", "MSME benefits"],
    "healthcare":    ["preventive care", "patient journey", "telemedicine", "mental wellness", "nutrition tips", "healthcare innovation", "doctor-patient trust", "health insurance", "clinical trials", "medical AI"],
    "education":     ["learning hacks", "EdTech trends", "exam preparation", "career guidance", "skill development", "online learning", "student success", "campus culture", "teaching innovation", "future of work"],
    "ecommerce":     ["product photography", "return policy tips", "customer reviews", "festive sale planning", "D2C branding", "packaging design", "quick commerce", "loyalty programs", "cart abandonment", "social commerce"],
    "food":          ["recipe ideas", "food safety", "sustainable sourcing", "festival specials", "kitchen tips", "food trends 2025", "nutrition facts", "chef secrets", "farm to fork", "zero waste cooking"],
    "real_estate":   ["home buying tips", "property valuation", "rental yield", "RERA compliance", "home loans", "interior design trends", "smart home tech", "investment zones", "property documents", "NRI investment"],
    "consulting":    ["client management", "proposal writing", "thought leadership", "billing best practices", "niche expertise", "case study format", "referral strategies", "pricing models", "project delivery", "team scaling"],
}

_CTAS = [
    "Follow {company} for more →", "Save this for later 📌", "Share with someone who needs this 👇",
    "Comment your thoughts below 💬", "DM us to learn more →", "Link in bio for the full guide →",
    "Tag a friend who needs this 👇", "What's your experience? Tell us below →",
    "Book a free consultation → [link]", "Subscribe for weekly tips →",
]


# ── R22: Product Launch Kit ──────────────────────────────────────────────────

_LAUNCH_PHASES = {
    "pre_launch": {
        "label": "Pre-Launch (7–14 days before)",
        "goal": "Build anticipation and grow waitlist",
        "hooks": ["Coming soon teaser", "Behind-the-scenes build", "Problem statement post", "Countdown post", "Early-access signup CTA"],
    },
    "launch_day": {
        "label": "Launch Day",
        "goal": "Maximum reach and conversions",
        "hooks": ["Big announcement post", "Founder story", "Key benefit highlight", "Social proof teaser", "Limited-time offer"],
    },
    "post_launch": {
        "label": "Post-Launch (days 2–14)",
        "goal": "Sustain momentum and drive reviews",
        "hooks": ["First-user testimonial request", "FAQ post", "Feature spotlight", "Use-case story", "Thank-you post"],
    },
}

_LAUNCH_PLATFORMS = {
    "instagram": {"char_limit": 2200, "format": "visual-first with emoji, line breaks, 5–10 hashtags"},
    "linkedin":  {"char_limit": 1300, "format": "professional narrative, 3–5 bullet points, 3 hashtags"},
    "twitter":   {"char_limit": 280,  "format": "punchy, one strong hook, 1–2 hashtags"},
    "whatsapp":  {"char_limit": 1000, "format": "conversational, broadcast-ready, no hashtags"},
}

_LAUNCH_EMAIL_TEMPLATES = {
    "waitlist_confirmation": "Subject: You're on the list 🎉 | Body: Confirm interest + what to expect",
    "launch_day_blast":      "Subject: It's here! [Product] is live | Body: CTA + benefit summary",
    "follow_up":             "Subject: Did you miss [Product]? | Body: Last chance + social proof",
}


# ── R23: Bio Optimizer ────────────────────────────────────────────────────────

_BIO_LIMITS = {
    "instagram": {"chars": 150, "lines": 5, "cta": "Link in bio"},
    "linkedin":  {"chars": 220, "lines": 3, "cta": "Connect / DM"},
    "twitter":   {"chars": 160, "lines": 2, "cta": "Follow for tips"},
    "youtube":   {"chars": 1000,"lines": 8, "cta": "Subscribe"},
}

_BIO_KEYWORDS_BY_INDUSTRY = {
    "technology":    ["Tech | AI | SaaS", "Building", "Founder", "Engineer", "Product"],
    "finance":       ["CA | CFA | Finance", "Wealth", "Investing", "Tax", "Money"],
    "marketing":     ["Growth | Marketing", "Brand", "Digital", "Content", "ROI"],
    "education":     ["Educator | Mentor", "Learning", "Coaching", "Skills", "Career"],
    "health":        ["Health | Wellness", "Coach", "Nutrition", "Fitness", "Mindset"],
    "ecommerce":     ["Founder | D2C", "Building", "Products", "Brand", "Entrepreneur"],
    "consulting":    ["Consultant | Advisor", "Strategy", "Growth", "Expert", "10+ years"],
    "creative":      ["Creator | Designer", "Visual", "Storyteller", "Brand", "Studio"],
}

_BIO_EMOJI_SETS = {
    "professional": ["💼", "📊", "🎯", "✅", "🔹"],
    "creative":     ["🎨", "✨", "🌟", "💡", "🎬"],
    "energetic":    ["🚀", "⚡", "🔥", "💪", "🌍"],
    "warm":         ["🙏", "❤️", "🌱", "🤝", "💛"],
}


# ── R24: Comment Reply Generator ─────────────────────────────────────────────

_COMMENT_TYPES = {
    "praise":      {"intent": "positive feedback", "goal": "amplify goodwill, invite engagement"},
    "question":    {"intent": "seeking information","goal": "answer helpfully, drive to DM or link"},
    "complaint":   {"intent": "negative experience","goal": "acknowledge, apologise, resolve offline"},
    "troll":       {"intent": "hostile/baiting",    "goal": "de-escalate, not engage, stay classy"},
    "spam":        {"intent": "irrelevant promo",   "goal": "brief polite decline, no engagement"},
    "general":     {"intent": "neutral comment",    "goal": "warm reply, keep conversation going"},
    "competitor":  {"intent": "comparison/rivalry", "goal": "confident, non-defensive, value-led"},
}

_COMMENT_TONES = {
    "professional": "formal yet warm, no slang",
    "friendly":     "casual, use emojis sparingly, conversational",
    "witty":        "clever, light humour, punchy",
    "empathetic":   "sensitive, validating, human first",
}

_COMMENT_REPLY_STARTERS = {
    "praise":    ["Thank you so much 🙏", "This made our day! 😊", "We really appreciate this ❤️", "Means a lot to us!"],
    "question":  ["Great question!", "Happy to help!", "Sure — here's the answer:", "Absolutely! 👇"],
    "complaint": ["We're really sorry to hear this 🙏", "That's not the experience we want for you.", "We sincerely apologise.", "Thank you for flagging this."],
    "troll":     ["We hear you.", "Thanks for sharing your thoughts.", "We appreciate all feedback.", "Noted!"],
    "general":   ["Thanks for stopping by! 😊", "Glad you're here!", "Love seeing this! ❤️", "Always great to hear from you!"],
    "competitor":["We're proud of what we've built!", "Every brand has its strengths 💪", "We'd love to show you why our users stay!", "Check out what makes us different 👇"],
}


# ── R25: Facebook Post Adapter ────────────────────────────────────────────────

_FB_POST_TYPES = {
    "awareness":    {"cta": "Save this post!", "emoji_set": ["📢","💡","🔔","👀"], "length": "medium"},
    "engagement":   {"cta": "Drop a comment below! 👇", "emoji_set": ["💬","🤔","❤️","🙌"], "length": "short"},
    "sale":         {"cta": "DM us or click the link in bio!", "emoji_set": ["🔥","💥","🎉","💰"], "length": "medium"},
    "story":        {"cta": "Share with someone who needs this!", "emoji_set": ["✨","🌟","💫","🙏"], "length": "long"},
    "educational":  {"cta": "Save & share with your team!", "emoji_set": ["📚","💡","🧠","✅"], "length": "long"},
    "testimonial":  {"cta": "See more reviews in our highlights!", "emoji_set": ["⭐","🏆","❤️","🙏"], "length": "short"},
}

_FB_AUDIENCE_HOOKS = {
    "b2c":      ["Did you know…", "Here's something most people miss:", "This changed everything for us:", "Stop scrolling — this is for you:"],
    "b2b":      ["For business owners only:", "Here's what the data says:", "We've helped 500+ businesses:", "Most founders overlook this:"],
    "local":    ["Chennai friends, listen up! 👋", "Coimbatore ke log, sunte ho?", "Our city deserves better.", "Proud to serve [City]!"],
    "youth":    ["Okay real talk —", "No cap,", "Lowkey, this hits different:", "POV: you finally found it 👇"],
}

_FB_HASHTAG_SETS = {
    "business":   ["#SmallBusiness", "#Entrepreneur", "#BusinessGrowth", "#StartupIndia", "#MSME"],
    "lifestyle":  ["#DailyLife", "#MadeInIndia", "#IndianBrand", "#SupportLocal", "#ShopSmall"],
    "education":  ["#LearnSomethingNew", "#DidYouKnow", "#TipsAndTricks", "#KnowledgeIsPower"],
    "sale":       ["#Sale", "#Offer", "#Discount", "#LimitedTime", "#DealAlert"],
}

_FB_FORMATS = {
    "text_post":   "Plain engaging text with hooks, story, and CTA",
    "list_post":   "Numbered list or bullet format — easy to scan",
    "question":    "Curiosity-triggering question post to drive comments",
    "poll_intro":  "Intro text for a Facebook Poll post",
    "event_post":  "Event announcement post with date/time/venue",
    "share_post":  "Post designed to maximize shares/reshares",
}


# ── R26: Meme Caption Generator ───────────────────────────────────────────────

_MEME_TEMPLATES = {
    "drake":          {"panels": ["Reject (top)",   "Accept (bottom)"],   "style": "contrast"},
    "distracted_bf":  {"panels": ["BF = you",       "GF = old way",       "Other girl = new product"], "style": "triangle"},
    "two_buttons":    {"panels": ["Option A",        "Option B"],          "style": "dilemma"},
    "galaxy_brain":   {"panels": ["Basic thought",   "Smart thought",      "Galaxy brain thought"],     "style": "escalation"},
    "one_does_not":   {"panels": ["Caption"],                              "style": "single"},
    "this_is_fine":   {"panels": ["Caption"],                              "style": "single"},
    "gru_plan":       {"panels": ["Step 1","Step 2", "Step 3","Twist"],    "style": "plan"},
    "success_kid":    {"panels": ["Caption"],                              "style": "single"},
    "expanding_brain":{"panels": ["Basic","Better","Advanced","Galaxy"],   "style": "escalation"},
    "custom":         {"panels": ["Panel 1","Panel 2"],                    "style": "custom"},
}

_MEME_INDUSTRIES = {
    "ecommerce":  ["Sale season 🛒","Delivery delays","Returns process","Cart abandonment","Free shipping threshold"],
    "saas":       ["Pricing pages","Onboarding flows","'Works on my machine'","Feature requests","Sprint planning"],
    "ca":         ["Tax season","Audit prep","Client documents","Form 16","GST filing"],
    "startup":    ["Pitch deck","Runway","VC meetings","MVP vs perfect product","Pivoting"],
    "marketing":  ["Client feedback","Content calendar","Campaign results","'Make it pop'","Metrics"],
    "hr":         ["Monday morning","Meeting that could be email","Performance reviews","Leave requests","Team building"],
    "general":    ["WFH life","Coffee dependence","Inbox zero","Weekend work","Deadline crunch"],
}

_MEME_TONES = {
    "relatable":   "Universally understood workplace/life situation",
    "brand_promo": "Subtly promotes the brand while being funny",
    "educational": "Teaches something through humour",
    "industry":    "Inside joke for the target industry",
    "festive":     "Tied to a festival or seasonal moment",
}

_MEME_CAPTION_FORMATS = {
    "drake": [
        ("Not tracking ROI", "Blaming the algorithm when sales drop"),
        ("Spending 3 hours on Canva", "Taking 2 minutes with our tool"),
        ("Checking email every 5 minutes", "Using automated workflows"),
    ],
    "two_buttons": [
        ("Post consistently", "Sleep"),
        ("Follow up with the lead", "Wait for them to call back"),
    ],
    "gru_plan": [
        ("Make a plan", "Execute the plan", "Plan works perfectly", "Client asks for changes"),
        ("Launch the product", "Get good reviews", "Scale marketing", "Server crashes"),
    ],
    "expanding_brain": [
        ("Using pen and paper", "Using Excel", "Using CRM software", "Using AI-powered assistant"),
        ("Sending emails manually", "Using templates", "Using automation", "AI writes them for you"),
    ],
}


# ── R27: Story Highlights Planner ────────────────────────────────────────────

_SH_COVER_STYLES = {
    "minimal":    {"desc": "Clean icon on solid background", "tools": "Canva, Adobe Express"},
    "gradient":   {"desc": "Brand gradient with icon overlay", "tools": "Canva"},
    "photograph": {"desc": "Real photo as cover with text", "tools": "VSCO, Lightroom"},
    "illustrated":{"desc": "Custom illustrated icon style", "tools": "Procreate, Canva"},
    "branded":    {"desc": "Logo-forward with accent color", "tools": "Canva, Figma"},
}

_SH_STANDARD_CATEGORIES = {
    "about":      {"icon": "🏠", "stories": ["Founder story","Team intro","Office/workspace","Our mission","Behind the scenes"], "caption": "Everything about us"},
    "products":   {"icon": "🛍️", "stories": ["Product demos","Unboxing","Features walkthrough","New arrivals","How to use"], "caption": "What we make"},
    "reviews":    {"icon": "⭐", "stories": ["Customer reviews","Before & after","UGC reposts","Ratings screenshots","Video testimonials"], "caption": "What they say"},
    "faqs":       {"icon": "❓", "stories": ["Pricing FAQ","Shipping FAQ","Return policy","How to order","Contact FAQ"], "caption": "Got questions?"},
    "offers":     {"icon": "🔥", "stories": ["Ongoing deals","Flash sales","Coupon codes","Bundle offers","Seasonal offers"], "caption": "Latest deals"},
    "process":    {"icon": "⚙️", "stories": ["How we make it","Quality checks","Packaging","Delivery process","After-sales"], "caption": "How it works"},
    "team":       {"icon": "👥", "stories": ["Founder intro","Team members","Day in the life","Culture moments","Hiring"], "caption": "Our people"},
    "events":     {"icon": "📅", "stories": ["Live events","Webinars","Exhibitions","Award ceremonies","Meetups"], "caption": "Events"},
    "tips":       {"icon": "💡", "stories": ["How-to guides","Pro tips","Hacks","Did you know","Industry trends"], "caption": "Tips & tricks"},
    "press":      {"icon": "📰", "stories": ["News features","Podcast appearances","Awards","Media coverage","Collaborations"], "caption": "In the news"},
    "reels":      {"icon": "🎬", "stories": ["Best reels","Trending videos","Behind the reel","BTS","Collab reels"], "caption": "Watch & enjoy"},
    "contact":    {"icon": "📞", "stories": ["WhatsApp link","Email ID","Store location","Working hours","How to reach us"], "caption": "Reach us"},
}

_SH_INDUSTRY_EXTRAS = {
    "fashion":   ["sizing_guide","styling_tips","lookbook","collection","care_instructions"],
    "food":      ["menu","chef_specials","ingredients","delivery_zones","combo_deals"],
    "fitness":   ["workout_plans","transformation","schedule","challenges","nutrition"],
    "education": ["courses","student_wins","curriculum","faculty","placement"],
    "realestate":["projects","floor_plans","site_visits","emi_calculator","testimonials"],
    "beauty":    ["tutorials","before_after","ingredients","skincare_routine","reviews"],
    "b2b":       ["case_studies","clients","pricing","integration","demo_booking"],
}

_SH_CONTENT_CALENDAR = {
    "weekly":  ["Monday Motivation", "Product spotlight mid-week", "Customer story Friday", "Weekend offer"],
    "monthly": ["Month theme announcement", "Big reveal / launch", "Review roundup", "Month wrap-up"],
}


# ── R28: Twitter/X Thread Generator ──────────────────────────────────────────

_THREAD_HOOKS = {
    "controversial":  "Most people are wrong about {topic}. Here's the truth 🧵",
    "story":          "I {verb} {topic} for {duration}. Here's what I learned 🧵",
    "listicle":       "{number} things about {topic} no one talks about 🧵",
    "how_to":         "How to {topic} — a complete guide in {number} tweets 🧵",
    "hot_take":       "Unpopular opinion: {topic} 🧵",
    "mistake":        "I made a ₹{amount} mistake with {topic}. Don't do what I did 🧵",
    "breakdown":      "Breaking down {topic} so anyone can understand it 🧵",
    "vs":             "{option_a} vs {option_b} — the honest comparison 🧵",
}

_THREAD_TWEET_TYPES = {
    "hook":        "Attention-grabbing opener — makes them click 'Show more'",
    "context":     "Brief background / why this matters",
    "main_point":  "Core insight or argument",
    "example":     "Real-world example or data point",
    "counter":     "Acknowledge the counterargument, then rebut",
    "practical":   "Actionable takeaway / how-to step",
    "stat":        "Surprising statistic or fact",
    "quote":       "Relevant quote from an expert or customer",
    "cta":         "Call to action — like, retweet, follow, reply",
}

_THREAD_STRUCTURES = {
    "educational": ["hook","context","main_point","main_point","example","stat","practical","practical","cta"],
    "story":       ["hook","context","main_point","example","counter","practical","cta"],
    "listicle":    ["hook","context","main_point","main_point","main_point","main_point","main_point","cta"],
    "opinion":     ["hook","main_point","counter","main_point","stat","practical","cta"],
}

_THREAD_HASHTAG_RULES = {
    "startup":    ["#StartupIndia","#Entrepreneur","#Founders","#BuildInPublic","#IndianStartup"],
    "marketing":  ["#MarketingTips","#DigitalMarketing","#ContentMarketing","#GrowthHacking"],
    "finance":    ["#PersonalFinance","#InvestingIndia","#MoneyMatters","#FinanceTips"],
    "tech":       ["#TechTwitter","#SaaS","#ProductManagement","#IndianTech"],
    "general":    ["#Thread","#TIL","#LearnOnTwitter","#KnowledgeBomb"],
}

_THREAD_ENGAGEMENT_TIPS = [
    "Post first tweet standalone — let it get some engagement before replies chain",
    "Number each tweet: '1/', '2/', etc. — makes threads easy to follow",
    "Add an image or chart to tweet #2 — visuals 3× engagement",
    "End with a question in the CTA — drives replies which boost algorithm",
    "Retweet your own thread's first tweet 12–24h later to revive reach",
    "Best time to post threads: Tuesday–Thursday, 7–9am or 5–7pm IST",
    "Quote-tweet your thread in a summary tweet 3 days later for second wind",
]


def generate_festive_post(
    brand_name: str,
    festival: str = "diwali",
    post_angle: str = "appreciation",
    industry: str = "general",
    offer_text: str = "",
    tip_text: str = "",
    prize_text: str = "",
    custom_festival_name: str = "",
    language: str = "en",
) -> dict:
    fest = _FESTIVE_CALENDAR.get(festival, _FESTIVE_CALENDAR["custom"])
    fest_name = custom_festival_name if festival == "custom" else fest["name"]
    emoji = fest["emoji"]
    vibe  = fest["vibe"]

    scripts = _FESTIVE_SCRIPTS.get(festival, _FESTIVE_SCRIPTS["generic"])
    template = scripts.get(post_angle, _FESTIVE_SCRIPTS["generic"].get(post_angle, _FESTIVE_SCRIPTS["generic"]["appreciation"]))

    post_text = template.format(
        brand=brand_name, festival=fest_name, emoji=emoji, vibe=vibe,
        industry=industry, offer=offer_text or "Exclusive festival discount",
        tip=tip_text or f"Plan your {industry} goals for the coming year",
        prize=prize_text or "exciting goodies", draw_date="after the festival",
        years="78", topic=fest_name,
    )

    return {
        "brand_name":    brand_name,
        "festival":      fest_name,
        "emoji":         emoji,
        "month":         fest["month"],
        "vibe":          vibe,
        "post_angle":    post_angle,
        "post_text":     post_text,
        "hashtags":      fest.get("hashtags", [f"#{festival}", f"#{festival}Sale", f"#{brand_name}"]),
        "full_post":     f"{post_text}\n\n{' '.join(fest.get('hashtags', [f'#{festival}', f'#{festival}Wishes'])[:6])}",
        "platform_tips": {
            "instagram": "Post 30 min before prime time (7–9pm). Add to Stories with countdown sticker.",
            "facebook":  "Boost post to 10km radius for ₹200–500/day — festive CPMs are high but conversions too.",
            "whatsapp":  "Send to broadcast list — festive forwards have highest open rates of the year.",
            "linkedin":  "Brand story angle works best on LinkedIn — keep it professional yet warm.",
        },
        "posting_schedule": {
            "eve":       f"Appreciation / brand story the day before {fest_name}",
            "day_of":    f"Offer / contest on {fest_name} morning (7–9am)",
            "follow_up": "Thank you story 2 days after",
        },
        "design_tips": [
            f"Use {vibe.split(',')[0]} color palette — match the festival mood",
            "Add your logo at bottom right corner",
            "Use festive frames/borders from Canva — free templates available",
            "Keep text minimal — let the visual carry the emotion",
        ],
        "all_angles": {"appreciation": "Brand warmth", "offer": "Festival discount", "contest": "Giveaway", "story": "Behind the scenes", "tips": "Festive tips"},
    }


def generate_twitter_thread(
    brand_name: str,
    topic: str,
    thread_type: str = "educational",
    industry: str = "general",
    num_tweets: int = 8,
    include_hook_variants: bool = True,
    language: str = "en",
) -> dict:
    structure = _THREAD_STRUCTURES.get(thread_type, _THREAD_STRUCTURES["educational"])
    hashtags  = _THREAD_HASHTAG_RULES.get(industry, _THREAD_HASHTAG_RULES["general"])

    # Build tweet sequence
    tweets = []
    for i, tweet_type in enumerate(structure[:num_tweets]):
        tweet_info = _THREAD_TWEET_TYPES.get(tweet_type, "")
        num_label  = f"{i+1}/" if i > 0 else "🧵"

        if tweet_type == "hook":
            text = f"🧵 THREAD: {topic}\n\nIf you're in {industry}, you need to read this."
        elif tweet_type == "context":
            text = f"2/ First, let's set the context.\n\n{topic} affects every {industry} business. Yet most founders never think about it until it's too late."
        elif tweet_type == "main_point":
            point_num = sum(1 for t in structure[:i+1] if t == "main_point")
            text = f"{i+1}/ Key insight #{point_num}:\n\n[Your core point about {topic} here — make it specific and surprising]"
        elif tweet_type == "example":
            text = f"{i+1}/ Real example:\n\nA {industry} founder I know dealt with this exact issue. Here's what happened: [your story]\n\nThe lesson? [one line takeaway]"
        elif tweet_type == "stat":
            text = f"{i+1}/ The data is clear:\n\n[Insert your statistic about {topic}]\n\nSource: [cite it — credibility matters on X]"
        elif tweet_type == "practical":
            text = f"{i+1}/ What to do about it:\n\n→ Step 1: [action]\n→ Step 2: [action]\n→ Step 3: [action]\n\nSimple. Repeatable. Works."
        elif tweet_type == "counter":
            text = f"{i+1}/ I know what you're thinking:\n\n'But {topic} doesn't apply to my business'\n\nHere's why you're wrong: [your rebuttal]"
        elif tweet_type == "quote":
            text = f"{i+1}/ As [Expert Name] once said:\n\n\"{topic} is one of the most underrated levers for growth.\"\n\nThey were right."
        elif tweet_type == "cta":
            text = f"{i+1}/ That's a wrap!\n\nIf this helped you:\n→ RT the first tweet to help others\n→ Follow @{brand_name.replace(' ','')} for more\n→ Reply with your take — I read every response 👇\n\n{' '.join(hashtags[:3])}"
        else:
            text = f"{i+1}/ [Tweet about {topic}]"

        tweets.append({
            "position":    i + 1,
            "type":        tweet_type,
            "type_desc":   tweet_info,
            "text":        text,
            "char_count":  len(text),
            "within_limit": len(text) <= 280,
        })

    # Hook variants
    hook_variants = []
    if include_hook_variants:
        for style, template in list(_THREAD_HOOKS.items())[:4]:
            hook_variants.append({
                "style": style,
                "text":  template.replace("{topic}", topic).replace("{verb}", "tested").replace("{duration}", "6 months").replace("{number}", str(num_tweets)).replace("{amount}", "50,000").replace("{option_a}", "Option A").replace("{option_b}", "Option B"),
            })

    return {
        "brand_name":       brand_name,
        "topic":            topic,
        "thread_type":      thread_type,
        "industry":         industry,
        "total_tweets":     len(tweets),
        "tweets":           tweets,
        "hook_variants":    hook_variants,
        "hashtags":         hashtags,
        "engagement_tips":  _THREAD_ENGAGEMENT_TIPS,
        "posting_strategy": {
            "spacing":    "Post all tweets as replies within 5 minutes of first tweet",
            "best_time":  "Tue–Thu, 7–9am or 5–7pm IST",
            "follow_up":  "Reply to every comment in first 2 hours to ride the algorithm",
            "repurpose":  "Turn the thread into a blog post, LinkedIn carousel, or Instagram slides",
        },
    }


def generate_story_highlights_plan(
    brand_name: str,
    industry: str = "general",
    brand_colors: str = "",
    num_highlights: int = 8,
    cover_style: str = "minimal",
    language: str = "en",
) -> dict:
    # Pick relevant categories
    base_cats = list(_SH_STANDARD_CATEGORIES.keys())
    industry_extras = _SH_INDUSTRY_EXTRAS.get(industry, [])

    # Pick top N highlights
    selected = base_cats[:num_highlights]

    highlights = []
    for cat in selected:
        cat_data = _SH_STANDARD_CATEGORIES[cat]
        highlights.append({
            "name":          cat.replace("_"," ").title(),
            "cover_icon":    cat_data["icon"],
            "cover_caption": cat_data["caption"],
            "story_ideas":   cat_data["stories"],
            "story_count_recommended": 5,
            "refresh_frequency": "Monthly" if cat in ("offers","events") else "Quarterly",
        })

    # Industry-specific add-ons
    extras = []
    for extra in industry_extras[:max(0, num_highlights - len(selected))]:
        extras.append({
            "name": extra.replace("_"," ").title(),
            "cover_icon": "📌",
            "cover_caption": extra.replace("_"," ").title(),
            "story_ideas": [f"Create {extra.replace('_',' ')} content tailored to {brand_name}"],
            "story_count_recommended": 3,
            "refresh_frequency": "Monthly",
        })

    cover_info = _SH_COVER_STYLES.get(cover_style, _SH_COVER_STYLES["minimal"])

    return {
        "brand_name":     brand_name,
        "industry":       industry,
        "cover_style":    cover_style,
        "cover_style_desc": cover_info["desc"],
        "design_tools":   cover_info["tools"],
        "brand_colors":   brand_colors or "Use your primary and secondary brand colors",
        "total_highlights": len(highlights) + len(extras),
        "highlights":     highlights,
        "industry_extras": extras,
        "cover_design_tips": [
            "All covers should look uniform — same background color family",
            "Use 1 icon per cover — avoid cluttered text",
            "Size: 1080×1920px (Stories format), but display as circle on profile",
            "Test how it looks as a circle before publishing",
            f"Recommended tools: {cover_info['tools']}",
            "Keep icon centered — circle crop cuts the edges",
        ],
        "content_calendar": _SH_CONTENT_CALENDAR,
        "strategy_tips": [
            "First 4–6 highlights are most visible — put your most important ones there",
            "Name highlights with 1–2 short words — long names get cut off on mobile",
            "Pin your 'Offers' highlight — it drives direct sales",
            "'Reviews' highlight is your social proof — keep it fresh monthly",
            "Archive Stories before they expire (24h) — use Instagram's Archive feature",
            "Story Highlights are permanent — update covers when rebranding",
            "Use consistent emoji in names: 🔥 Deals, ⭐ Reviews — looks polished",
        ],
        "highlight_refresh_plan": {
            "weekly":   "Add new Stories to Offers, Events, Reels",
            "monthly":  "Refresh Reviews, Tips, Process with new content",
            "quarterly":"Audit all highlights — remove outdated stories, update covers if brand changed",
        },
    }


def generate_meme_caption(
    brand_name: str,
    topic: str,
    meme_template: str = "drake",
    industry: str = "general",
    tone: str = "relatable",
    custom_panel_texts: list = None,
    language: str = "en",
) -> dict:
    template = _MEME_TEMPLATES.get(meme_template, _MEME_TEMPLATES["drake"])
    panels = template["panels"]
    style = template["style"]

    # Use custom texts if provided, otherwise pick from presets
    if custom_panel_texts and len(custom_panel_texts) >= len(panels):
        panel_captions = custom_panel_texts[:len(panels)]
    elif meme_template in _MEME_CAPTION_FORMATS:
        preset = _MEME_CAPTION_FORMATS[meme_template]
        panel_captions = list(preset[hash(topic) % len(preset)])
    else:
        # Generate generic captions based on topic
        industry_ideas = _MEME_INDUSTRIES.get(industry, _MEME_INDUSTRIES["general"])
        panel_captions = [f"Dealing with {topic}", f"Finding {brand_name}"]

    # Build output
    panel_map = {panels[i]: panel_captions[i] if i < len(panel_captions) else "" for i in range(len(panels))}

    caption_variants = [
        f"Tag someone who needs to see this 👇",
        f"Every {industry} person will relate to this 😅",
        f"Save this for later! You'll need it 📌",
        f"Which one are you? Comment below! 👇",
    ]
    post_caption = f"{caption_variants[hash(topic) % len(caption_variants)]}\n\n#{brand_name.replace(' ','')} #Meme #{industry.capitalize()} #RelateableMemes #Trending"

    hashtags = [
        f"#{brand_name.replace(' ','')}", "#MemeMarketing", "#FunnyButTrue",
        f"#{industry.capitalize()}", "#Trending", "#IndianStartup", "#SmallBusinessIndia",
    ]

    return {
        "brand_name":     brand_name,
        "topic":          topic,
        "meme_template":  meme_template,
        "template_style": style,
        "panel_labels":   panels,
        "panel_captions": panel_map,
        "full_caption_text": post_caption,
        "hashtags":       hashtags,
        "caption_hook_options": caption_variants,
        "design_tips": [
            "Use Canva Meme Maker or MemeFull.com to add your text to the template",
            "Keep text short — max 6 words per panel for readability",
            "Use bold white text with dark stroke for universal readability",
            "Add your logo subtly in one corner",
            "Don't over-explain — the punchline should land on its own",
        ],
        "posting_tips": [
            "Post memes on Wednesday or Thursday — mid-week peaks for humour content",
            "Memes get 60% more organic reach than product posts — use them weekly",
            "Avoid controversial topics — keep it safe and workplace-friendly",
            "Respond to every comment within 1 hour to ride the algorithm wave",
        ],
        "variants_for_platforms": {
            "instagram": "Square crop (1080×1080), add to Stories with poll sticker",
            "facebook":  "Landscape works well (1200×630), post in relevant groups too",
            "linkedin":  "Keep tone professional-funny — avoid slapstick on LinkedIn",
            "twitter":   "Add thread for context if the meme needs explanation",
            "whatsapp":  "Share in broadcast list — high forward rate for relatable memes",
        },
    }


def generate_facebook_post(
    brand_name: str,
    post_topic: str,
    post_type: str = "engagement",
    audience: str = "b2c",
    post_format: str = "text_post",
    product_or_offer: str = "",
    location: str = "",
    language: str = "en",
) -> dict:
    config = _FB_POST_TYPES.get(post_type, _FB_POST_TYPES["engagement"])
    hooks = _FB_AUDIENCE_HOOKS.get(audience, _FB_AUDIENCE_HOOKS["b2c"])
    hashtags = _FB_HASHTAG_SETS.get("business", []) + _FB_HASHTAG_SETS.get("lifestyle", [])

    hook = hooks[hash(post_topic) % len(hooks)]
    emoji1, emoji2 = config["emoji_set"][0], config["emoji_set"][1]
    cta = config["cta"]

    # Craft core body based on format
    if post_format == "list_post":
        body_lines = [
            f"{hook}",
            f"",
            f"Here are 5 reasons why {brand_name} stands out:",
            f"",
            f"1️⃣ Quality you can trust",
            f"2️⃣ Prices that make sense",
            f"3️⃣ Service that actually cares",
            f"4️⃣ {post_topic}",
            f"5️⃣ A brand that grows with you",
        ]
    elif post_format == "question":
        body_lines = [
            f"Quick question for you {emoji1}",
            f"",
            f"When it comes to {post_topic} — what matters most to you?",
            f"",
            f"A) Quality",
            f"B) Price",
            f"C) Speed",
            f"D) All of the above 😄",
        ]
    elif post_format == "poll_intro":
        body_lines = [
            f"We want to hear from YOU! {emoji1}",
            f"",
            f"Tell us about {post_topic}. Vote below and comment why! {emoji2}",
        ]
    elif post_format == "share_post":
        body_lines = [
            f"If this helped you, tag a friend who needs to see this {emoji1}",
            f"",
            f"{hook}",
            f"",
            f"{post_topic}",
            f"",
            f"Share this with someone it could help today 🙏",
        ]
    else:
        body_lines = [
            f"{hook}",
            f"",
            f"{emoji1} {post_topic}",
            f"",
            f"At {brand_name}, we believe every customer deserves the best.",
            f"{product_or_offer}" if product_or_offer else f"That's why we keep raising the bar every single day.",
        ]

    body_lines += ["", cta]
    if location:
        body_lines.append(f"📍 {location}")

    post_text = "\n".join(body_lines)
    hashtag_str = " ".join(hashtags[:8])

    full_post = f"{post_text}\n\n{hashtag_str}"

    return {
        "brand_name": brand_name,
        "post_type": post_type,
        "post_format": post_format,
        "audience": audience,
        "post_text": full_post,
        "character_count": len(full_post),
        "hashtags": hashtags[:8],
        "cta": cta,
        "best_time_to_post": {
            "weekday": "Tuesday–Thursday, 8–10am or 6–9pm IST",
            "weekend": "Saturday 10am–12pm IST",
            "avoid":   "Monday mornings and Sunday nights",
        },
        "fb_tips": [
            "Facebook prefers native video — add a relevant Reel if possible",
            "First 2 lines are critical — 'See More' hides the rest on mobile",
            "Posts with questions get 3× more comments",
            "Tag your location to boost local reach",
            "Reply to every comment within 1 hour for algorithm boost",
        ],
        "boost_suggestion": f"Boost this post for ₹200–₹500/day targeting {audience.upper()} within 25km of {location or 'your city'} for best ROI",
    }


def generate_comment_replies(
    brand_name: str,
    post_topic: str,
    comments: list,
    brand_tone: str = "friendly",
    platform: str = "instagram",
    include_cta: bool = True,
    language: str = "en",
) -> dict:
    tone_desc = _COMMENT_TONES.get(brand_tone, _COMMENT_TONES["friendly"])
    replies = []

    for i, comment_item in enumerate(comments[:10]):
        if isinstance(comment_item, dict):
            comment_text = comment_item.get("text", "")
            comment_type = comment_item.get("type", "general")
        else:
            comment_text = str(comment_item)
            comment_type = _detect_comment_type(comment_text)

        cfg = _COMMENT_TYPES.get(comment_type, _COMMENT_TYPES["general"])
        starters = _COMMENT_REPLY_STARTERS.get(comment_type, _COMMENT_REPLY_STARTERS["general"])
        starter = starters[i % len(starters)]

        reply = _craft_reply(
            starter=starter, comment=comment_text, brand=brand_name,
            topic=post_topic, comment_type=comment_type, platform=platform,
            include_cta=include_cta and comment_type in ["question", "praise", "general"],
            tone=brand_tone,
        )

        replies.append({
            "original_comment": comment_text,
            "detected_type": comment_type,
            "intent": cfg["intent"],
            "reply": reply,
            "char_count": len(reply),
            "do_not_do": _comment_dont(comment_type),
        })

    return {
        "brand": brand_name,
        "platform": platform,
        "post_topic": post_topic,
        "total_replies": len(replies),
        "replies": replies,
        "brand_tone": brand_tone,
        "comment_management_tips": [
            "Reply within 1 hour — engagement spikes when you reply fast",
            "Never delete negative comments unless abusive — it signals authenticity",
            "Use first names when visible: 'Hi Priya!' feels personal",
            "For complaints — always move to DM after the public acknowledgement",
            "Pin the best comment + reply to keep positive vibes at top",
            f"On {platform}, replying boosts your post in the algorithm",
        ],
    }


def _detect_comment_type(text: str) -> str:
    text_lower = text.lower()
    if any(w in text_lower for w in ["worst", "bad", "disappointed", "angry", "refund", "scam", "fake", "never again"]):
        return "complaint"
    if any(w in text_lower for w in ["love", "great", "amazing", "awesome", "best", "excellent", "❤️", "🔥", "👏"]):
        return "praise"
    if "?" in text or any(w in text_lower for w in ["how", "what", "when", "where", "why", "price", "cost", "available"]):
        return "question"
    if any(w in text_lower for w in ["competitor", "better than", "vs", "compared"]):
        return "competitor"
    if any(w in text_lower for w in ["follow me", "check my", "dm me", "visit my"]):
        return "spam"
    return "general"


def _craft_reply(starter, comment, brand, topic, comment_type, platform, include_cta, tone):
    cta_map = {
        "instagram": "DM us or check the link in bio 👆",
        "linkedin":  "Feel free to connect or message us directly.",
        "twitter":   "Slide into our DMs 😊",
        "whatsapp":  "WhatsApp us for more info!",
    }
    cta = cta_map.get(platform, cta_map["instagram"]) if include_cta else ""

    bodies = {
        "praise":    f"{starter} Feedback like yours keeps us going! 💪 Tell a friend if {brand} helped you. {cta}",
        "question":  f"{starter} We'll be happy to help — {cta if cta else 'send us a DM for details!'}",
        "complaint": f"{starter} Please DM us your order/contact details and we'll make it right asap. 🙏",
        "troll":     f"{starter} We're always working to improve. Have a good day! ✨",
        "spam":      "Thanks for reaching out! We'll stick to our own page for now 😊",
        "general":   f"{starter} Glad you're part of the {brand} community! ❤️ {cta}",
        "competitor":f"{starter} We'd love for you to experience {brand} first-hand — we think you'll love what you find. {cta}",
    }
    return bodies.get(comment_type, bodies["general"])


def _comment_dont(comment_type: str) -> str:
    donts = {
        "complaint":  "Don't argue publicly — acknowledge + move to DM always",
        "troll":      "Don't engage emotionally — one calm reply max, then disengage",
        "spam":       "Don't delete unless abusive — a polite decline looks professional",
        "praise":     "Don't just reply 'thanks' — missed opportunity to deepen the relationship",
        "question":   "Don't leave unanswered — unanswered questions signal poor support",
        "competitor": "Don't badmouth — confident + value-led always wins",
        "general":    "Don't use generic replies — personalise with their name or comment detail",
    }
    return donts.get(comment_type, donts["general"])


def generate_bio_optimizer(
    name: str,
    current_bio: str,
    profession: str,
    industry: str,
    target_audience: str,
    cta_goal: str,
    tone: str = "professional",
    achievements: str = "",
    platforms: list = None,
    language: str = "en",
) -> dict:
    platforms = platforms or ["instagram", "linkedin", "twitter"]
    kws = _BIO_KEYWORDS_BY_INDUSTRY.get(industry.lower(), _BIO_KEYWORDS_BY_INDUSTRY["technology"])
    emojis = _BIO_EMOJI_SETS.get(tone, _BIO_EMOJI_SETS["professional"])

    bios = {}
    for platform in platforms:
        cfg = _BIO_LIMITS.get(platform, _BIO_LIMITS["instagram"])
        bio = _craft_bio(
            name=name, profession=profession, industry=industry,
            audience=target_audience, cta=cta_goal, achievements=achievements,
            emojis=emojis, kws=kws, platform=platform, char_limit=cfg["chars"],
        )
        bios[platform] = {
            "bio": bio,
            "char_count": len(bio),
            "char_limit": cfg["chars"],
            "fits": len(bio) <= cfg["chars"],
            "tips": _bio_tips(platform, cta_goal),
        }

    # Keyword suggestions
    keyword_suggestions = kws[:5] + [profession, industry.capitalize(), target_audience.split()[0] if target_audience else ""]

    return {
        "name": name,
        "original_bio": current_bio,
        "bios": bios,
        "keyword_suggestions": [k for k in keyword_suggestions if k],
        "cta_options": [
            cta_goal,
            f"DM '{kws[0].split('|')[0].strip()}' to get started",
            f"Free consultation → Link below",
            f"Download my free guide 👇",
        ],
        "tone": tone,
        "headline_options": [
            f"{profession} | Helping {target_audience}",
            f"{kws[0]} | {profession}",
            f"I help {target_audience} {cta_goal.lower()[:40]}",
        ],
    }


def _craft_bio(name, profession, industry, audience, cta, achievements, emojis, kws, platform, char_limit):
    ach = f" | {achievements[:40]}" if achievements else ""
    lines = {
        "instagram": f"{emojis[0]} {profession}{ach}\n{emojis[1]} Helping {audience}\n{emojis[2]} {kws[0]}\n{emojis[3]} {cta}\n👇 {_BIO_LIMITS['instagram']['cta']}",
        "linkedin":  f"{profession} | {kws[0]}{ach} | Helping {audience} | {cta}",
        "twitter":   f"{profession} {emojis[0]} | {kws[0]} | {cta}",
        "youtube":   f"Welcome! I'm {name} — {profession}.\n\nI help {audience}.\n\n{kws[0]}{ach}\n\n{cta}\n\n📧 Contact: {cta}\n🔔 Subscribe for weekly tips!",
    }
    bio = lines.get(platform, lines["instagram"])
    if len(bio) > char_limit:
        bio = bio[:char_limit - 3] + "..."
    return bio


def _bio_tips(platform: str, cta: str) -> list:
    tips = {
        "instagram": ["Add 1 keyword in your Name field (not just bio) — it's searchable", "Use line breaks for scannability", "Change CTA link to match your current campaign", f"End with action: '{cta[:30]}'"],
        "linkedin":  ["First 220 chars appear in search results — front-load keywords", "Use | to separate phrases for easy scanning", "Mention who you help specifically", "No hashtags needed in LinkedIn bio"],
        "twitter":   ["160 chars max — every word must earn its place", "Include 1–2 searchable keywords", "Pinned tweet can extend your bio story", "Update bio when you launch something new"],
        "youtube":   ["First 100 chars show in search results", "Include keywords you want to rank for", "Add posting schedule so viewers know when to return", "Include email for business inquiries"],
    }
    return tips.get(platform, tips["instagram"])


def generate_product_launch_kit(
    product_name: str,
    product_description: str,
    target_audience: str,
    launch_date: str,
    platforms: list,
    usp: str = "",
    price_point: str = "",
    industry: str = "technology",
    language: str = "en",
) -> dict:
    platforms = platforms or ["instagram", "linkedin"]
    usp = usp or f"The easiest {product_name} for {target_audience}"
    price_tag = f" at {price_point}" if price_point else ""

    kit: dict = {"product": product_name, "launch_date": launch_date, "phases": {}}

    for phase_key, phase in _LAUNCH_PHASES.items():
        posts = []
        for i, hook in enumerate(phase["hooks"][:3]):
            platform = platforms[i % len(platforms)]
            plat_cfg = _LAUNCH_PLATFORMS.get(platform, _LAUNCH_PLATFORMS["instagram"])
            post_body = _craft_launch_post(
                hook=hook, product=product_name, desc=product_description,
                audience=target_audience, usp=usp, price_tag=price_tag,
                platform=platform, phase=phase_key,
            )
            posts.append({
                "hook_type": hook,
                "platform": platform,
                "caption": post_body,
                "char_count": len(post_body),
                "format_note": plat_cfg["format"],
            })

        kit["phases"][phase_key] = {
            "label": phase["label"],
            "goal": phase["goal"],
            "posts": posts,
            "checklist": _launch_checklist(phase_key, product_name, launch_date),
        }

    kit["email_sequence"] = [
        {"step": k, "guide": v} for k, v in _LAUNCH_EMAIL_TEMPLATES.items()
    ]
    kit["press_kit_bullets"] = [
        f"{product_name} launches {launch_date}{price_tag}",
        f"Designed for {target_audience} in {industry}",
        f"Key USP: {usp}",
        f"Available on: {', '.join(platforms)}",
    ]
    kit["hashtags"] = {
        "launch_day": [f"#{product_name.replace(' ', '')}", "#ProductLaunch", "#NewProduct", f"#{industry.capitalize()}India", "#IndianStartup"],
        "evergreen":  ["#MadeInIndia", "#StartupIndia", f"#{industry.capitalize()}", "#Innovation", "#SmallBusiness"],
    }
    return kit


def _craft_launch_post(hook: str, product: str, desc: str, audience: str,
                        usp: str, price_tag: str, platform: str, phase: str) -> str:
    intros = {
        "pre_launch": f"Something big is coming for {audience}. 👀\n\nWe've been building {product} — {desc}.\n\n{usp}.\n\nDrop a 🙋 if you want early access{price_tag}.",
        "launch_day": f"🚀 IT'S LIVE!\n\n{product} is now available{price_tag}.\n\n{desc}\n\nBuilt specifically for {audience}.\n\n✅ {usp}\n\nLink in bio / comments 👇",
        "post_launch": f"The response to {product} has been incredible! 🙏\n\n{audience} are already loving it.\n\n{usp}\n\nJoin them today{price_tag} — link in bio.",
    }
    base = intros.get(phase, intros["launch_day"])
    if platform == "twitter":
        return base[:270] + " 🔗"
    if platform == "linkedin":
        return base + "\n\n#ProductLaunch #Innovation #IndianStartup"
    if platform == "instagram":
        return base + "\n\n.\n.\n.\n#ProductLaunch #NewProduct #MadeInIndia #IndianStartup #Innovation"
    return base


def _launch_checklist(phase: str, product: str, launch_date: str) -> list:
    checklists = {
        "pre_launch": [
            f"Set up {product} waitlist landing page",
            "Schedule teaser posts (T-14, T-7, T-3, T-1 days)",
            "Prepare press kit and media assets",
            "Warm up email list with 'coming soon' campaign",
            "Brief team on launch-day responsibilities",
        ],
        "launch_day": [
            f"Publish announcement post at 9 AM IST on {launch_date}",
            "Send launch-day email blast to full list",
            "Go live on Instagram / LinkedIn for Q&A",
            "Monitor comments and DMs — reply within 1 hour",
            "Push PR outreach to tech and business media",
        ],
        "post_launch": [
            "Follow up with non-openers (email day 3)",
            "Collect first user testimonials",
            "Post a 'thank you' and first-week stats",
            "Run a limited-time offer for fence-sitters",
            "Start review request sequence",
        ],
    }
    return checklists.get(phase, [])


def generate_bulk_posts(
    company_name: str,
    industry: str,
    tone: str,
    target_audience: str,
    platform: str,
    count: int,
    brand_keywords: list,
    usp: str,
) -> dict:
    import random
    co = company_name or "Your Company"
    count = min(max(count, 5), 30)
    topics = _BULK_TOPICS.get(industry, _BULK_TOPICS["technology"])
    tone_guide = _BRAND_TONE_GUIDES.get(tone, _BRAND_TONE_GUIDES["professional"])
    fmt = _BULK_FORMATS.get(platform, _BULK_FORMATS["instagram"])
    structures = fmt["structures"]
    hooks = fmt.get("hooks", ["💡", "🔥", "✅"])
    kws = (brand_keywords or ["innovation", "growth", "results"])
    ctas = _CTAS

    posts = []
    for i in range(count):
        topic = topics[i % len(topics)]
        structure = structures[i % len(structures)]
        hook = hooks[i % len(hooks)]
        kw = kws[i % len(kws)]
        cta = ctas[i % len(ctas)].replace("{company}", co)
        tag1 = industry.replace(" ", "")
        tag2 = topic.replace(" ", "").replace("/", "")
        tag3 = co.replace(" ", "")

        # Generate body based on topic + tone
        if tone in ["professional", "authoritative"]:
            headline = f"The smart approach to {topic} for {target_audience or 'businesses'} in 2025"
            body = f"{co} has seen firsthand how {topic} can transform outcomes. Here's what actually works: focus on {kw}, measure every step, and never stop iterating."
            point1 = f"Start with {kw} as your north star"
            point2 = f"Track {topic} metrics weekly, not monthly"
            point3 = f"Learn from the leaders in {industry}"
            question = f"Are you getting the most out of {topic}?"
        elif tone in ["casual", "empathetic"]:
            headline = f"Real talk about {topic} — what nobody says out loud"
            body = f"We get it. {topic} can feel overwhelming. But here at {co}, we've helped dozens of {target_audience or 'businesses'} crack the code. The secret? {usp or kw}."
            point1 = f"Don't overthink it — start small with {topic}"
            point2 = f"One step at a time beats zero steps forever"
            point3 = f"The right partner ({co}!) makes all the difference"
            question = f"Struggling with {topic}? You're not alone."
        else:
            headline = f"🚀 Unlocking {topic}: A {industry} perspective"
            body = f"At {co}, we believe {topic} is the game-changer for {target_audience or 'Indian businesses'}. Here's our take: {usp or f'we put {kw} first in everything we build.'}."
            point1 = f"{topic.title()} starts with the right mindset"
            point2 = f"Data + {kw} = results that speak for themselves"
            point3 = f"The {industry} leaders are already doing this"
            question = f"What's holding you back from mastering {topic}?"

        hashtags = f"#{tag1} #{tag2} #{tag3} #India #Business"

        caption = structure.format(
            hook=hook, headline=headline, body=body, cta=cta,
            hashtags=hashtags, topic=topic, point1=point1, point2=point2, point3=point3,
            question=question, tag1=tag1, tag2=tag2, tag3=tag3, company=co,
        )

        posts.append({
            "id": i + 1,
            "topic": topic,
            "platform": platform,
            "caption": caption,
            "char_count": len(caption),
            "tone_used": tone,
        })

    return {
        "action": "bulk_posts",
        "company_name": co,
        "platform": platform,
        "industry": industry,
        "total_posts": len(posts),
        "posts": posts,
        "usage_guide": {
            "schedule": f"Post {min(2, len(posts))} per day to use all {len(posts)} posts over {len(posts) // 2} days",
            "tip": "Customise the [link] and [number] placeholders before posting.",
            "best_time": _POSTING_SCHEDULE.get(platform, {}).get("best_times", ["9 AM"])[0],
        },
        "pro_tips": [
            f"Rotate these {len(posts)} posts across a {len(posts) // 2}-day calendar.",
            "Add one real photo or video to each post — visuals boost reach by 3×.",
            "A/B test the first 3 captions — keep the format that gets most saves.",
            "Reply to every comment within 2 hours to trigger the algorithm.",
        ],
    }


def generate_brand_voice_engine(
    company_name: str,
    industry: str,
    primary_tone: str,
    target_audience: str,
    brand_keywords: list,
    avoid_words: list,
    competitors: list,
    usp: str,
    language: str,
) -> dict:
    co = company_name or "Your Company"
    tone_guide = _BRAND_TONE_GUIDES.get(primary_tone, _BRAND_TONE_GUIDES["professional"])
    pillars = _CONTENT_PILLARS_BY_INDUSTRY.get(industry, _CONTENT_PILLARS_BY_INDUSTRY["technology"])

    # Build brand voice guide
    voice_guide = {
        "brand_name": co,
        "industry": industry,
        "primary_tone": primary_tone,
        "voice_description": tone_guide["voice"],
        "avoid_in_all_content": (avoid_words or []) + [tone_guide["avoid"]],
        "cta_style": tone_guide["cta_style"],
    }

    # Content pillars (6 pillars with % split)
    splits = [25, 20, 15, 15, 15, 10]
    content_pillars = [
        {"pillar": p, "content_share": f"{splits[i]}%",
         "example_post_idea": f"{co} shares insights on {p.lower()} — relevant to {target_audience or 'your audience'}"}
        for i, p in enumerate(pillars[:6])
    ]

    # Audience persona
    audience_persona = {
        "who": target_audience or f"Decision makers in {industry}",
        "pain_points": [f"Staying updated with {industry} trends", "Finding reliable, trustworthy brands", "ROI on every purchase decision"],
        "what_they_want": ["Expertise and authority", "Authentic stories", "Real results and proof"],
        "platform_behaviour": "Scrolls quickly — hook must land in first 3 words. Saves informative posts. Shares stories they identify with.",
    }

    # Brand keywords and phrases
    brand_language = {
        "power_words": (brand_keywords or []) + ["innovative", "trusted", "proven", "India-first", "results"],
        "avoid_words": avoid_words or ["cheap", "basic", "just", "simply", "try"],
        "usp_one_liner": usp or f"The go-to {industry} brand for {target_audience or 'professionals'} in India.",
        "opening_hooks": [
            f"Did you know most {industry} brands get this wrong?",
            f"Here's what we learned after 1000+ {audience_persona['who']} told us their biggest challenge:",
            f"3 things that separate the best {industry} brands from the rest →",
            f"We asked {audience_persona['who']} what they actually want. Here's the truth:",
        ],
    }

    # Competitor differentiation
    comp_diff = {}
    for c in (competitors or []):
        comp_diff[c] = f"While {c} focuses on generic solutions, {co} delivers India-specific, personalised outcomes for {target_audience or 'your audience'}."

    # Posting schedule per platform
    schedule = {platform: data for platform, data in _POSTING_SCHEDULE.items()}

    # Content ratio rule
    content_mix = {
        "value_content": "60% — Tips, insights, how-tos, industry news",
        "brand_content":  "30% — Product updates, case studies, testimonials",
        "promotional":    "10% — Offers, discounts, direct CTAs",
        "rule": "Follow the 60-30-10 rule. Too much promo = audience tunes out.",
    }

    return {
        "action": "brand_voice_engine",
        "brand_name": co,
        "industry": industry,
        "language": language or "English",
        "voice_guide": voice_guide,
        "audience_persona": audience_persona,
        "content_pillars": content_pillars,
        "brand_language": brand_language,
        "competitor_differentiation": comp_diff,
        "posting_schedule": schedule,
        "content_mix": content_mix,
        "brand_checklist": [
            "Every post should pass: Would our ideal customer save or share this?",
            "First 3 words of every caption must hook — no 'We are excited to...'",
            "Use brand power words in at least 1 post per day.",
            "Reply to every comment within 2 hours — algorithm rewards engagement.",
            "Audit content pillars monthly — drop what gets <2% engagement.",
        ],
    }


# ── Round 20: 7-Day Content Calendar ─────────────────────────────────────────

_CALENDAR_THEMES = {
    "Monday":    "Motivation Monday — Start the week with an inspiring insight or bold statement",
    "Tuesday":   "Tip Tuesday — Educational content, how-to, quick win for your audience",
    "Wednesday": "Win Wednesday — Customer success story, case study, or milestone",
    "Thursday":  "Thought Leadership — Industry opinion, trend analysis, or expert take",
    "Friday":    "Feature Friday — Product highlight, behind the scenes, or team spotlight",
    "Saturday":  "Story Saturday — Brand story, founder journey, or human interest post",
    "Sunday":    "Community Sunday — Poll, question, UGC repost, or community shoutout",
}

_PLATFORM_FORMAT = {
    "instagram": {"format": "Visual caption + 3-5 hashtags + story idea", "char_limit": 2200, "hook_type": "emoji-led or question"},
    "linkedin":  {"format": "Long-form insight post + CTA + 3 hashtags", "char_limit": 3000, "hook_type": "bold statement or statistic"},
    "twitter":   {"format": "Thread opener or single tweet + 1-2 hashtags", "char_limit": 280, "hook_type": "punchy one-liner"},
    "facebook":  {"format": "Medium post + question to drive comments", "char_limit": 500, "hook_type": "relatable opener"},
    "whatsapp":  {"format": "Short broadcast message + emoji", "char_limit": 200, "hook_type": "personal greeting"},
}


def generate_content_calendar(
    company_name: str,
    industry: str,
    tone: str,
    target_audience: str,
    platforms: list,
    week_label: str,
    brand_keywords: list,
    usp: str,
) -> dict:
    co = company_name or "Your Company"
    plats = platforms if platforms else ["instagram", "linkedin"]
    pillars = _CONTENT_PILLARS_BY_INDUSTRY.get(industry, _CONTENT_PILLARS_BY_INDUSTRY["technology"])
    tone_guide = _BRAND_TONE_GUIDES.get(tone, _BRAND_TONE_GUIDES["professional"])

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    calendar = []

    for i, day in enumerate(days):
        theme = _CALENDAR_THEMES[day]
        pillar = pillars[i % len(pillars)]
        day_posts = []

        for platform in plats:
            fmt = _PLATFORM_FORMAT.get(platform, _PLATFORM_FORMAT["instagram"])
            kw = (brand_keywords or ["innovation", "trust", "results"])[i % max(len(brand_keywords or [1]), 1)] if brand_keywords else "expertise"

            if platform == "instagram":
                caption = f"{'🔥' if i % 2 == 0 else '💡'} {theme.split('—')[0].strip()}\n\nHere's what {target_audience or 'businesses like yours'} need to know about {pillar.lower()} this week:\n\n→ {usp or f'{co} delivers real results'}\n→ Built for {industry} businesses in India\n→ {kw.title()} that actually moves the needle\n\nDouble-tap if you agree 👇\n\n#{co.replace(' ', '')} #{industry.replace(' ', '')} #IndiaStartup #BusinessGrowth"
                story = f"Poll story: 'Is {pillar.lower()} your top priority this week? Yes / No'"
                post = {"platform": "instagram", "caption": caption, "story_idea": story, "format": fmt["format"]}

            elif platform == "linkedin":
                caption = f"Most {industry} leaders get {pillar.lower()} completely wrong.\n\nHere's the real picture:\n\n📊 {target_audience or 'Decision makers'} are demanding more from their partners.\n🎯 The brands winning in 2025 are doing ONE thing differently.\n💡 {usp or f'{co} is built for exactly this.'}\n\nWhat's your take? Drop a comment below 👇\n\n#{industry.replace(' ', '')} #{pillar.replace(' ', '')} #Leadership #India"
                post = {"platform": "linkedin", "caption": caption, "format": fmt["format"]}

            elif platform == "twitter":
                caption = f"{pillar.upper()} THREAD 🧵\n\n1/ Most {industry} brands miss this. Here's what {co} does differently:\n\n→ {usp or 'We put India-first in every decision.'}\n\n(Thread continues...)"
                post = {"platform": "twitter", "caption": caption, "format": fmt["format"]}

            elif platform == "whatsapp":
                audience = target_audience or "businesses"
                caption = f"Hi! 👋 {theme.split('—')[0].strip()} from {co}!\n\n{usp or f'We help {audience} grow with smart tools.'}\n\nReply YES to learn more! 🚀"
                post = {"platform": "whatsapp", "caption": caption, "format": fmt["format"]}

            else:
                caption = f"{theme}\n\n{usp or f'{co} — Built for {industry} businesses in India.'}"
                post = {"platform": platform, "caption": caption, "format": fmt["format"]}

            day_posts.append(post)

        calendar.append({
            "day": day,
            "theme": theme,
            "content_pillar": pillar,
            "posts": day_posts,
            "posting_tip": _POSTING_SCHEDULE.get(plats[0], {}).get("best_times", ["9 AM"])[0] + " is the sweet spot for this platform",
        })

    return {
        "action": "content_calendar",
        "company_name": co,
        "week": week_label or "This Week",
        "platforms": plats,
        "total_posts": len(calendar) * len(plats),
        "calendar": calendar,
        "weekly_summary": {
            "content_themes": list(_CALENDAR_THEMES.values()),
            "pillars_covered": pillars[:7],
            "estimated_reach": f"Consistent posting on {', '.join(plats)} typically reaches {len(plats) * 500}–{len(plats) * 2000} accounts/week organically.",
        },
        "pro_tips": [
            "Batch-create all 7 days of content in one sitting — saves 5+ hours/week.",
            "Use the same core message across platforms but reformat for each.",
            "Pin your best performing post of the week every Friday.",
            "Engage (comment on 5 posts) before and after you publish — algorithm boost.",
        ],
    }


def generate_linkedin_company_post(
    company_name: str,
    industry: str,
    post_type: str,
    topic: str,
    key_message: str,
    tone: str,
    include_cta: bool,
    target_audience: str,
) -> dict:
    company  = company_name or "Our Company"
    pt       = _COMPANY_POST_TYPES.get(post_type, _COMPANY_POST_TYPES["thought_leadership"])
    tone_desc = _COMPANY_TONES.get(tone, _COMPANY_TONES["professional"])
    audience = target_audience or "industry professionals"
    base_tags = _LINKEDIN_COMPANY_HASHTAGS.get(industry, _LINKEDIN_COMPANY_HASHTAGS["technology"])
    topic_str = topic or "industry trends"
    key_msg   = key_message or f"Our perspective on {topic_str}"

    # Build hooks
    hooks = [h.replace("{company}", company).replace("{topic}", topic_str).replace("{industry}", industry).replace("{audience}", audience)
             for h in pt["hook_styles"]]

    # Build primary post
    hook = hooks[0]
    structure = pt["structure"]
    emojis = pt["emoji_palette"]

    body_sections = []
    messages = key_msg.split(". ") if key_msg else [key_msg]
    for i, step in enumerate(structure):
        emoji = emojis[i % len(emojis)]
        if i == 0:
            body_sections.append(f"{hook}\n")
        elif i < len(messages) + 1:
            body_sections.append(f"{emoji} {step}:\n{messages[min(i-1, len(messages)-1)]}")
        else:
            body_sections.append(f"{emoji} {step}:\n[Add your detail here]")

    cta_options = _COMPANY_CTA_MAP.get(post_type, _COMPANY_CTA_MAP["thought_leadership"])
    cta = cta_options[0].replace("{company}", company) if include_cta else ""

    general_tags = ["#LinkedIn", f"#{company.replace(' ', '')}", f"#{industry.title()}India", "#IndianBusiness"]
    all_tags = base_tags + general_tags
    hashtag_str = " ".join(all_tags[:10])

    primary_post = "\n\n".join(body_sections)
    if cta:
        primary_post += f"\n\n{cta}"
    primary_post += f"\n\n{hashtag_str}"

    # Short version (under 700 chars for better reach)
    short_post = f"{hook}\n\n{key_msg}\n\n{cta}\n\n{hashtag_str}" if cta else f"{hook}\n\n{key_msg}\n\n{hashtag_str}"

    # Carousel teaser (text for a LinkedIn carousel post)
    carousel_slides = [
        {"slide": 1, "title": hook, "subtitle": "Swipe to learn more →"},
        {"slide": 2, "title": structure[0] if structure else "Key Insight", "subtitle": messages[0] if messages else key_msg},
        {"slide": 3, "title": structure[1] if len(structure) > 1 else "Why It Matters", "subtitle": messages[1] if len(messages) > 1 else "This matters because..."},
        {"slide": 4, "title": structure[-1] if structure else "What's Next", "subtitle": cta or "Follow us for more updates."},
    ]

    # Best time to post
    best_times = [
        "Tuesday–Thursday, 7:30–9:00 AM IST (professionals check LinkedIn before work)",
        "Tuesday–Thursday, 12:00–1:00 PM IST (lunch break scroll)",
        "Tuesday–Thursday, 5:00–6:00 PM IST (end of workday)",
    ]

    # Post checklist
    checklist = [
        {"item": "Hook is in the first line — no fluff before the main point", "done": False},
        {"item": "Line breaks after every 1-2 sentences (mobile reading)", "done": False},
        {"item": "CTA is specific — tells reader exactly what to do", "done": False},
        {"item": "Hashtags added (8-10 max for company pages)", "done": False},
        {"item": "Tag relevant people / partners mentioned in the post", "done": False},
        {"item": "First comment prepared (add link there, not in post body)", "done": False},
        {"item": "Scheduled for peak engagement time", "done": False},
    ]

    return {
        "action": "linkedin_company_post",
        "company_name": company,
        "post_type": pt["label"],
        "industry": industry,
        "tone": tone_desc,
        "target_audience": audience,
        "primary_post": primary_post,
        "short_post": short_post,
        "hook": hook,
        "hook_alternatives": hooks[1:],
        "cta_options": [c.replace("{company}", company) for c in cta_options],
        "carousel_slides": carousel_slides,
        "hashtags": all_tags[:10],
        "best_posting_times": best_times,
        "post_structure": structure,
        "post_checklist": checklist,
        "char_count": len(primary_post),
        "pro_tips": [
            "Company pages get 3× more reach when employees reshare — brief your team before posting.",
            "First comment tip: put any links in the first comment, not the post body (LinkedIn suppresses link posts).",
            f"For {pt['label']} posts, native documents (PDFs/carousels) get 3× more impressions than text posts.",
            "Reply to every comment within the first hour — early engagement signals boost distribution.",
            "Pin your best-performing post to the top of your company page.",
        ],
    }


def generate_youtube_description(
    channel_name: str,
    video_title: str,
    video_topic: str,
    video_category: str,
    target_audience: str,
    key_points: list,
    timestamps: list,
    website: str,
    social_handles: dict,
) -> dict:
    from datetime import datetime as _dt
    year = _dt.now().year

    cat      = _YT_CATEGORIES.get(video_category, _YT_CATEGORIES["education"])
    channel  = channel_name or "Your Channel"
    title    = video_title or f"The Ultimate Guide to {video_topic}"
    topic    = video_topic or "this topic"
    audience = target_audience or "viewers"

    # Hook (first 2 lines show in search results — critical)
    hook = f"Want to master {topic}? This video covers everything {audience} need to know — from basics to advanced tips, explained simply. {cat['emoji']}"

    # Body from key points
    if key_points:
        body_lines = [f"✅ {pt}" for pt in key_points[:8]]
        body = "In this video you'll learn:\n" + "\n".join(body_lines)
    else:
        body = f"In this video you'll learn:\n✅ What is {topic} and why it matters\n✅ Step-by-step breakdown for {audience}\n✅ Common mistakes to avoid\n✅ Pro tips from real experience\n✅ Action steps you can apply today"

    # Chapters section
    if timestamps:
        chapters_lines = [_YT_CHAPTER_INTRO]
        for ts in timestamps:
            if isinstance(ts, dict):
                chapters_lines.append(f"{ts.get('time', '0:00')} — {ts.get('title', 'Section')}")
            else:
                chapters_lines.append(str(ts))
        chapters_section = "\n".join(chapters_lines)
    else:
        chapters_section = f"{_YT_CHAPTER_INTRO}0:00 — Introduction\n1:30 — What is {topic}?\n4:00 — Step-by-step guide\n8:30 — Common mistakes\n11:00 — Pro tips\n13:30 — Conclusion & next steps"

    # About section
    about_section = f"🎯 ABOUT THIS VIDEO\nThis video is designed for {audience} who want to understand {topic} clearly and actionably. {channel} creates content to help you grow — subscribe to never miss an update."

    # Links section
    links = []
    if website:
        links.append(f"🌐 Website: {website}")
    if social_handles:
        for platform, handle in social_handles.items():
            emoji_map = {"instagram": "📸", "twitter": "🐦", "linkedin": "💼", "facebook": "👥"}
            links.append(f"{emoji_map.get(platform, '🔗')} {platform.title()}: {handle}")
    if not links:
        links = ["🌐 Website: [your website]", "📸 Instagram: [your handle]", "💼 LinkedIn: [your profile]"]
    links_section = "📲 CONNECT WITH US\n" + "\n".join(links)

    # Tags (YouTube allows 500 chars)
    base_tags = cat["tags"][:]
    topic_words = topic.lower().replace("-", " ").split()
    topic_tags = topic_words + [topic.lower(), f"{topic.lower()} india", f"{topic.lower()} hindi", f"best {topic.lower()}"]
    audience_tags = [audience.lower(), f"{audience.lower()} india"] if audience else []
    channel_tags = [channel.lower().replace(" ", "")] if channel_name else []
    general_tags = ["india", "indianyoutuber", "2025", channel.lower()]
    all_tags = list(dict.fromkeys(topic_tags + base_tags + audience_tags + channel_tags + general_tags))[:30]
    tags_str = ",".join(all_tags)
    tags_section = f"🏷️ TAGS (copy-paste into YouTube tag field):\n{tags_str}"

    # SEO title suggestions
    seo_titles = [f.format(topic=topic, audience=audience, year=year, channel=channel) for f in _YT_SEO_TITLE_FORMULAS]

    # Full description
    full_description = _YT_DESCRIPTION_TEMPLATE.format(
        hook=hook, body=body, chapters_section=chapters_section,
        about_section=about_section, links_section=links_section,
        category=video_category, subscribe_cta=f"[Subscribe button]",
        tags_section=tags_section,
    )

    # End screen suggestions
    end_screen = [t.replace("[topic]", topic).replace("[your most relevant video]", f"related {topic} video") for t in _YT_END_SCREEN_TEMPLATES]

    # Thumbnail tips
    thumbnail_tips = [
        f"Use a bold number: '5 {topic} Tips' or 'Top 3 Mistakes'",
        "High contrast — bright background (yellow/red) + dark text",
        "Face with exaggerated expression gets 30% higher CTR",
        "Include the year (2025) to signal fresh content",
        "Mobile-test: thumbnail should be readable at 120×67px",
    ]

    # Upload checklist
    upload_checklist = [
        {"item": "Title includes primary keyword in first 60 chars", "done": False},
        {"item": "Description first 2 lines hook viewer (shown in search)", "done": False},
        {"item": "Chapters/timestamps added (boosts watch time)", "done": False},
        {"item": "All tags entered (up to 500 chars)", "done": False},
        {"item": "End screen added at 20-second mark", "done": False},
        {"item": "Cards added at relevant moments", "done": False},
        {"item": "Custom thumbnail uploaded", "done": False},
        {"item": "Video added to a playlist", "done": False},
        {"item": "Pinned comment with key links", "done": False},
        {"item": "Posted to Community tab & social media", "done": False},
    ]

    return {
        "action": "youtube_description",
        "channel_name": channel,
        "video_title": title,
        "video_topic": topic,
        "category": video_category,
        "hook": hook,
        "full_description": full_description,
        "tags": all_tags,
        "tags_string": tags_str,
        "seo_title_suggestions": seo_titles,
        "chapters_section": chapters_section,
        "end_screen_suggestions": end_screen,
        "thumbnail_tips": thumbnail_tips,
        "upload_checklist": upload_checklist,
        "char_count": {
            "description": len(full_description),
            "description_limit": 5000,
            "tags": len(tags_str),
            "tags_limit": 500,
        },
    }


def generate_reel_script(
    business_name: str,
    business_type: str,
    reel_topic: str,
    reel_goal: str = "awareness",
    target_audience: str = "",
    duration: int = 30,
    style: str = "educational",
    language: str = "en",
) -> dict:
    style_info   = _REEL_STYLES.get(style, _REEL_STYLES["educational"])
    goal_info    = _REEL_GOALS.get(reel_goal, _REEL_GOALS["awareness"])
    hooks        = _REEL_HOOKS.get(style, _REEL_HOOKS["educational"])
    vo_guide     = _VOICEOVER_GUIDES.get(duration, _VOICEOVER_GUIDES[30])
    visuals      = _VISUAL_DIRECTION.get(style, _VISUAL_DIRECTION["educational"])

    biz  = business_name or "Your Business"
    biz_type = business_type or "business"
    topic = reel_topic or "your product"
    audience = target_audience or "customers"

    hook_filled = hooks[0].replace("{topic}", topic).replace("{business_name}", biz).replace("{business_type}", biz_type).replace("{audience}", audience).replace("{number}", "3").replace("{benefit}", "better results").replace("{revenue}", "10L").replace("{loss}", "50,000").replace("{city}", "India").replace("{product}", topic).replace("{product_type}", topic)

    # Build scene-by-scene script
    structure = style_info["structure"]
    scene_scripts = []
    scene_contents = [
        f"🎬 HOOK — {hook_filled}",
        f"📌 Introduce the core problem/topic: {topic} and why it matters to {audience}",
        f"💡 Key insight or step 1 related to {topic} — keep it visual and punchy",
        f"✨ Key insight or step 2 / result — show don't tell",
        f"🚀 CTA: {goal_info['cta']}",
    ]
    for i, (scene, content) in enumerate(zip(structure, scene_contents[:len(structure)])):
        scene_scripts.append({
            "scene": i + 1,
            "timing": scene,
            "voiceover": content,
            "visual_note": visuals[i % len(visuals)],
        })

    # Hashtags
    industry_key = "services"
    for k in _HASHTAG_SETS:
        if k in biz_type.lower():
            industry_key = k
            break
    base_tags = _HASHTAG_SETS[industry_key]
    general_tags = ["#Reels", "#InstagramReels", "#IndianBusiness", "#Entrepreneur", "#BusinessTips"]
    all_tags = (base_tags + general_tags)[:20]
    hashtag_str = " ".join(all_tags)

    caption = _CAPTION_TEMPLATES.get(style, _CAPTION_TEMPLATES["educational"]).format(
        hook=hook_filled,
        topic=topic,
        audience=audience,
        point1=f"Most {audience} don't think about {topic} proactively",
        point2=f"The right approach to {topic} saves time and money",
        point3=f"{biz} has cracked the formula — ask us how",
        story_line=f"When {biz} started, {topic} was our biggest challenge.",
        lesson=f"Understanding {topic} is the first step to growth.",
        product_name=topic,
        usp=f"Built for {audience} in India",
        benefit1="Saves time", benefit2="Saves money", benefit3="Built for Indian SMEs",
        business_name=biz,
        quote=f"I never thought {topic} could be this simple. Thank you {biz}!",
        customer="Happy Customer", customer_city="Bangalore",
        cta=goal_info["cta"],
        hashtags=hashtag_str,
    )

    # Audio suggestions
    audio_suggestions = [
        {"type": "Trending Instrumental", "note": "Search 'trending reels audio India 2025' on Instagram for latest hits"},
        {"type": "Original Voiceover", "note": f"Record in {style_info['tone']} tone — {vo_guide['pace']}"},
        {"type": "Text-Only (No Audio)", "note": "Works well for educational content with on-screen text"},
    ]

    # Pro tips
    pro_tips = [
        f"Post between 7-9 PM IST for maximum Indian audience reach",
        f"First 3 seconds decide everything — nail the hook: '{hook_filled}'",
        f"Add closed captions — 85% of Reels are watched without sound",
        f"Use the 'Collab' feature to co-post with complementary brands",
        f"Target metric for this Reel: {goal_info['metric']}",
        f"Repurpose this script for YouTube Shorts and LinkedIn Video",
    ]

    return {
        "action": "reel_script",
        "business_name": biz,
        "reel_topic": topic,
        "style": style,
        "style_label": style_info["label"],
        "duration_seconds": duration,
        "goal": reel_goal,
        "target_audience": audience,
        "hook": hook_filled,
        "hook_alternatives": [h.replace("{topic}", topic).replace("{business_name}", biz).replace("{business_type}", biz_type).replace("{audience}", audience).replace("{number}", "3").replace("{benefit}", "better results").replace("{revenue}", "10L").replace("{loss}", "50,000").replace("{city}", "India").replace("{product}", topic).replace("{product_type}", topic) for h in hooks[1:]],
        "script_scenes": scene_scripts,
        "voiceover_guide": vo_guide,
        "visual_direction": visuals,
        "caption": caption,
        "hashtags": all_tags,
        "audio_suggestions": audio_suggestions,
        "cta": goal_info["cta"],
        "pro_tips": pro_tips,
        "repurpose_tip": "Same script works for YouTube Shorts (60s version) and LinkedIn Video — adjust CTA per platform.",
    }


def generate_review_testimonial_kit(
    business_name: str,
    business_type: str,
    owner_name: str,
    product_service: str,
    review_platform: str = "google",
    customer_type: str = "b2c",
    tone: str = "warm",
) -> dict:
    company   = business_name or "Your Business"
    owner     = owner_name or "The Team"
    product   = product_service or "our products/services"
    biz_type  = business_type or "retail"
    platform  = _REVIEW_CHANNELS.get(review_platform, _REVIEW_CHANNELS["google"])
    wa_key    = "b2b_professional" if customer_type == "b2b" else "b2c_warm"

    review_link = f"[Your {platform['name']} link here — add from your Google Business / JustDial dashboard]"

    # Fill WhatsApp templates
    wa_template = _WHATSAPP_TEMPLATES[wa_key]
    wa_filled = wa_template.replace("{customer_name}", "[Customer Name]") \
        .replace("{business_name}", company) \
        .replace("{product_service}", product) \
        .replace("{platform_name}", platform["name"]) \
        .replace("{review_link}", review_link) \
        .replace("{owner_name}", owner) \
        .replace("{greeting}", "Namaste" if tone == "warm" else "Hello")

    wa_support = _WHATSAPP_TEMPLATES["post_support"] \
        .replace("{customer_name}", "[Customer Name]") \
        .replace("{review_link}", review_link) \
        .replace("{business_name}", company)

    # Email templates
    email_review_subjs = [s.replace("{customer_name}", "[Customer Name]").replace("{business_name}", company)
                          for s in _EMAIL_TEMPLATES["review_request"]["subject_options"]]
    email_review_body  = _EMAIL_TEMPLATES["review_request"]["body"] \
        .replace("{customer_name}", "[Customer Name]") \
        .replace("{business_name}", company) \
        .replace("{product_service}", product) \
        .replace("{platform_name}", platform["name"]) \
        .replace("{review_link}", review_link) \
        .replace("{owner_name}", owner) \
        .replace("{owner_phone}", "[Your WhatsApp number]")

    email_test_subjs = [s.replace("{customer_name}", "[Customer Name]").replace("{business_name}", company)
                        for s in _EMAIL_TEMPLATES["testimonial_request"]["subject_options"]]
    email_test_body  = _EMAIL_TEMPLATES["testimonial_request"]["body"] \
        .replace("{customer_name}", "[Customer Name]") \
        .replace("{business_name}", company) \
        .replace("{product_service}", product) \
        .replace("{review_link}", review_link) \
        .replace("{owner_name}", owner) \
        .replace("{owner_phone}", "[Your WhatsApp number]")

    # SMS
    sms_review    = _SMS_TEMPLATES["review"].replace("{business_name}", company).replace("{customer_name}", "[Name]").replace("{review_link}", review_link)
    sms_reminder  = _SMS_TEMPLATES["reminder"].replace("{business_name}", company).replace("{customer_name}", "[Name]").replace("{review_link}", review_link)

    return {
        "action":          "review_testimonial_kit",
        "business_name":   company,
        "platform":        platform,
        "review_link_placeholder": review_link,
        "whatsapp_templates": {
            "review_request": wa_filled,
            "post_support":   wa_support,
        },
        "email_templates": {
            "review_request": {
                "subject_options": email_review_subjs,
                "body": email_review_body,
            },
            "testimonial_request": {
                "subject_options": email_test_subjs,
                "body": email_test_body,
            },
        },
        "sms_templates": {
            "review":    sms_review,
            "reminder":  sms_reminder,
        },
        "follow_up_sequence": _REVIEW_FOLLOW_UP,
        "testimonial_formats": _TESTIMONIAL_FORMATS,
        "incentive_ideas": _INCENTIVE_IDEAS,
        "timing_guide": _REVIEW_TIMING,
        "pro_tips": [
            f"India-specific: WhatsApp has 90%+ open rate vs 20% for email — always lead with WhatsApp",
            f"Best time to send: 7-9 PM IST (post-dinner, highest phone usage in India)",
            f"{platform['name']}: {platform['impact']}",
            "Never ask for '5 stars' explicitly — just ask for 'honest feedback' to avoid policy violations",
            "Personalise the customer's name — personalised requests get 3x higher response rates",
            "Video testimonials via WhatsApp convert best for B2B proposals and social proof ads",
            "Follow up at least once — 70% of reviews come from the 2nd or 3rd nudge",
        ],
    }


def generate_linkedin_article(
    topic: str,
    brand_name: str,
    author_name: str,
    industry: str,
    target_audience: str,
    article_goal: str,
    key_points: list,
    word_count: int,
) -> dict:
    topic_clean = topic or "How Indian Startups Can Build Unbreakable Customer Loyalty"
    brand = brand_name or "Your Company"
    author = author_name or "Your Name"
    ind = industry or "technology"
    audience = target_audience or "startup founders and business leaders"
    goal_key = article_goal if article_goal in _ARTICLE_GOALS else "thought_leadership"
    goal_cfg = _ARTICLE_GOALS[goal_key]

    demo_points = key_points if key_points else [
        f"Most {ind} companies optimise for acquisition but lose on retention — the math doesn't work",
        f"The top 3 loyalty drivers in Indian B2B are response time, personalisation, and perceived value (not price)",
        f"A 5% improvement in retention increases profit by 25-95% (Bain & Company)",
        f"WhatsApp-first support has 3x higher satisfaction scores than email-first for Indian SMBs",
        f"Loyalty programs that reward behaviour (not just spend) drive 40% higher engagement",
    ]

    structure = goal_cfg["structure"]
    sections = []
    for i, section_key in enumerate(structure):
        guide = _SECTION_WRITERS.get(section_key, f"Write a compelling section on this topic: {section_key.replace('_',' ').title()}")
        if i == 0:
            content_hint = f"Hook readers on: {topic_clean}"
        elif i < len(demo_points) + 1 and section_key in ("insight_1","insight_2","insight_3","how_to_section_1","how_to_section_2","how_to_section_3"):
            point_idx = ["insight_1","insight_2","insight_3","how_to_section_1","how_to_section_2","how_to_section_3"].index(section_key)
            content_hint = demo_points[point_idx] if point_idx < len(demo_points) else f"Key insight about {topic_clean}"
        elif section_key == "cta":
            content_hint = f"Follow {author} for weekly {ind} insights. Ask: 'What's your biggest {topic_clean.split()[0].lower()} challenge?'"
        else:
            content_hint = f"Expand on: {topic_clean} from the perspective of {audience}"

        sections.append({
            "section_num":   i + 1,
            "section_key":   section_key,
            "section_title": section_key.replace("_", " ").title(),
            "writing_guide": guide,
            "content_hint":  content_hint,
            "approx_words":  word_count // len(structure),
        })

    # Pull quotes — pick top insights
    pull_quotes = [f'"{pt[:120]}{"…" if len(pt) > 120 else ""}"' for pt in demo_points[:3]]

    # Title options
    title_formulas = [
        f"Why Most {ind.title()} Companies Get {topic_clean.split()[0]} Wrong (And What to Do Instead)",
        f"The {len(demo_points)} {topic_clean.split()[0].title()} Lessons I Wish Someone Had Told Me Earlier",
        f"I Spent 5 Years Learning This About {topic_clean.split()[0].title()}. Here's Everything:",
        f"The {topic_clean.split()[0].title()} Playbook That Actually Works for Indian Businesses",
        f"Stop {topic_clean.split()[0].title()}ing the Wrong Way. Here's the Framework That Works:",
    ]

    # Hashtag suggestions
    hashtags = [
        f"#{ind.replace(' ','').title()}",
        f"#{topic_clean.split()[0].title()}",
        "#IndianBusiness",
        "#Leadership",
        "#BusinessGrowth",
        f"#{audience.split()[0].title()}",
        "#LinkedIn",
    ]

    estimated_read_time = max(1, word_count // 200)

    return {
        "action":           "linkedin_article",
        "topic":            topic_clean,
        "author":           author,
        "brand":            brand,
        "industry":         ind,
        "goal":             goal_key,
        "goal_description": goal_cfg["length_guide"],
        "title_options":    title_formulas[:5],
        "sections":         sections,
        "total_sections":   len(sections),
        "target_word_count": word_count,
        "estimated_read_time": f"{estimated_read_time} min read",
        "pull_quotes":      pull_quotes,
        "intro_hook_guide": goal_cfg["intro_hook"],
        "cta_type":         goal_cfg["cta_type"],
        "seo_tips":         _SEO_TIPS,
        "hashtags":         hashtags,
        "key_points_used":  demo_points,
        "summary":          f"LinkedIn article blueprint for '{topic_clean}' — {len(sections)} sections, ~{word_count} words, goal: {goal_key.replace('_',' ')}. {estimated_read_time} read.",
    }


# ── Podcast → Social Content Kit (Round 14) ──────────────────────────────────

_CAROUSEL_SLIDE_PROMPTS = [
    "Title slide: Episode title as bold headline + your brand name",
    "Hook slide: The most surprising or counterintuitive insight from the episode",
    "Key insight 1: First major takeaway with a supporting stat or quote",
    "Key insight 2: Second major takeaway — make it visual (list or before/after)",
    "Key insight 3: Third major takeaway — frame as a tip the audience can use today",
    "Quote slide: Best direct quote from the guest/host — large text, minimal design",
    "Action slide: 'The one thing to do after listening to this episode'",
    "CTA slide: 'Follow for weekly episodes' + link/handle",
]

_REELS_HOOKS = [
    "POV: You just learned {insight} in 45 minutes. Here's the 60-second version…",
    "This podcast episode changed how I think about {topic}. 3 things I learned 👇",
    "Stop doing {wrong_approach}. Here's what {guest_or_host} does instead:",
    "{Number} minutes into this episode and I had to pause. Here's why:",
    "The {topic} advice everyone gives you is wrong. {guest_or_host} explains why:",
]

_EMAIL_STRUCTURES = {
    "subject_lines": [
        "🎙️ New episode: {title}",
        "What {guest} taught me about {topic}",
        "{Number} insights from our latest podcast episode",
        "This week on the podcast: {title}",
    ],
    "structure": [
        "OPENING: One-line hook — the most surprising thing from this episode",
        "EPISODE SUMMARY: 2-3 sentences on who was on and what you covered",
        "TOP 3 INSIGHTS: Bulleted list — one line per insight, scannable",
        "FAVORITE QUOTE: Block-quoted — gives the email personality",
        "LISTEN NOW CTA: Big button + episode URL",
        "P.S.: Tease next week's episode or topic",
    ],
}


def generate_podcast_content_kit(
    episode_title: str,
    brand_name: str,
    host_name: str,
    key_points: list,
    guest_name: str,
    episode_url: str,
    industry: str,
    target_audience: str,
) -> dict:
    title = episode_title or "How Indian Startups Can Scale Without VC Funding"
    brand = brand_name or "Your Podcast"
    host = host_name or "Your Name"
    guest = guest_name or ""
    audience = target_audience or "entrepreneurs and business owners"
    ind = industry or "business"
    url = episode_url or "[episode link]"

    demo_points = key_points if key_points else [
        f"Most {audience} make the mistake of scaling headcount before product-market fit",
        f"Revenue-based financing is an underused alternative to VC in {ind}",
        f"The 'default alive' metric: if you stopped hiring today, would you reach profitability?",
        f"Building in public increases trust and reduces CAC by 30-40% for B2B brands",
        f"The best time to fundraise is when you don't need it — leverage matters",
    ]

    guest_or_host = guest if guest else host
    topic_short = title.split(":")[0].strip() if ":" in title else title[:40]

    # LinkedIn post
    linkedin_hook = f"I just finished recording an episode with {guest_or_host} and I'm still thinking about it." if guest else f"We just released a new episode and I can't stop thinking about one insight from it."
    linkedin_points = "\n".join([f"→ {pt}" for pt in demo_points[:4]])
    linkedin_post = f"""{linkedin_hook}

Topic: {title}

Here are the 4 things that hit hardest:

{linkedin_points}

The full conversation is up now — link in comments.

What's your biggest challenge with {topic_short.lower()}? Drop it below 👇

#Podcast #{ind.replace(' ','').title()} #{audience.split()[0].title()}"""

    # Twitter thread hook tweets
    twitter_hook = f"Just wrapped an episode on {topic_short.lower()}.\n\n{len(demo_points)} insights that changed how I think about it 🧵"
    twitter_tweets = [twitter_hook] + [f"{i+1}/ {pt}" for i, pt in enumerate(demo_points)] + [
        f"If you want the full breakdown, listen here 👇\n\n{url}\n\nFollow @{brand.lower().replace(' ','')} for weekly episodes on {ind}."
    ]

    # Instagram carousel slides
    carousel_slides = []
    for i, prompt in enumerate(_CAROUSEL_SLIDE_PROMPTS):
        if i == 0:
            content = f"Headline: \"{title}\"\nSubheading: {brand} Podcast"
        elif i == 1:
            content = demo_points[0] if demo_points else "Key insight here"
        elif i <= len(demo_points) and i >= 2:
            content = demo_points[min(i-1, len(demo_points)-1)]
        elif "Quote" in prompt and guest:
            content = f'"{demo_points[0]}"\n— {guest_or_host}'
        elif "Action" in prompt:
            content = f"One thing to do after this episode:\n\n{demo_points[-1].split('.')[0]}."
        elif "CTA" in prompt:
            content = f"New episode every week.\nFollow @{brand.lower().replace(' ','')} 🎙️\n\n{url}"
        else:
            content = demo_points[min(i, len(demo_points)-1)] if demo_points else "Content here"
        carousel_slides.append({"slide": i+1, "purpose": prompt.split(":")[0], "content": content})

    # Reels script
    reel_hook_template = _REELS_HOOKS[0]
    reel_hook = (reel_hook_template
        .replace("{insight}", demo_points[0][:60] + "…" if demo_points else "this insight")
        .replace("{topic}", topic_short.lower()))
    reels_script = {
        "hook_0_3s":   reel_hook,
        "setup_3_8s":  f"I just finished a {len(demo_points)*3}-minute episode on {topic_short.lower()} with {guest_or_host}.",
        "insight_1":   f"First: {demo_points[0]}" if demo_points else "First insight",
        "insight_2":   f"Second: {demo_points[1]}" if len(demo_points) > 1 else "Second insight",
        "insight_3":   f"Third: {demo_points[2]}" if len(demo_points) > 2 else "Third insight",
        "cta_end":     f"Full episode link in bio. New episodes weekly on {brand}.",
        "total_length": "45-60 seconds",
        "caption":     f"3 things I learned from this week's episode ↑\n\n🎙️ {title}\n\n{url}",
    }

    # Email newsletter
    email = {
        "subject": f"🎙️ New episode: {title}",
        "alt_subjects": [sl.replace("{title}", title).replace("{guest}", guest_or_host).replace("{topic}", topic_short.lower()).replace("{Number}", str(len(demo_points))) for sl in _EMAIL_STRUCTURES["subject_lines"][1:]],
        "body_structure": _EMAIL_STRUCTURES["structure"],
        "opening_hook": f"This week's episode of {brand} is one I've been wanting to record for a long time.",
        "summary": f"{'I sat down with ' + guest + ' to talk about' if guest else 'This week we explored'} {topic_short.lower()} — and it went deeper than I expected.",
        "top_3_insights": [f"**{pt.split(':')[0] if ':' in pt else pt[:50]}**: {pt.split(':')[1].strip() if ':' in pt else pt}" for pt in demo_points[:3]],
        "listen_cta": f"Listen to the full episode → {url}",
    }

    distribution_checklist = [
        {"platform": "LinkedIn", "format": "Long-form post", "timing": "Tuesday/Wednesday 8-10 AM", "action": "Post LinkedIn copy above. Reply to every comment in first 2 hours."},
        {"platform": "Twitter/X", "format": "Thread", "timing": "Monday/Thursday 8 AM or 9 PM", "action": "Post thread above. Pin it to your profile for 7 days."},
        {"platform": "Instagram", "format": "Carousel (8 slides)", "timing": "Tuesday/Friday 7-9 PM", "action": "Use carousel slides. Add swipe-worthy first slide visual. Use 5-8 niche hashtags."},
        {"platform": "Instagram Reels", "format": "60s vertical video", "timing": "Wednesday/Saturday 6-8 PM", "action": "Record Reels using script above. Add captions — 85% watch without sound."},
        {"platform": "Email", "format": "Newsletter", "timing": "Send day of or day after publish", "action": "Use email template above. A/B test subject lines on first 20%."},
        {"platform": "WhatsApp", "format": "Status + broadcast", "timing": "Same day as publish", "action": "Share 1-line episode teaser + link on status. Send to broadcast list."},
    ]

    return {
        "action":                "podcast_content_kit",
        "episode_title":         title,
        "brand":                 brand,
        "guest":                 guest,
        "host":                  host,
        "key_points_used":       demo_points,
        "linkedin_post":         linkedin_post,
        "twitter_thread_tweets": twitter_tweets,
        "instagram_carousel":    carousel_slides,
        "reels_script":          reels_script,
        "email_newsletter":      email,
        "distribution_checklist": distribution_checklist,
        "total_formats":         5,
        "summary":               f"Generated 5-format content kit for '{title}' — LinkedIn post, {len(twitter_tweets)}-tweet thread, {len(carousel_slides)}-slide carousel, Reels script & email newsletter.",
    }


def _generate_twitter_thread_legacy(
    topic: str,
    brand_name: str,
    industry: str,
    audience: str,
    num_tweets: int,
    style: str,
    include_cta: bool,
) -> dict:
    style_key = style if style in _THREAD_STYLES else "educational"
    style_cfg = _THREAD_STYLES[style_key]
    topic_clean = topic or "business growth"
    brand = brand_name or "your brand"
    aud = audience or "entrepreneurs"

    hook = (style_cfg["hook_formula"]
        .replace("{topic}", topic_clean)
        .replace("{audience}", aud)
        .replace("{num}", str(num_tweets - 2))
        .replace("{timeframe}", "30 days")
    )

    pattern = style_cfg["structure"]
    if num_tweets < len(pattern):
        pattern = pattern[:num_tweets - 1] + ["cta"]
    elif num_tweets > len(pattern):
        extras = ["point"] * (num_tweets - len(pattern))
        pattern = pattern[:-1] + extras + ["cta"]

    if not include_cta:
        pattern = [p for p in pattern if p != "cta"]

    tweets = []
    step_counter = 1
    for idx, tweet_type in enumerate(pattern):
        template_key = tweet_type
        tmpl = _TWEET_TEMPLATES.get(template_key, _TWEET_TEMPLATES["point"])

        if tweet_type == "hook":
            content = hook
            writing_guide = tmpl
        elif tweet_type == "cta":
            content = f"If you found this useful, follow @{brand.lower().replace(' ', '')} for weekly {topic_clean} insights.\n\nRT to help other {aud} in {industry or 'your space'} 🙏"
            writing_guide = tmpl
        elif tweet_type == "summary":
            content = f"TL;DR — Everything about {topic_clean} in one tweet:\n\n• [Key point 1]\n• [Key point 2]\n• [Key point 3]\n• [Key point 4]\n\nSave this 📌"
            writing_guide = tmpl
        elif tweet_type == "step":
            content = f"Step {step_counter}/ [Action for {topic_clean}]\n\nHow: [specific how-to]\nResult: [what you get]\n\nMost people skip this. Don't."
            step_counter += 1
            writing_guide = tmpl.replace("N", str(step_counter - 1))
        elif tweet_type == "tip":
            content = f"[Tip about {topic_clean}]\n\nWhy it works: [explanation]\n\nMost {aud} do the opposite."
            writing_guide = tmpl
        elif tweet_type == "example":
            content = f"Real example:\n\n[Company/person] did [action] for {topic_clean}.\n\nResult: [specific outcome with numbers]\n\nHere's exactly how:"
            writing_guide = tmpl
        else:
            content = f"[{tweet_type.replace('_', ' ').title()} — about {topic_clean}]\n\nCustomize this tweet with your specific insight, data, or story."
            writing_guide = tmpl

        tweets.append({
            "tweet_num":     idx + 1,
            "total":         len(pattern),
            "type":          tweet_type,
            "label":         tweet_type.replace("_", " ").title(),
            "content":       content,
            "writing_guide": writing_guide,
            "char_count":    len(content),
            "over_limit":    len(content) > 280,
        })

    engagement_hooks = [
        f"Tweet 2: Ask 'Which of these surprised you most?' — easy reply, algorithm boost",
        f"Tweet {len(pattern)//2}: Add a poll 'Do you do X or Y?' — polls get 10x more engagement than regular tweets",
        f"Final tweet: 'RT if this helped one person in {industry or 'your industry'}' — social proof ask works",
    ]

    return {
        "action":          "twitter_thread",
        "topic":           topic_clean,
        "brand":           brand,
        "style":           style_key,
        "audience":        aud,
        "total_tweets":    len(tweets),
        "hook_text":       hook,
        "tweets":          tweets,
        "thread_rules":    _THREAD_RULES,
        "engagement_tips": style_cfg["engagement_tip"],
        "tone":            style_cfg["tone"],
        "engagement_hooks": engagement_hooks,
        "summary": f"Generated {len(tweets)}-tweet {style_key} thread on '{topic_clean}'. Hook: '{hook[:60]}…'",
    }


# ── LinkedIn Carousel Generator (Round 12) ───────────────────────────────────

_CAROUSEL_STYLES = {
    "educational": {
        "hook_formula":  "X things about {topic} that most {audience} don't know",
        "slide_pattern": ["hook", "problem", "insight", "insight", "insight", "example", "takeaway", "cta"],
        "tone":          "informative, clear, scannable",
        "design_tip":    "Use numbered slides (1/8, 2/8…). Bold the key stat or phrase on each slide. Keep text under 30 words per slide.",
    },
    "storytelling": {
        "hook_formula":  "How {brand} went from {pain} to {outcome} — the real story",
        "slide_pattern": ["hook", "context", "turning_point", "obstacle", "solution", "result", "lesson", "cta"],
        "tone":          "personal, vulnerable, narrative arc",
        "design_tip":    "Start dark (problem) and get lighter (solution). First-person voice works best. End with a question to drive comments.",
    },
    "listicle": {
        "hook_formula":  "{num} {topic} mistakes that are costing {audience} time and money",
        "slide_pattern": ["hook", "item1", "item2", "item3", "item4", "item5", "bonus", "cta"],
        "tone":          "punchy, direct, actionable",
        "design_tip":    "Each slide = one mistake + one fix. Use emoji as visual anchors. Keep consistent layout across all slides.",
    },
    "how_to": {
        "hook_formula":  "How to {outcome} in {timeframe} (step-by-step for {audience})",
        "slide_pattern": ["hook", "overview", "step1", "step2", "step3", "step4", "common_mistake", "cta"],
        "tone":          "structured, practical, beginner-friendly",
        "design_tip":    "Use progress bar or step indicator. Include one actionable tip per step slide. Final slide = summary checklist.",
    },
    "data_driven": {
        "hook_formula":  "We studied {number} {industry} brands. Here's what the data says about {topic}",
        "slide_pattern": ["hook", "methodology", "finding1", "finding2", "finding3", "surprise", "what_it_means", "cta"],
        "tone":          "authoritative, credible, insight-led",
        "design_tip":    "Lead each slide with the stat in large text. Explain in one sentence below. Add source attribution in small text.",
    },
}

_SLIDE_TEMPLATES = {
    "hook": {
        "label": "Hook (Slide 1)",
        "purpose": "Stop the scroll — make them swipe to slide 2",
        "elements": ["Bold, curious headline (max 10 words)", "Teaser of what they'll learn", "Visual: bold text on contrast background"],
        "tip": "The hook is 80% of carousel performance. Test multiple versions.",
    },
    "problem": {
        "label": "Problem / Pain",
        "purpose": "Agitate the pain — make them feel seen",
        "elements": ["Name the specific problem", "1 stat or relatable scenario", "Empathy line: 'If you're feeling X, you're not alone'"],
        "tip": "Be specific. 'Indian SMBs lose ₹2L/yr to bad invoicing' beats 'businesses lose money'.",
    },
    "insight": {
        "label": "Key Insight",
        "purpose": "Deliver the 'aha' moment",
        "elements": ["One insight per slide", "Bold the key phrase", "Optional: counter-intuitive angle"],
        "tip": "Each insight should be screenshot-worthy on its own.",
    },
    "example": {
        "label": "Real Example",
        "purpose": "Make it tangible with a case/story",
        "elements": ["Brand/company name or anonymized case", "Before → After format", "Specific numbers or results"],
        "tip": "India-specific examples (Zoho, Freshworks, D2C brands) resonate more on Indian LinkedIn.",
    },
    "takeaway": {
        "label": "Key Takeaway",
        "purpose": "The 'save this slide' moment — summarize learning",
        "elements": ["Bullet summary of all insights", "Bold the most important one", "Make it standalone without context"],
        "tip": "This is the most saved slide. Design it as a standalone visual.",
    },
    "cta": {
        "label": "CTA (Last Slide)",
        "purpose": "Drive the action you want",
        "elements": ["One clear action (comment / follow / DM / link)", "Restate the value they just received", "Question to spark comments"],
        "tip": "Ask a question that's easy to answer in 1-2 words — drives comments algorithm boost.",
    },
    "context": {
        "label": "Context / Background",
        "purpose": "Set the scene before the story unfolds",
        "elements": ["Where / when / who", "Keep it brief — 2-3 lines max", "Hook them into wanting to know what happened next"],
        "tip": "Don't over-explain here — save the detail for later slides.",
    },
    "turning_point": {
        "label": "Turning Point",
        "purpose": "The moment everything changed",
        "elements": ["The decision / discovery / event", "Why it mattered", "Emotional beat"],
        "tip": "This is the heart of the story. Give it space.",
    },
    "obstacle": {
        "label": "Obstacle / Challenge",
        "purpose": "Show the struggle — makes the win more satisfying",
        "elements": ["What almost derailed it", "Internal or external challenge", "How close they came to giving up"],
        "tip": "Vulnerability here builds massive trust with the audience.",
    },
    "solution": {
        "label": "The Solution",
        "purpose": "The breakthrough moment",
        "elements": ["What actually worked", "Why it worked (the insight)", "How they implemented it"],
        "tip": "Be specific — generic solutions don't get saved or shared.",
    },
    "result": {
        "label": "Result / Outcome",
        "purpose": "The payoff the reader has been waiting for",
        "elements": ["Specific measurable outcome", "Timeframe", "Qualitative change too (not just numbers)"],
        "tip": "Numbers with context beat raw numbers. '3x revenue in 6 months from ₹10L to ₹30L' > '3x growth'.",
    },
    "lesson": {
        "label": "The Lesson",
        "purpose": "What others can take away from this story",
        "elements": ["1-2 transferable lessons", "Who this applies to", "What to avoid"],
        "tip": "This is why they'll share it. Make it universally applicable.",
    },
    "overview": {"label": "Overview", "purpose": "Preview what's coming", "elements": ["List of steps", "Time/effort required", "Who this is for"], "tip": "Set expectations clearly."},
    "step1":    {"label": "Step 1", "purpose": "First action", "elements": ["Clear action", "Why it matters", "Quick win possible here"], "tip": "Make step 1 easy — build momentum."},
    "step2":    {"label": "Step 2", "purpose": "Second action", "elements": ["Build on step 1", "Common mistake here", "Pro tip"], "tip": ""},
    "step3":    {"label": "Step 3", "purpose": "Third action", "elements": ["The pivotal step", "Most people skip this", "Result if done right"], "tip": ""},
    "step4":    {"label": "Step 4", "purpose": "Final action", "elements": ["Completion step", "How to measure success", "What good looks like"], "tip": ""},
    "common_mistake": {"label": "Common Mistake", "purpose": "What to avoid", "elements": ["The mistake", "Why people make it", "The fix"], "tip": "Negative framing gets high saves."},
    "methodology": {"label": "Methodology", "purpose": "Build credibility", "elements": ["How the data was gathered", "Sample size", "Time period"], "tip": ""},
    "finding1": {"label": "Finding 1", "purpose": "First data insight", "elements": ["Stat in large text", "1-line explanation", "Source"], "tip": ""},
    "finding2": {"label": "Finding 2", "purpose": "Second data insight", "elements": ["Stat in large text", "1-line explanation", "Implication"], "tip": ""},
    "finding3": {"label": "Finding 3", "purpose": "Third data insight", "elements": ["Stat in large text", "1-line explanation", "Pattern emerging"], "tip": ""},
    "surprise": {"label": "Surprising Finding", "purpose": "The unexpected result", "elements": ["Counter-intuitive stat", "Why it surprised us", "What it means"], "tip": "This is your most shareable slide."},
    "what_it_means": {"label": "What It Means For You", "purpose": "Practical application of data", "elements": ["If you're X, do Y", "Specific action", "Expected outcome"], "tip": ""},
    "item1": {"label": "Point 1", "purpose": "", "elements": ["The mistake/tip", "Why it happens", "The fix"], "tip": ""},
    "item2": {"label": "Point 2", "purpose": "", "elements": ["The mistake/tip", "Why it happens", "The fix"], "tip": ""},
    "item3": {"label": "Point 3", "purpose": "", "elements": ["The mistake/tip", "Why it happens", "The fix"], "tip": ""},
    "item4": {"label": "Point 4", "purpose": "", "elements": ["The mistake/tip", "Why it happens", "The fix"], "tip": ""},
    "item5": {"label": "Point 5", "purpose": "", "elements": ["The mistake/tip", "Why it happens", "The fix"], "tip": ""},
    "bonus":  {"label": "Bonus Point", "purpose": "Surprise extra value", "elements": ["Unexpected tip", "Why it's underrated", "Quick win"], "tip": "Bonus slides get high engagement — people feel they got more than promised."},
}


def generate_linkedin_carousel(
    topic: str,
    brand_name: str,
    industry: str,
    audience: str,
    num_slides: int,
    goal: str,
    style: str,
) -> dict:
    style_key = style if style in _CAROUSEL_STYLES else "educational"
    style_cfg = _CAROUSEL_STYLES[style_key]
    brand = brand_name or "your brand"
    topic_clean = topic or "business growth"
    aud = audience or "professionals"

    hook_text = (style_cfg["hook_formula"]
        .replace("{topic}", topic_clean)
        .replace("{audience}", aud)
        .replace("{brand}", brand)
        .replace("{pain}", f"struggling with {topic_clean}")
        .replace("{outcome}", f"mastering {topic_clean}")
        .replace("{num}", str(num_slides - 2))
        .replace("{number}", "100")
        .replace("{industry}", industry or "industry")
        .replace("{timeframe}", "30 days")
    )

    pattern = style_cfg["slide_pattern"]
    if num_slides < len(pattern):
        pattern = pattern[:num_slides]
    elif num_slides > len(pattern):
        extras = ["insight"] * (num_slides - len(pattern))
        pattern = pattern[:-1] + extras + [pattern[-1]]

    slides = []
    for idx, slide_type in enumerate(pattern):
        tmpl = _SLIDE_TEMPLATES.get(slide_type, _SLIDE_TEMPLATES["insight"])
        slide_headline = ""
        if slide_type == "hook":
            slide_headline = hook_text
        elif slide_type == "cta":
            slide_headline = f"Found this useful? Follow {brand} for more {topic_clean} insights for {aud}."
        elif slide_type in ("insight", "finding1", "finding2", "finding3"):
            slide_headline = f"[Key insight about {topic_clean} — add your specific data or perspective here]"
        elif slide_type == "example":
            slide_headline = f"Real example: How a {industry or 'business'} used {topic_clean} to [achieve outcome]"
        elif slide_type == "problem":
            slide_headline = f"Most {aud} are losing [time/money/opportunities] because of {topic_clean} mistakes"
        elif slide_type == "takeaway":
            slide_headline = f"TL;DR — Everything you need to know about {topic_clean} in one slide"
        elif slide_type.startswith("step"):
            n = slide_type.replace("step", "")
            slide_headline = f"Step {n}: [Action for {topic_clean}]"
        elif slide_type.startswith("item"):
            n = slide_type.replace("item", "")
            slide_headline = f"Mistake #{n}: [Common {topic_clean} mistake] — and how to fix it"
        else:
            slide_headline = f"[{tmpl['label']} — customize for {topic_clean}]"

        slides.append({
            "slide_num":    idx + 1,
            "total_slides": len(pattern),
            "type":         slide_type,
            "label":        tmpl["label"],
            "purpose":      tmpl.get("purpose", ""),
            "headline":     slide_headline,
            "elements":     tmpl.get("elements", []),
            "design_tip":   tmpl.get("tip", ""),
        })

    caption_template = f"""🧵 {hook_text}

Swipe through → (saves this for later!)

{''.join(f"Slide {s['slide_num']}: {s['label']}" + chr(10) for s in slides[:4])}...

If you found this valuable, repost to help other {aud} in {industry or 'your industry'}.

Follow {brand} for weekly {topic_clean} insights.

#{topic_clean.replace(' ', '')} #{industry.replace(' ', '') if industry else 'business'} #LinkedIn #IndianBusiness"""

    distribution_tips = [
        "Post Tuesday–Thursday between 8–10 AM IST for maximum reach on Indian LinkedIn.",
        "Slide 1 thumbnail is critical — it shows in the feed. Make it bold, high-contrast, and text-heavy.",
        "Comment on your own post within the first 60 minutes — it boosts early algorithmic distribution.",
        "Repurpose this carousel: break each slide into a standalone Twitter thread post.",
        f"Tag 2-3 relevant people in the caption who'd find this useful (not random tagging — genuine picks).",
        "First carousel usually gets 50% less reach than your 5th — consistency beats perfection.",
    ]

    return {
        "action":             "linkedin_carousel",
        "topic":              topic_clean,
        "brand":              brand,
        "style":              style_key,
        "goal":               goal,
        "audience":           aud,
        "total_slides":       len(slides),
        "hook_text":          hook_text,
        "slides":             slides,
        "caption_template":   caption_template,
        "design_guide":       style_cfg["design_tip"],
        "tone":               style_cfg["tone"],
        "distribution_tips":  distribution_tips,
        "summary": f"Generated {len(slides)}-slide {style_key} carousel on '{topic_clean}' for {aud}. Hook: '{hook_text[:60]}…'",
    }


# ── Influencer Outreach Generator (Round 11) ────────────────────────────────

_COLLAB_TYPES = {
    "product_review":    {"label": "Product Review",    "deliverable": "honest review post/reel", "timeline": "2 weeks post product receipt"},
    "sponsored_post":    {"label": "Sponsored Post",    "deliverable": "1 feed post + 3 stories",  "timeline": "within 7 days of brief approval"},
    "brand_ambassador":  {"label": "Brand Ambassador",  "deliverable": "monthly posts + exclusive discount code", "timeline": "ongoing 3-month engagement"},
    "event_coverage":    {"label": "Event Coverage",    "deliverable": "live stories + 1 post-event reel", "timeline": "day of event + 48h after"},
    "giveaway":          {"label": "Giveaway Collab",   "deliverable": "joint giveaway post + story countdown", "timeline": "coordinated campaign window"},
    "affiliate":         {"label": "Affiliate Partner", "deliverable": "custom discount code + tracking link in bio", "timeline": "30-day campaign with performance review"},
}

_TIER_RATES = {
    "nano":   {"range": "1K–10K",   "rate_post": "₹2K–₹10K",   "rate_reel": "₹5K–₹20K",   "negotiation_tip": "Offer free product + small fee — nano influencers prioritize authentic partnerships over money."},
    "micro":  {"range": "10K–100K", "rate_post": "₹10K–₹50K",  "rate_reel": "₹20K–₹80K",  "negotiation_tip": "Lead with creative freedom — micro influencers reject overly scripted briefs. Offer performance bonus on conversions."},
    "macro":  {"range": "100K–1M",  "rate_post": "₹50K–₹2L",   "rate_reel": "₹80K–₹3L",   "negotiation_tip": "Come with a clear brief and fast payment terms. Macro creators have busy pipelines — show you're organized."},
    "mega":   {"range": "1M+",      "rate_post": "₹2L–₹10L+",  "rate_reel": "₹3L–₹15L+",  "negotiation_tip": "Work through their management. Lead with brand story and long-term partnership potential, not just one-off fees."},
}

_FOLLOW_UP_TEMPLATES = [
    {
        "day": 3,
        "subject": "Quick follow-up — {brand} x {influencer} collab",
        "body": "Hi {influencer},\n\nJust wanted to bump this up in case my earlier message got buried! We're genuinely excited about working with you and would love to get on a quick call this week to discuss.\n\nWould {day_option_1} or {day_option_2} work for a 15-min chat?\n\nLooking forward to connecting!\nBest,\n{sender}",
    },
    {
        "day": 7,
        "subject": "Last nudge — {brand} partnership (closing spots this week)",
        "body": "Hi {influencer},\n\nWe're finalising our influencer roster for this campaign and have a spot reserved for you. We'd hate to close this without hearing back!\n\nIf you're not interested, no worries at all — just a quick reply to let us know and we won't bother you again.\n\nIf you are open to it, I'd love to chat this week.\n\nCheers,\n{sender}",
    },
]


def generate_influencer_outreach(
    brand_name: str,
    influencer_name: str,
    influencer_niche: str,
    influencer_platform: str,
    follower_count: int,
    campaign_goal: str,
    product_name: str,
    budget_range: str,
    deliverables: list,
    industry: str,
) -> dict:
    brand = brand_name or "Our Brand"
    influencer = influencer_name or "Creator"
    niche = influencer_niche or industry or "lifestyle"
    platform = influencer_platform or "instagram"
    product = product_name or f"{brand} product"

    if follower_count < 10000:
        tier_key = "nano"
    elif follower_count < 100000:
        tier_key = "micro"
    elif follower_count < 1000000:
        tier_key = "macro"
    else:
        tier_key = "mega"

    tier = _TIER_RATES[tier_key]
    deliv_list = deliverables if deliverables else ["1 feed post", "3 stories"]

    primary_email = f"""Subject: Collaboration Opportunity — {brand} x {influencer} 🤝

Hi {influencer},

I hope this finds you well! I'm [Your Name] from the partnerships team at {brand}.

We've been following your {niche} content on {platform.title()} and genuinely love the way you connect with your audience — your authentic style is exactly what we look for in a partner.

We'd love to explore a collaboration with you for our upcoming {campaign_goal} campaign featuring {product}. Here's what we have in mind:

✅ Campaign Goal: {campaign_goal.title()}
📦 Product/Service: {product}
📱 Platform: {platform.title()}
🎯 Deliverables: {", ".join(deliv_list)}
💰 Compensation: {budget_range or tier["rate_post"] + " (negotiable based on deliverables)"}
📅 Timeline: Flexible — we want this to work with your schedule

We believe your audience aligns perfectly with the people who would love {product}, and we want to give you full creative freedom to present it in your signature style.

Would you be open to a quick 15-minute call this week to discuss? I'd love to share more details and hear your ideas.

Looking forward to potentially working together!

Warm regards,
[Your Name]
{brand} Partnerships Team
[Email] | [Phone]"""

    negotiation_email = f"""Subject: Re: {brand} Collaboration — Let's Find the Right Fit

Hi {influencer},

Thank you for getting back to us! We appreciate your transparency about rates.

We completely understand your value, and we want to make this work for both sides. Here's our updated thinking:

💡 Counter-proposal:
• Upfront fee: [Adjusted amount]
• Performance bonus: Additional [X]% of tracked sales using your custom code
• Gifting: [Product worth ₹X] for you to keep regardless
• Long-term: If this campaign performs well, we'd love to discuss a 3-month ambassador arrangement

We're flexible on the deliverables too — if some formats work better for your audience, we're open to swapping. The goal is content your followers will actually engage with, not a forced brand message.

Can we hop on a 10-minute call to finalize? I want to make sure this feels right for you.

Best,
[Your Name]"""

    follow_ups = []
    for fu in _FOLLOW_UP_TEMPLATES:
        body_filled = (fu["body"]
            .replace("{brand}", brand)
            .replace("{influencer}", influencer)
            .replace("{day_option_1}", "Tuesday afternoon")
            .replace("{day_option_2}", "Thursday morning")
            .replace("{sender}", f"[Your Name], {brand} Partnerships"))
        follow_ups.append({
            "day": fu["day"],
            "subject": fu["subject"].replace("{brand}", brand).replace("{influencer}", influencer),
            "body": body_filled,
        })

    brief_outline = [
        f"Brand Overview: {brand} — {industry or 'leading brand'} focused on {campaign_goal}",
        f"Product to Feature: {product}",
        f"Key Message: [1-2 sentence message you want the audience to take away]",
        f"Dos: Authentic storytelling, show product in real use, tag @{brand.lower().replace(' ', '')}",
        f"Don'ts: No competitor mentions, no false claims, disclose #ad or #sponsored",
        f"Hashtags: #{brand.lower().replace(' ', '')} + [2-3 campaign hashtags]",
        f"Approval: Send draft 72h before posting for brand review",
        f"Payment: Within 7 days of content going live (with invoice)",
    ]

    do_dont = {
        "do": [
            "Research their recent posts before reaching out — mention a specific piece of content",
            "Keep the first email under 200 words — respect their time",
            "Give creative freedom — over-scripted briefs get rejected by top creators",
            "Pay fast — word travels fast in creator communities about slow-paying brands",
            "Send product before asking for content — let them experience it first",
        ],
        "dont": [
            "Offer 'exposure' as payment — it's insulting and will get you blocked",
            "Send a copy-paste email — creators can spot these immediately",
            "Demand exclusivity without extra compensation",
            "Set unrealistic timelines — quality content takes time",
            "Ask for all rights in perpetuity without acknowledging it in the rate",
        ],
    }

    return {
        "action":              "influencer_outreach",
        "brand":               brand,
        "influencer":          influencer,
        "platform":            platform,
        "niche":               niche,
        "follower_count":      follower_count,
        "tier":                tier_key,
        "tier_range":          tier["range"],
        "market_rate_post":    tier["rate_post"],
        "market_rate_reel":    tier["rate_reel"],
        "negotiation_tip":     tier["negotiation_tip"],
        "primary_outreach_email": primary_email,
        "negotiation_email":   negotiation_email,
        "follow_up_sequence":  follow_ups,
        "campaign_brief_outline": brief_outline,
        "do_dont":             do_dont,
        "summary": f"Generated outreach kit for {tier_key}-tier influencer {influencer} ({follower_count:,} followers) on {platform}. Market rate: {tier['rate_post']} per post.",
    }


# ── Viral Hook Generator (Round 10) ─────────────────────────────────────────

_HOOK_FORMULAS = {
    "question": {
        "template": "What if {brand} could {outcome} in {timeframe}?",
        "variants": [
            "Are you making this {industry} mistake that costs {pain}?",
            "What would your business look like if {positive_outcome}?",
            "Why do {percentage}% of {industry} businesses fail at {topic}?",
        ],
        "predicted_ctr_boost": "+34%",
        "best_platforms": ["linkedin", "twitter", "instagram"],
        "psychology": "Curiosity gap — forces the reader to keep scrolling to find the answer",
    },
    "shocking_stat": {
        "template": "{percentage}% of {audience} don't know {topic} — do you?",
        "variants": [
            "We analyzed {number} {industry} brands. Here's what shocked us about {topic}.",
            "{number} businesses lose {pain} every year because of this one {topic} mistake.",
            "In 90 days, {brand} went from 0 to {outcome}. Here's the exact playbook.",
        ],
        "predicted_ctr_boost": "+41%",
        "best_platforms": ["linkedin", "twitter"],
        "psychology": "Social proof + FOMO — numbers create credibility and urgency",
    },
    "bold_claim": {
        "template": "{topic} is dead. Here's what replaced it.",
        "variants": [
            "Stop using {old_approach}. This works 3x better for {industry}.",
            "I tried every {topic} strategy. Only this one actually worked for {brand}.",
            "The {topic} advice everyone gives is wrong. Here's why.",
        ],
        "predicted_ctr_boost": "+38%",
        "best_platforms": ["twitter", "linkedin", "instagram"],
        "psychology": "Pattern interrupt — contradicts expectations and demands attention",
    },
    "story_hook": {
        "template": "6 months ago, {brand} was struggling with {pain}. Today: {outcome}.",
        "variants": [
            "I almost gave up on {topic}. Then I discovered {solution}.",
            "Nobody told me this about {industry} when I started. Now I tell everyone.",
            "We made every mistake in the {topic} playbook. Here's what we learned.",
        ],
        "predicted_ctr_boost": "+29%",
        "best_platforms": ["instagram", "linkedin", "facebook"],
        "psychology": "Narrative arc — humans are wired for story structure (conflict → resolution)",
    },
    "list_hook": {
        "template": "{number} {industry} tactics that grew {brand}'s {metric} by {percentage}%",
        "variants": [
            "The only {number} {topic} tools you'll ever need (free + paid)",
            "{number} things I wish I knew about {industry} before starting",
            "{number} signs your {topic} strategy is broken (and how to fix each one)",
        ],
        "predicted_ctr_boost": "+26%",
        "best_platforms": ["linkedin", "instagram", "youtube"],
        "psychology": "Completeness bias — our brain wants to consume complete numbered lists",
    },
    "direct_address": {
        "template": "Attention {audience}: your {topic} approach is leaving {pain} on the table.",
        "variants": [
            "If you're a {audience} struggling with {topic}, this is for you.",
            "Hey {audience} — stop scrolling. This {topic} tip alone saved us {outcome}.",
            "{audience}: here's the {topic} shortcut no one is talking about.",
        ],
        "predicted_ctr_boost": "+31%",
        "best_platforms": ["instagram", "facebook", "linkedin"],
        "psychology": "Personal address — 'you/your' activates relevance filter in the brain",
    },
    "contrast": {
        "template": "Most {industry} brands do {old}. The best ones do {new}.",
        "variants": [
            "Before {topic}: {bad_state}. After {topic}: {good_state}. The difference? {solution}.",
            "Average {industry} result: {average}. Top 1% result: {excellent}. Here's the gap.",
            "What {industry} beginners do vs what pros do — a {topic} breakdown.",
        ],
        "predicted_ctr_boost": "+33%",
        "best_platforms": ["instagram", "linkedin", "twitter"],
        "psychology": "Contrast effect — comparison makes the gap immediately tangible",
    },
    "how_to": {
        "template": "How to {achieve_outcome} in {timeframe} (without {common_pain})",
        "variants": [
            "How {brand} increased {metric} by {percentage}% using only {topic}",
            "The step-by-step {topic} system that works for {industry} every time",
            "How to fix {pain} in under {timeframe} — no {expensive_solution} needed",
        ],
        "predicted_ctr_boost": "+22%",
        "best_platforms": ["youtube", "linkedin", "instagram"],
        "psychology": "Utility promise — clear ROI for reading makes the click feel worth it",
    },
}

_PLATFORM_HOOK_TIPS = {
    "linkedin": "Keep first line under 200 chars — LinkedIn truncates at 'see more'. Use line breaks for rhythm. Professional but personal tone wins.",
    "twitter":  "Lead with the hook in tweet 1. Save the stat or punchline for tweet 2. Threads with 5-10 tweets outperform single tweets by 6x.",
    "instagram":"First 125 chars show before 'more'. Use emoji strategically (1-2 max). Stories hooks need to work in 3 seconds.",
    "facebook": "Questions outperform statements by 2x on Facebook. Emotional story hooks drive highest shares.",
    "youtube":  "Thumbnail + title together are your hook. Start video with a pattern interrupt in first 5 seconds. Promise the payoff early.",
    "whatsapp": "Short, direct, conversational. Use 'You' language. Value-first without the fluff — people read WhatsApp fast.",
}

def generate_viral_hooks(
    topic: str,
    brand_name: str,
    industry: str,
    platforms: list,
    goal: str,
) -> dict:
    hooks_generated = []
    topic_clean = topic.strip() or "your product"
    brand_clean = brand_name.strip() or "your brand"
    industry_clean = industry.strip() or "your industry"

    for formula_key, formula in _HOOK_FORMULAS.items():
        filled_main = (formula["template"]
            .replace("{brand}", brand_clean)
            .replace("{industry}", industry_clean)
            .replace("{topic}", topic_clean)
            .replace("{audience}", f"{industry_clean} professionals")
            .replace("{outcome}", "10x your results")
            .replace("{timeframe}", "30 days")
            .replace("{pain}", "time and money")
            .replace("{percentage}", "73")
            .replace("{number}", "7")
            .replace("{metric}", "engagement")
            .replace("{solution}", "this one strategy")
            .replace("{positive_outcome}", "you never worried about {topic} again".replace("{topic}", topic_clean))
            .replace("{old_approach}", f"generic {topic_clean}")
            .replace("{old}", "follow the crowd")
            .replace("{new}", "lead with data")
            .replace("{bad_state}", "stuck and frustrated")
            .replace("{good_state}", "scaling confidently")
            .replace("{average}", "2% growth")
            .replace("{excellent}", "47% growth")
            .replace("{achieve_outcome}", f"master {topic_clean}")
            .replace("{common_pain}", "expensive consultants")
            .replace("{expensive_solution}", "agencies")
        )

        filled_variants = []
        for v in formula["variants"][:2]:
            filled_variants.append(
                v.replace("{brand}", brand_clean)
                 .replace("{industry}", industry_clean)
                 .replace("{topic}", topic_clean)
                 .replace("{audience}", f"{industry_clean} owners")
                 .replace("{outcome}", "10x revenue")
                 .replace("{timeframe}", "30 days")
                 .replace("{pain}", "₹50,000/mo")
                 .replace("{percentage}", "73")
                 .replace("{number}", "7")
                 .replace("{metric}", "leads")
                 .replace("{solution}", "automation")
                 .replace("{positive_outcome}", f"never struggled with {topic_clean} again")
                 .replace("{old_approach}", f"outdated {topic_clean}")
                 .replace("{old}", "guesswork")
                 .replace("{new}", "data-driven content")
                 .replace("{bad_state}", "0 leads/month")
                 .replace("{good_state}", "50 leads/month")
                 .replace("{average}", "5% CTR")
                 .replace("{excellent}", "22% CTR")
                 .replace("{achieve_outcome}", f"dominate {topic_clean}")
                 .replace("{common_pain}", "burning budget")
                 .replace("{expensive_solution}", "agencies")
            )

        relevant_platforms = [p for p in platforms if p in formula["best_platforms"]]
        platform_score = len(relevant_platforms) / max(len(platforms), 1)

        hooks_generated.append({
            "formula": formula_key.replace("_", " ").title(),
            "main_hook": filled_main,
            "variants": filled_variants,
            "ctr_boost": formula["predicted_ctr_boost"],
            "psychology": formula["psychology"],
            "best_for": formula["best_platforms"],
            "platform_fit": "High" if platform_score >= 0.5 else "Medium",
            "recommended": platform_score >= 0.5,
        })

    hooks_generated.sort(key=lambda h: (h["recommended"], h["ctr_boost"]), reverse=True)

    platform_tips = {p: _PLATFORM_HOOK_TIPS.get(p, "Lead with the most valuable insight first.") for p in platforms}

    top_hook = hooks_generated[0] if hooks_generated else {}

    return {
        "action":       "viral_hook_generator",
        "topic":        topic_clean,
        "brand":        brand_clean,
        "industry":     industry_clean,
        "goal":         goal,
        "platforms":    platforms,
        "total_hooks":  len(hooks_generated),
        "hooks":        hooks_generated,
        "platform_tips": platform_tips,
        "top_pick":     top_hook.get("formula", ""),
        "top_hook_text": top_hook.get("main_hook", ""),
        "pro_tip": f"Test 2-3 hooks per week. Track 48h engagement. The hook that gets 2x comments becomes your content pillar for the month.",
        "summary": f"Generated {len(hooks_generated)} viral hook formulas for '{topic_clean}'. Top pick: {top_hook.get('formula','')} ({top_hook.get('ctr_boost','')}) — {top_hook.get('psychology','')}.",
    }


# ── AI Content Scheduler (Round 4) ───────────────────────────────────────────

OPTIMAL_TIMES = {
    "instagram":  [("08:00", "Morning scroll"), ("12:30", "Lunch break"), ("19:00", "Evening prime")],
    "linkedin":   [("08:30", "Pre-work"), ("12:00", "Lunch"), ("17:30", "End of day")],
    "twitter":    [("09:00", "Morning"), ("13:00", "Afternoon"), ("20:00", "Night")],
    "facebook":   [("09:00", "Morning"), ("15:00", "Afternoon"), ("21:00", "Night")],
    "youtube":    [("14:00", "Afternoon"), ("20:00", "Prime time")],
}

CONTENT_PILLARS = ["Educational", "Promotional", "Engagement", "Behind-the-Scenes", "User Stories", "Trending"]


async def plan_content_scheduler(
    brand_name: str,
    industry:   str,
    platforms:  list[str],
    days:       int = 7,
    goal:       str = "brand awareness",
    audience:   str = "general",
    language:   str = "en",
) -> dict:
    """Rich AI content scheduler with optimal times, captions, and pillar distribution."""
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL
    from datetime import datetime, timedelta, timezone
    import json

    today = datetime.now(timezone.utc)
    platform_str = ", ".join(platforms)

    system = f"""You are an expert social media strategist for Indian businesses.
Generate a {days}-day content schedule for {brand_name} ({industry}).
Platforms: {platform_str}. Goal: {goal}. Audience: {audience}. Language: {language}.

Return JSON with this structure:
{{
  "summary": "one-line schedule overview",
  "pillar_distribution": {{"Educational": 30, "Promotional": 20, "Engagement": 25, "Behind-the-Scenes": 15, "Trending": 10}},
  "schedule": [
    {{
      "day": 1,
      "date": "Mon Jul 21",
      "pillar": "Educational",
      "topic": "specific topic for the day",
      "posts": [
        {{
          "platform": "instagram",
          "time": "19:00",
          "time_label": "Evening prime",
          "caption": "ready-to-post caption (2-3 sentences + emojis for the platform)",
          "hashtags": ["#tag1", "#tag2"],
          "content_tip": "one actionable tip for this post"
        }}
      ]
    }}
  ]
}}
Return ONLY valid JSON."""

    try:
        raw = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": f"Create {days}-day schedule starting {today.strftime('%a %b %d')}."},
            ],
            model=OLLAMA_MODEL,
            max_tokens=2000,
        )
        raw = raw.strip()
        if "{" in raw:
            raw = raw[raw.index("{"):]
            if "}" in raw:
                raw = raw[:raw.rindex("}") + 1]
        result = json.loads(raw)
        if "schedule" not in result:
            raise ValueError("missing schedule key")
        return {"action": "content_scheduler", **result, "days": days, "platforms": platforms}
    except Exception as e:
        logger.error("Content scheduler failed: %s", e)
        pillars = CONTENT_PILLARS[:days]
        schedule = []
        for i in range(days):
            day_dt = today + timedelta(days=i + 1)
            pillar = pillars[i % len(pillars)]
            posts = []
            for plat in platforms:
                times = OPTIMAL_TIMES.get(plat, [("12:00", "Midday")])
                t = times[0]
                posts.append({
                    "platform": plat,
                    "time": t[0],
                    "time_label": t[1],
                    "caption": f"[{brand_name}] {pillar} post for {industry} — {day_dt.strftime('%a')} 🚀",
                    "hashtags": [f"#{industry.replace(' ', '')}", f"#{brand_name.replace(' ', '')}"],
                    "content_tip": f"Keep {pillar.lower()} content under 150 words for best engagement.",
                })
            schedule.append({
                "day": i + 1,
                "date": day_dt.strftime("%a %b %d"),
                "pillar": pillar,
                "topic": f"{brand_name} — {pillar} content",
                "posts": posts,
            })
        return {
            "action": "content_scheduler",
            "summary": f"{days}-day schedule for {brand_name} across {platform_str}",
            "pillar_distribution": {"Educational": 30, "Promotional": 20, "Engagement": 25, "Behind-the-Scenes": 15, "Trending": 10},
            "schedule": schedule,
            "days": days,
            "platforms": platforms,
            "demo_mode": True,
        }


# ── A/B Copy Tester (Round 5) ─────────────────────────────────────────────────

_HOOK_TYPES = [
    "Bold Question",
    "Shocking Statistic",
    "Relatable Pain Point",
    "Bold Claim / Contrarian",
    "Story Opening",
    "Listicle Hook",
    "Social Proof",
    "Curiosity Gap",
]

_ENGAGEMENT_SIGNALS = {
    "Bold Question":        {"base": 72, "comment_boost": 15, "share_boost": 5},
    "Shocking Statistic":   {"base": 68, "comment_boost": 8,  "share_boost": 18},
    "Relatable Pain Point": {"base": 75, "comment_boost": 20, "share_boost": 10},
    "Bold Claim / Contrarian": {"base": 70, "comment_boost": 25, "share_boost": 12},
    "Story Opening":        {"base": 65, "comment_boost": 18, "share_boost": 8},
    "Listicle Hook":        {"base": 60, "comment_boost": 5,  "share_boost": 22},
    "Social Proof":         {"base": 63, "comment_boost": 6,  "share_boost": 15},
    "Curiosity Gap":        {"base": 78, "comment_boost": 12, "share_boost": 9},
}


async def generate_ab_copy(
    topic:      str,
    platform:   str = "linkedin",
    brand_name: str = "",
    industry:   str = "",
    goal:       str = "engagement",
    variations: int = 4,
    language:   str = "en",
) -> dict:
    """Generate N post variations with different hooks, score each, rank by predicted engagement."""
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL
    import json, random

    variations = min(max(variations, 2), 6)
    hooks = random.sample(_HOOK_TYPES, variations)

    system = f"""You are an elite social media copywriter specializing in {platform} for Indian businesses.
Topic: {topic}. Brand: {brand_name or 'the brand'}. Industry: {industry or 'general'}. Goal: {goal}. Language: {language}.

Generate {variations} distinct post variations — each using a DIFFERENT hook style from this list: {hooks}.

Return JSON:
{{
  "variations": [
    {{
      "id": 1,
      "hook_type": "Bold Question",
      "hook_line": "first sentence (the hook)",
      "full_post": "complete ready-to-post text (platform-appropriate length, emojis if suitable)",
      "cta": "call to action used",
      "why_it_works": "one sentence on why this hook drives {goal}",
      "predicted_engagement": 74,
      "predicted_comments": 12,
      "predicted_shares": 8
    }}
  ],
  "winner_id": 1,
  "winner_reason": "why variation 1 is predicted to win",
  "testing_advice": "how to A/B test these effectively"
}}
Return ONLY valid JSON."""

    try:
        raw = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": f"Generate {variations} A/B variations for: {topic}"},
            ],
            model=OLLAMA_MODEL,
            max_tokens=1800,
        )
        raw = raw.strip()
        if "{" in raw:
            raw = raw[raw.index("{"):]
            if "}" in raw:
                raw = raw[:raw.rindex("}") + 1]
        result = json.loads(raw)
        return {"action": "ab_copy_test", "topic": topic, "platform": platform, **result}
    except Exception as e:
        logger.error("A/B copy test failed: %s", e)
        # Demo fallback
        demo_variations = []
        for i, hook in enumerate(hooks):
            sig = _ENGAGEMENT_SIGNALS.get(hook, {"base": 65, "comment_boost": 10, "share_boost": 8})
            eng = sig["base"] + random.randint(-5, 5)
            demo_variations.append({
                "id": i + 1,
                "hook_type": hook,
                "hook_line": f"[{hook}] {topic[:60]}...",
                "full_post": f"[Demo] {hook} variation for '{topic}' on {platform}. This is where your {brand_name or 'brand'} story begins. #{industry.replace(' ', '') if industry else 'business'} #India",
                "cta": "Comment your thoughts below 👇" if i % 2 == 0 else "Share if this resonates ♻️",
                "why_it_works": f"{hook} hooks work well for {goal} on {platform}.",
                "predicted_engagement": eng,
                "predicted_comments": sig["comment_boost"] + random.randint(-3, 3),
                "predicted_shares": sig["share_boost"] + random.randint(-2, 2),
            })
        best = max(demo_variations, key=lambda x: x["predicted_engagement"])
        return {
            "action": "ab_copy_test",
            "topic": topic,
            "platform": platform,
            "variations": demo_variations,
            "winner_id": best["id"],
            "winner_reason": f"{best['hook_type']} has the highest predicted engagement score ({best['predicted_engagement']}%) for {goal}.",
            "testing_advice": "Run each variation for 24h. Compare comment rate (not just likes). Pause lowest performer at 6h if gap is >20%.",
            "demo_mode": True,
        }


# ── Brand Mention Responder (Round 6) ─────────────────────────────────────────

_MENTION_SENTIMENT = {
    "positive":  {"color": "#10b981", "urgency": "low",      "action": "Engage warmly"},
    "neutral":   {"color": "#6b7280", "urgency": "low",      "action": "Acknowledge"},
    "question":  {"color": "#3b82f6", "urgency": "medium",   "action": "Answer promptly"},
    "complaint": {"color": "#f59e0b", "urgency": "high",     "action": "Resolve quickly"},
    "negative":  {"color": "#ef4444", "urgency": "high",     "action": "Address immediately"},
    "pr_risk":   {"color": "#dc2626", "urgency": "critical", "action": "Escalate now"},
}


async def respond_to_mentions(
    mentions:    list[dict],
    brand_name:  str = "",
    brand_voice: str = "professional",
    industry:    str = "",
    language:    str = "en",
) -> dict:
    """
    Categorize and draft replies for social media mentions/comments.
    Each mention: {id, platform, author, text, likes, is_verified}
    """
    from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL
    import json

    if not mentions:
        return {"error": "No mentions provided"}

    system = f"""You are a social media community manager for {brand_name or 'a brand'} ({industry or 'general'}).
Brand voice: {brand_voice}. Language: {language}.

Analyze each mention and return JSON array:
[
  {{
    "id": "same id as input",
    "sentiment": "positive|neutral|question|complaint|negative|pr_risk",
    "sentiment_score": 0-100,
    "key_issue": "what the person is really saying (one phrase)",
    "reply": "ready-to-post reply (platform-appropriate, brand voice, under 280 chars for Twitter)",
    "urgency": "low|medium|high|critical",
    "action": "what to do",
    "pr_risk": true/false,
    "risk_reason": "why it's a risk (or null)"
  }}
]
Return ONLY the JSON array."""

    mentions_text = "\n".join(
        f"[{m.get('id','?')}] @{m.get('author','?')} on {m.get('platform','?')}: {m.get('text','')}"
        for m in mentions
    )

    try:
        raw = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": f"Analyze and draft replies for these mentions:\n{mentions_text}"},
            ],
            model=OLLAMA_MODEL,
            max_tokens=2000,
        )
        raw = raw.strip()
        if "[" in raw:
            raw = raw[raw.index("["):]
            if "]" in raw:
                raw = raw[:raw.rindex("]") + 1]
        results = json.loads(raw)
    except Exception as e:
        logger.error("Mention responder failed: %s", e)
        # Demo fallback
        import random
        sentiments = ["positive", "question", "complaint", "neutral", "negative"]
        results = []
        for m in mentions:
            sent = random.choice(sentiments)
            info = _MENTION_SENTIMENT[sent]
            results.append({
                "id": m.get("id", ""),
                "sentiment": sent,
                "sentiment_score": random.randint(20, 90),
                "key_issue": m.get("text", "")[:50],
                "reply": f"Hi @{m.get('author', 'there')}! Thanks for reaching out. Our team at {brand_name or 'us'} will get back to you shortly. 🙏",
                "urgency": info["urgency"],
                "action": info["action"],
                "pr_risk": sent == "pr_risk",
                "risk_reason": None,
            })

    # Merge with original mention data and add color
    id_map = {m.get("id", str(i)): m for i, m in enumerate(mentions)}
    enriched = []
    pr_risks = []
    for r in results:
        original = id_map.get(str(r.get("id", "")), {})
        info = _MENTION_SENTIMENT.get(r.get("sentiment", "neutral"), _MENTION_SENTIMENT["neutral"])
        r["color"]    = info["color"]
        r["platform"] = original.get("platform", "")
        r["author"]   = original.get("author", "")
        r["original_text"] = original.get("text", "")
        r["likes"]    = original.get("likes", 0)
        enriched.append(r)
        if r.get("pr_risk"):
            pr_risks.append(r)

    stats = {
        "total": len(enriched),
        "positive":  sum(1 for r in enriched if r["sentiment"] == "positive"),
        "questions": sum(1 for r in enriched if r["sentiment"] == "question"),
        "complaints": sum(1 for r in enriched if r["sentiment"] in ("complaint", "negative")),
        "pr_risks":  len(pr_risks),
        "critical":  sum(1 for r in enriched if r["urgency"] == "critical"),
    }

    return {
        "action":     "mention_responder",
        "brand_name": brand_name,
        "stats":      stats,
        "mentions":   sorted(enriched, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x.get("urgency"), 4)),
        "pr_risks":   pr_risks,
        "health":     "Critical" if pr_risks else ("At Risk" if stats["complaints"] > stats["total"] * 0.3 else "Healthy"),
    }


# ── Social ROI Dashboard (Round 7) ────────────────────────────────────────────

def calculate_social_roi(
    campaigns: list,
    brand_name: str = "",
    period: str = "",
    language: str = "en",
) -> dict:
    if not campaigns:
        campaigns = [
            {"platform": "Meta", "spend": 15000, "impressions": 120000, "clicks": 3600, "leads": 180, "conversions": 22, "revenue": 110000},
            {"platform": "Google", "spend": 20000, "impressions": 85000, "clicks": 4250, "leads": 212, "conversions": 35, "revenue": 175000},
            {"platform": "LinkedIn", "spend": 10000, "impressions": 32000, "clicks": 960, "leads": 96, "conversions": 8, "revenue": 64000},
        ]

    total_spend = total_rev = total_leads = total_conv = total_impressions = total_clicks = 0
    platform_rows = []

    for c in campaigns:
        spend  = float(c.get("spend", 0) or 0)
        rev    = float(c.get("revenue", 0) or 0)
        leads  = float(c.get("leads", 0) or 0)
        conv   = float(c.get("conversions", 0) or 0)
        impr   = float(c.get("impressions", 0) or 0)
        clicks = float(c.get("clicks", 0) or 0)

        cpl    = round(spend / leads, 2)  if leads  else 0
        cpa    = round(spend / conv, 2)   if conv   else 0
        roas   = round(rev   / spend, 2)  if spend  else 0
        ctr    = round(clicks / impr * 100, 2) if impr else 0
        cvr    = round(conv  / leads * 100, 1) if leads else 0
        profit = round(rev - spend, 0)

        total_spend += spend; total_rev += rev; total_leads += leads
        total_conv  += conv;  total_impressions += impr; total_clicks += clicks

        platform_rows.append({
            "platform":    c.get("platform", "Unknown"),
            "spend":       spend, "revenue": rev, "profit": profit,
            "impressions": impr,  "clicks": clicks, "leads": leads, "conversions": conv,
            "cpl": cpl, "cpa": cpa, "roas": roas, "ctr": ctr, "cvr": cvr,
            "roi_pct": round((rev - spend) / spend * 100, 1) if spend else 0,
            "grade": "Excellent" if roas >= 4 else ("Good" if roas >= 2 else ("Average" if roas >= 1 else "Poor")),
        })

    platform_rows.sort(key=lambda x: x["roas"], reverse=True)

    overall_roas = round(total_rev / total_spend, 2) if total_spend else 0
    overall_cpl  = round(total_spend / total_leads, 2) if total_leads else 0
    overall_cpa  = round(total_spend / total_conv, 2)  if total_conv  else 0
    best = platform_rows[0]["platform"] if platform_rows else "N/A"
    worst = platform_rows[-1]["platform"] if len(platform_rows) > 1 else "N/A"

    recommendations = []
    for row in platform_rows:
        if row["roas"] < 1:
            recommendations.append(f"Pause or reduce budget on {row['platform']} — ROAS {row['roas']}x below break-even.")
        elif row["roas"] >= 4:
            recommendations.append(f"Scale {row['platform']} — ROAS {row['roas']}x is excellent. Increase budget 20-30%.")
        if row["cpl"] > overall_cpl * 1.5:
            recommendations.append(f"{row['platform']} CPL (₹{row['cpl']:,.0f}) is 50%+ above average — review targeting.")

    return {
        "action":       "social_roi",
        "brand_name":   brand_name,
        "period":       period,
        "totals": {
            "spend":       round(total_spend, 0),
            "revenue":     round(total_rev, 0),
            "profit":      round(total_rev - total_spend, 0),
            "impressions": round(total_impressions, 0),
            "clicks":      round(total_clicks, 0),
            "leads":       round(total_leads, 0),
            "conversions": round(total_conv, 0),
            "roas":        overall_roas,
            "cpl":         overall_cpl,
            "cpa":         overall_cpa,
            "roi_pct":     round((total_rev - total_spend) / total_spend * 100, 1) if total_spend else 0,
        },
        "platforms":        platform_rows,
        "best_platform":    best,
        "worst_platform":   worst,
        "recommendations":  recommendations,
        "health":           "Excellent" if overall_roas >= 4 else ("Good" if overall_roas >= 2 else ("Needs Review" if overall_roas >= 1 else "Losing Money")),
    }


# ── Employee Advocacy Generator (Round 9) ────────────────────────────────────

_ADVOCACY_HOOKS = {
    "achievement": ["Proud moment 🎉", "Big news from our team!", "We did it!", "Exciting announcement →", "Something we've been working hard on..."],
    "culture":     ["Why I love working here:", "Real talk about our culture 🙌", "This is what great teams look like", "3 months in and here's what I've learned:", "Our team just did something special —"],
    "product":     ["Our product just leveled up 🚀", "We just shipped something I'm excited about", "If you work in [industry], you need to see this:", "This is the feature I've been waiting for →", "We built this because our customers asked for it:"],
    "hiring":      ["We're growing! 🎯", "Want to join our team?", "Looking for someone special —", "We're hiring and here's why you should apply:", "Best role I've ever worked in — and we're adding more people:"],
    "milestone":   ["We just hit a milestone I'll never forget:", "1 year ago vs today — the growth is real 📈", "We crossed a number that felt impossible 6 months ago:", "Grateful, proud, and just getting started —", "Some numbers we're celebrating this week:"],
}

_PERSONA_TIPS = {
    "founder":     "Share the 'why behind the what' — your personal conviction is your brand",
    "sales":       "Lead with customer outcome, not product features — stories sell",
    "engineer":    "Show the problem you solved and the elegant solution — geeks love details",
    "hr":          "Highlight people and culture — humanise the brand authentically",
    "marketing":   "Use data + emotion combo — numbers give credibility, story gives resonance",
    "default":     "Speak from personal experience — 'I' outperforms 'we' on personal profiles",
}


async def generate_employee_advocacy(
    company_name: str,
    news_or_achievement: str,
    employee_role: str = "",
    industry: str = "",
    tone: str = "professional",
    platforms: list | None = None,
    num_variants: int = 3,
    language: str = "en",
) -> dict:
    platforms = platforms or ["linkedin"]
    role_key = next((k for k in _PERSONA_TIPS if k in employee_role.lower()), "default")
    persona_tip = _PERSONA_TIPS[role_key]

    # Pick hook category from content
    content_lower = news_or_achievement.lower()
    hook_cat = "achievement"
    if any(w in content_lower for w in ["hire", "join", "team", "recruit"]):
        hook_cat = "hiring"
    elif any(w in content_lower for w in ["launch", "ship", "release", "feature", "product"]):
        hook_cat = "product"
    elif any(w in content_lower for w in ["culture", "value", "team", "office", "event"]):
        hook_cat = "culture"
    elif any(w in content_lower for w in ["milestone", "year", "growth", "revenue", "customers"]):
        hook_cat = "milestone"

    hooks = _ADVOCACY_HOOKS[hook_cat][:num_variants]

    try:
        from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL
        posts_raw = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": f"You generate {num_variants} distinct LinkedIn/social posts for employee advocacy. Language: {language}. Tone: {tone}. Each post: 3-5 sentences, starts with a hook, ends with a question or CTA. Output as JSON array with keys: hook, body, cta, hashtags (array of 3-5)."},
                {"role": "user", "content": f"Company: {company_name}. News: {news_or_achievement}. Role: {employee_role or 'team member'}. Generate {num_variants} variants for {', '.join(platforms)}."},
            ],
            model=OLLAMA_MODEL, max_tokens=800,
        )
        import json as _json
        start = posts_raw.find("[")
        end = posts_raw.rfind("]") + 1
        variants = _json.loads(posts_raw[start:end]) if start >= 0 else []
    except Exception:
        variants = []

    if not variants:
        variants = [
            {
                "hook": hooks[i % len(hooks)],
                "body": f"{news_or_achievement}\n\nAs part of the {company_name} team, I'm incredibly proud of what we've achieved. This milestone represents months of hard work, collaboration, and customer obsession.",
                "cta": "What's a recent win your team celebrated? Drop it in the comments 👇",
                "hashtags": [f"#{company_name.replace(' ','')}", f"#{industry.replace(' ','') or 'Innovation'}", "#TeamWin", "#GrowthMindset", "#ProudMoment"],
                "engagement_tip": f"Tip {i+1}: Post between 8-10 AM on weekdays for 3x more reach on LinkedIn.",
                "persona_angle": f"As a {employee_role or 'team member'}: {persona_tip}",
            }
            for i in range(num_variants)
        ]
    else:
        for i, v in enumerate(variants):
            v["engagement_tip"] = f"Tip {i+1}: Tag 2-3 teammates to boost organic reach by 40%."
            v["persona_angle"] = persona_tip

    return {
        "action":           "employee_advocacy",
        "company_name":     company_name,
        "news":             news_or_achievement,
        "employee_role":    employee_role,
        "platforms":        platforms,
        "total_variants":   len(variants),
        "variants":         variants,
        "persona_tip":      persona_tip,
        "best_practice": [
            "Post from personal profile — personal posts get 3-8x more reach than company pages",
            "Add your own 1-2 sentence opinion before the main content",
            "Post same content 2 weeks apart — 90% of followers won't see it the first time",
            "Reply to every comment in the first hour — triggers the algorithm",
        ],
    }


# ── Competitor Content Spy (Round 8) ──────────────────────────────────────────

_CONTENT_THEMES = [
    "educational_tips", "product_showcase", "customer_testimonials",
    "behind_the_scenes", "industry_news", "offers_discounts",
    "thought_leadership", "employee_stories", "events_webinars", "memes_humor",
]

_PLATFORM_BENCHMARKS = {
    "instagram": {"post_freq": "1/day", "best_time": "7-9 PM IST", "top_format": "Reels 15-30s", "avg_engagement": "3-5%"},
    "linkedin":  {"post_freq": "3-5/week", "best_time": "8-10 AM IST Tue-Thu", "top_format": "Carousel / Long-form", "avg_engagement": "2-4%"},
    "twitter":   {"post_freq": "3-5/day", "best_time": "9 AM & 6 PM IST", "top_format": "Threads", "avg_engagement": "0.5-1%"},
    "facebook":  {"post_freq": "1-2/day", "best_time": "1-3 PM IST", "top_format": "Video + Image", "avg_engagement": "1-2%"},
    "youtube":   {"post_freq": "2/week", "best_time": "Fri 4-6 PM IST", "top_format": "8-15 min how-to", "avg_engagement": "4-6%"},
}


def competitor_content_spy(
    brand_name: str,
    competitors: list,
    industry: str = "",
    platforms: list | None = None,
    language: str = "en",
) -> dict:
    if not competitors:
        competitors = [
            {"name": "CompetitorA", "strengths": "Daily Reels, strong CTA", "weaknesses": "No LinkedIn, no regional content", "estimated_followers": 45000, "avg_engagement": 4.2, "top_content": "Product demos + customer stories"},
            {"name": "CompetitorB", "strengths": "Thought leadership on LinkedIn", "weaknesses": "Inconsistent posting, no video", "estimated_followers": 28000, "avg_engagement": 2.8, "top_content": "Industry reports + CEO posts"},
            {"name": "CompetitorC", "strengths": "Heavy ad spend on Meta", "weaknesses": "Generic content, low organic reach", "estimated_followers": 62000, "avg_engagement": 1.1, "top_content": "Offer-based ads, discount posts"},
        ]
    platforms = platforms or ["instagram", "linkedin"]

    # Gap analysis — what competitors aren't doing
    comp_strengths = " ".join(c.get("strengths", "") for c in competitors).lower()
    comp_weaknesses = " ".join(c.get("weaknesses", "") for c in competitors).lower()

    gaps = []
    if "regional" not in comp_strengths and "tamil" not in comp_strengths and "hindi" not in comp_strengths:
        gaps.append({"gap": "Regional Language Content", "opportunity": f"None of your competitors post in regional languages. {brand_name} can own Tamil/Hindi audience.", "priority": "High"})
    if "video" not in comp_strengths and "reel" not in comp_strengths:
        gaps.append({"gap": "Short-form Video (Reels/Shorts)", "opportunity": "Competitors are text-heavy. Own Reels/Shorts to drive 3x more reach.", "priority": "High"})
    if "customer" not in comp_strengths and "testimonial" not in comp_strengths:
        gaps.append({"gap": "Customer Success Stories", "opportunity": "No competitor showcases real ROI stories. Feature case studies to build trust.", "priority": "Medium"})
    if "behind" not in comp_strengths and "team" not in comp_strengths:
        gaps.append({"gap": "Behind-the-Scenes / Culture Content", "opportunity": "Show the human side — team stories, office culture. Builds authentic brand.", "priority": "Medium"})
    if "linkedin" not in comp_strengths:
        gaps.append({"gap": "LinkedIn Thought Leadership", "opportunity": "Competitors missing LinkedIn. Publish weekly insights from founder/CEO to capture B2B.", "priority": "High"})

    # Counter strategy per platform
    counter_plan = []
    for plat in platforms:
        bench = _PLATFORM_BENCHMARKS.get(plat, {})
        counter_plan.append({
            "platform": plat,
            "post_frequency": bench.get("post_freq", "3-5/week"),
            "best_posting_time": bench.get("best_time", ""),
            "top_format": bench.get("top_format", ""),
            "industry_avg_engagement": bench.get("avg_engagement", ""),
            "recommended_themes": [
                t.replace("_", " ").title() for t in _CONTENT_THEMES
                if t not in comp_strengths.replace(" ", "_")
            ][:4],
            "90_day_goal": f"Surpass competitor engagement rate on {plat} by focusing on gaps they ignore",
        })

    # Content calendar seeds (3 posts per platform)
    calendar_seeds = []
    for plat in platforms[:2]:
        calendar_seeds.append({"platform": plat, "week": "Week 1", "post": f"Before/After: How {brand_name} helped a customer save time — with real numbers", "format": "Carousel", "gap_addressed": "Customer success"})
        calendar_seeds.append({"platform": plat, "week": "Week 2", "post": f"[Regional Language] Why {industry or 'your industry'} businesses trust {brand_name} — 30s Reel", "format": "Reel/Short", "gap_addressed": "Regional + video"})
        calendar_seeds.append({"platform": plat, "week": "Week 3", "post": f"Founder's take: 3 mistakes {industry or 'SMB'} owners make (and how to avoid them)", "format": "Long-form / Thread", "gap_addressed": "Thought leadership"})

    best_comp = max(competitors, key=lambda c: float(c.get("avg_engagement", 0))) if competitors else {}
    avg_comp_engagement = sum(float(c.get("avg_engagement", 0)) for c in competitors) / len(competitors) if competitors else 0

    return {
        "action":            "competitor_spy",
        "brand_name":        brand_name,
        "industry":          industry,
        "competitors_analyzed": len(competitors),
        "competitor_profiles":  competitors,
        "content_gaps":         gaps,
        "counter_strategy":     counter_plan,
        "calendar_seeds":       calendar_seeds,
        "benchmark_to_beat":    best_comp.get("name", ""),
        "avg_competitor_engagement": round(avg_comp_engagement, 1),
        "summary":           f"Found {len(gaps)} content gaps competitors are missing. Focus on {gaps[0]['gap'] if gaps else 'video content'} first — highest ROI opportunity.",
    }
