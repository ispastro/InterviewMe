import json
import logging
from typing import Dict, Any, Optional
from groq import AsyncGroq
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from app.config import settings
from app.core.exceptions import AIServiceError

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL
        self.default_max_tokens = settings.GROQ_MAX_TOKENS
        self.default_temperature = settings.GROQ_TEMPERATURE

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
    async def chat_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: float = 0.9
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.default_temperature,
                max_tokens=max_tokens or self.default_max_tokens,
                top_p=top_p
            )

            if not response.choices or not response.choices[0].message:
                raise AIServiceError("Empty response from AI service")

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"LLM chat completion failed: {str(e)}")
            raise AIServiceError(f"LLM request failed: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
    async def chat_completion_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        content = await self.chat_completion(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )

        try:
            return self._parse_json_response(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {content[:200]}")
            raise AIServiceError(f"Invalid JSON response from AI: {str(e)}")

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        try:
            return json.loads(content.strip())
        except json.JSONDecodeError:
            if "```" in content:
                start = content.find("```json") + 7 if "```json" in content else content.find("```") + 3
                end = content.find("```", start)
                if end > start:
                    return json.loads(content[start:end].strip())
            raise


llm_client = LLMClient()
