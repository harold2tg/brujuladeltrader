variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for the load balancer"
  type        = string
}

variable "env" {
  description = "Environment name (dev, prod)"
  type        = string
}

# ---------------------------------------------------------------------------
# Cloud Run service URLs (for serverless NEG backends)
# ---------------------------------------------------------------------------

variable "api_service_name" {
  description = "Cloud Run API service name"
  type        = string
}

variable "api_service_url" {
  description = "Cloud Run API service URL (for NEG)"
  type        = string
}

variable "web_service_name" {
  description = "Cloud Run Web service name"
  type        = string
}

variable "web_service_url" {
  description = "Cloud Run Web service URL (for NEG)"
  type        = string
}

# ---------------------------------------------------------------------------
# Domain configuration
# ---------------------------------------------------------------------------

variable "domain" {
  description = "Primary domain (e.g. brujula.app)"
  type        = string
}

variable "api_subdomain" {
  description = "API subdomain (e.g. api.brujula.app)"
  type        = string
}

# ---------------------------------------------------------------------------
# SSL certificate
# ---------------------------------------------------------------------------

variable "managed_ssl_certificate_id" {
  description = "Managed SSL certificate resource ID (created externally via Google-managed cert)"
  type        = string
  default     = ""
}

variable "ssl_certificate_self_link" {
  description = "Self-link of the SSL certificate to use"
  type        = string
  default     = ""
}
