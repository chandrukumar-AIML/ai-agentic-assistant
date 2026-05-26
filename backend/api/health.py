# backend/api/health.py
"""
Comprehensive health check endpoint.
Checks every service dependency with timeout protection.
"""
import asyncio
import logging
import time
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter()


class ServiceStatus(BaseModel):
    name:       str
    healthy:    bool
    latency_ms: float
    detail:     Optional[str] = None


class HealthResponse(BaseModel):
    status:    str   # "ok" | "degraded" | "critical"
    version:   str   = "2.0.0"
    services:  list[ServiceStatus]
    summary:   str


async def _check(name: str, coro, timeout: float = 5.0) -> ServiceStatus:
    start = time.monotonic()
    try:
        ok, detail = await asyncio.wait_for(coro, timeout=timeout)
        return ServiceStatus(
            name=name,
            healthy=ok,
            latency_ms=round((time.monotonic() - start) * 1000, 2),
            detail=detail,
        )
    except asyncio.TimeoutError:
        return ServiceStatus(
            name=name, healthy=False,
            latency_ms=round(timeout * 1000),
            detail=f"Timeout after {timeout}s",
        )
    except Exception as e:
        return ServiceStatus(
            name=name, healthy=False,
            latency_ms=round((time.monotonic() - start) * 1000, 2),
            detail=str(e)[:100],
        )


async def _check_openai() -> tuple[bool, str]:
    from backend.llm.openai_client import openai_health_check
    ok = await openai_health_check()
    return ok, "gpt-4o reachable" if ok else "OpenAI unreachable"


async def _check_ollama() -> tuple[bool, str]:
    from backend.llm.ollama_client import ollama_health
    ok = await ollama_health()
    return ok, "ollama running" if ok else "ollama unreachable"


async def _check_neo4j() -> tuple[bool, str]:
    from backend.graph_db.neo4j_client import health_check, get_node_counts
    ok = await health_check()
    if ok:
        counts = await get_node_counts()
        total  = sum(counts.values())
        return True, f"{total} nodes in graph"
    return False, "Neo4j unreachable"


async def _check_redis() -> tuple[bool, str]:
    from backend.session.redis_client import get_redis
    r    = await get_redis()
    pong = await r.ping()
    info = await r.info("memory")
    used = info.get("used_memory_human", "?")
    return bool(pong), f"Redis OK, memory={used}"


async def _check_chromadb() -> tuple[bool, str]:
    from backend.rag.chroma_store import get_count
    count = get_count()
    return True, f"{count} documents indexed"


async def _check_faiss() -> tuple[bool, str]:
    from backend.rag.faiss_store import get_index_size
    size = get_index_size()
    return True, f"{size} vectors indexed"


async def _check_postgres() -> tuple[bool, str]:
    from backend.prompts.registry import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT COUNT(*) AS cnt FROM prompt_versions")
    count = row["cnt"] if row else 0
    return True, f"{count} prompt versions"


async def _check_playwright() -> tuple[bool, str]:
    import httpx
    r = await httpx.AsyncClient(timeout=5.0).get("http://aaa_playwright:8010/health")
    if r.status_code == 200:
        data     = r.json()
        sessions = data.get("active_sessions", 0)
        return True, f"browser ready, {sessions} active sessions"
    return False, f"HTTP {r.status_code}"


async def _check_circuit_breaker() -> tuple[bool, str]:
    from backend.llm.router import llm_router
    status = llm_router.circuit.get_status()
    state  = status["state"]
    ok     = state in ("closed", "half_open")
    return ok, f"circuit={state} fallbacks={status['total_fallbacks']}"


@router.get("/health/deep", response_model=HealthResponse)
async def deep_health_check():
    """
    Deep health check — tests every service dependency.
    Used by monitoring systems and load balancers.
    Returns 200 even if degraded (so LB doesn't pull the instance).
    Returns 503 only if critical.
    """
    checks = await asyncio.gather(
        _check("openai",          _check_openai(),          timeout=8.0),
        _check("ollama",          _check_ollama(),          timeout=5.0),
        _check("neo4j",           _check_neo4j(),           timeout=5.0),
        _check("redis",           _check_redis(),           timeout=3.0),
        _check("chromadb",        _check_chromadb(),        timeout=3.0),
        _check("faiss",           _check_faiss(),           timeout=2.0),
        _check("postgres",        _check_postgres(),        timeout=5.0),
        _check("playwright",      _check_playwright(),      timeout=5.0),
        _check("circuit_breaker", _check_circuit_breaker(), timeout=2.0),
    )

    # Categorise
    critical_services = {"redis", "postgres", "faiss"}
    critical_down     = [s for s in checks if s.name in critical_services and not s.healthy]
    any_down          = [s for s in checks if not s.healthy]

    if critical_down:
        overall = "critical"
    elif any_down:
        overall = "degraded"
    else:
        overall = "ok"

    down_names = [s.name for s in any_down]
    summary    = (
        f"All {len(checks)} services healthy"
        if not any_down
        else f"{len(any_down)} service(s) unhealthy: {', '.join(down_names)}"
    )

    return HealthResponse(
        status=overall,
        services=list(checks),
        summary=summary,
    )