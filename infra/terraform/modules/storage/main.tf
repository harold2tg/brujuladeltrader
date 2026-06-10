# ---------------------------------------------------------------------------
# Cloud Storage — GCS bucket for uploads
# ---------------------------------------------------------------------------

resource "google_storage_bucket" "uploads" {
  name          = "brujula-uploads-${var.env}"
  location      = var.region
  project       = var.project_id
  storage_class = "STANDARD"
  uniform_bucket_level_access = true

  versioning {
    enabled = false
  }

  # Lifecycle rules — delete old uploads after 90 days
  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 90
    }
  }

  # Lifecycle rules — move to Nearline after 30 days
  lifecycle_rule {
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
    condition {
      age = 30
    }
  }

  labels = {
    env     = var.env
    project = "brujula"
  }

  force_destroy = var.env != "prod"
}

# ---------------------------------------------------------------------------
# CORS configuration for web uploads
# ---------------------------------------------------------------------------

resource "google_storage_bucket_iam_member" "public_read" {
  count  = var.env == "dev" ? 1 : 0
  bucket = google_storage_bucket.uploads.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}
