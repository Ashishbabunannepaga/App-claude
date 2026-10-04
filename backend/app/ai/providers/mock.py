"""MOCK AI provider — offline, deterministic, for development and automated tests ONLY.

It does not understand language. It uses regex heuristics for extraction and returns the most
relevant retrieved excerpt for Q&A. Config validation refuses it when ENV=production.
"""

import re
from typing import Any

from app.ai.providers.base import AIProvider
from app.processing import heuristics as h

_STOP = {
    "is",
    "my",
    "the",
    "a",
    "an",
    "what",
    "how",
    "does",
    "do",
    "i",
    "in",
    "of",
    "for",
    "to",
    "covered",
    "cover",
    "policy",
    "much",
    "are",
    "it",
    "will",
    "have",
    "be",
    "can",
    "with",
}


class MockProvider(AIProvider):
    name = "mock"

    def complete_json(
        self, task: str, system: str, prompt: str, *, context: dict[str, Any], max_tokens: int = 2000
    ) -> dict[str, Any]:
        return getattr(self, f"_{task}")(context)

    def _extract(self, ctx: dict[str, Any]) -> dict[str, Any]:
        text: str = ctx["text"]
        start, end = h.find_dates(text)
        premium, cover = h.find_premium(text), h.find_sum_insured(text)
        values = {
            "insurer": h.find_insurer(text),
            "plan_name": None,
            "policy_number": h.find_policy_number(text),
            "start_date": start.isoformat() if start else None,
            "end_date": end.isoformat() if end else None,
            "premium": float(premium) if premium else None,
            "sum_insured": float(cover) if cover else None,
            "payment_frequency": "annual" if re.search(r"annual|yearly", text, re.I) else None,
        }
        return {
            "policy_type": h.classify(text),
            "fields": {k: {"value": v, "confidence": 0.7 if v is not None else 0.0} for k, v in values.items()},
            "details": {},
        }

    def _summary(self, ctx: dict[str, Any]) -> dict[str, Any]:
        p = ctx["structured"]
        return {
            "headline": f"[MOCK SUMMARY] {p.get('policy_type', 'insurance').title()} policy from "
            f"{p.get('insurer') or 'your insurer'}.",
            "key_points": [f"{k.replace('_', ' ').title()}: {v}" for k, v in p.items() if v][:6],
            "watch_outs": ["Configure a real AI provider to generate a plain-language summary."],
        }

    def _qa(self, ctx: dict[str, Any]) -> dict[str, Any]:
        terms = {t for t in re.findall(r"[a-z]+", ctx["question"].lower()) if t not in _STOP and len(t) > 2}
        best_id, best_score, best_text = None, 0, ""
        for chunk_id, labelled in ctx["chunks"]:
            text = re.sub(r"^\(page[^)]*\)\s*", "", labelled)
            score = sum(text.lower().count(t) for t in terms)
            if score > best_score:
                best_id, best_score, best_text = chunk_id, score, text
        if not best_id:
            return {
                "answerable": False,
                "answer": "I couldn't find this in your policy document.",
                "citations": [],
                "confidence": "low",
            }
        sentence = next(
            (s for s in re.split(r"(?<=[.!?])\s+", best_text) if any(t in s.lower() for t in terms)), best_text[:300]
        )
        return {
            "answerable": True,
            "answer": f'[MOCK ANSWER] Your document says: "{sentence.strip()}"',
            "citations": [best_id],
            "confidence": "low",
        }
