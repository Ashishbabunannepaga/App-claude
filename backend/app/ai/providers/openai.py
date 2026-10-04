from typing import Any

import httpx

from app.ai.providers.base import AIProvider, AIProviderError, parse_json_object


class OpenAIProvider(AIProvider):
    name = "openai"
    url = "https://api.openai.com/v1/chat/completions"

    def __init__(self, api_key: str, model: str, timeout: float):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def complete_json(
        self, task: str, system: str, prompt: str, *, context: dict[str, Any], max_tokens: int = 2000
    ) -> dict[str, Any]:
        try:
            resp = httpx.post(
                self.url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                },
                timeout=self.timeout,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise AIProviderError(f"openai request failed: {type(exc).__name__}") from exc
        return parse_json_object(resp.json()["choices"][0]["message"]["content"])
