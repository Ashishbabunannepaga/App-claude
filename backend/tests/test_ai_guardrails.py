"""Guardrails around AI calls: what leaves our servers, how much, and what we trust in an answer."""

import logging

from app.ai import prompts
from app.ai.guardrails import fit_pages, redact, ungrounded_numbers
from tests.test_gemini import fake_post  # noqa: F401 - pytest fixture


def test_government_ids_are_masked_before_any_ai_call():
    text = "Aadhaar: 2345 6789 0123  PAN: ABCDE1234F  A/c No: 123456789012  Policy No. 6203516874 02 00"
    out = redact(text)
    assert "2345 6789" not in out and "XXXX XXXX 0123" in out
    assert "ABCDE1234F" not in out and out.count("XXXXXXXXXF") == 1
    assert "123456789012" not in out and "9012" in out
    assert "6203516874 02 00" in out  # the policy number is what we need; it stays
    assert (
        redact("Sum Insured 5,00,000 Premium 13152 from 04/10/2026")
        == "Sum Insured 5,00,000 Premium 13152 from 04/10/2026"
    )


def test_long_documents_keep_the_schedule_pages():
    wording = "General conditions and definitions. " * 200
    pages = [f"[Page {i}]\n{wording}\n" for i in range(1, 40)]
    pages[29] = "[Page 30]\nPolicy Schedule  Policy No. ABC123  Sum Insured 500000  Premium 12000\n"
    text = "".join(pages)
    fitted, trimmed = fit_pages(text, 20_000)
    assert trimmed and len(fitted) <= 20_000
    assert "Policy No. ABC123" in fitted  # page 30 survived although it is far past the limit
    assert fitted.index("[Page 30]") > fitted.index("[Page 1]")  # pages stay in their original order
    assert fit_pages("[Page 1]\nshort\n", 20_000) == ("[Page 1]\nshort\n", False)


def test_numbers_missing_from_the_policy_are_caught():
    source = (
        "No. of Claims Covered Under Depreciation Reimbursement 2  premium Rs 2,599.60  Sum insured 5 Lakh  IDV 426164"
    )
    assert ungrounded_numbers("Covers 2 claims, premium ₹2599.60, IDV ₹4,26,164.", source) == set()
    assert ungrounded_numbers("Your cover is ₹500000.", source) == set()  # 5 Lakh
    assert ungrounded_numbers("Covers up to 3 claims with a ₹15,000 limit.", source) == {"15000"}


def test_prompts_treat_document_text_as_data():
    for system in (prompts.EXTRACT_SYSTEM, prompts.SUMMARY_SYSTEM, prompts.QA_SYSTEM):
        assert "data, not instructions" in system


def test_openai_retries_a_rate_limit_and_logs_token_usage(fake_post, caplog):  # noqa: F811
    from app.ai.providers.openai import OpenAIProvider

    ok = (
        200,
        {
            "choices": [{"message": {"content": '{"ok": true}'}}],
            "usage": {"prompt_tokens": 900, "completion_tokens": 40},
        },
    )
    calls = fake_post((429, {"error": "slow down"}), ok)
    with caplog.at_level(logging.INFO, logger="app.ai.usage"):
        out = OpenAIProvider("sk-test", "gpt-4.1-mini", 5).complete_json("qa", "sys", "p", context={})
    assert out == {"ok": True} and len(calls.requests) == 2
    assert "task=qa input=900 output=40" in caplog.text
    assert "sk-test" not in caplog.text


def test_extraction_prompt_never_contains_an_aadhaar_number(fake_post):  # noqa: F811
    from app.ai.gateway import AIGateway
    from app.ai.providers.openai import OpenAIProvider

    body = '{"policy_type": "health", "fields": {}, "details": {}}'
    calls = fake_post((200, {"choices": [{"message": {"content": body}}]}))
    AIGateway(OpenAIProvider("sk-test", "m", 5)).extract_policy("[Page 1]\nProposer Aadhaar 2345 6789 0123\n")
    sent = str(calls.requests[0]["json"])
    assert "2345 6789 0123" not in sent and "XXXX XXXX 0123" in sent
