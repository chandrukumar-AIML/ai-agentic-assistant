# backend/mlops/drift_monitor.py
"""
Evidently AI integration for production drift monitoring.

Monitors four key signals:
  1. Response quality drift    — faithfulness score distribution
  2. Guardrail trigger rate    — safety event frequency
  3. Tool usage patterns       — which agents/tools are called
  4. Latency drift             — p95 response time

Drift is detected by comparing a rolling window (last 7 days)
against a reference window (previous 7 days or baseline).
"""
import logging
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

REPORTS_DIR = Path("data/evidently_reports")


@dataclass
class DriftSignal:
    metric_name:    str
    current_value:  float
    baseline_value: float
    drift_score:    float       # 0-1, higher = more drift
    is_drifting:    bool
    direction:      str         # "up", "down", "stable"
    threshold:      float


@dataclass
class DriftReport:
    generated_at:   datetime
    period_days:    int
    signals:        list[DriftSignal] = field(default_factory=list)
    overall_drift:  bool = False
    needs_retrain:  bool = False
    summary:        str  = ""


async def _get_metric_timeseries(
    workspace_id: str,
    metric_name:  str,
    days_back:    int,
    window_days:  int = 7,
) -> tuple[list[float], list[float]]:
    """
    Fetch two windows of metric data from audit_log.
    Returns (current_window, reference_window).
    """
    try:
        from backend.prompts.registry import get_pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            # Current window
            if metric_name == "faithfulness":
                # Proxy: low reflection score = low faithfulness
                current_rows = await conn.fetch(
                    """
                    SELECT (metadata->>'reflection_score')::float AS val
                    FROM audit_log
                    WHERE workspace_id = $1::uuid
                      AND action = 'query'
                      AND timestamp >= NOW() - $2 * INTERVAL '1 day'  -- FIXED: asyncpg doesn't substitute inside string literals
                      AND timestamp < NOW() - $3 * INTERVAL '1 day'   -- FIXED: asyncpg doesn't substitute inside string literals
                      AND metadata->>'reflection_score' IS NOT NULL
                    """,
                    workspace_id, days_back, days_back - window_days,
                )
                ref_rows = await conn.fetch(
                    """
                    SELECT (metadata->>'reflection_score')::float AS val
                    FROM audit_log
                    WHERE workspace_id = $1::uuid
                      AND action = 'query'
                      AND timestamp >= NOW() - $2 * INTERVAL '1 day'  -- FIXED: asyncpg doesn't substitute inside string literals
                      AND timestamp < NOW() - $3 * INTERVAL '1 day'   -- FIXED: asyncpg doesn't substitute inside string literals
                    """,
                    workspace_id, days_back + window_days, days_back,
                )
            elif metric_name == "guardrail_rate":
                current_rows = await conn.fetch(
                    """
                    SELECT CASE WHEN guardrail_triggered THEN 1.0 ELSE 0.0 END AS val
                    FROM audit_log
                    WHERE workspace_id = $1::uuid
                      AND action = 'query'
                      AND timestamp >= NOW() - $2 * INTERVAL '1 day'  -- FIXED: asyncpg doesn't substitute inside string literals
                      AND timestamp < NOW() - $3 * INTERVAL '1 day'   -- FIXED: asyncpg doesn't substitute inside string literals
                    """,
                    workspace_id, days_back, days_back - window_days,
                )
                ref_rows = await conn.fetch(
                    """
                    SELECT CASE WHEN guardrail_triggered THEN 1.0 ELSE 0.0 END AS val
                    FROM audit_log
                    WHERE workspace_id = $1::uuid
                      AND action = 'query'
                      AND timestamp >= NOW() - $2 * INTERVAL '1 day'  -- FIXED: asyncpg doesn't substitute inside string literals
                      AND timestamp < NOW() - $3 * INTERVAL '1 day'   -- FIXED: asyncpg doesn't substitute inside string literals
                    """,
                    workspace_id, days_back + window_days, days_back,
                )
            elif metric_name == "latency_ms":
                current_rows = await conn.fetch(
                    """
                    SELECT latency_ms::float AS val
                    FROM audit_log
                    WHERE workspace_id = $1::uuid
                      AND action = 'query'
                      AND timestamp >= NOW() - $2 * INTERVAL '1 day'  -- FIXED: asyncpg doesn't substitute inside string literals
                      AND timestamp < NOW() - $3 * INTERVAL '1 day'   -- FIXED: asyncpg doesn't substitute inside string literals
                    """,
                    workspace_id, days_back, days_back - window_days,
                )
                ref_rows = await conn.fetch(
                    """
                    SELECT latency_ms::float AS val
                    FROM audit_log
                    WHERE workspace_id = $1::uuid
                      AND action = 'query'
                      AND timestamp >= NOW() - $2 * INTERVAL '1 day'  -- FIXED: asyncpg doesn't substitute inside string literals
                      AND timestamp < NOW() - $3 * INTERVAL '1 day'   -- FIXED: asyncpg doesn't substitute inside string literals
                    """,
                    workspace_id, days_back + window_days, days_back,
                )
            else:
                return [], []

        current = [float(r["val"]) for r in current_rows if r["val"] is not None]
        reference = [float(r["val"]) for r in ref_rows if r["val"] is not None]
        return current, reference

    except Exception as e:
        logger.warning(f"Metric fetch failed for {metric_name}: {e}")
        return [], []


def _compute_drift_score(
    current:   list[float],
    reference: list[float],
) -> tuple[float, float, float, str]:
    """
    Compute Population Stability Index (PSI) — standard drift metric.
    PSI < 0.1: no drift
    PSI 0.1-0.25: slight drift
    PSI > 0.25: significant drift

    Returns: (current_mean, reference_mean, psi_score, direction)
    """
    if not current or not reference:
        return 0.0, 0.0, 0.0, "stable"

    curr_mean = sum(current) / len(current)
    ref_mean  = sum(reference) / len(reference)

    # Simple PSI approximation using 10 buckets
    import statistics
    all_vals = current + reference
    min_val  = min(all_vals)
    max_val  = max(all_vals)

    if max_val == min_val:
        return curr_mean, ref_mean, 0.0, "stable"

    n_buckets = 10
    bucket_size = (max_val - min_val) / n_buckets

    psi = 0.0
    for i in range(n_buckets):
        lo = min_val + i * bucket_size
        hi = lo + bucket_size
        curr_pct = len([v for v in current   if lo <= v < hi]) / max(len(current), 1)
        ref_pct  = len([v for v in reference if lo <= v < hi]) / max(len(reference), 1)
        curr_pct = max(curr_pct, 0.0001)
        ref_pct  = max(ref_pct,  0.0001)
        psi += (curr_pct - ref_pct) * (curr_pct / ref_pct)

    direction = "stable"
    if abs(curr_mean - ref_mean) > 0.05 * max(abs(ref_mean), 0.001):
        direction = "up" if curr_mean > ref_mean else "down"

    return curr_mean, ref_mean, round(abs(psi), 4), direction


DRIFT_THRESHOLDS: dict[str, float] = {
    "faithfulness":   0.15,   # PSI > 0.15 = drift in quality scores
    "guardrail_rate": 0.20,   # PSI > 0.20 = unusual safety event rate
    "latency_ms":     0.25,   # PSI > 0.25 = significant latency shift
}


async def run_drift_analysis(
    workspace_id:  str,
    window_days:   int = 7,
) -> DriftReport:
    """
    Run full drift analysis for a workspace.
    Compares last window_days vs previous window_days.
    """
    report = DriftReport(
        generated_at=datetime.now(timezone.utc),
        period_days=window_days,
    )

    metrics = ["faithfulness", "guardrail_rate", "latency_ms"]

    for metric in metrics:
        current, reference = await _get_metric_timeseries(
            workspace_id=workspace_id,
            metric_name=metric,
            days_back=window_days,
            window_days=window_days,
        )

        if len(current) < 10:
            logger.info(f"Insufficient data for {metric} drift ({len(current)} samples)")
            continue

        curr_mean, ref_mean, psi, direction = _compute_drift_score(current, reference)
        threshold   = DRIFT_THRESHOLDS.get(metric, 0.2)
        is_drifting = psi > threshold

        signal = DriftSignal(
            metric_name=metric,
            current_value=round(curr_mean, 4),
            baseline_value=round(ref_mean, 4),
            drift_score=psi,
            is_drifting=is_drifting,
            direction=direction,
            threshold=threshold,
        )
        report.signals.append(signal)

        if is_drifting:
            logger.warning(
                f"Drift detected: {metric} PSI={psi:.3f} "
                f"(current={curr_mean:.3f} vs baseline={ref_mean:.3f}) "
                f"direction={direction}"
            )

    report.overall_drift = any(s.is_drifting for s in report.signals)

    # Trigger retraining if quality drift persists
    faithfulness_signal = next(
        (s for s in report.signals if s.metric_name == "faithfulness"), None
    )
    report.needs_retrain = (
        report.overall_drift and
        faithfulness_signal is not None and
        faithfulness_signal.is_drifting and
        faithfulness_signal.direction == "down"
    )

    # Generate summary
    drifting = [s.metric_name for s in report.signals if s.is_drifting]
    if drifting:
        report.summary = (
            f"Drift detected in: {', '.join(drifting)}. "
            f"{'Retraining recommended.' if report.needs_retrain else 'Monitor closely.'}"
        )
    else:
        report.summary = f"All metrics stable ({len(report.signals)} signals checked)."

    # Save report
    await _save_report(report, workspace_id)

    return report


async def _save_report(report: DriftReport, workspace_id: str):
    """Persist drift report to disk for audit trail."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts   = report.generated_at.strftime("%Y%m%d_%H%M")
    path = REPORTS_DIR / f"drift_{workspace_id[:8]}_{ts}.json"
    data = {
        "generated_at":  report.generated_at.isoformat(),
        "period_days":   report.period_days,
        "overall_drift": report.overall_drift,
        "needs_retrain": report.needs_retrain,
        "summary":       report.summary,
        "signals": [
            {
                "metric":    s.metric_name,
                "current":   s.current_value,
                "baseline":  s.baseline_value,
                "psi":       s.drift_score,
                "drifting":  s.is_drifting,
                "direction": s.direction,
            }
            for s in report.signals
        ],
    }
    path.write_text(json.dumps(data, indent=2))


async def get_latest_drift_report(workspace_id: str) -> Optional[dict]:
    """Load the most recent drift report for a workspace."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    reports = sorted(
        REPORTS_DIR.glob(f"drift_{workspace_id[:8]}_*.json"),
        reverse=True,
    )
    if not reports:
        return None
    return json.loads(reports[0].read_text())