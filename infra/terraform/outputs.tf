output "vpc_id" {
  description = "VPC network self-link"
  value       = module.networking.vpc_id
}

output "vpc_connector_id" {
  description = "Serverless VPC Access connector ID"
  value       = module.networking.vpc_connector_id
}

output "subnet_id" {
  description = "Subnet self-link"
  value       = module.networking.subnet_id
}

output "cloud_run_sa_email" {
  description = "Cloud Run service account email"
  value       = module.iam.cloud_run_sa_email
}

output "worker_sa_email" {
  description = "Worker service account email"
  value       = module.iam.worker_sa_email
}

# ---------------------------------------------------------------------------
# Data layer outputs
# ---------------------------------------------------------------------------

output "cloud_sql_connection_name" {
  description = "Cloud SQL instance connection name"
  value       = module.cloud_sql.instance_connection_name
}

output "cloud_sql_private_ip" {
  description = "Cloud SQL private IP address"
  value       = module.cloud_sql.private_ip_address
}

output "redis_host" {
  description = "Memorystore Redis host IP"
  value       = module.memorystore.host
}

output "redis_port" {
  description = "Memorystore Redis port"
  value       = module.memorystore.port
}

output "uploads_bucket_name" {
  description = "GCS uploads bucket name"
  value       = module.storage.bucket_name
}

output "uploads_bucket_url" {
  description = "GCS uploads bucket URL"
  value       = module.storage.bucket_url
}
