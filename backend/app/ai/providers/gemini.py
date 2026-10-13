import base64
from typing import Any

from app.ai.providers.base import AIProvider, AIProviderError, parse_json_object, post_with_retry

API = "https://generativelanguage.googleapis.com/v1beta/models"

TRANSCRIBE_PROMPT = (
    "Transcribe all text on this insurance document page exactly as printed, in reading order. "
    "Keep numbers, dates, amounts, policy numbers and names exactly as written; do not correct, translate, "
    "summarise or add anything. Put table rows on their own lines with cells separated by ' | '. "
    "If the page has no text, return nothing."
)


class GeminiProvider(AIProvider):
    """Google Gemini through the official Generative Language API, with the user's own key (GEMINI_API_KEY)."""

    name = "gemini"

    def __init__(self, api_key: str, model: str, timeout: float):
        self.api_key, self.model, self.timeout = api_key, model, timeout

    def complete_json(
        self, task: str, system: str, prompt: str, *, context: dict[str, Any], max_tokens: int = 2000
    ) -> dict[str, Any]:
        config: dict[str, Any] = {
            "maxOutputTokens": max_tokens,
            "responseMimeType": "application/json",
            # Extraction should copy what the document says, not paraphrase it.
            "temperature": 0.1 if task == "extract" else 0.3,
        }
        if "flash" in self.model:
            # 2.5 Flash "thinks" by default and thinking tokens count against maxOutputTokens, which cuts the
            # JSON short. These tasks are grounded lookups, so thinking is switched off. Pro cannot turn it off.
            config["thinkingConfig"] = {"thinkingBudget": 0}
        resp = post_with_retry(
            f"{API}/{self.model}:generateContent",
            headers={"x-goog-api-key": self.api_key},
            json={
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": config,
            },
            timeout=self.timeout,
            label="gemini",
        )
        body = resp.json()
        candidates = body.get("candidates") or []
        if not candidates:
            reason = (body.get("promptFeedback") or {}).get("blockReason", "no candidates")
            raise AIProviderError(f"gemini returned no answer: {reason}")
        candidate = candidates[0]
        finish = candidate.get("finishReason", "STOP")
        if finish not in ("STOP", "MAX_TOKENS"):
            raise AIProviderError(f"gemini stopped early: {finish}")
        text = "".join(p.get("text", "") for p in (candidate.get("content") or {}).get("parts", []))
        if finish == "MAX_TOKENS" and not text.rstrip().endswith("}"):
            raise AIProviderError("gemini answer was cut off (MAX_TOKENS)")
        return parse_json_object(text)

    def transcribe(self, image: bytes, mime_type: str = "image/png") -> str:
        """OCR: the page's text, verbatim. Used for photos and scanned PDFs when no local OCR is installed."""
        config: dict[str, Any] = {"temperature": 0, "maxOutputTokens": 8192}
        if "flash" in self.model:
            config["thinkingConfig"] = {"thinkingBudget": 0}
        resp = post_with_retry(
            f"{API}/{self.model}:generateContent",
            headers={"x-goog-api-key": self.api_key},
            json={
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"inline_data": {"mime_type": mime_type, "data": base64.b64encode(image).decode()}},
                            {"text": TRANSCRIBE_PROMPT},
                        ],
                    }
                ],
                "generationConfig": config,
            },
            timeout=self.timeout,
            label="gemini ocr",
        )
        candidates = resp.json().get("candidates") or []
        if not candidates:
            return ""
        candidate = candidates[0]
        if candidate.get("finishReason", "STOP") not in ("STOP", "MAX_TOKENS"):
            raise AIProviderError(f"gemini ocr stopped early: {candidate.get('finishReason')}")
        return "".join(p.get("text", "") for p in (candidate.get("content") or {}).get("parts", [])).strip()
