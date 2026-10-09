# Design: unified-data-ingestion

## Technical Approach

Replace the `Upload` model (file-centric) with a `DataSource` model (broker-centric). The `Upload` table represented a file that was uploaded — but for cTrader and future brokers, there's no file. A `DataSource` represents a broker account from which trades are synced.

The `Trade` model's FK `upload_id` is renamed to `data_source_id`. All downstream modules (analytics, alerts, ai_engine, reports) follow the rename. Time segmentation is added at the query layer (analytics endpoints).

## Architecture Decisions

### Decision: DataSource vs keeping Upload

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Keep `Upload`, repurpose it | Minimal migration, but semantically wrong (no file) | Rejected |
| New `DataSource` model, migrate | Clean separation, proper semantics, supports multi-broker | ✅ Chosen |

Rationale: The `Upload` model has file-specific fields (`stored_path`, `file_size_kb`, `original_name`) that don't apply to broker syncs. Polluting it with broker fields or leaving dead columns is worse than a clean rename migration.

### Decision: Where does `calculate_derived_fields` live?

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Keep in `parser/service.py` | Dead module (parser is removed) | Rejected |
| Move to `app/shared/utils.py` | Logical for shared utility, but file is small | ✅ Chosen |
| Create `app/shared/trade_utils.py` | Dedicated file for trade calculations | ✅ Chosen |

Rationale: Both cTrader and future brokers need `calculate_derived_fields` and `classify_session`. A dedicated `trade_utils.py` in `shared/` keeps it discoverable and broker-agnostic.

### Decision: Time segmentation approach

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Pre-aggregate in DB (materialized views) | Complex, overkill for current scale | Rejected |
| Filter at query time with date params | Simple, flexible, scales fine | ✅ Chosen |
| Add granularity column to Trade | Redundant — data already has closed_at | Rejected |

Rationale: Trades already store `closed_at` (timestamp), `hour_of_day`, `day_of_week`, `week_of_year`, `month`, `year`. Analytics just needs `start_date`, `end_date`, `granularity` query params to filter and group.

### Decision: Sync deduplication strategy

Keep existing approach: deduplicate by `deal_id` per user. The `Trade` model already has a nullable `deal_id` column. For cTrader, `deal_id` is always set. For future brokers, each provider defines its own unique trade identifier.

Add a `UNIQUE(user_id, deal_id)` constraint on trades where `deal_id IS NOT NULL` to enforce deduplication at the DB level (defense in depth — the service already checks, but DB constraint prevents race conditions).

## Data Model Changes

### New: `data_sources` table

```sql
CREATE TABLE data_sources (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    broker          VARCHAR(50) NOT NULL,           -- ctrader | metatrader | binance | ...
    broker_account_id VARCHAR(200) NOT NULL,        -- account ID from the broker
    name            VARCHAR(200) NOT NULL,          -- e.g. "cTrader - Live Account"
    sync_status     VARCHAR(20) NOT NULL DEFAULT 'idle',  -- idle | syncing | error
    last_synced_at  TIMESTAMPTZ,
    trade_count     INTEGER NOT NULL DEFAULT 0,
    first_trade_at  TIMESTAMPTZ,
    last_trade_at   TIMESTAMPTZ,
    metadata        JSONB DEFAULT '{}',             -- broker-specific extra data
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(user_id, broker, broker_account_id)      -- one DataSource per broker account per user
);
```

### Modified: `trades` table

```sql
-- Rename column
ALTER TABLE trades RENAME COLUMN upload_id TO data_source_id;

-- Rename FK constraint
ALTER TABLE trades RENAME CONSTRAINT trades_upload_id_fkey TO trades_data_source_id_fkey;

-- Add dedup constraint (partial index — only non-null deal_id)
CREATE UNIQUE INDEX idx_trades_user_deal_id
ON trades(user_id, deal_id)
WHERE deal_id IS NOT NULL;
```

### Dropped: `uploads` table

```sql
DROP TABLE uploads;
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `app/modules/data_sources/__init__.py` | Create | Package init |
| `app/modules/data_sources/models.py` | Create | `DataSource` SQLAlchemy model |
| `app/modules/data_sources/schemas.py` | Create | Pydantic request/response schemas |
| `app/modules/data_sources/service.py` | Create | CRUD + sync orchestration |
| `app/modules/data_sources/router.py` | Create | 4 endpoints |
| `app/shared/trade_utils.py` | Create | Extract `calculate_derived_fields` + `classify_session` from parser |
| `app/modules/ctrader/service.py` | Modify | Replace Upload creation with DataSource creation |
| `app/modules/ctrader/router.py` | Modify | Route sync through data_sources |
| `app/modules/ctrader/schemas.py` | Modify | Update response schemas |
| `app/modules/analytics/service.py` | Modify | `upload_id` → `data_source_id`, add date filters |
| `app/modules/analytics/router.py` | Modify | Update path params + query params |
| `app/modules/alerts/service.py` | Modify | `upload_id` → `data_source_id` |
| `app/modules/alerts/models.py` | Modify | FK rename in `alert_history` |
| `app/modules/ai_engine/service.py` | Modify | Cache key: `upload_id` → `data_source_id` |
| `app/modules/reports/service.py` | Modify | Reference rename |
| `app/main.py` | Modify | Register `data_sources.router` |
| `alembic/versions/` | New | Migration: create data_sources, migrate data, rename FK, drop uploads |
| `app/modules/uploads/` | Delete | Entire directory |
| `app/modules/parser/` | Delete | Entire directory (after extracting trade_utils) |

## API Contracts

### DataSource Endpoints

```
GET /data-sources
Response: {
    "success": true,
    "data": {
        "items": [
            {
                "id": "uuid",
                "broker": "ctrader",
                "broker_account_id": "12345",
                "name": "cTrader - Live Account",
                "sync_status": "idle",
                "last_synced_at": "2026-10-09T10:00:00Z",
                "trade_count": 377,
                "first_trade_at": "2025-01-15T08:30:00Z",
                "last_trade_at": "2026-10-09T09:45:00Z",
                "created_at": "2026-06-08T00:00:00Z"
            }
        ],
        "total": 1,
        "page": 1,
        "page_size": 20
    }
}

GET /data-sources/{id}
Response: { "success": true, "data": { ...full DataSource... } }

DELETE /data-sources/{id}
Response: 204 No Content (cascades to trades)

POST /data-sources/{id}/sync
Body: { "mode": "day"|"month"|"year", "date": "YYYY-MM-DD" }
Response: { "success": true, "data": { "job_id": "...", "status": "processing" } }
```

### Analytics Endpoints (updated)

All analytics endpoints change `{upload_id}` to `{data_source_id}` and accept optional date filters:

```
GET /analytics/{data_source_id}?start_date=2026-01-01&end_date=2026-10-31
GET /analytics/{data_source_id}/summary?granularity=month
GET /analytics/{data_source_id}/by-hour?start_date=...&end_date=...
GET /analytics/{data_source_id}/by-day?start_date=...&end_date=...
GET /analytics/{data_source_id}/by-month
GET /analytics/{data_source_id}/by-session
GET /analytics/{data_source_id}/streaks
GET /analytics/{data_source_id}/distribution
GET /analytics/{data_source_id}/simulate
GET /analytics/compare?ids=id1,id2
```

Query params (all optional):
- `start_date` (YYYY-MM-DD): filter trades closed on or after this date
- `end_date` (YYYY-MM-DD): filter trades closed on or before this date
- `granularity` (week|month|year): grouping for time-series endpoints

## cTrader Service Evolution

### Before (creates synthetic Upload)
```python
upload = Upload(
    user_id=user_id,
    original_name=f"cTrader_{mode}_{date_str}",
    stored_name=f"ctrader_{uuid.uuid4()}.sync",
    stored_path="",
    file_size_kb=0,
    status="processing",
    source="ctrader",
)
```

### After (creates real DataSource)
```python
data_source = await data_source_service.get_or_create(
    user_id=user_id,
    broker="ctrader",
    broker_account_id=account_id,
    name=f"{broker_name} - {account_name}",
)
data_source.sync_status = "syncing"
```

### Sync flow (after)
```
POST /data-sources/{id}/sync {mode, date}
  ├─► Validate DataSource exists and belongs to user
  ├─► Set sync_status = "syncing"
  ├─► Get cTrader credentials for this user
  ├─► Fetch deals from cTrader (existing client code)
  ├─► Deduplicate by deal_id (existing logic)
  ├─► Insert new trades with data_source_id
  ├─► Update DataSource metadata:
  │     trade_count += len(new_trades)
  │     last_synced_at = now()
  │     last_trade_at = max(closed_at)
  │     first_trade_at = min(first_trade_at, min(closed_at))
  ├─► Set sync_status = "idle"
  └─► Return { data_source_id, trades_added }
```

## Migration Strategy

Single Alembic migration with these steps:

```python
def upgrade():
    # 1. Create data_sources table
    op.create_table('data_sources', ...)

    # 2. Migrate existing uploads → data_sources
    #    Only uploads with source='ctrader' (file uploads are abandoned)
    op.execute("""
        INSERT INTO data_sources (id, user_id, broker, broker_account_id, name,
                                   sync_status, last_synced_at, trade_count,
                                   first_trade_at, last_trade_at, created_at, updated_at)
        SELECT
            id,
            user_id,
            'ctrader',
            COALESCE(period_label, 'unknown'),
            original_name,
            'idle',
            processed_at,
            COALESCE(total_trades, 0),
            date_from,
            date_to,
            created_at,
            COALESCE(processed_at, created_at)
        FROM uploads
        WHERE source = 'ctrader'
    """)

    # 3. Add data_source_id column to trades (nullable temporarily)
    op.add_column('trades', sa.Column('data_source_id', sa.UUID()))

    # 4. Copy upload_id → data_source_id for migrated trades
    op.execute("""
        UPDATE trades SET data_source_id = upload_id
        WHERE upload_id IN (SELECT id FROM data_sources)
    """)

    # 5. Delete trades linked to file uploads (they'll be orphaned)
    op.execute("""
        DELETE FROM trades
        WHERE upload_id NOT IN (SELECT id FROM data_sources)
    """)

    # 6. Make data_source_id NOT NULL
    op.alter_column('trades', 'data_source_id', nullable=False)

    # 7. Drop old FK and column
    op.drop_constraint('trades_upload_id_fkey', 'trades', type_='foreignkey')
    op.drop_column('trades', 'upload_id')

    # 8. Add new FK
    op.create_foreign_key('trades_data_source_id_fkey', 'trades', 'data_sources',
                          ['data_source_id'], ['id'], ondelete='CASCADE')

    # 9. Add dedup index
    op.create_index('idx_trades_user_deal_id', 'trades', ['user_id', 'deal_id'],
                    unique=True, postgresql_where=sa.text("deal_id IS NOT NULL"))

    # 10. Drop uploads table
    op.drop_table('uploads')
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | DataSource model CRUD | pytest with test DB |
| Unit | `calculate_derived_fields` in new location | Same tests as before, new import path |
| Unit | cTrader sync creates DataSource (not Upload) | Mock cTrader client, verify DataSource created |
| Unit | Dedup: sync twice = no duplicates | Mock cTrader, call sync twice, verify trade_count unchanged |
| Unit | Analytics date filtering | Create trades with known dates, filter by week/month/year |
| Integration | `GET /data-sources` | HTTP test with test DB |
| Integration | `POST /data-sources/{id}/sync` | Mock cTrader, verify end-to-end |
| Integration | Analytics with date params | Verify filtering works correctly |
| Migration | Existing cTrader data migrates | Run migration on dev DB, verify data integrity |

## Frontend Changes

### Remove
- `frontend-bdt/app/[locale]/(dashboard)/uploads/` — entire directory
- `frontend-bdt/components/uploads/` — entire directory
- `frontend-bdt/lib/api/uploads.ts`
- `frontend-bdt/lib/hooks/useUploads.ts`

### Create
- `frontend-bdt/app/[locale]/(dashboard)/data-sources/page.tsx` — list data sources
- `frontend-bdt/components/data-sources/DataSourceList.tsx`
- `frontend-bdt/lib/api/data-sources.ts`
- `frontend-bdt/lib/hooks/useDataSources.ts`

### Modify
- Navigation: "Uploads" → "Data Sources"
- `analytics/page.tsx`: `useUploads()` → `useDataSources()`, add period selector
- `analytics/[id]/page.tsx`: use `data_source_id` instead of `upload_id`
- Alert, AI, Reports pages: same rename

## Risk Mitigations

1. **Migration data loss**: File upload trades are deleted (they can't be re-imported). If the user has valuable file-uploaded data, they should export it first. Document this in release notes.

2. **Seven modules to update**: Use systematic grep for `upload_id` and `Upload` before starting. Create a checklist.

3. **Frontend breakage**: Build after each module update. TypeScript catches most issues.

4. **cTrader sync regression**: The sync logic itself doesn't change — only the DataSource creation replaces Upload creation. Test with real cTrader connection.
