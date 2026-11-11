"""OpenAI vision OCR and response handling against canned HTTP responses (no network, no key)."""

import io

import pytesseract
import pytest
from PIL import Image

from app.ai.providers.base import AIProviderError
from app.ai.providers.openai import OpenAIProvider
from app.core.config import get_settings
from app.processing.text_extraction import ExtractionError, extract_text
from tests.test_gemini import fake_post  # noqa: F401 - pytest fixture

PAGE = "HDFC ERGO\nPolicy No: 2856 2034 1234 5678 000\nSum Insured: Rs. 10,00,000"


def _chat(text):
    return 200, {"choices": [{"message": {"role": "assistant", "content": text}}]}


def _png(size=(3000, 4000)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, "white").save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def no_tesseract(monkeypatch):
    def missing(*a, **k):
        raise pytesseract.TesseractNotFoundError()

    monkeypatch.setattr(pytesseract, "get_languages", missing)


def test_photo_is_read_by_openai_when_tesseract_is_missing(fake_post, no_tesseract, monkeypatch):  # noqa: F811
    s = get_settings()
    monkeypatch.setattr(s, "ai_provider", "openai")
    monkeypatch.setattr(s, "openai_api_key", "sk-test")
    monkeypatch.setattr(s, "gemini_api_key", None)
    calls = fake_post(_chat(PAGE))

    out = extract_text(_png(), "image/png")

    assert out.method == "ocr" and "1234 5678" in out.full_text
    req = calls.requests[0]
    assert req["url"].endswith("/chat/completions")
    assert req["headers"] == {"Authorization": "Bearer sk-test"}
    assert req["json"]["temperature"] == 0
    image = req["json"]["messages"][0]["content"][1]["image_url"]["url"]
    assert image.startswith("data:image/jpeg;base64,")  # downscaled and re-encoded, not the raw upload


def test_main_ai_provider_picks_the_vision_ocr(fake_post, no_tesseract, monkeypatch):  # noqa: F811
    s = get_settings()
    monkeypatch.setattr(s, "ai_provider", "openai")
    monkeypatch.setattr(s, "openai_api_key", "sk-test")
    monkeypatch.setattr(s, "gemini_api_key", "g-test")
    calls = fake_post(_chat(PAGE))
    extract_text(_png((200, 200)), "image/png")
    assert "openai.com" in calls.requests[0]["url"]


def test_ocr_provider_openai_skips_tesseract(fake_post, monkeypatch):  # noqa: F811
    s = get_settings()
    monkeypatch.setattr(s, "ocr_provider", "openai")
    monkeypatch.setattr(s, "openai_api_key", "sk-test")
    calls = fake_post(_chat(PAGE))
    assert "HDFC" in extract_text(_png((200, 200)), "image/png").full_text
    assert len(calls.requests) == 1


def test_no_tesseract_and_no_keys_fails_clearly(no_tesseract, monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "gemini_api_key", None)
    monkeypatch.setattr(s, "openai_api_key", None)
    with pytest.raises(ExtractionError, match="ocr_unavailable"):
        extract_text(_png((100, 100)), "image/png")


@pytest.mark.parametrize(
    "body",
    [{"error": {"message": "x"}}, {"choices": []}, {"choices": [{"message": {"content": None, "refusal": "no"}}]}],
)
def test_odd_openai_answers_are_provider_errors_not_crashes(fake_post, body):  # noqa: F811
    fake_post((200, body))
    with pytest.raises(AIProviderError):
        OpenAIProvider("sk-test", "gpt-4.1-mini", 5).complete_json("extract", "sys", "p", context={})
