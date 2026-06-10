# ---------------------------------------------------------------------------
# External HTTPS Load Balancer — routes traffic to Cloud Run services
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Serverless Network Endpoint Groups (NEGs)
# ---------------------------------------------------------------------------

resource "google_compute_region_network_endpoint_group" "api" {
  name                  = "brujula-api-neg-${var.env}"
  region                = var.region
  project               = var.project_id
  network_endpoint_type = "SERVERLESS"

  cloud_run {
    service = var.api_service_name
  }
}

resource "google_compute_region_network_endpoint_group" "web" {
  name                  = "brujula-web-neg-${var.env}"
  region                = var.region
  project               = var.project_id
  network_endpoint_type = "SERVERLESS"

  cloud_run {
    service = var.web_service_name
  }
}

# ---------------------------------------------------------------------------
# Backend services
# ---------------------------------------------------------------------------

resource "google_compute_backend_service" "api" {
  name                  = "brujula-api-backend-${var.env}"
  project               = var.project_id
  protocol              = "HTTP"
  port_name             = "http"
  timeout_sec           = 30
  connection_draining_timeout_sec = 10

  backend {
    group = google_compute_region_network_endpoint_group.api.id
  }

  log_config {
    enable      = true
    sample_rate = 1.0
  }
}

resource "google_compute_backend_service" "web" {
  name                  = "brujula-web-backend-${var.env}"
  project               = var.project_id
  protocol              = "HTTP"
  port_name             = "http"
  timeout_sec           = 30
  connection_draining_timeout_sec = 10

  backend {
    group = google_compute_region_network_endpoint_group.web.id
  }

  log_config {
    enable      = true
    sample_rate = 1.0
  }
}

# ---------------------------------------------------------------------------
# URL map — path-based routing
# ---------------------------------------------------------------------------

resource "google_compute_url_map" "main" {
  name            = "brujula-url-map-${var.env}"
  project         = var.project_id
  default_service = google_compute_backend_service.web.id

  host_rule {
    hosts        = [var.api_subdomain]
    path_matcher = "api"
  }

  host_rule {
    hosts        = [var.domain, "www.${var.domain}"]
    path_matcher = "web"
  }

  path_matcher {
    name            = "api"
    default_service = google_compute_backend_service.api.id
  }

  path_matcher {
    name            = "web"
    default_service = google_compute_backend_service.web.id
  }
}

# ---------------------------------------------------------------------------
# Managed SSL certificate
# ---------------------------------------------------------------------------

resource "google_managed_ssl_certificate" "main" {
  count   = var.ssl_certificate_self_link == "" ? 1 : 0
  name    = "brujula-ssl-${var.env}"
  project = var.project_id

  managed {
    domains = [var.domain, "www.${var.domain}", var.api_subdomain]
  }
}

locals {
  ssl_cert_self_link = var.ssl_certificate_self_link != "" ? var.ssl_certificate_self_link : google_managed_ssl_certificate.main[0].self_link
}

# ---------------------------------------------------------------------------
# HTTPS proxy
# ---------------------------------------------------------------------------

resource "google_compute_target_https_proxy" "main" {
  name             = "brujula-https-proxy-${var.env}"
  project          = var.project_id
  url_map          = google_compute_url_map.main.id
  ssl_certificates = [local.ssl_cert_self_link]
}

# ---------------------------------------------------------------------------
# Global forwarding rule
# ---------------------------------------------------------------------------

resource "google_compute_global_forwarding_rule" "https" {
  name       = "brujula-https-fr-${var.env}"
  project    = var.project_id
  target     = google_compute_target_https_proxy.main.id
  port_range = "443"
  ip_address = google_compute_global_address.lb_ip.address
}

# ---------------------------------------------------------------------------
# HTTP → HTTPS redirect
# ---------------------------------------------------------------------------

resource "google_compute_url_map" "http_redirect" {
  name    = "brujula-http-redirect-${var.env}"
  project = var.project_id

  default_url_redirect {
    https_redirect         = true
    redirect_response_code = "MOVED_PERMANENTLY_DEFAULT"
  }
}

resource "google_compute_target_http_proxy" "http_redirect" {
  name    = "brujula-http-proxy-${var.env}"
  project = var.project_id
  url_map = google_compute_url_map.http_redirect.id
}

resource "google_compute_global_forwarding_rule" "http" {
  name       = "brujula-http-fr-${var.env}"
  project    = var.project_id
  target     = google_compute_target_http_proxy.http_redirect.id
  port_range = "80"
  ip_address = google_compute_global_address.lb_ip.address
}

# ---------------------------------------------------------------------------
# Static IP for the load balancer
# ---------------------------------------------------------------------------

resource "google_compute_global_address" "lb_ip" {
  name    = "brujula-lb-ip-${var.env}"
  project = var.project_id
}
