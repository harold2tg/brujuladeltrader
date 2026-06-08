# Proposal: parser-module

## Intent
Parse CSV/XLSX trade history files from cTrader and insert trades into database. This is the data processing layer that transforms raw files into structured trade data.

## Scope
- Parse CSV files with cTrader format
- Detect columns by name (not position)
- Validate required columns exist
- Calculate derived fields (hour, day, session, is_winner)
- Insert trades in batch
- Update upload status

## Approach
1. Create Trade model in SQLAlchemy
2. Implement parser service with pandas
3. Implement normalizer for data cleaning
4. Implement validator for column validation
5. Create Celery task for async processing
6. Write tests

## Risk Assessment
- **Medium risk**: CSV parsing with various edge cases
- **Medium risk**: Date/timezone handling
- **Dependencies**: uploads module (already complete)

## Out of Scope
- File upload (already in uploads module)
- Analytics calculations (separate module)
- AI analysis (separate module)

## Estimated Size
- ~400 lines implementation
- ~200 lines tests
- **Total: ~600 lines** (over 400-line budget)
