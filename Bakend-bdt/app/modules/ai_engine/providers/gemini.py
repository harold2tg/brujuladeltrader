"""Google Gemini provider implementation."""

import asyncio
import logging

import google.generativeai as genai

from app.modules.ai_engine.providers.base import AIProvider

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]


class GeminiProvider(AIProvider):
    """Google Gemini provider."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1500,
        temperature: float = 0.7,
    ) -> str:
        """Generate response using Google Generative AI API with retry."""
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(
            model_name=self.model,
            system_instruction=system_prompt,
        )

        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                response = await model.generate_content_async(
                    user_prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=max_tokens,
                        temperature=temperature,
                    ),
                )
                return response.text
            except Exception as e:
                last_error = e
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    logger.warning(
                        "Gemini rate limit hit (attempt %d/%d)", attempt + 1, MAX_RETRIES
                    )
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAYS[attempt])
                else:
                    logger.error("Gemini API error: %s", e)
                    raise

        raise RuntimeError(f"Gemini API failed after {MAX_RETRIES} retries: {last_error}")

    async def health_check(self) -> bool:
        """Check if Gemini API is reachable."""
        try:
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(model_name=self.model)
            response = await model.generate_content_async("ping")
            return bool(response.text)
        except Exception as e:
            logger.warning("Gemini health check failed: %s", e)
            return False
