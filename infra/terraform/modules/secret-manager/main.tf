# ---------------------------------------------------------------------------
# Secrets — populated via setup-secrets.sh after initial apply
# ---------------------------------------------------------------------------

resource "google_secret_manager_secret" "jwt_secret_key" {
  secret_id = "brujula-jwt-secret-key-${var.env}"
  project   = var.project_id

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "encryption_key" {
  secret_id = "brujula-encryption-key-${var.env}"
  project   = var.project_id

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "anthropic_api_key" {
  secret_id = "brujula-anthropic-api-key-${var.env}"
  project   = var.project_id

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "db_password" {
  secret_id = "brujula-db-password-${var.env}"
  project   = var.project_id

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "redis_password" {
  secret_id = "brujula-redis-password-${var.env}"
  project   = var.project_id

  replication {
    auto {}
  }
}

# ---------------------------------------------------------------------------
# IAM Bindings — Cloud Run SA can read all secrets
# ---------------------------------------------------------------------------

locals {
  secrets = [
    google_secret_manager_secret.jwt_secret_key,
    google_secret_manager_secret.encryption_key,
    google_secret_manager_secret.anthropic_api_key,
    google_secret_manager_secret.db_password,
    google_secret_manager_secret.redis_password,
  ]
}

resource "google_secret_manager_secret_iam_member" "cloud_run_access" {
  for_each = { for s in local.secrets : s.secret_id => s }

  secret_id = each.value.secret_id
  project   = var.project_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.cloud_run_sa}"
}
