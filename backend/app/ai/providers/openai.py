import base64
from typing import Any

import httpx

from app.ai.providers.base import TRANSCRIBE_PROMPT, AIProvider, AIProviderError, parse_json_object, post_with_retry


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
        return parse_json_object(_message_text(resp.json()))

    def transcribe(self, image: bytes, mime_type: str = "image/jpeg") -> str:
        """OCR with a vision model: the page's text, verbatim. Used for photos and scanned PDFs."""
        data_url = f"data:{mime_type};base64,{base64.b64encode(image).decode()}"
        resp = post_with_retry(
            self.url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "temperature": 0,
                "max_tokens": 8192,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": TRANSCRIBE_PROMPT},
                            {"type": "image_url", "image_url": {"url": data_url, "detail": "high"}},
                        ],
                    }
                ],
            },
            timeout=self.timeout,
            label="openai ocr",
        )
        return _message_text(resp.json()).strip()


def _message_text(body: Any) -> str:
    """The first choice's text. A body without one (a refusal, a changed API) is a provider error, not a crash."""
    try:
        content = body["choices"][0]["message"].get("content")
    except (KeyError, IndexError, TypeError, AttributeError) as exc:
        raise AIProviderError("openai returned no message") from exc
    if content is None:
        raise AIProviderError("openai returned an empty message")
    return content
