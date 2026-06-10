"""Pydantic schemas for AI Engine endpoints."""

from pydantic import BaseModel, Field


# --- Credentials ---

class CredentialsCreate(BaseModel):
    """Request to store AI credentials."""
    provider: str = Field(..., pattern="^(claude|openai|gemini|ollama)$")
    api_key: str | None = None
    base_url: str | None = None
    model_override: str | None = None


class CredentialsUpdate(BaseModel):
    """Request to update AI credentials."""
    api_key: str | None = None
    model_override: str | None = None
    is_active: bool | None = None


class CredentialsResponse(BaseModel):
    """Response for stored credentials."""
    id: str
    provider: str
    api_key_masked: str | None = None
    base_url: str | None = None
    model_override: str | None = None
    is_active: bool
    created_at: str
    updated_at: str


class CredentialsCreateResponse(BaseModel):
    """Response after creating credentials."""
    connected: bool
    provider: str
    model: str


class TestProviderRequest(BaseModel):
    """Request to test an AI provider connection."""
    provider: str = Field(..., pattern="^(claude|openai|gemini|ollama)$")
    api_key: str | None = None
    base_url: str | None = None


class TestProviderResponse(BaseModel):
    """Response from provider test."""
    connected: bool
    latency_ms: int
    model: str
    error: str | None = None


# --- Analysis ---

class AnalyzeRequest(BaseModel):
    """Request to start AI analysis."""
    analysis_type: str = Field(
        ...,
        pattern="^(full_diagnosis|monthly_review|improvement_plan|quick_summary|session_analysis)$",
    )
    language: str = Field("es", pattern="^(es|en)$")


class AnalyzeResponse(BaseModel):
    """Response after starting analysis."""
    job_id: str
    status: str = "processing"


class JobStatusResponse(BaseModel):
    """Response for job status polling."""
    status: str
    result: dict | None = None
    error: str | None = None
    fallback_used: bool = False


class InsightsResponse(BaseModel):
    """Response for cached insights."""
    insights: list[dict]
    cached: bool


# --- Providers List ---

class ProviderInfo(BaseModel):
    """Available provider info."""
    name: str
    display_name: str
    models: list[str]
    requires_key: bool


class ProvidersListResponse(BaseModel):
    """Response listing available providers."""
    providers: list[ProviderInfo]
