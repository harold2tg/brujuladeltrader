# ---------------------------------------------------------------------------
# Service Accounts
# ---------------------------------------------------------------------------

# Cloud Run service account — used by API and Web services
resource "google_service_account" "cloud_run" {
  account_id   = "brujula-cloud-run-${var.env}"
  display_name = "Brujula Cloud Run (${var.env})"
  project      = var.project_id
}

# Worker service account — used by the Celery worker VM
resource "google_service_account" "worker" {
  account_id   = "brujula-worker-${var.env}"
  display_name = "Brujula Worker (${var.env})"
  project      = var.project_id
}

# Cloud SQL service account — for Cloud SQL Admin API
resource "google_service_account" "cloud_sql" {
  account_id   = "brujula-cloud-sql-${var.env}"
  display_name = "Brujula Cloud SQL (${var.env})"
  project      = var.project_id
}

# ---------------------------------------------------------------------------
# IAM Bindings — Cloud Run SA
# ---------------------------------------------------------------------------

# Allow Cloud Run SA to act as itself (required for Cloud Run services)
resource "google_project_iam_member" "cloud_run_run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

# Cloud Run SA needs access to Secret Manager secrets
resource "google_project_iam_member" "cloud_run_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

# Cloud Run SA needs access to Cloud Storage for uploads
resource "google_project_iam_member" "cloud_run_storage_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

# Cloud Run SA needs Cloud SQL Client for database connections
resource "google_project_iam_member" "cloud_run_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

# ---------------------------------------------------------------------------
# IAM Bindings — Worker SA
# ---------------------------------------------------------------------------

# Worker SA needs access to Secret Manager
resource "google_project_iam_member" "worker_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.worker.email}"
}

# Worker SA needs access to Cloud Storage for file processing
resource "google_project_iam_member" "worker_storage_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.worker.email}"
}

# Worker SA needs Cloud SQL Client for database writes
resource "google_project_iam_member" "worker_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.worker.email}"
}

# Worker SA needs monitoring writer for logging
resource "google_project_iam_member" "worker_monitoring_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.worker.email}"
}
