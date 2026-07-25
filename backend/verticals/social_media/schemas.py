"""Pydantic request/response schemas for the Social Media agent."""
from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel


class GenerateRequest(BaseModel):
    topic: str = ""
    tone: str = "professional"
    include_emoji: bool = True
    brand_name: str = ""
    language: str = "en"
    extra_context: str = ""

class HashtagRequest(BaseModel):
    topic: str
    industry: str = ""
    platform: str = "instagram"
    language: str = "en"

class CalendarRequest(BaseModel):
    brand_name: str
    industry: str
    platforms: List[str] = ["linkedin", "twitter", "instagram"]
    month: str = ""
    language: str = "en"

class FestivePostRequest(BaseModel):
    brand_name: str
    festival: str
    post_angle: str = "appreciation"
    industry: str = ""
    offer_text: str = ""
    language: str = "en"

class TwitterThreadRequest(BaseModel):
    brand_name: str
    topic: str
    thread_type: str = "educational"
    industry: str = ""
    num_tweets: int = 7
    include_hook_variants: bool = True

class CommentReplyRequest(BaseModel):
    brand_name: str
    topic: str
    comments: List[str]
    platform: str = "instagram"
    include_cta: bool = True
    tone: str = "friendly"

class AgentResponse(BaseModel):
    action: str
    status: str = "success"
    data: Dict[str, Any] = {}
