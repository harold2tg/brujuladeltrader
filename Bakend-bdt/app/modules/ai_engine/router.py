"""AI Engine router — 9 endpoints (5 credentials + 3 analysis + 1 providers list)."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_active_user, get_db, get_redis
from app.modules.auth.models import User
from app.modules.ai_engine.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    CredentialsCreate,
    CredentialsCreateResponse,
    CredentialsResponse,
    CredentialsUpdate,
    JobStatusResponse,
    ProvidersListResponse,
    TestProviderRequest,
    TestProviderResponse,
)
from app.modules.ai_engine.service import AiService
from app.shared.responses import success_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai_engine"])


def get_ai_service(
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
) -> AiService:
    """Dependency that provides AiService."""
    return AiService(db, redis_client)


# ─── Credentials endpoints ──────────────────────────────────────────────


@router.post("/credentials", response_model=CredentialsCreateResponse)
async def store_credentials(
    data: CredentialsCreate,
    current_user: User = Depends(get_current_active_user),
    service: AiService = Depends(get_ai_service),
):
    """Store AI provider credentials (encrypted at rest)."""
    result = await service.store_credentials(
        str(current_user.id),
        data.model_dump(),
    )
    return success_response(result)


@router.get("/credentials")
async def list_credentials(
    current_user: User = Depends(get_current_active_user),
    service: AiService = Depends(get_ai_service),
):
    """List AI credentials for the current user (keys masked)."""
    credentials = await service.list_credentials(str(current_user.id))
    return success_response(credentials)


@router.put("/credentials/{credential_id}", response_model=CredentialsResponse)
async def update_credentials(
    credential_id: str,
    data: CredentialsUpdate,
    current_user: User = Depends(get_current_active_user),
    service: AiService = Depends(get_ai_service),
):
    """Update AI credentials."""
    result = await service.update_credentials(
        str(current_user.id),
        credential_id,
        data.model_dump(exclude_unset=True),
    )
    return success_response(result)


@router.delete("/credentials/{credential_id}", status_code=204)
async def delete_credentials(
    credential_id: str,
    current_user: User = Depends(get_current_active_user),
    service: AiService = Depends(get_ai_service),
):
    """Delete AI credentials."""
    await service.delete_credentials(str(current_user.id), credential_id)


@router.post("/credentials/test", response_model=TestProviderResponse)
async def test_credentials(
    data: TestProviderRequest,
    current_user: User = Depends(get_current_active_user),
    service: AiService = Depends(get_ai_service),
):
    """Test an AI provider connection."""
    result = await service.test_provider_connection(data.model_dump())
    return success_response(result)


# ─── Analysis endpoints ─────────────────────────────────────────────────


@router.post("/{upload_id}/analyze", response_model=AnalyzeResponse)
async def start_analysis(
    upload_id: str,
    data: AnalyzeRequest,
    current_user: User = Depends(get_current_active_user),
    service: AiService = Depends(get_ai_service),
):
    """Start an AI analysis job (async via Celery)."""
    result = await service.start_analysis(
        str(current_user.id),
        upload_id,
        data.analysis_type,
        data.language,
    )
    return success_response(result)


@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    service: AiService = Depends(get_ai_service),
):
    """Get AI analysis job status."""
    result = await service.get_job_status(job_id)
    return success_response(result)


@router.get("/{upload_id}/insights")
async def get_insights(
    upload_id: str,
    current_user: User = Depends(get_current_active_user),
    service: AiService = Depends(get_ai_service),
):
    """Get cached AI insights for an upload."""
    result = await service.get_cached_insights(upload_id)
    return success_response(result)


# ─── Providers list ─────────────────────────────────────────────────────


@router.get("/providers/list")
async def list_providers(
    current_user: User = Depends(get_current_active_user),
    service: AiService = Depends(get_ai_service),
):
    """List available AI providers and their models."""
    providers = service.get_available_providers()
    return success_response(providers)
