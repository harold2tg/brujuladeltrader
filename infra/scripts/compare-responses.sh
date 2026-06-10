#!/bin/bash
set -euo pipefail

# ---------------------------------------------------------------------------
# compare-responses.sh — Send identical requests to VPS and Cloud Run,
#                         compare response status codes and JSON structure.
#
# Used during Phase 4 (parallel run) to verify Cloud Run parity with VPS.
#
# Usage:
#   ./compare-responses.sh \
#     --vps-url <https://brujula.app> \
#     --cloud-run-url <https://api-xxxxx-uc.a.run.app> \
#     [--auth-token <token>]
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Defaults
VPS_URL=""
CR_URL=""
AUTH_TOKEN=""
TESTS_RUN=0
TESTS_MATCHED=0
TESTS_DIFFER=0
REPORT_FILE="/tmp/brujula_compare_$(date +%Y%m%d_%H%M%S).txt"

usage() {
  cat <<EOF
Usage: $0 [OPTIONS]

Compare VPS and Cloud Run responses for parity validation.

Options:
  --vps-url          VPS base URL (required, e.g. https://brujula.app)
  --cloud-run-url    Cloud Run API base URL (required)
  --auth-token       JWT token for authenticated endpoints (optional)
  --report-file      Output report path (default: /tmp/brujula_compare_<timestamp>.txt)
  --help             Show this help message
EOF
  exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --vps-url) VPS_URL="$2"; shift 2 ;;
    --cloud-run-url) CR_URL="$2"; shift 2 ;;
    --auth-token) AUTH_TOKEN="$2"; shift 2 ;;
    --report-file) REPORT_FILE="$2"; shift 2 ;;
    --help) usage ;;
    *) echo "Unknown option: $1"; usage ;;
  esac
done

# Validate required arguments
if [[ -z "$VPS_URL" || -z "$CR_URL" ]]; then
  echo "Error: --vps-url and --cloud-run-url are required"
  usage
fi

# Remove trailing slashes
VPS_URL="${VPS_URL%/}"
CR_URL="${CR_URL%/}"

# ---------------------------------------------------------------------------
# Helper: compare a single endpoint
# ---------------------------------------------------------------------------
compare_endpoint() {
  local name="$1"
  local path="$2"
  local method="${3:-GET}"
  local data="${4:-}"

  TESTS_RUN=$((TESTS_RUN + 1))

  local curl_args=(-s -o /dev/null -w "%{http_code}" -X "$method" --max-time 15)
  if [[ -n "$data" ]]; then
    curl_args+=(-H "Content-Type: application/json" -d "$data")
  fi
  if [[ -n "$AUTH_TOKEN" ]]; then
    curl_args+=(-H "Authorization: Bearer $AUTH_TOKEN")
  fi

  # Make requests
  local vps_status cr_status
  vps_status=$(curl "${curl_args[@]}" "${VPS_URL}${path}" 2>/dev/null || echo "000")
  cr_status=$(curl "${curl_args[@]}" "${CR_URL}${path}" 2>/dev/null || echo "000")

  local match="✅ MATCH"
  if [[ "$vps_status" != "$cr_status" ]]; then
    match="❌ DIFFER"
    TESTS_DIFFER=$((TESTS_DIFFER + 1))
  else
    TESTS_MATCHED=$((TESTS_MATCHED + 1))
  fi

  echo "  [$name] VPS=$vps_status CR=$cr_status  $match"
  echo "[$name] VPS=$vps_status CR=$cr_status $match" >> "$REPORT_FILE"
}

# ---------------------------------------------------------------------------
# Helper: compare JSON structure (keys present in both)
# ---------------------------------------------------------------------------
compare_json_structure() {
  local name="$1"
  local path="$2"

  TESTS_RUN=$((TESTS_RUN + 1))

  local curl_args=(-s --max-time 15)
  if [[ -n "$AUTH_TOKEN" ]]; then
    curl_args+=(-H "Authorization: Bearer $AUTH_TOKEN")
  fi

  local vps_body cr_body
  vps_body=$(curl "${curl_args[@]}" "${VPS_URL}${path}" 2>/dev/null || echo "{}")
  cr_body=$(curl "${curl_args[@]}" "${CR_URL}${path}" 2>/dev/null || echo "{}")

  local vps_keys cr_keys
  vps_keys=$(echo "$vps_body" | jq -r 'keys[]' 2>/dev/null | sort || true)
  cr_keys=$(echo "$cr_body" | jq -r 'keys[]' 2>/dev/null | sort || true)

  if [[ "$vps_keys" == "$cr_keys" ]]; then
    echo "  [$name] JSON keys match ✅"
    echo "[$name] JSON keys match" >> "$REPORT_FILE"
    TESTS_MATCHED=$((TESTS_MATCHED + 1))
  else
    echo "  [$name] JSON keys differ ❌"
    echo "    VPS keys:  $(echo "$vps_keys" | tr '\n' ', ')"
    echo "    CR keys:   $(echo "$cr_keys" | tr '\n' ', ')"
    echo "[$name] JSON keys differ — VPS: $(echo "$vps_keys" | tr '\n' ',') CR: $(echo "$cr_keys" | tr '\n' ',')" >> "$REPORT_FILE"
    TESTS_DIFFER=$((TESTS_DIFFER + 1))
  fi
}

# ---------------------------------------------------------------------------
# Run comparisons
# ---------------------------------------------------------------------------
echo "🧭 Brujula Response Comparison"
echo "========================================"
echo "VPS:        $VPS_URL"
echo "Cloud Run:  $CR_URL"
echo "Report:     $REPORT_FILE"
echo "========================================"
echo ""

echo "📋 Starting comparison..."
echo "Comparison: $(date)" > "$REPORT_FILE"
echo "VPS: $VPS_URL" >> "$REPORT_FILE"
echo "CR:  $CR_URL" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Public endpoints
echo "📡 Public Endpoints"
compare_endpoint "GET /health" "/health" "GET"
compare_json_structure "GET /health (structure)" "/health"
echo ""

# Auth flow
echo "🔐 Auth Flow"
compare_endpoint "POST /auth/register" "/auth/register" "POST" \
  '{"email":"compare-test-'$(date +%s)'@brujula.test","password":"Test1234!","name":"Compare Test"}'

# Login (use fixed test user if available)
LOGIN_PAYLOAD='{"email":"compare-test@brujula.test","password":"Test1234!"}'
compare_endpoint "POST /auth/login" "/auth/login" "POST" "$LOGIN_PAYLOAD"
echo ""

# Authenticated endpoints (if token provided)
if [[ -n "$AUTH_TOKEN" ]]; then
  echo "🔒 Authenticated Endpoints"
  compare_endpoint "GET /uploads" "/uploads" "GET"
  compare_json_structure "GET /uploads (structure)" "/uploads"
  echo ""
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo "========================================"
echo "📊 Comparison Summary"
echo "========================================"
echo "Tests run:    $TESTS_RUN"
echo "Matched:      $TESTS_MATCHED"
echo "Differ:       $TESTS_DIFFER"
echo ""
echo "Report saved: $REPORT_FILE"

if [[ $TESTS_DIFFER -gt 0 ]]; then
  echo ""
  echo "⚠️  Some endpoints differ. Review the report for details."
  echo "   During parallel run, investigate each difference before DNS cutover."
  exit 1
else
  echo ""
  echo "✅ All endpoints match. Ready for DNS cutover."
fi
