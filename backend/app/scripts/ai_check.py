"""Checks the configured AI and embedding providers with one tiny request each: `python -m app.scripts.ai_check`.

Run it after putting a key in `.env`. It prints what worked and what failed, never the key itself.
The sample policy below is fictional.
"""

import sys
import time

from app.ai.embeddings import get_embedder
from app.ai.gateway import get_ai_gateway
from app.ai.providers.base import AIProviderError
from app.core.config import get_settings
from app.processing.extraction import validate_extraction

SAMPLE = """Sample Health Insurance Co. Ltd.
Policy Schedule - Family Floater Health Plan
Policy Number: SHI/2026/000123
Period of Insurance: 01/04/2026 to 31/03/2027
Sum Insured: Rs. 5,00,000
Total Premium: Rs. 18,450 (annual)
Room rent: up to 1% of sum insured per day. Co-payment: 10% for insured aged above 60.
Pre-existing diseases are covered after 36 months of continuous coverage."""


def _hint(exc: Exception) -> str:
    text = str(exc)
    if "HTTP 400" in text or "HTTP 401" in text or "HTTP 403" in text:
        return "\n       Check the API key in .env (no quotes, no spaces) and that the API is enabled for it."
    if "HTTP 429" in text:
        return "\n       Rate limit or free-tier quota reached. Wait a minute or check your quota in AI Studio."
    if "HTTP 404" in text:
        return "\n       Model name not found. Check GEMINI_MODEL / GEMINI_EMBEDDING_MODEL."
    return ""


def main() -> int:
    s = get_settings()
    print(f"AI provider: {s.ai_provider} ({getattr(s, f'{s.ai_provider}_model', '-')})")
    print(f"Embeddings:  {s.embedding_provider}")
    ok = True

    t = time.monotonic()
    try:
        raw = get_ai_gateway().extract_policy(SAMPLE)
        result = validate_extraction(raw, SAMPLE)
        print(f"\n[OK] extraction in {time.monotonic() - t:.1f}s")
        for name in ("insurer", "policy_number", "start_date", "end_date", "sum_insured", "premium"):
            print(f"     {name:14} {result.values.get(name)!s:30} confidence {result.confidence.get(name, 0):.2f}")
    except (AIProviderError, RuntimeError) as exc:
        ok = False
        print(f"\n[FAIL] extraction: {exc}{_hint(exc)}")

    t = time.monotonic()
    try:
        vector = get_embedder().embed_query("Is maternity covered?")
        print(f"\n[OK] embedding in {time.monotonic() - t:.1f}s ({len(vector)} numbers)")
    except (AIProviderError, RuntimeError) as exc:
        ok = False
        print(f"\n[FAIL] embedding: {exc}{_hint(exc)}")

    if s.ai_provider == "mock" or s.embedding_provider == "hashing":
        print("\nNote: mock/hashing are offline stand-ins (MOCK). Set AI_PROVIDER and EMBEDDING_PROVIDER for real AI.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
