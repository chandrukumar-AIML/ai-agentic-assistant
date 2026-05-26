# backend/agent/nodes/worker_dispatcher.py
"""
Dispatches tasks to worker agents based on supervisor routing.
Handles both parallel (asyncio.gather) and sequential execution.
"""
import asyncio
import time
import logging
from typing import Any

from backend.agent.state         import AgentState
from backend.agent.research_agent import ResearchAgent
from backend.agent.code_agent     import CodeAgent
from backend.agent.vision_agent   import VisionAgent
from backend.agent.memory_agent   import MemoryAgent
from backend.agent.planning_agent import PlanningAgent
from backend.agent.base_agent     import WorkerResult

logger = logging.getLogger(__name__)

# Registry — instantiate once at module level
WORKER_REGISTRY: dict[str, Any] = {
    "research_agent": ResearchAgent(),
    "code_agent":     CodeAgent(),
    "vision_agent":   VisionAgent(),
    "memory_agent":   MemoryAgent(),
    "planning_agent": PlanningAgent(),
}


async def _run_worker(
    worker_name:    str,
    sub_query:      str,
    state:          AgentState,
) -> WorkerResult:
    """Run a single worker agent and return its result."""
    worker = WORKER_REGISTRY.get(worker_name)
    if not worker:
        return WorkerResult(
            worker_name=worker_name,
            content=f"Unknown worker: {worker_name}",
            confidence=0.0,
            error="not_found",
        )

    context = {
        "user_id":    state.get("user_id", "anonymous"),
        "session_id": state.get("session_id", ""),
        "image_data": state.get("image_data"),
        "intent":     state.get("intent", ""),
    }

    try:
        result = await worker.run(
            query=sub_query,
            context=context,
            memory_context=state.get("memory_context", ""),
        )
        return result
    except Exception as e:
        logger.error(f"Worker {worker_name} failed: {e}", exc_info=True)
        return WorkerResult(
            worker_name=worker_name,
            content=f"Worker {worker_name} encountered an error: {str(e)}",
            confidence=0.0,
            error=str(e),
        )


async def worker_dispatcher(state: AgentState) -> dict:
    """
    Dispatches tasks to workers based on supervisor routing.
    Returns worker_results list for the aggregator node.
    """
    start   = time.monotonic()
    workers = state.get("supervisor_workers", [])
    parallel = state.get("supervisor_parallel", True)

    if not workers:
        logger.warning("No workers dispatched — defaulting to research_agent")
        workers = [{"worker": "research_agent", "sub_query": state["user_query"], "priority": 1}]

    # Sort by priority
    workers_sorted = sorted(workers, key=lambda w: w.get("priority", 99))

    worker_results: list[dict] = []

    if parallel:
        # All workers run concurrently
        logger.info(f"Dispatching {len(workers_sorted)} workers in parallel")
        tasks   = [
            _run_worker(w["worker"], w.get("sub_query", state["user_query"]), state)
            for w in workers_sorted
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for res in results:
            if isinstance(res, WorkerResult):
                worker_results.append({
                    "worker_name": res.worker_name,
                    "content":     res.content,
                    "sources":     res.sources,
                    "confidence":  res.confidence,
                    "metadata":    res.metadata,
                    "latency_ms":  res.latency_ms,
                    "error":       res.error,
                })
    else:
        # Sequential — each worker's output added to context
        logger.info(f"Dispatching {len(workers_sorted)} workers sequentially")
        accumulated_context = ""
        for w in workers_sorted:
            sub_query = w.get("sub_query", state["user_query"])
            if accumulated_context:
                sub_query += f"\n\nPrevious results:\n{accumulated_context[:500]}"

            res = await _run_worker(w["worker"], sub_query, state)
            worker_results.append({
                "worker_name": res.worker_name,
                "content":     res.content,
                "sources":     res.sources,
                "confidence":  res.confidence,
                "metadata":    res.metadata,
                "latency_ms":  res.latency_ms,
                "error":       res.error,
            })
            accumulated_context += f"\n{res.worker_name}: {res.content[:300]}"

    elapsed = (time.monotonic() - start) * 1000
    logger.info(f"Dispatcher: {len(worker_results)} workers completed in {elapsed:.0f}ms")

    return {
        "worker_results": worker_results,
        "latency_ms":     {"dispatcher": round(elapsed, 2)},
    }