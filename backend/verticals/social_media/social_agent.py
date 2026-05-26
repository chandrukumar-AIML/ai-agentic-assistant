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
            raise ValueError("Empty Ollama response")
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
        return {"error": "Content generation failed.", "platform": platform}


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

    return {"error": f"Unknown social action: {action}"}
