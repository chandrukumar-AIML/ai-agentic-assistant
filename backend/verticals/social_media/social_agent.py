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

logger   = logging.getLogger(__name__)
settings = get_settings()

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
        return await generate_reel_script(
            topic=payload.get("topic", ""),
            duration=payload.get("duration", 30),
            platform=payload.get("reel_platform", "instagram"),
            hook_style=payload.get("hook_style", "question"),
            brand_name=payload.get("brand_name", ""),
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
            topic=payload.get("topic", ""),
            brand_name=payload.get("brand_name", ""),
            language=language,
            audience=payload.get("audience", ""),
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
        return await generate_bulk_posts(
            topics=payload.get("topics", []),
            platform=platform,
            tone=payload.get("tone", "professional"),
            brand_name=payload.get("brand_name", ""),
            language=language,
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

    elif action == "whatsapp_content":
        return await generate_whatsapp_content(
            content_type=payload.get("content_type", "broadcast"),
            brand_name=payload.get("brand_name", ""),
            industry=payload.get("industry", ""),
            product_name=payload.get("product_name", ""),
            offer=payload.get("offer", ""),
            customer_name=payload.get("customer_name", "Customer"),
            language=language,
            tone=payload.get("tone", "friendly"),
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

    return {"error": f"Unknown social action: {action}"}


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
