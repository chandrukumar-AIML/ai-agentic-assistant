"""Tests for vertical action endpoints — runs with DEMO_MODE=true."""
import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def authed_client():
    """Client with a valid JWT token from the demo admin user."""
    from backend.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        login = await c.post("/api/auth/login", json={"email": "admin@agentic.local", "password": "admin123"})
        token = login.json()["access_token"]
        c.headers["Authorization"] = f"Bearer {token}"
        yield c


async def test_social_action_requires_auth(authed_client):
    r = await authed_client.post(
        "/api/verticals/social/action",
        json={"action": "generate", "platform": "linkedin", "payload": {"topic": "AI tools for SMBs"}, "language": "en"},
        headers={"Authorization": ""},
    )
    assert r.status_code == 401


async def test_social_generate(authed_client):
    r = await authed_client.post(
        "/api/verticals/social/action",
        json={"action": "generate", "platform": "linkedin", "payload": {"topic": "AI tools for SMBs"}, "language": "en"},
    )
    assert r.status_code == 200
    assert "error" not in r.json() or r.json().get("error") in (None, False, "")


async def test_ca_gst_query(authed_client):
    r = await authed_client.post(
        "/api/verticals/ca/action",
        json={"action": "gst_query", "payload": {"query": "What is the GST rate for IT services?"}, "language": "en"},
    )
    assert r.status_code == 200
    assert "error" not in r.json() or r.json().get("error") in (None, False, "")


async def test_cs_faq_bot(authed_client):
    r = await authed_client.post(
        "/api/verticals/cs/action",
        json={"action": "faq_bot", "payload": {"question": "What are your business hours?"}, "language": "en"},
    )
    assert r.status_code == 200
    assert "error" not in r.json() or r.json().get("error") in (None, False, "")


async def test_invalid_payload_schema(authed_client):
    """Missing required 'action' field should return 422 Unprocessable Entity."""
    r = await authed_client.post(
        "/api/verticals/ca/action",
        json={"payload": {}, "language": "en"},
    )
    assert r.status_code == 422
