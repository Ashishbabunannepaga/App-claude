"""Turns raw AI extraction output into validated, typed policy fields with confidence."""

import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any

from app.ai.prompts import CORE_FIELDS, DETAIL_FIELDS
from app.processing import heuristics as h

POLICY_TYPES = {"health", "life", "motor", "other"}
FREQUENCIES = {"annual", "half_yearly", "quarterly", "monthly", "single"}
# Fields the user is asked to verify; drive the overall confidence score.
KEY_FIELDS = ["insurer", "policy_number", "start_date", "end_date", "premium", "sum_insured"]


@dataclass
class ValidatedExtraction:
    policy_type: str
    values: dict[str, Any]
    confidence: dict[str, float]
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def overall_confidence(self) -> float:
        return round(sum(self.confidence.get(k, 0.0) for k in KEY_FIELDS) / len(KEY_FIELDS), 3)


def _conf(raw: Any) -> float:
    try:
        return max(0.0, min(1.0, float(raw)))
    except (TypeError, ValueError):
        return 0.0


def validate_extraction(raw: dict[str, Any], text: str) -> ValidatedExtraction:
    policy_type = raw.get("policy_type") if raw.get("policy_type") in POLICY_TYPES else h.classify(text)
    fields = raw.get("fields") or {}
    values: dict[str, Any] = {}
    confidence: dict[str, float] = {}
    norm_text = h.normalise(text)

    for name in CORE_FIELDS:
        item = fields.get(name) or {}
        value = item.get("value") if isinstance(item, dict) else item
        conf = _conf(item.get("confidence")) if isinstance(item, dict) else 0.5
        if value in ("", "null", None):
            value, conf = None, 0.0

        if value is not None and name in ("start_date", "end_date"):
            value = date.fromisoformat(value) if _is_iso(value) else h.parse_date(str(value))
            conf = conf if value else 0.0
        elif value is not None and name in ("premium", "sum_insured"):
            value = h.parse_amount(value)
            conf = conf if value else 0.0
        elif value is not None and name == "payment_frequency":
            value = str(value).lower().replace("-", "_").replace(" ", "_")
            if value not in FREQUENCIES:
                value, conf = None, 0.0
        elif value is not None:
            value = str(value).strip()[:200]

        # Grounding check: identifiers must literally appear in the document.
        if name == "policy_number" and value and h.normalise(value) not in norm_text:
            conf = min(conf, 0.3)
        if name in ("premium", "sum_insured") and isinstance(value, Decimal):
            if not _amount_in_text(value, text):
                conf = min(conf, 0.4)
        values[name], confidence[name] = value, round(conf, 3)

    start, end = values.get("start_date"), values.get("end_date")
    if start and end and start >= end:
        confidence["start_date"] = min(confidence["start_date"], 0.2)
        confidence["end_date"] = min(confidence["end_date"], 0.2)

    allowed = set(DETAIL_FIELDS[policy_type])
    details = {k: v for k, v in (raw.get("details") or {}).items() if k in allowed and v not in (None, "")}
    return ValidatedExtraction(policy_type, values, confidence, details)


def _is_iso(value: Any) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value))


def _amount_in_text(amount: Decimal, text: str) -> bool:
    numbers = {n.replace(",", "").split(".")[0] for n in re.findall(r"\d[\d,]*(?:\.\d+)?", text)}
    return str(int(amount)) in numbers
