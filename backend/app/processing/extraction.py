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


def is_not_a_policy(raw: dict[str, Any], text: str) -> bool:
    """True for documents that are not insurance policies: no insurance markers at all, or the AI
    says so and the text has almost none. A real policy the AI misjudges still has plenty of markers."""
    signal = h.insurance_signal(text)
    return signal == 0 or (raw.get("policy_type") == "not_insurance" and signal < 3)


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

    _prefer_total_premium(values, text)
    _plausibility(policy_type, values, confidence)

    start, end = values.get("start_date"), values.get("end_date")
    if start and end and start >= end:
        confidence["start_date"] = min(confidence["start_date"], 0.2)
        confidence["end_date"] = min(confidence["end_date"], 0.2)

    allowed = set(DETAIL_FIELDS[policy_type])
    details = {k: v for k, v in (raw.get("details") or {}).items() if k in allowed and v not in (None, "")}
    ncb = details.get("ncb_percentage")
    if ncb is not None and NCB_NOT_CLAIMED.search(text) and not _ncb_discount_shown(ncb, text):
        # Motor schedules list the previous policy's NCB next to "NCB claimed: NA"; only a claimed NCB applies here.
        # But a discount line in this policy's premium schedule ("Less: No claim bonus (25%)") wins over a
        # proposal-section "NCB Claimed: NA".
        del details["ncb_percentage"]
    if details.get("registration_number"):
        # "AP 39 KS 7117", "AP-23-AL-2600" and "ap39ks7117" are the same vehicle.
        details["registration_number"] = re.sub(r"[^A-Za-z0-9]", "", str(details["registration_number"])).upper()
    return ValidatedExtraction(policy_type, values, confidence, details)


NCB_NOT_CLAIMED = re.compile(r"NCB\s*claimed\s*[:\-]?\s*(?:NA|N/A|Nil|No|0(?:\.0+)?\s*%?)(?![\w.])", re.IGNORECASE)


def _ncb_discount_shown(value: Any, text: str) -> bool:
    """Whether this policy's premium schedule shows the NCB discount right after its label: "No claim bonus (50%)",
    "No claim bonus 45%" or "NCB Discount(25%)". "NCB in Previous Policy: 25 %" does not count."""
    try:
        pct = int(float(str(value).strip().rstrip("%")))
    except ValueError:
        return False
    if pct <= 0:
        return False
    pattern = rf"(?:no\s*claim\s*bonus|\bNCB)(?:\s*discount)?\s*[:(]?\s*{pct}(?:\.0+)?\s*%"
    return re.search(pattern, text, re.IGNORECASE) is not None


# Schedules show "Net Premium 8758.91 · GST 1576.61 · Final Premium 10335.52"; the client pays the total.
GST_RATE = Decimal("0.18")


def _prefer_total_premium(values: dict[str, Any], text: str) -> None:
    """If the AI returned the pre-tax net premium, switch to the total the client pays: the document shows both
    the 18% GST on that amount (whole, or split as CGST + SGST) and the net + GST total. Table layouts lose the
    labels in extracted text, so this checks the arithmetic instead."""
    premium = values.get("premium")
    if not isinstance(premium, Decimal) or premium < MIN_PREMIUM:
        return
    amounts = [a for m in re.finditer(r"\d[\d,]*(?:\.\d{1,2})?", text) if (a := h.parse_amount(m.group(0)))]

    def in_text(amount: Decimal) -> Decimal | None:
        """The document's own figure within ₹1 of amount (it rounds GST its own way)."""
        return next((a for a in amounts if abs(a - amount) <= 1), None)

    gst = premium * GST_RATE
    total = in_text(premium + gst)
    if total is not None and total > premium and (in_text(gst) or in_text(gst / 2)):
        values["premium"] = total


# Below these, a "sum insured" is almost certainly a misread (a page number, a count, a lakh figure without unit).
MIN_SUM_INSURED = Decimal(10_000)
MIN_PREMIUM = Decimal(100)


def _plausibility(policy_type: str, values: dict[str, Any], confidence: dict[str, float]) -> None:
    """Flags values that cannot be right so the user is asked to check them, instead of trusting them."""
    cover, premium = values.get("sum_insured"), values.get("premium")
    if isinstance(cover, Decimal) and cover < MIN_SUM_INSURED:
        confidence["sum_insured"] = min(confidence["sum_insured"], 0.2)
    if isinstance(premium, Decimal) and premium < MIN_PREMIUM:
        confidence["premium"] = min(confidence["premium"], 0.2)
    # An annual premium larger than the cover is not a real health or motor policy (life single-premium can be).
    if (
        policy_type in ("health", "motor")
        and isinstance(cover, Decimal)
        and isinstance(premium, Decimal)
        and cover >= MIN_SUM_INSURED
        and premium > cover
    ):
        confidence["premium"] = min(confidence["premium"], 0.2)


def _is_iso(value: Any) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value))


def _amount_in_text(amount: Decimal, text: str) -> bool:
    # Matches "5,00,000", "500000" and "Rs. 5 Lakh" alike.
    return int(amount) in h.amounts_in_text(text)
