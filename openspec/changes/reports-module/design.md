# Design: Reports Module

## Technical Approach

Thin read-only projection over AnalyticsService that packages existing metrics into client-ready reports (monthly/annual) and exports (PDF/CSV). No new DB tables. Report narrative uses deterministic template-based insights — zero AI dependency. PDF generation is async via Celery, CSV is sync via StreamingResponse.

## Architecture Decisions

| Option | Tradeoffs | Decision |
|--------|-----------|----------|
| Inheritance vs composition for AnalyticsService | Inheritance couples lifetimes; composition allows test injection | ReportsService **composes** AnalyticsService via constructor injection |
| Async PDF via Celery vs sync | Async avoids timeout on large reports, requires polling pattern | **Celery async** — same pattern as ai_engine |
| pandas HTML → WeasyPrint vs ReportLab | pandas keeps metric formatting; WeasyPrint handles CSS | **Jinja2 template → HTML → WeasyPrint** — lower code, CSS-driven layout |
| CSV via pandas to_csv() vs manual | pandas handles escaping, formatting, numeric precision | **pandas to_csv()** with StringIO wrapped in StreamingResponse |
| Decorator vs dependency for plan check | Both work; project uses Depends pattern | **Dependency function** `require_pro_plan` consistent with `get_current_active_user` |
| Template-based insights vs AI fallback | Deterministic, no cost, but less nuance | **Rule-based insight generator** with language-aware sentence templates |

## Data Flow

```
Client ──GET /reports/{id}/monthly?year=2026&month=3──→ Router
                                                          │
                                                    ┌─────▼──────┐
                                                    │  Reports   │
                                                    │  Service   │
                                                    └─────┬──────┘
                                                          │
                                            ┌─────────────┼─────────────┐
                                            ▼             ▼             ▼
                                    AnalyticsService  Redis (check)  InsightGen
                                            │             │             │
                                            └──metrics────► cache ──────┘
                                                            │
                                                       response dict

Client ──POST /reports/{id}/export/pdf ──→ Router
                                             │
                                        ReportsService
                                             │
                                      dispatch Celery task
                                             │
                                    ┌────────▼────────┐
                                    │ Celery Worker   │
                                    │ → Load metrics  │
                                    │ → Render Jinja2 │
                                    │ → WeasyPrint    │
                                    │ → Save to Redis │
                                    └────────┬────────┘
                                             │
Client ◄───poll GET /reports/jobs/{job_id}───┘

Client ──GET /reports/{id}/export/csv ──→ Router
                                             │
                                        ReportsService
                                             │
                                        pandas → StringIO
                                             │
                                    StreamingResponse (text/csv)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `app/modules/reports/__init__.py` | Create | Package init |
| `app/modules/reports/router.py` | Create | 4 endpoints: monthly, annual, export PDF, export CSV |
| `app/modules/reports/service.py` | Create | ReportsService: compose reports from analytics + insights |
| `app/modules/reports/schemas.py` | Create | Request/response Pydantic models |
| `app/modules/reports/insights.py` | Create | Deterministic insight generator (template-based) |
| `app/modules/reports/tasks.py` | Create | Celery task for async PDF generation |
| `app/modules/reports/templates/report.html` | Create | Jinja2 template for PDF rendering |
| `app/main.py` | Modify | Register reports router |
| `pyproject.toml` | Modify | Add `weasyprint`, `jinja2` dependencies |
| `docker/Dockerfile` | Modify | Install system libs: `libpango-1.0-0`, `libcairo2`, `libgdk-pixbuf2.0-0` |

## Interfaces / Contracts

### Endpoints

```
GET    /reports/{upload_id}/monthly
       Query:  year: int, month: int, language: str = "es"
       Plan:   all
       Cache:  3600s Redis key `report:{uid}:{upload_id}:monthly:{year}:{month}:{lang}`
       Response: { success, data: { upload_info, period, metrics, insights, summary } }

GET    /reports/{upload_id}/annual
       Query:  year: int, language: str = "es"
       Plan:   all
       Cache:  3600s
       Response: { success, data: { upload_info, period, monthly_breakdown, annual_summary, insights } }

POST   /reports/{upload_id}/export/pdf
       Body:  { year: int, month: int | null, language: str = "es" }
       Plan:  pro ONLY (403 if free)
       Response: { success, data: { job_id: str, status: "processing" } }

GET    /reports/jobs/{job_id}
       Plan:  all
       Response: { success, data: { status: "processing"|"completed"|"failed", download_url?, error? } }

GET    /reports/{upload_id}/export/csv
       Query:  year: int, month: int | null, language: str = "es"
       Plan:  pro ONLY (403 if free)
       Response: StreamingResponse (text/csv) with Content-Disposition attachment
```

### ReportsService

```python
class ReportsService:
    def __init__(self, db, redis_client, analytics_service: AnalyticsService):
        ...

    async def get_monthly(upload_id, user_id, year, month, language) -> dict
    async def get_annual(upload_id, user_id, year, language) -> dict
    async def export_csv(upload_id, user_id, year, month, language) -> StreamingResponse
    async def generate_pdf_task(upload_id, user_id, year, month, language) -> str  # job_id
    async def get_job_status(job_id) -> dict
```

### InsightGenerator (stateless)

```python
class InsightGenerator:
    @staticmethod
    def monthly_insights(metrics: dict, language: str) -> list[dict]:
        """Returns list of { type, title, text, severity }."""
    @staticmethod
    def annual_insights(metrics: dict, language: str) -> list[dict]:
        ...
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | InsightGenerator logic (en/es, edge cases, empty data) | Pure function tests, no DB |
| Unit | ReportsService plan check | Mock analytics, assert 403 for free users on export |
| Integration | Monthly report end-to-end | Real DB, seed trades, verify response shape |
| Integration | CSV export content | Real DB, assert `text/csv`, header row, data rows |
| Integration | Celery task dispatch | Mock worker, assert job_id returned, poll status |
| E2E | Full PDF flow (smoke) | Use `subprocess` to test WeasyPrint binary or skip in CI |

## Migration / Rollout

No migration required. Reports is a read-only layer over analytics with no new DB tables. Requires dependency installs (WeasyPrint + system libs) in Docker image.

## Open Questions

- [ ] Should annual report include YoY comparison if user has multiple years of data?
- [ ] What's the max trades/users we should support for sync CSV (10K? 100K?) — may need Celery if > threshold
