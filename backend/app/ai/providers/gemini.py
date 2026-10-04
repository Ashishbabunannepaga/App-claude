from typing import Any

import httpx

from app.ai.providers.base import AIProvider, AIProviderError, parse_json_object


class GeminiProvider(AIProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str, timeout: float):
        self.api_key, self.model, self.timeout = api_key, model, timeout

    def complete_json(
        self, task: str, system: str, prompt: str, *, context: dict[str, Any], max_tokens: int = 2000
    ) -> dict[str, Any]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        try:
            resp = httpx.post(
                url,
                headers={"x-goog-api-key": self.api_key},
                json={
                    "systemInstruction": {"parts": [{"text": system}]},
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "generationConfig": {"maxOutputTokens": max_tokens, "responseMimeType": "application/json"},
                },
                timeout=self.timeout,
            )
            resp.raise_for_status()
            parts = resp.json()["candidates"][0]["content"]["parts"]
        except (httpx.HTTPError, KeyError, IndexError) as exc:
            raise AIProviderError(f"gemini request failed: {type(exc).__name__}") from exc
        return parse_json_object("".join(p.get("text", "") for p in parts))
