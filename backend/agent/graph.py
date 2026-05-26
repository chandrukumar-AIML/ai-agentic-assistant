# FIXED: Removed duplicate Phase A/B build_graph — Phase C is the canonical version
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from backend.agent.state import AgentState

# Memory nodes (Phase A)
from backend.agent.nodes.memory_loader       import memory_loader
from backend.agent.nodes.memory_updater_node import memory_updater_node

# Core nodes
from backend.agent.nodes.input_parser        import input_parser
from backend.agent.nodes.response_streamer   import response_streamer

# Reflection nodes (Phase B)
from backend.agent.nodes.reflection_node     import reflection_node
from backend.agent.nodes.rewrite_node        import rewrite_node

# Multi-agent nodes (Phase C)
from backend.agent.nodes.supervisor_node     import supervisor_node
from backend.agent.nodes.worker_dispatcher   import worker_dispatcher
from backend.agent.nodes.aggregator_node     import aggregator_node

# Routing
from backend.agent.routing.edges import (
    route_after_reflection,
    route_after_rewrite,
)


def build_graph() -> StateGraph:
    """
    Phase C multi-agent graph:
      memory_loader → input_parser → supervisor → dispatcher →
      aggregator → reflection_node ⟷ rewrite_node →
      memory_updater → response_streamer → END
    """
    graph = StateGraph(AgentState)

    graph.add_node("memory_loader",    memory_loader)
    graph.add_node("input_parser",     input_parser)
    graph.add_node("supervisor",       supervisor_node)
    graph.add_node("dispatcher",       worker_dispatcher)
    graph.add_node("aggregator",       aggregator_node)
    graph.add_node("reflection_node",  reflection_node)
    graph.add_node("rewrite_node",     rewrite_node)
    graph.add_node("memory_updater",   memory_updater_node)
    graph.add_node("response_streamer", response_streamer)

    graph.add_edge(START,               "memory_loader")
    graph.add_edge("memory_loader",     "input_parser")
    graph.add_edge("input_parser",      "supervisor")
    graph.add_edge("supervisor",        "dispatcher")
    graph.add_edge("dispatcher",        "aggregator")
    graph.add_edge("aggregator",        "reflection_node")
    graph.add_edge("memory_updater",    "response_streamer")
    graph.add_edge("response_streamer", END)

    graph.add_conditional_edges(
        "reflection_node",
        route_after_reflection,
        {"memory_updater": "memory_updater", "rewrite_node": "rewrite_node"},
    )
    graph.add_conditional_edges(
        "rewrite_node",
        route_after_rewrite,
        {"reflection_node": "reflection_node"},
    )

    return graph


def compile_graph(checkpointer=None):
    """Compile graph with optional checkpoint backend. Called once at startup."""
    return build_graph().compile(
        checkpointer=checkpointer or MemorySaver()
    )
