# Proposal: uploads-module

## Intent
Implement file upload management for CSV/XLSX trade history files. This is the data ingestion layer — without it, no analysis can happen.

## Scope
- POST /uploads/ — file upload with validation
- GET /uploads/ — list user uploads (paginated)
- GET /uploads/{id} — upload detail
- GET /uploads/{id}/status — processing status
- DELETE /uploads/{id} — delete upload + file

## Approach
1. Create Upload model in SQLAlchemy
2. Implement file storage service (local filesystem)
3. Create schemas for request/response
4. Implement service layer with business logic
5. Create router with all endpoints
6. Register router in main.py
7. Write tests

## Risk Assessment
- **Low risk**: Standard CRUD operations
- **Medium risk**: File system operations (need proper error handling)
- **Dependencies**: auth module (already complete)

## Out of Scope
- Async processing (Celery tasks) — will be in parser module
- cTrader integration — separate module
- File content parsing — separate module

## Estimated Size
- ~300 lines implementation
- ~150 lines tests
- **Total: ~450 lines** (within 400-line budget with minor exception)
