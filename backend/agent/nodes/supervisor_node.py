# backend/agent/nodes/supervisor_node.py
"""
Supervisor node — decides which workers to dispatch and in what order.
Routes to worker_dispatcher via Send API fan-out.
"""
import logging
from backend.agent.state import AgentState

logger = logging.getLogger(__name__)

WORKER_MAP = {
    "rag":        "rag_tool",
    "web_search": "web_search_tool",
    "code":       "code_runner_tool",
    "graph":      "graph_tool",
    "memory":     "memory_loader",
}


async def supervisor_node(state: AgentState) -> dict:
    """
    Reads the planner's selected_tools and builds the worker dispatch list.
    Each worker entry is: {"worker_name": str, "task": str, "priority": int}
    """
    selected = state.get("selected_tools", [])
    plan     = state.get("plan", [])
    intent   = state.get("intent", "general")

    workers = []
    for i, tool in enumerate(selected):
        worker_name = WORKER_MAP.get(tool, tool)
        task = plan[i] if i < len(plan) else f"Execute {tool} for: {state.get('user_query', '')}"
        workers.append({
            "worker_name": worker_name,
            "task":        task,
            "priority":    i,
        })

    logger.info(f"Supervisor dispatching {len(workers)} workers for intent={intent}")

    return {
        "supervisor_workers":    workers,
        "supervisor_parallel":   len(workers) > 1,
        "supervisor_aggregation": "merge",
        "supervisor_decision":   f"Dispatching {len(workers)} workers: {[w['worker_name'] for w in workers]}",
    }
