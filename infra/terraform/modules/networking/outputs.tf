output "vpc_id" {
  description = "VPC network self-link"
  value       = google_compute_network.main.self_link
}

output "subnet_id" {
  description = "Subnet self-link"
  value       = google_compute_subnetwork.main.self_link
}

output "vpc_connector_id" {
  description = "Serverless VPC Access connector self-link"
  value       = google_vpc_access_connector.main.self_link
}

output "vpc_connector_name" {
  description = "Serverless VPC Access connector name (for Cloud Run)"
  value       = google_vpc_access_connector.main.name
}
