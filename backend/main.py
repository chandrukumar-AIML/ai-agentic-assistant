import json
import logging
import logging.config
import os
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from backend.api.auth import limiter
from backend.api.auth import router as auth_router
from backend.api.auth_social import router as auth_social_router
from backend.api.health import router as health_router
from backend.api.vertical_routes import router as vertical_router
from backend.config import get_settings


class _JSONFormatter(logging.Formatter):
    """Emit one JSON object per log line — friendly for cloud log parsers."""
    def format(self, record: logging.LogRecord) -> str:
        base = {
            "ts":      self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level":   record.levelname,
            "logger":  record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            base["exc"] = self.formatException(record.exc_info)
        return json.dumps(base, ensure_ascii=False)


def _setup_logging(level: str = "INFO") -> None:
    _fmt = _JSONFormatter() if os.getenv("APP_ENV", "development") == "production" else None
    handler = logging.StreamHandler()
    if _fmt:
        handler.setFormatter(_fmt)
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        handlers=[handler],
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )


_setup_logging(os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(
    title="AI Agentic Assistant",
    version="1.0.0",
    description="Social Media · CA Accounting · Customer Support agents",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def _request_logger(request: Request, call_next):
    start = time.monotonic()

    # Extract action name from POST body on action endpoints (non-destructive read)
    action = ""
    if request.method == "POST" and "/action" in request.url.path:
        try:
            body = await request.body()
            import json as _json
            action = _json.loads(body).get("action", "")
            # Re-attach body so downstream handlers can still read it
            from starlette.requests import Request as StarletteRequest
            async def _receive():
                return {"type": "http.request", "body": body}
            request = StarletteRequest(request.scope, _receive)
        except Exception:
            pass

    response = await call_next(request)
    ms = round((time.monotonic() - start) * 1000, 1)
    logger.info(
        "%s %s action=%s → %s  (%.1fms)",
        request.method, request.url.path, action or "-", response.status_code, ms,
    )
    return response


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "rate_limit_exceeded", "retry_after": getattr(exc, "retry_after", 60)},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "message": "An internal error occurred."},
    )


app.include_router(auth_router,        prefix="/api")
app.include_router(auth_social_router, prefix="/api")
app.include_router(health_router,      prefix="/api")
app.include_router(vertical_router,    prefix="/api")


@app.get("/")
async def root():
    return {
        "name":    "AI Agentic Assistant",
        "version": "1.0.0",
        "docs":    "/docs",
        "health":  "/api/health",
        "agents":  ["social_media", "ca_accounting", "customer_support"],
    }
