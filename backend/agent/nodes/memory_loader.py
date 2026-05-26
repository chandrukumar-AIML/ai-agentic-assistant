# backend/agent/nodes/memory_loader.py
"""
LangGraph node: loads memory context before the agent runs.
Injects memory into AgentState so all downstream nodes can use it.
"""
import time
import logging
from backend.agent.state import AgentState
from backend.memory.memory_retriever import build_memory_context

logger = logging.getLogger(__name__)


async def memory_loader(state: AgentState) -> dict:
    """
    Entry memory node.
    Retrieves episodic + semantic + procedural memories
    and stores them in state["memory_context"].
    This is injected into the system prompt in planner/synthesizer.
    """
    start   = time.monotonic()
    user_id = state.get("user_id", "anonymous")

    # Skip memory for anonymous users
    if user_id == "anonymous":
        return {
            "memory_context": "",
            "latency_ms": {"memory_loader": 0.0},
        }

    try:
        memory_context = await build_memory_context(
            query=state["user_query"],
            user_id=user_id,
            session_id=state.get("session_id", ""),
        )
    except Exception as e:
        logger.warning(f"Memory loader failed (non-fatal): {e}")
        memory_context = ""

    elapsed = (time.monotonic() - start) * 1000
    logger.info(
        f"Memory loaded for {user_id}: "
        f"{len(memory_context)} chars in {elapsed:.0f}ms"
    )

    return {
        "memory_context": memory_context,
        "latency_ms":     {"memory_loader": round(elapsed, 2)},
    }