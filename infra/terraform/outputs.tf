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
