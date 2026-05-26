# playwright-service/Dockerfile
# Isolated browser execution environment
# Runs as separate container — never on same process as FastAPI

FROM python:3.11-slim

# Install Playwright system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl gnupg ca-certificates \
    libglib2.0-0 libnss3 libnspr4 libdbus-1-3 \
    libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 \
    libxrandr2 libgbm1 libasound2 libpango-1.0-0 \
    libcairo2 libatspi2.0-0 libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (Chromium only — ~170MB)
RUN playwright install chromium
RUN playwright install-deps chromium

COPY server.py .

# Non-root user for security
RUN useradd -m -u 1000 browseruser
USER browseruser

EXPOSE 8010

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8010/health || exit 1

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8010"]