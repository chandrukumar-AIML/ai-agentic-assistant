# backend/memory/mem0_client.py
"""
Mem0 client wrapper.
Supports both Mem0 Cloud (API key) and self-hosted (PostgreSQL).
We default to self-hosted using our existing PostgreSQL.
"""
import logging
from functools import lru_cache
from mem0 import Memory
from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _build_config() -> dict:
    """
    Build Mem0 config.
    If MEM0_API_KEY is set → use Mem0 Cloud.
    Otherwise → self-hosted with PostgreSQL + local embeddings.
    """
    if settings.mem0_api_key:
        # Cloud mode — simplest, no infra needed
        return {
            "api_key": settings.mem0_api_key,
        }

    # Self-hosted mode — PostgreSQL backend + OpenAI embeddings
    return {
        "vector_store": {
            "provider": "pgvector",
            "config": {
                "dbname":   settings.postgres_db,
                "user":     settings.postgres_user,
                "password": settings.postgres_password,
                "host":     settings.postgres_host,
                "port":     settings.postgres_port,
            },
        },
        "llm": {
            "provider": "openai",
            "config": {
                "model":   settings.openai_model,
                "api_key": settings.openai_api_key,
            },
        },
        "embedder": {
            "provider": "openai",
            "config": {
                "model":   "text-embedding-3-small",
                "api_key": settings.openai_api_key,
            },
        },
        "history_db_path": "",          # use PostgreSQL, not SQLite
        "version":         "v1.1",
    }


@lru_cache(maxsize=1)
def get_mem0() -> Memory:
    """
    Singleton Mem0 client.
    Cached — instantiated once at startup.
    """
    config = _build_config()
    try:
        if settings.mem0_api_key:
            from mem0 import MemoryClient
            client = MemoryClient(api_key=settings.mem0_api_key)
            logger.info("Mem0: using cloud mode")
            return client
        else:
            client = Memory.from_config(config)
            logger.info("Mem0: using self-hosted PostgreSQL mode")
            return client
    except Exception as e:
        logger.error(f"Mem0 init failed: {e}")
        raise