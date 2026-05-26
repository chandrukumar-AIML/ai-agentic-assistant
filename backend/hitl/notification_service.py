# backend/hitl/notification_service.py
"""
HITL Notification Service — multi-channel delivery.

Channels:
  email   — SendGrid transactional email with approval/reject links
  slack   — Webhook with interactive buttons
  in_app  — WebSocket push to connected reviewer sessions
  webhook — Generic HTTP POST for custom integrations

All channels are fire-and-forget (asyncio.create_task) so they never
block the approval queue writer.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import httpx

from backend.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()

# ── Base URL for approval links ──────────────────────────────────────────────
_FRONTEND_URL = getattr(settings, "frontend_url", "http://localhost:5173")
_BACKEND_URL  = getattr(settings, "backend_url",  "http://localhost:8000")


def _approval_url(approval_id: str, action: str) -> str:
    """Deep-link that lets reviewer approve/reject without logging in again."""
    return f"{_FRONTEND_URL}/hitl/{approval_id}/{action}"


# ── Email via SendGrid ────────────────────────────────────────────────────────

async def _send_email(
    to_email:       str,
    approval_id:    str,
    action_type:    str,
    context_summary: str,
    expires_at:     datetime,
) -> bool:
    """Send HITL approval request email via SendGrid."""
    api_key = getattr(settings, "sendgrid_api_key", None)
    if not api_key:
        logger.warning("SENDGRID_API_KEY not set — skipping email notification")
        return False

    approve_url = _approval_url(approval_id, "approve")
    reject_url  = _approval_url(approval_id, "reject")
    expires_fmt = expires_at.strftime("%H:%M UTC")

    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from":             {"email": "noreply@ai-assistant.com", "name": "AI Agentic Assistant"},
        "subject":          f"⚡ Action Requires Your Approval — {action_type}",
        "content":          [{
            "type":  "text/html",
            "value": f"""
            <div style="font-family:sans-serif;max-width:560px;margin:0 auto;">
              <h2 style="color:#534AB7">🛡️ Human Approval Required</h2>
              <p>An AI action requires your review before proceeding.</p>
              <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                <tr><td style="padding:8px;font-weight:bold;color:#374151">Action</td>
                    <td style="padding:8px">{action_type}</td></tr>
                <tr style="background:#f9fafb"><td style="padding:8px;font-weight:bold;color:#374151">Details</td>
                    <td style="padding:8px">{context_summary}</td></tr>
                <tr><td style="padding:8px;font-weight:bold;color:#374151">Expires</td>
                    <td style="padding:8px;color:#dc2626">{expires_fmt} (auto-rejected if no action)</td></tr>
              </table>
              <div style="margin:24px 0;display:flex;gap:12px;">
                <a href="{approve_url}" style="background:#22c55e;color:#fff;padding:12px 24px;
                   border-radius:8px;text-decoration:none;font-weight:bold;">✅ Approve</a>
                &nbsp;&nbsp;
                <a href="{reject_url}" style="background:#ef4444;color:#fff;padding:12px 24px;
                   border-radius:8px;text-decoration:none;font-weight:bold;">❌ Reject</a>
              </div>
              <p style="color:#9ca3af;font-size:12px;">
                Approval ID: {approval_id}<br>
                This email was sent by AI Agentic Assistant V2.
              </p>
            </div>
            """,
        }],
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
            )
            resp.raise_for_status()
            logger.info("HITL email sent to %s for approval %s", to_email[:3] + "***", approval_id)
            return True
    except Exception as e:
        logger.error("HITL email failed for %s: %s", approval_id, e)
        return False


# ── Slack via Incoming Webhook ────────────────────────────────────────────────

async def _send_slack(
    approval_id:     str,
    action_type:     str,
    context_summary: str,
    user_id:         str,
    expires_at:      datetime,
) -> bool:
    """Post HITL approval card to Slack webhook."""
    webhook_url = getattr(settings, "slack_webhook_url", None)
    if not webhook_url:
        logger.warning("SLACK_WEBHOOK_URL not set — skipping Slack notification")
        return False

    approve_url = _approval_url(approval_id, "approve")
    reject_url  = _approval_url(approval_id, "reject")
    expires_fmt = expires_at.strftime("%Y-%m-%d %H:%M UTC")

    payload = {
        "text": f"⚡ *HITL Approval Required* — `{action_type}`",
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "🛡️ Human-in-the-Loop Approval Required"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Action:*\n`{action_type}`"},
                    {"type": "mrkdwn", "text": f"*Requested by:*\n`{user_id}`"},
                    {"type": "mrkdwn", "text": f"*Details:*\n{context_summary}"},
                    {"type": "mrkdwn", "text": f"*Expires:*\n{expires_fmt}"},
                ],
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "✅ Approve"},
                        "style": "primary",
                        "url":   approve_url,
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "❌ Reject"},
                        "style": "danger",
                        "url":   reject_url,
                    },
                ],
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"Approval ID: `{approval_id}`"},
                ],
            },
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(webhook_url, json=payload)
            resp.raise_for_status()
            logger.info("HITL Slack notification sent for approval %s", approval_id)
            return True
    except Exception as e:
        logger.error("HITL Slack failed for %s: %s", approval_id, e)
        return False


# ── In-app WebSocket push ─────────────────────────────────────────────────────

async def _send_in_app(
    approval_id:     str,
    action_type:     str,
    context_summary: str,
    session_id:      str,
) -> bool:
    """
    Push HITL notification to the user's active WebSocket session via Redis pub/sub.
    The WebSocket endpoint subscribes to `hitl:{session_id}` channel.
    """
    try:
        from backend.session.redis_client import get_redis
        redis = await get_redis()
        message = json.dumps({
            "type":            "hitl_pending",
            "approval_id":     approval_id,
            "action_type":     action_type,
            "context_summary": context_summary,
            "message":         f"⏳ Action '{action_type}' is waiting for your approval.",
        })
        await redis.publish(f"hitl:{session_id}", message)
        logger.info("HITL in-app push sent for session %s", session_id)
        return True
    except Exception as e:
        logger.error("HITL in-app push failed: %s", e)
        return False


# ── Audit log helper ─────────────────────────────────────────────────────────

async def _log_notification(
    approval_id: str,
    channel:     str,
    recipient:   str,
    success:     bool,
    pool=None,
) -> None:
    try:
        if pool is None:
            from backend.prompts.registry import get_pool
            pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO hitl_notifications (approval_id, channel, recipient, status)
                VALUES ($1::uuid, $2, $3, $4)
                """,
                approval_id, channel, recipient, "sent" if success else "failed",
            )
    except Exception as e:
        logger.debug("hitl_notifications log failed (non-fatal): %s", e)


# ── Public dispatcher ────────────────────────────────────────────────────────

async def send_hitl_notifications(
    approval_id:     str,
    action_type:     str,
    context_summary: str,
    user_id:         str,
    session_id:      str,
    reviewer_email:  Optional[str] = None,
    expires_at:      Optional[datetime] = None,
) -> None:
    """
    Fire all HITL notifications concurrently.
    Called from hitl_manager when a new approval request is created.
    Non-blocking — caller should use asyncio.create_task().
    """
    if expires_at is None:
        from datetime import timedelta
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)

    email  = reviewer_email or getattr(settings, "hitl_reviewer_email", None)
    tasks  = []

    if email:
        tasks.append(_send_email(email, approval_id, action_type, context_summary, expires_at))
    tasks.append(_send_slack(approval_id, action_type, context_summary, user_id, expires_at))
    tasks.append(_send_in_app(approval_id, action_type, context_summary, session_id))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Log each channel result
    channels  = (["email"] if email else []) + ["slack", "in_app"]
    recipients = ([email]  if email else []) + ["#hitl-approvals", session_id]

    for channel, recipient, result in zip(channels, recipients, results):
        success = result is True
        asyncio.create_task(_log_notification(approval_id, channel, recipient, success))
