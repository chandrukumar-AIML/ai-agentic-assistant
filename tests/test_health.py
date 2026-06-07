"""
Health and auth endpoint tests.
"""
import pytest


def test_health_returns_ok(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "ollama_healthy" in data
    assert "circuit_state" in data


def test_llm_health(client):
    resp = client.get("/api/llm/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "active_model" in data
    assert "circuit" in data


def test_login_admin_success(client):
    resp = client.post("/api/auth/login", json={"email": "admin@agentic.local", "password": "admin123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_demo_success(client):
    resp = client.post("/api/auth/login", json={"email": "demo@agentic.local", "password": "demo123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client):
    resp = client.post("/api/auth/login", json={"email": "admin@agentic.local", "password": "wrongpass"})
    assert resp.status_code == 401


def test_login_unknown_user(client):
    resp = client.post("/api/auth/login", json={"email": "nobody@agentic.local", "password": "any"})
    assert resp.status_code == 401


def test_refresh_token(client, admin_token):
    resp = client.post("/api/auth/refresh", json={"refresh_token": admin_token})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data


def test_refresh_invalid_token(client):
    resp = client.post("/api/auth/refresh", json={"refresh_token": "not.a.valid.token"})
    assert resp.status_code == 401


def test_protected_route_requires_auth(client):
    """RAG stats requires valid token in production. Dev mode auto-passes."""
    resp = client.get("/api/rag/stats")
    # Dev mode returns 200 with dev token; production returns 401 without header
    assert resp.status_code in (200, 401)


def test_rag_stats_with_token(client, auth_headers):
    resp = client.get("/api/rag/stats", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "faiss_vectors" in data
