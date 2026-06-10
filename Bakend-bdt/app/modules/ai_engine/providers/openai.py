"""OpenAI provider implementation."""

import asyncio
import logging

import openai

from app.modules.ai_engine.providers.base import AIProvider

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]


class OpenAIProvider(AIProvider):
    """OpenAI GPT provider."""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1500,
        temperature: float = 0.7,
    ) -> str:
        """Generate response using OpenAI API with retry."""
        client = openai.AsyncOpenAI(api_key=self.api_key)

        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                response = await client.chat.completions.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                return response.choices[0].message.content
            except openai.RateLimitError as e:
                last_error = e
                logger.warning(
                    "OpenAI rate limit hit (attempt %d/%d)", attempt + 1, MAX_RETRIES
                )
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAYS[attempt])
            except openai.APIError as e:
                last_error = e
                logger.error("OpenAI API error: %s", e)
                raise
            except Exception as e:
                logger.error("OpenAI unexpected error: %s", e)
                raise

        raise RuntimeError(f"OpenAI API failed after {MAX_RETRIES} retries: {last_error}")

    async def health_check(self) -> bool:
        """Check if OpenAI API is reachable."""
        try:
            client = openai.AsyncOpenAI(api_key=self.api_key)
            await client.chat.completions.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "ping"}],
            )
            return True
        except Exception as e:
            logger.warning("OpenAI health check failed: %s", e)
            return False
