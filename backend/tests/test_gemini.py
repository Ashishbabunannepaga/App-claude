"""Gemini provider and embedder against canned HTTP responses (no network, no key)."""

import httpx
import pytest

from app.ai import embeddings
from app.ai.providers import base
from app.ai.providers.base import AIProviderError
from app.ai.providers.gemini import GeminiProvider
from app.processing.extraction import validate_extraction


class _Calls:
    def __init__(self, responses):
        self.responses, self.requests = list(responses), []

    def __call__(self, url, headers, json, timeout):
        self.requests.append({"url": url, "headers": headers, "json": json})
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        status, body = item
        return httpx.Response(status, json=body, request=httpx.Request("POST", url))


@pytest.fixture
def fake_post(monkeypatch):
    def install(*responses):
        calls = _Calls(responses)
        monkeypatch.setattr(base.httpx, "post", calls)
        monkeypatch.setattr(base.time, "sleep", lambda s: None)
        return calls

    return install


def _answer(text, finish="STOP"):
    return 200, {"candidates": [{"content": {"parts": [{"text": text}]}, "finishReason": finish}]}


def test_extract_sends_json_mode_low_temperature_and_no_thinking(fake_post):
    calls = fake_post(_answer('{"policy_type": "health", "fields": {}}'))
    out = GeminiProvider("k", "gemini-2.5-flash", 5).complete_json("extract", "sys", "prompt", context={})
    assert out["policy_type"] == "health"
    req = calls.requests[0]
    assert req["headers"] == {"x-goog-api-key": "k"}  # key in a header, never in the URL
    assert "k" not in req["url"]
    cfg = req["json"]["generationConfig"]
    assert cfg["responseMimeType"] == "application/json"
    assert cfg["temperature"] == 0.1
    assert cfg["thinkingConfig"] == {"thinkingBudget": 0}


def test_pro_model_keeps_thinking(fake_post):
    calls = fake_post(_answer("{}"))
    GeminiProvider("k", "gemini-2.5-pro", 5).complete_json("qa", "s", "p", context={})
    assert "thinkingConfig" not in calls.requests[0]["json"]["generationConfig"]


def test_retries_rate_limit_then_succeeds(fake_post):
    calls = fake_post((429, {"error": {}}), (503, {"error": {}}), _answer('{"ok": true}'))
    assert GeminiProvider("k", "gemini-2.5-flash", 5).complete_json("qa", "s", "p", context={}) == {"ok": True}
    assert len(calls.requests) == 3


def test_does_not_retry_bad_key(fake_post):
    calls = fake_post((400, {"error": {"message": "API key not valid"}}))
    with pytest.raises(AIProviderError, match="HTTP 400"):
        GeminiProvider("bad", "gemini-2.5-flash", 5).complete_json("qa", "s", "p", context={})
    assert len(calls.requests) == 1


def test_network_failure_after_retries_is_provider_error(fake_post):
    fake_post(httpx.ConnectError("x"), httpx.ConnectError("x"), httpx.ConnectError("x"))
    with pytest.raises(AIProviderError):
        GeminiProvider("k", "gemini-2.5-flash", 5).complete_json("qa", "s", "p", context={})


@pytest.mark.parametrize(
    "response",
    [
        (200, {"promptFeedback": {"blockReason": "SAFETY"}}),
        _answer('{"a": 1}', finish="SAFETY"),
        _answer('{"a": ', finish="MAX_TOKENS"),
    ],
)
def test_blocked_or_cut_off_answers_raise(fake_post, response):
    fake_post(response)
    with pytest.raises(AIProviderError):
        GeminiProvider("k", "gemini-2.5-flash", 5).complete_json("extract", "s", "p", context={})


def test_embedder_batches_normalises_and_uses_query_mode(fake_post):
    calls = fake_post(
        (200, {"embeddings": [{"values": [3.0, 4.0]}] * 100}),
        (200, {"embeddings": [{"values": [0.0, 2.0]}]}),
        (200, {"embeddings": [{"values": [1.0, 0.0]}]}),
    )
    e = embeddings.GeminiEmbedder("k", "gemini-embedding-001", 2, 5)
    vectors = e.embed(["chunk"] * 101)
    assert len(vectors) == 101 and len(calls.requests) == 2
    assert vectors[0] == pytest.approx([0.6, 0.8]) and vectors[100] == pytest.approx([0.0, 1.0])
    first = calls.requests[0]["json"]["requests"][0]
    assert first["taskType"] == "RETRIEVAL_DOCUMENT" and first["outputDimensionality"] == 2
    assert e.embed_query("q") == pytest.approx([1.0, 0.0])
    assert calls.requests[2]["json"]["requests"][0]["taskType"] == "RETRIEVAL_QUERY"


def test_implausible_amounts_are_flagged_for_review():
    text = "Sum Insured: 1\nPremium: 10,84,746\nPolicy No ABC123"
    raw = {
        "policy_type": "health",
        "fields": {
            "sum_insured": {"value": "1", "confidence": 0.9},
            "premium": {"value": "1084746", "confidence": 0.9},
        },
    }
    result = validate_extraction(raw, text)
    assert result.confidence["sum_insured"] <= 0.2  # the "₹1 cover" seen on the phone test


def test_premium_above_cover_is_flagged_for_health():
    text = "Sum Insured 5,00,000 Premium 9,00,000"
    raw = {
        "policy_type": "health",
        "fields": {
            "sum_insured": {"value": "500000", "confidence": 0.9},
            "premium": {"value": "900000", "confidence": 0.9},
        },
    }
    result = validate_extraction(raw, text)
    assert result.confidence["premium"] <= 0.2
    assert result.confidence["sum_insured"] == 0.9


def test_insurer_heuristic_matches_whole_words_only():
    from app.processing.heuristics import find_insurer

    assert find_insurer("Group Health Insurance Policy issued under public scheme") is None
    assert find_insurer("Issued by LIC of India") == "LIC"


def test_period_of_insurance_gives_both_dates():
    from datetime import date

    from app.processing.heuristics import find_dates

    assert find_dates("Period of Insurance: 01/04/2026 to 31/03/2027") == (date(2026, 4, 1), date(2027, 3, 31))
