"""
Load test — measures real p50/p95/p99 latency for the AI Agentic backend.
Uses DEMO_MODE so no LLM cost. Run against a live or local server.

Usage:
    # Local (start backend first: python -m uvicorn backend.main:app --port 8001)
    python qa/load_test.py --url http://localhost:8001 --users 10 --duration 30

    # Against live Render (DEMO_MODE must be enabled)
    python qa/load_test.py --url https://ai-agentic-backend-ywdx.onrender.com --users 5 --duration 20
"""
from __future__ import annotations

import argparse
import asyncio
import statistics
import time
from typing import NamedTuple

import httpx


BASE_PAYLOADS = [
    ("social", {"action": "generate", "platform": "linkedin", "payload": {"topic": "AI for SMBs"}, "language": "en"}),
    ("ca",     {"action": "gst_query", "payload": {"query": "What is GST rate for IT services?"}, "language": "en"}),
    ("cs",     {"action": "faq_bot",   "payload": {"business_name": "Test Co", "business_type": "Retail", "faq_context": "We are open 9-6", "customer_question": "What are your timings?"}, "language": "en"}),
    ("social", {"action": "hashtags",  "platform": "instagram", "payload": {"topic": "healthy food India"}, "language": "en"}),
    ("ca",     {"action": "deadlines", "payload": {}, "language": "en"}),
]


class Result(NamedTuple):
    vertical: str
    status:   int
    latency_ms: float
    ok: bool


async def _login(client: httpx.AsyncClient, base_url: str) -> str:
    r = await client.post(f"{base_url}/api/auth/login", json={"email": "admin@agentic.local", "password": "admin123"})
    r.raise_for_status()
    return r.json()["access_token"]


async def _one_request(client: httpx.AsyncClient, base_url: str, token: str, vertical: str, body: dict) -> Result:
    url = f"{base_url}/api/verticals/{vertical}/action"
    headers = {"Authorization": f"Bearer {token}"}
    t0 = time.monotonic()
    try:
        r = await client.post(url, json=body, headers=headers, timeout=30.0)
        ms = (time.monotonic() - t0) * 1000
        ok = r.status_code == 200 and "error" not in r.json()
        return Result(vertical=vertical, status=r.status_code, latency_ms=ms, ok=ok)
    except Exception as exc:
        ms = (time.monotonic() - t0) * 1000
        return Result(vertical=vertical, status=0, latency_ms=ms, ok=False)


async def run(base_url: str, concurrent_users: int, duration_s: int) -> None:
    print(f"\n🔥 Load test — {base_url}")
    print(f"   {concurrent_users} concurrent users · {duration_s}s duration\n")

    results: list[Result] = []
    deadline = time.monotonic() + duration_s

    async with httpx.AsyncClient() as client:
        token = await _login(client, base_url)
        print(f"   ✅ Logged in\n")

        async def worker():
            idx = 0
            while time.monotonic() < deadline:
                vertical, body = BASE_PAYLOADS[idx % len(BASE_PAYLOADS)]
                r = await _one_request(client, base_url, token, vertical, body)
                results.append(r)
                idx += 1

        await asyncio.gather(*[worker() for _ in range(concurrent_users)])

    if not results:
        print("No results collected.")
        return

    latencies = [r.latency_ms for r in results]
    latencies.sort()
    ok_count = sum(1 for r in results if r.ok)
    err_count = len(results) - ok_count

    p50 = statistics.median(latencies)
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]
    rps  = len(results) / duration_s

    print("=" * 50)
    print(f"  Total requests : {len(results)}")
    print(f"  Success        : {ok_count}  ({ok_count/len(results)*100:.1f}%)")
    print(f"  Errors         : {err_count} ({err_count/len(results)*100:.1f}%)")
    print(f"  Throughput     : {rps:.1f} req/s")
    print(f"  p50 latency    : {p50:.0f}ms")
    print(f"  p95 latency    : {p95:.0f}ms")
    print(f"  p99 latency    : {p99:.0f}ms")
    print(f"  Min / Max      : {min(latencies):.0f}ms / {max(latencies):.0f}ms")
    print("=" * 50)

    by_vertical: dict[str, list[float]] = {}
    for r in results:
        by_vertical.setdefault(r.vertical, []).append(r.latency_ms)
    print("\nPer-vertical p95:")
    for v, lats in sorted(by_vertical.items()):
        lats.sort()
        vp95 = lats[int(len(lats) * 0.95)]
        print(f"  {v:8s}  p95={vp95:.0f}ms  n={len(lats)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url",      default="http://localhost:8001")
    parser.add_argument("--users",    type=int, default=5)
    parser.add_argument("--duration", type=int, default=30)
    args = parser.parse_args()
    asyncio.run(run(args.url, args.users, args.duration))
