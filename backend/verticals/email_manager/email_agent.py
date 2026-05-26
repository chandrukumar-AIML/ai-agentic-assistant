# backend/verticals/email_manager/email_agent.py
"""
AI Email Manager (Feature 15).

Capabilities:
  1. Gmail OAuth2 — list, read, search, draft, send (via google-api-python-client)
  2. Outlook/Microsoft OAuth2 — same via Microsoft Graph API (msal)
  3. Auto-categorize emails: urgent | follow_up | newsletter | invoice | spam | general
  4. AI-draft replies (GPT-4o-mini) with context from original thread
  5. HITL gate: all sends require approval before dispatch
  6. Summarize inbox (top N unread with action items)
  7. Attachment extraction summary

Security:
  - OAuth tokens stored encrypted in Redis (never in plain text)
  - No email body text is logged
  - PII not included in any audit logs
"""
from __future__ import annotations

import base64
import logging
from datetime import datetime, timezone
from typing import Optional

from backend.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()

# ── Category classifier ───────────────────────────────────────────────────────

_CATEGORY_KEYWORDS = {
    "urgent":     ["urgent", "asap", "immediately", "critical", "emergency", "deadline today"],
    "invoice":    ["invoice", "payment", "bill", "receipt", "amount due", "gst", "tax invoice"],
    "newsletter": ["unsubscribe", "newsletter", "weekly digest", "monthly update", "opt out"],
    "spam":       ["click here", "free offer", "winner", "lottery", "100%", "guaranteed"],
    "follow_up":  ["follow up", "following up", "checking in", "any update", "reminder"],
}


def classify_email(subject: str, snippet: str) -> str:
    """Classify email into category based on subject + snippet keywords."""
    text = (subject + " " + snippet).lower()
    for category, keywords in _CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return category
    return "general"


# ── Gmail OAuth helpers ───────────────────────────────────────────────────────

def _build_gmail_service(access_token: str):
    """Build Gmail API service from access token."""
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    creds = Credentials(token=access_token)
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def _decode_part(part: dict) -> str:
    """Decode a Gmail message part body (base64url)."""
    data = part.get("body", {}).get("data", "")
    if data:
        return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    return ""


def _extract_gmail_body(payload: dict) -> str:
    """Recursively extract plain text body from Gmail message payload."""
    mime = payload.get("mimeType", "")
    if mime == "text/plain":
        return _decode_part(payload)
    if mime.startswith("multipart/"):
        for part in payload.get("parts", []):
            body = _extract_gmail_body(part)
            if body:
                return body
    return ""


async def list_gmail_messages(
    access_token: str,
    max_results:  int = 20,
    query:        str = "is:unread",
) -> list[dict]:
    """List Gmail messages matching query. Returns metadata only (no full body)."""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    def _list():
        try:
            svc  = _build_gmail_service(access_token)
            resp = svc.users().messages().list(
                userId="me", q=query, maxResults=min(max_results, 50)
            ).execute()
        except Exception as _auth_err:
            logger.warning("Gmail API auth failed: %s", type(_auth_err).__name__)
            return [{"error": "Gmail authentication failed. Please reconnect your Gmail account.", "detail": type(_auth_err).__name__}]
        messages = resp.get("messages", [])
        results  = []
        for m in messages[:max_results]:
            try:
                meta = svc.users().messages().get(
                    userId="me", id=m["id"], format="metadata",
                    metadataHeaders=["Subject", "From", "Date"],
                ).execute()
            except Exception:
                continue
            headers  = {h["name"]: h["value"] for h in meta.get("payload", {}).get("headers", [])}
            snippet  = meta.get("snippet", "")[:200]
            subject  = headers.get("Subject", "(no subject)")
            results.append({
                "id":       m["id"],
                "subject":  subject,
                "from":     headers.get("From", ""),
                "date":     headers.get("Date", ""),
                "snippet":  snippet,
                "category": classify_email(subject, snippet),
                "labels":   meta.get("labelIds", []),
            })
        return results

    loop = asyncio.get_event_loop()
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            return await loop.run_in_executor(pool, _list)
    except Exception as e:
        logger.warning("Gmail list_messages failed (invalid/expired token?): %s", type(e).__name__)
        return [{"error": "Gmail authentication failed. Please reconnect your Gmail account.", "detail": type(e).__name__}]


async def get_gmail_message(access_token: str, message_id: str) -> dict:
    """Get full Gmail message body and metadata."""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    def _get():
        svc = _build_gmail_service(access_token)
        msg = svc.users().messages().get(userId="me", id=message_id, format="full").execute()
        payload = msg.get("payload", {})
        headers = {h["name"]: h["value"] for h in payload.get("headers", [])}
        body    = _extract_gmail_body(payload)
        # Extract attachment names (no content — too large)
        attachments = [
            {
                "filename": part.get("filename", ""),
                "mimeType": part.get("mimeType", ""),
                "size":     part.get("body", {}).get("size", 0),
            }
            for part in payload.get("parts", [])
            if part.get("filename")
        ]
        return {
            "id":          message_id,
            "subject":     headers.get("Subject", ""),
            "from":        headers.get("From", ""),
            "to":          headers.get("To", ""),
            "date":        headers.get("Date", ""),
            "body":        body[:5000],   # cap to avoid huge payloads
            "attachments": attachments,
            "labels":      msg.get("labelIds", []),
        }

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=1) as pool:
        return await loop.run_in_executor(pool, _get)


async def send_gmail_message(
    access_token: str,
    to:           str,
    subject:      str,
    body:         str,
    reply_to_id:  Optional[str] = None,
) -> dict:
    """
    Send a Gmail message. All sends go through HITL — this function is called
    only AFTER HITL approval. Never call directly from user-facing code.
    """
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    import email.mime.text
    import email.mime.multipart

    def _send():
        svc  = _build_gmail_service(access_token)
        mime = email.mime.text.MIMEText(body)
        mime["to"]      = to
        mime["subject"] = subject
        raw  = base64.urlsafe_b64encode(mime.as_bytes()).decode()
        kwargs: dict = {"userId": "me", "body": {"raw": raw}}
        if reply_to_id:
            kwargs["body"]["threadId"] = reply_to_id
        result = svc.users().messages().send(**kwargs).execute()
        return {"message_id": result.get("id"), "thread_id": result.get("threadId")}

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=1) as pool:
        return await loop.run_in_executor(pool, _send)


# ── Microsoft Graph (Outlook) helpers ────────────────────────────────────────

async def list_outlook_messages(
    access_token: str,
    max_results:  int = 20,
    filter_query: str = "isRead eq false",
) -> list[dict]:
    """List Outlook messages via Microsoft Graph API."""
    import httpx

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept":        "application/json",
    }
    params = {
        "$filter":  filter_query,
        "$top":     min(max_results, 50),
        "$select":  "id,subject,from,receivedDateTime,bodyPreview,isRead",
        "$orderby": "receivedDateTime desc",
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://graph.microsoft.com/v1.0/me/messages",
                headers=headers,
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

        results = []
        for msg in data.get("value", []):
            subject = msg.get("subject", "(no subject)")
            snippet = msg.get("bodyPreview", "")[:200]
            results.append({
                "id":       msg.get("id", ""),
                "subject":  subject,
                "from":     msg.get("from", {}).get("emailAddress", {}).get("address", ""),
                "date":     msg.get("receivedDateTime", ""),
                "snippet":  snippet,
                "category": classify_email(subject, snippet),
                "is_read":  msg.get("isRead", True),
            })
        return results
    except Exception as e:
        logger.error("Outlook Graph API error: %s", e)
        return [{"error": "Outlook temporarily unavailable."}]


async def send_outlook_message(
    access_token: str,
    to:           str,
    subject:      str,
    body:         str,
) -> dict:
    """Send Outlook message via Microsoft Graph. Called only post-HITL."""
    import httpx
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type":  "application/json",
    }
    payload = {
        "message": {
            "subject": subject,
            "body":    {"contentType": "Text", "content": body},
            "toRecipients": [{"emailAddress": {"address": to}}],
        }
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://graph.microsoft.com/v1.0/me/sendMail",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
        return {"status": "sent", "to": to, "subject": subject}
    except Exception as e:
        logger.error("Outlook send failed: %s", e)
        return {"error": "Send failed.", "detail": type(e).__name__}


# ── AI draft generation ───────────────────────────────────────────────────────

async def draft_reply(
    original_subject: str,
    original_body:    str,
    original_from:    str,
    tone:             str = "professional",   # professional | friendly | formal
    language:         str = "en",
    extra_context:    str = "",
) -> str:
    """
    Generate an AI reply draft for an email using GPT-4o-mini.
    Returns plain text draft. Never sends — requires HITL approval.
    """
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    system = (
        f"You are an expert email assistant. Write a {tone} reply in {language}. "
        f"Be concise (3-5 sentences unless more is clearly needed). "
        f"Do not use filler phrases. Sign off professionally."
    )
    user = (
        f"From: {original_from}\nSubject: {original_subject}\n\n"
        f"Original email:\n{original_body[:2000]}\n\n"
        f"{'Additional context: ' + extra_context if extra_context else ''}\n\n"
        f"Write a reply:"
    )
    try:
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            max_tokens=500,
            temperature=0.6,
        )
        return resp.choices[0].message.content or ""
    except Exception as openai_err:
        logger.warning("Email draft OpenAI failed, trying Ollama: %s", openai_err)
        try:
            from backend.llm.ollama_client import ollama_chat
            text = await ollama_chat(
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user},
                ],
                max_tokens=250,
                num_ctx=512,
                stream=False,
            )
            return text or ""
        except Exception as ollama_err:
            logger.error("Email draft Ollama fallback failed: %s", ollama_err)
            return ""


# ── Inbox summary ─────────────────────────────────────────────────────────────

async def summarize_inbox(messages: list[dict], language: str = "en") -> dict:
    """
    Summarize a list of email metadata into priority action items.
    No full email bodies — only subjects and snippets.
    """
    if not messages:
        return {"summary": "Inbox is empty.", "action_items": [], "categories": {}}

    # Category counts
    from collections import Counter
    cat_counts = Counter(m.get("category", "general") for m in messages)

    urgent   = [m for m in messages if m.get("category") == "urgent"]
    invoices = [m for m in messages if m.get("category") == "invoice"]
    followups = [m for m in messages if m.get("category") == "follow_up"]

    # AI summary of top urgent messages
    summary_text = ""
    if urgent or invoices or followups:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)

        items_text = "\n".join(
            f"- [{m.get('category','?').upper()}] {m.get('subject','')} (from {m.get('from','')})"
            for m in (urgent + invoices + followups)[:10]
        )
        try:
            resp = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": (
                        f"Summarize these emails into 3-5 action items in {language}. "
                        f"Be very concise. Focus on what requires the user's attention today."
                    )},
                    {"role": "user", "content": items_text},
                ],
                max_tokens=300,
            )
            summary_text = resp.choices[0].message.content or ""
        except Exception:
            summary_text = f"{len(urgent)} urgent, {len(invoices)} invoices, {len(followups)} follow-ups need attention."

    action_items = []
    for m in urgent[:3]:
        action_items.append({"priority": "HIGH", "subject": m.get("subject"), "from": m.get("from")})
    for m in invoices[:3]:
        action_items.append({"priority": "MEDIUM", "subject": m.get("subject"), "from": m.get("from")})
    for m in followups[:3]:
        action_items.append({"priority": "LOW", "subject": m.get("subject"), "from": m.get("from")})

    return {
        "total_messages": len(messages),
        "summary":        summary_text,
        "action_items":   action_items,
        "categories":     dict(cat_counts),
        "urgent_count":   len(urgent),
        "invoice_count":  len(invoices),
    }


# ── Main email agent dispatcher ───────────────────────────────────────────────

async def email_agent(
    action:       str,            # list | read | draft | send | summarize | search
    provider:     str,            # gmail | outlook
    access_token: str,
    user_id:      str,
    session_id:   str = "",
    message_id:   Optional[str] = None,
    query:        str = "is:unread",
    draft_params: Optional[dict] = None,
    send_params:  Optional[dict] = None,
    max_results:  int = 20,
    language:     str = "en",
) -> dict:
    """
    Main email agent dispatcher.
    All send actions create a HITL approval request instead of sending directly.
    """
    if action == "list":
        if provider == "gmail":
            msgs = await list_gmail_messages(access_token, max_results, query)
        else:
            msgs = await list_outlook_messages(access_token, max_results)
        return {"messages": msgs, "count": len(msgs), "provider": provider}

    elif action == "read":
        if not message_id:
            return {"error": "message_id required for read action"}
        if provider == "gmail":
            return await get_gmail_message(access_token, message_id)
        return {"error": "Outlook message read not yet implemented in this version."}

    elif action == "summarize":
        if provider == "gmail":
            msgs = await list_gmail_messages(access_token, max_results, "is:unread")
        else:
            msgs = await list_outlook_messages(access_token, max_results)
        summary = await summarize_inbox(msgs, language)
        return {**summary, "provider": provider}

    elif action == "draft":
        if not draft_params:
            return {"error": "draft_params required"}
        draft = await draft_reply(
            original_subject=draft_params.get("subject", ""),
            original_body=draft_params.get("body", ""),
            original_from=draft_params.get("from", ""),
            tone=draft_params.get("tone", "professional"),
            language=language,
            extra_context=draft_params.get("extra_context", ""),
        )
        return {
            "draft":    draft,
            "to":       draft_params.get("to", ""),
            "subject":  "Re: " + draft_params.get("subject", ""),
            "status":   "draft_ready",
            "note":     "Review and approve via HITL before sending.",
        }

    elif action == "send":
        # Always gate through HITL — never send directly
        if not send_params:
            return {"error": "send_params required"}

        try:
            from backend.hitl.hitl_manager import request_approval
            approval_id = await request_approval(
                action_type="send_email",
                action_payload={
                    "provider":    provider,
                    "to":          send_params.get("to", ""),
                    "subject":     send_params.get("subject", ""),
                    "body_length": len(send_params.get("body", "")),
                },
                context_summary=(
                    f"Send email to {send_params.get('to')} "
                    f"with subject: {send_params.get('subject', '')[:80]}"
                ),
                user_id=user_id,
                session_id=session_id,
            )
            return {
                "status":      "pending_approval",
                "approval_id": approval_id,
                "note":        "Email queued for HITL approval before dispatch.",
            }
        except Exception as e:
            logger.error("Email HITL request failed: %s", e)
            return {"error": "Could not queue email for approval."}

    elif action == "search":
        if provider == "gmail":
            msgs = await list_gmail_messages(access_token, max_results, query)
        else:
            msgs = await list_outlook_messages(
                access_token, max_results, f"subject eq '{query}' or body/content eq '{query}'"
            )
        return {"messages": msgs, "count": len(msgs), "query": query}

    return {"error": f"Unknown email action: {action}"}
