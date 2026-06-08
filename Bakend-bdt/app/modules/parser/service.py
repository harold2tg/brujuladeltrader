"""Parser service for processing uploaded files."""

import logging
import uuid
from datetime import datetime, timezone

import pandas as pd

logger = logging.getLogger(__name__)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.parser.normalizer import (
    clean_balance,
    extract_lot_size,
    parse_datetime,
    parse_net_pnl,
)
from app.modules.parser.validators import map_columns, validate_columns
from app.modules.uploads.models import Upload
from app.shared.exceptions import BadRequestException, NotFoundException


def classify_session(hour: int) -> str:
    """
    Classify trading session based on hour (UTC-5).
    
    Sessions:
        - london_open: 07:00 - 09:00
        - ny_overlap: 09:00 - 12:00
        - ny_session: 12:00 - 17:00
        - off_hours: all other times
    """
    if 7 <= hour < 9:
        return "london_open"
    elif 9 <= hour < 12:
        return "ny_overlap"
    elif 12 <= hour < 17:
        return "ny_session"
    else:
        return "off_hours"


def calculate_derived_fields(row: dict, trade_number: int) -> dict:
    """
    Calculate derived fields for a trade.
    
    Args:
        row: Dictionary with normalized trade data
        trade_number: Sequential number within upload
        
    Returns:
        Dictionary with derived fields added
    """
    closed_at = row.get("closed_at")
    
    if closed_at is None:
        return row
    
    # Extract time components
    row["hour_of_day"] = closed_at.hour
    row["day_of_week"] = closed_at.weekday()  # 0=Monday, 6=Sunday
    row["week_of_year"] = closed_at.isocalendar()[1]
    row["month"] = closed_at.month
    row["year"] = closed_at.year
    row["session"] = classify_session(closed_at.hour)
    row["is_winner"] = row.get("net_pnl", 0) > 0
    row["trade_number"] = trade_number
    
    return row


class ParserService:
    """Parser service for processing uploaded files."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def parse_upload(self, upload_id: str) -> dict:
        """
        Parse an uploaded CSV file and insert trades.
        
        Returns:
            Dictionary with parsing results
        """
        from app.modules.parser.models import Trade
        
        # Get upload record
        result = await self.db.execute(
            select(Upload).where(Upload.id == uuid.UUID(upload_id))
        )
        upload = result.scalar_one_or_none()
        
        if not upload:
            raise NotFoundException("Upload not found")
        
        # Update status to processing
        upload.status = "processing"
        await self.db.commit()
        
        try:
            # Read CSV file
            df = pd.read_csv(upload.stored_path)
            
            # Validate columns
            missing_columns = validate_columns(df)
            if missing_columns:
                upload.status = "error"
                upload.error_message = f"Missing required columns: {', '.join(missing_columns)}"
                await self.db.commit()
                return {
                    "status": "error",
                    "error_message": upload.error_message,
                }
            
            # Map column names
            df = map_columns(df)
            
            # Parse and normalize data
            trades = []
            for idx, row in df.iterrows():
                trade_data = {
                    "upload_id": uuid.UUID(upload_id),
                    "user_id": upload.user_id,
                    "symbol": row.get("symbol"),
                    "direction": row.get("direction"),
                    "closed_at": parse_datetime(row.get("closed_at")),
                    "entry_price": row.get("entry_price"),
                    "close_price": row.get("close_price"),
                    "lot_size": extract_lot_size(row.get("lot_size")),
                    "net_pnl": parse_net_pnl(row.get("net_pnl")),
                    "balance": clean_balance(row.get("balance")),
                }
                
                # Calculate derived fields
                trade_data = calculate_derived_fields(trade_data, idx + 1)
                
                # Create Trade object
                trade = Trade(**trade_data)
                trades.append(trade)
            
            # Insert trades in batch
            self.db.add_all(trades)
            
            # Update upload record
            upload.status = "ready"
            upload.total_trades = len(trades)
            
            if trades:
                dates = [t.closed_at for t in trades if t.closed_at]
                if dates:
                    upload.date_from = min(dates).date()
                    upload.date_to = max(dates).date()
            
            upload.processed_at = datetime.now(timezone.utc)
            
            await self.db.commit()
            
            return {
                "status": "ready",
                "total_trades": len(trades),
                "date_from": upload.date_from.isoformat() if upload.date_from else None,
                "date_to": upload.date_to.isoformat() if upload.date_to else None,
            }
            
        except Exception as e:
            logger.exception("Failed to parse upload %s", upload_id)
            upload.status = "error"
            upload.error_message = str(e)
            await self.db.commit()
            
            return {
                "status": "error",
                "error_message": str(e),
            }
