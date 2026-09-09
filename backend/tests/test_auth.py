"""Tests for auth endpoints."""
import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def client():
    from backend.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_login_admin(client):
    r = await client.post("/api/auth/login", json={"email": "admin@agentic.local", "password": "admin123"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_login_demo(client):
    r = await client.post("/api/auth/login", json={"email": "demo@agentic.local", "password": "demo123"})
    assert r.status_code == 200
    assert "access_token" in r.json()


async def test_login_wrong_password(client):
    r = await client.post("/api/auth/login", json={"email": "admin@agentic.local", "password": "wrong"})
    assert r.status_code == 401


async def test_login_unknown_user(client):
    r = await client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "x"})
    assert r.status_code == 401


async def test_me_requires_auth(client):
    r = await client.get("/api/auth/me")
    assert r.status_code == 401


async def test_me_with_token(client):
    login = await client.post("/api/auth/login", json={"email": "admin@agentic.local", "password": "admin123"})
    token = login.json()["access_token"]
    r = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "admin@agentic.local"


async def test_register_new_user(client):
    r = await client.post("/api/auth/register", json={
        "email": "newuser@test.com",
        "password": "strongpass123",
        "full_name": "Test User",
    })
    assert r.status_code == 201
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "newuser@test.com"
    assert data["user"]["role"] == "member"


async def test_register_duplicate_email(client):
    await client.post("/api/auth/register", json={
        "email": "dup@test.com", "password": "pass12345", "full_name": "Dup User"
    })
    r = await client.post("/api/auth/register", json={
        "email": "dup@test.com", "password": "pass12345", "full_name": "Dup User"
    })
    assert r.status_code == 409


async def test_register_short_password(client):
    r = await client.post("/api/auth/register", json={
        "email": "short@test.com", "password": "abc", "full_name": "Short"
    })
    assert r.status_code == 422


async def test_refresh_token(client):
    login = await client.post("/api/auth/login", json={"email": "admin@agentic.local", "password": "admin123"})
    refresh_tok = login.json()["refresh_token"]
    r = await client.post("/api/auth/refresh", json={"refresh_token": refresh_tok})
    assert r.status_code == 200
    assert "access_token" in r.json()


async def test_refresh_with_access_token_fails(client):
    login = await client.post("/api/auth/login", json={"email": "admin@agentic.local", "password": "admin123"})
    access_tok = login.json()["access_token"]
    r = await client.post("/api/auth/refresh", json={"refresh_token": access_tok})
    assert r.status_code == 401
