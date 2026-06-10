output "bucket_name" {
  description = "GCS bucket name"
  value       = google_storage_bucket.uploads.name
}

output "bucket_url" {
  description = "GCS bucket URL"
  value       = google_storage_bucket.uploads.url
}

output "bucket_self_link" {
  description = "GCS bucket self-link"
  value       = google_storage_bucket.uploads.self_link
}
