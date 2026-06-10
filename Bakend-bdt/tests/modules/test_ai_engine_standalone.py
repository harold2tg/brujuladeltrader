"""Standalone tests for AI Engine module (no DB/Redis required)."""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.ai_engine.providers.base import AIProvider
from app.modules.ai_engine.providers.claude import ClaudeProvider
from app.modules.ai_engine.providers.openai import OpenAIProvider
from app.modules.ai_engine.providers.ollama import OllamaProvider
from app.modules.ai_engine.service import AiService, AVAILABLE_PROVIDERS, DEFAULT_MODELS
from app.modules.ai_engine.prompts import SYSTEM_PROMPT, ANALYSIS_CONTEXT
from app.shared.crypto import encrypt, decrypt


# ─── Provider ABC tests ────────────────────────────────────────────────


class TestAIProviderABC:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            AIProvider()

    def test_concrete_provider_has_required_methods(self):
        class DummyProvider(AIProvider):
            async def generate(self, system_prompt, user_prompt, max_tokens=1500, temperature=0.7):
                return "ok"
            async def health_check(self):
                return True
        p = DummyProvider()
        assert hasattr(p, "generate")
        assert hasattr(p, "health_check")


# ─── Claude Provider tests ─────────────────────────────────────────────


class TestClaudeProvider:
    @pytest.mark.asyncio
    async def test_generate_success(self):
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
            mock_client.messages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_success(self):
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
        with patch("app.modules.ai_engine.providers.claude.anthropic") as mock_anthropic:
            mock_anthropic.AsyncAnthropic.side_effect = Exception("Connection refused")
            provider = ClaudeProvider(api_key="test-key")
            result = await provider.health_check()
            assert result is False


# ─── OpenAI Provider tests ─────────────────────────────────────────────


class TestOpenAIProvider:
    @pytest.mark.asyncio
    async def test_generate_success(self):
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


# ─── Ollama Provider tests ─────────────────────────────────────────────


class TestOllamaProvider:
    @pytest.mark.asyncio
    async def test_generate_success(self):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"message": {"content": "Local result"}}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.modules.ai_engine.providers.ollama.httpx") as mock_httpx:
            mock_httpx.AsyncClient.return_value = mock_client
            provider = OllamaProvider(base_url="http://localhost:11434")
            result = await provider.generate("system", "user")
            assert result == "Local result"


# ─── Service unit tests (mocked DB/Redis) ──────────────────────────────


class TestAiServiceUnit:
    def test_get_available_providers(self):
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
    async def test_list_credentials_empty(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_redis = AsyncMock()
        service = AiService(mock_db, mock_redis)
        result = await service.list_credentials(str(uuid.uuid4()))
        assert result == []

    @pytest.mark.asyncio
    async def test_get_job_status_not_found(self):
        mock_db = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        service = AiService(mock_db, mock_redis)
        result = await service.get_job_status("nonexistent")
        assert result["status"] == "not_found"

    @pytest.mark.asyncio
    async def test_get_job_status_returns_data(self):
        mock_db = AsyncMock()
        mock_redis = AsyncMock()
        job_data = {"status": "completed", "result": {"text": "done"}, "fallback_used": False}
        mock_redis.get = AsyncMock(return_value=json.dumps(job_data))
        service = AiService(mock_db, mock_redis)
        result = await service.get_job_status("job-123")
        assert result["status"] == "completed"
        assert result["result"]["text"] == "done"
        assert result["fallback_used"] is False

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self):
        mock_db = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value="10")

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
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        mock_user = MagicMock()
        mock_user.plan = "pro"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = AiService(mock_db, mock_redis)
        await service._check_rate_limit(str(uuid.uuid4()))
        mock_redis.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_store_credentials_missing_api_key(self):
        mock_db = AsyncMock()
        mock_redis = AsyncMock()
        service = AiService(mock_db, mock_redis)
        with pytest.raises(Exception) as exc_info:
            await service.store_credentials(str(uuid.uuid4()), {"provider": "claude", "api_key": None})
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_store_credentials_missing_base_url(self):
        mock_db = AsyncMock()
        mock_redis = AsyncMock()
        service = AiService(mock_db, mock_redis)
        with pytest.raises(Exception) as exc_info:
            await service.store_credentials(str(uuid.uuid4()), {"provider": "ollama", "base_url": None})
        assert exc_info.value.status_code == 400


# ─── Prompts tests ─────────────────────────────────────────────────────


class TestPrompts:
    def test_system_prompt_es_and_en(self):
        assert "es" in SYSTEM_PROMPT
        assert "en" in SYSTEM_PROMPT
        assert "XAUUSD" in SYSTEM_PROMPT["es"]
        assert "XAUUSD" in SYSTEM_PROMPT["en"]

    def test_analysis_context_all_types(self):
        for analysis_type in ["full_diagnosis", "monthly_review", "improvement_plan", "quick_summary", "session_analysis"]:
            assert analysis_type in ANALYSIS_CONTEXT
            assert "es" in ANALYSIS_CONTEXT[analysis_type]
            assert "en" in ANALYSIS_CONTEXT[analysis_type]


# ─── Crypto integration ────────────────────────────────────────────────


class TestCryptoIntegration:
    def test_encrypt_decrypt_ai_key(self):
        api_key = "sk-ant-api03-test-key-12345"
        encrypted = encrypt(api_key)
        decrypted = decrypt(encrypted)
        assert decrypted == api_key
        assert encrypted != api_key  # Not stored in plaintext


# ─── Default models tests ──────────────────────────────────────────────


class TestDefaultModels:
    def test_claude_default_model(self):
        assert DEFAULT_MODELS["claude"] == "claude-sonnet-4-20250514"

    def test_all_providers_have_defaults(self):
        for provider in ["claude", "openai", "gemini", "ollama"]:
            assert provider in DEFAULT_MODELS
            assert isinstance(DEFAULT_MODELS[provider], str)
            assert len(DEFAULT_MODELS[provider]) > 0
