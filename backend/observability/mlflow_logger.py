"""
MLflow LLMOps logger.
All public functions are safe to call outside an active run context.
"""
import logging
import time
import json
import tempfile
import os
from contextlib import contextmanager
from typing import Any

import mlflow
from backend.config import get_settings  # FIXED: use package-relative import

logger   = logging.getLogger(__name__)
settings = get_settings()

EXP_AGENT_RUNS = "agent_runs"
EXP_RAG        = "rag_experiments"
EXP_PROMPT_AB  = "prompt_ab_tests"
EXP_COST       = "cost_tracking"

# Pricing map — update when OpenAI changes pricing
_COST_PER_1K = {
    "gpt-4o":                 {"input": 0.005,   "output": 0.015},
    "text-embedding-3-small": {"input": 0.00002,  "output": 0.0},
    "ollama/llama3":          {"input": 0.0,      "output": 0.0},
}


def configure_mlflow():
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    for exp_name in [EXP_AGENT_RUNS, EXP_RAG, EXP_PROMPT_AB, EXP_COST]:
        try:
            mlflow.set_experiment(exp_name)
        except Exception as e:
            logger.warning(f"MLflow experiment setup failed for '{exp_name}': {e}")
    logger.info(f"MLflow configured → tracking URI: {settings.mlflow_tracking_uri}")


@contextmanager
def mlflow_run(experiment_name: str, run_name: str, tags: dict | None = None):
    mlflow.set_experiment(experiment_name)
    run = mlflow.start_run(run_name=run_name, tags=tags or {})
    try:
        yield run
        mlflow.set_tag("status", "completed")
    except Exception as e:
        mlflow.set_tag("status", "failed")
        mlflow.set_tag("error", str(e)[:200])
        raise
    finally:
        mlflow.end_run()


def log_agent_run(
    session_id:    str,
    query:         str,
    intent:        str,
    selected_tools: list[str],
    model_used:    str,
    latency_ms:    dict[str, float],
    final_answer:  str,
    sources:       list[str],
    retry_count:   int,
    error:         str | None = None,
):
    try:
        mlflow.set_experiment(EXP_AGENT_RUNS)
        with mlflow.start_run(
            run_name=f"run_{session_id[:8]}",
            tags={"intent": intent, "model": model_used, "has_error": str(error is not None)},
        ):
            mlflow.log_param("session_id",     session_id)
            mlflow.log_param("intent",         intent)
            mlflow.log_param("selected_tools", ",".join(selected_tools))
            mlflow.log_param("model_used",     model_used)
            mlflow.log_param("retry_count",    retry_count)

            total_latency = sum(latency_ms.values())
            mlflow.log_metric("total_latency_ms", round(total_latency, 2))
            mlflow.log_metric("retry_count",      retry_count)
            mlflow.log_metric("source_count",     len(sources))

            for node_name, ms in latency_ms.items():
                mlflow.log_metric(f"latency_{node_name}_ms", round(ms, 2))

            run_data = {
                "query": query, "final_answer": final_answer[:500],
                "sources": sources, "error": error,
            }
            # Tempfile with finally cleanup to prevent leaks on exception
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                    json.dump(run_data, f, indent=2)
                    tmp_path = f.name
                mlflow.log_artifact(tmp_path, artifact_path="run_data")
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)

    except Exception as e:
        logger.warning(f"MLflow agent run logging failed (non-fatal): {e}")


def log_llm_cost(
    model:         str,
    prompt_tokens: int,
    output_tokens: int,
    run_id:        str | None = None,
):
    """
    Log token usage and estimated cost.
    If inside an active run, logs to it directly. Otherwise creates a standalone run.
    """
    try:
        costs = _COST_PER_1K.get(model, {"input": 0.005, "output": 0.015})
        cost_usd = (
            (prompt_tokens / 1000) * costs["input"] +
            (output_tokens / 1000) * costs["output"]
        )
        metrics = {
            "prompt_tokens": prompt_tokens,
            "output_tokens": output_tokens,
            "total_tokens":  prompt_tokens + output_tokens,
            "cost_usd":      round(cost_usd, 6),
        }

        # If already inside an active run, log directly without changing experiment
        if mlflow.active_run():
            mlflow.log_metrics(metrics)
        else:
            mlflow.set_experiment(EXP_COST)
            with mlflow.start_run(run_name=f"cost_{model}"):
                mlflow.log_metrics(metrics)
                mlflow.log_param("model", model)

    except Exception as e:
        logger.warning(f"MLflow cost logging failed (non-fatal): {e}")


def log_rag_retrieval(
    query: str, strategy: str,
    faiss_hits: int, chroma_hits: int,
    candidates: int, returned: int,
    latency_ms: float, top_score: float, avg_score: float,
):
    try:
        mlflow.set_experiment(EXP_RAG)
        with mlflow.start_run(run_name=f"rag_{strategy}"):
            mlflow.log_param("strategy",      strategy)
            mlflow.log_param("query_preview", query[:100])
            mlflow.log_metric("faiss_hits",  faiss_hits)
            mlflow.log_metric("chroma_hits", chroma_hits)
            mlflow.log_metric("candidates",  candidates)
            mlflow.log_metric("returned",    returned)
            mlflow.log_metric("latency_ms",  round(latency_ms, 2))
            mlflow.log_metric("top_score",   round(top_score, 4))
            mlflow.log_metric("avg_score",   round(avg_score, 4))
    except Exception as e:
        logger.warning(f"MLflow RAG logging failed (non-fatal): {e}")


def log_prompt_version(
    prompt_name: str,
    prompt_text: str,
    version:     str,
    metrics:     dict[str, float] | None = None,
):
    try:
        mlflow.set_experiment(EXP_PROMPT_AB)
        with mlflow.start_run(run_name=f"{prompt_name}_{version}"):
            mlflow.log_param("prompt_name", prompt_name)
            mlflow.log_param("version",     version)
            mlflow.log_param("char_count",  len(prompt_text))
            for k, v in (metrics or {}).items():
                mlflow.log_metric(k, v)

            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                    f.write(prompt_text)
                    tmp_path = f.name
                mlflow.log_artifact(tmp_path, artifact_path="prompts")
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)

            mlflow.set_tag("prompt_name", prompt_name)
            mlflow.set_tag("version",     version)
        logger.info(f"Prompt version logged: {prompt_name} {version}")
    except Exception as e:
        logger.warning(f"MLflow prompt logging failed (non-fatal): {e}")


def get_best_run(
    experiment_name: str,
    metric:          str,
    higher_is_better: bool = True,
) -> dict | None:
    try:
        client     = mlflow.tracking.MlflowClient()
        experiment = client.get_experiment_by_name(experiment_name)
        if not experiment:
            return None
        order = "DESC" if higher_is_better else "ASC"
        runs  = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=[f"metrics.{metric} {order}"],
            max_results=1,
        )
        if not runs:
            return None
        best = runs[0]
        return {
            "run_id":  best.info.run_id,
            "metrics": dict(best.data.metrics),
            "params":  dict(best.data.params),
            "tags":    dict(best.data.tags),
        }
    except Exception as e:
        logger.warning(f"MLflow best run query failed: {e}")
        return None


def compare_runs(
    experiment_name: str,
    metric:          str,
    n_runs:          int = 5,
) -> list[dict]:
    try:
        client     = mlflow.tracking.MlflowClient()
        experiment = client.get_experiment_by_name(experiment_name)
        if not experiment:
            return []
        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=[f"metrics.{metric} DESC"],
            max_results=n_runs,
        )
        return [
            {"run_id": r.info.run_id, "run_name": r.info.run_name,
             "metrics": dict(r.data.metrics), "params": dict(r.data.params)}
            for r in runs
        ]
    except Exception as e:
        logger.warning(f"MLflow compare_runs failed: {e}")
        return []  
    
# Add this function to backend/observability/mlflow_logger.py

def log_reflection_run(
    session_id:   str,
    query:        str,
    attempts:     int,
    final_score:  float,
    history:      list[dict],
):
    """
    Log reflection loop metrics to MLflow.
    Tracks: how many loops needed, score improvement per loop.
    """
    try:
        mlflow.set_experiment(EXP_AGENT_RUNS)
        with mlflow.start_run(run_name=f"reflection_{session_id[:8]}"):
            mlflow.log_param("query_preview",   query[:100])
            mlflow.log_param("session_id",      session_id)
            mlflow.log_metric("reflection_loops",      attempts)
            mlflow.log_metric("final_reflection_score", final_score)

            # Log score progression
            for i, entry in enumerate(history):
                mlflow.log_metric(
                    f"score_loop_{i+1}",
                    entry.get("score", 0),
                    step=i,
                )

            # Did it need rewriting?
            needed_rewrite = attempts > 1
            mlflow.log_metric("needed_rewrite", int(needed_rewrite))

    except Exception as e:
        logger.warning(f"MLflow reflection logging failed: {e}")