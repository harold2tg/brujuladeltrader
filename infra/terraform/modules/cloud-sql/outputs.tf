output "instance_connection_name" {
  description = "Cloud SQL instance connection name (for Cloud SQL Proxy and Cloud Run)"
  value       = google_sql_database_instance.main.connection_name
}

output "private_ip_address" {
  description = "Private IP address of the Cloud SQL instance"
  value       = google_sql_database_instance.main.private_ip_address
}

output "database_name" {
  description = "Name of the database"
  value       = google_sql_database.brujula.name
}

output "user_name" {
  description = "Database user name"
  value       = google_sql_user.brujula.name
}
