# Tasks: GCP + Terraform + Cloud Run + Cloud SQL Migration

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 850–1600 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 → PR 2 → PR 3 → PR 4 |
| Delivery strategy | ask-on-risk |
| Chain strategy | stacked-to-main |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Foundation: Terraform root + networking + IAM + secrets | PR 1 | base=main; ~300 lines; foundational — everything depends on this |
| 2 | Data layer: Cloud SQL + Memorystore + storage + migration scripts | PR 2 | base=PR 1 branch; ~350 lines; depends on PR 1 networking |
| 3 | Compute: Cloud Run services + worker VM + load balancer | PR 3 | base=PR 2 branch; ~400 lines; depends on PR 2 databases |
| 4 | CI/CD + app config + workflows | PR 4 | base=PR 3 branch; ~250 lines; depends on PR 3 services |

---

## Phase 1: Foundation — Terraform, VPC, IAM, Secret Manager

- [x] 1.1 Create `infra/terraform/main.tf` — root config with GCP provider, GCS backend, project/region variables
- [x] 1.2 Create `infra/terraform/variables.tf` — input variables: project_id, region, env, db_password, redis_password
- [x] 1.3 Create `infra/terraform/outputs.tf` — outputs: service URLs, LB IP, Cloud SQL connection name
- [x] 1.4 Create `infra/terraform/modules/networking/main.tf` — VPC, subnet (10.0.0.0/24), serverless VPC connector, firewall rules (allow internal, deny external)
- [x] 1.5 Create `infra/terraform/modules/iam/main.tf` — service accounts: cloud-run-sa, cloud-sql-sa, worker-sa; custom roles for Secret Manager access
- [x] 1.6 Create `infra/terraform/modules/secret-manager/main.tf` — secrets: JWT_SECRET_KEY, ENCRYPTION_KEY, ANTHROPIC_API_KEY, DB_PASSWORD, REDIS_PASSWORD; IAM bindings for cloud-run-sa
- [x] 1.7 Create `infra/scripts/setup-secrets.sh` — script to populate Secret Manager from .env file (reads local .env, pushes each var as a secret)
- [x] 1.8 Create `.github/workflows/infra.yml` — CI: terraform fmt check, terraform plan on PR, terraform apply on push to main (infra/ path trigger)

## Phase 2: Databases — Cloud SQL, Memorystore, Storage

- [x] 2.1 Create `infra/terraform/modules/cloud-sql/main.tf` — PostgreSQL 15 instance (db-f1-micro), private IP only, database brujula_db, user brujula, authorized networks empty
- [x] 2.2 Create `infra/terraform/modules/memorystore/main.tf` — Redis 7 basic tier, 1GB, private IP, auth enabled
- [x] 2.3 Create `infra/terraform/modules/storage/main.tf` — GCS bucket brujula-uploads-{env}, lifecycle rules (delete after 90 days), uniform bucket-level access
- [x] 2.4 Create `infra/scripts/migrate-db.sh` — script to: (1) pg_dump from VPS, (2) pg_restore to Cloud SQL, (3) verify row counts and checksums
- [ ] 2.5 Run `setup-secrets.sh` to populate all secrets in Secret Manager
- [ ] 2.6 Run `terraform apply` for Phase 2 modules (cloud-sql, memorystore, storage) — verify all resources created

## Phase 3: Containers — Artifact Registry, Cloud Run, Worker VM

- [x] 3.1 Create `infra/terraform/modules/cloud-run/main.tf` — Cloud Run services (api:8000, web:3000) with IAM, env vars from Secret Manager, VPC connector, max-instances=10
- [x] 3.2 Create `infra/terraform/modules/compute-worker/main.tf` — e2-micro VM, startup script installs Docker, pulls brujula-api image, runs celery worker; service account with Secret Manager + Storage access
- [x] 3.3 Create `infra/terraform/modules/load-balancer/main.tf` — external HTTPS LB, managed SSL cert, serverless NEGs for api and web, path-based routing (/ → web, /api/* → api)
- [x] 3.4 Modify `Bakend-bdt/app/config.py` — add GCS_BUCKET, STORAGE_TYPE="gcs" env vars; conditional upload path (local vs GCS)
- [x] 3.5 Modify `Bakend-bdt/docker/Dockerfile` — add `--break-system-packages` flag, ensure Cloud Run PORT env var support, healthcheck endpoint
- [ ] 3.6 Push API image to Artifact Registry: `gcloud builds submit --tag {region}-docker.pkg.dev/{project}/brujula/api:latest`
- [ ] 3.7 Push Web image to Artifact Registry: `gcloud builds submit --tag {region}-docker.pkg.dev/{project}/brujula/web:latest`
- [ ] 3.8 Run `terraform apply` for Phase 3 modules (cloud-run, compute-worker, load-balancer) — verify services deploy and healthchecks pass

## Phase 4: Parallel Run — Validation

- [x] 4.1 Create `infra/scripts/validate-cloud-run.sh` — script to test all Cloud Run endpoints: health check, auth flow, file upload, AI diagnosis
- [x] 4.2 Create `infra/scripts/compare-responses.sh` — script to send identical requests to VPS and Cloud Run, compare responses (status codes, JSON structure)
- [ ] 4.3 Run parallel validation for 48 hours — VPS serves production, Cloud Run tested internally; log any discrepancies
- [ ] 4.4 Verify Cloud SQL data consistency — compare row counts between VPS PostgreSQL and Cloud SQL for all tables

## Phase 5: DNS Cutover

- [x] 5.0 Create `infra/scripts/cutover-dns.sh` — script to update Cloud DNS A records to LB IP
- [x] 5.0 Create `infra/scripts/rollback.sh` — script to revert DNS to VPS IP (emergency rollback)
- [ ] 5.1 Update Cloud DNS A records: brujula.app → LB IP, api.brujula.app → LB IP, www.brujula.app → LB IP
- [ ] 5.2 Verify HTTPS serves correctly: `curl -I https://brujula.app` and `curl -I https://api.brujula.app`
- [ ] 5.3 Verify SSL certificate is valid and auto-renewing
- [ ] 5.4 Monitor for 24 hours post-cutover — check Cloud Run logs, error rates, latency
- [x] 5.5 Keep VPS as cold standby for 7 days — document rollback procedure (revert DNS to VPS IP)

## Phase 6: Decommission

- [ ] 6.1 Take VPS snapshot: `gcloud compute disks snapshot` or equivalent
- [ ] 6.2 Power down VPS: `gcloud compute instances stop`
- [ ] 6.3 After 30 days with no issues: delete VPS instance and attached disk
- [ ] 6.4 Remove old VPS-related GitHub Actions secrets and workflow references
- [ ] 6.5 Update project documentation (README, AGENTS.md) to reflect GCP-only infrastructure

---

## Dependency Graph

```
Phase 1 (Foundation)
  ├─ 1.1 → 1.2, 1.3
  ├─ 1.4 → 2.1, 2.2, 2.3, 3.1, 3.2
  ├─ 1.5 → 3.1, 3.2
  ├─ 1.6 → 1.7
  └─ 1.8 (independent)

Phase 2 (Databases)
  ├─ 2.1, 2.2, 2.3 (parallel, depend on 1.4)
  ├─ 2.4 (depends on 2.1)
  ├─ 2.5 (depends on 1.6, 1.7)
  └─ 2.6 (depends on 2.1-2.5)

Phase 3 (Containers)
  ├─ 3.1 (depends on 1.4, 1.5)
  ├─ 3.2 (depends on 1.4, 1.5)
  ├─ 3.3 (depends on 3.1)
  ├─ 3.4, 3.5 (parallel, independent)
  ├─ 3.6, 3.7 (parallel, depend on 3.4, 3.5)
  └─ 3.8 (depends on 3.1-3.7)

Phase 4 (Parallel Run)
  ├─ 4.1, 4.2 (parallel, depend on 3.8)
  ├─ 4.3 (depends on 4.1, 4.2)
  └─ 4.4 (depends on 4.3)

Phase 5 (DNS Cutover)
  ├─ 5.1 (depends on 4.3)
  ├─ 5.2, 5.3 (parallel, depend on 5.1)
  ├─ 5.4 (depends on 5.2)
  └─ 5.5 (depends on 5.4)

Phase 6 (Decommission)
  ├─ 6.1 → 6.2 → 6.3 (sequential)
  ├─ 6.4 (depends on 6.3)
  └─ 6.5 (depends on 6.3)
```
