# FIXED: Removed duplicate Phase A definitions — Phase B is the canonical version
from langgraph.types import Send
from backend.agent.state import AgentState

MAX_REFLECTION_LOOPS = 3
PASS_THRESHOLD       = 7.0


def route_after_planner(state: AgentState) -> list[Send]:
    """Fan out to tool nodes in parallel using LangGraph Send API."""
    tool_to_node = {
        "rag_tool":         "rag_retriever",
        "web_search_tool":  "web_searcher",
        "code_runner_tool": "code_executor",
        "vision_tool":      "vision_analyzer",
        "graph_tool":       "graph_querier",
    }
    sends = [
        Send(tool_to_node[t], state)
        for t in state["selected_tools"]
        if t in tool_to_node
    ]
    return sends or [Send("rag_retriever", state)]


def route_after_evaluator(state: AgentState) -> str:
    """
    Three routes:
    1. No error → synthesizer
    2. Error + retries left → planner
    3. Retries exhausted → ollama_node (local fallback)
    """
    if state.get("error") is None:
        return "synthesizer"
    if state["retry_count"] < state["max_retries"]:
        return "planner"
    return "ollama_node"


def route_after_reflection(state: AgentState) -> str:
    """
    Core reflection routing:
    - pass  → memory_updater (accept answer)
    - fail + loops left → rewrite_node
    - exhausted → memory_updater (accept best answer)
    """
    verdict  = state.get("reflection_verdict", "pass")
    attempts = state.get("reflection_attempts", 0)

    if verdict == "pass":
        return "memory_updater"

    if attempts >= MAX_REFLECTION_LOOPS:
        return "memory_updater"

    return "rewrite_node"


def route_after_rewrite(state: AgentState) -> str:
    """After rewriting, always go back to reflection for another check."""
    return "reflection_node"
