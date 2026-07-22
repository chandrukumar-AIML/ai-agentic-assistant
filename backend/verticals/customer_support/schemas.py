"""Pydantic request/response schemas for the Customer Support agent."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FaqRequest(BaseModel):
    query: str
    business_name: str = ""
    business_type: str = ""
    faq_context: str = ""
    language: str = "en"

class LeadRequest(BaseModel):
    lead_name: str = ""
    business_name: str = ""
    budget: str = ""
    authority: str = ""
    need: str = ""
    timeline: str = ""
    language: str = "en"

class WhatsAppDraftRequest(BaseModel):
    customer_name: str = ""
    business_name: str = ""
    message_type: str = "promotional"
    topic: str = ""
    offer: str = ""
    language: str = "en"

class SentimentRequest(BaseModel):
    text: str
    customer_name: str = ""
    language: str = "en"

class ComplaintRequest(BaseModel):
    complaint_text: str
    customer_name: str = ""
    business_name: str = ""
    category: str = ""
    language: str = "en"

class TicketSummaryRequest(BaseModel):
    ticket_text: str
    ticket_id: str = ""
    language: str = "en"

class WeeklyReportRequest(BaseModel):
    business_name: str = ""
    tickets: List[Dict[str, Any]] = []
    period: str = ""
    language: str = "en"

class TicketTriageRequest(BaseModel):
    subject: str
    body: str
    customer_tier: str = "standard"
    channel: str = "email"
    language: str = "en"

class VocReportRequest(BaseModel):
    business_name: str = ""
    feedback_items: List[str] = []
    period: str = ""
    language: str = "en"

class AgentResponse(BaseModel):
    action: str
    status: str = "success"
    data: Dict[str, Any] = {}
