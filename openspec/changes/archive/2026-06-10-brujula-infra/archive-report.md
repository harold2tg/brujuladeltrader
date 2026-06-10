# Archive Report: brujula-infra (GCP + Terraform + Cloud Run + Cloud SQL)

**Status**: ⛔ BLOCKED — Critical issues prevent archive

**Date**: 2026-06-10

**Change**: brujula-infra

**Artifact Store**: openspec

---

## Executive Summary

The brujula-infra change implements a comprehensive GCP infrastructure migration from VPS-based Docker Compose to Cloud Run (API/Web), Compute Engine (Celery worker), Cloud SQL (PostgreSQL), Memorystore (Redis), Cloud Storage (uploads), and an HTTPS Load Balancer. All 19 code implementation tasks are complete, but 2 critical issues in GitHub Actions workflows would cause deployment failures, and 11 operational tasks remain pending (expected — require manual GCP project execution).

**Archive is BLOCKED** due to critical issues in the verification report.

---

## Change Summary

**What was done**: Designed and implemented a complete GCP serverless infrastructure using Terraform IaC, including:
- 9 Terraform modules (networking, IAM, secret-manager, cloud-sql, memorystore, storage, cloud-run, compute-worker, load-balancer)
- 6 operational scripts (setup-secrets, migrate-db, validate-cloud-run, compare-responses, cutover-dns, rollback)
- 3 GitHub Actions workflows (infra, deploy-api, deploy-web)
- Modified Dockerfile for Cloud Run compatibility
- Modified config.py for GCS storage support

**Migration approach**: 6-phase phased migration (Foundation → Databases → Containers → Parallel Run → DNS Cutover → Decommission)

---

## Artifacts Created

| Artifact | Path | Status |
|----------|------|--------|
| design.md | `openspec/changes/brujula-infra/design.md` | ✅ Complete |
| tasks.md | `openspec/changes/brujula-infra/tasks.md` | ✅ Complete |
| verify-report.md | `openspec/changes/brujula-infra/verify-report.md` | ✅ Complete |
| proposal.md | — | ❌ Missing |
| spec.md | — | ❌ Missing |

---

## Files Changed

### Terraform Modules (30+ files)
- `infra/terraform/main.tf` — Root config with GCP provider, GCS backend
- `infra/terraform/variables.tf` — Input variables
- `infra/terraform/outputs.tf` — Output values
- `infra/terraform/modules/networking/` — VPC, subnet, serverless VPC connector
- `infra/terraform/modules/iam/` — Service accounts, custom roles
- `infra/terraform/modules/secret-manager/` — Secrets with IAM bindings
- `infra/terraform/modules/cloud-sql/` — PostgreSQL 15 instance
- `infra/terraform/modules/memorystore/` — Redis 7 instance
- `infra/terraform/modules/storage/` — GCS bucket with lifecycle rules
- `infra/terraform/modules/cloud-run/` — Cloud Run services (api, web)
- `infra/terraform/modules/compute-worker/` — e2-micro VM for Celery
- `infra/terraform/modules/load-balancer/` — HTTPS LB with SSL

### Scripts (6 files)
- `infra/scripts/setup-secrets.sh` — Populate Secret Manager from .env
- `infra/scripts/migrate-db.sh` — Export/import PostgreSQL data
- `infra/scripts/validate-cloud-run.sh` — Test Cloud Run endpoints
- `infra/scripts/compare-responses.sh` — Compare VPS vs Cloud Run responses
- `infra/scripts/cutover-dns.sh` — Update DNS records
- `infra/scripts/rollback.sh` — Emergency rollback

### CI/CD Workflows (3 files)
- `.github/workflows/infra.yml` — Terraform plan/apply
- `.github/workflows/deploy-api.yml` — Build → AR → Cloud Run
- `.github/workflows/deploy-web.yml` — Build → AR → Cloud Run

### Application Code (2 files)
- `Bakend-bdt/app/config.py` — Added GCS support
- `Bakend-bdt/docker/Dockerfile` — Cloud Run compatibility

---

## Decisions Made

1. **Cloud Run for stateless services** — Auto-scaling to zero, managed infra, pay-per-request
2. **Compute Engine for Celery worker** — Pragmatic for MVP, no code changes needed
3. **Single GCP project** — Simple, no org overhead for solo developer
4. **Serverless VPC Connector** — Keeps databases off public internet (~$18/mo)
5. **Secret Manager** — Managed, audited, versioned secrets
6. **Cloud Load Balancer** — Native GCP integration, replaces Nginx
7. **Host-based routing** — Cleaner architecture than path-based (api.brujula.app vs brujula.app)

---

## Risks Identified

### CRITICAL (Blocking Archive)
1. **Stray closing brace in deploy workflows** — Would cause `gcloud run deploy` to fail with invalid service name
2. **Hardcoded Redis IP** — Not guaranteed to be 10.0.0.2, could break silently

### WARNINGS
1. **APP_SECRET_KEY reuses JWT_SECRET_KEY** — Security risk if one is compromised
2. **`.terraform.lock.hcl` not committed** — Should be committed for deterministic builds
3. **Web Cloud Run has no secret references** — Missing wiring for future secrets

### Open Questions
1. Celery worker Redis connectivity via Memorystore
2. WeasyPrint PDF generation on Cloud Run's gVisor sandbox
3. Serverless VPC Connector cost (~$18/mo)
4. e2-micro memory for Celery + PDF generation

---

## Verification Results

**Status**: ⚠️ WARNING — Issues found, none blocking deployment (but blocking archive)

**Passed Checks**:
- ✅ File existence (30/31 files)
- ✅ Shell script syntax (6/6 scripts pass `bash -n`)
- ✅ Module wiring (9/9 modules correctly connected)
- ✅ Spec compliance (12/12 key design requirements met)

**Failed Checks**:
- ❌ 2 CRITICAL issues in GitHub Actions workflows
- ❌ Missing proposal.md and spec.md

**Task Completion**:
- ✅ Code implementation: 19/19 tasks complete
- ⏳ Operational tasks: 0/11 tasks complete (expected — require manual GCP execution)

---

## Next Steps for Deployment

### Immediate (Before Archive)
1. **Fix critical workflow issues**:
   - Remove stray `}` in deploy-api.yml line 103 and deploy-web.yml line 104
   - Replace hardcoded Redis IP with dynamic retrieval from Terraform output
2. **Fix warning issues**:
   - Create dedicated `app_secret_key` secret
   - Run `terraform init` and commit `.terraform.lock.hcl`
   - Add `web_secret_vars` to root module call

### After Archive (Operational)
1. **Phase 1**: Run `terraform apply` for foundation (VPC, IAM, secrets)
2. **Phase 2**: Run `terraform apply` for databases (Cloud SQL, Memorystore, storage)
3. **Phase 3**: Push images to Artifact Registry, run `terraform apply` for services
4. **Phase 4**: Run 48-hour parallel validation
5. **Phase 5**: Execute DNS cutover
6. **Phase 6**: Decommission VPS after 30 days

---

## Archive Decision

**Recommendation**: ⛔ BLOCK ARCHIVE

**Reasons**:
1. 2 CRITICAL issues in verification report would cause deployment failures
2. Missing proposal.md and spec.md (required artifacts)
3. Operational tasks pending (expected, but should be documented)

**Required Actions Before Archive**:
1. Fix the 2 critical workflow issues
2. Create proposal.md and spec.md (or explicitly approve partial archive)
3. Re-run verification to confirm fixes

---

## Intentional Partial Archive (If Approved)

If the orchestrator explicitly approves partial archive without proposal.md and spec.md:

**Missing Artifacts**:
- proposal.md — Reason: Not created during change planning
- spec.md — Reason: Design document serves as technical specification

**Recorded Warnings**:
- Archive proceeds with missing artifacts per orchestrator approval
- Operational tasks remain pending until GCP project execution
- Critical workflow issues must be fixed before deployment

---

## Archive Report Metadata

- **Generated by**: sdd-archive executor
- **Date**: 2026-06-10
- **Artifact store**: openspec
- **Change path**: `openspec/changes/brujula-infra/`
- **Archive path**: `openspec/changes/archive/2026-06-10-brujula-infra/` (if approved)