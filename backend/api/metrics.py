"""Prometheus metrics endpoint — /metrics for observability."""
from __future__ import annotations

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)
from fastapi import APIRouter
from fastapi.responses import Response

router = APIRouter(tags=["observability"])

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["path"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)
llm_calls_total = Counter(
    "llm_calls_total",
    "Total LLM provider calls",
    ["provider", "action", "status"],
)


@router.get("/metrics", include_in_schema=False)
async def metrics():
    """Prometheus scrape endpoint — no auth required."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
