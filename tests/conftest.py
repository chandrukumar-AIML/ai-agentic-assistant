"""
Shared pytest fixtures for the AI Agentic test suite.
Runs against a live backend (start with: uvicorn backend.main:app).
Set APP_ENV=test in .env.test to skip heavy model loads.
"""
import os
import pytest
import httpx

# Backend URL — override with TEST_BASE_URL env var
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def client():
    """Synchronous HTTPX client for the full test session."""
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as c:
        yield c


@pytest.fixture(scope="session")
def admin_token(client):
    """Log in as admin and return Bearer token."""
    resp = client.post("/api/auth/login", json={"email": "admin@agentic.local", "password": "admin123"})
    assert resp.status_code == 200, f"Admin login failed: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def auth_headers(admin_token):
    """Headers dict with admin Bearer token."""
    return {"Authorization": f"Bearer {admin_token}"}
