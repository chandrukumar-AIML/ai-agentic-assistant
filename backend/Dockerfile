# backend/Dockerfile
# Build context: project root (.)
# The backend/ package is copied to /app/backend/ so that
# "uvicorn backend.main:app" resolves correctly.

# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Build context is project root — requirements.txt lives under backend/
COPY backend/requirements.txt requirements.txt

# Cache-bust: changing this value forces full pip reinstall (2026-06-06-v3)
ARG CACHE_BUST=2026-06-06-v5

RUN pip install --upgrade pip \
 && pip install --prefix=/install --no-cache-dir -r requirements.txt

# Download spaCy model required by presidio-analyzer (PII/PHI detection)
# Uses the smaller 'sm' model — sufficient for entity recognition
RUN /install/bin/python -m spacy download en_core_web_sm || \
    pip install --prefix=/install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl


# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 appuser

WORKDIR /app

COPY --from=builder /install /usr/local

# Copy only the backend package — root .dockerignore excludes .env, __pycache__, etc.
# Result: /app/backend/main.py, /app/backend/config.py, ...
COPY --chown=appuser:appuser backend/ ./backend/

RUN mkdir -p data/faiss_index data/chroma_db data/mlflow_runs \
             data/training_data data/evidently_reports \
 && chown -R appuser:appuser data/

USER appuser

# Health check uses $PORT (Railway injects this) with fallback to 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8000}/api/health || exit 1

EXPOSE 8000

# WORKDIR=/app, package at /app/backend/ → "backend.main" resolves correctly
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --loop uvloop --http h11 --log-level info"]
