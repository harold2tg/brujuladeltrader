"""DataSource router for broker trade data management."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_active_user
from app.modules.auth.models import User
from app.modules.data_sources.schemas import (
    DataSourceListResponse,
    DataSourceResponse,
    SyncRequest,
    SyncResponse,
)
from app.modules.data_sources.service import DataSourceService
from app.shared.responses import success_response

router = APIRouter(prefix="/data-sources", tags=["data-sources"])


def get_data_source_service(db: AsyncSession = Depends(get_db)) -> DataSourceService:
    """Dependency that provides a DataSourceService instance."""
    return DataSourceService(db)


@router.get("", response_model=dict)
async def list_data_sources(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    data_source_service: DataSourceService = Depends(get_data_source_service),
):
    """List data sources for the current user."""
    result = await data_source_service.list_data_sources(
        user_id=str(current_user.id),
        page=page,
        page_size=page_size,
    )
    return success_response(data=result)


@router.get("/{data_source_id}", response_model=dict)
async def get_data_source(
    data_source_id: str,
    current_user: User = Depends(get_current_active_user),
    data_source_service: DataSourceService = Depends(get_data_source_service),
):
    """Get detail of a specific data source."""
    data_source = await data_source_service.get_data_source(
        data_source_id=data_source_id,
        user_id=str(current_user.id),
    )
    return success_response(data=data_source)


@router.delete("/{data_source_id}", status_code=204)
async def delete_data_source(
    data_source_id: str,
    current_user: User = Depends(get_current_active_user),
    data_source_service: DataSourceService = Depends(get_data_source_service),
):
    """Delete a data source and all associated trades."""
    await data_source_service.delete_data_source(
        data_source_id=data_source_id,
        user_id=str(current_user.id),
    )


@router.post("/{data_source_id}/sync", response_model=dict)
async def sync_data_source(
    data_source_id: str,
    data: SyncRequest,
    current_user: User = Depends(get_current_active_user),
    data_source_service: DataSourceService = Depends(get_data_source_service),
):
    """Trigger a sync for this data source.

    Placeholder — actual sync logic lives in broker-specific services
    (e.g. ctrader). This endpoint validates ownership and returns a
    placeholder response until the broker-specific sync is wired up.
    """
    # Validate ownership
    data_source = await data_source_service.get_data_source(
        data_source_id=data_source_id,
        user_id=str(current_user.id),
    )

    return success_response(
        data={
            "data_source_id": str(data_source.id),
            "status": "not_implemented",
            "message": (
                f"Sync for broker '{data_source.broker}' is not yet wired "
                "through this endpoint. Use the broker-specific sync endpoint."
            ),
        },
        message="Sync placeholder",
    )
