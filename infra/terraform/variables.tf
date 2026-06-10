variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for all resources"
  type        = string
  default     = "us-central1"
}

variable "env" {
  description = "Environment name (dev, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "prod"], var.env)
    error_message = "env must be 'dev' or 'prod'."
  }
}

variable "db_password" {
  description = "Password for the Cloud SQL brujula user"
  type        = string
  sensitive   = true
}

variable "redis_password" {
  description = "Password for Memorystore Redis authentication"
  type        = string
  sensitive   = true
}

variable "domain" {
  description = "Primary domain (e.g. brujula.app)"
  type        = string
  default     = "brujula.app"
}

variable "api_subdomain" {
  description = "API subdomain (e.g. api.brujula.app)"
  type        = string
  default     = "api.brujula.app"
}
