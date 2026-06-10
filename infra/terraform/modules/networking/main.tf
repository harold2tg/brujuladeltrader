# ---------------------------------------------------------------------------
# VPC Network
# ---------------------------------------------------------------------------

resource "google_compute_network" "main" {
  name                    = "brujula-vpc-${var.env}"
  auto_create_subnetworks = false
  project                 = var.project_id
}

# ---------------------------------------------------------------------------
# Subnet — used by Cloud SQL private IP and the worker VM
# ---------------------------------------------------------------------------

resource "google_compute_subnetwork" "main" {
  name          = "brujula-subnet-${var.env}"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.main.id
  project       = var.project_id

  private_ip_google_access = true
}

# ---------------------------------------------------------------------------
# Private services access (required for Cloud SQL private IP)
# ---------------------------------------------------------------------------

resource "google_compute_global_address" "private_ip_range" {
  name          = "brujula-private-ip-${var.env}"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.main.id
  project       = var.project_id
}

resource "google_service_networking_connection" "private_vpc" {
  network                 = google_compute_network.main.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_range.name]
  project                 = var.project_id
}

# ---------------------------------------------------------------------------
# Serverless VPC Access Connector — allows Cloud Run to reach private IPs
# ---------------------------------------------------------------------------

resource "google_vpc_access_connector" "main" {
  name          = "brujula-connector-${var.env}"
  ip_cidr_range = "10.8.0.0/28"
  network       = google_compute_network.main.name
  region        = var.region
  project       = var.project_id

  machine_type = "e2-micro"

  min_instances = 2
  max_instances = 3
}

# ---------------------------------------------------------------------------
# Firewall Rules
# ---------------------------------------------------------------------------

# Allow internal traffic within the VPC
resource "google_compute_firewall" "allow_internal" {
  name    = "brujula-allow-internal-${var.env}"
  network = google_compute_network.main.name
  project = var.project_id

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "icmp"
  }

  source_ranges = ["10.0.0.0/8"]
  priority      = 1000
}

# Allow health checks from Google's health check ranges
resource "google_compute_firewall" "allow_health_checks" {
  name    = "brujula-allow-health-checks-${var.env}"
  network = google_compute_network.main.name
  project = var.project_id

  allow {
    protocol = "tcp"
    ports    = ["8000", "3000"]
  }

  source_ranges = [
    "35.191.0.0/16",  # Google health check range
    "130.211.0.0/22", # Google health check range
  ]

  target_tags = ["allow-health-check"]
  priority    = 1000
}

# Allow SSH to worker VM (restrict to your IP in production)
resource "google_compute_firewall" "allow_ssh" {
  name    = "brujula-allow-ssh-${var.env}"
  network = google_compute_network.main.name
  project = var.project_id

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["allow-ssh"]
  priority      = 2000
}
