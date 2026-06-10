#!/bin/bash
set -euo pipefail

# ---------------------------------------------------------------------------
# cutover-dns.sh — Update Cloud DNS A records to point to Cloud Load Balancer
#
# Phase 5: DNS Cutover
# This script updates DNS records to route production traffic to GCP.
#
# Usage:
#   ./cutover-dns.sh \
#     --project <gcp-project> \
#     --lb-ip <load-balancer-ip> \
#     [--zone <dns-zone>] \
#     [--dry-run]
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Defaults
PROJECT=""
LB_IP=""
ZONE="brujula-app"
DRY_RUN=false
DOMAINS=("brujula.app" "www.brujula.app" "api.brujula.app")

usage() {
  cat <<EOF
Usage: $0 [OPTIONS]

Update Cloud DNS A records to point to Cloud Load Balancer IP.

Options:
  --project    GCP project ID (required)
  --lb-ip      Load Balancer IP address (required)
  --zone       Cloud DNS managed zone name (default: brujula-app)
  --dry-run    Show what would be changed without making changes
  --help       Show this help message
EOF
  exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --project) PROJECT="$2"; shift 2 ;;
    --lb-ip) LB_IP="$2"; shift 2 ;;
    --zone) ZONE="$2"; shift 2 ;;
    --dry-run) DRY_RUN=true; shift ;;
    --help) usage ;;
    *) echo "Unknown option: $1"; usage ;;
  esac
done

# Validate required arguments
if [[ -z "$PROJECT" || -z "$LB_IP" ]]; then
  echo "Error: --project and --lb-ip are required"
  usage
fi

echo "🧭 Brujula DNS Cutover"
echo "========================================"
echo "Project:     $PROJECT"
echo "LB IP:       $LB_IP"
echo "DNS Zone:    $ZONE"
echo "Domains:     ${DOMAINS[*]}"
echo "Dry Run:     $DRY_RUN"
echo "========================================"
echo ""

# ---------------------------------------------------------------------------
# Step 1: Get current DNS records (backup)
# ---------------------------------------------------------------------------
echo "📦 Step 1: Backing up current DNS records..."
BACKUP_FILE="/tmp/dns_backup_$(date +%Y%m%d_%H%M%S).json"

for domain in "${DOMAINS[@]}"; do
  RECORD_NAME="${domain}."
  echo -n "  $domain → "
  CURRENT=$(gcloud dns record-sets list \
    --project="$PROJECT" \
    --zone="$ZONE" \
    --filter="name=$RECORD_NAME AND type=A" \
    --format="json" 2>/dev/null || echo "[]")

  if [[ "$CURRENT" != "[]" ]]; then
    CURRENT_IP=$(echo "$CURRENT" | jq -r '.[0].rrdatas[0] // "none"')
    CURRENT_TTL=$(echo "$CURRENT" | jq -r '.[0].ttl // "none"')
    echo "$CURRENT_IP (TTL: $CURRENT_TTL)"
    echo "{\"domain\": \"$domain\", \"ip\": \"$CURRENT_IP\", \"ttl\": $CURRENT_TTL}" >> "$BACKUP_FILE"
  else
    echo "no existing record"
  fi
done

echo ""
echo "Backup saved: $BACKUP_FILE"
echo ""

# ---------------------------------------------------------------------------
# Step 2: Create DNS transaction
# ---------------------------------------------------------------------------
echo "📝 Step 2: Creating DNS transaction..."

if [[ "$DRY_RUN" == "true" ]]; then
  echo "  [DRY RUN] Would create transaction and update records:"
  for domain in "${DOMAINS[@]}"; do
    echo "    $domain A $LB_IP (TTL: 300)"
  done
else
  TRANSACTION_FILE="/tmp/dns_transaction.yaml"
  cat > "$TRANSACTION_FILE" <<YAML
additions:
YAML

  for domain in "${DOMAINS[@]}"; do
    cat >> "$TRANSACTION_FILE" <<YAML
- name: "${domain}."
  type: A
  ttl: 300
  rrdatas:
  - "${LB_IP}"
YAML
  done

  echo "  Transaction file: $TRANSACTION_FILE"
fi

# ---------------------------------------------------------------------------
# Step 3: Execute DNS transaction
# ---------------------------------------------------------------------------
echo ""
echo "🚀 Step 3: Applying DNS changes..."

if [[ "$DRY_RUN" == "true" ]]; then
  echo "  [DRY RUN] Would apply transaction to zone $ZONE"
else
  gcloud dns record-sets transaction start \
    --project="$PROJECT" \
    --zone="$ZONE" \
    --transaction-file="$TRANSACTION_FILE" \
    2>/dev/null || echo "  (transaction already started)"

  gcloud dns record-sets transaction execute \
    --project="$PROJECT" \
    --zone="$ZONE" \
    --transaction-file="$TRANSACTION_FILE"

  echo "  ✅ DNS transaction applied"
fi

# ---------------------------------------------------------------------------
# Step 4: Verify DNS propagation
# ---------------------------------------------------------------------------
echo ""
echo "🔍 Step 4: Verifying DNS records..."

sleep 5  # Wait for propagation

ALL_OK=true
for domain in "${DOMAINS[@]}"; do
  echo -n "  $domain → "
  RESOLVED=$(dig +short "$domain" A 2>/dev/null | head -1 || echo "unresolvable")
  if [[ "$RESOLVED" == "$LB_IP" ]]; then
    echo "✅ $RESOLVED"
  elif [[ "$DRY_RUN" == "true" ]]; then
    echo "⏭️  (dry run — skipping verification)"
  else
    echo "❌ $RESOLVED (expected $LB_IP)"
    ALL_OK=false
  fi
done

# ---------------------------------------------------------------------------
# Step 5: Verify HTTPS
# ---------------------------------------------------------------------------
echo ""
echo "🔒 Step 5: Verifying HTTPS..."

if [[ "$DRY_RUN" == "false" ]]; then
  for domain in "${DOMAINS[@]}"; do
    echo -n "  https://$domain → "
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://$domain" --max-time 15 2>/dev/null || echo "000")
    if [[ "$HTTP_STATUS" == "200" || "$HTTP_STATUS" == "301" || "$HTTP_STATUS" == "302" ]]; then
      echo "✅ $HTTP_STATUS"
    else
      echo "⚠️  $HTTP_STATUS (may need SSL cert propagation)"
    fi
  done
else
  echo "  [DRY RUN] Skipping HTTPS verification"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "========================================"
echo "📋 DNS Cutover Summary"
echo "========================================"
echo "Domains updated: ${#DOMAINS[@]}"
echo "New LB IP:       $LB_IP"
echo "Backup:          $BACKUP_FILE"
echo ""

if [[ "$ALL_OK" == "true" ]]; then
  echo "✅ DNS cutover complete. Production traffic is now on Cloud Run."
  echo ""
  echo "📌 Next steps:"
  echo "   1. Monitor Cloud Run logs for 24h"
  echo "   2. Keep VPS as cold standby for 7 days"
  echo "   3. If issues found, run: ./rollback.sh --project $PROJECT --vps-ip <VPS_IP>"
else
  echo "⚠️  Some DNS records may not have propagated yet."
  echo "   DNS propagation can take up to 48h. Re-run verification later:"
  echo "   dig +short brujula.app A"
  echo "   dig +short api.brujula.app A"
fi
