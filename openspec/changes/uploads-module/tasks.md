# Tasks: uploads-module

## Task 1: Create Upload Model
- [ ] Create `app/modules/uploads/models.py`
- [ ] Define Upload SQLAlchemy model
- [ ] Add relationship to User model
- **Files**: `app/modules/uploads/models.py`
- **Estimate**: ~40 lines

## Task 2: Create Storage Service
- [ ] Create `app/modules/uploads/storage.py`
- [ ] Implement local filesystem storage
- [ ] Methods: save_file, delete_file, get_file_path
- **Files**: `app/modules/uploads/storage.py`
- **Estimate**: ~60 lines

## Task 3: Create Schemas
- [ ] Create `app/modules/uploads/schemas.py`
- [ ] Define request/response schemas
- [ ] Include pagination schema
- **Files**: `app/modules/uploads/schemas.py`
- **Estimate**: ~50 lines

## Task 4: Create Service
- [ ] Create `app/modules/uploads/service.py`
- [ ] Implement upload_file, list_uploads, get_upload, get_status, delete_upload
- [ ] Add plan limit validation
- **Files**: `app/modules/uploads/service.py`
- **Estimate**: ~120 lines

## Task 5: Create Router
- [ ] Create `app/modules/uploads/router.py`
- [ ] Implement all 5 endpoints
- [ ] Add proper error handling
- **Files**: `app/modules/uploads/router.py`
- **Estimate**: ~80 lines

## Task 6: Register Router
- [ ] Create `app/modules/uploads/__init__.py`
- [ ] Register router in `app/main.py`
- **Files**: `app/modules/uploads/__init__.py`, `app/main.py`
- **Estimate**: ~10 lines

## Task 7: Add Dependencies
- [ ] Add `aiofiles` to pyproject.toml
- [ ] Update poetry.lock
- **Files**: `pyproject.toml`
- **Estimate**: ~5 lines

## Task 8: Write Tests
- [ ] Create `tests/modules/test_uploads.py`
- [ ] Test all 5 endpoints
- [ ] Test validation errors
- [ ] Test plan limits
- **Files**: `tests/modules/test_uploads.py`
- **Estimate**: ~150 lines

## Total Estimate
- Implementation: ~365 lines
- Tests: ~150 lines
- **Total: ~515 lines** (slightly over 400-line budget)

## Notes
- File operations need proper error handling
- Use async file operations with aiofiles
- Plan limit check should be atomic
- Consider adding file cleanup on delete
