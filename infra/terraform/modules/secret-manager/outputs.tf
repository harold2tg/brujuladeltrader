output "secret_ids" {
  description = "Map of secret names to their Secret Manager IDs"
  value = {
    jwt_secret_key     = google_secret_manager_secret.jwt_secret_key.secret_id
    encryption_key     = google_secret_manager_secret.encryption_key.secret_id
    anthropic_api_key  = google_secret_manager_secret.anthropic_api_key.secret_id
    db_password        = google_secret_manager_secret.db_password.secret_id
    redis_password     = google_secret_manager_secret.redis_password.secret_id
  }
}
