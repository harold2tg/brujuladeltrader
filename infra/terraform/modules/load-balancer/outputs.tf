output "lb_ip_address" {
  description = "Load balancer static IP address"
  value       = google_compute_global_address.lb_ip.address
}

output "lb_ip_name" {
  description = "Load balancer static IP resource name"
  value       = google_compute_global_address.lb_ip.name
}

output "https_proxy_name" {
  description = "HTTPS proxy name"
  value       = google_compute_target_https_proxy.main.name
}

output "url_map_name" {
  description = "URL map name"
  value       = google_compute_url_map.main.name
}
