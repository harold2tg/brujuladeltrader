# Spec: parser

## Capability
Parse CSV/XLSX trade history files from cTrader and insert trades into database.

## Requirements

### RF-PR-01: Parse CSV File
- Input: Upload record with stored_path
- Process:
  1. Read CSV file
  2. Detect columns by name (not position)
  3. Validate required columns exist
  4. Parse each row into Trade record
  5. Calculate derived fields (hour, day, session, is_winner)
  6. Insert trades in batch
- Required columns:
  - `Símbolo` → symbol
  - `Dirección de apertura` → direction (Buy/Sell)
  - `Hora de cierre (UTC-5)` → closed_at (format: DD/MM/YYYY HH:MM:SS.fff)
  - `Precio de entrada` → entry_price
  - `Precio de cierre` → close_price
  - `Cantidad de Cierre` → lot_size (extract number from "0.02 Lotes")
  - `$ neto` → net_pnl
  - `Saldo $` → balance (clean \xa0)
- Errors: Mark upload as `error` with missing columns list

### RF-PR-02: Calculate Derived Fields
For each trade, calculate:
- `hour_of_day`: 0-23 from closed_at
- `day_of_week`: 0=Monday, 6=Sunday
- `week_of_year`: ISO week number
- `month`: 1-12
- `year`: YYYY
- `session`: london_open | ny_overlap | ny_session | off_hours
- `is_winner`: net_pnl > 0
- `trade_number`: sequential within upload

### RF-PR-03: Session Classification
```python
def classify_session(hour: int) -> str:
    if 7 <= hour < 9:
        return "london_open"
    elif 9 <= hour < 12:
        return "ny_overlap"
    elif 12 <= hour < 17:
        return "ny_session"
    else:
        return "off_hours"
```

### RF-PR-04: Update Upload Status
- Set status to `processing` when starting
- Set status to `ready` when complete
- Set status to `error` with error_message on failure
- Set `total_trades`, `date_from`, `date_to` when complete

## Scenarios

### Scenario 1: Parse Valid CSV
```
GIVEN an upload with status "pending"
WHEN parser processes the file
THEN all trades are inserted
AND upload status changes to "ready"
AND total_trades, date_from, date_to are set
```

### Scenario 2: Parse Missing Columns
```
GIVEN an upload with CSV missing required columns
WHEN parser processes the file
THEN upload status changes to "error"
AND error_message lists missing columns
AND no trades are inserted
```

### Scenario 3: Parse Empty CSV
```
GIVEN an upload with CSV containing only headers
WHEN parser processes the file
THEN upload status changes to "ready"
AND total_trades = 0
```

### Scenario 4: Session Classification
```
GIVEN a trade closed at 10:30 UTC-5
WHEN parser calculates session
THEN session = "ny_overlap"
```

## Data Model

### trades table
```sql
id               UUID PRIMARY KEY DEFAULT gen_random_uuid()
upload_id        UUID NOT NULL REFERENCES uploads(id) ON DELETE CASCADE
user_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
symbol           VARCHAR(20) NOT NULL
direction        VARCHAR(10) NOT NULL        -- Buy | Sell
closed_at        TIMESTAMPTZ NOT NULL
entry_price      NUMERIC(12,5) NOT NULL
close_price      NUMERIC(12,5) NOT NULL
lot_size         NUMERIC(8,4)
net_pnl          NUMERIC(10,2) NOT NULL
balance          NUMERIC(10,2)
hour_of_day      SMALLINT NOT NULL
day_of_week      SMALLINT NOT NULL
week_of_year     SMALLINT NOT NULL
month            SMALLINT NOT NULL
year             SMALLINT NOT NULL
session          VARCHAR(20) NOT NULL
is_winner        BOOLEAN NOT NULL
trade_number     INTEGER NOT NULL
```

## Dependencies
- uploads module (Upload model, status updates)
- pandas (for CSV parsing)
- PostgreSQL (trade storage)

## Acceptance Criteria
- [ ] Parser detects columns by name, not position
- [ ] Missing columns mark upload as error
- [ ] Date format DD/MM/YYYY HH:MM:SS.fff is parsed correctly
- [ ] Quantity "0.02 Lotes" extracts number only
- [ ] Balance \xa0 is cleaned before parsing
- [ ] Derived fields are calculated correctly
- [ ] Session classification follows specification
- [ ] Upload status is updated correctly
- [ ] Tests pass with >= 80% coverage
