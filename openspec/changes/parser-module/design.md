# Design: parser-module

## Architecture
```
modules/parser/
├── __init__.py
├── models.py        # SQLAlchemy Trade model
├── schemas.py       # Pydantic schemas
├── service.py       # Parser orchestrator
├── normalizer.py    # Data cleaning and normalization
├── validators.py    # Column validation
└── tasks.py         # Celery tasks for async processing
```

## Data Flow
```
Upload (status=pending)
  → Celery task triggered
  → Parser reads CSV
  → Normalizer cleans data
  → Validator checks columns
  → Trades inserted in batch
  → Upload status = "ready"
```

## Key Decisions

### Column Detection
- Detect by name, not position
- Use fuzzy matching for column names (handle variations)
- Required columns must all be present

### Data Cleaning
- Clean \xa0 from balance column
- Extract number from "0.02 Lotes" format
- Parse dates with timezone awareness

### Derived Fields
- Calculate from closed_at timestamp
- Session classification based on hour
- is_winner = net_pnl > 0

## Models

### Trade
```python
class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    upload_id = Column(UUID, ForeignKey("uploads.id"), nullable=False)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    symbol = Column(String(20), nullable=False)
    direction = Column(String(10), nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=False)
    entry_price = Column(Numeric(12,5), nullable=False)
    close_price = Column(Numeric(12,5), nullable=False)
    lot_size = Column(Numeric(8,4), nullable=True)
    net_pnl = Column(Numeric(10,2), nullable=False)
    balance = Column(Numeric(10,2), nullable=True)
    hour_of_day = Column(SmallInteger, nullable=False)
    day_of_week = Column(SmallInteger, nullable=False)
    week_of_year = Column(SmallInteger, nullable=False)
    month = Column(SmallInteger, nullable=False)
    year = Column(SmallInteger, nullable=False)
    session = Column(String(20), nullable=False)
    is_winner = Column(Boolean, nullable=False)
    trade_number = Column(Integer, nullable=False)
```

## Error Handling
- Missing columns: mark upload as error with details
- Invalid data: skip row, log warning
- Parse errors: mark upload as error with message

## Dependencies
- pandas for CSV parsing
- celery for async processing
- redis for task queue
