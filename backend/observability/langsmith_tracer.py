"""
LangSmith tracing utilities.

Automatic tracing: set env vars — LangGraph traces all nodes automatically.
Manual tracing:    use @traceable from langsmith.run_helpers for custom spans.
Feedback:          call submit_feedback() from the WebSocket handler.
"""
import logging
import time
from typing import Any

from langsmith import Client
from langsmith.run_helpers import traceable
from backend.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()

_ls_client: Client | None = None


def get_ls_client() -> Client:
    global _ls_client
    if _ls_client is None:
        _ls_client = Client(api_key=settings.langchain_api_key)
    return _ls_client


def configure_tracing():
    """Enable LangSmith tracing. Called once at app startup."""
    import os
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"]    = settings.langchain_api_key
    os.environ["LANGCHAIN_PROJECT"]    = settings.langchain_project
    logger.info(f"LangSmith tracing enabled → project: {settings.langchain_project}")


async def submit_feedback(
    run_id:  str,
    score:   float,
    comment: str = "",
    key:     str = "user_feedback",
) -> bool:
    try:
        client = get_ls_client()
        client.create_feedback(
            run_id=run_id,
            key=key,
            score=score,
            comment=comment,
        )
        logger.info(f"Feedback submitted: run={run_id}, score={score}")
        return True
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}")
        return False


async def create_eval_dataset(
    name:        str,
    description: str,
    examples:    list[dict],
) -> str | None:
    try:
        client  = get_ls_client()
        dataset = client.create_dataset(dataset_name=name, description=description)
        client.create_examples(
            inputs=[e["input"] for e in examples],
            outputs=[e["output"] for e in examples],
            dataset_id=dataset.id,
        )
        logger.info(f"Dataset '{name}' created: {len(examples)} examples")
        return str(dataset.id)
    except Exception as e:
        logger.error(f"Failed to create dataset: {e}")
        return None


async def run_evaluation(
    dataset_name: str,
    graph=None,   # Accept compiled graph as parameter — never import at module level
    evaluators: list[str] | None = None,
) -> dict | None:
    """
    Run the compiled agent against a LangSmith dataset.
    Pass the compiled graph explicitly to avoid module-level import issues.
    """
    if graph is None:
        logger.error("run_evaluation requires a compiled graph — pass app.state.agent")
        return None

    try:
        from langsmith.evaluation import evaluate
        from langchain_core.messages import HumanMessage

        async def agent_runner(inputs: dict) -> dict:
            state = {
                "messages":       [HumanMessage(content=inputs["query"])],
                "user_query":     inputs["query"],
                "image_data":     inputs.get("image_data"),
                "session_id":     "eval-session",
                "intent":         "",
                "plan":           [],
                "selected_tools": [],
                "tool_results":   [],
                "retry_count":    0,
                "max_retries":    3,
                "final_answer":   None,
                "sources":        [],
                "trace_id":       "",
                "latency_ms":     {},
                "model_used":     "gpt-4o",
                "error":          None,
            }
            result = await graph.ainvoke(state)
            return {"answer": result.get("final_answer", "")}

        results = evaluate(
            agent_runner,
            data=dataset_name,
            evaluators=evaluators or ["qa"],
            experiment_prefix="agent_eval",
        )
        return {"experiment_url": results.experiment_name}

    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        return None


async def get_project_stats(days: int = 7) -> dict:
    try:
        client = get_ls_client()
        from datetime import datetime, timedelta, timezone
        start_time = datetime.now(timezone.utc) - timedelta(days=days)

        runs = list(client.list_runs(
            project_name=settings.langchain_project,
            start_time=start_time,
            run_type="chain",
            limit=1000,
        ))

        if not runs:
            return {"total_runs": 0}

        total    = len(runs)
        errors   = sum(1 for r in runs if r.error)
        latencies = [
            r.end_time.timestamp() - r.start_time.timestamp()
            for r in runs if r.end_time and r.start_time
        ]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0

        return {
            "total_runs":    total,
            "error_count":   errors,
            "error_rate":    round(errors / total, 3),
            "avg_latency_s": round(avg_latency, 2),
            "p95_latency_s": round(
                sorted(latencies)[int(len(latencies) * 0.95)]
                if latencies else 0, 2
            ),
            "period_days": days,
        }
    except Exception as e:
        logger.error(f"Failed to fetch project stats: {e}")
        return {"error": str(e)}