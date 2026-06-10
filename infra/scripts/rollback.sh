#!/bin/bash
set -euo pipefail

# ---------------------------------------------------------------------------
# rollback.sh — Emergency rollback: revert DNS to VPS IP
#
# Reverts Cloud DNS A records to point back to the VPS, effectively routing
# production traffic away from Cloud Run.
#
# Usage:
#   ./rollback.sh \
#     --project <gcp-project> \
#     --vps-ip <vps-ip-address> \
#     [--zone <dns-zone>]
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Defaults
PROJECT=""
VPS_IP=""
ZONE="brujula-app"
DOMAINS=("brujula.app" "www.brujula.app" "api.brujula.app")

usage() {
  cat <<EOF
Usage: $0 [OPTIONS]

Emergency rollback: revert DNS to VPS IP.

Options:
  --project    GCP project ID (required)
  --vps-ip     VPS IP address to revert DNS to (required)
  --zone       Cloud DNS managed zone name (default: brujula-app)
  --help       Show this help message
EOF
  exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --project) PROJECT="$2"; shift 2 ;;
    --vps-ip) VPS_IP="$2"; shift 2 ;;
    --zone) ZONE="$2"; shift 2 ;;
    --help) usage ;;
    *) echo "Unknown option: $1"; usage ;;
  esac
done

# Validate required arguments
if [[ -z "$PROJECT" || -z "$VPS_IP" ]]; then
  echo "Error: --project and --vps-ip are required"
  usage
fi

echo "🚨 Brujula DNS Rollback"
echo "========================================"
echo "Project:     $PROJECT"
echo "Revert to:   $VPS_IP"
echo "DNS Zone:    $ZONE"
echo "Domains:     ${DOMAINS[*]}"
echo "========================================"
echo ""
echo "⚠️  This will route ALL production traffic back to the VPS."
echo ""
read -p "Continue? (yes/no): " CONFIRM
if [[ "$CONFIRM" != "yes" ]]; then
  echo "Aborted."
  exit 0
fi

# ---------------------------------------------------------------------------
# Step 1: Create rollback transaction
# ---------------------------------------------------------------------------
echo ""
echo "📝 Step 1: Creating rollback transaction..."

TRANSACTION_FILE="/tmp/dns_rollback_transaction.yaml"
cat > "$TRANSACTION_FILE" <<YAML
additions:
YAML

for domain in "${DOMAINS[@]}"; do
  cat >> "$TRANSACTION_FILE" <<YAML
- name: "${domain}."
  type: A
  ttl: 300
  rrdatas:
  - "${VPS_IP}"
YAML
done

echo "  Transaction file: $TRANSACTION_FILE"

# ---------------------------------------------------------------------------
# Step 2: Execute rollback transaction
# ---------------------------------------------------------------------------
echo ""
echo "🔄 Step 2: Applying rollback..."

gcloud dns record-sets transaction start \
  --project="$PROJECT" \
  --zone="$ZONE" \
  --transaction-file="$TRANSACTION_FILE" \
  2>/dev/null || echo "  (transaction already started)"

gcloud dns record-sets transaction execute \
  --project="$PROJECT" \
  --zone="$ZONE" \
  --transaction-file="$TRANSACTION_FILE"

echo "  ✅ Rollback applied"

# ---------------------------------------------------------------------------
# Step 3: Verify rollback
# ---------------------------------------------------------------------------
echo ""
echo "🔍 Step 3: Verifying rollback..."

sleep 5

ALL_OK=true
for domain in "${DOMAINS[@]}"; do
  echo -n "  $domain → "
  RESOLVED=$(dig +short "$domain" A 2>/dev/null | head -1 || echo "unresolvable")
  if [[ "$RESOLVED" == "$VPS_IP" ]]; then
    echo "✅ $RESOLVED (VPS)"
  else
    echo "❌ $RESOLVED (expected $VPS_IP)"
    ALL_OK=false
  fi
done

# ---------------------------------------------------------------------------
# Step 4: Verify VPS is responding
# ---------------------------------------------------------------------------
echo ""
echo "🌐 Step 4: Verifying VPS endpoints..."

for domain in "brujula.app" "api.brujula.app"; do
  echo -n "  https://$domain → "
  HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://$domain" --max-time 15 2>/dev/null || echo "000")
  if [[ "$HTTP_STATUS" == "200" || "$HTTP_STATUS" == "301" || "$HTTP_STATUS" == "302" ]]; then
    echo "✅ $HTTP_STATUS"
  else
    echo "⚠️  $HTTP_STATUS"
  fi
done

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "========================================"
echo "📋 Rollback Summary"
echo "========================================"
echo "Domains reverted: ${#DOMAINS[@]}"
echo "VPS IP:           $VPS_IP"

if [[ "$ALL_OK" == "true" ]]; then
  echo ""
  echo "✅ Rollback complete. Production traffic is now on VPS."
  echo ""
  echo "📌 Post-rollback actions:"
  echo "   1. Investigate Cloud Run issues before retrying migration"
  echo "   2. VPS is serving production traffic"
  echo "   3. Cloud Run can be kept running for debugging (no traffic)"
else
  echo ""
  echo "⚠️  Rollback applied but DNS propagation may be incomplete."
  echo "   Check again in a few minutes: dig +short brujula.app A"
fi
