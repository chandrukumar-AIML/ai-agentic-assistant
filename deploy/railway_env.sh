#!/usr/bin/env bash
# deploy/railway_env.sh
# Set Railway environment variables from .env without exposing secrets to shell environment.
# Usage: bash deploy/railway_env.sh

set -euo pipefail

if ! command -v railway &>/dev/null; then
  echo "Railway CLI not installed. Run: npm i -g @railway/cli"
  exit 1
fi

if [ ! -f ".env" ]; then
  echo ".env file not found. Copy .env.example and fill in values."
  exit 1
fi

echo "Setting Railway environment variables for backend service..."

# Read a single key from .env without sourcing the whole file.
# This avoids exposing all secrets as shell environment variables.
get_env_val() {
  local key=$1
  grep "^${key}=" .env | head -1 | cut -d'=' -f2- | tr -d '"' | tr -d "'"
}

railway_set() {
  local key=$1
  local val
  val=$(get_env_val "$key")

  if [ -z "$val" ]; then
    echo "  SKIP $key (not found in .env)"
    return
  fi

  railway variables set "${key}=${val}" --service backend 2>/dev/null \
    && echo "  SET  $key" \
    || echo "  FAIL $key"
}

railway_set "OPENAI_API_KEY"
railway_set "OPENAI_MODEL"
railway_set "OPENAI_EMBEDDING_MODEL"
railway_set "LANGCHAIN_API_KEY"
railway_set "LANGCHAIN_PROJECT"
railway_set "TAVILY_API_KEY"
railway_set "JWT_SECRET"
railway_set "CHUNK_SIZE"
railway_set "CHUNK_OVERLAP"
railway_set "API_RATE_LIMIT"

# Static production values
railway variables set "LANGCHAIN_TRACING_V2=true"  --service backend
railway variables set "APP_ENV=production"          --service backend
railway variables set "LOG_LEVEL=INFO"              --service backend

echo ""
echo "Setting frontend variables..."

# These use Railway reference variables — set literally (Railway resolves them)
railway variables set 'VITE_API_URL=https://${{backend.RAILWAY_PUBLIC_DOMAIN}}/api' --service frontend
railway variables set 'VITE_WS_URL=wss://${{backend.RAILWAY_PUBLIC_DOMAIN}}/ws'    --service frontend

echo ""
echo "Done. Manually set in dashboard:"
echo "  NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD"
echo "  REDIS_URL"
echo "  CHROMA_HOST, CHROMA_PORT"
echo "  CORS_ORIGINS (your frontend public URL)"
echo ""
echo "Deploy with: railway up"