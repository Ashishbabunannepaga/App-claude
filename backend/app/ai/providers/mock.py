"""MOCK AI provider — offline, deterministic, for development, demos and automated tests ONLY.

It does not understand language: it uses regex/keyword heuristics for extraction, and quotes the most
relevant retrieved excerpt for Q&A. Responses carry provider="mock" so the app can label them.
Config validation refuses it when ENV=production.
"""

import re
from typing import Any

from app.ai.prompts import DETAIL_FIELDS
from app.ai.providers.base import AIProvider
from app.processing import heuristics as h
from app.processing.glossary import english_terms
from app.processing.text_utils import sentences as _sentences

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

DETAIL_KEYWORDS: dict[str, list[str]] = {
    "room_rent_limit": ["room rent"],
    "initial_waiting_period": ["initial waiting", "first 30 days"],
    "ped_waiting_period": ["pre-existing"],
    "specific_disease_waiting_period": ["specific disease", "specified disease"],
    "pre_hospitalisation_days": ["pre-hospitalisation", "pre-hospitalization", "pre hospitalisation"],
    "post_hospitalisation_days": ["post-hospitalisation", "post-hospitalization", "post hospitalisation"],
    "maternity": ["maternity"],
    "opd": ["opd", "out-patient", "outpatient"],
    "day_care": ["day care", "daycare", "day-care"],
    "ambulance": ["ambulance"],
    "domiciliary": ["domiciliary"],
    "home_healthcare": ["home care", "home healthcare", "home health care"],
    "ayush": ["ayush"],
    "modern_treatment": ["modern treatment", "robotic", "advanced treatment"],
    "no_claim_bonus": ["no claim bonus", "cumulative bonus", "no-claim bonus"],
    "deductible": ["deductible"],
    "co_payment": ["co-pay", "copay", "co pay"],
    "restoration": ["restoration", "restore", "recharge", "refill"],
    "tpa": ["tpa", "third party administrator"],
    "exclusions": ["not covered", "excluded", "exclusion"],
    "vehicle_make_model": ["make/model", "make & model", "vehicle make", "model:"],
    "registration_number": ["registration no", "registration number", "reg. no"],
    "idv": ["idv", "insured declared value"],
    "zero_depreciation": ["zero dep", "nil depreciation"],
    "engine_protection": ["engine protect"],
    "return_to_invoice": ["return to invoice"],
    "consumables": ["consumable"],
    "roadside_assistance": ["roadside"],
    "ncb_percentage": ["ncb", "no claim bonus"],
    "compulsory_deductible": ["compulsory deductible"],
    "nominee": ["nominee"],
    "death_benefit": ["death benefit", "on death"],
    "maturity_benefit": ["maturity"],
    "policy_term": ["policy term"],
    "premium_paying_term": ["premium paying term", "premium payment term"],
    "riders": ["rider"],
    "life_assured": ["life assured"],
    "surrender": ["surrender"],
}


def _lakh(amount: float) -> str:
    if amount >= 1e7:
        return f"₹{amount / 1e7:g} crore"
    if amount >= 1e5:
        return f"₹{amount / 1e5:g} lakh"
    return f"₹{amount:,.0f}"


_WATCH = re.compile(
    r"\bnot (covered|included|payable)\b|exclu|waiting period|per day|\d+% co-?payment|deductible", re.I
)


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
        plan = re.search(r"(?:plan(?: name)?|product)\s*[:\-]\s*([^\n]{3,80})", text, re.I)
        policy_type = h.classify(text)
        values = {
            "insurer": h.find_insurer(text),
            "plan_name": plan.group(1).strip() if plan else None,
            "policy_number": h.find_policy_number(text),
            "start_date": start.isoformat() if start else None,
            "end_date": end.isoformat() if end else None,
            "premium": float(premium) if premium else None,
            "sum_insured": float(cover) if cover else None,
            "payment_frequency": "annual" if re.search(r"annual|yearly", text, re.I) else None,
        }
        sentences = _sentences(text)
        details: dict[str, str] = {}
        for field in DETAIL_FIELDS[policy_type]:
            for kw in DETAIL_KEYWORDS.get(field, []):
                hit = next((s for s in sentences if kw in s.lower()), None)
                if hit:
                    details[field] = hit[:240]
                    break
        return {
            "policy_type": policy_type,
            "fields": {k: {"value": v, "confidence": 0.7 if v is not None else 0.0} for k, v in values.items()},
            "details": details,
        }

    def _summary(self, ctx: dict[str, Any]) -> dict[str, Any]:
        p = ctx["structured"]
        kind = {"health": "health insurance", "life": "life insurance", "motor": "motor insurance"}.get(
            p.get("policy_type"), "insurance"
        )
        cover = p.get("sum_insured")
        headline = f"A {kind} policy from {p.get('insurer') or 'your insurer'}"
        headline += f" with {_lakh(float(cover))} cover." if cover else "."
        if ctx.get("language") == "hi":
            kind_hi = {"health": "स्वास्थ्य", "life": "जीवन", "motor": "मोटर"}.get(p.get("policy_type"), "")
            headline = f"{p.get('insurer') or 'आपकी'} की {kind_hi} बीमा पॉलिसी"
            amount = _lakh(float(cover)).replace("lakh", "लाख").replace("crore", "करोड़") if cover else ""
            headline += f", {amount} कवर के साथ।" if cover else "।"
        details = [str(v) for k, v in p.items() if k in DETAIL_KEYWORDS and k not in ("tpa", "exclusions") and v]
        key_points = [v for v in details if not _WATCH.search(v)][:6]
        watch_outs = [v for v in details if _WATCH.search(v)][:4]
        return {"headline": headline, "key_points": key_points, "watch_outs": watch_outs}

    def _qa(self, ctx: dict[str, Any]) -> dict[str, Any]:
        hindi = ctx.get("language") == "hi"
        question = f"{ctx['question']} {english_terms(ctx['question'])}"
        terms = {t for t in re.findall(r"[a-z]+", question.lower()) if t not in _STOP and len(t) > 2}
        best_id, best_score, best_text = None, 0, ""
        for chunk_id, labelled in ctx["chunks"]:
            text = re.sub(r"^\(page[^)]*\)\s*", "", labelled)
            score = max((len({t for t in terms if t in s.lower()}) for s in _sentences(text)), default=0)
            if score > best_score:
                best_id, best_score, best_text = chunk_id, score, text
        if not best_id:
            return {
                "answerable": False,
                "answer": "यह जानकारी आपके पॉलिसी दस्तावेज़ में नहीं मिली।"
                if hindi
                else "I couldn't find this in your policy document.",
                "citations": [],
                "confidence": "low",
            }
        sentences = _sentences(best_text)
        # The sentence matching the most distinct question terms (ties: earliest).
        scores = [len({t for t in terms if t in s.lower()}) for s in sentences]
        idx = scores.index(max(scores)) if scores else 0
        quote = sentences[idx] if sentences else best_text[:300]
        return {
            "answerable": True,
            "answer": f"आपके पॉलिसी दस्तावेज़ में लिखा है: “{quote}”" if hindi else f"Your policy document says: “{quote}”",
            "citations": [best_id],
            "confidence": "medium",
        }
