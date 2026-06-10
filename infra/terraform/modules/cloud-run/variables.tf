variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for Cloud Run services"
  type        = string
}

variable "env" {
  description = "Environment name (dev, prod)"
  type        = string
}

# ---------------------------------------------------------------------------
# Service definitions
# ---------------------------------------------------------------------------

variable "api_image" {
  description = "Docker image for the API service"
  type        = string
}

variable "web_image" {
  description = "Docker image for the Web service"
  type        = string
}

# ---------------------------------------------------------------------------
# Networking
# ---------------------------------------------------------------------------

variable "vpc_connector_name" {
  description = "Serverless VPC Access connector name"
  type        = string
}

variable "cloud_run_sa_email" {
  description = "Service account email for Cloud Run services"
  type        = string
}

variable "cloud_sql_connection_name" {
  description = "Cloud SQL instance connection name"
  type        = string
}

# ---------------------------------------------------------------------------
# Environment variables (non-sensitive, injected directly)
# ---------------------------------------------------------------------------

variable "api_env_vars" {
  description = "Non-sensitive environment variables for the API service"
  type        = map(string)
  default     = {}
}

variable "web_env_vars" {
  description = "Non-sensitive environment variables for the Web service"
  type        = map(string)
  default     = {}
}

# ---------------------------------------------------------------------------
# Secret references (sensitive, mounted from Secret Manager)
# ---------------------------------------------------------------------------

variable "api_secret_vars" {
  description = "Secret Manager secret references for the API service (env var name => secret ID)"
  type        = map(string)
  default     = {}
}

variable "web_secret_vars" {
  description = "Secret Manager secret references for the Web service (env var name => secret ID)"
  type        = map(string)
  default     = {}
}

# ---------------------------------------------------------------------------
# Scaling
# ---------------------------------------------------------------------------

variable "api_max_instances" {
  description = "Maximum number of API instances"
  type        = number
  default     = 10
}

variable "web_max_instances" {
  description = "Maximum number of Web instances"
  type        = number
  default     = 10
}
