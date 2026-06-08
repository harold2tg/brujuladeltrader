# Design: uploads-module

## Architecture
```
modules/uploads/
├── __init__.py
├── models.py        # SQLAlchemy Upload model
├── schemas.py       # Pydantic request/response schemas
├── service.py       # Business logic (file storage, CRUD)
├── router.py        # FastAPI endpoints
└── storage.py       # File storage abstraction (local filesystem)
```

## Data Flow
```
Client → POST /uploads/ (multipart)
       → router validates auth
       → service validates file (ext, size, plan limit)
       → storage saves file with UUID name
       → service creates Upload record in DB
       → returns { upload_id, status: "pending" }
```

## Key Decisions

### File Storage
- Use local filesystem (STORAGE_LOCAL_PATH from .env)
- Files saved as `{uuid4}.{ext}` — never original filename
- Track stored_path in database for cleanup

### Plan Limits
- Check active uploads count before accepting
- Free plan: max 5 active uploads
- Return 403 if limit reached

### Status Tracking
- Status field: pending → processing → ready | error
- progress_pct for polling during processing
- error_message for failure details

## Models

### Upload
```python
class Upload(Base):
    __tablename__ = "uploads"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    original_name = Column(String(255), nullable=False)
    stored_name = Column(String(255), nullable=False)
    stored_path = Column(String(500), nullable=False)
    file_size_kb = Column(Integer, nullable=False)
    status = Column(String(20), default="pending")
    error_message = Column(Text, nullable=True)
    source = Column(String(20), default="file")
    total_trades = Column(Integer, nullable=True)
    date_from = Column(Date, nullable=True)
    date_to = Column(Date, nullable=True)
    period_label = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
```

## Error Handling
- 400: Invalid file type, file too large
- 403: Plan limit reached
- 404: Upload not found or not owned by user
- 422: Validation errors

## Dependencies
- `aiofiles` for async file operations
- `python-multipart` for file upload (already installed)
- auth module for user authentication
