# ---------------------------------------------------------------------------
# Compute Engine — Celery Worker (e2-micro)
# ---------------------------------------------------------------------------

locals {
  zone = var.zone != "" ? var.zone : "${var.region}-a"
}

resource "google_compute_instance" "worker" {
  name         = "brujula-worker-${var.env}"
  machine_type = var.machine_type
  zone         = local.zone
  project      = var.project_id

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
      size  = var.disk_size_gb
      type  = "pd-standard"
    }
  }

  network_interface {
    subnetwork = var.subnet_id

    # Ephemeral public IP for pulling images and updates
    access_config {}
  }

  service_account {
    email = var.worker_sa_email
    scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
    ]
  }

  tags = ["allow-ssh"]

  metadata = {
    startup-script = templatefile("${path.module}/startup.sh.tpl", {
      docker_image        = var.docker_image
      cloud_sql_connection = var.cloud_sql_connection_name
      redis_host          = var.redis_host
      redis_port          = var.redis_port
      redis_password      = var.redis_password
      env_vars_json       = jsonencode(var.env_vars)
    })
  }

  labels = {
    env     = var.env
    project = "brujula"
    role    = "celery-worker"
  }

  # Allow stopping for maintenance (preemptible)
  allow_stopping_for_update = true

  # Preemptible for cost savings (~60% cheaper)
  scheduling {
    preemptible       = true
    automatic_restart = false
  }
}
