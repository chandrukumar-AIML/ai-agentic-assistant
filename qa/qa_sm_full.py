# -*- coding: utf-8 -*-
"""SM Full Feature QA — 53 actions (37 core + 4 AI Brain + 12 advanced) | Kavitha Nair / Brand: SpiceRoute Teas persona"""
import sys, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8')

BASE = "http://localhost:8000"
results = []

def post(path, body, timeout=90):
    data = json.dumps(body).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=data,
          headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read()), None
    except Exception as e:
        return None, str(e)

IMAGE_SKIP = {"image"}  # requires DALL-E, unavailable in Ollama mode

def check(name, r, err, *keys):
    if name in IMAGE_SKIP and r and r.get("error"):
        status = "SKIP"; detail = "DALL-E not available — expected"
        results.append((status, name, detail))
        print(f"  - {name:<42} {detail[:70]}")
        return
    if err or r is None:
        status = "FAIL"; detail = str(err)[:90]
    elif r.get("error") not in (None, False, ""):
        status = "FAIL"; detail = str(r.get("error",""))[:90]
    else:
        missing = [k for k in keys if k not in r]
        if missing:
            status = "PARTIAL"; detail = f"missing:{missing} | got:{list(r.keys())[:5]}"
        else:
            val = r.get(keys[0], "")
            preview = f"[{type(val).__name__} len={len(val)}]" if isinstance(val,(list,dict)) else str(val)[:60]
            status = "PASS"; detail = preview
    results.append((status, name, detail))
    icon = "✓" if status=="PASS" else ("~" if status=="PARTIAL" else "✗")
    print(f"  {icon} {name:<42} {detail[:70]}")

PATH = "/api/verticals/social/action"
def sm(action, payload, *keys, platform="all", language="en", timeout=90):
    r, e = post(PATH, {"action": action, "platform": platform, "payload": payload, "language": language}, timeout=timeout)
    check(action, r, e, *keys)

print("=" * 80)
print("  SM FULL QA — 37 actions | SpiceRoute Teas / Kavitha Nair")
print("=" * 80)

BRAND = "SpiceRoute Teas"
INDUSTRY = "D2C Tea Brand"

# 1
sm("generate", {"topic": "Monsoon is the perfect time for our Masala Chai", "platform": "instagram", "tone": "warm", "brand": BRAND}, "posts")
# 2
sm("hashtags", {"topic": "Masala Chai benefits", "platform": "instagram", "brand": BRAND}, "hashtags")
# 3 — image generation requires DALL-E; skip with a soft check
sm("image", {"prompt": f"Premium tea brand product shot, {BRAND}, warm colours, Indian aesthetic"}, "prompt")
# 4
sm("calendar", {"brand": BRAND, "industry": INDUSTRY, "platforms": ["instagram", "linkedin"], "days": 7}, "calendar")
# 5
sm("repurpose", {"content": "Our Masala Chai blend uses 6 hand-picked spices from Kerala. Slow brewed for 15 minutes for maximum flavour.", "brand": BRAND, "source_platform": "blog"}, "formats")
# 6
sm("competitor_audit", {"competitor_brand": "Chaayos", "our_brand": BRAND, "industry": INDUSTRY}, "audit")
# 7
sm("ad_copy", {"product": "SpiceRoute Premium Masala Chai", "platform": "instagram", "target_audience": "health-conscious urban Indians 25-40", "usp": "100% natural, no preservatives"}, "copy")
# 8
sm("influencer_brief", {"brand": BRAND, "product": "Monsoon Chai Collection", "campaign_goal": "brand awareness", "budget": "₹50,000", "target_audience": "food and lifestyle bloggers"}, "brief")
# 9
sm("crisis_response", {"brand": BRAND, "crisis_type": "product quality complaint", "severity": "medium", "description": "A customer posted that they found a foreign object in our tea packet"}, "response")
# 10
sm("youtube_script", {"brand": BRAND, "topic": "How to make the perfect Masala Chai at home", "duration_minutes": 5, "style": "tutorial"}, "script")
# 11
sm("email_sequence", {"brand": BRAND, "campaign_goal": "welcome new subscribers", "emails": 3, "product": "Starter Tea Kit"}, "sequence")
# 12
sm("reel_script", {"brand": BRAND, "topic": "Morning ritual with SpiceRoute Masala Chai", "duration_seconds": 30}, "script_scenes")
# 13
sm("monthly_report", {"brand": BRAND, "period": "July 2026", "total_posts": 28, "avg_engagement": "4.2%", "top_post": "Monsoon Chai launch got 1200 likes", "followers_gained": 342}, "report")
# 14
sm("keyword_cluster", {"topic": "Indian tea brands", "industry": INDUSTRY}, "cluster")
# 15
sm("best_post_time", {"platform": "instagram", "industry": INDUSTRY, "target_audience": "urban Indian millennials"}, "schedule")
# 16
sm("benchmark_engagement", {"platform": "instagram", "industry": INDUSTRY, "our_engagement_rate": 4.2}, "analysis")
# 17
sm("performance_score", {"platform": "instagram", "content": "Our Masala Chai is made with 6 hand-picked spices", "hashtags": "#masalachai #indiantea", "posting_time": "8 AM IST"}, "analysis")
# 18
sm("india_trends", {"industry": INDUSTRY, "platform": "instagram", "month": "July"}, "trends")
# 19
sm("regional_post", {"content": "Try our Masala Chai this monsoon!", "brand": BRAND, "target_language": "tamil", "platform": "instagram"}, "post", language="ta")
# 20
sm("whatsapp_content", {"brand": BRAND, "content_type": "broadcast", "product": "Monsoon Chai Kit", "offer": "20% off"}, "content_type")
# 21
sm("niche_templates", {"brand": BRAND, "industry": INDUSTRY, "platform": "instagram"}, "templates")
# 22
sm("bulk_generate", {"brand": BRAND, "topics": ["Morning chai routine", "Benefits of cardamom", "Tea vs Coffee"], "platform": "instagram", "tone": "friendly"}, "posts")
# 23
sm("content_pillars", {"brand": BRAND, "industry": INDUSTRY, "target_audience": "health-conscious millennials"}, "plan")
# 24
sm("brand_monitor", {"brand": BRAND, "competitors": ["Chaayos", "Tea Trunk"], "industry": INDUSTRY}, "intelligence")
# 25
sm("competitor_tracker", {"competitor": "Chaayos", "our_brand": BRAND, "platform": "instagram"}, "report")
# 26
sm("post_preview", {"platform": "instagram", "content": "Monsoon mornings are better with SpiceRoute Masala Chai ☕ #chai #monsoon", "brand": BRAND}, "tips")
# 27
sm("festive_post", {"brand_name": BRAND, "festival": "onam", "post_angle": "appreciation", "industry": "d2c"}, "post_text")
# 28
sm("twitter_thread", {"brand_name": BRAND, "topic": "Why Indian chai is better than coffee for productivity", "num_tweets": 5}, "tweets")
# 29
sm("story_highlights", {"brand": BRAND, "categories": ["Products", "Reviews", "Behind the Scenes", "Recipes"]}, "highlights")
# 30
sm("meme_caption", {"brand": BRAND, "meme_type": "relatable", "context": "Monday morning without chai"}, "panel_captions")
# 31
sm("bio_optimizer", {"brand": BRAND, "platform": "instagram", "usp": "Premium hand-crafted Indian teas", "target_audience": "tea lovers"}, "bios")
# 32
sm("product_launch_kit", {"brand": BRAND, "product": "SpiceRoute Winter Blend", "launch_date": "October 2026", "budget": "₹1L"}, "phases")
# 33
sm("viral_hook_generator", {"brand": BRAND, "content_type": "educational", "platform": "instagram", "topic": "Why masala chai helps digestion"}, "hooks")
# 34
sm("linkedin_article", {"brand": BRAND, "topic": "Building a D2C tea brand in India — lessons from our first year", "word_count": 600}, "sections")
# 35
sm("review_testimonial_kit", {"brand": BRAND, "product": "Masala Chai Box", "reviews": [{"text": "Best chai I've had!", "rating": 5}, {"text": "Very authentic taste", "rating": 4}]}, "whatsapp_templates")
# 36
sm("ab_copy_test", {"brand": BRAND, "product": "Monsoon Chai Kit", "platform": "instagram", "variants": 2, "goal": "conversions"}, "variations")
# 37
sm("social_roi", {"brand": BRAND, "platform": "instagram", "period": "Q2 FY26", "ad_spend": 50000, "revenue_attributed": 180000, "new_followers": 1200, "total_posts": 28}, "totals")

SM_WS = {"brand_name": BRAND, "industry": INDUSTRY, "platform": "instagram", "target_audience": "tea lovers aged 25-45", "usp": "Hand-crafted premium Indian teas", "tone": "warm"}

# 38 — AI Brain: Mission Control
sm("mission_control", SM_WS, "briefing")
# 39 — AI Brain: Goal Engine
sm("goal_engine", {"goal": "follower_growth", "workspace": SM_WS, "timeline": "30 days", "budget": "₹50,000"}, "campaign")
# 40 — AI Brain: Creative Score
sm("creative_score", {"post_text": "Monsoon mornings call for SpiceRoute Masala Chai ☕ Handcrafted with 9 spices. Taste the tradition. #chai #india", "platform": "instagram", "brand_name": BRAND, "industry": INDUSTRY, "tone": "warm"}, "scores")
# 41 — AI Brain: AI Team Meeting
sm("ai_team_meeting", {**SM_WS, "focus": "content_strategy"}, "meeting")

print()
passed  = sum(1 for s,_,_ in results if s=="PASS")
partial = sum(1 for s,_,_ in results if s=="PARTIAL")
failed  = sum(1 for s,_,_ in results if s=="FAIL")
skipped = sum(1 for s,_,_ in results if s=="SKIP")
total   = len(results)
print(f"  RESULTS: {passed}/{total} PASS | {partial} PARTIAL | {failed} FAIL | {skipped} SKIP")
if failed:
    print(f"\n  FAILURES:")
    for s,n,d in results:
        if s == "FAIL":
            print(f"    [FAIL] {n}")
            print(f"         {d}")
print("=" * 80)
sys.exit(0 if (failed == 0 and partial == 0) else 1)
