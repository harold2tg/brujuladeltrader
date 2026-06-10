#!/bin/bash
set -euo pipefail

# ---------------------------------------------------------------------------
# migrate-db.sh — Migrate PostgreSQL data from VPS to Cloud SQL
#
# Usage:
#   ./scripts/migrate-db.sh \
#     --vps-host <IP> \
#     --vps-user <user> \
#     --cloud-sql-ip <private-ip> \
#     --db-name brujula_db \
#     --db-user brujula \
#     --db-password <password>
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/tmp/brujula_migration_${TIMESTAMP}"

# Defaults
VPS_HOST=""
VPS_USER="ubuntu"
CLOUD_SQL_IP=""
DB_NAME="brujula_db"
DB_USER="brujula"
DB_PASSWORD=""
VPS_DB_PORT=5432
CLOUD_SQL_PORT=5432

usage() {
  cat <<EOF
Usage: $0 [OPTIONS]

Migrate PostgreSQL data from VPS to Cloud SQL.

Options:
  --vps-host       VPS IP address (required)
  --vps-user       VPS SSH user (default: ubuntu)
  --cloud-sql-ip   Cloud SQL private IP (required)
  --db-name        Database name (default: brujula_db)
  --db-user        Database user (default: brujula)
  --db-password    Database password (required)
  --help           Show this help message
EOF
  exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --vps-host) VPS_HOST="$2"; shift 2 ;;
    --vps-user) VPS_USER="$2"; shift 2 ;;
    --cloud-sql-ip) CLOUD_SQL_IP="$2"; shift 2 ;;
    --db-name) DB_NAME="$2"; shift 2 ;;
    --db-user) DB_USER="$2"; shift 2 ;;
    --db-password) DB_PASSWORD="$2"; shift 2 ;;
    --help) usage ;;
    *) echo "Unknown option: $1"; usage ;;
  esac
done

# Validate required arguments
if [[ -z "$VPS_HOST" || -z "$CLOUD_SQL_IP" || -z "$DB_PASSWORD" ]]; then
  echo "❌ Error: --vps-host, --cloud-sql-ip, and --db-password are required"
  usage
fi

echo "🧭 Brujula DB Migration — VPS → Cloud SQL"
echo "================================================"
echo "VPS Host:     $VPS_HOST"
echo "VPS User:     $VPS_USER"
echo "Cloud SQL IP: $CLOUD_SQL_IP"
echo "Database:     $DB_NAME"
echo "User:         $DB_USER"
echo "================================================"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# ---------------------------------------------------------------------------
# Step 1: pg_dump from VPS
# ---------------------------------------------------------------------------
echo ""
echo "📦 Step 1: Dumping database from VPS..."

ssh "$VPS_USER@$VPS_HOST" \
  "PGPASSWORD=\$POSTGRES_PASSWORD pg_dump -h localhost -p $VPS_DB_PORT -U \$POSTGRES_USER -d $DB_NAME --no-owner --no-privileges" \
  | gzip > "$BACKUP_DIR/dump.sql.gz"

DUMP_SIZE=$(du -h "$BACKUP_DIR/dump.sql.gz" | cut -f1)
echo "✅ Dump completed: $DUMP_SIZE"

# Get row counts from VPS for verification
echo "📊 Getting row counts from VPS..."
VPS_COUNTS=$(ssh "$VPS_USER@$VPS_HOST" \
  "PGPASSWORD=\$POSTGRES_PASSWORD psql -h localhost -p $VPS_DB_PORT -U \$POSTGRES_USER -d $DB_NAME -t -c \"SELECT tablename, n_live_tup FROM pg_stat_user_tables ORDER BY tablename;\"" 2>/dev/null || echo "Could not retrieve counts")
echo "$VPS_COUNTS" > "$BACKUP_DIR/vps_row_counts.txt"
echo "✅ VPS row counts saved"

# ---------------------------------------------------------------------------
# Step 2: pg_restore to Cloud SQL
# ---------------------------------------------------------------------------
echo ""
echo "📥 Step 2: Restoring to Cloud SQL..."

# Decompress and pipe to psql (Cloud SQL via private IP)
gunzip -c "$BACKUP_DIR/dump.sql.gz" | \
  PGPASSWORD="$DB_PASSWORD" psql \
    -h "$CLOUD_SQL_IP" \
    -p "$CLOUD_SQL_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --no-owner \
    --no-privileges \
    -q

echo "✅ Restore completed"

# ---------------------------------------------------------------------------
# Step 3: Verify row counts
# ---------------------------------------------------------------------------
echo ""
echo "🔍 Step 3: Verifying row counts..."

CLOUD_COUNTS=$(PGPASSWORD="$DB_PASSWORD" psql \
  -h "$CLOUD_SQL_IP" \
  -p "$CLOUD_SQL_PORT" \
  -U "$DB_USER" \
  -d "$DB_NAME" \
  -t -c "SELECT tablename, n_live_tup FROM pg_stat_user_tables ORDER BY tablename;" 2>/dev/null || echo "Could not retrieve counts")
echo "$CLOUD_COUNTS" > "$BACKUP_DIR/cloud_row_counts.txt"

echo ""
echo "📊 VPS Row Counts:"
cat "$BACKUP_DIR/vps_row_counts.txt"
echo ""
echo "📊 Cloud SQL Row Counts:"
cat "$BACKUP_DIR/cloud_row_counts.txt"

# ---------------------------------------------------------------------------
# Step 4: Compare checksums (if both are available)
# ---------------------------------------------------------------------------
echo ""
echo "🔗 Step 4: Comparing table counts..."

if [[ "$VPS_COUNTS" != *"Could not retrieve counts"* && "$CLOUD_COUNTS" != *"Could not retrieve counts"* ]]; then
  # Simple comparison - check if counts match
  VPS_SUM=$(echo "$VPS_COUNTS" | awk '{sum += $2} END {print sum}')
  CLOUD_SUM=$(echo "$CLOUD_COUNTS" | awk '{sum += $2} END {print sum}')

  if [[ "$VPS_SUM" == "$CLOUD_SUM" ]]; then
    echo "✅ Row counts match: $VPS_SUM total rows"
  else
    echo "⚠️  Row counts differ: VPS=$VPS_SUM, Cloud SQL=$CLOUD_SUM"
    echo "   Manual verification recommended."
  fi
else
  echo "⚠️  Could not compare counts — verify manually"
fi

# ---------------------------------------------------------------------------
# Step 5: Verify key tables exist
# ---------------------------------------------------------------------------
echo ""
echo "🔍 Step 5: Verifying key tables..."

EXPECTED_TABLES=("users" "uploads" "trades" "analysis_results" "alert_rules")
MISSING_TABLES=()

for table in "${EXPECTED_TABLES[@]}"; do
  TABLE_EXISTS=$(PGPASSWORD="$DB_PASSWORD" psql \
    -h "$CLOUD_SQL_IP" \
    -p "$CLOUD_SQL_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -t -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '$table');" 2>/dev/null | tr -d '[:space:]')

  if [[ "$TABLE_EXISTS" == "t" ]]; then
    echo "  ✅ $table"
  else
    echo "  ❌ $table — MISSING"
    MISSING_TABLES+=("$table")
  fi
done

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "================================================"
echo "📋 Migration Summary"
echo "================================================"
echo "Backup location: $BACKUP_DIR"
echo "Backup size:     $DUMP_SIZE"

if [[ ${#MISSING_TABLES[@]} -eq 0 ]]; then
  echo "Status:          ✅ All tables present"
else
  echo "Status:          ⚠️  Missing tables: ${MISSING_TABLES[*]}"
fi

echo ""
echo "🧹 To cleanup backup files:"
echo "   rm -rf $BACKUP_DIR"
echo ""
echo "✅ Migration complete!"
