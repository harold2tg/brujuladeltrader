terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "brujula-terraform-state"
    prefix = "infra"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ---------------------------------------------------------------------------
# Foundation modules
# ---------------------------------------------------------------------------

module "networking" {
  source     = "./modules/networking"
  project_id = var.project_id
  env        = var.env
  region     = var.region
}

module "iam" {
  source     = "./modules/iam"
  project_id = var.project_id
  env        = var.env
}

module "secret_manager" {
  source          = "./modules/secret-manager"
  project_id      = var.project_id
  env             = var.env
  cloud_run_sa    = module.iam.cloud_run_sa_email
}

# ---------------------------------------------------------------------------
# Data layer modules
# ---------------------------------------------------------------------------

module "cloud_sql" {
  source               = "./modules/cloud-sql"
  project_id           = var.project_id
  env                  = var.env
  region               = var.region
  vpc_id               = module.networking.vpc_id
  vpc_peering_connection = module.networking.vpc_peering_connection
  db_password          = var.db_password
}

module "memorystore" {
  source          = "./modules/memorystore"
  project_id      = var.project_id
  env             = var.env
  region          = var.region
  vpc_id          = module.networking.vpc_id
  redis_password  = var.redis_password
}

module "storage" {
  source     = "./modules/storage"
  project_id = var.project_id
  env        = var.env
  region     = var.region
}

# ---------------------------------------------------------------------------
# Compute layer modules
# ---------------------------------------------------------------------------

locals {
  # Construct DATABASE_URL for Cloud SQL (Unix socket via Cloud SQL Auth Proxy)
  cloud_sql_conn = module.cloud_sql.instance_connection_name
  db_user        = module.cloud_sql.user_name
  db_name        = module.cloud_sql.database_name

  # Redis URL from Memorystore
  redis_url = "redis://:${var.redis_password}@${module.memorystore.host}:${module.memorystore.port}/0"

  # Image paths (Artifact Registry)
  api_image = "${var.region}-docker.pkg.dev/${var.project_id}/brujula/api:latest"
  web_image = "${var.region}-docker.pkg.dev/${var.project_id}/brujula/web:latest"
  worker_image = "${var.region}-docker.pkg.dev/${var.project_id}/brujula/api:latest"

  # Shared env vars for API and worker
  api_env_vars = {
    APP_ENV            = var.env == "prod" ? "production" : "development"
    DEBUG              = var.env == "prod" ? "false" : "true"
    STORAGE_TYPE       = "gcs"
    GCS_BUCKET         = module.storage.bucket_name
    CORS_ORIGINS       = "https://${var.domain},https://www.${var.domain}"
    DATABASE_URL       = "postgresql+asyncpg://${local.db_user}@//cloudsql/${local.cloud_sql_conn}/${local.db_name}"
    DATABASE_URL_SYNC  = "postgresql://${local.db_user}@//cloudsql/${local.cloud_sql_conn}/${local.db_name}"
    REDIS_URL          = local.redis_url
  }

  web_env_vars = {
    NEXT_PUBLIC_API_URL      = "https://${var.api_subdomain}"
    NEXT_PUBLIC_DEFAULT_LOCALE = "es"
  }
}

module "cloud_run" {
  source     = "./modules/cloud-run"
  project_id = var.project_id
  region     = var.region
  env        = var.env

  api_image  = local.api_image
  web_image  = local.web_image

  vpc_connector_name       = module.networking.vpc_connector_name
  cloud_run_sa_email       = module.iam.cloud_run_sa_email
  cloud_sql_connection_name = module.cloud_sql.instance_connection_name

  api_env_vars  = local.api_env_vars
  web_env_vars  = local.web_env_vars

  api_secret_vars = {
    JWT_SECRET_KEY   = module.secret_manager.secret_ids["jwt_secret_key"]
    ENCRYPTION_KEY   = module.secret_manager.secret_ids["encryption_key"]
    APP_SECRET_KEY   = module.secret_manager.secret_ids["jwt_secret_key"]
  }

  api_max_instances = 10
  web_max_instances = 10
}

module "compute_worker" {
  source     = "./modules/compute-worker"
  project_id = var.project_id
  region     = var.region
  env        = var.env

  subnet_id         = module.networking.subnet_id
  worker_sa_email   = module.iam.worker_sa_email
  docker_image      = local.worker_image
  cloud_sql_connection_name = module.cloud_sql.instance_connection_name
  redis_host        = module.memorystore.host
  redis_port        = module.memorystore.port
  redis_password    = var.redis_password

  env_vars = {
    APP_ENV  = var.env == "prod" ? "production" : "development"
    DEBUG    = "false"
  }

  machine_type = "e2-micro"
  disk_size_gb = 10
}

module "load_balancer" {
  source     = "./modules/load-balancer"
  project_id = var.project_id
  region     = var.region
  env        = var.env

  api_service_name = module.cloud_run.api_service_name
  api_service_url  = module.cloud_run.api_service_url
  web_service_name = module.cloud_run.web_service_name
  web_service_url  = module.cloud_run.web_service_url

  domain         = var.domain
  api_subdomain  = var.api_subdomain
}
