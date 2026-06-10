# ---------------------------------------------------------------------------
# Memorystore — Redis 7 Basic Tier, 1GB, private IP
# ---------------------------------------------------------------------------

resource "google_redis_instance" "main" {
  name           = "brujula-redis-${var.env}"
  display_name   = "Brujula Redis ${var.env}"
  tier           = "BASIC"
  memory_size_gb = 1
  region         = var.region
  project        = var.project_id

  redis_version = "REDIS_7_0"
  auth_enabled  = true
  auth_string   = var.redis_password

  transit_encryption_mode = "SERVER_AUTHENTICATION"

  authorized_network = var.vpc_id

  redis_configs = {
    maxmemory-policy = "allkeys-lru"
    notify-keyspace-events = ""
  }

  labels = {
    env     = var.env
    project = "brujula"
  }
}
