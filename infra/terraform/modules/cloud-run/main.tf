# ---------------------------------------------------------------------------
# Cloud Run — API service (FastAPI :8000)
# ---------------------------------------------------------------------------

resource "google_cloud_run_v2_service" "api" {
  name     = "brujula-api-${var.env}"
  location = var.region
  project  = var.project_id

  template {
    service_account = var.cloud_run_sa_email

    scaling {
      min_instance_count = 0
      max_instance_count = var.api_max_instances
    }

    vpc_access {
      connector = var.vpc_connector_name
      egress    = "ALL_TRAFFIC"
    }

    annotations = {
      "run.googleapis.com/cloudsql-instances" = var.cloud_sql_connection_name
    }

    containers {
      image = var.api_image

      ports {
        container_port = 8000
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      # Non-sensitive environment variables
      dynamic "env" {
        for_each = var.api_env_vars
        content {
          name  = env.key
          value = env.value
        }
      }

      # Sensitive environment variables from Secret Manager
      dynamic "env" {
        for_each = var.api_secret_vars
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value
              version = "latest"
            }
          }
        }
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Allow unauthenticated access (public API)
resource "google_cloud_run_v2_service_iam_member" "api_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ---------------------------------------------------------------------------
# Cloud Run — Web service (Next.js :3000)
# ---------------------------------------------------------------------------

resource "google_cloud_run_v2_service" "web" {
  name     = "brujula-web-${var.env}"
  location = var.region
  project  = var.project_id

  template {
    service_account = var.cloud_run_sa_email

    scaling {
      min_instance_count = 0
      max_instance_count = var.web_max_instances
    }

    vpc_access {
      connector = var.vpc_connector_name
      egress    = "ALL_TRAFFIC"
    }

    containers {
      image = var.web_image

      ports {
        container_port = 3000
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      # Non-sensitive environment variables
      dynamic "env" {
        for_each = var.web_env_vars
        content {
          name  = env.key
          value = env.value
        }
      }

      # Sensitive environment variables from Secret Manager
      dynamic "env" {
        for_each = var.web_secret_vars
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value
              version = "latest"
            }
          }
        }
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Allow unauthenticated access (public web frontend)
resource "google_cloud_run_v2_service_iam_member" "web_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.web.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
