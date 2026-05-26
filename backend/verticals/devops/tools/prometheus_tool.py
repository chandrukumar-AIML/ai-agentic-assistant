# backend/verticals/devops/tools/prometheus_tool.py
"""
Prometheus metrics query tool.
Fetches key service metrics: error rate, latency, availability.
"""
import logging
import httpx
from datetime import datetime, timezone, timedelta

from backend.config import get_settings  # FIXED: import settings to avoid hardcoded URL

logger   = logging.getLogger(__name__)
settings = get_settings()

# FIXED: hardcoded URL replaced with settings lookup (falls back to localhost for local dev)
PROMETHEUS_URL = getattr(settings, "prometheus_url", "http://localhost:9090")
_client = httpx.AsyncClient(timeout=10.0)


async def query_metric(promql: str, time_range: str = "1h") -> dict:
    """Execute a PromQL instant query."""
    try:
        r = await _client.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": promql},
        )
        r.raise_for_status()
        data   = r.json()
        result = data.get("data", {}).get("result", [])
        return {
            "query":   promql,
            "results": [
                {
                    "labels": r.get("metric", {}),
                    "value":  float(r["value"][1]) if r.get("value") else 0,
                }
                for r in result
            ],
        }
    except Exception as e:
        logger.warning(f"Prometheus query failed: {e}")
        return {"query": promql, "error": str(e)}


async def get_service_health(service_name: str) -> dict:
    """
    Get comprehensive health metrics for a service.
    Returns: error rate, p95 latency, request rate, availability.
    """
    queries = {
        "error_rate":    f'sum(rate(http_request_errors_total{{service="{service_name}"}}[5m]))',
        "p95_latency":   f'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{{service="{service_name}"}}[5m]))',
        "request_rate":  f'sum(rate(http_requests_total{{service="{service_name}"}}[5m]))',
        "availability":  f'avg(up{{service="{service_name}"}})',
    }

    results = {}
    for metric_name, query in queries.items():
        data = await query_metric(query)
        if data.get("results"):
            results[metric_name] = round(float(data["results"][0]["value"]), 4)
        else:
            results[metric_name] = None

    # Determine overall health
    availability = results.get("availability")
    error_rate   = results.get("error_rate", 0) or 0

    health = "healthy"
    if availability is not None and availability < 0.99:
        health = "degraded"
    if availability is not None and availability < 0.95:
        health = "critical"
    if error_rate > 0.05:
        health = "degraded"

    return {
        "service":      service_name,
        "health":       health,
        "metrics":      results,
        "alert":        health in ("degraded", "critical"),
    }


async def get_recent_alerts() -> list[dict]:
    """Fetch currently firing Prometheus alerts."""
    try:
        r = await _client.get(f"{PROMETHEUS_URL}/api/v1/alerts")
        r.raise_for_status()
        alerts = r.json().get("data", {}).get("alerts", [])
        return [
            {
                "name":        a.get("labels", {}).get("alertname", ""),
                "severity":    a.get("labels", {}).get("severity", ""),
                "state":       a.get("state", ""),
                "service":     a.get("labels", {}).get("service", ""),
                "summary":     a.get("annotations", {}).get("summary", ""),
                "started_at":  a.get("activeAt", ""),
            }
            for a in alerts
            if a.get("state") == "firing"
        ]
    except Exception as e:
        logger.warning(f"Prometheus alerts failed: {e}")
        return []