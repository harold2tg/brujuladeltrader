output "cloud_run_sa_email" {
  description = "Cloud Run service account email"
  value       = google_service_account.cloud_run.email
}

output "worker_sa_email" {
  description = "Worker service account email"
  value       = google_service_account.worker.email
}

output "cloud_sql_sa_email" {
  description = "Cloud SQL service account email"
  value       = google_service_account.cloud_sql.email
}
