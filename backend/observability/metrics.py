"""
Prometheus metrics for the AI Agentic Assistant.

Exposed at GET /metrics (restricted to private networks in nginx).
"""
import logging
from typing import Any

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# ── Metrics ───────────────────────────────────────────────────────────────────

agent_runs_total = Counter(
    "agent_runs_total",
    "Total number of agent runs",
    ["status"],        # "success" | "error"
)

agent_latency_seconds = Histogram(
    "agent_latency_seconds",
    "End-to-end agent run latency in seconds",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
)

node_latency_seconds = Histogram(
    "node_latency_seconds",
    "Per-node latency in seconds",
    ["node"],
    buckets=[0.05, 0.1, 0.5, 1.0, 5.0, 15.0],
)

active_sessions = Gauge(
    "active_websocket_sessions",
    "Number of currently connected WebSocket sessions",
)

# ── Helper ────────────────────────────────────────────────────────────────────


def record_agent_run(
    status: str,
    latency_s: float,
    node_times: dict[str, Any],
) -> None:
    """
    Record a completed agent run.

    Args:
        status:     "success" or "error"
        latency_s:  total wall-clock seconds for the run
        node_times: dict of {node_name: latency_ms}
    """
    try:
        agent_runs_total.labels(status=status).inc()
        agent_latency_seconds.observe(latency_s)

        for node_name, ms in node_times.items():
            try:
                node_latency_seconds.labels(node=node_name).observe(
                    float(ms) / 1000.0
                )
            except Exception:
                pass
    except Exception as e:
        logger.warning(f"Metrics recording failed (non-fatal): {e}")


# ── ASGI endpoint ─────────────────────────────────────────────────────────────


async def metrics_endpoint(request: Request) -> Response:
    """Starlette-compatible /metrics endpoint for Prometheus scraping."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
