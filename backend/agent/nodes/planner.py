import time
import json
import logging
from backend.agent.state import AgentState  # FIXED: wrong import path
from backend.agent.prompts import PLANNER_PROMPT  # FIXED: wrong import path
from backend.llm.router import llm_router  # FIXED: wrong import path
from backend.utils.text import strip_code_fence  # FIXED: wrong import path

logger = logging.getLogger(__name__)

TOOL_REGISTRY = {
    "rag":        ["rag_tool"],
    "web_search": ["web_search_tool"],
    "code":       ["code_runner_tool"],
    "vision":     ["vision_tool"],
    "graph":      ["graph_tool"],
    "hybrid":     ["rag_tool", "web_search_tool"],
}


async def planner(state: AgentState) -> dict:
    start = time.monotonic()

    messages = [
        {
            "role":    "system",
            "content": "You are a task planner. Respond only with valid JSON.",
        },
        {
            "role": "user",
            "content": PLANNER_PROMPT.format(
                query=state["user_query"],
                intent=state["intent"],
                retry_count=state["retry_count"],
                error=state.get("error") or "none",
            ),
        },
    ]

    response, model_used = await llm_router.complete(
        messages=messages,
        temperature=0,
        max_tokens=300,
    )

    try:
        clean = strip_code_fence(response if isinstance(response, str) else "")
        parsed = json.loads(clean)
        plan = parsed.get("plan", [state["user_query"]])
        selected_tools = parsed.get(
            "selected_tools",
            TOOL_REGISTRY.get(state["intent"], ["rag_tool"])
        )
    except (json.JSONDecodeError, KeyError, AttributeError) as e:  # FIXED: was silently swallowing parse errors without logging
        logger.warning(f"Planner JSON parse failed, using defaults: {e}")
        plan = [state["user_query"]]
        selected_tools = TOOL_REGISTRY.get(state["intent"], ["rag_tool"])

    elapsed = (time.monotonic() - start) * 1000

    return {
        "plan":           plan,
        "selected_tools": selected_tools,
        "latency_ms":     {"planner": round(elapsed, 2)},
        "model_used":     model_used,
    }