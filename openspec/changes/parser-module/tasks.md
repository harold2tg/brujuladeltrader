# Tasks: parser-module

## Task 1: Create Trade Model
- [ ] Create `app/modules/parser/models.py`
- [ ] Define Trade SQLAlchemy model
- [ ] Add relationships to Upload and User
- **Files**: `app/modules/parser/models.py`
- **Estimate**: ~50 lines

## Task 2: Create Validator
- [ ] Create `app/modules/parser/validators.py`
- [ ] Implement column detection by name
- [ ] Validate required columns exist
- **Files**: `app/modules/parser/validators.py`
- **Estimate**: ~60 lines

## Task 3: Create Normalizer
- [ ] Create `app/modules/parser/normalizer.py`
- [ ] Clean \xa0 from balance
- [ ] Extract number from "0.02 Lotes"
- [ ] Parse dates with timezone
- **Files**: `app/modules/parser/normalizer.py`
- **Estimate**: ~80 lines

## Task 4: Create Parser Service
- [ ] Create `app/modules/parser/service.py`
- [ ] Implement parse_upload method
- [ ] Calculate derived fields
- [ ] Insert trades in batch
- **Files**: `app/modules/parser/service.py`
- **Estimate**: ~150 lines

## Task 5: Create Celery Task
- [ ] Create `app/modules/parser/tasks.py`
- [ ] Implement async parsing task
- [ ] Update upload status
- **Files**: `app/modules/parser/tasks.py`
- **Estimate**: ~60 lines

## Task 6: Create Schemas
- [ ] Create `app/modules/parser/schemas.py`
- [ ] Define request/response schemas
- **Files**: `app/modules/parser/schemas.py`
- **Estimate**: ~30 lines

## Task 7: Register Module
- [ ] Create `app/modules/parser/__init__.py`
- [ ] Register router in `app/main.py` (if needed)
- **Files**: `app/modules/parser/__init__.py`, `app/main.py`
- **Estimate**: ~10 lines

## Task 8: Add Dependencies
- [ ] Add `pandas` to pyproject.toml
- [ ] Update poetry.lock
- **Files**: `pyproject.toml`
- **Estimate**: ~5 lines

## Task 9: Write Tests
- [ ] Create `tests/modules/test_parser.py`
- [ ] Test column validation
- [ ] Test data normalization
- [ ] Test session classification
- [ ] Test full parsing flow
- **Files**: `tests/modules/test_parser.py`
- **Estimate**: ~200 lines

## Total Estimate
- Implementation: ~445 lines
- Tests: ~200 lines
- **Total: ~645 lines** (over 400-line budget)

## Notes
- Parser should be idempotent (safe to re-run)
- Consider batching inserts for performance
- Log warnings for skipped rows
- Handle edge cases in CSV format
