"""Claude (Anthropic) provider implementation."""

import asyncio
import logging
import time

import anthropic

from app.modules.ai_engine.providers.base import AIProvider

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]  # Exponential backoff seconds


class ClaudeProvider(AIProvider):
    """Anthropic Claude provider."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key
        self.model = model

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1500,
        temperature: float = 0.7,
    ) -> str:
        """Generate response using Anthropic Claude API with retry."""
        client = anthropic.AsyncAnthropic(api_key=self.api_key)

        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                message = await client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                return message.content[0].text
            except anthropic.RateLimitError as e:
                last_error = e
                logger.warning(
                    "Claude rate limit hit (attempt %d/%d)", attempt + 1, MAX_RETRIES
                )
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAYS[attempt])
            except anthropic.APIError as e:
                last_error = e
                logger.error("Claude API error: %s", e)
                raise
            except Exception as e:
                logger.error("Claude unexpected error: %s", e)
                raise

        raise RuntimeError(f"Claude API failed after {MAX_RETRIES} retries: {last_error}")

    async def health_check(self) -> bool:
        """Check if Anthropic API is reachable."""
        try:
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            await client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "ping"}],
            )
            return True
        except Exception as e:
            logger.warning("Claude health check failed: %s", e)
            return False
