"""AI Engine service — business logic for credentials, providers, and analysis."""

import json
import logging
import uuid
from datetime import datetime, timezone

import redis.asyncio as redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.modules.ai_engine.models import AiCredentials
from app.modules.ai_engine.providers.base import AIProvider
from app.modules.ai_engine.prompts import ANALYSIS_CONTEXT, SYSTEM_PROMPT
from app.modules.auth.models import User
from app.shared.crypto import decrypt, encrypt, mask_token
from app.shared.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)

logger = logging.getLogger(__name__)

CACHE_TTL = 86400  # 24 hours
RATE_LIMIT_KEY_PREFIX = "ai_rate:"

# Default models per provider
DEFAULT_MODELS = {
    "claude": "claude-sonnet-4-20250514",
    "openai": "gpt-4o",
    "gemini": "gemini-2.0-flash",
    "ollama": "llama3",
}

AVAILABLE_PROVIDERS = [
    {
        "name": "claude",
        "display_name": "Anthropic Claude",
        "models": ["claude-sonnet-4-20250514", "claude-3-5-haiku-20241022"],
        "requires_key": True,
    },
    {
        "name": "openai",
        "display_name": "OpenAI",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        "requires_key": True,
    },
    {
        "name": "gemini",
        "display_name": "Google Gemini",
        "models": ["gemini-2.0-flash", "gemini-1.5-pro"],
        "requires_key": True,
    },
    {
        "name": "ollama",
        "display_name": "Ollama (Local)",
        "models": ["llama3", "mistral", "codellama"],
        "requires_key": False,
    },
]


class AiService:
    """Service for AI credentials, provider management, and analysis."""

    def __init__(self, db: AsyncSession, redis_client: redis.Redis):
        self.db = db
        self.redis = redis_client

    # ─── Credentials CRUD ────────────────────────────────────────────────

    async def store_credentials(
        self,
        user_id: str,
        data: dict,
    ) -> dict:
        """Store AI credentials (encrypted). Returns connection test result."""
        provider = data["provider"]
        api_key = data.get("api_key")
        base_url = data.get("base_url")
        model_override = data.get("model_override")

        # Validate provider-specific requirements
        if provider != "ollama" and not api_key:
            raise BadRequestException(f"API key is required for {provider}")
        if provider == "ollama" and not base_url:
            raise BadRequestException("Base URL is required for Ollama")

        # Test connection before storing
        test_result = await self._test_provider(provider, api_key, base_url)
        if not test_result["connected"]:
            raise BadRequestException(
                f"Could not connect to {provider}: {test_result.get('error', 'Unknown error')}"
            )

        # Encrypt API key
        api_key_enc = encrypt(api_key) if api_key else None

        # Check if user already has credentials for this provider
        existing = await self._get_credentials_by_provider(user_id, provider)
        if existing:
            existing.api_key_enc = api_key_enc
            existing.base_url = base_url
            existing.model_override = model_override
            existing.is_active = True
            existing.updated_at = datetime.now(timezone.utc)
            await self.db.commit()
            credential = existing
        else:
            credential = AiCredentials(
                user_id=uuid.UUID(user_id),
                provider=provider,
                api_key_enc=api_key_enc,
                base_url=base_url,
                model_override=model_override,
                is_active=True,
            )
            self.db.add(credential)
            await self.db.commit()

        model = model_override or DEFAULT_MODELS[provider]
        return {
            "connected": True,
            "provider": provider,
            "model": model,
        }

    async def list_credentials(self, user_id: str) -> list[dict]:
        """List all AI credentials for a user (masked keys)."""
        result = await self.db.execute(
            select(AiCredentials)
            .where(AiCredentials.user_id == uuid.UUID(user_id))
            .order_by(AiCredentials.created_at.desc())
        )
        credentials = result.scalars().all()

        return [
            {
                "id": str(c.id),
                "provider": c.provider,
                "api_key_masked": mask_token(decrypt(c.api_key_enc)) if c.api_key_enc else None,
                "base_url": c.base_url,
                "model_override": c.model_override,
                "is_active": c.is_active,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat(),
            }
            for c in credentials
        ]

    async def update_credentials(
        self,
        user_id: str,
        credential_id: str,
        data: dict,
    ) -> dict:
        """Update AI credentials."""
        credential = await self._get_credential_or_404(credential_id, user_id)

        if data.get("api_key"):
            credential.api_key_enc = encrypt(data["api_key"])
        if data.get("model_override") is not None:
            credential.model_override = data["model_override"]
        if data.get("is_active") is not None:
            credential.is_active = data["is_active"]
        credential.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(credential)

        return {
            "id": str(credential.id),
            "provider": credential.provider,
            "api_key_masked": mask_token(decrypt(credential.api_key_enc)) if credential.api_key_enc else None,
            "base_url": credential.base_url,
            "model_override": credential.model_override,
            "is_active": credential.is_active,
            "created_at": credential.created_at.isoformat(),
            "updated_at": credential.updated_at.isoformat(),
        }

    async def delete_credentials(self, user_id: str, credential_id: str) -> None:
        """Delete AI credentials."""
        credential = await self._get_credential_or_404(credential_id, user_id)
        await self.db.delete(credential)
        await self.db.commit()

    async def test_provider_connection(self, data: dict) -> dict:
        """Test an AI provider connection."""
        provider = data["provider"]
        api_key = data.get("api_key")
        base_url = data.get("base_url")
        return await self._test_provider(provider, api_key, base_url)

    # ─── Analysis ────────────────────────────────────────────────────────

    async def start_analysis(
        self,
        user_id: str,
        upload_id: str,
        analysis_type: str,
        language: str,
    ) -> dict:
        """Start an AI analysis job. Returns job_id and status."""
        # Check rate limit for free users
        await self._check_rate_limit(user_id)

        # Check cache first
        cache_key = f"ai:{upload_id}:{analysis_type}:{language}"
        try:
            cached = await self.redis.get(cache_key)
            if cached:
                job_id = str(uuid.uuid4())
                # Store cached result as completed job
                job_data = {
                    "status": "completed",
                    "result": json.loads(cached),
                    "fallback_used": False,
                }
                await self.redis.setex(
                    f"ai:job:{job_id}", CACHE_TTL, json.dumps(job_data)
                )
                return {"job_id": job_id, "status": "completed"}
        except Exception:
            logger.warning("Redis cache read failed for analysis")

        job_id = str(uuid.uuid4())

        # Store job in Redis
        job_data = {
            "status": "processing",
            "upload_id": upload_id,
            "user_id": user_id,
            "analysis_type": analysis_type,
            "language": language,
        }
        try:
            await self.redis.setex(
                f"ai:job:{job_id}", CACHE_TTL, json.dumps(job_data)
            )
        except Exception:
            logger.error("Failed to create AI job in Redis")

        # Dispatch Celery task with fallback
        try:
            from app.worker import celery_app
            from app.modules.ai_engine.tasks import run_ai_analysis

            celery_app.send_task(
                "app.modules.ai_engine.tasks.run_ai_analysis",
                args=[job_id, upload_id, user_id, analysis_type, language],
            )
        except ImportError:
            # Celery not available — run inline via InsightGenerator
            logger.warning("Celery not available, running analysis inline")
            import asyncio

            asyncio.create_task(
                self._run_analysis_inline(
                    job_id, upload_id, user_id, analysis_type, language
                )
            )

        return {"job_id": job_id, "status": "processing"}

    async def get_job_status(self, job_id: str) -> dict:
        """Get AI analysis job status."""
        try:
            data = await self.redis.get(f"ai:job:{job_id}")
            if data:
                return json.loads(data)
        except Exception:
            logger.warning("Redis read failed for job status")

        return {"status": "not_found"}

    async def get_cached_insights(self, upload_id: str) -> dict:
        """Get cached AI insights for an upload."""
        # Check multiple analysis types
        for analysis_type in ["full_diagnosis", "monthly_review", "quick_summary"]:
            cache_key = f"ai:{upload_id}:{analysis_type}:es"
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    return {"insights": json.loads(cached), "cached": True}
            except Exception:
                continue

        return {"insights": [], "cached": False}

    # ─── Providers list ──────────────────────────────────────────────────

    def get_available_providers(self) -> list[dict]:
        """Return list of available AI providers."""
        return AVAILABLE_PROVIDERS

    # ─── Internal helpers ────────────────────────────────────────────────

    async def _get_credentials_by_provider(
        self, user_id: str, provider: str
    ) -> AiCredentials | None:
        """Get active credentials for a specific provider."""
        result = await self.db.execute(
            select(AiCredentials).where(
                AiCredentials.user_id == uuid.UUID(user_id),
                AiCredentials.provider == provider,
                AiCredentials.is_active == True,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def _get_credential_or_404(
        self, credential_id: str, user_id: str
    ) -> AiCredentials:
        """Get credential by ID, raising 404 if not found or wrong user."""
        result = await self.db.execute(
            select(AiCredentials).where(
                AiCredentials.id == uuid.UUID(credential_id),
                AiCredentials.user_id == uuid.UUID(user_id),
            )
        )
        credential = result.scalar_one_or_none()
        if not credential:
            raise NotFoundException("AI credentials not found")
        return credential

    async def _get_provider_instance(
        self, provider: str, api_key_enc: str | None, base_url: str | None, model: str | None
    ) -> AIProvider:
        """Instantiate the appropriate AI provider."""
        api_key = decrypt(api_key_enc) if api_key_enc else None
        model_name = model or DEFAULT_MODELS[provider]

        if provider == "claude":
            from app.modules.ai_engine.providers.claude import ClaudeProvider
            return ClaudeProvider(api_key=api_key, model=model_name)
        elif provider == "openai":
            from app.modules.ai_engine.providers.openai import OpenAIProvider
            return OpenAIProvider(api_key=api_key, model=model_name)
        elif provider == "gemini":
            from app.modules.ai_engine.providers.gemini import GeminiProvider
            return GeminiProvider(api_key=api_key, model=model_name)
        elif provider == "ollama":
            from app.modules.ai_engine.providers.ollama import OllamaProvider
            return OllamaProvider(base_url=base_url or "http://localhost:11434", model=model_name)
        else:
            raise BadRequestException(f"Unknown provider: {provider}")

    async def _test_provider(
        self, provider: str, api_key: str | None, base_url: str | None
    ) -> dict:
        """Test a provider connection and return result."""
        import time

        start = time.monotonic()
        try:
            if provider == "claude":
                from app.modules.ai_engine.providers.claude import ClaudeProvider
                p = ClaudeProvider(api_key=api_key)
            elif provider == "openai":
                from app.modules.ai_engine.providers.openai import OpenAIProvider
                p = OpenAIProvider(api_key=api_key)
            elif provider == "gemini":
                from app.modules.ai_engine.providers.gemini import GeminiProvider
                p = GeminiProvider(api_key=api_key)
            elif provider == "ollama":
                from app.modules.ai_engine.providers.ollama import OllamaProvider
                p = OllamaProvider(base_url=base_url or "http://localhost:11434")
            else:
                return {"connected": False, "latency_ms": 0, "model": "", "error": f"Unknown provider: {provider}"}

            connected = await p.health_check()
            latency = int((time.monotonic() - start) * 1000)
            model = DEFAULT_MODELS.get(provider, "")
            return {
                "connected": connected,
                "latency_ms": latency,
                "model": model,
                "error": None if connected else "Health check failed",
            }
        except Exception as e:
            latency = int((time.monotonic() - start) * 1000)
            logger.error("Provider test failed for %s: %s", provider, e)
            return {
                "connected": False,
                "latency_ms": latency,
                "model": DEFAULT_MODELS.get(provider, ""),
                "error": str(e),
            }

    async def _check_rate_limit(self, user_id: str) -> None:
        """Check daily AI call rate limit for free users. Raises 403 if exceeded.

        Rate limit resets at midnight UTC-5 (Colombia time).
        Key format: ai_rate:{user_id}:{YYYY-MM-DD}
        """
        from datetime import timezone, timedelta

        # Get user plan
        result = await self.db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundException("User not found")

        if user.plan != "free":
            return  # Pro users have no limit

        # Calculate today's date in UTC-5 and TTL until midnight
        utc_minus5 = timezone(timedelta(hours=-5))
        now = datetime.now(utc_minus5)
        today_str = now.strftime("%Y-%m-%d")

        # TTL = seconds until next midnight UTC-5
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        ttl_seconds = int((tomorrow - now).total_seconds())

        key = f"{RATE_LIMIT_KEY_PREFIX}{user_id}:{today_str}"
        try:
            count = await self.redis.get(key)
            if count and int(count) >= settings.FREE_PLAN_MAX_AI_CALLS_PER_DAY:
                raise ForbiddenException(
                    f"Daily AI limit reached ({settings.FREE_PLAN_MAX_AI_CALLS_PER_DAY}/day). Upgrade to Pro for unlimited."
                )
            pipe = self.redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, ttl_seconds)
            await pipe.execute()
        except ForbiddenException:
            raise
        except Exception:
            logger.warning("Redis rate limit check failed, allowing request")

    async def _run_analysis_inline(
        self,
        job_id: str,
        upload_id: str,
        user_id: str,
        analysis_type: str,
        language: str,
    ) -> None:
        """Fallback inline analysis using InsightGenerator when Celery is unavailable."""
        from app.modules.reports.insights import InsightGenerator

        try:
            # Get basic metrics from analytics
            from app.modules.analytics.service import AnalyticsService

            analytics = AnalyticsService(self.db, self.redis)
            metrics = await analytics.get_full_metrics(upload_id, user_id)
            global_metrics = metrics.get("global", {})

            # Generate deterministic insights as fallback
            insights = InsightGenerator.monthly_insights(global_metrics, language)

            result = {
                "analysis_type": analysis_type,
                "language": language,
                "insights": insights,
                "source": "deterministic_fallback",
            }

            # Cache result
            cache_key = f"ai:{upload_id}:{analysis_type}:{language}"
            try:
                await self.redis.setex(cache_key, CACHE_TTL, json.dumps(result))
            except Exception:
                logger.warning("Failed to cache analysis result")

            # Update job status
            job_data = {
                "status": "completed",
                "result": result,
                "fallback_used": True,
            }
            await self.redis.setex(
                f"ai:job:{job_id}", CACHE_TTL, json.dumps(job_data)
            )
            logger.info("Inline analysis completed for job %s", job_id)

        except Exception as e:
            logger.error("Inline analysis failed: %s", e)
            job_data = {
                "status": "failed",
                "error": str(e),
                "fallback_used": True,
            }
            try:
                await self.redis.setex(
                    f"ai:job:{job_id}", CACHE_TTL, json.dumps(job_data)
                )
            except Exception:
                pass
