"""Rules-based Policy Health check (V1). Deterministic and explainable — no AI.

Each feature is graded strong / attention / not_covered from the extracted policy details.
Features the document doesn't mention are listed separately and never guessed.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal

from app.models import Policy

_NEG = re.compile(
    r"\b(not covered|not payable|excluded|not available|not applicable|not included|not offered)\b"
    r"|^\s*(no|nil|none)\s*[.,]?\s*$",
    re.I,
)
_NO_LIMIT = re.compile(
    r"\b(no (room rent )?(limit|cap|capping|restriction|sub-?limit)|any room|no sub-?limits?)\b", re.I
)
_LIMITED = re.compile(r"(\d+(\.\d+)?\s*%|up ?to|limit|capped|single private|shared|twin sharing|per day)", re.I)

Grade = str  # strong | attention | not_covered


@dataclass
class Finding:
    key: str
    label: str
    grade: Grade
    detail: str


def _covered(value: str) -> bool:
    return not _NEG.search(value)


def _says_none(value: str, term: str) -> bool:
    """'No co-payment', 'Co-payment: Nil', 'Deductible: 0' …"""
    return bool(
        re.search(rf"\b(no|nil|without)\b[^.]{{0,20}}{term}", value, re.I)
        or re.search(rf"{term}[^.]{{0,25}}\b(nil|none|not applicable|0\s*%?)(?![\d,])", value, re.I)
        or _NEG.search(value)
    )


def _months(value: str) -> int | None:
    m = re.search(r"(\d+)\s*(month|year)", value, re.I)
    if not m:
        return None
    n = int(m.group(1))
    return n * 12 if m.group(2).lower().startswith("year") else n


def _days(value: str, prefix: str) -> int | None:
    m = re.search(prefix + r"[^\d]{0,40}?(\d+)\s*days", value, re.I) or re.search(r"(\d+)\s*days", value, re.I)
    return int(m.group(1)) if m else None


def _percent(value: str) -> float | None:
    m = re.search(r"(\d+(\.\d+)?)\s*%", value)
    return float(m.group(1)) if m else None


def _cover_benefit(label: str) -> Callable[[str], tuple[Grade, str]]:
    def rule(v: str) -> tuple[Grade, str]:
        return ("strong", f"{label} is covered.") if _covered(v) else ("not_covered", f"{label} is not covered.")

    return rule


def _room_rent(v: str) -> tuple[Grade, str]:
    if _NO_LIMIT.search(v):
        return "strong", "No room-rent limit."
    if _LIMITED.search(v):
        return "attention", "Room rent is limited. Choosing a costlier room can reduce what is paid for the whole bill."
    return "strong", "Room rent is covered."


def _co_pay(v: str) -> tuple[Grade, str]:
    pct = _percent(v)
    if _says_none(v, r"co-?pay") or pct == 0:
        return "strong", "No co-payment."
    return "attention", f"You pay {pct:g}% of every claim yourself." if pct else "A co-payment applies to claims."


def _deductible(v: str) -> tuple[Grade, str]:
    if _says_none(v, "deductible"):
        return "strong", "No deductible."
    return "attention", "A deductible applies — claims below it are paid by you."


def _ped(v: str) -> tuple[Grade, str]:
    months = _months(v)
    if months is None:
        return "attention", "Pre-existing diseases have a waiting period."
    if months <= 24:
        return "strong", f"Pre-existing diseases covered after {months} months."
    return "attention", f"Pre-existing diseases covered only after {months} months."


def _pre_post(policy: Policy) -> Finding | None:
    d = policy.details or {}
    pre_text, post_text = d.get("pre_hospitalisation_days"), d.get("post_hospitalisation_days")
    if not pre_text and not post_text:
        return None
    pre = _days(str(pre_text or ""), "pre")
    post = _days(str(post_text or ""), "post")
    if pre is None or post is None:
        return Finding(
            "pre_post", "Pre/post hospitalisation", "strong", "Pre and post hospitalisation expenses are covered."
        )
    grade = "strong" if pre >= 30 and post >= 60 else "attention"
    return Finding("pre_post", "Pre/post hospitalisation", grade, f"{pre} days before and {post} days after admission.")


def _sum_insured(policy: Policy) -> Finding | None:
    if not policy.sum_insured:
        return None
    lakhs = float(policy.sum_insured / Decimal(100000))
    amount = f"₹{lakhs:g} lakh"
    if lakhs >= 10:
        return Finding("sum_insured", "Sum insured", "strong", f"{amount} cover.")
    return Finding(
        "sum_insured",
        "Sum insured",
        "attention",
        f"{amount} cover. Major treatment in large-city hospitals can cost more than this.",
    )


HEALTH_RULES: list[tuple[str, str, Callable[[str], tuple[Grade, str]]]] = [
    ("room_rent_limit", "Room rent", _room_rent),
    ("co_payment", "Co-payment", _co_pay),
    ("deductible", "Deductible", _deductible),
    ("ped_waiting_period", "Pre-existing disease waiting", _ped),
    ("restoration", "Restoration of cover", _cover_benefit("Restoration of sum insured")),
    ("no_claim_bonus", "No-claim bonus", _cover_benefit("No-claim bonus")),
    ("maternity", "Maternity", _cover_benefit("Maternity")),
    ("day_care", "Day-care procedures", _cover_benefit("Day-care treatment")),
    ("ambulance", "Ambulance", _cover_benefit("Ambulance")),
    ("ayush", "AYUSH treatment", _cover_benefit("AYUSH treatment")),
    ("modern_treatment", "Modern treatments", _cover_benefit("Modern treatment")),
    ("opd", "OPD / doctor visits", _cover_benefit("OPD")),
    ("domiciliary", "Treatment at home", _cover_benefit("Domiciliary treatment")),
]

MOTOR_RULES: list[tuple[str, str, Callable[[str], tuple[Grade, str]]]] = [
    ("zero_depreciation", "Zero depreciation", _cover_benefit("Zero depreciation")),
    ("engine_protection", "Engine protection", _cover_benefit("Engine protection")),
    ("consumables", "Consumables", _cover_benefit("Consumables")),
    ("return_to_invoice", "Return to invoice", _cover_benefit("Return to invoice")),
    ("roadside_assistance", "Roadside assistance", _cover_benefit("Roadside assistance")),
]

DISCLAIMER = (
    "This check is based on the details we read from your document and is for your understanding only. "
    "It is not a recommendation to buy, keep or change any policy."
)


def health_check(policy: Policy) -> dict:
    rules = {"health": HEALTH_RULES, "motor": MOTOR_RULES}.get(policy.policy_type)
    if rules is None:
        return {
            "available": False,
            "score": None,
            "strong": [],
            "attention": [],
            "not_covered": [],
            "not_mentioned": [],
            "disclaimer": "Policy health checks are available for health and motor policies.",
        }

    details = policy.details or {}
    findings: list[Finding] = []
    not_mentioned: list[str] = []
    if policy.policy_type == "health":
        findings += [f for f in (_sum_insured(policy), _pre_post(policy)) if f]
    for key, label, rule in rules:
        value = details.get(key)
        if value in (None, "", []):
            not_mentioned.append(label)
            continue
        grade, text = rule(", ".join(map(str, value)) if isinstance(value, list) else str(value))
        findings.append(Finding(key, label, grade, text))

    by = {g: [f.__dict__ for f in findings if f.grade == g] for g in ("strong", "attention", "not_covered")}
    graded = len(findings)
    score = round(100 * (len(by["strong"]) + 0.5 * len(by["attention"])) / graded) if graded else None
    return {"available": graded > 0, "score": score, **by, "not_mentioned": not_mentioned, "disclaimer": DISCLAIMER}
