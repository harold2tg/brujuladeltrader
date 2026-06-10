variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "env" {
  description = "Environment name (dev, prod)"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "vpc_id" {
  description = "VPC network self-link for authorized network"
  type        = string
}

variable "redis_password" {
  description = "Password for Redis authentication"
  type        = string
  sensitive   = true
}
