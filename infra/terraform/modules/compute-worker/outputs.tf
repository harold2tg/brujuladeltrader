output "vm_name" {
  description = "Worker VM instance name"
  value       = google_compute_instance.worker.name
}

output "vm_external_ip" {
  description = "Worker VM external IP address"
  value       = google_compute_instance.worker.network_interface[0].access_config[0].nat_ip
}

output "vm_internal_ip" {
  description = "Worker VM internal IP address"
  value       = google_compute_instance.worker.network_interface[0].network_ip
}

output "vm_zone" {
  description = "Worker VM zone"
  value       = google_compute_instance.worker.zone
}
