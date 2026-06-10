output "api_service_name" {
  description = "Cloud Run API service name"
  value       = google_cloud_run_v2_service.api.name
}

output "api_service_url" {
  description = "Cloud Run API service URL"
  value       = google_cloud_run_v2_service.api.uri
}

output "web_service_name" {
  description = "Cloud Run Web service name"
  value       = google_cloud_run_v2_service.web.name
}

output "web_service_url" {
  description = "Cloud Run Web service URL"
  value       = google_cloud_run_v2_service.web.uri
}
