"""Ollama (local) provider implementation."""

import asyncio
import logging

import httpx

from app.modules.ai_engine.providers.base import AIProvider

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]


class OllamaProvider(AIProvider):
    """Ollama local LLM provider via HTTP API."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1500,
        temperature: float = 0.7,
    ) -> str:
        """Generate response using Ollama HTTP API with retry."""
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(
                        f"{self.base_url}/api/chat",
                        json={
                            "model": self.model,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt},
                            ],
                            "stream": False,
                            "options": {
                                "num_predict": max_tokens,
                                "temperature": temperature,
                            },
                        },
                    )
                    response.raise_for_status()
                    data = response.json()
                    return data["message"]["content"]
            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(
                    "Ollama timeout (attempt %d/%d)", attempt + 1, MAX_RETRIES
                )
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAYS[attempt])
            except httpx.HTTPStatusError as e:
                last_error = e
                logger.error("Ollama HTTP error: %s", e)
                raise
            except Exception as e:
                logger.error("Ollama unexpected error: %s", e)
                raise

        raise RuntimeError(f"Ollama failed after {MAX_RETRIES} retries: {last_error}")

    async def health_check(self) -> bool:
        """Check if Ollama server is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.warning("Ollama health check failed: %s", e)
            return False
