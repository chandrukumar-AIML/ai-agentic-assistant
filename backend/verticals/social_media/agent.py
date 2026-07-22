"""Social Media Agent — thin dispatcher. All business logic lives in tools/."""
from .tools import (
    # content
    generate_post, generate_bulk_posts, generate_regional_post,
    generate_niche_templates, generate_whatsapp_content, repurpose_content,
    # platform
    generate_twitter_thread, generate_facebook_post, generate_reel_script,
    generate_youtube_script, generate_youtube_description,
    generate_linkedin_company_post, generate_linkedin_article,
    generate_linkedin_carousel, generate_podcast_content_kit,
    # research
    research_hashtags, generate_india_trends, build_keyword_cluster,
    competitor_social_audit, track_competitor_posts, monitor_brand_mentions,
    competitor_content_spy,
    # campaigns
    plan_content_calendar, generate_content_calendar, build_content_pillar_plan,
    generate_festive_post, plan_cultural_calendar, generate_brand_voice_engine,
    generate_product_launch_kit,
    # engagement
    generate_comment_replies, generate_bio_optimizer, generate_story_highlights_plan,
    generate_meme_caption, generate_viral_hooks, generate_influencer_outreach,
    generate_influencer_brief,
    # analytics
    generate_monthly_report, benchmark_engagement_rate, score_content_performance,
    calculate_social_roi, generate_unified_analytics, suggest_best_post_time,
    build_post_preview_tips, generate_cross_agent_content,
    # publishing
    post_to_linkedin, post_to_twitter, schedule_via_buffer, generate_social_image,
    # advanced
    generate_ad_copy, generate_crisis_response, generate_email_sequence,
    generate_review_testimonial_kit, generate_employee_advocacy,
    respond_to_mentions, generate_ab_copy, plan_content_scheduler,
)
from ._impl import social_agent   # dispatcher lives in _impl until fully migrated

__all__ = ["social_agent"]
