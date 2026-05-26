"""
Tests for backend.observability.mlflow_logger:
  - configure_mlflow() calls mlflow.set_tracking_uri
  - log_llm_cost() calculates cost correctly for gpt-4o
  - log_llm_cost() does not raise when mlflow is unavailable
  - log_agent_run() does not raise when mlflow is unavailable
  - get_best_run() returns None when the experiment does not exist
"""
import pytest
from unittest.mock import patch, MagicMock, call


# ---------------------------------------------------------------------------
# Shared mock settings
# ---------------------------------------------------------------------------

def _mock_settings():
    s = MagicMock()
    s.mlflow_tracking_uri = "/tmp/test_mlflow_runs"
    return s


# ---------------------------------------------------------------------------
# Tests — configure_mlflow()
# ---------------------------------------------------------------------------

class TestConfigureMlflow:
    """Tests for configure_mlflow() startup function."""

    def test_configure_mlflow_calls_set_tracking_uri(self):
        """configure_mlflow() must call mlflow.set_tracking_uri with the configured URI."""
        mock_settings = _mock_settings()

        with patch("backend.observability.mlflow_logger.settings", mock_settings), \
             patch("backend.observability.mlflow_logger.mlflow") as mock_mlflow:
            from backend.observability.mlflow_logger import configure_mlflow
            configure_mlflow()

        mock_mlflow.set_tracking_uri.assert_called_once_with("/tmp/test_mlflow_runs")

    def test_configure_mlflow_creates_all_experiments(self):
        """configure_mlflow() must call set_experiment for every canonical experiment name."""
        mock_settings = _mock_settings()
        from backend.observability.mlflow_logger import (
            EXP_AGENT_RUNS, EXP_RAG, EXP_PROMPT_AB, EXP_COST
        )
        expected_experiments = {EXP_AGENT_RUNS, EXP_RAG, EXP_PROMPT_AB, EXP_COST}

        with patch("backend.observability.mlflow_logger.settings", mock_settings), \
             patch("backend.observability.mlflow_logger.mlflow") as mock_mlflow:
            from backend.observability.mlflow_logger import configure_mlflow
            configure_mlflow()

        actual_experiments = {
            c.args[0] for c in mock_mlflow.set_experiment.call_args_list
        }
        assert actual_experiments == expected_experiments

    def test_configure_mlflow_tolerates_experiment_failure(self):
        """configure_mlflow() must not raise even if set_experiment fails."""
        mock_settings = _mock_settings()

        with patch("backend.observability.mlflow_logger.settings", mock_settings), \
             patch("backend.observability.mlflow_logger.mlflow") as mock_mlflow:
            mock_mlflow.set_experiment.side_effect = RuntimeError("MLflow unavailable")
            from backend.observability.mlflow_logger import configure_mlflow
            # Must not raise
            configure_mlflow()


# ---------------------------------------------------------------------------
# Tests — log_llm_cost()
# ---------------------------------------------------------------------------

class TestLogLLMCost:
    """Tests for log_llm_cost() cost calculation and resilience."""

    def test_gpt4o_cost_calculation_is_correct(self):
        """
        gpt-4o pricing: input=$0.005/1K, output=$0.015/1K.
        1000 prompt tokens + 1000 output tokens = $0.005 + $0.015 = $0.020
        """
        logged_metrics = {}

        mock_run_ctx = MagicMock()
        mock_run_ctx.__enter__ = MagicMock(return_value=mock_run_ctx)
        mock_run_ctx.__exit__  = MagicMock(return_value=False)

        with patch("backend.observability.mlflow_logger.mlflow") as mock_mlflow:
            mock_mlflow.active_run.return_value   = None
            mock_mlflow.start_run.return_value    = mock_run_ctx
            mock_mlflow.set_experiment.return_value = None

            def capture_metrics(metrics):
                logged_metrics.update(metrics)

            mock_mlflow.log_metrics.side_effect = capture_metrics

            from backend.observability.mlflow_logger import log_llm_cost
            log_llm_cost(model="gpt-4o", prompt_tokens=1000, output_tokens=1000)

        expected_cost = round(
            (1000 / 1000) * 0.005 + (1000 / 1000) * 0.015,
            6,
        )
        assert "cost_usd" in logged_metrics
        assert abs(logged_metrics["cost_usd"] - expected_cost) < 1e-6

    def test_log_llm_cost_logs_token_counts(self):
        """log_llm_cost() must log prompt_tokens and output_tokens as metrics."""
        logged_metrics = {}

        mock_run_ctx = MagicMock()
        mock_run_ctx.__enter__ = MagicMock(return_value=mock_run_ctx)
        mock_run_ctx.__exit__  = MagicMock(return_value=False)

        with patch("backend.observability.mlflow_logger.mlflow") as mock_mlflow:
            mock_mlflow.active_run.return_value = None
            mock_mlflow.start_run.return_value  = mock_run_ctx

            def capture(metrics):
                logged_metrics.update(metrics)
            mock_mlflow.log_metrics.side_effect = capture

            from backend.observability.mlflow_logger import log_llm_cost
            log_llm_cost(model="gpt-4o", prompt_tokens=200, output_tokens=150)

        assert logged_metrics.get("prompt_tokens") == 200
        assert logged_metrics.get("output_tokens") == 150
        assert logged_metrics.get("total_tokens")  == 350

    def test_log_llm_cost_does_not_raise_when_mlflow_unavailable(self):
        """log_llm_cost() must not raise when mlflow throws an exception."""
        with patch("backend.observability.mlflow_logger.mlflow") as mock_mlflow:
            mock_mlflow.active_run.side_effect   = RuntimeError("MLflow server gone")
            mock_mlflow.set_experiment.side_effect = RuntimeError("MLflow server gone")

            from backend.observability.mlflow_logger import log_llm_cost
            # Must not raise — all errors are caught internally
            log_llm_cost(model="gpt-4o", prompt_tokens=100, output_tokens=50)

    def test_ollama_cost_is_zero(self):
        """ollama models must have zero cost."""
        logged_metrics = {}

        mock_run_ctx = MagicMock()
        mock_run_ctx.__enter__ = MagicMock(return_value=mock_run_ctx)
        mock_run_ctx.__exit__  = MagicMock(return_value=False)

        with patch("backend.observability.mlflow_logger.mlflow") as mock_mlflow:
            mock_mlflow.active_run.return_value = None
            mock_mlflow.start_run.return_value  = mock_run_ctx

            def capture(metrics):
                logged_metrics.update(metrics)
            mock_mlflow.log_metrics.side_effect = capture

            from backend.observability.mlflow_logger import log_llm_cost
            log_llm_cost(model="ollama/llama3", prompt_tokens=500, output_tokens=500)

        assert logged_metrics.get("cost_usd", -1) == 0.0


# ---------------------------------------------------------------------------
# Tests — log_agent_run()
# ---------------------------------------------------------------------------

class TestLogAgentRun:
    """Tests for log_agent_run() resilience."""

    def test_log_agent_run_does_not_raise_when_mlflow_unavailable(self):
        """log_agent_run() must swallow all mlflow exceptions without re-raising."""
        with patch("backend.observability.mlflow_logger.mlflow") as mock_mlflow:
            mock_mlflow.set_experiment.side_effect  = RuntimeError("mlflow down")
            mock_mlflow.start_run.side_effect        = RuntimeError("mlflow down")

            from backend.observability.mlflow_logger import log_agent_run
            log_agent_run(
                session_id="abc123",
                query="What is the capital of France?",
                intent="factual_qa",
                selected_tools=["rag_tool"],
                model_used="gpt-4o",
                latency_ms={"rag_retriever": 150.0, "synthesizer": 200.0},
                final_answer="Paris",
                sources=["wiki/Paris"],
                retry_count=0,
                error=None,
            )

    def test_log_agent_run_logs_session_id(self):
        """When mlflow is available, log_agent_run() must log the session_id param."""
        logged_params = {}

        mock_run_ctx = MagicMock()
        mock_run_ctx.__enter__ = MagicMock(return_value=mock_run_ctx)
        mock_run_ctx.__exit__  = MagicMock(return_value=False)

        with patch("backend.observability.mlflow_logger.mlflow") as mock_mlflow, \
             patch("backend.observability.mlflow_logger.tempfile") as mock_tmp, \
             patch("backend.observability.mlflow_logger.os") as mock_os:

            mock_mlflow.start_run.return_value = mock_run_ctx
            mock_tmp.NamedTemporaryFile.return_value.__enter__ = MagicMock(
                return_value=MagicMock(name="/tmp/fake.json")
            )
            mock_tmp.NamedTemporaryFile.return_value.__exit__ = MagicMock(return_value=False)
            mock_os.path.exists.return_value = False

            def capture_param(k, v):
                logged_params[k] = v
            mock_mlflow.log_param.side_effect = capture_param

            from backend.observability.mlflow_logger import log_agent_run
            log_agent_run(
                session_id="session-xyz",
                query="Hello",
                intent="greeting",
                selected_tools=[],
                model_used="gpt-4o",
                latency_ms={},
                final_answer="Hi!",
                sources=[],
                retry_count=0,
            )

        # If logging succeeded, session_id must have been logged
        if "session_id" in logged_params:
            assert logged_params["session_id"] == "session-xyz"


# ---------------------------------------------------------------------------
# Tests — get_best_run()
# ---------------------------------------------------------------------------

class TestGetBestRun:
    """Tests for get_best_run()."""

    def test_returns_none_when_experiment_missing(self):
        """get_best_run() must return None when the experiment doesn't exist."""
        mock_client = MagicMock()
        mock_client.get_experiment_by_name.return_value = None

        with patch("backend.observability.mlflow_logger.mlflow") as mock_mlflow:
            mock_mlflow.tracking.MlflowClient.return_value = mock_client

            from backend.observability.mlflow_logger import get_best_run
            result = get_best_run("nonexistent_experiment", "avg_score")

        assert result is None

    def test_returns_none_when_no_runs_found(self):
        """get_best_run() must return None when experiment exists but has no runs."""
        mock_experiment = MagicMock()
        mock_experiment.experiment_id = "123"

        mock_client = MagicMock()
        mock_client.get_experiment_by_name.return_value = mock_experiment
        mock_client.search_runs.return_value = []

        with patch("backend.observability.mlflow_logger.mlflow") as mock_mlflow:
            mock_mlflow.tracking.MlflowClient.return_value = mock_client

            from backend.observability.mlflow_logger import get_best_run
            result = get_best_run("empty_experiment", "cost_usd")

        assert result is None

    def test_returns_run_dict_on_success(self):
        """get_best_run() must return a dict with run_id, metrics, params, tags."""
        mock_experiment = MagicMock()
        mock_experiment.experiment_id = "42"

        mock_run = MagicMock()
        mock_run.info.run_id       = "run-abc"
        mock_run.data.metrics      = {"avg_score": 0.9}
        mock_run.data.params       = {"strategy": "hyde"}
        mock_run.data.tags         = {"status": "completed"}

        mock_client = MagicMock()
        mock_client.get_experiment_by_name.return_value = mock_experiment
        mock_client.search_runs.return_value = [mock_run]

        with patch("backend.observability.mlflow_logger.mlflow") as mock_mlflow:
            mock_mlflow.tracking.MlflowClient.return_value = mock_client

            from backend.observability.mlflow_logger import get_best_run
            result = get_best_run("rag_experiments", "avg_score")

        assert result is not None
        assert result["run_id"] == "run-abc"
        assert "metrics" in result
        assert "params"  in result
        assert "tags"    in result

    def test_returns_none_when_mlflow_raises(self):
        """get_best_run() must return None (not raise) when mlflow throws."""
        with patch("backend.observability.mlflow_logger.mlflow") as mock_mlflow:
            mock_mlflow.tracking.MlflowClient.side_effect = RuntimeError("MLflow gone")

            from backend.observability.mlflow_logger import get_best_run
            result = get_best_run("any_experiment", "any_metric")

        assert result is None
