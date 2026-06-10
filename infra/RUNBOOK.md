# Runbook: La Brújula del Trader — GCP Migration (Phases 4–6)

This runbook covers the parallel run, DNS cutover, and decommission phases of the VPS → GCP migration.

## Prerequisites

- All Terraform modules applied (Phases 1–3)
- Cloud Run services deployed and healthy
- Cloud SQL seeded with production data (via `migrate-db.sh`)
- Artifact Registry images pushed
- `gcloud` CLI authenticated with project access

---

## Phase 4: Parallel Run (48 hours)

### Goal

Run VPS and Cloud Run side-by-side. VPS serves production; Cloud Run is tested internally. Verify parity before cutover.

### Steps

1. **Start parallel validation**

```bash
# Run the comparison script
./infra/scripts/compare-responses.sh \
  --vps-url https://brujula.app \
  --cloud-run-url <API_CLOUD_RUN_URL>

# Run full smoke tests
./infra/scripts/validate-cloud-run.sh --env prod
```

2. **Monitor for 48 hours**
   - Check Cloud Run logs daily: `gcloud run services logs read brujula-api-prod --region us-central1`
   - Verify no errors in API or Web logs
   - Compare response times: VPS vs Cloud Run
   - Verify Celery worker is processing tasks from Memorystore

3. **Data consistency check**

```bash
# Compare row counts between VPS PostgreSQL and Cloud SQL
# (use migrate-db.sh verification step or manual psql queries)
```

4. **Document discrepancies**
   - If any endpoint returns different status codes or JSON structure, investigate before proceeding
   - Common issues: CORS misconfiguration, missing env vars, Cloud SQL connection timeouts

### Rollback (during parallel run)

No DNS changes yet — simply stop Cloud Run services. VPS continues serving normally.

---

## Phase 5: DNS Cutover

### Goal

Route production traffic from VPS to Cloud Load Balancer → Cloud Run.

### Steps

1. **Pre-cutover checklist**
   - [ ] All endpoints pass `compare-responses.sh` with 0 differences
   - [ ] Cloud Run health checks pass for 48+ hours
   - [ ] Cloud SQL data matches VPS (row counts, checksums)
   - [ ] SSL certificate provisioned on Cloud Load Balancer
   - [ ] Celery worker processing tasks correctly

2. **Get Load Balancer IP**

```bash
gcloud compute addresses describe brujula-lb-ip \
  --global \
  --format="value(address)"
```

3. **Update DNS records**

```bash
./infra/scripts/cutover-dns.sh \
  --project <GCP_PROJECT_ID> \
  --lb-ip <LOAD_BALANCER_IP>
```

4. **Verify cutover**

```bash
# Check DNS resolution
dig +short brujula.app A
dig +short api.brujula.app A
dig +short www.brujula.app A

# Verify HTTPS
curl -I https://brujula.app
curl -I https://api.brujula.app/health
```

5. **Monitor for 24 hours post-cutover**
   - Watch Cloud Run logs: `gcloud run services logs read brujula-api-prod --region us-central1`
   - Monitor error rates and latency
   - Verify all user flows work: login, upload, analysis, AI diagnosis

### Rollback (if issues found)

```bash
./infra/scripts/rollback.sh \
  --project <GCP_PROJECT_ID> \
  --vps-ip <VPS_IP_ADDRESS>
```

This reverts DNS to VPS. Cloud Run continues running but receives no traffic.

---

## Phase 6: Decommission VPS

### Goal

Power down the VPS after 7 days of stable Cloud Run operation.

### Steps

1. **7-day stability check**
   - No errors in Cloud Run logs
   - All user flows working
   - Celery worker processing tasks correctly
   - No data inconsistencies

2. **Take VPS snapshot**

```bash
# From local machine (if VPS is GCE)
gcloud compute disks snapshot <VPS_DISK_NAME> \
  --zone <VPS_ZONE> \
  --snapshot-names=vps-snapshot-$(date +%Y%m%d)

# Or use VPS provider's snapshot mechanism
ssh <VPS_USER>@<VPS_IP> "sudo shutdown -h +0"  # graceful shutdown
```

3. **Power down VPS**

```bash
# If GCE
gcloud compute instances stop <VPS_INSTANCE_NAME> --zone <VPS_ZONE>

# If non-GCE: shut down via provider console
```

4. **After 30 days with no issues**
   - Delete VPS instance and disk
   - Remove old GitHub Actions secrets (VPS_HOST, VPS_USER, VPS_SSH_KEY, GHCR_TOKEN)
   - Remove old deploy workflow (`.github/workflows/deploy.yml`)
   - Update README and AGENTS.md to reflect GCP-only infrastructure

---

## Emergency Contacts

| Situation | Action |
|-----------|--------|
| Cloud Run down | Check logs, restart service: `gcloud run services update brujula-api-prod --no-traffic && gcloud run services update-traffic brujula-api-prod --to-latest` |
| Cloud SQL down | Check Cloud SQL console, verify connections, check IAM permissions |
| DNS issues | Verify Cloud DNS zone, check propagation with `dig`, verify LB health |
| Data inconsistency | Stop Cloud Run traffic, investigate, use VPS as source of truth |
| Complete failure | Rollback DNS to VPS: `./rollback.sh --project <PROJECT> --vps-ip <VPS_IP>` |

---

## Key GCP Resources

| Resource | Name/ID |
|----------|---------|
| Project | `<GCP_PROJECT_ID>` |
| Region | `us-central1` |
| Cloud Run (API) | `brujula-api-prod` |
| Cloud Run (Web) | `brujula-web-prod` |
| Cloud SQL | `brujula-prod` |
| Memorystore | `brujula-redis-prod` |
| GCS Bucket | `brujula-uploads-prod` |
| Load Balancer | `brujula-lb` |
| VPC | `brujula-vpc` |
| Artifact Registry | `brujula` |
| DNS Zone | `brujula-app` |

---

## Cost Monitoring

After cutover, monitor GCP costs:

```bash
# Check current month's costs
gcloud billing accounts list
gcloud billing budgets list --billing-account=<ACCOUNT_ID>

# Set up budget alert (recommended: $100/month threshold)
```

Expected monthly cost: ~$90/mo (see design.md for breakdown).
