import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from backend.config              import get_settings
from backend.api.auth            import limiter
from backend.api.health          import router as health_router
from backend.api.vertical_routes import router as vertical_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger   = logging.getLogger(__name__)
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


app.include_router(health_router,   prefix="/api")
app.include_router(vertical_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name":    "AI Agentic Assistant",
        "version": "1.0.0",
        "docs":    "/docs",
        "health":  "/api/health",
        "agents":  ["social_media", "ca_accounting", "customer_support"],
    }
