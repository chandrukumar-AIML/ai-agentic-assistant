"""Tests for health endpoints — no auth required."""
import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def client():
    from backend.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_root(client):
    r = await client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "AI Agentic Assistant"
    assert "agents" in data


async def test_health_ok(client):
    r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


async def test_health_deep(client):
    r = await client.get("/api/health/deep")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
    assert "services" in data
    assert isinstance(data["services"], list)
