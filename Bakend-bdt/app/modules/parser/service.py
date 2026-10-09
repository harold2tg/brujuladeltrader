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
from app.shared.trade_utils import calculate_derived_fields, classify_session


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
