# Tasks: unified-data-ingestion

## Review Workload Forecast

| Metric | Value |
|--------|-------|
| Estimated changed lines | ~1,500 |
| Files to create/modify/delete | 30+ |
| Risk level | High (DB migration + 7 modules) |
| Delivery strategy | `auto-chain` |
| Chained PRs recommended | Yes (4 PRs) |

---

## PR 1: Foundation + Migration (~350 lines)

### Task 1.1: Extract trade_utils from parser
**Files**: `app/shared/trade_utils.py`
**Lines**: ~60
**Dependencies**: None
**Status**: ✅ Complete

- [x] Create `app/shared/trade_utils.py`
- [x] Move `calculate_derived_fields()` from `parser/service.py`
- [x] Move `classify_session()` from `parser/service.py`
- [x] Update imports — verify no circular dependencies

### Task 1.2: DataSource Model
**Files**: `app/modules/data_sources/__init__.py`, `app/modules/data_sources/models.py`, `app/modules/data_sources/schemas.py`
**Lines**: ~50 + ~60 = ~110
**Dependencies**: None
**Status**: ✅ Complete

- [x] Create `app/modules/data_sources/__init__.py`
- [x] Create `app/modules/data_sources/models.py`
- [x] Define `DataSource` SQLAlchemy model with all required fields and constraints
- [x] Create `app/modules/data_sources/schemas.py` with response and request schemas

### Task 1.3: DataSource Schemas
**Files**: `app/modules/data_sources/schemas.py`
**Lines**: ~60
**Dependencies**: 1.2
**Status**: ✅ Complete

- [x] `DataSourceResponse` — full read schema
- [x] `DataSourceListResponse` — paginated list
- [x] `SyncRequest` — `{ mode: "day"|"month"|"year", date: str }`
- [x] `SyncResponse` — `{ job_id, status }`

### Task 1.4: Alembic Migration
**Files**: `alembic/versions/008_unified_data_ingestion.py`
**Lines**: ~120
**Dependencies**: 1.2
**Status**: ✅ Complete

- [x] Create `data_sources` table
- [x] Migrate `uploads WHERE source='ctrader'` → `data_sources`
- [x] Add `data_source_id` column to `trades` (nullable)
- [x] Copy `upload_id` → `data_source_id` for migrated trades
- [x] Delete trades linked to file uploads (not in data_sources)
- [x] Make `data_source_id` NOT NULL
- [x] Drop old FK `trades_upload_id_fkey`
- [x] Drop `upload_id` column from `trades`
- [x] Add new FK `trades_data_source_id_fkey`
- [x] Add unique partial index `idx_trades_user_deal_id` (WHERE deal_id IS NOT NULL)
- [x] Drop `uploads` table
- [x] **Rollback plan**: reverse all steps in downgrade()

### Task 1.5: Update Trade Model
**Files**: `app/modules/parser/models.py`
**Lines**: ~10
**Dependencies**: 1.4
**Status**: ✅ Complete

- [x] Rename `upload_id` → `data_source_id` in Trade model
- [x] Update FK to point to `data_sources.id`
- [x] Update relationship: `data_source = relationship("DataSource", backref="trades")`
- [x] Update `alembic/env.py` to import DataSource instead of Upload

**Validation**:
```bash
poetry run alembic upgrade head
poetry run alembic downgrade -1   # test rollback
poetry run alembic upgrade head   # re-apply
```

---

## PR 2: Backend Core — DataSource Service + cTrader Evolution (~450 lines)

### Task 2.1: DataSource Service
**Files**: `app/modules/data_sources/service.py`
**Lines**: ~150
**Dependencies**: 1.2, 1.3
**Status**: ✅ Complete

- [x] `list_data_sources(user_id, page, page_size)` — paginated list
- [x] `get_data_source(data_source_id, user_id)` — detail or 404
- [x] `delete_data_source(data_source_id, user_id)` — cascades to trades
- [x] `get_or_create_data_source(user_id, broker, broker_account_id, name)` — idempotent creation
- [x] `update_sync_metadata(data_source_id, trades_added, first_trade_at, last_trade_at)` — updates trade_count, last_synced_at, timestamps

### Task 2.2: DataSource Router
**Files**: `app/modules/data_sources/router.py`
**Lines**: ~80
**Dependencies**: 2.1
**Status**: ✅ Complete

- [x] `GET /data-sources` — list with pagination
- [x] `GET /data-sources/{id}` — detail
- [x] `DELETE /data-sources/{id}` — delete (204)
- [x] `POST /data-sources/{id}/sync` — trigger sync (placeholder)
- [x] All endpoints require auth (`get_current_active_user`)

### Task 2.3: Register DataSource Router
**Files**: `app/main.py`
**Lines**: ~5
**Dependencies**: 2.2
**Status**: ✅ Complete

- [x] Import and register `data_sources.router` in `app/main.py`

### Task 2.4: Evolve cTrader Service
**Files**: `app/modules/ctrader/service.py`
**Lines**: ~100 (modifications, net)
**Dependencies**: 2.1
**Status**: ✅ Complete

- [x] Remove synthetic Upload creation
- [x] Import `DataSourceService` instead of `Upload` model
- [x] Call `get_or_create_data_source(user_id, "ctrader", account_id, name)` at sync start
- [x] Set `data_source.sync_status = "syncing"` before fetching deals
- [x] Replace `upload.id` with `data_source.id` in trade creation
- [x] Update `calculate_derived_fields` import to `app.shared.trade_utils`
- [x] After sync: call `update_sync_metadata()` with new trades count and date range
- [x] Set `data_source.sync_status = "idle"` on success
- [x] Set `data_source.sync_status = "error"` on failure (with try/except)
- [x] Return `{ data_source_id, status, total_trades }` instead of `{ upload_id, ... }`

### Task 2.5: Update cTrader Router
**Files**: `app/modules/ctrader/router.py`
**Lines**: ~30
**Dependencies**: 2.4
**Status**: ✅ Complete

- [x] Update sync endpoint response schema (return data_source_id instead of upload_id)
- [x] No upload_id references remain in cTrader module

### Task 2.6: cTrader Service Tests
**Files**: `tests/modules/test_ctrader.py` (update existing)
**Lines**: ~80
**Dependencies**: 2.4
**Status**: ✅ Complete

- [x] Test sync creates DataSource (not Upload)
- [x] Test sync is idempotent — sync twice, same deal_id not duplicated
- [x] Test sync updates DataSource metadata (trade_count, last_synced_at)
- [x] Test sync status transitions (idle → syncing → idle)
- [x] Mock cTrader client — no real API calls
- [x] 12 unit tests for DataSourceService CRUD + metadata
- [x] 2 integration tests for cTrader sync with DataSource

---

## PR 3: Downstream Modules (~350 lines)

### Task 3.1: Update Analytics Service
**Files**: `app/modules/analytics/service.py`
**Lines**: ~100
**Dependencies**: 1.5

- [ ] Replace all `upload_id` → `data_source_id` references
- [ ] Update `_get_trades_df()` query: filter by `data_source_id`
- [ ] Add optional `start_date` parameter — filter `trades.closed_at >= start_date`
- [ ] Add optional `end_date` parameter — filter `trades.closed_at <= end_date`
- [ ] Add optional `granularity` parameter (week|month|year) for time-series grouping
- [ ] Update Redis cache keys: `analytics:{data_source_id}:{endpoint}:{date_params_hash}`

### Task 3.2: Update Analytics Router
**Files**: `app/modules/analytics/router.py`
**Lines**: ~40
**Dependencies**: 3.1

- [ ] Rename path param `{upload_id}` → `{data_source_id}` in all endpoints
- [ ] Add query params `start_date`, `end_date`, `granularity` to all analytics endpoints
- [ ] Update `GET /analytics/compare?ids=...` to use data_source_ids

### Task 3.3: Update Alerts Module
**Files**: `app/modules/alerts/models.py`, `app/modules/alerts/service.py`
**Lines**: ~40
**Dependencies**: 1.5

- [ ] `alerts/models.py`: Rename `upload_id` → `data_source_id` in `alert_history` model
- [ ] `alerts/service.py`: Update all `upload_id` references → `data_source_id`
- [ ] Update alert trigger logic to work with data_source_id

### Task 3.4: Update AI Engine Module
**Files**: `app/modules/ai_engine/service.py`, `app/modules/ai_engine/router.py`
**Lines**: ~40
**Dependencies**: 1.5

- [ ] `service.py`: Update cache keys from `ai:{upload_id}:...` → `ai:{data_source_id}:...`
- [ ] `service.py`: Update trade query to use `data_source_id`
- [ ] `router.py`: Rename path param `{upload_id}` → `{data_source_id}`

### Task 3.5: Update Reports Module
**Files**: `app/modules/reports/service.py`, `app/modules/reports/router.py`
**Lines**: ~30
**Dependencies**: 1.5

- [ ] `service.py`: Update references from `upload_id` → `data_source_id`
- [ ] `router.py`: Rename path param if applicable

### Task 3.6: Delete Old Modules
**Files**: `app/modules/uploads/`, `app/modules/parser/`
**Lines**: ~0 (deletions only)
**Dependencies**: 3.1, 3.3, 3.4, 3.5 (all downstream must be updated first)

- [ ] Delete `app/modules/uploads/` entire directory
- [ ] Delete `app/modules/parser/` entire directory (trade_utils already extracted in Task 1.1)
- [ ] Remove imports from `app/main.py` if any remain
- [ ] Verify no dangling imports: `grep -r "from app.modules.uploads" app/` and `grep -r "from app.modules.parser" app/`

### Task 3.7: Update Downstream Tests
**Files**: `tests/modules/test_analytics.py`, `tests/modules/test_alerts.py`
**Lines**: ~60
**Dependencies**: 3.1, 3.3

- [ ] Update test fixtures: replace Upload with DataSource
- [ ] Update test assertions: `upload_id` → `data_source_id`
- [ ] Add tests for date filtering (start_date, end_date, granularity)
- [ ] Delete `tests/modules/test_uploads.py` and `tests/modules/test_parser.py`

---

## PR 4: Frontend (~350 lines)

### Task 4.1: Create Data Sources API Client + Hook
**Files**: `frontend-bdt/lib/api/data-sources.ts`, `frontend-bdt/lib/hooks/useDataSources.ts`
**Lines**: ~80
**Dependencies**: PR 2 (backend endpoints must exist)

- [ ] Create `lib/api/data-sources.ts`:
  - `getDataSources(page, pageSize)` → paginated list
  - `getDataSource(id)` → detail
  - `deleteDataSource(id)` → 204
  - `syncDataSource(id, mode, date)` → trigger sync
- [ ] Create `lib/hooks/useDataSources.ts`:
  - `useDataSources()` — SWR hook for list
  - `useDataSource(id)` — SWR hook for detail
  - `useSyncDataSource()` — mutation hook

### Task 4.2: Create Data Sources Page + Components
**Files**: `frontend-bdt/app/[locale]/(dashboard)/data-sources/page.tsx`, `frontend-bdt/components/data-sources/DataSourceList.tsx`
**Lines**: ~150
**Dependencies**: 4.1

- [ ] Create `data-sources/page.tsx` — list all data sources
- [ ] Create `DataSourceList.tsx` — table/card list with:
  - Broker icon + name
  - Trade count
  - Last synced at
  - Sync button
  - Delete button with confirmation
- [ ] Update navigation: "Uploads" → "Data Sources"

### Task 4.3: Delete Upload Frontend Code
**Files**: `frontend-bdt/app/[locale]/(dashboard)/uploads/`, `frontend-bdt/components/uploads/`, `frontend-bdt/lib/api/uploads.ts`, `frontend-bdt/lib/hooks/useUploads.ts`
**Lines**: ~0 (deletions only)
**Dependencies**: 4.2 (new data sources page must exist first)

- [ ] Delete `frontend-bdt/app/[locale]/(dashboard)/uploads/` directory
- [ ] Delete `frontend-bdt/components/uploads/` directory
- [ ] Delete `frontend-bdt/lib/api/uploads.ts`
- [ ] Delete `frontend-bdt/lib/hooks/useUploads.ts`
- [ ] Update any imports that referenced deleted files

### Task 4.4: Update Analytics Frontend
**Files**: `frontend-bdt/app/[locale]/(dashboard)/analytics/page.tsx`, `frontend-bdt/app/[locale]/(dashboard)/analytics/[id]/page.tsx`
**Lines**: ~80
**Dependencies**: 4.1, PR 3 (analytics API updated)

- [ ] Replace `useUploads()` → `useDataSources()`
- [ ] Update all API calls: `/uploads/{id}` → `/data-sources/{id}`
- [ ] Add period selector component (week/month/year)
- [ ] Pass `start_date`, `end_date`, `granularity` to analytics endpoints
- [ ] Update analytics detail page to use `data_source_id`

### Task 4.5: Update Remaining Frontend Pages
**Files**: Alert, AI, Reports pages that reference uploads
**Lines**: ~40
**Dependencies**: 4.1, PR 3

- [ ] Update alert pages: upload references → data source
- [ ] Update AI pages: upload references → data source
- [ ] Update reports pages: upload references → data source
- [ ] Run `npm run build` — verify zero TypeScript errors

---

## Dependencies Graph

```
PR 1: Foundation + Migration
  1.1 (trade_utils) ──→ 2.4 (ctrader evolution)
  1.2 (DataSource model) ──→ 1.3 (schemas) ──→ 2.1 (service) ──→ 2.2 (router) ──→ 2.3 (register)
                         ──→ 1.4 (migration) ──→ 1.5 (Trade model update) ──→ 3.1, 3.3, 3.4, 3.5
  1.5 ──→ 3.1 (analytics) ──→ 3.2 (analytics router)
       ──→ 3.3 (alerts)
       ──→ 3.4 (ai_engine)
       ──→ 3.5 (reports)
  3.1 + 3.3 + 3.4 + 3.5 ──→ 3.6 (delete old modules)

PR 2: Backend Core
  2.1 ──→ 2.4 (ctrader evolution) ──→ 2.5 (ctrader router) ──→ 2.6 (tests)

PR 3: Downstream (after PR 1)
  All tasks depend on 1.5 (Trade model updated)
  3.6 depends on all other 3.x tasks

PR 4: Frontend (after PR 2 + PR 3)
  4.1 ──→ 4.2 (data sources page) ──→ 4.3 (delete uploads UI)
  4.1 ──→ 4.4 (analytics UI)
  4.1 ──→ 4.5 (remaining pages)
```

## Commit Strategy

### PR 1: Foundation + Migration
1. `feat(data-sources): extract trade_utils from parser module`
2. `feat(data-sources): add DataSource model and schemas`
3. `feat(data-sources): add Alembic migration for unified data ingestion`
4. `refactor(parser): rename upload_id to data_source_id in Trade model`

### PR 2: Backend Core
5. `feat(data-sources): add DataSource service and router`
6. `feat(ctrader): evolve sync to use DataSource instead of Upload`
7. `test(ctrader): update tests for DataSource-based sync`

### PR 3: Downstream Modules
8. `feat(analytics): update to data_source_id + add date range filters`
9. `refactor(alerts,ai_engine,reports): rename upload_id to data_source_id`
10. `chore: delete uploads and parser modules`
11. `test: update downstream tests for data_source_id`

### PR 4: Frontend
12. `feat(frontend): add data sources API client and hooks`
13. `feat(frontend): add data sources page and components`
14. `chore(frontend): delete upload pages and components`
15. `feat(frontend): update analytics with date range filters`
16. `refactor(frontend): update alert, AI, reports pages`

## Validation Commands

```bash
# Backend
poetry run alembic upgrade head
poetry run pytest tests/ -v --cov=app --cov-report=term-missing
poetry run ruff check app/
grep -r "upload_id" app/    # should return nothing
grep -r "from app.modules.uploads" app/   # should return nothing
grep -r "from app.modules.parser" app/    # should return nothing

# Frontend
cd frontend-bdt && npm run build   # zero TypeScript errors
cd frontend-bdt && npm run lint    # zero lint errors
```
