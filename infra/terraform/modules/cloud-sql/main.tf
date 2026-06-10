# ---------------------------------------------------------------------------
# Cloud SQL — PostgreSQL 15 (db-f1-micro, private IP only)
# ---------------------------------------------------------------------------

resource "google_sql_database_instance" "main" {
  name             = "brujula-sql-${var.env}"
  database_version = "POSTGRES_15"
  region           = var.region
  project          = var.project_id

  settings {
    tier              = "db-f1-micro"
    availability_type = var.env == "prod" ? "REGIONAL" : "ZONAL"
    disk_type         = "PD_SSD"
    disk_size         = 10

    ip_configuration {
      ipv4_enabled    = false
      private_network = var.vpc_id
      require_ssl     = true
    }

    backup_configuration {
      enabled          = var.env == "prod" ? true : false
      start_time       = "03:00"
      point_in_time_recovery_enabled = var.env == "prod" ? true : false
    }

    maintenance_window {
      day  = 7
      hour = 4
    }

    user_labels = {
      env     = var.env
      project = "brujula"
    }
  }

  deletion_protection = var.env == "prod" ? true : false

  depends_on = [var.vpc_peering_connection]
}

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

resource "google_sql_database" "brujula" {
  name     = "brujula_db"
  instance = google_sql_database_instance.main.name
  project  = var.project_id
}

# ---------------------------------------------------------------------------
# User — authenticates via private IP (no password auth needed for private)
# ---------------------------------------------------------------------------

resource "google_sql_user" "brujula" {
  name     = "brujula"
  instance = google_sql_database_instance.main.name
  project  = var.project_id
  password = var.db_password
}
