"""Guardrails around every AI call: what may leave our servers, how much, and what we trust in the answer.

- redact():           government ID numbers never go to an AI vendor (they are never needed to read a policy).
- fit_pages():        long documents keep the schedule pages instead of being cut off at an arbitrary character.
- ungrounded_numbers(): numbers in an answer that appear nowhere in the policy text or data.
- log_usage():        token counts per task, for cost tracking. Never the text itself.
"""

import logging
import re
from typing import Any

log = logging.getLogger("app.ai.usage")

# Aadhaar: 12 digits, first digit 2-9, usually written 4-4-4. PAN: 5 letters, 4 digits, 1 letter.
# Masked keeping the last 4, the way Indian documents print them, so the text still reads naturally.
_AADHAAR = re.compile(r"(?<![\d])([2-9]\d{3})[\s-]?(\d{4})[\s-]?(\d{4})(?![\d])")
_PAN = re.compile(r"\b([A-Z]{5})(\d{4})([A-Z])\b")
# Indian bank account numbers are 9-18 digits; only masked where the text says it is an account number.
_ACCOUNT = re.compile(r"(?i)((?:a/?c|account)\s*(?:no\.?|number)?\s*[:\-]?\s*)(\d{5,14})(\d{4})\b")


def redact(text: str) -> str:
    """Masks Aadhaar, PAN and bank account numbers. Policy numbers, amounts and dates are left alone."""
    text = _AADHAAR.sub(lambda m: f"XXXX XXXX {m.group(3)}", text)
    text = _PAN.sub(lambda m: "XXXXXXXXX" + m.group(3), text)
    return _ACCOUNT.sub(lambda m: f"{m.group(1)}{'X' * len(m.group(2))}{m.group(3)}", text)


_PAGE = re.compile(r"(?=\[Page \d+\]\n)")
# Words that mark the pages holding the fields we extract (schedule, certificate, premium table, period).
_SCHEDULE_WORDS = re.compile(
    r"(?i)policy\s*(no|number)|sum\s*insured|premium|period\s*of\s*insurance|schedule|certificate|"
    r"insured\s*declared\s*value|\bidv\b|valid\s*(from|till)|nominee|plan\s*name|date\s*of\s*expiry"
)


def fit_pages(text: str, max_chars: int) -> tuple[str, bool]:
    """Text of at most max_chars, as whole pages: schedule-like pages first, then the rest in page order,
    always output in the original order. Returns (text, trimmed)."""
    if len(text) <= max_chars:
        return text, False
    pages = [p for p in _PAGE.split(text) if p]
    ranked = sorted(range(len(pages)), key=lambda i: (-len(_SCHEDULE_WORDS.findall(pages[i])), i))
    keep, used = set(), 0
    for i in ranked:
        if used + len(pages[i]) > max_chars:
            continue
        keep.add(i)
        used += len(pages[i])
    if not keep:  # one huge page: fall back to its start
        return text[:max_chars], True
    return "".join(pages[i] for i in sorted(keep)), True


_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


def _numbers(text: str) -> set[str]:
    out = set()
    for n in _NUMBER.findall(text):
        plain = n.replace(",", "").rstrip(".")
        if "." in plain:
            plain = plain.rstrip("0").rstrip(".")
        out.add(plain)
    return out


def ungrounded_numbers(answer: str, source: str) -> set[str]:
    """Numbers of 2+ digits in the answer that don't appear in the source (commas and trailing zeros ignored).
    Lakh/crore wording ("5 lakh" for 500000) is accepted when the figure itself is in the source."""
    have = _numbers(source)
    lakh = {str(int(float(n) * unit)) for n in have for unit in (100_000, 10_000_000)}
    missing = set()
    for n in _numbers(answer):
        if len(n.replace(".", "")) < 2 or n in have:
            continue
        try:
            if str(int(float(n))) in have or n in lakh:
                continue
        except ValueError:
            pass
        missing.add(n)
    return missing


def log_usage(provider: str, model: str, task: str, usage: dict[str, Any] | None) -> None:
    if usage:
        log.info(
            "ai usage provider=%s model=%s task=%s input=%s output=%s",
            provider,
            model,
            task,
            usage.get("prompt_tokens", usage.get("input_tokens")),
            usage.get("completion_tokens", usage.get("output_tokens")),
        )
