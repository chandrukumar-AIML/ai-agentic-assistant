"""
Tests for backend.observability.langsmith_tracer:
  - configure_tracing() sets LANGCHAIN_TRACING_V2 env var
  - get_ls_client() returns a client instance (LangSmith network mocked)
  - Tracer handles missing LANGCHAIN_API_KEY gracefully
"""
import os
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_settings(api_key="ls__testkey000000000000000000000000000000000"):
    settings = MagicMock()
    settings.langchain_api_key = api_key
    settings.langchain_project = "test-project"
    return settings


# ---------------------------------------------------------------------------
# Tests — configure_tracing()
# ---------------------------------------------------------------------------

class TestConfigureTracing:
    """Tests for configure_tracing() in langsmith_tracer."""

    def test_configure_tracing_sets_tracing_v2_env_var(self):
        """
        configure_tracing() must set LANGCHAIN_TRACING_V2='true' in os.environ.
        Assertion is inside the patch.dict context so env changes are visible.
        """
        mock_settings = _make_mock_settings()

        with patch("backend.observability.langsmith_tracer.settings", mock_settings), \
             patch.dict(os.environ, {}, clear=False):

            from backend.observability.langsmith_tracer import configure_tracing
            configure_tracing()
            # Assert inside the context — patch.dict restores env on exit
            assert os.environ.get("LANGCHAIN_TRACING_V2") == "true"

    def test_configure_tracing_sets_api_key_env_var(self):
        """configure_tracing() must write LANGCHAIN_API_KEY to os.environ."""
        mock_settings = _make_mock_settings(api_key="ls__somekey")

        with patch("backend.observability.langsmith_tracer.settings", mock_settings), \
             patch.dict(os.environ, {}, clear=False):

            from backend.observability.langsmith_tracer import configure_tracing
            configure_tracing()
            assert os.environ.get("LANGCHAIN_API_KEY") == "ls__somekey"

    def test_configure_tracing_sets_project_env_var(self):
        """configure_tracing() must set LANGCHAIN_PROJECT in os.environ."""
        mock_settings = _make_mock_settings()
        mock_settings.langchain_project = "my-test-project"

        with patch("backend.observability.langsmith_tracer.settings", mock_settings), \
             patch.dict(os.environ, {}, clear=False):

            from backend.observability.langsmith_tracer import configure_tracing
            configure_tracing()
            assert os.environ.get("LANGCHAIN_PROJECT") == "my-test-project"


# ---------------------------------------------------------------------------
# Tests — get_ls_client()
# ---------------------------------------------------------------------------

class TestGetLSClient:
    """Tests for get_ls_client() — no real network calls."""

    def setup_method(self):
        """Reset the module-level singleton before each test."""
        import backend.observability.langsmith_tracer as tracer_mod
        tracer_mod._ls_client = None

    def test_get_ls_client_returns_client_instance(self):
        """get_ls_client() must return a LangSmith Client object."""
        mock_settings = _make_mock_settings()
        mock_client   = MagicMock()

        with patch("backend.observability.langsmith_tracer.settings", mock_settings), \
             patch("backend.observability.langsmith_tracer.Client", return_value=mock_client):
            from backend.observability.langsmith_tracer import get_ls_client
            client = get_ls_client()

        assert client is mock_client

    def test_get_ls_client_is_singleton(self):
        """get_ls_client() must return the same object on repeated calls."""
        mock_settings = _make_mock_settings()
        mock_client   = MagicMock()

        with patch("backend.observability.langsmith_tracer.settings", mock_settings), \
             patch("backend.observability.langsmith_tracer.Client", return_value=mock_client):
            from backend.observability.langsmith_tracer import get_ls_client
            first  = get_ls_client()
            second = get_ls_client()

        assert first is second

    def test_get_ls_client_passes_api_key(self):
        """get_ls_client() must instantiate Client with the configured api_key."""
        mock_settings = _make_mock_settings(api_key="ls__myspecialkey")
        mock_client_cls = MagicMock(return_value=MagicMock())

        with patch("backend.observability.langsmith_tracer.settings", mock_settings), \
             patch("backend.observability.langsmith_tracer.Client", mock_client_cls):
            from backend.observability.langsmith_tracer import get_ls_client
            get_ls_client()

        mock_client_cls.assert_called_once_with(api_key="ls__myspecialkey")


# ---------------------------------------------------------------------------
# Tests — graceful handling of missing/invalid API key
# ---------------------------------------------------------------------------

class TestTracerGracefulDegradation:
    """Verify the tracer does not crash when the API key is absent."""

    def setup_method(self):
        import backend.observability.langsmith_tracer as tracer_mod
        tracer_mod._ls_client = None

    def test_configure_tracing_does_not_raise_with_empty_key(self):
        """
        configure_tracing() must not raise even if LANGCHAIN_API_KEY is empty.
        The function only writes env vars — it does not validate the key format.
        """
        mock_settings = MagicMock()
        mock_settings.langchain_api_key = ""
        mock_settings.langchain_project = "test"

        with patch("backend.observability.langsmith_tracer.settings", mock_settings), \
             patch.dict(os.environ, {}, clear=False):
            from backend.observability.langsmith_tracer import configure_tracing
            # Must not raise
            configure_tracing()
            # Env var is set (even if empty) — assert inside context
            assert "LANGCHAIN_TRACING_V2" in os.environ

    @pytest.mark.asyncio
    async def test_submit_feedback_returns_false_when_client_raises(self):
        """
        submit_feedback() must return False (not raise) when the LangSmith
        client throws a network or auth error.
        """
        mock_settings = _make_mock_settings()
        mock_client   = MagicMock()
        mock_client.create_feedback.side_effect = RuntimeError("LangSmith unreachable")

        with patch("backend.observability.langsmith_tracer.settings", mock_settings), \
             patch("backend.observability.langsmith_tracer._ls_client", mock_client):
            from backend.observability.langsmith_tracer import submit_feedback
            result = await submit_feedback(
                run_id="run-123",
                score=1.0,
                comment="Great answer",
            )
        assert result is False
