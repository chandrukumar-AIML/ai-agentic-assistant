# backend/evaluation/eval_runner.py
"""
Runs the full agent against the eval dataset.
Collects metrics, detects regressions, logs to MLflow + LangSmith.
"""
import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Optional

import mlflow

from backend.evaluation.dataset    import load_eval_dataset, save_baseline, load_baseline, EvalSample
from backend.evaluation.metrics    import (
    EvalMetrics,
    compute_tcr,
    compute_tool_accuracy,
    compute_faithfulness,
    compute_trajectory_efficiency,
    compute_self_correction_rate,
    compute_composite_score,
)
from backend.agent.graph     import compile_graph
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)

TCR_GATE_THRESHOLD      = 0.80   # block deploy if TCR < 80%
COMPOSITE_GATE_THRESHOLD = 0.65  # block if composite < 65%
REGRESSION_THRESHOLD    = 0.05   # flag if any metric drops > 5% from baseline

# FIXED: Made model configurable instead of hardcoded
DEFAULT_EVAL_MODEL = "gpt-4o"
EVAL_MODELS_SUPPORTED = ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo", "ollama/llama3"]


async def _run_single_sample(
    sample: EvalSample,
    graph,
    model: str = DEFAULT_EVAL_MODEL,  # FIXED: Model now configurable
) -> EvalMetrics:
    """
    Run one eval sample through the agent and compute all metrics.
    
    Args:
        sample: The evaluation sample to run
        graph: The compiled agent graph
        model: Model to use for evaluation (default: gpt-4o)
    """
    metrics = EvalMetrics(
        query_id=sample.id,
        query=sample.query,
        agent_type=sample.agent_type,
        difficulty=sample.difficulty,
    )

    initial_state = {
        "messages":           [HumanMessage(content=sample.query)],
        "user_query":         sample.query,
        "image_data":         None,
        "session_id":         f"eval_{sample.id}",
        "user_id":            "eval_runner",
        "memory_context":     "",
        "intent":             "",
        "plan":               [],
        "selected_tools":     [],
        "tool_results":       [],
        "retry_count":        0,
        "max_retries":        3,
        "final_answer":       None,
        "sources":            [],
        "trace_id":           f"eval_{sample.id}_{int(time.time())}",
        "latency_ms":         {},
        "model_used":         model,  # FIXED: Use configurable model
        "error":              None,
        "reflection_score":   0.0,
        "reflection_verdict": "fail",
        "reflection_critique":"",
        "reflection_missing": [],
        "reflection_attempts":0,
        "reflection_history": [],
        "supervisor_workers":    [],
        "supervisor_parallel":   True,
        "supervisor_aggregation":"merge",
        "supervisor_decision":   "",
        "worker_results":        [],
    }

    start = time.monotonic()
    try:
        final_state = await graph.ainvoke(initial_state)
        elapsed_ms  = (time.monotonic() - start) * 1000

        response        = final_state.get("final_answer") or ""
        workers_used    = [
            w.get("worker_name", "")
            for w in final_state.get("worker_results", [])
        ]
        reflection_att  = final_state.get("reflection_attempts", 0)
        reflection_score = final_state.get("reflection_score", 0.0)
        retry_count     = final_state.get("retry_count", 0)

        # Compute all metrics
        task_completed = await compute_tcr(
            query=sample.query,
            response=response,
            expected_topics=sample.expected_topics,
        )
        tool_accuracy  = compute_tool_accuracy(
            expected_tools=sample.expected_tools,
            actual_tools=workers_used,
        )
        faithfulness   = await compute_faithfulness(  # FIXED: compute_faithfulness is async
            response=response,
            expected_topics=sample.expected_topics,
        )
        efficiency     = compute_trajectory_efficiency(
            reflection_attempts=reflection_att,
            retry_count=retry_count,
        )
        self_correction = compute_self_correction_rate(
            reflection_attempts=reflection_att,
            reflection_score=reflection_score,
        )

        metrics.task_completed        = task_completed
        metrics.tool_accuracy         = tool_accuracy
        metrics.faithfulness          = faithfulness
        metrics.trajectory_efficiency = efficiency
        metrics.self_correction_rate  = self_correction
        metrics.response              = response
        metrics.workers_used          = workers_used
        metrics.reflection_attempts   = reflection_att
        metrics.reflection_score      = reflection_score
        metrics.retry_count           = retry_count
        metrics.latency_ms            = elapsed_ms
        metrics.composite_score       = compute_composite_score(metrics)

        logger.info(
            f"  [{sample.id}] TCR={task_completed} "
            f"faith={faithfulness:.2f} "
            f"composite={metrics.composite_score:.2f} "
            f"({elapsed_ms:.0f}ms)"
        )

    except Exception as e:
        logger.error(f"Eval sample {sample.id} failed: {e}", exc_info=True)
        metrics.error          = str(e)
        metrics.task_completed = False
        metrics.composite_score = 0.0

    return metrics


async def run_evaluation(
    agent_type:    Optional[str] = None,
    difficulty:    Optional[str] = None,
    limit:         Optional[int] = None,
    save_as_baseline: bool       = False,
    experiment_name:  str        = "agent_evaluation",
    model:            str        = DEFAULT_EVAL_MODEL,  # FIXED: Added model parameter
) -> dict:
    """
    Run full evaluation suite.
    Returns comprehensive report dict.

    Args:
        agent_type:       Filter to specific agent type (or None for all)
        difficulty:       Filter to specific difficulty (or None for all)
        limit:            Max samples to run (None = full dataset)
        save_as_baseline: If True, save results as new regression baseline
        experiment_name:  MLflow experiment to log to
        model:            Model to use for evaluation (validates against EVAL_MODELS_SUPPORTED)
    """
    # FIXED: Validate model selection
    if model not in EVAL_MODELS_SUPPORTED:
        logger.warning(f"Model '{model}' not in supported list. Using default: {DEFAULT_EVAL_MODEL}")
        model = DEFAULT_EVAL_MODEL
    
    logger.info("=" * 60)
    logger.info(f"Starting Agent Evaluation Suite (model: {model})")
    logger.info("=" * 60)

    samples = load_eval_dataset(
        agent_type=agent_type,
        difficulty=difficulty,
        limit=limit,
    )

    if not samples:
        return {"error": "No eval samples found", "passed": False}

    # Compile agent graph
    graph = compile_graph()

    # Run all samples with concurrency limit (avoid rate limits)
    # FIXED: Increased from 3 to 10 for better batch processing
    semaphore = asyncio.Semaphore(10)   # max 10 concurrent evals

    async def run_with_semaphore(sample: EvalSample) -> EvalMetrics:
        async with semaphore:
            return await _run_single_sample(sample, graph, model=model)  # FIXED: Pass model

    start       = time.monotonic()
    all_metrics = await asyncio.gather(
        *[run_with_semaphore(s) for s in samples],
        return_exceptions=False,
    )
    total_elapsed = (time.monotonic() - start) * 1000

    # ── Aggregate results ──────────────────────────────────────────────────
    completed     = [m for m in all_metrics if not m.error]
    failed_evals  = [m for m in all_metrics if m.error]

    if not completed:
        return {"error": "All eval samples failed", "passed": False}

    tcr           = sum(1 for m in completed if m.task_completed) / len(completed)
    avg_tool_acc  = sum(m.tool_accuracy         for m in completed) / len(completed)
    avg_faithful  = sum(m.faithfulness          for m in completed) / len(completed)
    avg_efficiency= sum(m.trajectory_efficiency for m in completed) / len(completed)
    avg_selfcorr  = sum(m.self_correction_rate  for m in completed) / len(completed)
    avg_composite = sum(m.composite_score       for m in completed) / len(completed)
    avg_latency   = sum(m.latency_ms            for m in completed) / len(completed)

    # Per-difficulty breakdown
    difficulty_breakdown = {}
    for diff in ["easy", "medium", "hard"]:
        diff_samples = [m for m in completed if m.difficulty == diff]
        if diff_samples:
            difficulty_breakdown[diff] = {
                "count":     len(diff_samples),
                "tcr":       sum(1 for m in diff_samples if m.task_completed) / len(diff_samples),
                "composite": sum(m.composite_score for m in diff_samples) / len(diff_samples),
            }

    # Per-agent-type breakdown
    agent_breakdown = {}
    for agent in ["research_agent", "code_agent", "multi", "memory_agent"]:
        agent_samples = [m for m in completed if m.agent_type == agent]
        if agent_samples:
            agent_breakdown[agent] = {
                "count":     len(agent_samples),
                "tcr":       sum(1 for m in agent_samples if m.task_completed) / len(agent_samples),
                "composite": sum(m.composite_score for m in agent_samples) / len(agent_samples),
            }

    # ── Regression detection ───────────────────────────────────────────────
    baseline     = load_baseline()
    regressions  = []
    improvements = []

    if baseline:
        checks = [
            ("tcr",           tcr,           baseline.get("tcr", 0)),
            ("faithfulness",  avg_faithful,  baseline.get("faithfulness", 0)),
            ("tool_accuracy", avg_tool_acc,  baseline.get("tool_accuracy", 0)),
            ("composite",     avg_composite, baseline.get("composite", 0)),
        ]
        for name, current, base in checks:
            delta = current - base
            if delta < -REGRESSION_THRESHOLD:
                regressions.append({
                    "metric":    name,
                    "baseline":  round(base, 4),
                    "current":   round(current, 4),
                    "delta":     round(delta, 4),
                })
            elif delta > REGRESSION_THRESHOLD:
                improvements.append({
                    "metric":    name,
                    "baseline":  round(base, 4),
                    "current":   round(current, 4),
                    "delta":     round(delta, 4),
                })

    # ── CI gate decision ───────────────────────────────────────────────────
    gate_passed = (
        tcr           >= TCR_GATE_THRESHOLD and
        avg_composite >= COMPOSITE_GATE_THRESHOLD and
        len(regressions) == 0
    )

    # ── Build report ───────────────────────────────────────────────────────
    report = {
        "timestamp":       datetime.now(timezone.utc).isoformat(),
        "total_samples":   len(samples),
        "completed":       len(completed),
        "failed":          len(failed_evals),
        "total_elapsed_ms":round(total_elapsed, 0),
        "avg_latency_ms":  round(avg_latency, 0),

        "metrics": {
            "tcr":                round(tcr,            4),
            "tool_accuracy":      round(avg_tool_acc,   4),
            "faithfulness":       round(avg_faithful,   4),
            "efficiency":         round(avg_efficiency, 4),
            "self_correction":    round(avg_selfcorr,   4),
            "composite":          round(avg_composite,  4),
        },

        "gate": {
            "passed":            gate_passed,
            "tcr_threshold":     TCR_GATE_THRESHOLD,
            "composite_threshold": COMPOSITE_GATE_THRESHOLD,
            "regressions_found": len(regressions),
        },

        "regressions":  regressions,
        "improvements": improvements,

        "breakdown_by_difficulty": difficulty_breakdown,
        "breakdown_by_agent":      agent_breakdown,

        "failed_samples": [
            {"id": m.query_id, "error": m.error}
            for m in failed_evals
        ],

        "worst_samples": sorted(
            [
                {
                    "id":        m.query_id,
                    "composite": m.composite_score,
                    "tcr":       m.task_completed,
                    "query":     m.query[:80],
                }
                for m in completed
            ],
            key=lambda x: x["composite"],
        )[:5],
    }

    # ── Log to MLflow ──────────────────────────────────────────────────────
    try:
        mlflow.set_experiment(experiment_name)
        with mlflow.start_run(
            run_name=f"eval_{datetime.now().strftime('%Y%m%d_%H%M')}",
            tags={
                "agent_type":  agent_type or "all",
                "gate_passed": str(gate_passed),
            },
        ):
            mlflow.log_metrics({
                "tcr":             tcr,
                "tool_accuracy":   avg_tool_acc,
                "faithfulness":    avg_faithful,
                "efficiency":      avg_efficiency,
                "self_correction": avg_selfcorr,
                "composite":       avg_composite,
                "avg_latency_ms":  avg_latency,
                "regression_count":len(regressions),
            })
            mlflow.log_param("total_samples",     len(samples))
            mlflow.log_param("gate_passed",       gate_passed)
            mlflow.log_param("tcr_threshold",     TCR_GATE_THRESHOLD)

            # Log full report as artifact
            import tempfile, os
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(report, f, indent=2)
                tmp = f.name
            try:
                mlflow.log_artifact(tmp, "eval_report")
            finally:
                os.unlink(tmp)

    except Exception as e:
        logger.warning(f"MLflow eval logging failed: {e}")

    # ── Save baseline if requested ────────────────────────────────────────
    if save_as_baseline:
        save_baseline(report["metrics"])
        logger.info("Scores saved as new baseline")

    # ── Log to LangSmith ──────────────────────────────────────────────────
    try:
        from backend.observability.langsmith_tracer import get_ls_client
        client = get_ls_client()
        client.create_feedback(
            run_id=None,
            key="eval_composite",
            score=avg_composite,
            comment=f"Full eval: TCR={tcr:.2%}, composite={avg_composite:.2%}, gate={'PASS' if gate_passed else 'FAIL'}",
        )
    except Exception:
        pass

    logger.info("=" * 60)
    logger.info(f"Eval complete: TCR={tcr:.1%} composite={avg_composite:.2%} gate={'PASS ✅' if gate_passed else 'FAIL ❌'}")
    logger.info("=" * 60)

    return report