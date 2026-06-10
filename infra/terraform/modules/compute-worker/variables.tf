variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for the worker VM"
  type        = string
}

variable "env" {
  description = "Environment name (dev, prod)"
  type        = string
}

variable "zone" {
  description = "GCP zone for the worker VM (defaults to region + 'a')"
  type        = string
  default     = ""
}

# ---------------------------------------------------------------------------
# Networking
# ---------------------------------------------------------------------------

variable "subnet_id" {
  description = "Subnet self-link for the worker VM"
  type        = string
}

variable "worker_sa_email" {
  description = "Service account email for the worker VM"
  type        = string
}

# ---------------------------------------------------------------------------
# Container configuration
# ---------------------------------------------------------------------------

variable "docker_image" {
  description = "Docker image for the Celery worker"
  type        = string
}

variable "cloud_sql_connection_name" {
  description = "Cloud SQL instance connection name"
  type        = string
}

# ---------------------------------------------------------------------------
# Environment variables
# ---------------------------------------------------------------------------

variable "env_vars" {
  description = "Environment variables for the worker (non-sensitive)"
  type        = map(string)
  default     = {}
}

variable "redis_host" {
  description = "Memorystore Redis host IP"
  type        = string
}

variable "redis_port" {
  description = "Memorystore Redis port"
  type        = number
  default     = 6379
}

variable "redis_password" {
  description = "Memorystore Redis password"
  type        = string
  sensitive   = true
}

# ---------------------------------------------------------------------------
# Machine configuration
# ---------------------------------------------------------------------------

variable "machine_type" {
  description = "Compute Engine machine type"
  type        = string
  default     = "e2-micro"
}

variable "disk_size_gb" {
  description = "Boot disk size in GB"
  type        = number
  default     = 10
}
