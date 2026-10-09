"""DataSource service for broker trade data management."""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.data_sources.models import DataSource
from app.shared.exceptions import ForbiddenException, NotFoundException

logger = logging.getLogger(__name__)


class DataSourceService:
    """Service for managing DataSource records."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_data_sources(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> dict:
        """List data sources for a user with pagination."""
        user_uuid = uuid.UUID(user_id)
        offset = (page - 1) * page_size

        # Get total count
        count_result = await self.db.execute(
            select(func.count(DataSource.id)).where(DataSource.user_id == user_uuid)
        )
        total = count_result.scalar() or 0

        # Get data sources
        result = await self.db.execute(
            select(DataSource)
            .where(DataSource.user_id == user_uuid)
            .order_by(DataSource.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        data_sources = result.scalars().all()

        has_next = offset + len(data_sources) < total

        return {
            "items": data_sources,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_next": has_next,
        }

    async def get_data_source(self, data_source_id: str, user_id: str) -> DataSource:
        """Get a specific data source (must belong to the user)."""
        user_uuid = uuid.UUID(user_id)
        ds_uuid = uuid.UUID(data_source_id)

        result = await self.db.execute(
            select(DataSource).where(
                DataSource.id == ds_uuid,
                DataSource.user_id == user_uuid,
            )
        )
        data_source = result.scalar_one_or_none()

        if not data_source:
            raise NotFoundException("Data source not found")

        return data_source

    async def delete_data_source(self, data_source_id: str, user_id: str) -> bool:
        """Delete a data source and cascade to trades."""
        data_source = await self.get_data_source(data_source_id, user_id)
        await self.db.delete(data_source)
        await self.db.commit()
        logger.info(
            "Deleted data source %s for user %s (%d trades cascaded)",
            data_source_id,
            user_id,
            data_source.trade_count,
        )
        return True

    async def get_or_create_data_source(
        self,
        user_id: str,
        broker: str,
        broker_account_id: str,
        name: str,
    ) -> DataSource:
        """Idempotent: create or return existing data source.

        Uses the unique constraint (user_id, broker, broker_account_id) to
        find an existing record. If not found, creates a new one.
        """
        user_uuid = uuid.UUID(user_id)

        result = await self.db.execute(
            select(DataSource).where(
                DataSource.user_id == user_uuid,
                DataSource.broker == broker,
                DataSource.broker_account_id == broker_account_id,
            )
        )
        data_source = result.scalar_one_or_none()

        if data_source:
            # Update name if it changed
            if data_source.name != name:
                data_source.name = name
                await self.db.commit()
                await self.db.refresh(data_source)
            return data_source

        # Create new data source
        data_source = DataSource(
            user_id=user_uuid,
            broker=broker,
            broker_account_id=broker_account_id,
            name=name,
        )
        self.db.add(data_source)
        await self.db.commit()
        await self.db.refresh(data_source)

        logger.info(
            "Created data source %s for user %s (broker=%s, account=%s)",
            data_source.id,
            user_id,
            broker,
            broker_account_id,
        )
        return data_source

    async def update_sync_metadata(
        self,
        data_source_id: str,
        trades_added: int,
        first_trade_at: datetime | None,
        last_trade_at: datetime | None,
    ) -> None:
        """Update metadata after a successful sync.

        Accumulates trade_count and extends first/last trade date range.
        Sets sync_status to 'idle' on success.
        """
        ds_uuid = uuid.UUID(data_source_id)

        result = await self.db.execute(
            select(DataSource).where(DataSource.id == ds_uuid)
        )
        data_source = result.scalar_one_or_none()

        if not data_source:
            raise NotFoundException("Data source not found")

        data_source.trade_count += trades_added
        data_source.last_synced_at = datetime.now(timezone.utc)
        data_source.sync_status = "idle"

        # Extend date range
        if first_trade_at is not None:
            if data_source.first_trade_at is None or first_trade_at < data_source.first_trade_at:
                data_source.first_trade_at = first_trade_at
        if last_trade_at is not None:
            if data_source.last_trade_at is None or last_trade_at > data_source.last_trade_at:
                data_source.last_trade_at = last_trade_at

        await self.db.commit()
        await self.db.refresh(data_source)

        logger.info(
            "Updated sync metadata for data source %s: +%d trades, total=%d",
            data_source_id,
            trades_added,
            data_source.trade_count,
        )

    async def set_sync_status(self, data_source_id: str, status: str) -> None:
        """Update sync status: idle | syncing | error."""
        if status not in ("idle", "syncing", "error"):
            raise ValueError(f"Invalid sync status: {status}")

        ds_uuid = uuid.UUID(data_source_id)

        result = await self.db.execute(
            select(DataSource).where(DataSource.id == ds_uuid)
        )
        data_source = result.scalar_one_or_none()

        if not data_source:
            raise NotFoundException("Data source not found")

        data_source.sync_status = status
        await self.db.commit()
