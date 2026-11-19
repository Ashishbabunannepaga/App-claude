import base64
from typing import Any

from app.ai.guardrails import log_usage
from app.ai.providers.base import TRANSCRIBE_PROMPT, AIProvider, AIProviderError, parse_json_object, post_with_retry

REASONING_PREFIXES = ("gpt-5", "gpt-6", "o1", "o3", "o4")
# Reasoning tokens count toward the output limit; this much is added so thinking never crowds out the answer.
REASONING_HEADROOM = 8000


def is_reasoning_model(model: str) -> bool:
    return model.startswith(REASONING_PREFIXES)


class OpenAIProvider(AIProvider):
    name = "openai"
    url = "https://api.openai.com/v1/chat/completions"

    def __init__(self, api_key: str, model: str, timeout: float, reasoning_effort: str | None = None):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.reasoning = is_reasoning_model(model)
        self.reasoning_effort = (reasoning_effort or "low") if self.reasoning else None

    def _limits(self, max_tokens: int, temperature: float | None = None) -> dict[str, Any]:
        """Output limit and sampling settings in the form the model accepts.

        Reasoning models refuse `max_tokens` and a custom `temperature`; they take `max_completion_tokens`
        (thinking included) and `reasoning_effort`. Older chat models take the classic pair."""
        if self.reasoning:
            return {"max_completion_tokens": max_tokens + REASONING_HEADROOM, "reasoning_effort": self.reasoning_effort}
        limits: dict[str, Any] = {"max_tokens": max_tokens}
        if temperature is not None:
            limits["temperature"] = temperature
        return limits

    def complete_json(
        self, task: str, system: str, prompt: str, *, context: dict[str, Any], max_tokens: int = 2000
    ) -> dict[str, Any]:
        resp = post_with_retry(
            self.url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                **self._limits(max_tokens),
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=self.timeout,
            label="openai",
        )
        body = resp.json()
        log_usage(self.name, self.model, task, body.get("usage"))
        return parse_json_object(_message_text(body))

    def transcribe(self, image: bytes, mime_type: str = "image/jpeg") -> str:
        """OCR with a vision model: the page's text, verbatim. Used for photos and scanned PDFs."""
        data_url = f"data:{mime_type};base64,{base64.b64encode(image).decode()}"
        resp = post_with_retry(
            self.url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                **self._limits(8192, temperature=0),
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
        body = resp.json()
        log_usage(self.name, self.model, "ocr", body.get("usage"))
        return _message_text(body).strip()


def _message_text(body: Any) -> str:
    """The first choice's text. A body without one (a refusal, a changed API) is a provider error, not a crash."""
    try:
        content = body["choices"][0]["message"].get("content")
    except (KeyError, IndexError, TypeError, AttributeError) as exc:
        raise AIProviderError("openai returned no message") from exc
    if content is None:
        raise AIProviderError("openai returned an empty message")
    return content
