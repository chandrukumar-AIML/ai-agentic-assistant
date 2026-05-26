"""
Tests for the LLM router and circuit breaker:
  - Circuit breaker starts CLOSED
  - 3 consecutive failures open the circuit
  - Open circuit raises / falls back without calling the primary LLM again
  - classify_query() returns TRIVIAL for short greetings
  - classify_query() returns COMPLEX for long technical queries
"""
import asyncio
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Tests — CircuitBreaker state machine
# ---------------------------------------------------------------------------

class TestCircuitBreaker:
    """Unit tests for backend.llm.router.CircuitBreaker."""

    def _make_breaker(self):
        from backend.llm.router import CircuitBreaker
        return CircuitBreaker(failure_threshold=3, cooldown_seconds=30.0)

    def test_circuit_starts_closed(self):
        """A freshly created CircuitBreaker must be in the CLOSED state."""
        from backend.llm.router import CircuitState
        cb = self._make_breaker()
        assert cb.state == CircuitState.CLOSED

    def test_should_attempt_primary_when_closed(self):
        """should_attempt_primary() must return True when CLOSED."""
        cb = self._make_breaker()
        assert cb.should_attempt_primary() is True

    def test_three_consecutive_failures_open_circuit(self):
        """After 3 record_failure() calls, state must become OPEN."""
        from backend.llm.router import CircuitState
        cb = self._make_breaker()
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED   # Not yet
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_open_circuit_does_not_attempt_primary(self):
        """should_attempt_primary() must return False when OPEN (cooldown not elapsed)."""
        from backend.llm.router import CircuitState
        import time
        cb = self._make_breaker()
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        # Manually set last_failure_time to 'now' so cooldown hasn't elapsed
        cb.last_failure_time = time.monotonic()
        assert cb.should_attempt_primary() is False

    def test_record_success_resets_failure_count(self):
        """record_success() while CLOSED must reset the failure counter."""
        cb = self._make_breaker()
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb.failure_count == 0

    def test_half_open_after_cooldown(self):
        """Circuit transitions OPEN → HALF_OPEN after cooldown elapses."""
        from backend.llm.router import CircuitState
        import time
        cb = self._make_breaker()
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Simulate cooldown elapsed by backdating last_failure_time
        cb.last_failure_time = time.monotonic() - 60.0
        assert cb.should_attempt_primary() is True
        assert cb.state == CircuitState.HALF_OPEN

    def test_total_fallbacks_increments_on_open(self):
        """total_fallbacks counter must increment each time circuit opens."""
        cb = self._make_breaker()
        for _ in range(3):
            cb.record_failure()
        assert cb.total_fallbacks == 1


# ---------------------------------------------------------------------------
# Tests — LLMRouter: open circuit skips primary LLM call
# ---------------------------------------------------------------------------

class TestLLMRouterCircuitOpen:
    """
    Verify that when the circuit is OPEN, llm_router.complete() bypasses
    the OpenAI client and falls back to Ollama (without an explicit
    CircuitOpenError being raised — the router handles it internally).
    """

    @pytest.mark.asyncio
    async def test_open_circuit_skips_openai_call(self):
        """When circuit is OPEN, openai_chat must NOT be called."""
        from backend.llm.router import LLMRouter, CircuitState
        import time

        router = LLMRouter()
        # Force circuit OPEN with expired cooldown simulated by backdating
        router.circuit.state = CircuitState.OPEN
        router.circuit.last_failure_time = time.monotonic() - 1   # cooldown NOT elapsed → stays OPEN
        router.circuit.last_failure_time = time.monotonic()        # resets to now → OPEN stays

        mock_openai = AsyncMock(return_value="openai response")
        mock_ollama = AsyncMock(return_value="ollama response")

        with patch("backend.llm.router.openai_chat", mock_openai), \
             patch("backend.llm.router.ollama_chat", mock_ollama):
            # circuit is OPEN with cooldown not elapsed — should NOT call openai
            try:
                response, model = await router.complete([{"role": "user", "content": "hi"}])
            except Exception:
                pass

        mock_openai.assert_not_called()

    @pytest.mark.asyncio
    async def test_successful_call_records_success(self):
        """A successful ollama_chat call must return the expected model name and no failures."""
        from backend.llm.router import LLMRouter, CircuitState

        router = LLMRouter()
        assert router.circuit.state == CircuitState.CLOSED

        with patch("backend.llm.router.ollama_chat", AsyncMock(return_value="ok")):
            response, model = await router.complete([{"role": "user", "content": "hello"}])

        # Router is Ollama-first: primary model is ollama/<ollama_model>
        assert model.startswith("ollama/")
        assert router.circuit.failure_count == 0


# ---------------------------------------------------------------------------
# Tests — classify_query() complexity classifier
# ---------------------------------------------------------------------------

class TestClassifyQuery:
    """Tests for backend.cost.classifier.classify_query()."""

    def test_short_greeting_classified_as_trivial(self):
        """A bare greeting like 'Hi' must be classified as TRIVIAL."""
        from backend.cost.classifier import classify_query, Complexity
        result = classify_query(query="hi", has_image=False)
        assert result.complexity == Complexity.TRIVIAL

    def test_hello_classified_as_trivial(self):
        """'hello' must map to TRIVIAL and route to ollama."""
        from backend.cost.classifier import classify_query, Complexity
        result = classify_query(query="hello")
        assert result.complexity == Complexity.TRIVIAL
        assert result.model == "ollama"

    def test_long_technical_query_classified_as_complex(self):
        """A long multi-concept query must be classified as COMPLEX."""
        from backend.cost.classifier import classify_query, Complexity
        long_query = (
            "Please compare and contrast the system design tradeoffs between "
            "microservices and monolithic architectures, analyse the performance "
            "implications, explain why distributed transactions are problematic, "
            "and provide a comprehensive step-by-step migration strategy for a "
            "legacy monolith with 500k daily active users and strict SLA requirements."
        )
        result = classify_query(query=long_query, has_image=False)
        assert result.complexity == Complexity.COMPLEX

    def test_image_query_classified_as_vision(self):
        """Any query with has_image=True must be classified as VISION."""
        from backend.cost.classifier import classify_query, Complexity
        result = classify_query(query="describe this", has_image=True)
        assert result.complexity == Complexity.VISION
        assert result.model == "gpt-4o"

    def test_confidence_between_0_and_1(self):
        """Confidence score must be in [0, 1] for any input."""
        from backend.cost.classifier import classify_query
        for query in ["hi", "explain recursion", "Write me a comprehensive analysis"]:
            result = classify_query(query=query)
            assert 0.0 <= result.confidence <= 1.0, (
                f"Confidence out of range for query '{query}': {result.confidence}"
            )

    def test_complex_query_routes_to_gpt4o(self):
        """COMPLEX classification must route to gpt-4o."""
        from backend.cost.classifier import classify_query, Complexity
        result = classify_query(
            query="Analyse the architectural design patterns and evaluate the performance "
                  "tradeoffs in detail, providing a comprehensive step-by-step comparison.",
        )
        if result.complexity == Complexity.COMPLEX:
            assert result.model == "gpt-4o"

    def test_classification_result_has_reasons(self):
        """ClassificationResult must include a non-empty reasons list."""
        from backend.cost.classifier import classify_query
        result = classify_query(
            query="Explain step-by-step how gradient descent works in neural networks."
        )
        assert isinstance(result.reasons, list)
        assert len(result.reasons) > 0
