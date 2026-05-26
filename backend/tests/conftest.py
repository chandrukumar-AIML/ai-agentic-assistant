"""
Shared pytest fixtures for the AI Agentic backend test suite.
"""
import os
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Environment setup — must happen before any backend imports
# ---------------------------------------------------------------------------

os.environ.setdefault("OPENAI_API_KEY",    "sk-test-0000000000000000000000000000000000000000000000000")
os.environ.setdefault("LANGCHAIN_API_KEY", "ls__test000000000000000000000000000000000000000000000")
os.environ.setdefault("JWT_SECRET",        "test-jwt-secret-that-is-at-least-32-chars-long!")
os.environ.setdefault("NEO4J_PASSWORD",    "test-password")
os.environ.setdefault("TAVILY_API_KEY",    "tvly-test-key")
os.environ.setdefault("APP_ENV",           "development")


# ---------------------------------------------------------------------------
# Singleton resets (prevent cross-test bleed)
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_faiss_singleton():
    """Reset FAISS in-memory singleton before and after every test to prevent bleed."""
    import backend.rag.faiss_store as fs
    fs._index    = None
    fs._metadata = []
    yield
    fs._index    = None
    fs._metadata = []


@pytest.fixture(autouse=True)
def reset_neo4j_driver():
    """Reset Neo4j driver singleton between tests."""
    try:
        import backend.graph_db.neo4j_client as nc
        nc._driver = None
        yield
        nc._driver = None
    except ImportError:
        yield


@pytest.fixture(autouse=True)
def reset_redis_singleton():
    """Reset Redis singleton between tests."""
    try:
        import backend.session.redis_client as rc
        rc._redis = None
        yield
        rc._redis = None
    except ImportError:
        yield


# ---------------------------------------------------------------------------
# Settings override fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_settings():
    """
    Override sensitive settings so tests never touch real external services.
    Returns the patched settings object so tests can inspect/modify it.
    """
    from unittest.mock import MagicMock
    settings = MagicMock()
    settings.openai_api_key          = "sk-test-000"
    settings.openai_model            = "gpt-4o"
    settings.openai_embedding_model  = "text-embedding-3-small"
    settings.langchain_api_key       = "ls__test000"
    settings.langchain_project       = "test-project"
    settings.jwt_secret              = "test-jwt-secret-that-is-at-least-32-chars-long!"
    settings.app_env                 = "production"   # Use production so auth is enforced
    settings.cors_origins            = ["http://localhost:5173"]
    settings.mlflow_tracking_uri     = "/tmp/test_mlflow"
    settings.faiss_index_path        = "/tmp/test_faiss_index"
    settings.chroma_persist_path     = "/tmp/test_chroma"
    settings.chroma_host             = "localhost"
    settings.chroma_port             = 8001
    settings.ollama_model            = "llama3"
    settings.ollama_base_url         = "http://localhost:11434"
    settings.redis_url               = "redis://localhost:6379"
    settings.neo4j_uri               = "bolt://localhost:7687"
    settings.neo4j_user              = "neo4j"
    settings.neo4j_password          = "test"
    settings.tavily_api_key          = "tvly-test"
    settings.api_rate_limit          = 60
    return settings


# ---------------------------------------------------------------------------
# FastAPI app fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def app():
    """
    Return a minimal FastAPI app for testing that avoids triggering
    the full lifespan (which requires real Redis, Neo4j, etc.).
    """
    from fastapi import FastAPI, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse

    test_app = FastAPI(title="Test App")

    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @test_app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "message": "An internal error occurred."},
        )

    @test_app.get("/api/health")
    async def health():
        return {"status": "ok"}

    @test_app.get("/api/protected")
    async def protected():
        # Simulates an endpoint that requires auth
        return {"data": "secret"}

    @test_app.get("/api/error")
    async def error_endpoint():
        raise ValueError("This is a raw internal error — must NOT appear in response")

    return test_app


# ---------------------------------------------------------------------------
# Async HTTP client fixture
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture()
async def client(app):
    """Async HTTP test client backed by the test FastAPI app."""
    from httpx import AsyncClient, ASGITransport
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
