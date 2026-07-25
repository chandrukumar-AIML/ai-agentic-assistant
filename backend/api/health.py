"""Health check endpoints — app status and Ollama connectivity."""
import asyncio
import logging
import time
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


class ServiceStatus(BaseModel):
    name:       str
    healthy:    bool
    latency_ms: float
    detail:     Optional[str] = None


class HealthResponse(BaseModel):
    status:   str
    version:  str = "1.0.0"
    services: list[ServiceStatus]
    summary:  str


async def _check(name: str, coro, timeout: float = 5.0) -> ServiceStatus:
    start = time.monotonic()
    try:
        ok, detail = await asyncio.wait_for(coro, timeout=timeout)
        return ServiceStatus(
            name=name, healthy=ok,
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
            detail=str(e)[:120],
        )


async def _check_ollama() -> tuple[bool, str]:
    from backend.llm.ollama_openai import ollama_health
    ok = await ollama_health()
    return ok, "Ollama running (llama3.2)" if ok else "Ollama unreachable — start with: ollama serve"


async def _check_groq() -> tuple[bool, str]:
    from backend.config import get_settings
    cfg = get_settings()
    if not cfg.groq_api_key:
        return False, "GROQ_API_KEY not set (optional)"
    return True, "Groq API key configured"


async def _check_gemini() -> tuple[bool, str]:
    from backend.config import get_settings
    cfg = get_settings()
    if not cfg.gemini_api_key:
        return False, "GEMINI_API_KEY not set (optional)"
    return True, "Gemini API key configured"


@router.get("/health", tags=["health"])
async def health():
    """Quick liveness probe — used by load balancers."""
    return {"status": "ok", "version": "1.0.0"}


@router.get("/health/deep", response_model=HealthResponse, tags=["health"])
async def deep_health():
    """Deep health check — tests Ollama + optional LLM providers."""
    checks = await asyncio.gather(
        _check("ollama", _check_ollama(), timeout=5.0),
        _check("groq",   _check_groq(),   timeout=2.0),
        _check("gemini", _check_gemini(), timeout=2.0),
    )

    any_critical_down = [s for s in checks if s.name == "ollama" and not s.healthy]
    any_down          = [s for s in checks if not s.healthy]

    overall = "critical" if any_critical_down else ("degraded" if any_down else "ok")
    down_names = [s.name for s in any_down]
    summary = (
        "All services healthy"
        if not any_down
        else f"{len(any_down)} service(s) not available: {', '.join(down_names)}"
    )

    return HealthResponse(status=overall, services=list(checks), summary=summary)
