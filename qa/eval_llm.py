# -*- coding: utf-8 -*-
"""
LLM Eval Framework — AI Agentic Assistant
Automated quality scoring for LLM responses across all verticals.

Usage:
    python qa/eval_llm.py              # runs all eval suites
    python qa/eval_llm.py --vertical cs   # CS only
    python qa/eval_llm.py --vertical ca   # CA only
"""
import sys, json, re, time, argparse, urllib.request
from dataclasses import dataclass, field
from typing import Optional

sys.stdout.reconfigure(encoding='utf-8')

BASE = "http://localhost:8000"

# ── Scoring dimensions ────────────────────────────────────────────────────────

@dataclass
class EvalResult:
    action: str
    vertical: str
    latency_ms: float
    completeness: float   # 0–1: did the response have all expected keys?
    length_score: float   # 0–1: is response length reasonable?
    json_valid: bool      # did it return parseable structured output?
    error: Optional[str] = None
    raw_keys: list = field(default_factory=list)

    @property
    def score(self) -> float:
        if self.error:
            return 0.0
        return round((self.completeness * 0.5 + self.length_score * 0.3 + (1.0 if self.json_valid else 0.0) * 0.2), 3)

    @property
    def grade(self) -> str:
        s = self.score
        if s >= 0.9: return "A"
        if s >= 0.8: return "B"
        if s >= 0.7: return "C"
        if s >= 0.5: return "D"
        return "F"


def _post(path: str, body: dict, timeout: int = 90):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{BASE}{path}", data=data,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            result = json.loads(r.read())
            ms = round((time.monotonic() - t0) * 1000, 1)
            return result, ms, None
    except Exception as e:
        ms = round((time.monotonic() - t0) * 1000, 1)
        return None, ms, str(e)


def _score_response(r: dict, expected_keys: list[str], min_len: int = 20) -> tuple[float, float, bool]:
    """Returns (completeness, length_score, json_valid)."""
    if r is None:
        return 0.0, 0.0, False

    # completeness — what fraction of expected keys are present?
    present = sum(1 for k in expected_keys if k in r and r[k] not in (None, "", [], {}))
    completeness = present / len(expected_keys) if expected_keys else 1.0

    # length_score — penalise responses that are too short or suspiciously empty
    total_chars = sum(len(str(v)) for v in r.values())
    length_score = min(1.0, total_chars / 200)   # 200 chars = full score

    return completeness, length_score, True


def eval_action(vertical: str, action: str, payload: dict, expected_keys: list[str]) -> EvalResult:
    path = f"/api/verticals/{vertical}/action"
    body = {"action": action, "payload": payload, "language": "en"}
    r, ms, err = _post(path, body)

    if err or r is None:
        return EvalResult(action=action, vertical=vertical, latency_ms=ms,
                          completeness=0.0, length_score=0.0, json_valid=False, error=err)

    if r.get("error") not in (None, False, ""):
        return EvalResult(action=action, vertical=vertical, latency_ms=ms,
                          completeness=0.0, length_score=0.0, json_valid=False,
                          error=str(r.get("error", ""))[:80], raw_keys=list(r.keys()))

    comp, lscore, valid = _score_response(r, expected_keys)
    return EvalResult(action=action, vertical=vertical, latency_ms=ms,
                      completeness=comp, length_score=lscore, json_valid=valid,
                      raw_keys=list(r.keys()))


# ── Eval suites ───────────────────────────────────────────────────────────────

CS_EVALS = [
    ("faq_bot",          {"query": "Order not delivered", "business_name": "ShopEasy", "business_type": "ecommerce", "faq_context": "Deliver in 3-5 days"},                                   ["answer", "confidence"]),
    ("analyze_sentiment", {"text": "I'm very frustrated with this order!", "customer_name": "Rajesh"},                                                                                        ["sentiment", "urgency", "score"]),
    ("handle_complaint",  {"complaint": "Wrong item sent", "customer_name": "Rajesh", "order_id": "SHE-001", "business_name": "ShopEasy", "category": "product"},                           ["acknowledgment", "resolution_steps"]),
    ("ticket_triage",     {"ticket_text": "My ₹45K jewellery order is missing for 7 days!", "customer_name": "Rajesh", "channel": "whatsapp", "customer_tier": "gold", "is_repeat_contact": True}, ["priority", "category"]),
    ("summarize_ticket",  {"conversation": "Customer: Missing order. Agent: Will check. Agent: Re-dispatching.", "customer_name": "Rajesh"},                                                  ["issue_summary", "customer_mood"]),
    ("weekly_report",     {"ticket_data": "247 tickets, 198 resolved", "period": "July 2025", "business_name": "ShopEasy"},                                                                  ["executive_summary", "top_issues"]),
    ("customer_360",      {"customer_name": "Rajesh Kumar", "customer_email": "r@g.com", "customer_since_months": 18, "total_orders": 23, "total_revenue": 87500, "last_order_days_ago": 12, "open_tickets": 1, "total_tickets": 5, "avg_resolution_hrs": 8, "avg_csat": 4.0, "plan_type": "Gold", "has_referred": True, "payment_status": "current"}, ["customer_name", "customer_email"]),
    ("csat_survey",       {"business_name": "ShopEasy", "product_name": "ShopEasy App", "survey_goal": "post_purchase", "customer_segment": "repeat_buyers", "industry": "ecommerce", "max_questions": 5, "include_nps": True}, ["survey_focus", "business_name"]),
    ("analyze_csat",      {"responses": [{"rating": 5, "comment": "Great!", "touchpoint": "post_delivery"}, {"rating": 2, "comment": "Late", "touchpoint": "post_support"}], "business_name": "ShopEasy"}, ["csat_score", "avg_rating"]),
    ("churn_risk",        {"customers": [{"name": "Rajesh", "days_since_last_login": 3, "support_tickets_30d": 1, "nps": 8, "ltv": 87500, "contract_end_days": 180}], "business_name": "ShopEasy", "industry": "ecommerce"}, ["total_analyzed", "high_count"]),
]

CA_EVALS = [
    ("gst_query",    {"query": "GST on yoga mats?", "gstin": "29AABCU9603R1ZX"},                                         ["answer"]),
    ("tds_calc",     {"section": "194J", "amount": 150000, "pan_available": True, "payee_type": "individual"},           ["tds_amount"]),
    ("deadlines",    {"month": 7, "year": 2025, "taxpayer_type": "regular"},                                             ["deadlines", "count"]),
    ("itr_advice",   {"income_sources": ["salary"], "gross_income": 900000, "taxpayer_type": "individual", "age": 32, "has_80c": True, "has_hra": True}, ["itr_form"]),
    ("capital_gains", {"asset_type": "property", "purchase_price": 5000000, "sale_price": 8500000, "purchase_date": "2018-03-15", "sale_date": "2025-01-10", "sale_expenses": 85000}, ["gross_gain", "term_label"]),
    ("tax_planning", {"income_details": {"salary": 900000}, "investments": {"ppf": 60000}, "expenses": {"hra_paid": 336000}, "taxpayer_type": "individual", "age": 35, "regime": "old"}, ["taxpayer_type", "recommendations"]),
    ("advance_tax",  {"taxpayer_name": "Priya", "taxpayer_type": "individual", "financial_year": "2025-26", "estimated_income": 1200000, "salary_income": 900000, "tds_deducted": 80000, "regime": "new", "deductions_80c": 150000}, ["installments", "income_summary"]),
    ("cash_flow_forecast", {"company_name": "ZenFit", "monthly_revenue": 2083333, "revenue_growth": 8, "fixed_expenses": 800000, "variable_expense_pct": 35, "opening_cash": 1500000, "industry": "wellness"}, ["company_name", "opening_cash", "closing_cash"]),
    ("business_valuation", {"revenue": 25000000, "ebitda": 5000000, "net_profit": 3500000, "industry": "wellness", "stage": "growth", "growth_rate": 25, "assets": 10000000, "liabilities": 4000000}, ["industry", "inputs", "financials"]),
    ("gst_notice_reply", {"notice_type": "scrutiny", "notice_ref": "GSTN/SCR/2025", "gstin": "29ZENFIT1234R1Z5", "taxpayer_name": "ZenFit", "notice_details": "ITC mismatch", "reply_points": "Clerical error"}, ["notice_type", "taxpayer_name", "gstin"]),
]

SM_EVALS = [
    ("generate_post", {"platform": "linkedin", "topic": "AI for Indian SMBs", "business_name": "TechStartup", "tone": "professional"}, ["post"]),
    ("hashtag_research", {"topic": "Indian ecommerce growth", "platform": "instagram", "count": 10}, ["hashtags"]),
    ("content_calendar", {"business_name": "ShopEasy", "industry": "ecommerce", "platforms": ["instagram", "linkedin"], "days": 7}, ["calendar"]),
]


def run_suite(vertical: str, evals: list, label: str) -> list[EvalResult]:
    print(f"\n{'='*70}")
    print(f"  EVAL SUITE — {label}")
    print(f"{'='*70}")
    results = []
    for action, payload, expected_keys in evals:
        r = eval_action(vertical, action, payload, expected_keys)
        icon = "✓" if r.grade in ("A","B") else ("~" if r.grade == "C" else "✗")
        print(f"  {icon} [{r.grade}] {action:<42} score={r.score:.2f}  {r.latency_ms:.0f}ms"
              + (f"  ⚠ {r.error[:50]}" if r.error else ""))
        results.append(r)
    return results


def print_summary(all_results: list[EvalResult]) -> None:
    print(f"\n{'='*70}")
    print("  EVAL SUMMARY")
    print(f"{'='*70}")
    avg_score = sum(r.score for r in all_results) / len(all_results)
    avg_latency = sum(r.latency_ms for r in all_results) / len(all_results)
    grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    for r in all_results:
        grade_counts[r.grade] += 1

    print(f"  Total actions evaluated : {len(all_results)}")
    print(f"  Average quality score   : {avg_score:.3f} / 1.000")
    print(f"  Average latency         : {avg_latency:.0f}ms")
    print(f"  Grade distribution      : A={grade_counts['A']}  B={grade_counts['B']}  C={grade_counts['C']}  D={grade_counts['D']}  F={grade_counts['F']}")
    print(f"\n  Lowest scoring actions (need prompt improvement):")
    worst = sorted(all_results, key=lambda r: r.score)[:5]
    for r in worst:
        print(f"    [{r.grade}] {r.vertical}/{r.action}  score={r.score:.2f}" + (f"  error={r.error[:40]}" if r.error else ""))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LLM Eval Framework")
    parser.add_argument("--vertical", choices=["cs", "ca", "sm", "all"], default="all")
    args = parser.parse_args()

    all_results = []

    if args.vertical in ("cs", "all"):
        all_results += run_suite("cs", CS_EVALS, "Customer Support Agent")

    if args.vertical in ("ca", "all"):
        all_results += run_suite("ca", CA_EVALS, "CA Accounting Agent")

    if args.vertical in ("sm", "all"):
        all_results += run_suite("sm", SM_EVALS, "Social Media Agent")

    print_summary(all_results)
