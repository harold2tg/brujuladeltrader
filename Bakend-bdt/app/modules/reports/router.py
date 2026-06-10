"""Reports router — 5 endpoints for reports and exports."""

import logging

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_active_user, get_redis
from app.modules.analytics.service import AnalyticsService
from app.modules.auth.models import User
from app.modules.reports.schemas import (
    ExportRequest,
    JobStatusData,
    MonthlyReportData,
    AnnualReportData,
)
from app.modules.reports.service import ReportsService
from app.shared.responses import success_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])


def get_reports_service(
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
) -> ReportsService:
    """Dependency that provides ReportsService."""
    analytics_service = AnalyticsService(db, redis_client)
    return ReportsService(db, redis_client, analytics_service)


@router.get("/{upload_id}/monthly")
async def get_monthly_report(
    upload_id: str,
    year: int = Query(..., description="Report year"),
    month: int = Query(..., ge=1, le=12, description="Report month"),
    language: str = Query("es", pattern="^(es|en)$"),
    current_user: User = Depends(get_current_active_user),
    service: ReportsService = Depends(get_reports_service),
):
    """Get monthly report for a specific upload."""
    result = await service.get_monthly(
        upload_id=upload_id,
        user_id=str(current_user.id),
        year=year,
        month=month,
        language=language,
    )
    return success_response(result)


@router.get("/{upload_id}/annual")
async def get_annual_report(
    upload_id: str,
    year: int = Query(..., description="Report year"),
    language: str = Query("es", pattern="^(es|en)$"),
    current_user: User = Depends(get_current_active_user),
    service: ReportsService = Depends(get_reports_service),
):
    """Get annual report for a specific upload."""
    result = await service.get_annual(
        upload_id=upload_id,
        user_id=str(current_user.id),
        year=year,
        language=language,
    )
    return success_response(result)


@router.post("/{upload_id}/export/pdf")
async def export_pdf(
    upload_id: str,
    body: ExportRequest,
    current_user: User = Depends(get_current_active_user),
    service: ReportsService = Depends(get_reports_service),
):
    """Export report as PDF (async, Pro-only)."""
    job_id = await service.generate_pdf_task(
        upload_id=upload_id,
        user_id=str(current_user.id),
        year=body.year,
        month=body.month,
        language=body.language,
    )
    return success_response(
        {"job_id": job_id, "status": "processing"},
        message="PDF generation started"
    )


@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    service: ReportsService = Depends(get_reports_service),
):
    """Get PDF generation job status."""
    result = await service.get_job_status(job_id)
    return success_response(result)


@router.get("/{upload_id}/export/csv")
async def export_csv(
    upload_id: str,
    year: int = Query(..., description="Report year"),
    month: int = Query(None, ge=1, le=12, description="Report month (optional)"),
    language: str = Query("es", pattern="^(es|en)$"),
    current_user: User = Depends(get_current_active_user),
    service: ReportsService = Depends(get_reports_service),
):
    """Export report as CSV (sync streaming, Pro-only)."""
    return await service.export_csv(
        upload_id=upload_id,
        user_id=str(current_user.id),
        year=year,
        month=month,
        language=language,
    )
