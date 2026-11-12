import json
import logging
from functools import lru_cache
from typing import Any

from app.ai import prompts
from app.ai.guardrails import fit_pages, redact
from app.ai.providers.base import AIProvider
from app.core.config import get_settings

MAX_EXTRACT_CHARS = 60_000  # about 30 dense pages; when longer, schedule pages are kept first
log = logging.getLogger(__name__)


class AIGateway:
    """Task-level AI API. Business code calls these methods, never a vendor SDK directly."""

    def __init__(self, provider: AIProvider):
        self.provider = provider

    @property
    def provider_name(self) -> str:
        return self.provider.name

    def extract_policy(self, text: str) -> dict[str, Any]:
        fitted, trimmed = fit_pages(redact(text), MAX_EXTRACT_CHARS)
        if trimmed:
            log.warning(
                "extraction text trimmed from %d to %d characters (schedule pages kept)", len(text), len(fitted)
            )
        prompt = prompts.EXTRACT_PROMPT.format(
            core_fields=", ".join(prompts.CORE_FIELDS),
            detail_fields=json.dumps(prompts.DETAIL_FIELDS, indent=1),
            text=fitted,
        )
        return self.provider.complete_json(
            "extract", prompts.EXTRACT_SYSTEM, prompt, context={"text": text}, max_tokens=8000
        )

    def summarise(self, structured: dict[str, Any], excerpts: str, language: str = "en") -> dict[str, Any]:
        prompt = prompts.SUMMARY_PROMPT.format(
            policy_type=structured.get("policy_type", "insurance"),
            structured=json.dumps(structured, default=str, indent=1),
            excerpts=redact(excerpts),
        )
        system = prompts.SUMMARY_SYSTEM + prompts.language_instruction(language)
        return self.provider.complete_json(
            "summary", system, prompt, context={"structured": structured, "language": language}, max_tokens=1500
        )

    def answer_question(
        self,
        question: str,
        structured: dict[str, Any],
        chunks: list[tuple[str, str]],
        language: str = "en",
        notes: list[str] | None = None,
    ) -> dict[str, Any]:
        excerpts = "\n\n".join(f"[{cid}] {redact(text)}" for cid, text in chunks) or "(none)"
        prompt = prompts.QA_PROMPT.format(
            structured=json.dumps(structured, default=str, indent=1),
            excerpts=excerpts,
            notes="\n".join(f"- {n}" for n in notes or []) or "(none)",
            question=redact(question),
        )
        system = prompts.QA_SYSTEM + prompts.language_instruction(language)
        return self.provider.complete_json(
            "qa",
            system,
            prompt,
            context={"question": question, "chunks": chunks, "language": language},
            max_tokens=1000,
        )


@lru_cache
def get_ai_gateway() -> AIGateway:
    s = get_settings()
    provider: AIProvider
    if s.ai_provider == "claude":
        from app.ai.providers.claude import ClaudeProvider

        if not s.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is required for the claude provider")
        provider = ClaudeProvider(s.anthropic_api_key, s.claude_model, s.ai_timeout_seconds)
    elif s.ai_provider == "openai":
        from app.ai.providers.openai import OpenAIProvider

        if not s.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for the openai provider")
        provider = OpenAIProvider(s.openai_api_key, s.openai_model, s.ai_timeout_seconds)
    elif s.ai_provider == "gemini":
        from app.ai.providers.gemini import GeminiProvider

        if not s.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is required for the gemini provider")
        provider = GeminiProvider(s.gemini_api_key, s.gemini_model, s.ai_timeout_seconds)
    else:
        from app.ai.providers.mock import MockProvider

        provider = MockProvider()
    return AIGateway(provider)
