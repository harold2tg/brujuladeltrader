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
