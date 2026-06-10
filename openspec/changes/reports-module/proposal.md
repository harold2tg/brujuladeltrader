# Proposal: Reports Module

## Intent

Package analytics into client-ready reports (monthly PDF, annual PDF, CSV export) and generate deterministic text insights as fallback when AI Engine is unavailable. Reports is a thin wrapper over AnalyticsService — no duplicate queries.

## Scope

### In Scope
- GET /reports/{upload_id}/monthly — monthly report with metrics + narrative
- GET /reports/{upload_id}/annual — annual report (aggregates all uploads in that year)
- POST /reports/export — export to PDF/CSV (Pro-only)
- Deterministic narrative insights from metrics (fallback for AI Engine)
- Plan enforcement: Pro check on export endpoints
- Redis cache for report text (TTL: 1h)
- Streaming CSV with pandas → StringIO → StreamingResponse

### Out of Scope
- PDF generation in Celery (heavy, deferred to design phase)
- Email delivery of reports (future)
- Scheduled/automated report generation
- Custom report templates or branding config
- Reports for multiple years at once

## Capabilities

### New Capabilities
- `reports`: Report generation — formatted monthly/annual reports, PDF/CSV export, and deterministic narrative insights from trade metrics

### Modified Capabilities
- None (reports depends on analytics but doesn't change its spec)

## Approach

**Thin Wrapper**: ReportsService wraps AnalyticsService to get pre-computed metrics, formats them into human-readable reports, and serves them via REST or file export.

- Monthly: `AnalyticsService.get_full_metrics()` → format as structured JSON + narrative text
- Annual: Get all uploads for user in year `N`, call `get_full_metrics()` per upload, aggregate
- CSV export (sync): pandas DataFrame from metrics → StringIO → StreamingResponse with `text/csv`
- PDF export: Celery task with WeasyPrint renders HTML template → PDF, stores temp file, returns status URL for polling
- Deterministic fallback: `generate_insights()` reads `get_summary()` + `by_session()` + `by_hour()` metrics, produces template-based sentences per metric category
- Export endpoints check `user.plan == "pro"` before processing, raise 403 Forbidden otherwise

## Endpoint Contracts

### GET /reports/{upload_id}/monthly
```
Response: { success: true, data: { period, global_metrics, dimensions, insights: string, export_available: bool } }
```
### GET /reports/{upload_id}/annual
```
Query: year (int, default current)
Aggregates all uploads in that year. Response same shape as monthly.
```
### POST /reports/export
```
Body: { upload_id, format: "pdf" | "csv", period: "monthly" | "annual", year?: int }
Response (sync CSV): StreamingResponse with Content-Disposition attachment
Response (async PDF): { success: true, data: { job_id, status: "processing" } }
GET  /reports/export/{job_id} → { status, download_url?, error? }
```

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/modules/reports/` | New | router.py, service.py, schemas.py, insights.py, tasks.py, templates/ |
| `app/main.py` | Modified | Register reports router |
| `pyproject.toml` | Modified | Add weasyprint dependency |
| `tests/modules/test_reports.py` | New | Integration tests for all endpoints |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| WeasyPrint install on Alpine/Docker | Medium | Add system deps (libpango, cairo) to Dockerfile; test in CI build |  |  |  |
| PDF generation blocks response | High | Celery task + status polling pattern (same as ai_engine) |
| Large dataset CSV memory blowup | Low | StreamingResponse with pandas chunks; free users never hit this path |

## Rollback Plan

Remove `app.modules.reports` directory, revert `app/main.py` router registration, and remove weasyprint from `pyproject.toml`. Data already in analytics — reports is a read-only projection; no data migration risk.

## Dependencies

- AnalyticsService (pre-computed metrics, Redis cache layer)
- Upload model (for annual aggregation and date range lookup)
- auth module (user.plan for Pro enforcement)
- Celery + Redis (PDF generation async tasks)
- WeasyPrint (HTML→PDF rendering, added to pyproject.toml)
- pandas (CSV streaming)
- jinja2 (PDF HTML template rendering)

## Success Criteria

- [ ] Monthly report returns metrics + narrative text in < 500ms (cached)
- [ ] Annual report aggregates all uploads in a year correctly
- [ ] CSV export returns valid downloadable file with Content-Disposition
- [ ] PDF export creates Celery task, stores file, and exposes download URL
- [ ] Pro-only endpoints return 403 for free-tier users
- [ ] Deterministic insights never fail (no external dependency)
- [ ] All endpoints require valid JWT; 401 for anonymous requests
- [ ] Tests pass with >= 80% coverage on reports module
