# Design: GCP + Terraform + Cloud Run + Cloud SQL

## Technical Approach

Migrate from single-VPS Docker Compose to GCP serverless managed services using Terraform for infrastructure-as-code. API and Web run on Cloud Run; the Celery worker runs on a minimal Compute Engine VM (e2-micro, preemptible) since Celery needs a persistent process. Cloud SQL replaces self-hosted Postgres, Memorystore replaces Redis, Cloud Storage replaces the local uploads volume. Migration is phased: infra first, then containers, then data, then DNS cutover.

## Architecture Decisions

### Decision: Cloud Run for stateless services

| Option | Tradeoff | Decision |
|--------|----------|----------|
| **Cloud Run** | Auto-scaling to zero, managed infra, pay-per-request. Max 60s request timeout (can be extended to 60m). No persistent process support. | ✅ **Chosen** — API and Web are stateless HTTP services. Perfect fit. |
| GKE | Full control, persistent pods, but high ops overhead for a single developer. | ❌ Overkill for MVP |
| Compute Engine | Full control, persistent VMs, but requires manual scaling and OS maintenance. | ❌ More ops than needed for HTTP services |

### Decision: Compute Engine for Celery worker

| Option | Tradeoff | Decision |
|--------|----------|----------|
| **Compute Engine (e2-micro)** | ~$7/mo, persistent process needed by Celery, simple migration path. | ✅ **Chosen** — pragmatic for MVP. No code changes. |
| Cloud Run (with Cloud Tasks) | True serverless, but requires refactoring from Celery to Cloud Tasks. Full rewrite of task system. | ❌ Split into separate change post-MVP |
| Cloud Run Jobs | No persistent process — jobs run and exit. Not compatible with Celery's long-lived worker model. | ❌ Incompatible architecture |

### Decision: Single GCP project (dev and prod in same project)

| Option | Tradeoff | Decision |
|--------|----------|----------|
| **Single project, env separation by naming** | Simple, no org overhead, $0 extra. Prefix resources with `dev-`/`prod-`. | ✅ **Chosen** — single developer, no compliance requirement. |
| Separate projects per env | Clean isolation, IAM per project, but double management overhead. | ❌ Not justified for solo dev |

### Decision: Serverless VPC Connector for Cloud Run

| Option | Tradeoff | Decision |
|--------|----------|----------|
| **Serverless VPC Connector** | Allows Cloud Run to reach Cloud SQL and Memorystore via internal IPs. ~$18/mo fixed cost. | ✅ **Chosen** — keeps databases off the public internet. |
| Cloud SQL via public IP + SSL | No VPC connector cost, but database exposes a public endpoint (even if authorized networks only). | ❌ Security risk for production data |
| Direct access via Unix sockets (Cloud SQL) | No VPC connector needed for Cloud SQL only, but Memorystore still needs VPC. | ❌ Memorystore forces VPC anyway |

### Decision: Secret Manager for secrets

| Option | Tradeoff | Decision |
|--------|----------|----------|
| **Secret Manager** | Managed, audited, versioned. $0.06/secret/month. | ✅ **Chosen** — no .env files in production. |
| .env in Cloud Storage | Simple, but no versioning, no audit trail, harder to rotate. | ❌ Poor security practice |
| Encrypted in Git | Leak risk, no rotation support. | ❌ Never |

### Decision: Cloud Load Balancer for HTTPS + routing

| Option | Tradeoff | Decision |
|--------|----------|----------|
| **External HTTPS LB + Serverless NEG** | Managed SSL, routes to Cloud Run, global edge. Replaces Nginx proxy. | ✅ **Chosen** — native GCP integration. |
| Cloudflare + direct Cloud Run URL | No LB cost, but more DNS hops, less GCP-native. | ❌ Keep infra simple — all GCP |

## Architecture

```
                         Cloud DNS (brujula.app, api.brujula.app)
                                    │
                         Cloud Load Balancer (HTTPS, SSL)
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
              Serverless NEG                  Serverless NEG
                    │                               │
             Cloud Run (api)                  Cloud Run (web)
             FastAPI :8000                     Next.js :3000
                    │                               │
                    └───────────┬───────────────────┘
                                │
                    Serverless VPC Connector
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                  │
        Cloud SQL            Memorystore       Compute Engine
       PostgreSQL 15         Redis 7            Celery Worker
       (private IP)         (private IP)        e2-micro
              │                 │                  │
              └─────────────────┼──────────────────┘
                                │
                        Cloud Storage
                      uploads-bucket
```

## Data Flow

```
1. User uploads CSV → Cloud Run API (writes to Cloud Storage bucket)
2. API enqueues Celery task → Memorystore (Redis)
3. Celery worker (Compute Engine) picks up task ← Memorystore
4. Worker reads file from Cloud Storage → processes → writes trades to Cloud SQL
5. Worker updates upload status in Cloud SQL
6. Frontend polls API → API reads analytics (cache: Memorystore → miss → compute → store)
7. AI diagnosis: API → Anthropic API → stores result in Cloud SQL
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `openspec/changes/brujula-infra/design.md` | Create | This design document |
| `infra/terraform/main.tf` | Create | Root Terraform config with providers and GCS backend |
| `infra/terraform/variables.tf` | Create | Input variables (project, region, env) |
| `infra/terraform/outputs.tf` | Create | Output values (service URLs, IPs) |
| `infra/terraform/modules/networking/main.tf` | Create | VPC, subnet, serverless VPC connector, firewall rules |
| `infra/terraform/modules/cloud-sql/main.tf` | Create | Cloud SQL PostgreSQL 15 instance, database, user |
| `infra/terraform/modules/memorystore/main.tf` | Create | Redis 7 instance with private IP |
| `infra/terraform/modules/cloud-run/main.tf` | Create | Cloud Run services (api, web) with IAM, env vars |
| `infra/terraform/modules/compute-worker/main.tf` | Create | e2-micro VM with startup script for Celery worker |
| `infra/terraform/modules/storage/main.tf` | Create | GCS bucket for uploads with lifecycle rules |
| `infra/terraform/modules/load-balancer/main.tf` | Create | HTTPS LB, SSL cert, serverless NEGs |
| `infra/terraform/modules/iam/main.tf` | Create | Service accounts, custom roles, permissions |
| `infra/terraform/.terraform.lock.hcl` | Create | Lock file for provider versions |
| `infra/scripts/migrate-db.sh` | Create | Script to export/import PostgreSQL data from VPS to Cloud SQL |
| `infra/scripts/setup-secrets.sh` | Create | Script to populate Secret Manager from .env |
| `.github/workflows/infra.yml` | Create | Terraform plan/apply on push to infra/ |
| `.github/workflows/deploy-api.yml` | Modify | Build → Artifact Registry → Cloud Run (replace GHCR+VPS) |
| `.github/workflows/deploy-web.yml` | Modify | Build → Artifact Registry → Cloud Run (replace GHCR+VPS) |
| `Bakend-bdt/app/config.py` | Modify | Add Cloud Storage env vars, accept GCS URLs for uploads |
| `Bakend-bdt/docker/Dockerfile` | Modify | Add `--break-system-packages` compat, ensure Cloud Run healthcheck ready |

## Interfaces / Contracts

### Cloud Run service contract (api)

```yaml
# cloud-run/env-vars.yaml (injected via Secret Manager)
DATABASE_URL:     "postgresql+asyncpg://brujula@//cloudsql/<project>:<region>:<instance>/brujula_db"
DATABASE_URL_SYNC:"postgresql://brujula@//cloudsql/<project>:<region>:<instance>/brujula_db"
REDIS_URL:        "redis://10.x.x.x:6379/0"
STORAGE_TYPE:     "gcs"
GCS_BUCKET:       "brujula-uploads-{env}"
CORS_ORIGINS:     "https://brujula.app,https://www.brujula.app"
```

### Terraform module interface

```hcl
module "cloud_sql" {
  source     = "./modules/cloud-sql"
  project    = var.project_id
  env        = var.env
  region     = var.region
  vpc_id     = module.networking.vpc_id
  db_password = data.google_secret_manager_secret_version.db_password.secret_data
}

module "cloud_run_api" {
  source         = "./modules/cloud-run"
  service_name   = "brujula-api-${var.env}"
  image          = "${var.region}-docker.pkg.dev/${var.project_id}/brujula/api:latest"
  port           = 8000
  env_vars       = { DATABASE_URL = "...", REDIS_URL = "...", ... }
  secrets        = ["JWT_SECRET_KEY", "ENCRYPTION_KEY", "ANTHROPIC_API_KEY"]
  vpc_connector  = module.networking.vpc_connector_id
}
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Terraform plan | All modules apply cleanly | `terraform plan` in CI, `terraform apply` on main |
| Cloud Run deploy | Container starts, healthcheck passes, env vars injected | `gcloud run deploy --no-traffic` smoke test |
| Data migration | Export from VPS PG, import to Cloud SQL, verify row counts | Manual script with checksums |
| DNS cutover | All domains resolve, LB serves traffic, SSL valid | `curl -I https://api.brujula.app` + cert check |
| Rollback | terraform destroy + VPS re-enable | Documented runbook |

## Migration / Rollout

**Phase 1 — Foundation**: Terraform GCS backend, VPC, IAM, Secret Manager. Apply from local machine. No services yet.

**Phase 2 — Databases**: Cloud SQL + Memorystore. Run `migrate-db.sh` to seed Cloud SQL from VPS PostgreSQL. Keep VPS running — apps still connect to VPS databases.

**Phase 3 — Container migration**: Build images → push to Artifact Registry → deploy API + Web to Cloud Run → deploy Worker VM. Point Cloud Run services to Cloud SQL + Memorystore.

**Phase 4 — Parallel run**: Both VPS and Cloud Run active. VPS serves production, Cloud Run is tested internally. Run side-by-side for 48h.

**Phase 5 — DNS cutover**: Update DNS A records for `brujula.app` and `api.brujula.app` to point to Cloud Load Balancer IP. Keep VPS as cold standby for 7 days.

**Phase 6 — Decommission**: Take VPS snapshot, power down. Delete VPS after 30 days.

**Rollback**: Revert DNS to VPS IP. Cloud Run → 0 traffic. VPS already has the latest data (Cloud SQL is the primary).

## Open Questions

- [ ] Celery worker needs Redis to be available — does the e2-micro startup script handle Memorystore connectivity correctly, or do we need a VPC peering setup?
- [ ] WeasyPrint PDF generation has system dependencies (libpango, libcairo) — already in the Dockerfile. Verify they work on Cloud Run's gVisor sandbox.
- [ ] Cost of Serverless VPC Connector is ~$18/mo fixed — confirm this fits within monthly infra budget.
- [ ] Does the e2-micro with 1GB RAM handle Celery + PDF generation? If weasyprint is memory-intensive, consider e2-small.

## Cost Estimation

| Service | Config | Est. Monthly |
|---------|--------|-------------|
| Cloud Run (api) | 2 services × 256MB × 500k req/mo | ~$8 |
| Cloud Run (web) | 256MB × 300k req/mo | ~$5 |
| Compute Engine (worker) | e2-micro, 1 vCPU, 1GB, preemptible | ~$7 |
| Cloud SQL | db-f1-micro, 10GB SSD, HA disabled | ~$15 |
| Memorystore | Basic tier, 1GB | ~$18 |
| Cloud Storage | 5GB, standard class | ~$0.50 |
| Load Balancer | 1 forwarding rule | ~$18 |
| Serverless VPC Connector | 1 connector | ~$18 |
| Artifact Registry | 1GB stored | ~$0.10 |
| Total | | **~$90/mo** |

Optimizations: Use preemptible worker VM, Cloud Run auto-scales to zero in off hours, db-f1-micro for dev/prod shared during MVP. Upgrade to HA only when paying users onboard.
