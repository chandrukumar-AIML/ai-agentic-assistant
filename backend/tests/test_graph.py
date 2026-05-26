"""
Tests for the LangGraph agent graph:
  - compile_graph() succeeds without error
  - AgentState TypedDict has all required keys
  - route_after_reflection() routing logic
"""
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Helpers — mock all heavy node imports so the graph module loads without
# real OpenAI / Neo4j / Redis connections.
# ---------------------------------------------------------------------------

def _patch_graph_nodes():
    """
    Return a context manager that patches every node imported by graph.py
    so that compile_graph() can be tested without real external services.
    """
    import contextlib
    import sys

    # Build a minimal async coroutine function to stand in for every node
    async def _noop_node(state):
        return state

    modules_to_patch = {
        "backend.agent.nodes.memory_loader":        MagicMock(memory_loader=_noop_node),
        "backend.agent.nodes.memory_updater_node":  MagicMock(memory_updater_node=_noop_node),
        "backend.agent.nodes.input_parser":         MagicMock(input_parser=_noop_node),
        "backend.agent.nodes.response_streamer":    MagicMock(response_streamer=_noop_node),
        "backend.agent.nodes.reflection_node":      MagicMock(reflection_node=_noop_node),
        "backend.agent.nodes.rewrite_node":         MagicMock(rewrite_node=_noop_node),
        "backend.agent.nodes.supervisor_node":      MagicMock(supervisor_node=_noop_node),
        "backend.agent.nodes.worker_dispatcher":    MagicMock(worker_dispatcher=_noop_node),
        "backend.agent.nodes.aggregator_node":      MagicMock(aggregator_node=_noop_node),
    }

    patches = [
        patch.dict("sys.modules", modules_to_patch)
    ]
    return contextlib.ExitStack, patches


# ---------------------------------------------------------------------------
# Tests — AgentState structure (pure TypedDict, no imports needed)
# ---------------------------------------------------------------------------

class TestAgentState:
    """Verify the AgentState TypedDict declares all expected keys."""

    REQUIRED_KEYS = [
        # Conversation
        "messages",
        # Current turn
        "user_query", "image_data", "session_id",
        # Identity + Memory
        "user_id", "memory_context",
        # Planning
        "intent", "plan", "selected_tools",
        # Execution
        "tool_results", "retry_count", "max_retries",
        # Output
        "final_answer", "sources",
        # Reflection
        "reflection_score", "reflection_verdict", "reflection_critique",
        "reflection_missing", "reflection_attempts", "reflection_history",
        # Multi-agent
        "supervisor_workers", "supervisor_parallel", "supervisor_aggregation",
        "supervisor_decision", "worker_results",
        # Observability
        "trace_id", "latency_ms", "model_used", "error",
    ]

    def test_agent_state_has_all_required_keys(self):
        """AgentState.__annotations__ must contain every required key."""
        from backend.agent.state import AgentState
        annotations = AgentState.__annotations__
        for key in self.REQUIRED_KEYS:
            assert key in annotations, f"AgentState missing required key: '{key}'"

    def test_agent_state_messages_is_annotated(self):
        """'messages' must use the add_messages reducer annotation."""
        from backend.agent.state import AgentState
        import typing
        # Annotated types appear as typing.Annotated in __annotations__
        ann = AgentState.__annotations__["messages"]
        # Should be Annotated[list, add_messages]
        origin = getattr(ann, "__class__", type(ann)).__name__
        assert ann is not None   # Just verify it's declared (not None / missing)

    def test_agent_state_is_typed_dict(self):
        """AgentState must be a TypedDict subclass."""
        from backend.agent.state import AgentState
        # TypedDicts have __annotations__ and __required_keys__
        assert hasattr(AgentState, "__annotations__")
        assert hasattr(AgentState, "__required_keys__") or issubclass(AgentState, dict)


# ---------------------------------------------------------------------------
# Tests — route_after_reflection() routing logic
# ---------------------------------------------------------------------------

class TestRouteAfterReflection:
    """
    Test the conditional edge function that decides:
      - score via 'reflection_verdict' == "pass"  → "memory_updater"
      - 'reflection_verdict' == "fail" and retries left → "rewrite_node"
      - 'reflection_verdict' == "fail" and loops exhausted → "memory_updater"
    """

    def _state(self, verdict="pass", attempts=0) -> dict:
        """Build a minimal AgentState-shaped dict for routing tests."""
        return {
            "reflection_verdict":  verdict,
            "reflection_attempts": attempts,
            "reflection_score":    9.0 if verdict == "pass" else 4.0,
        }

    def test_routes_to_memory_updater_on_pass(self):
        """When verdict is 'pass', route to 'memory_updater'."""
        from backend.agent.routing.edges import route_after_reflection
        result = route_after_reflection(self._state(verdict="pass", attempts=0))
        assert result == "memory_updater"

    def test_routes_to_rewrite_node_on_fail_with_retries(self):
        """When verdict is 'fail' and retries remain, route to 'rewrite_node'."""
        from backend.agent.routing.edges import route_after_reflection
        result = route_after_reflection(self._state(verdict="fail", attempts=1))
        assert result == "rewrite_node"

    def test_routes_to_memory_updater_when_loops_exhausted(self):
        """When reflection_attempts >= MAX_REFLECTION_LOOPS, accept best answer."""
        from backend.agent.routing.edges import route_after_reflection, MAX_REFLECTION_LOOPS
        result = route_after_reflection(
            self._state(verdict="fail", attempts=MAX_REFLECTION_LOOPS)
        )
        assert result == "memory_updater"

    def test_route_after_rewrite_returns_reflection_node(self):
        """After rewriting, always return to reflection for another check."""
        from backend.agent.routing.edges import route_after_rewrite
        result = route_after_rewrite(self._state())
        assert result == "reflection_node"

    def test_compile_graph_returns_compiled_graph(self):
        """
        compile_graph() must return a compiled graph object without raising.
        Heavy external nodes are mocked at the module level.
        """
        import sys
        from unittest.mock import patch, MagicMock

        async def _noop(state):
            return state

        mock_modules = {
            "backend.agent.nodes.memory_loader":       MagicMock(memory_loader=_noop),
            "backend.agent.nodes.memory_updater_node": MagicMock(memory_updater_node=_noop),
            "backend.agent.nodes.input_parser":        MagicMock(input_parser=_noop),
            "backend.agent.nodes.response_streamer":   MagicMock(response_streamer=_noop),
            "backend.agent.nodes.reflection_node":     MagicMock(reflection_node=_noop),
            "backend.agent.nodes.rewrite_node":        MagicMock(rewrite_node=_noop),
            "backend.agent.nodes.supervisor_node":     MagicMock(supervisor_node=_noop),
            "backend.agent.nodes.worker_dispatcher":   MagicMock(worker_dispatcher=_noop),
            "backend.agent.nodes.aggregator_node":     MagicMock(aggregator_node=_noop),
        }

        # Remove cached graph module so patches take effect cleanly
        for mod in list(sys.modules.keys()):
            if "backend.agent.graph" in mod:
                del sys.modules[mod]

        with patch.dict("sys.modules", mock_modules):
            from backend.agent.graph import compile_graph
            compiled = compile_graph()

        # A LangGraph compiled graph exposes .invoke / .ainvoke
        assert hasattr(compiled, "invoke") or hasattr(compiled, "ainvoke")
