#!/bin/bash
set -euo pipefail

# ---------------------------------------------------------------------------
# setup-secrets.sh
# Populate GCP Secret Manager from a local .env file.
#
# Usage:
#   ./setup-secrets.sh <env_file> <project_id> <env>
#
# Example:
#   ./setup-secrets.sh ../../.env my-gcp-project dev
# ---------------------------------------------------------------------------

ENV_FILE="${1:?Usage: setup-secrets.sh <env_file> <project_id> <env>}"
PROJECT_ID="${2:?Usage: setup-secrets.sh <env_file> <project_id> <env>}"
ENV="${3:?Usage: setup-secrets.sh <env_file> <project_id> <env>}"

# Map from .env variable names to Secret Manager secret names
declare -A SECRET_MAP=(
  ["JWT_SECRET_KEY"]="brujula-jwt-secret-key-${ENV}"
  ["ENCRYPTION_KEY"]="brujula-encryption-key-${ENV}"
  ["ANTHROPIC_API_KEY"]="brujula-anthropic-api-key-${ENV}"
  ["POSTGRES_PASSWORD"]="brujula-db-password-${ENV}"
  ["REDIS_PASSWORD"]="brujula-redis-password-${ENV}"
)

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Error: .env file not found at $ENV_FILE"
  exit 1
fi

echo "Populating Secret Manager for project=$PROJECT_ID env=$ENV"

for VAR_NAME in "${!SECRET_MAP[@]}"; do
  SECRET_NAME="${SECRET_MAP[$VAR_NAME]}"

  # Extract value from .env (handles KEY=VALUE and KEY="VALUE")
  VALUE=$(grep -E "^${VAR_NAME}=" "$ENV_FILE" | head -1 | cut -d'=' -f2- | tr -d '"' | tr -d "'")

  if [[ -z "$VALUE" ]]; then
    echo "Warning: $VAR_NAME not found in $ENV_FILE — skipping"
    continue
  fi

  # Create secret if it doesn't exist
  if ! gcloud secrets describe "$SECRET_NAME" --project="$PROJECT_ID" &>/dev/null; then
    echo "Creating secret: $SECRET_NAME"
    gcloud secrets create "$SECRET_NAME" --project="$PROJECT_ID" --replication-policy="automatic"
  fi

  # Add new version with the value
  echo "Adding version to: $SECRET_NAME"
  echo -n "$VALUE" | gcloud secrets versions add "$SECRET_NAME" \
    --project="$PROJECT_ID" \
    --data-file=-

  echo "  ✓ $VAR_NAME -> $SECRET_NAME"
done

echo ""
echo "All secrets populated successfully."
