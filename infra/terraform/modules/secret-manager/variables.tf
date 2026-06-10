variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "env" {
  description = "Environment name (dev, prod)"
  type        = string
}

variable "cloud_run_sa" {
  description = "Cloud Run service account email to grant secret access"
  type        = string
}
