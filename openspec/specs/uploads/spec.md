# Spec: uploads

## Capability
File upload management for CSV/XLSX trade history files in La Brújula del Trader.

## Requirements

### RF-UP-01: Upload File
- Endpoint: `POST /uploads/`
- Header: `Authorization: Bearer <access_token>`
- Content-Type: `multipart/form-data`
- Body: `{ file: UploadFile, period_label?: str }`
- Validation:
  - File extension must be `.csv` or `.xlsx` (400 otherwise)
  - File size max 10 MB (400 otherwise)
  - User must have < 5 active uploads for free plan (403 otherwise)
- File storage: `{uuid4}.{ext}` — never original filename
- Response: `{ success: true, data: { upload_id, status: "pending" } }`

### RF-UP-02: List Uploads
- Endpoint: `GET /uploads/`
- Header: `Authorization: Bearer <access_token>`
- Query params: `page?: int, limit?: int`
- Response: `{ success: true, data: { items: [...], total, page, limit } }`
- Notes: Returns uploads for current user only, ordered by created_at desc

### RF-UP-03: Get Upload Detail
- Endpoint: `GET /uploads/{id}`
- Header: `Authorization: Bearer <access_token>`
- Response: `{ success: true, data: { id, original_name, status, file_size_kb, total_trades, date_from, date_to, period_label, created_at, processed_at } }`
- Errors: `404 Not Found` if upload doesn't belong to user

### RF-UP-04: Get Upload Status
- Endpoint: `GET /uploads/{id}/status`
- Header: `Authorization: Bearer <access_token>`
- Response: `{ success: true, data: { status, progress_pct, error_message? } }`
- Notes: Useful for polling during async processing

### RF-UP-05: Delete Upload
- Endpoint: `DELETE /uploads/{id}`
- Header: `Authorization: Bearer <access_token>`
- Response: `{ success: true, message: "Upload deleted" }`
- Actions: Delete file from disk + delete upload record + cascade delete trades
- Errors: `404 Not Found` if upload doesn't belong to user

## Scenarios

### Scenario 1: Upload CSV Success
```
GIVEN an authenticated user with < 5 uploads
WHEN POST /uploads/ with valid CSV file
THEN file is saved with UUID filename
AND response contains upload_id with status "pending"
```

### Scenario 2: Upload Invalid Extension
```
GIVEN an authenticated user
WHEN POST /uploads/ with .txt file
THEN response is 400 Bad Request
AND error indicates only csv/xlsx allowed
```

### Scenario 3: Upload Over Size Limit
```
GIVEN an authenticated user
WHEN POST /uploads/ with file > 10MB
THEN response is 400 Bad Request
AND error indicates file too large
```

### Scenario 4: Upload Over Free Plan Limit
```
GIVEN an authenticated user with 5 active uploads
WHEN POST /uploads/ with new file
THEN response is 403 Forbidden
AND error indicates plan limit reached
```

### Scenario 5: List Uploads Success
```
GIVEN an authenticated user with 3 uploads
WHEN GET /uploads/
THEN response contains list of 3 uploads
AND ordered by created_at desc
```

### Scenario 6: Get Upload Detail Success
```
GIVEN an authenticated user with an upload
WHEN GET /uploads/{id}
THEN response contains full upload details
```

### Scenario 7: Get Upload Status
```
GIVEN an authenticated user with a processing upload
WHEN GET /uploads/{id}/status
THEN response contains status and progress_pct
```

### Scenario 8: Delete Upload Success
```
GIVEN an authenticated user with an upload
WHEN DELETE /uploads/{id}
THEN file is deleted from disk
AND upload record is deleted
AND trades are cascade deleted
```

### Scenario 9: Delete Upload Not Found
```
GIVEN an authenticated user
WHEN DELETE /uploads/{id} with invalid id
THEN response is 404 Not Found
```

## Data Model

### uploads table
```sql
id             UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
original_name  VARCHAR(255) NOT NULL
stored_name    VARCHAR(255) NOT NULL      -- uuid.ext
stored_path    VARCHAR(500) NOT NULL
file_size_kb   INTEGER NOT NULL
status         VARCHAR(20) NOT NULL DEFAULT 'pending'
               -- pending | processing | ready | error
error_message  TEXT
source         VARCHAR(20) NOT NULL DEFAULT 'file'  -- file | ctrader
total_trades   INTEGER
date_from      DATE
date_to        DATE
period_label   VARCHAR(50)               -- ej: "Mayo 2025", "2025"
created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
processed_at   TIMESTAMPTZ
```

### Expected CSV Format (cTrader)
```csv
"Símbolo","Dirección de apertura","Hora de cierre (UTC-5)","Precio de entrada","Precio de cierre","Cantidad de Cierre","$ neto","Saldo $"
"XAUUSD","Sell","08/06/2026 14:25:40.501","4326.73","4326.68","0.02 Lotes","0.10","845.36"
```

**Column Details:**
- `Símbolo`: Symbol (e.g., XAUUSD)
- `Dirección de apertura`: Direction (Buy | Sell)
- `Hora de cierre (UTC-5)`: Close time format `DD/MM/YYYY HH:MM:SS.fff`
- `Precio de entrada`: Entry price (numeric with decimals)
- `Precio de cierre`: Close price (numeric with decimals)
- `Cantidad de Cierre`: Close quantity (format: `"0.02 Lotes"` — extract number only)
- `$ neto`: Net PnL (can be negative, e.g., `"-4.94"`)
- `Saldo $`: Balance (cumulative, may contain `\xa0` as thousands separator)

## API Response Format

```python
# Success
{ "success": True, "data": { ... }, "message": "Optional description" }

# Error
{ "detail": "Human-readable message", "code": "ERROR_CODE_SNAKE_CASE" }
```

## Dependencies
- auth module (User model, get_current_active_user)
- PostgreSQL (upload storage)
- Local filesystem (file storage at STORAGE_LOCAL_PATH)

## Acceptance Criteria
- [ ] POST /uploads/ accepts only .csv and .xlsx files
- [ ] POST /uploads/ rejects files > 10MB
- [ ] POST /uploads/ enforces free plan limit (5 uploads)
- [ ] POST /uploads/ saves file with UUID filename
- [ ] GET /uploads/ returns paginated list for current user
- [ ] GET /uploads/{id} returns upload details
- [ ] GET /uploads/{id}/status returns processing status
- [ ] DELETE /uploads/{id} removes file and record
- [ ] All endpoints require valid access token
- [ ] Tests pass with >= 80% coverage
