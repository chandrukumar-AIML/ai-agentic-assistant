# backend/api/webhook_routes.py — Webhook registration + in-app notification store
import uuid
import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl

from backend.api.auth import verify_token

logger = logging.getLogger(__name__)
router = APIRouter()

# ─── In-memory stores (swap to Redis/DB in production) ───────────────────────
_webhooks:       list[dict] = []   # registered webhook endpoints
_notifications:  list[dict] = []   # system notification log (last 100)

VALID_EVENTS = {
    "agent.response",
    "hitl.created",
    "hitl.resolved",
    "scheduler.completed",
    "ingest.completed",
    "budget.alert",
    "compliance.violation",
    "user.login",
}


# ─── Pydantic schemas ─────────────────────────────────────────────────────────
class WebhookCreate(BaseModel):
    name:   str
    url:    str
    events: list[str]
    secret: Optional[str] = None


class WebhookTest(BaseModel):
    payload: Optional[dict] = None


# ─── Internal helpers ─────────────────────────────────────────────────────────
def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _fire_webhook(webhook: dict, event: str, payload: dict):
    """Fire a webhook in the background — never raises."""
    try:
        import httpx
        data = {
            "event":     event,
            "timestamp": _now(),
            "payload":   payload,
            "webhook_id": webhook["id"],
        }
        headers = {"Content-Type": "application/json"}
        if webhook.get("secret"):
            import hmac, hashlib, json
            body    = json.dumps(data)
            sig     = hmac.new(webhook["secret"].encode(), body.encode(), hashlib.sha256).hexdigest()
            headers["X-Webhook-Signature"] = f"sha256={sig}"

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(webhook["url"], json=data, headers=headers)
            logger.info(f"Webhook {webhook['id']} → {resp.status_code}")
    except Exception as exc:
        logger.warning(f"Webhook fire failed ({webhook['url']}): {exc}")


async def push_notification(
    title:   str,
    message: str,
    type:    str = "info",     # info | success | warning | error
    source:  str = "system",
    event:   Optional[str] = None,
    payload: Optional[dict] = None,
):
    """
    Push an in-app notification AND fire matching webhooks.
    Call this from any feature when something notable happens.
    """
    notif = {
        "id":        str(uuid.uuid4()),
        "title":     title,
        "message":   message,
        "type":      type,
        "source":    source,
        "read":      False,
        "created_at": _now(),
    }
    _notifications.append(notif)

    # Keep only the last 100
    if len(_notifications) > 100:
        _notifications.pop(0)

    # Fire matching webhooks in background
    if event:
        targets = [w for w in _webhooks if event in w.get("events", [])]
        if targets and payload:
            await asyncio.gather(
                *[_fire_webhook(w, event, payload) for w in targets],
                return_exceptions=True,
            )

    return notif


# ─── Notifications endpoints ──────────────────────────────────────────────────
@router.get("/notifications")
async def get_notifications(_token: dict = Depends(verify_token)):
    """Return last 50 notifications, newest first."""
    return {
        "notifications": list(reversed(_notifications[-50:])),
        "unread_count":  sum(1 for n in _notifications if not n["read"]),
    }


@router.post("/notifications/mark-read")
async def mark_all_read(_token: dict = Depends(verify_token)):
    """Mark all notifications as read."""
    for n in _notifications:
        n["read"] = True
    return {"ok": True, "marked": len(_notifications)}


@router.delete("/notifications/{notif_id}")
async def delete_notification(notif_id: str, _token: dict = Depends(verify_token)):
    global _notifications
    before = len(_notifications)
    _notifications = [n for n in _notifications if n["id"] != notif_id]
    if len(_notifications) == before:
        raise HTTPException(404, "Notification not found")
    return {"ok": True}


# ─── Webhook CRUD endpoints ───────────────────────────────────────────────────
@router.get("/webhooks")
async def list_webhooks(_token: dict = Depends(verify_token)):
    return {
        "webhooks":     _webhooks,
        "valid_events": sorted(VALID_EVENTS),
    }


@router.post("/webhooks", status_code=201)
async def create_webhook(body: WebhookCreate, _token: dict = Depends(verify_token)):
    invalid = [e for e in body.events if e not in VALID_EVENTS]
    if invalid:
        raise HTTPException(400, f"Unknown events: {invalid}. Valid: {sorted(VALID_EVENTS)}")

    webhook = {
        "id":         str(uuid.uuid4()),
        "name":       body.name,
        "url":        body.url,
        "events":     body.events,
        "secret":     body.secret,
        "active":     True,
        "created_at": _now(),
        "last_fired": None,
        "fire_count": 0,
    }
    _webhooks.append(webhook)
    logger.info(f"Webhook registered: {webhook['name']} → {webhook['url']}")
    return webhook


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(webhook_id: str, _token: dict = Depends(verify_token)):
    global _webhooks
    before = len(_webhooks)
    _webhooks = [w for w in _webhooks if w["id"] != webhook_id]
    if len(_webhooks) == before:
        raise HTTPException(404, "Webhook not found")
    return {"ok": True}


@router.post("/webhooks/{webhook_id}/test")
async def test_webhook(webhook_id: str, _token: dict = Depends(verify_token)):
    """Fire a test payload to the registered webhook URL."""
    wh = next((w for w in _webhooks if w["id"] == webhook_id), None)
    if not wh:
        raise HTTPException(404, "Webhook not found")

    test_payload = {
        "test":    True,
        "message": "This is a test event from AI Agentic Assistant V2",
        "agent":   "system",
    }
    asyncio.create_task(_fire_webhook(wh, "agent.response", test_payload))
    wh["last_fired"] = _now()
    wh["fire_count"] += 1
    return {"ok": True, "message": f"Test event fired to {wh['url']}"}


@router.patch("/webhooks/{webhook_id}/toggle")
async def toggle_webhook(webhook_id: str, _token: dict = Depends(verify_token)):
    wh = next((w for w in _webhooks if w["id"] == webhook_id), None)
    if not wh:
        raise HTTPException(404, "Webhook not found")
    wh["active"] = not wh["active"]
    return {"ok": True, "active": wh["active"]}
