# backend/verticals/legal/legal_agent.py
"""
Indian Legal Research Agent (Feature 10).

Capabilities:
  1. IndianKanoon case search API — court judgements and citations
  2. Bare Acts RAG — IPC, CPC, CrPC, Constitution via existing FAISS/ChromaDB
  3. Query classification: case_search | bare_act | legal_advice
  4. Multilingual: Hindi, English, regional languages
  5. Citation extraction and case summary

All responses include a legal disclaimer.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

import httpx

from backend.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()

_DISCLAIMER = (
    "\n\n⚠️ *Disclaimer: This is AI-generated legal information for reference only. "
    "Consult a qualified advocate for legal advice. Not a substitute for professional legal counsel.*"
)

# ── IndianKanoon API ─────────────────────────────────────────────────────────

async def search_indiankanoon(
    query:       str,
    doc_types:   str = "judgments",
    max_results: int = 5,
) -> list[dict]:
    """
    Search IndianKanoon for court judgements.
    API Reference: https://api.indiankanoon.org
    """
    api_key = settings.indiankanoon_api_key

    if not api_key:
        # Return mock results for development
        return [
            {
                "title":   f"Mock: {query} — Supreme Court of India",
                "docid":   "mock_12345",
                "url":     f"https://indiankanoon.org/doc/12345/",
                "snippet": f"This judgment relates to {query}. The court held that...",
                "court":   "Supreme Court of India",
                "date":    "2023-01-15",
                "mock":    True,
            }
        ]

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.indiankanoon.org/search/",
                headers={"Authorization": f"Token {api_key}"},
                data={
                    "formInput":  query,
                    "pagenum":    0,
                    "doc_type":   doc_types,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        results = []
        for doc in data.get("docs", [])[:max_results]:
            results.append({
                "title":   doc.get("title", ""),
                "docid":   doc.get("tid", ""),
                "url":     f"https://indiankanoon.org/doc/{doc.get('tid', '')}/",
                "snippet": doc.get("headline", ""),
                "court":   doc.get("docsource", ""),
                "date":    doc.get("publishdate", ""),
            })
        return results

    except Exception as e:
        logger.error("IndianKanoon API error: %s", e)
        return [{"error": "Case search temporarily unavailable."}]


# ── Bare Acts RAG ────────────────────────────────────────────────────────────

# Known bare act categories with their section patterns
_ACT_PATTERNS = {
    "IPC":  re.compile(r'(?i)\b(?:IPC|Indian Penal Code)\s+(?:section|sec|s\.?)?\s*(\d+[A-Z]?)\b'),
    "CPC":  re.compile(r'(?i)\b(?:CPC|Code of Civil Procedure)\s+(?:order|section|s\.?)?\s*([\dA-Z]+)\b'),
    "CrPC": re.compile(r'(?i)\b(?:CrPC|Cr\.?P\.?C\.?|Criminal Procedure)\s+(?:section|s\.?)?\s*(\d+[A-Z]?)\b'),
    "IT Act": re.compile(r'(?i)\b(?:IT Act|Information Technology)\s+(?:section|s\.?)?\s*(\d+[A-Z]?)\b'),
    "GST":  re.compile(r'(?i)\b(?:CGST|SGST|IGST|GST Act)\s+(?:section|s\.?)?\s*(\d+[A-Z]?)\b'),
}

# Inline summaries for most-referenced sections (reduces LLM calls)
_BARE_ACT_SUMMARIES = {
    "IPC 420":  "IPC Section 420 — Cheating and dishonestly inducing delivery of property. Punishment: up to 7 years + fine.",
    "IPC 302":  "IPC Section 302 — Punishment for murder. Death or life imprisonment + fine.",
    "IPC 354":  "IPC Section 354 — Assault or criminal force to woman with intent to outrage her modesty. 1–5 years imprisonment.",
    "IPC 376":  "IPC Section 376 — Punishment for rape. Minimum 10 years, extendable to life imprisonment.",
    "IPC 498A": "IPC Section 498A — Cruelty by husband or his relatives. Up to 3 years + fine.",
    "CrPC 41":  "CrPC Section 41 — When police may arrest without warrant.",
    "CrPC 125": "CrPC Section 125 — Order for maintenance of wives, children and parents.",
    "CrPC 161": "CrPC Section 161 — Examination of witnesses by police.",
    "CPC 9":    "CPC Order 9 — Appearance of parties and consequence of non-appearance.",
    "IT Act 66": "IT Act Section 66 — Computer related offences. Up to 3 years or ₹5 lakh fine.",
    "IT Act 66A": "IT Act Section 66A — Declared unconstitutional by Supreme Court (Shreya Singhal v. UoI, 2015).",
}


def extract_section_references(query: str) -> list[dict]:
    """Extract legal section references from query text."""
    refs = []
    for act_name, pattern in _ACT_PATTERNS.items():
        for match in pattern.finditer(query):
            section = match.group(1)
            key     = f"{act_name} {section}"
            refs.append({
                "act":     act_name,
                "section": section,
                "summary": _BARE_ACT_SUMMARIES.get(key, f"{act_name} Section {section}"),
            })
    return refs


async def rag_bare_acts(query: str) -> list[dict]:
    """
    Use existing FAISS/ChromaDB RAG pipeline to retrieve bare act text.
    Falls back to section extraction if RAG unavailable.
    """
    # First try inline summaries
    refs = extract_section_references(query)
    if refs:
        return refs

    # Try RAG pipeline
    try:
        from backend.rag.faiss_store  import FAISSStore
        from backend.rag.chroma_store import ChromaStore
        store  = FAISSStore()
        chunks = store.similarity_search(query, k=3)
        if chunks:
            return [{"source": c.get("source", "Bare Act"), "content": c.get("content", "")[:500]} for c in chunks]
    except Exception as e:
        logger.debug("Bare acts RAG failed (non-fatal): %s", e)

    return []


# ── Query classifier ─────────────────────────────────────────────────────────

def classify_legal_query(query: str) -> str:
    """Returns: 'case_search' | 'bare_act' | 'legal_advice'"""
    q = query.lower()
    if any(kw in q for kw in ["case", "judgement", "judgment", "court", "verdict", "held", "ruling"]):
        return "case_search"
    if any(kw in q for kw in ["section", "ipc", "cpc", "crpc", "act", "provision", "clause"]):
        return "bare_act"
    return "legal_advice"


# ── Main legal agent ─────────────────────────────────────────────────────────

async def legal_agent(
    query:    str,
    language: str = "en",
) -> dict:
    """
    Main Indian Legal Research agent dispatcher.
    """
    intent = classify_legal_query(query)

    if intent == "case_search":
        cases = await search_indiankanoon(query)
        return {
            "intent":    "case_search",
            "cases":     cases,
            "disclaimer": _DISCLAIMER,
        }

    if intent == "bare_act":
        sections = await rag_bare_acts(query)
        # LLM explanation (Ollama-first)
        explanation = ""
        try:
            from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL
            explanation = await ollama_chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"You are an expert in Indian law. "
                            f"Explain legal provisions clearly in {language}. "
                            f"Reference specific sections. Include practical implications."
                        ),
                    },
                    {"role": "user", "content": query},
                ],
                model=OLLAMA_MODEL,
                max_tokens=400,
            ) or ""
        except Exception as e:
            logger.error("Legal bare_act LLM failed: %s", e)

        return {
            "intent":      "bare_act",
            "sections":    sections,
            "explanation": explanation,
            "disclaimer":  _DISCLAIMER,
        }

    # Generic legal advice (Ollama-first)
    try:
        from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL
        response_text = await ollama_chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are an expert in Indian law. "
                        f"Respond in {language}. "
                        f"Provide practical legal guidance. "
                        f"Always recommend consulting a qualified advocate for specific cases."
                    ),
                },
                {"role": "user", "content": query},
            ],
            model=OLLAMA_MODEL,
            max_tokens=500,
        )
        if not response_text:
            raise ValueError("Empty Ollama response")
        return {
            "intent":     "legal_advice",
            "response":   response_text,
            "disclaimer": _DISCLAIMER,
            "model":      f"ollama/{OLLAMA_MODEL}",
        }
    except Exception as e:
        logger.error("Legal agent LLM failed: %s", e)
        return {"error": "Legal assistant temporarily unavailable.", "disclaimer": _DISCLAIMER}
