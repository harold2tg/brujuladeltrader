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
  description = "VPC network self-link for private IP"
  type        = string
}

variable "vpc_peering_connection" {
  description = "VPC peering connection for private services access"
  type        = any
}

variable "db_password" {
  description = "Password for the brujula database user"
  type        = string
  sensitive   = true
}
