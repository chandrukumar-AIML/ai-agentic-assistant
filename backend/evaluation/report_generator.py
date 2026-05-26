# backend/evaluation/report_generator.py
"""
Weekly eval report generator.
Detects agent degradation over time.
Can be run as a cron job or triggered manually.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import mlflow

logger = logging.getLogger(__name__)

REPORTS_DIR = Path("data/eval_reports")


def generate_weekly_report(
    current_metrics: dict,
    baseline_metrics: dict,
    agent_breakdown:  dict,
) -> str:
    """
    Generate a human-readable weekly evaluation report.
    Returns markdown string.
    """
    now    = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines  = []
    append = lines.append

    append(f"# Agent Evaluation Report")
    append(f"**Generated:** {now}\n")

    # Overall metrics table
    append("## Overall Metrics\n")
    append("| Metric | Score | Threshold | Status |")
    append("|--------|-------|-----------|--------|")

    checks = [
        ("Task Completion Rate (TCR)",  current_metrics.get("tcr", 0),          0.80),
        ("Tool Call Accuracy",          current_metrics.get("tool_accuracy", 0), 0.70),
        ("Response Faithfulness",       current_metrics.get("faithfulness", 0),  0.60),
        ("Trajectory Efficiency",       current_metrics.get("efficiency", 0),    0.70),
        ("Self-correction Rate",        current_metrics.get("self_correction",0), 0.70),
        ("Composite Score",             current_metrics.get("composite", 0),     0.65),
    ]

    for name, score, threshold in checks:
        status = "✅ PASS" if score >= threshold else "❌ FAIL"
        append(f"| {name} | {score:.1%} | {threshold:.0%} | {status} |")

    append("")

    # Regression analysis
    regressions = []
    for metric, current in current_metrics.items():
        baseline = baseline_metrics.get(metric, 0)
        if baseline > 0:
            delta = current - baseline
            if delta < -0.05:
                regressions.append((metric, baseline, current, delta))

    if regressions:
        append("## ⚠️ Regressions Detected\n")
        for metric, base, curr, delta in regressions:
            append(f"- **{metric}**: {base:.1%} → {curr:.1%} (Δ {delta:+.1%})")
        append("")
    else:
        append("## ✅ No Regressions Detected\n")

    # Per-agent breakdown
    if agent_breakdown:
        append("## Per-Agent Performance\n")
        append("| Agent | Samples | TCR | Composite |")
        append("|-------|---------|-----|-----------|")
        for agent, stats in agent_breakdown.items():
            agent_name = agent.replace("_agent", "").replace("_", " ").title()
            append(
                f"| {agent_name} | {stats['count']} | "
                f"{stats['tcr']:.1%} | {stats['composite']:.1%} |"
            )
        append("")

    # Recommendations
    append("## Recommendations\n")
    current_tcr = current_metrics.get("tcr", 0)
    current_faith = current_metrics.get("faithfulness", 0)

    if current_tcr < 0.80:
        append(f"- 🔴 **TCR below threshold ({current_tcr:.1%})**: "
               f"Review failed samples — likely tool routing or reflection issues")
    if current_faith < 0.60:
        append(f"- 🟡 **Low faithfulness ({current_faith:.1%})**: "
               f"Agent may be hallucinating — check tool result quality")
    if current_metrics.get("efficiency", 0) < 0.70:
        append("- 🟡 **Low efficiency**: Too many reflection loops — "
               "consider raising PASS_THRESHOLD or improving synthesizer prompt")
    if not regressions and current_tcr >= 0.80:
        append("- 🟢 All metrics healthy — no action required")

    return "\n".join(lines)


async def run_weekly_eval_and_report():
    """Scheduled weekly eval + report generation."""
    from backend.evaluation.eval_runner import run_evaluation
    from backend.evaluation.dataset     import load_baseline

    logger.info("Running weekly evaluation...")
    report = await run_evaluation(limit=50)   # 50 samples for weekly check

    baseline = load_baseline()
    report_md = generate_weekly_report(
        current_metrics=report.get("metrics", {}),
        baseline_metrics=baseline,
        agent_breakdown=report.get("breakdown_by_agent", {}),
    )

    # Save report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp  = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")  # FIXED: use timezone-aware datetime
    report_path = REPORTS_DIR / f"eval_report_{timestamp}.md"
    report_path.write_text(report_md)

    logger.info(f"Weekly report saved: {report_path}")
    logger.info(f"Gate: {'PASS' if report['gate']['passed'] else 'FAIL'}")

    return report