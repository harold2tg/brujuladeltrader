"""Reports service — thin wrapper over AnalyticsService."""

import csv
import io
import json
import logging
import uuid
from io import StringIO

import redis.asyncio as redis
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.service import AnalyticsService
from app.modules.reports.insights import InsightGenerator
from app.modules.reports.schemas import (
    JobStatusData,
    MonthlyReportData,
    PeriodInfo,
    UploadInfo,
)
from app.modules.uploads.models import Upload
from app.shared.exceptions import NotFoundException, ForbiddenException

logger = logging.getLogger(__name__)

CACHE_TTL = 3600  # 1 hour


class ReportsService:
    """Service for generating reports from analytics data."""

    def __init__(
        self,
        db: AsyncSession,
        redis_client: redis.Redis,
        analytics_service: AnalyticsService,
    ):
        self.db = db
        self.redis = redis_client
        self.analytics = analytics_service

    def _cache_key(self, user_id: str, upload_id: str, report_type: str, **kwargs) -> str:
        """Generate Redis cache key for reports."""
        parts = [f"report:{user_id}:{upload_id}:{report_type}"]
        for k, v in sorted(kwargs.items()):
            parts.append(f"{k}:{v}")
        return ":".join(parts)

    async def _get_upload_info(self, upload_id: str, user_id: str) -> UploadInfo:
        """Get upload info, raising 404 if not found."""
        upload = await self.analytics.get_upload_or_404(upload_id, user_id)
        return UploadInfo(
            id=str(upload.id),
            original_name=upload.original_name,
            status=upload.status,
            total_trades=upload.total_trades,
            date_from=str(upload.date_from) if upload.date_from else None,
            date_to=str(upload.date_to) if upload.date_to else None,
            period_label=upload.period_label,
        )

    async def get_monthly(
        self,
        upload_id: str,
        user_id: str,
        year: int,
        month: int,
        language: str = "es",
    ) -> dict:
        """Get monthly report for a specific upload."""
        cache_key = self._cache_key(
            user_id, upload_id, "monthly", year=year, month=month, lang=language
        )

        # Check cache
        try:
            cached = await self.redis.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            logger.warning("Redis cache read failed")

        # Get metrics from analytics
        metrics = await self.analytics.get_full_metrics(upload_id, user_id)
        global_metrics = metrics.get("global", {})

        # Generate insights
        insights = InsightGenerator.monthly_insights(global_metrics, language)

        # Build summary text
        summary = self._build_monthly_summary(global_metrics, language)

        upload_info = await self._get_upload_info(upload_id, user_id)

        result = {
            "upload_info": upload_info.model_dump(),
            "period": PeriodInfo(
                year=year, month=month, label=f"{year}-{month:02d}"
            ).model_dump(),
            "metrics": metrics,
            "insights": insights,
            "summary": summary,
        }

        # Cache result
        try:
            await self.redis.setex(cache_key, CACHE_TTL, json.dumps(result))
        except Exception:
            logger.warning("Redis cache write failed")

        return result

    async def get_annual(
        self,
        upload_id: str,
        user_id: str,
        year: int,
        language: str = "es",
    ) -> dict:
        """Get annual report for a specific upload."""
        cache_key = self._cache_key(
            user_id, upload_id, "annual", year=year, lang=language
        )

        # Check cache
        try:
            cached = await self.redis.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            logger.warning("Redis cache read failed")

        # Get all metrics
        metrics = await self.analytics.get_full_metrics(upload_id, user_id)
        global_metrics = metrics.get("global", {})
        by_month = metrics.get("by_month", [])

        # Generate insights
        insights = InsightGenerator.annual_insights(global_metrics, language)

        upload_info = await self._get_upload_info(upload_id, user_id)

        result = {
            "upload_info": upload_info.model_dump(),
            "period": PeriodInfo(year=year, label=str(year)).model_dump(),
            "monthly_breakdown": by_month,
            "annual_summary": global_metrics,
            "insights": insights,
        }

        # Cache result
        try:
            await self.redis.setex(cache_key, CACHE_TTL, json.dumps(result))
        except Exception:
            logger.warning("Redis cache write failed")

        return result

    async def export_csv(
        self,
        upload_id: str,
        user_id: str,
        year: int,
        month: int | None = None,
        language: str = "es",
    ) -> StreamingResponse:
        """Export report as CSV (sync streaming)."""
        # Check plan
        await self._check_pro_plan(user_id)

        # Get full metrics
        metrics = await self.analytics.get_full_metrics(upload_id, user_id)
        global_metrics = metrics.get("global", {})
        by_hour = metrics.get("by_hour", [])
        by_session = metrics.get("by_session", [])

        # Build CSV content
        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(["Report", f"{year}" + (f"-{month:02d}" if month else "")])
        writer.writerow([])

        # Global metrics
        writer.writerow(["Global Metrics"])
        for key, value in global_metrics.items():
            writer.writerow([key, value])
        writer.writerow([])

        # By hour
        writer.writerow(["Metrics by Hour"])
        writer.writerow(["Hour", "Trades", "Wins", "Losses", "Win Rate", "Net PnL"])
        for h in by_hour:
            writer.writerow([
                h.get("label", ""),
                h.get("trades", 0),
                h.get("wins", 0),
                h.get("losses", 0),
                f"{h.get('win_rate', 0):.1%}",
                f"${h.get('net_pnl', 0):,.2f}",
            ])
        writer.writerow([])

        # By session
        writer.writerow(["Metrics by Session"])
        writer.writerow(["Session", "Trades", "Wins", "Losses", "Win Rate", "Net PnL"])
        for s in by_session:
            writer.writerow([
                s.get("label_es", s.get("session", "")),
                s.get("trades", 0),
                s.get("wins", 0),
                s.get("losses", 0),
                f"{s.get('win_rate', 0):.1%}",
                f"${s.get('net_pnl', 0):,.2f}",
            ])

        output.seek(0)

        # Generate filename
        filename = f"report_{year}"
        if month:
            filename += f"_{month:02d}"
        filename += ".csv"

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    async def generate_pdf_task(
        self,
        upload_id: str,
        user_id: str,
        year: int,
        month: int | None = None,
        language: str = "es",
    ) -> str:
        """Dispatch Celery task for async PDF generation. Returns job_id."""
        await self._check_pro_plan(user_id)

        job_id = str(uuid.uuid4())

        # Store job status in Redis
        job_data = {
            "status": "processing",
            "upload_id": upload_id,
            "user_id": user_id,
            "year": year,
            "month": month,
            "language": language,
        }

        try:
            await self.redis.setex(
                f"report:job:{job_id}", 3600, json.dumps(job_data)
            )
        except Exception:
            logger.error("Failed to create PDF job in Redis")

        # Try to dispatch Celery task, fallback to inline
        try:
            from app.worker import celery_app
            from app.modules.reports.tasks import generate_report_pdf

            celery_app.send_task(
                "app.modules.reports.tasks.generate_report_pdf",
                args=[job_id, upload_id, user_id, year, month, language],
            )
        except ImportError:
            # Celery not available — run inline (sync fallback)
            logger.warning("Celery not available, running PDF generation inline")
            import asyncio
            asyncio.create_task(
                self._generate_pdf_inline(job_id, upload_id, user_id, year, month, language)
            )

        return job_id

    async def _generate_pdf_inline(
        self,
        job_id: str,
        upload_id: str,
        user_id: str,
        year: int,
        month: int | None,
        language: str,
    ) -> None:
        """Fallback inline PDF generation when Celery is not available."""
        try:
            from app.modules.reports.tasks import generate_report_pdf_sync

            generate_report_pdf_sync(job_id, upload_id, user_id, year, month, language)
        except Exception as e:
            logger.error("PDF generation failed: %s", e)
            # Update job status to failed
            try:
                job_data = json.dumps({"status": "failed", "error": str(e)})
                await self.redis.setex(f"report:job:{job_id}", 3600, job_data)
            except Exception:
                pass

    async def get_job_status(self, job_id: str) -> dict:
        """Get PDF generation job status."""
        try:
            data = await self.redis.get(f"report:job:{job_id}")
            if data:
                return json.loads(data)
        except Exception:
            logger.warning("Redis read failed for job status")

        return {"status": "not_found"}

    async def _check_pro_plan(self, user_id: str) -> None:
        """Check if user has Pro plan. Raises 403 if not."""
        from sqlalchemy import select
        from app.modules.auth.models import User

        result = await self.db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        user = result.scalar_one_or_none()

        if not user or user.plan != "pro":
            raise ForbiddenException("Export requires Pro plan")

    def _build_monthly_summary(self, metrics: dict, language: str) -> str:
        """Build a text summary from global metrics."""
        total = metrics.get("total_trades", 0)
        win_rate = metrics.get("win_rate", 0)
        net_pnl = metrics.get("net_pnl", 0)
        pf = metrics.get("profit_factor")

        if language == "es":
            parts = [f"Realizaste {total} trades este mes."]
            parts.append(f"Tu win rate fue de {win_rate * 100:.1f}%.")
            if net_pnl >= 0:
                parts.append(f"Ganaste ${net_pnl:,.2f}.")
            else:
                parts.append(f"Perdiste ${abs(net_pnl):,.2f}.")
            if pf is not None:
                parts.append(f"Profit factor: {pf:.2f}.")
            return " ".join(parts)
        else:
            parts = [f"You took {total} trades this month."]
            parts.append(f"Your win rate was {win_rate * 100:.1f}%.")
            if net_pnl >= 0:
                parts.append(f"You earned ${net_pnl:,.2f}.")
            else:
                parts.append(f"You lost ${abs(net_pnl):,.2f}.")
            if pf is not None:
                parts.append(f"Profit factor: {pf:.2f}.")
            return " ".join(parts)
