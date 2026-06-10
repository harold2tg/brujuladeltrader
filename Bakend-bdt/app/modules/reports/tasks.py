"""Celery tasks for reports module."""

import json
import logging

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)


def generate_report_pdf_sync(
    job_id: str,
    upload_id: str,
    user_id: str,
    year: int,
    month: int | None,
    language: str,
) -> None:
    """Generate PDF report synchronously (for inline fallback or Celery worker).

    This function runs in the Celery worker or as inline fallback.
    It does NOT use async — designed for sync Celery execution.
    """
    from jinja2 import Environment, FileSystemLoader
    from weasyprint import HTML

    from app.database import sync_session_factory
    from app.modules.analytics.metrics import (
        calculate_by_hour,
        calculate_by_session,
        calculate_global_metrics,
    )
    from app.modules.parser.models import Trade
    from app.modules.reports.insights import InsightGenerator
    from sqlalchemy import select

    def update_job(status: str, **kwargs):
        """Update job status in Redis."""
        try:
            client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            data = {"status": status, **kwargs}
            client.setex(f"report:job:{job_id}", 3600, json.dumps(data))
            client.close()
        except Exception as e:
            logger.error("Failed to update job status: %s", e)

    try:
        update_job("processing")

        # Get trades from DB (sync session)
        with sync_session_factory() as session:
            result = session.execute(
                select(Trade).where(Trade.upload_id == upload_id)
            )
            trades = result.scalars().all()

            if not trades:
                update_job("failed", error="No trades found")
                return

            # Build DataFrame-like data
            import pandas as pd

            data = [
                {
                    "net_pnl": float(t.net_pnl),
                    "hour_of_day": t.hour_of_day,
                    "day_of_week": t.day_of_week,
                    "month": t.month,
                    "session": t.session,
                    "direction": t.direction,
                    "balance": float(t.balance) if t.balance else 0.0,
                }
                for t in trades
            ]
            df = pd.DataFrame(data)

        # Calculate metrics
        global_metrics = calculate_global_metrics(df)
        by_hour = calculate_by_hour(df)
        by_session = calculate_by_session(df)

        # Generate insights
        insights = InsightGenerator.monthly_insights(global_metrics, language)

        # Render HTML template
        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template("report.html")

        html_content = template.render(
            upload_id=upload_id,
            year=year,
            month=month,
            language=language,
            metrics=global_metrics,
            by_hour=by_hour,
            by_session=by_session,
            insights=insights,
        )

        # Generate PDF
        pdf_bytes = HTML(string=html_content).write_pdf()

        # Store PDF in Redis (base64 encoded)
        import base64

        pdf_b64 = base64.b64encode(pdf_bytes).decode()
        update_job(
            "completed",
            pdf_data=pdf_b64,
            filename=f"report_{year}" + (f"_{month:02d}" if month else "") + ".pdf",
        )

        logger.info("PDF generated successfully for job %s", job_id)

    except Exception as e:
        logger.error("PDF generation failed: %s", e)
        update_job("failed", error=str(e))


# Try to import os at module level
import os
