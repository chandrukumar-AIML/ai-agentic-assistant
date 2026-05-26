# backend/mlops/report_scheduler.py
"""
Scheduled LLMOps reports and automatic drift alerts.
Run as a background task or cron job.
"""
import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


async def run_weekly_mlops_report(workspace_id: str) -> dict:
    """
    Full weekly LLMOps report:
    1. Drift analysis (Evidently-style)
    2. Cost report
    3. Eval summary
    4. Canary status

    Returns consolidated report dict.
    """
    logger.info(f"Running weekly MLOps report for workspace {workspace_id[:8]}")

    results = {}

    # 1. Drift analysis
    try:
        from backend.mlops.drift_monitor import run_drift_analysis
        drift_report = await run_drift_analysis(workspace_id, window_days=7)
        results["drift"] = {
            "overall_drift":  drift_report.overall_drift,
            "needs_retrain":  drift_report.needs_retrain,
            "summary":        drift_report.summary,
            "signals":        [
                {
                    "metric":     s.metric_name,
                    "psi":        s.drift_score,
                    "drifting":   s.is_drifting,
                    "direction":  s.direction,
                }
                for s in drift_report.signals
            ],
        }
    except Exception as e:
        results["drift"] = {"error": str(e)}

    # 2. Cost report
    try:
        from backend.cost.tracker import get_workspace_cost_report
        cost = await get_workspace_cost_report(workspace_id=workspace_id, days=7)
        results["cost"] = cost
    except Exception as e:
        results["cost"] = {"error": str(e)}

    # 3. Eval summary (last run)
    try:
        from backend.evaluation.dataset import load_baseline
        baseline = load_baseline()
        results["eval_baseline"] = baseline
    except Exception as e:
        results["eval_baseline"] = {"error": str(e)}

    # 4. Canary status
    try:
        from backend.mlops.canary import get_canary_status
        results["canary"] = await get_canary_status()
    except Exception as e:
        results["canary"] = {"error": str(e)}

    # 5. Check if retraining needed
    drift = results.get("drift", {})
    if drift.get("needs_retrain"):
        logger.warning(
            "⚠️ RETRAINING RECOMMENDED: Quality drift detected. "
            "Run data_collector.collect_training_samples() and fine-tune."
        )
        results["action_required"] = "retrain"
    elif drift.get("overall_drift"):
        results["action_required"] = "monitor"
    else:
        results["action_required"] = "none"

    logger.info(
        f"Weekly report complete: "
        f"drift={drift.get('overall_drift', False)} "
        f"action={results.get('action_required', 'none')}"
    )

    return results


async def start_background_scheduler(workspace_id: str):
    """
    Background task: run drift check daily, full report weekly.
    Call from FastAPI lifespan if desired.
    """
    check_count = 0
    while True:
        await asyncio.sleep(86400)   # 24 hours
        check_count += 1

        try:
            from backend.mlops.drift_monitor import run_drift_analysis
            drift_report = await run_drift_analysis(workspace_id)

            if drift_report.needs_retrain:
                logger.warning(
                    f"Daily drift check — retraining recommended: "
                    f"{drift_report.summary}"
                )

            # Full report weekly (every 7 days)
            if check_count % 7 == 0:
                await run_weekly_mlops_report(workspace_id)

        except Exception as e:
            logger.error(f"Scheduler error: {e}")