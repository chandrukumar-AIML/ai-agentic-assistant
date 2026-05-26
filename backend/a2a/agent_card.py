# backend/a2a/agent_card.py
"""
Google Agent-to-Agent (A2A) Protocol — Agent Card.

The agent card is a JSON-LD document served at /.well-known/agent.json
that describes this agent's capabilities to other agents and orchestrators.

Reference: https://google.github.io/A2A (Linux Foundation 2026 standard)

The card declares:
  - agent identity + version
  - supported skills (capabilities)
  - authentication methods
  - streaming capabilities
  - endpoint URLs
"""
from __future__ import annotations

from backend.config import get_settings

settings = get_settings()

_BASE_URL = getattr(settings, "backend_url", "http://localhost:8000")


def get_agent_card() -> dict:
    """
    Return the A2A agent card for this AI Agentic Assistant instance.
    Served at GET /.well-known/agent.json
    """
    return {
        "@context":    "https://schema.org/",
        "@type":       "SoftwareApplication",
        "name":        "AI Agentic Assistant V2",
        "version":     "2.0.0",
        "description": (
            "Enterprise multi-agent AI system with RAG, voice, browser automation, "
            "compliance guardian (HIPAA/GDPR/SOC2/EU AI Act), and 19 domain verticals."
        ),
        "url":         _BASE_URL,
        "provider": {
            "@type": "Organization",
            "name":  "AI Agentic Assistant",
        },

        # A2A standard fields
        "a2a": {
            "protocol_version": "1.0",
            "agent_id":         f"urn:aaa:agent:{getattr(settings, 'app_env', 'dev')}",
            "endpoint":         f"{_BASE_URL}/api/a2a",
            "streaming":        True,
            "authentication": {
                "schemes": ["bearer", "api_key"],
                "bearer": {
                    "token_url": f"{_BASE_URL}/api/auth/token",
                    "scopes":    ["agent:read", "agent:write"],
                },
            },
            "skills": [
                {
                    "id":          "rag_query",
                    "name":        "RAG Knowledge Query",
                    "description": "Answer questions using FAISS + ChromaDB dual retrieval with HyDE.",
                    "input_schema":  {"type": "object", "properties": {"query": {"type": "string"}}},
                    "output_schema": {"type": "object", "properties": {"answer": {"type": "string"}, "sources": {"type": "array"}}},
                    "streaming":    True,
                },
                {
                    "id":          "web_search",
                    "name":        "Web Search",
                    "description": "Real-time web search via Tavily with citation extraction.",
                    "input_schema":  {"type": "object", "properties": {"query": {"type": "string"}}},
                    "output_schema": {"type": "object", "properties": {"results": {"type": "array"}}},
                },
                {
                    "id":          "code_execution",
                    "name":        "Safe Code Runner",
                    "description": "Execute Python/JavaScript code in a sandboxed environment.",
                    "input_schema":  {"type": "object", "properties": {"code": {"type": "string"}, "language": {"type": "string"}}},
                    "output_schema": {"type": "object", "properties": {"output": {"type": "string"}, "error": {"type": "string"}}},
                },
                {
                    "id":          "document_generation",
                    "name":        "Multi-modal Document Generation",
                    "description": "Generate PDF, PPTX, Excel, images (DALL-E 3), or audio (TTS).",
                    "input_schema":  {"type": "object", "properties": {"format": {"type": "string"}, "payload": {"type": "object"}}},
                    "output_schema": {"type": "object", "properties": {"download_url": {"type": "string"}}},
                },
                {
                    "id":          "hitl_approval",
                    "name":        "Human-in-the-Loop Approval",
                    "description": "Request human approval for irreversible actions with 30-min timeout.",
                    "input_schema":  {"type": "object", "properties": {"action_type": {"type": "string"}, "context": {"type": "string"}}},
                    "output_schema": {"type": "object", "properties": {"decision": {"type": "string"}, "approval_id": {"type": "string"}}},
                },
                {
                    "id":          "compliance_check",
                    "name":        "Compliance Guardian",
                    "description": "HIPAA PHI detection, GDPR, SOC2, EU AI Act compliance checking.",
                    "input_schema":  {"type": "object", "properties": {"text": {"type": "string"}}},
                    "output_schema": {"type": "object", "properties": {"status": {"type": "string"}, "violations": {"type": "array"}}},
                },
                {
                    "id":          "agri_advisory",
                    "name":        "AgriTech Advisory (India)",
                    "description": "Crop disease, mandi prices, weather, government schemes. Tamil/Hindi/English.",
                    "input_schema":  {"type": "object", "properties": {"query": {"type": "string"}, "language": {"type": "string"}}},
                    "output_schema": {"type": "object", "properties": {"advice": {"type": "string"}}},
                },
                {
                    "id":          "legal_research",
                    "name":        "Indian Legal Research",
                    "description": "IndianKanoon case search, IPC/CPC/CrPC Bare Acts RAG, multilingual.",
                    "input_schema":  {"type": "object", "properties": {"query": {"type": "string"}}},
                    "output_schema": {"type": "object", "properties": {"cases": {"type": "array"}, "bare_acts": {"type": "array"}}},
                },
                {
                    "id":          "lead_qualification",
                    "name":        "Sales Lead Qualifier",
                    "description": "Score leads 0-100, enrich with Clearbit, sync to HubSpot/Salesforce.",
                    "input_schema":  {"type": "object", "properties": {"lead_data": {"type": "object"}}},
                    "output_schema": {"type": "object", "properties": {"score": {"type": "number"}, "crm_id": {"type": "string"}}},
                },
                {
                    "id":          "gst_calculation",
                    "name":        "GST/TDS Calculator (India)",
                    "description": "GSTIN validation, GST rate lookup, TDS calculation, GSTR export.",
                    "input_schema":  {"type": "object", "properties": {"amount": {"type": "number"}, "hsn_code": {"type": "string"}}},
                    "output_schema": {"type": "object", "properties": {"gst_amount": {"type": "number"}, "breakdown": {"type": "object"}}},
                },
            ],

            # External system adapters (mock implementations provided)
            "adapters": [
                {
                    "id":       "salesforce",
                    "name":     "Salesforce CRM",
                    "type":     "crm",
                    "endpoint": f"{_BASE_URL}/api/a2a/adapters/salesforce",
                    "mock":     True,
                },
                {
                    "id":       "sap",
                    "name":     "SAP ERP",
                    "type":     "erp",
                    "endpoint": f"{_BASE_URL}/api/a2a/adapters/sap",
                    "mock":     True,
                },
                {
                    "id":       "servicenow",
                    "name":     "ServiceNow ITSM",
                    "type":     "itsm",
                    "endpoint": f"{_BASE_URL}/api/a2a/adapters/servicenow",
                    "mock":     True,
                },
            ],

            "rate_limits": {
                "requests_per_minute": 60,
                "tokens_per_minute":   100_000,
            },
        },
    }
