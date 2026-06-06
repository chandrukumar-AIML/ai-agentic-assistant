# FIXED: Removed duplicate Phase A/B app definition — Phase L is canonical
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from backend.config              import get_settings
from backend.api.auth            import limiter
from backend.api.routes              import router
from backend.api.admin_routes        import router as admin_router
from backend.api.memory_routes       import router as memory_router
from backend.api.compliance_routes   import router as compliance_router
from backend.api.hitl_routes         import router as hitl_router
from backend.api.scheduler_routes    import router as scheduler_router
from backend.api.output_routes       import router as output_router
from backend.api.billing_routes      import router as billing_router
from backend.api.a2a_routes          import router as a2a_router, well_known_router
from backend.api.commerce_routes     import router as commerce_router
from backend.api.vertical_routes     import router as vertical_router
from backend.api.ab_routes           import router as ab_router
from backend.api.webhook_routes      import router as webhook_router
from backend.api.websocket       import websocket_endpoint
from backend.mcp.server          import router as mcp_router
from backend.observability.langsmith_tracer import configure_tracing
from backend.observability.mlflow_logger    import configure_mlflow, log_prompt_version
from backend.observability.metrics          import metrics_endpoint
from backend.graph_db.neo4j_client          import close_driver
from backend.session.redis_client           import close_redis
from backend.prompts.registry               import close_pool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger   = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("═══════════════════════════════════════")
    logger.info("  AI Agentic Assistant V2 — Starting")
    logger.info("═══════════════════════════════════════")

    configure_tracing()
    configure_mlflow()

    # PostgreSQL pool
    try:
        from backend.prompts.registry import get_pool
        await get_pool()
        logger.info("PostgreSQL pool ready")
    except Exception as e:
        logger.warning(f"PostgreSQL (non-fatal): {e}")

    # DB migrations
    try:
        from pathlib import Path
        from backend.prompts.registry import get_pool as gp
        pool = await gp()
        for sql_file in sorted(Path("backend").rglob("create_*.sql")):
            async with pool.acquire() as conn:
                await conn.execute(sql_file.read_text())
        logger.info("DB migrations applied")
    except Exception as e:
        logger.warning(f"DB migrations (non-fatal): {e}")

    # Prompt registry
    try:
        from backend.prompts.prompt_loader import seed_default_prompts
        await seed_default_prompts()
        logger.info("Prompt registry ready")
    except Exception as e:
        logger.warning(f"Prompt seed (non-fatal): {e}")

    # LLM warmup — lightweight check only, no model loading
    try:
        from backend.llm.router import llm_router
        health = await asyncio.wait_for(llm_router.health(), timeout=5.0)
        logger.info(
            f"LLM: {health['active_model']} active, "
            f"circuit={health['circuit']['state']}"
        )
    except (asyncio.TimeoutError, Exception) as e:
        logger.warning(f"LLM warmup (non-fatal): {e}")

    # LangGraph agent — lazy compile on first request to save startup RAM
    # On Render free tier (512MB) eager compile causes OOM before port binds
    app.state.agent = None
    app.state.agent_lock = asyncio.Lock()
    logger.info("LangGraph agent: lazy-compile on first request")

    # Log prompt versions — lightweight, no model loading
    try:
        from backend.agent.prompts import PLANNER_PROMPT, SYNTHESIZER_PROMPT
        log_prompt_version("planner_prompt",     PLANNER_PROMPT,     "v2.0.0")
        log_prompt_version("synthesizer_prompt", SYNTHESIZER_PROMPT, "v2.0.0")
    except Exception as e:
        logger.warning(f"Prompt version logging (non-fatal): {e}")

    # Neo4j schema — skip if no password configured (free tier uses FAISS only)
    if settings.neo4j_password:
        try:
            from backend.graph_db.schema import apply_schema
            await asyncio.wait_for(apply_schema(), timeout=10.0)
        except (Exception, asyncio.TimeoutError) as e:
            logger.warning(f"Neo4j schema (non-fatal): {e}")
    else:
        logger.info("Neo4j skipped — NEO4J_PASSWORD not set")

    # Heavy model warmups — skipped on free tier to stay under 512MB RAM
    # Models load lazily on first actual request instead
    if settings.app_env != "production":
        for warmup_name, warmup_fn in [
            ("FlashRank", lambda: __import__("backend.rag.reranker", fromlist=["get_ranker"]).get_ranker()),
        ]:
            try:
                warmup_fn()
                logger.info(f"{warmup_name} loaded")
            except Exception as e:
                logger.warning(f"{warmup_name} warmup (non-fatal): {e}")

        try:
            from backend.voice.stt import warmup_whisper
            await warmup_whisper()
        except Exception as e:
            logger.warning(f"Whisper warmup (non-fatal): {e}")
    else:
        logger.info("Production mode: heavy model warmups deferred to first request")

    # APScheduler — load and resume all active scheduled tasks
    try:
        from backend.scheduler.task_scheduler import start_scheduler
        await start_scheduler()
        logger.info("Task scheduler (APScheduler) started")
    except Exception as e:
        logger.warning(f"Task scheduler (non-fatal): {e}")

    # HITL expiry sweeper — runs every 5 minutes regardless of env
    async def _hitl_sweeper():
        from backend.hitl.hitl_manager import expire_stale_approvals
        while True:
            try:
                await asyncio.sleep(300)   # 5 minutes
                count = await expire_stale_approvals()
                if count:
                    logger.info(f"HITL sweeper expired {count} stale approval(s)")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"HITL sweeper error (non-fatal): {e}")
    asyncio.create_task(_hitl_sweeper())
    logger.info("HITL expiry sweeper started (5-min interval)")

    # Background MLOps scheduler (production only)
    if settings.app_env == "production":
        try:
            from backend.mlops.report_scheduler import start_background_scheduler
            asyncio.create_task(
                start_background_scheduler("00000000-0000-0000-0000-000000000001")
            )
            logger.info("MLOps scheduler started")
        except Exception as e:
            logger.warning(f"MLOps scheduler (non-fatal): {e}")

    logger.info("═══════════════════════════════════════")
    logger.info("  Ready to serve requests")
    logger.info("═══════════════════════════════════════")

    yield

    logger.info("Graceful shutdown — draining connections...")
    await asyncio.sleep(2)
    await close_driver()
    await close_redis()
    await close_pool()
    # Stop APScheduler
    try:
        from backend.scheduler.task_scheduler import stop_scheduler
        await stop_scheduler()
    except Exception:
        pass

    logger.info("All connections closed. Goodbye.")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "0"   # modern browsers ignore; CSP is the real guard
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "   # inline needed for Vite HMR in dev
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "connect-src 'self' ws: wss:; "
            "font-src 'self'; "
            "frame-ancestors 'none';"
        )
        if settings.app_env != "development":
            # HSTS: only set over HTTPS (not in local dev)
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        return response


app = FastAPI(
    title="AI Agentic Assistant V2",
    version="2.0.0",
    description="Production enterprise multi-agent AI system",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter

app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "rate_limit_exceeded",
                 "retry_after": getattr(exc, "retry_after", 60)},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "message": "An internal error occurred."},
    )


app.include_router(router,             prefix="/api")
app.include_router(admin_router,       prefix="/api")
app.include_router(memory_router,      prefix="/api")
app.include_router(compliance_router,  prefix="/api")
app.include_router(hitl_router,        prefix="/api")
app.include_router(scheduler_router,   prefix="/api")
app.include_router(output_router,      prefix="/api")
app.include_router(billing_router,     prefix="/api")
app.include_router(a2a_router,         prefix="/api")
app.include_router(commerce_router,    prefix="/api")
app.include_router(vertical_router,    prefix="/api")
app.include_router(ab_router,          prefix="/api")
app.include_router(webhook_router,     prefix="/api")
app.include_router(well_known_router)   # /.well-known/agent.json (no prefix)
app.include_router(mcp_router)

from backend.api.health import router as health_router
app.include_router(health_router, prefix="/api")

app.add_api_websocket_route("/ws", websocket_endpoint)
app.add_route("/metrics", metrics_endpoint)


@app.get("/")
async def root():
    return {
        "name":    "AI Agentic Assistant V2",
        "version": "2.0.0",
        "docs":    "/docs",
        "health":  "/api/health",
        "phases":  "A-O complete",
    }
