# Proposal: unified-data-ingestion

## Intent

Replace the manual file upload flow with a unified broker data source abstraction. Remove CSV file uploads entirely. Keep cTrader as the sole broker integration, but design the architecture so additional brokers (MetaTrader, Binance, etc.) can be added as new DataSource providers.

User requirements:
1. **No duplicate data**: Sync must be idempotent — deduplicate by broker deal/trade ID. Only new trades are inserted.
2. **Time segmentation**: Trades must be queryable/filterable by week, month, or year periods.
3. **Multi-broker ready**: Architecture must support adding new brokers without restructuring the core.

## Scope

### In Scope
- **Create `DataSource` model** — replaces `Upload`, represents a collection of trades from a broker
- **Rename `Trade.upload_id` → `Trade.data_source_id`** — FK still NOT NULL, points to DataSource
- **Evolve cTrader module** — creates real DataSource instead of synthetic Upload; sync is idempotent
- **Extract `calculate_derived_fields`** — move from parser to shared utility (used by all brokers)
- **Update downstream modules** — analytics, alerts, ai_engine, reports change upload_id → data_source_id
- **Add time segmentation to analytics** — query params: start_date, end_date, granularity (week|month|year)
- **Create DataSource endpoints**:
  - `GET /data-sources` — list user's data sources
  - `GET /data-sources/{id}` — detail with metadata (trade_count, date_range, sync_status)
  - `DELETE /data-sources/{id}` — delete data source + all its trades
  - `POST /data-sources/{id}/sync` — trigger sync from broker (delegates to broker-specific logic)
- **Update frontend**:
  - Remove upload pages, dropzone, upload list
  - Rename "Uploads" to "Data Sources" in navigation
  - Add period selector to analytics (week/month/year)
  - Update analytics, alerts, AI, reports pages to use data_source_id
- **Database migration**:
  - Create `data_sources` table
  - Migrate existing `uploads` rows (filter source="ctrader") → `data_sources`
  - Rename `trades.upload_id` → `trades.data_source_id`
  - Drop `uploads` table
- **Remove modules**:
  - `uploads/` — model, router, service, storage, schemas
  - `parser/` — service, normalizer, validators (keep only `calculate_derived_fields` in shared utils)
  - Frontend upload pages and components

### Out of Scope
- Implementing MetaTrader or Binance brokers (architecture supports it, but implementation is future work)
- Changing the Trade model schema (fields stay the same)
- Modifying the cTrader TCP/Protobuf client (it already works)
- Real-time trade streaming (future enhancement)

## Approach

### Phase 1: Database Schema Migration
1. Create Alembic migration:
   - Create `data_sources` table (id, user_id, broker, broker_account_id, name, sync_status, last_synced_at, trade_count, first_trade_at, last_trade_at, created_at, updated_at)
   - Insert into `data_sources` from `uploads WHERE source='ctrader'` (map fields)
   - Add `data_source_id` column to `trades` (nullable temporarily)
   - Populate `trades.data_source_id` from `trades.upload_id` (lookup in migration)
   - Drop FK constraint on `upload_id`, add FK on `data_source_id` (NOT NULL)
   - Drop `upload_id` column from `trades`
   - Drop `uploads` table
2. Test migration on development database

### Phase 2: Backend - DataSource Model and Service
1. Create `DataSource` model in `app/modules/data_sources/models.py`
2. Create schemas in `app/modules/data_sources/schemas.py`
3. Create service in `app/modules/data_sources/service.py`:
   - `list_data_sources(user_id)` — paginated list
   - `get_data_source(data_source_id, user_id)` — detail
   - `delete_data_source(data_source_id, user_id)` — cascades to trades
   - `create_or_get_data_source(user_id, broker, broker_account_id, name)` — idempotent creation
4. Create router in `app/modules/data_sources/router.py`:
   - `GET /data-sources`
   - `GET /data-sources/{id}`
   - `DELETE /data-sources/{id}`
5. Register router in `main.py`

### Phase 3: Backend - Evolve cTrader Module
1. Update `ctrader/service.py`:
   - Remove synthetic Upload creation (line 221-232)
   - Call `data_sources.create_or_get_data_source(user_id, "ctrader", account_id, name)`
   - Use returned DataSource ID for trade creation
   - Update DataSource metadata after sync (trade_count, last_synced_at, last_trade_at)
2. Add `POST /data-sources/{id}/sync` endpoint that delegates to cTrader sync logic
3. Verify deduplication logic still works (by deal_id)

### Phase 4: Backend - Extract Shared Utilities
1. Move `calculate_derived_fields` from `parser/service.py` to `app/utils/trade_utils.py`
2. Update cTrader service to import from `trade_utils`
3. Delete `parser/` module entirely

### Phase 5: Backend - Update Downstream Modules
1. **analytics/service.py**:
   - Change all `upload_id` references → `data_source_id`
   - Add query params: `start_date`, `end_date`, `granularity` (week|month|year)
   - Update `_get_trades_df` to filter by date range
2. **analytics/router.py**:
   - Add query params to all analytics endpoints
3. **alerts/**:
   - Change `upload_id` → `data_source_id` in models and service
4. **ai_engine/service.py**:
   - Change cache keys from `upload_id` → `data_source_id`
5. **reports/service.py**:
   - Change references from `upload_id` → `data_source_id`

### Phase 6: Frontend - Remove Uploads, Add Data Sources
1. Delete `frontend-bdt/app/[locale]/(dashboard)/uploads/` directory
2. Delete `frontend-bdt/components/uploads/` directory
3. Delete `frontend-bdt/lib/api/uploads.ts`
4. Delete `frontend-bdt/lib/hooks/useUploads.ts`
5. Create `frontend-bdt/app/[locale]/(dashboard)/data-sources/page.tsx` — list data sources
6. Create `frontend-bdt/components/data-sources/DataSourceList.tsx`
7. Create `frontend-bdt/lib/api/data-sources.ts`
8. Create `frontend-bdt/lib/hooks/useDataSources.ts`
9. Update navigation to replace "Uploads" with "Data Sources"

### Phase 7: Frontend - Update Downstream Pages
1. **analytics/page.tsx**:
   - Change `useUploads()` → `useDataSources()`
   - Update all API calls to use `/data-sources` instead of `/uploads`
   - Add period selector component (week/month/year)
   - Pass `start_date`, `end_date`, `granularity` to analytics endpoints
2. **alerts/** pages:
   - Change upload references → data source
3. **ai_engine/** pages:
   - Change upload references → data source
4. **reports/** pages:
   - Change upload references → data source

### Phase 8: Testing and Verification
1. Run all backend tests, fix broken tests
2. Run frontend build, fix TypeScript errors
3. Test cTrader sync end-to-end:
   - Connect cTrader account
   - Sync trades for a month
   - Verify no duplicates
   - Sync again, verify no new duplicates
4. Test analytics with date filters:
   - Filter by week
   - Filter by month
   - Filter by year
5. Test data source deletion cascades to trades

## Risk Assessment

- **High risk**: Database migration — renaming FK and dropping tables. Must test on dev DB first.
- **Medium risk**: Seven backend modules reference `upload_id` — easy to miss one.
- **Medium risk**: Frontend has many pages referencing uploads — need systematic search-and-replace.
- **Low risk**: cTrader sync logic already works and is idempotent.
- **Low risk**: Analytics date filtering is straightforward SQL.

**Mitigations**:
- Test migration on dev DB before production
- Use grep to find ALL references to `upload_id` before starting
- Keep `calculate_derived_fields` in shared location to avoid breaking cTrader
- Phase-by-phase approach allows incremental testing

## Dependencies

- `auth` module (already complete)
- `users` module (already complete)
- `ctrader` module (already complete)
- No external dependencies

## Estimated Size

- Phase 1 (Migration): ~100 lines
- Phase 2 (DataSource model/service): ~300 lines
- Phase 3 (cTrader evolution): ~150 lines (mostly deletions)
- Phase 4 (Extract utilities): ~50 lines
- Phase 5 (Update downstream): ~200 lines (mostly renames)
- Phase 6 (Frontend data sources): ~400 lines
- Phase 7 (Frontend updates): ~300 lines (mostly renames)
- Phase 8 (Testing): ~0 lines (verification only)

**Total: ~1,500 lines** (across 8 phases, ~188 lines/phase average)

This exceeds the 400-line per-task budget, so it MUST be split into multiple tasks. Each phase is a natural task boundary.

## Success Criteria

- [ ] Manual file upload is completely removed (no endpoints, no UI)
- [ ] cTrader sync creates real DataSource (not synthetic Upload)
- [ ] cTrader sync is idempotent — running it twice produces no duplicates
- [ ] Analytics can filter by week, month, or year
- [ ] Architecture supports adding MetaTrader/Binance as new brokers without schema changes
- [ ] All existing tests pass (after fixing references)
- [ ] Frontend builds without errors
- [ ] Manual smoke test: connect cTrader, sync, view analytics with date filters

## Out of Scope (Explicit)

- Implementing MetaTrader or Binance brokers
- Real-time trade streaming
- Changing Trade model schema
- Modifying cTrader TCP/Protobuf client
- Multi-currency support
- Trade reconciliation across brokers
