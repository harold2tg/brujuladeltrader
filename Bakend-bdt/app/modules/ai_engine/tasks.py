"""Celery tasks for AI Engine module."""

import json
import logging

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)

CACHE_TTL = 86400  # 24 hours


def run_ai_analysis(
    job_id: str,
    upload_id: str,
    user_id: str,
    analysis_type: str,
    language: str,
) -> None:
    """Run AI analysis in Celery worker (sync context).

    Tries to call the configured AI provider. On failure, falls back to
    InsightGenerator deterministic analysis.
    """
    from app.database import async_session_factory, sync_session_factory
    from app.modules.ai_engine.prompts import ANALYSIS_CONTEXT, SYSTEM_PROMPT
    from app.modules.ai_engine.service import AiService
    from app.modules.reports.insights import InsightGenerator
    from app.modules.auth.models import User
    from app.modules.ai_engine.models import AiCredentials
    from sqlalchemy import select
    import asyncio

    def update_job(status: str, **kwargs):
        """Update job status in Redis."""
        try:
            client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            data = {"status": status, **kwargs}
            client.setex(f"ai:job:{job_id}", CACHE_TTL, json.dumps(data))
            client.close()
        except Exception as e:
            logger.error("Failed to update AI job status: %s", e)

    try:
        update_job("processing")

        # Get user's active AI credentials (sync)
        with sync_session_factory() as session:
            result = session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                update_job("failed", error="User not found")
                return

            # Get active credentials
            cred_result = session.execute(
                select(AiCredentials).where(
                    AiCredentials.user_id == user_id,
                    AiCredentials.is_active == True,  # noqa: E712
                ).order_by(AiCredentials.created_at.desc())
            )
            credentials = cred_result.scalars().all()

            # Get metrics for the upload
            from app.modules.parser.models import Trade

            trade_result = session.execute(
                select(Trade).where(Trade.upload_id == upload_id)
            )
            trades = trade_result.scalars().all()

        if not credentials:
            # No AI credentials — use deterministic fallback
            logger.info("No AI credentials for user %s, using fallback", user_id)
            _run_fallback(job_id, upload_id, user_id, analysis_type, language, trades)
            return

        # Try each active credential
        cred = credentials[0]  # Use the most recent active one
        try:
            # Run async provider call in sync context
            loop = asyncio.new_event_loop()
            result_text = loop.run_until_complete(
                _call_ai_provider(cred, analysis_type, language, trades)
            )
            loop.close()

            result_data = {
                "analysis_type": analysis_type,
                "language": language,
                "text": result_text,
                "source": cred.provider,
            }

            # Cache result
            try:
                client = redis.from_url(settings.REDIS_URL, decode_responses=True)
                cache_key = f"ai:{upload_id}:{analysis_type}:{language}"
                client.setex(cache_key, CACHE_TTL, json.dumps(result_data))
                client.close()
            except Exception:
                logger.warning("Failed to cache AI result")

            update_job("completed", result=result_data, fallback_used=False)
            logger.info("AI analysis completed for job %s via %s", job_id, cred.provider)

        except Exception as e:
            logger.error("AI provider call failed: %s, falling back", e)
            _run_fallback(job_id, upload_id, user_id, analysis_type, language, trades)

    except Exception as e:
        logger.error("AI analysis task failed: %s", e)
        update_job("failed", error=str(e))


def _run_fallback(
    job_id: str,
    upload_id: str,
    user_id: str,
    analysis_type: str,
    language: str,
    trades: list,
) -> None:
    """Run deterministic fallback analysis using InsightGenerator."""
    import json
    import redis as sync_redis

    from app.modules.reports.insights import InsightGenerator
    from app.modules.analytics.metrics import calculate_global_metrics
    import pandas as pd

    def update_job(status: str, **kwargs):
        try:
            client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            data = {"status": status, **kwargs}
            client.setex(f"ai:job:{job_id}", CACHE_TTL, json.dumps(data))
            client.close()
        except Exception as e:
            logger.error("Failed to update AI job status: %s", e)

    try:
        if not trades:
            update_job("failed", error="No trades found for analysis")
            return

        # Build DataFrame
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
        global_metrics = calculate_global_metrics(df)

        insights = InsightGenerator.monthly_insights(global_metrics, language)

        result_data = {
            "analysis_type": analysis_type,
            "language": language,
            "insights": insights,
            "source": "deterministic_fallback",
        }

        # Cache result
        try:
            client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            cache_key = f"ai:{upload_id}:{analysis_type}:{language}"
            client.setex(cache_key, CACHE_TTL, json.dumps(result_data))
            client.close()
        except Exception:
            pass

        update_job("completed", result=result_data, fallback_used=True)
        logger.info("Fallback analysis completed for job %s", job_id)

    except Exception as e:
        logger.error("Fallback analysis failed: %s", e)
        update_job("failed", error=str(e))


async def _call_ai_provider(cred, analysis_type: str, language: str, trades: list) -> str:
    """Call the AI provider asynchronously."""
    from app.modules.ai_engine.prompts import ANALYSIS_CONTEXT, SYSTEM_PROMPT

    # Build metrics summary for the prompt
    from app.modules.analytics.metrics import calculate_global_metrics
    import pandas as pd

    data = [
        {
            "net_pnl": float(t.net_pnl),
            "hour_of_day": t.hour_of_day,
            "day_of_day": t.day_of_week,
            "session": t.session,
            "direction": t.direction,
        }
        for t in trades
    ]
    df = pd.DataFrame(data)
    metrics = calculate_global_metrics(df)

    system = SYSTEM_PROMPT.get(language, SYSTEM_PROMPT["es"])
    context = ANALYSIS_CONTEXT.get(analysis_type, {}).get(language, "")
    user_prompt = f"{context}\n\nMétricas del trader:\n{json.dumps(metrics, indent=2, default=str)}"

    from app.modules.ai_engine.service import AiService

    provider = await AiService._get_provider_instance(
        None,
        cred.provider,
        cred.api_key_enc,
        cred.base_url,
        cred.model_override,
    )
    return await provider.generate(system, user_prompt)
