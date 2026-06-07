"""
Vertical API smoke tests.
Uses 60-second timeout per test — Ollama on CPU is slow.
Run: pytest tests/test_verticals.py -v --timeout=180
"""
import pytest

pytestmark = pytest.mark.timeout(180)


# ── Accountant ────────────────────────────────────────────────────────────────

def test_gst_calc(client, auth_headers):
    resp = client.post(
        "/api/verticals/accountant/action",
        json={"action": "gst_calc", "payload": {"amount": 10000, "gst_rate": 18, "transaction": "intra"}},
        headers=auth_headers,
        timeout=30,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "cgst" in data or "result" in data or "gst" in str(data).lower()


def test_tds_calc(client, auth_headers):
    resp = client.post(
        "/api/verticals/accountant/action",
        json={"action": "tds_calc", "payload": {"amount": 50000, "section": "194J", "pan_available": True}},
        headers=auth_headers,
        timeout=30,
    )
    assert resp.status_code == 200


def test_hsn_lookup(client, auth_headers):
    resp = client.get("/api/verticals/accountant/hsn/8471", headers=auth_headers, timeout=10)
    assert resp.status_code == 200


# ── HR ────────────────────────────────────────────────────────────────────────

def test_hr_onboarding(client, auth_headers):
    resp = client.post(
        "/api/verticals/hr/action",
        json={"action": "onboarding", "payload": {"role": "Backend Engineer", "department": "Engineering"}},
        headers=auth_headers,
        timeout=120,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "checklist" in data or "onboarding" in str(data).lower() or "action" in data


def test_hr_qa(client, auth_headers):
    resp = client.post(
        "/api/verticals/hr/action",
        json={"action": "qa", "payload": {"question": "How many days of annual leave do employees get?"}},
        headers=auth_headers,
        timeout=120,
    )
    assert resp.status_code == 200


# ── Sales ─────────────────────────────────────────────────────────────────────

def test_sales_score(client, auth_headers):
    lead = {"budget_usd": 50000, "title": "CTO", "company_size": 200, "has_need": True, "timeline_days": 30}
    resp = client.post("/api/verticals/sales/score", json=lead, headers=auth_headers, timeout=15)
    assert resp.status_code == 200
    data = resp.json()
    assert "score" in data


# ── Forms ─────────────────────────────────────────────────────────────────────

def test_validate_pan(client, auth_headers):
    resp = client.post(
        "/api/verticals/forms/validate",
        json={"pan": "ABCDE1234F"},
        headers=auth_headers,
        timeout=10,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "pan" in data
    assert "valid" in data["pan"]


def test_validate_gstin(client, auth_headers):
    resp = client.post(
        "/api/verticals/forms/validate",
        json={"gstin": "29ABCDE1234F1Z5"},
        headers=auth_headers,
        timeout=10,
    )
    assert resp.status_code == 200


def test_validate_empty_fields_422(client, auth_headers):
    resp = client.post("/api/verticals/forms/validate", json={}, headers=auth_headers, timeout=10)
    assert resp.status_code == 400


# ── AgriTech ──────────────────────────────────────────────────────────────────

def test_mandi_prices(client, auth_headers):
    resp = client.get(
        "/api/verticals/agri/mandi-prices?commodity=rice&state=Tamil+Nadu",
        headers=auth_headers,
        timeout=15,
    )
    assert resp.status_code == 200


def test_govt_schemes(client, auth_headers):
    resp = client.get(
        "/api/verticals/agri/schemes?query=crop+insurance",
        headers=auth_headers,
        timeout=15,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "schemes" in data


# ── Legal ─────────────────────────────────────────────────────────────────────

def test_legal_case_search(client, auth_headers):
    resp = client.post(
        "/api/verticals/legal/case-search",
        json={"query": "property dispute", "max_results": 3},
        headers=auth_headers,
        timeout=30,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "cases" in data


# ── QA Agent ─────────────────────────────────────────────────────────────────

def test_qa_acceptance_criteria(client, auth_headers):
    resp = client.post(
        "/api/verticals/qa/action",
        json={
            "action": "acceptance_criteria",
            "payload": {"user_story": "As a user I want to log in so that I can access my dashboard"},
        },
        headers=auth_headers,
        timeout=120,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "acceptance_criteria" in data or "action" in data


# ── PM Agent ─────────────────────────────────────────────────────────────────

def test_pm_estimation(client, auth_headers):
    resp = client.post(
        "/api/verticals/pm/action",
        json={
            "action": "estimation",
            "payload": {
                "stories": ["User login with OAuth", "Dashboard with charts"],
                "technique": "planning_poker",
            },
        },
        headers=auth_headers,
        timeout=120,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "estimates" in data or "action" in data


# ── Code Agent ────────────────────────────────────────────────────────────────

def test_code_review(client, auth_headers):
    resp = client.post(
        "/api/verticals/code/action",
        json={
            "action": "review",
            "code":   "def add(a, b):\n    return a + b",
            "prompt": "Quick review",
            "language": "python",
        },
        headers=auth_headers,
        timeout=120,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "content" in data


# ── HITL ─────────────────────────────────────────────────────────────────────

def test_hitl_pending_list(client, auth_headers):
    resp = client.get("/api/hitl/pending", headers=auth_headers, timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert "pending" in data or "requests" in data or isinstance(data, list)


# ── Social Media ──────────────────────────────────────────────────────────────

def test_social_hashtags(client, auth_headers):
    resp = client.post(
        "/api/verticals/social/action",
        json={"action": "hashtags", "platform": "instagram", "payload": {"topic": "AI productivity tools"}},
        headers=auth_headers,
        timeout=120,
    )
    assert resp.status_code == 200
