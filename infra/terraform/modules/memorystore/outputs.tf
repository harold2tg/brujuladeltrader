output "host" {
  description = "Redis host IP address"
  value       = google_redis_instance.main.host
}

output "port" {
  description = "Redis port"
  value       = google_redis_instance.main.port
}

output "name" {
  description = "Redis instance name"
  value       = google_redis_instance.main.name
}

output "auth_string" {
  description = "Redis auth string (password)"
  value       = google_redis_instance.main.auth_string
  sensitive   = true
}
