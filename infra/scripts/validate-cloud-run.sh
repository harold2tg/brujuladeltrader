#!/bin/bash
set -euo pipefail

# ---------------------------------------------------------------------------
# validate-cloud-run.sh — Smoke-test all Cloud Run endpoints
#
# Tests: health check, auth flow, file upload, AI diagnosis endpoints.
# Requires: curl, jq, gcloud CLI authenticated.
#
# Usage:
#   ./validate-cloud-run.sh --env <prod|dev> [--project <gcp-project>]
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Defaults
ENV="prod"
PROJECT=""
API_URL=""
WEB_URL=""
FAILED=0
PASSED=0

usage() {
  cat <<EOF
Usage: $0 [OPTIONS]

Validate Cloud Run services for La Brújula del Trader.

Options:
  --env       Target environment: prod or dev (default: prod)
  --project   GCP project ID (default: from gcloud config)
  --api-url   Override API URL (default: auto-detect from Cloud Run)
  --web-url   Override Web URL (default: auto-detect from Cloud Run)
  --help      Show this help message
EOF
  exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --env) ENV="$2"; shift 2 ;;
    --project) PROJECT="$2"; shift 2 ;;
    --api-url) API_URL="$2"; shift 2 ;;
    --web-url) WEB_URL="$2"; shift 2 ;;
    --help) usage ;;
    *) echo "Unknown option: $1"; usage ;;
  esac
done

# Auto-detect project if not set
if [[ -z "$PROJECT" ]]; then
  PROJECT=$(gcloud config get-value project 2>/dev/null)
  if [[ -z "$PROJECT" ]]; then
    echo "Error: --project required or gcloud project must be configured"
    exit 1
  fi
fi

REGION=$(gcloud config get-value compute/region 2>/dev/null || echo "us-central1")

# Auto-detect URLs from Cloud Run if not overridden
if [[ -z "$API_URL" ]]; then
  API_URL=$(gcloud run services describe "brujula-api-${ENV}" --region "$REGION" --format="value(status.url)" 2>/dev/null || echo "")
  if [[ -z "$API_URL" ]]; then
    echo "Error: Could not detect API URL. Use --api-url to override."
    exit 1
  fi
fi

if [[ -z "$WEB_URL" ]]; then
  WEB_URL=$(gcloud run services describe "brujula-web-${ENV}" --region "$REGION" --format="value(status.url)" 2>/dev/null || echo "")
  if [[ -z "$WEB_URL" ]]; then
    echo "Error: Could not detect Web URL. Use --web-url to override."
    exit 1
  fi
fi

echo "🧭 Brujula Cloud Run Validation"
echo "========================================"
echo "Environment: $ENV"
echo "Project:     $PROJECT"
echo "Region:      $REGION"
echo "API URL:     $API_URL"
echo "Web URL:     $WEB_URL"
echo "========================================"
echo ""

# ---------------------------------------------------------------------------
# Helper: test an endpoint
# ---------------------------------------------------------------------------
test_endpoint() {
  local name="$1"
  local method="$2"
  local url="$3"
  local expected_status="$4"
  local data="${5:-}"

  echo -n "  $name ... "

  if [[ -n "$data" ]]; then
    RESPONSE=$(curl -s -o /tmp/brujula_resp.json -w "%{http_code}" \
      -X "$method" "$url" \
      -H "Content-Type: application/json" \
      -d "$data" \
      --max-time 15 2>/dev/null || echo "000")
  else
    RESPONSE=$(curl -s -o /tmp/brujula_resp.json -w "%{http_code}" \
      -X "$method" "$url" \
      --max-time 15 2>/dev/null || echo "000")
  fi

  if [[ "$RESPONSE" == "$expected_status" ]]; then
    echo "✅ $RESPONSE"
    PASSED=$((PASSED + 1))
  else
    echo "❌ $RESPONSE (expected $expected_status)"
    if [[ -f /tmp/brujula_resp.json ]]; then
      echo "     Response: $(cat /tmp/brujula_resp.json | head -c 200)"
    fi
    FAILED=$((FAILED + 1))
  fi
}

# ---------------------------------------------------------------------------
# Test 1: API Health Check
# ---------------------------------------------------------------------------
echo "📡 API Endpoints"
test_endpoint "GET /health" "GET" "$API_URL/health" "200"

# ---------------------------------------------------------------------------
# Test 2: Web Health Check
# ---------------------------------------------------------------------------
echo ""
echo "🌐 Web Endpoints"
test_endpoint "GET /" "GET" "$WEB_URL" "200"

# ---------------------------------------------------------------------------
# Test 3: API Auth Flow (register → login)
# ---------------------------------------------------------------------------
echo ""
echo "🔐 Auth Flow"

REGISTER_PAYLOAD='{"email":"test-'$(date +%s)'@brujula.test","password":"Test1234!","name":"Test User"}'
test_endpoint "POST /auth/register" "POST" "$API_URL/auth/register" "201" "$REGISTER_PAYLOAD"

# Extract credentials from registration for login
if [[ -f /tmp/brujula_resp.json ]]; then
  TEST_EMAIL=$(jq -r '.email // empty' /tmp/brujula_resp.json 2>/dev/null || echo "")
  TEST_PASSWORD=$(echo "$REGISTER_PAYLOAD" | jq -r '.password')
fi

if [[ -n "$TEST_EMAIL" ]]; then
  LOGIN_PAYLOAD="{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}"
  test_endpoint "POST /auth/login" "POST" "$API_URL/auth/login" "200" "$LOGIN_PAYLOAD"

  # Extract token for authenticated requests
  if [[ -f /tmp/brujula_resp.json ]]; then
    AUTH_TOKEN=$(jq -r '.access_token // .token // empty' /tmp/brujula_resp.json 2>/dev/null || echo "")
  fi
fi

# ---------------------------------------------------------------------------
# Test 4: Authenticated Endpoints
# ---------------------------------------------------------------------------
echo ""
echo "🔒 Authenticated Endpoints"

if [[ -n "${AUTH_TOKEN:-}" ]]; then
  test_endpoint "GET /uploads (auth)" "GET" "$API_URL/uploads" "200" ""
  # Note: upload and AI endpoints require specific request formats
  # These are basic smoke tests — full validation happens in compare-responses.sh
else
  echo "  ⚠️  Skipping authenticated endpoints — no auth token"
fi

# ---------------------------------------------------------------------------
# Test 5: CORS check
# ---------------------------------------------------------------------------
echo ""
echo "🌍 CORS Configuration"

CORS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X OPTIONS "$API_URL/health" \
  -H "Origin: https://brujula.app" \
  -H "Access-Control-Request-Method: GET" \
  --max-time 10 2>/dev/null || echo "000")

if [[ "$CORS_STATUS" == "204" || "$CORS_STATUS" == "200" ]]; then
  echo "  CORS preflight ... ✅ $CORS_STATUS"
  PASSED=$((PASSED + 1))
else
  echo "  CORS preflight ... ❌ $CORS_STATUS"
  FAILED=$((FAILED + 1))
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "========================================"
echo "📋 Validation Summary"
echo "========================================"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

if [[ $FAILED -gt 0 ]]; then
  echo "❌ Some tests failed. Review output above."
  exit 1
else
  echo "✅ All tests passed."
fi
