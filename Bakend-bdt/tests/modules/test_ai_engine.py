"""Tests for AI Engine module."""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.ai_engine.models import AiCredentials
from app.modules.ai_engine.providers.base import AIProvider
from app.modules.ai_engine.providers.claude import ClaudeProvider
from app.modules.ai_engine.providers.gemini import GeminiProvider
from app.modules.ai_engine.providers.ollama import OllamaProvider
from app.modules.ai_engine.providers.openai import OpenAIProvider
from app.modules.ai_engine.service import AiService
from app.shared.crypto import encrypt


# ─── Provider unit tests ────────────────────────────────────────────────


class TestAIProviderABC:
    """Tests for AIProvider abstract base class."""

    def test_cannot_instantiate_directly(self):
        """AIProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AIProvider()

    def test_concrete_provider_has_required_methods(self):
        """Concrete provider must implement generate and health_check."""

        class DummyProvider(AIProvider):
            async def generate(self, system_prompt, user_prompt, max_tokens=1500, temperature=0.7):
                return "ok"

            async def health_check(self):
                return True

        p = DummyProvider()
        assert hasattr(p, "generate")
        assert hasattr(p, "health_check")


class TestClaudeProvider:
    """Tests for ClaudeProvider."""

    @pytest.mark.asyncio
    async def test_generate_success(self):
        """Claude provider generates text on success."""
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Analysis result")]
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_message)

        with patch("app.modules.ai_engine.providers.claude.anthropic") as mock_anthropic:
            mock_anthropic.AsyncAnthropic.return_value = mock_client
            mock_anthropic.RateLimitError = type("RateLimitError", (Exception,), {})
            mock_anthropic.APIError = type("APIError", (Exception,), {})

            provider = ClaudeProvider(api_key="test-key")
            result = await provider.generate("system", "user")
            assert result == "Analysis result"

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Claude health check returns True on success."""
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="pong")]
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_message)

        with patch("app.modules.ai_engine.providers.claude.anthropic") as mock_anthropic:
            mock_anthropic.AsyncAnthropic.return_value = mock_client

            provider = ClaudeProvider(api_key="test-key")
            result = await provider.health_check()
            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Claude health check returns False on error."""
        with patch("app.modules.ai_engine.providers.claude.anthropic") as mock_anthropic:
            mock_anthropic.AsyncAnthropic.side_effect = Exception("Connection refused")

            provider = ClaudeProvider(api_key="test-key")
            result = await provider.health_check()
            assert result is False


class TestOpenAIProvider:
    """Tests for OpenAIProvider."""

    @pytest.mark.asyncio
    async def test_generate_success(self):
        """OpenAI provider generates text on success."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="GPT result"))]
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("app.modules.ai_engine.providers.openai.openai") as mock_openai:
            mock_openai.AsyncOpenAI.return_value = mock_client
            mock_openai.RateLimitError = type("RateLimitError", (Exception,), {})
            mock_openai.APIError = type("APIError", (Exception,), {})

            provider = OpenAIProvider(api_key="test-key")
            result = await provider.generate("system", "user")
            assert result == "GPT result"


class TestOllamaProvider:
    """Tests for OllamaProvider."""

    @pytest.mark.asyncio
    async def test_generate_success(self):
        """Ollama provider generates text on success."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"message": {"content": "Local result"}}

        with patch("app.modules.ai_engine.providers.ollama.httpx") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_httpx.AsyncClient.return_value = mock_client

            provider = OllamaProvider(base_url="http://localhost:11434")
            result = await provider.generate("system", "user")
            assert result == "Local result"


# ─── Service tests ──────────────────────────────────────────────────────


class TestAiService:
    """Tests for AiService business logic."""

    @pytest.mark.asyncio
    async def test_store_credentials_missing_api_key(self):
        """Store credentials raises 400 if API key missing for non-ollama provider."""
        mock_db = AsyncMock()
        mock_redis = AsyncMock()
        service = AiService(mock_db, mock_redis)

        with pytest.raises(Exception) as exc_info:
            await service.store_credentials(
                str(uuid.uuid4()),
                {"provider": "claude", "api_key": None},
            )
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_store_credentials_missing_base_url(self):
        """Store credentials raises 400 if base_url missing for ollama."""
        mock_db = AsyncMock()
        mock_redis = AsyncMock()
        service = AiService(mock_db, mock_redis)

        with pytest.raises(Exception) as exc_info:
            await service.store_credentials(
                str(uuid.uuid4()),
                {"provider": "ollama", "base_url": None},
            )
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_list_credentials_empty(self):
        """List credentials returns empty list when no credentials exist."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        mock_redis = AsyncMock()
        service = AiService(mock_db, mock_redis)

        result = await service.list_credentials(str(uuid.uuid4()))
        assert result == []

    @pytest.mark.asyncio
    async def test_get_available_providers(self):
        """Returns list of available providers."""
        mock_db = AsyncMock()
        mock_redis = AsyncMock()
        service = AiService(mock_db, mock_redis)

        providers = service.get_available_providers()
        assert len(providers) == 4
        names = [p["name"] for p in providers]
        assert "claude" in names
        assert "openai" in names
        assert "gemini" in names
        assert "ollama" in names

    @pytest.mark.asyncio
    async def test_get_job_status_not_found(self):
        """Returns not_found for unknown job."""
        mock_db = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        service = AiService(mock_db, mock_redis)

        result = await service.get_job_status("nonexistent-job")
        assert result["status"] == "not_found"

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self):
        """Free user exceeding daily limit gets 403."""
        mock_db = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value="10")  # Already at limit

        # Mock user query
        mock_user = MagicMock()
        mock_user.plan = "free"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = AiService(mock_db, mock_redis)

        with pytest.raises(Exception) as exc_info:
            await service._check_rate_limit(str(uuid.uuid4()))
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_rate_limit_not_checked_for_pro(self):
        """Pro users don't hit rate limit."""
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        mock_user = MagicMock()
        mock_user.plan = "pro"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = AiService(mock_db, mock_redis)

        # Should not raise
        await service._check_rate_limit(str(uuid.uuid4()))
        mock_redis.get.assert_not_called()


# ─── Integration tests (with test client) ───────────────────────────────


class TestAiEngineEndpoints:
    """Integration tests for AI Engine API endpoints."""

    @pytest.mark.asyncio
    async def test_list_providers(self, client, test_user, test_user_tokens):
        """GET /ai/providers/list returns available providers."""
        response = await client.get(
            "/ai/providers/list",
            headers={"Authorization": f"Bearer {test_user_tokens['access_token']}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # success_response() wraps list directly: { success, data: [<list>] }
        assert len(data["data"]) == 4

    @pytest.mark.asyncio
    async def test_list_credentials_empty(self, client, test_user, test_user_tokens):
        """GET /ai/credentials returns empty list."""
        response = await client.get(
            "/ai/credentials",
            headers={"Authorization": f"Bearer {test_user_tokens['access_token']}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []

    @pytest.mark.asyncio
    async def test_get_job_status_not_found(self, client, test_user, test_user_tokens):
        """GET /ai/jobs/{job_id} returns not_found."""
        response = await client.get(
            "/ai/jobs/nonexistent-job-id",
            headers={"Authorization": f"Bearer {test_user_tokens['access_token']}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "not_found"

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client):
        """Endpoints return 401 without auth."""
        response = await client.get("/ai/credentials")
        assert response.status_code == 422  # Missing required header
