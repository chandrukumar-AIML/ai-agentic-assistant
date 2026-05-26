#!/usr/bin/env bash
# deploy/health_check_prod.sh
# Post-deployment production health check.
# Usage: BACKEND_URL=https://your-backend.railway.app bash deploy/health_check_prod.sh

set -euo pipefail

BACKEND_URL="${BACKEND_URL:-}"
MAX_RETRIES=20
SLEEP_SECS=10

if [[ -z "$BACKEND_URL" ]]; then
  echo "ERROR: BACKEND_URL environment variable is required."
  echo "Usage: BACKEND_URL=https://your-backend.railway.app bash deploy/health_check_prod.sh"
  exit 1
fi

echo "=== Production Health Check ==="
echo "Target: $BACKEND_URL"
echo ""

for i in $(seq 1 $MAX_RETRIES); do
  echo -n "Attempt $i/$MAX_RETRIES: "

  STATUS=$(curl -sf "$BACKEND_URL/api/health" \
    -H "Accept: application/json" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','unknown'))" \
    2>/dev/null || echo "unreachable")

  echo "$STATUS"

  if [[ "$STATUS" == "ok" ]]; then
    echo ""
    echo "Backend is healthy!"

    # Print full health JSON
    echo ""
    echo "=== Health Details ==="
    curl -sf "$BACKEND_URL/api/health" | python3 -m json.tool || true
    echo ""
    echo "=== All checks passed ==="
    exit 0
  fi

  if [[ $i -lt $MAX_RETRIES ]]; then
    echo "  Waiting ${SLEEP_SECS}s..."
    sleep "$SLEEP_SECS"
  fi
done

echo ""
echo "ERROR: Backend health check timed out after $((MAX_RETRIES * SLEEP_SECS))s"
exit 1
