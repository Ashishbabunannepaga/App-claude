"""Coverage report: a sectioned checklist of what a policy covers, built from the user's own document.

Deterministic and explainable — no AI. Every row says where the answer came from (an extracted
field or a clause with its page). Anything the document doesn't mention is shown as "not found",
never guessed. Product-neutral: it explains the user's policy and never names or ranks products.
"""

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

from app.services.health_check import _NEG, _co_pay, _deductible, _ped, _room_rent

# good: works in your favour · limited: covered with a catch · missing: not covered
# info: a fact about the policy (charges, terms) · unknown: the document doesn't say
Status = str


@dataclass(frozen=True)
class ItemDef:
    key: str
    label: str
    why: str
    kind: str = "benefit"  # benefit | graded | info
    keywords: str | None = None  # regex used to find a supporting clause in the wording
    grade: Callable[[str], tuple[str, str]] | None = None  # for kind=graded (health_check rules)


@dataclass(frozen=True)
class SectionDef:
    key: str
    title: str
    subtitle: str
    items: tuple[ItemDef, ...]
    rated: bool = True


@dataclass
class Row:
    key: str
    label: str
    status: Status
    value: str
    why: str
    detail: str | None = None
    page: int | None = None
    source: str = "document"  # document | clause | none


@dataclass
class Section:
    key: str
    title: str
    subtitle: str
    rating: str | None
    items: list[Row] = field(default_factory=list)


# ---- Item catalogue --------------------------------------------------------------------------

HEALTH: tuple[SectionDef, ...] = (
    SectionDef(
        "essentials",
        "Essentials",
        "These decide how much of a hospital bill actually gets paid",
        (
            ItemDef(
                "sum_insured",
                "Sum insured",
                "The most the policy pays in a year. Big-city surgeries can cost " "₹5–15 lakh.",
                "info",
            ),
            ItemDef(
                "room_rent_limit",
                "Room rent",
                "A room-rent cap can cut the payout for the whole bill, not just " "the room.",
                "graded",
                r"room rent",
                _room_rent,
            ),
            ItemDef(
                "co_payment",
                "Co-payment",
                "A co-payment means you pay a share of every claim yourself.",
                "graded",
                r"co-?pay",
                _co_pay,
            ),
            ItemDef(
                "deductible",
                "Deductible",
                "With a deductible, the first part of each claim is paid by you.",
                "graded",
                r"deductible",
                _deductible,
            ),
            ItemDef(
                "ped_waiting_period",
                "Pre-existing illness waiting",
                "Illnesses you already had are covered " "only after this wait.",
                "graded",
                r"pre-?existing",
                _ped,
            ),
            ItemDef(
                "pre_post",
                "Before & after admission",
                "Tests and medicines before and after a hospital stay.",
                "benefit",
                r"pre-?hospitali|post-?hospitali",
            ),
        ),
    ),
    SectionDef(
        "important",
        "Important",
        "Make your cover go further",
        (
            ItemDef(
                "restoration",
                "Restoration of cover",
                "Refills your sum insured if it runs out in the year.",
                keywords=r"restor|recharge|reinstat",
            ),
            ItemDef(
                "no_claim_bonus",
                "No-claim bonus",
                "Your cover grows for every claim-free year.",
                keywords=r"no[- ]claim bonus|cumulative bonus",
            ),
            ItemDef(
                "day_care",
                "Day-care treatment",
                "Procedures that need less than 24 hours in hospital.",
                keywords=r"day ?care",
            ),
            ItemDef(
                "modern_treatment",
                "Modern treatments",
                "Robotic surgery, immunotherapy and similar care.",
                keywords=r"modern treatment|robotic|advanced treatment",
            ),
            ItemDef(
                "specific_disease_waiting_period",
                "Specific illness waiting",
                "Some illnesses (e.g. cataract, " "hernia) are covered only after a wait.",
                "info",
                r"specific (disease|illness)",
            ),
        ),
    ),
    SectionDef(
        "extras",
        "Extras",
        "Useful, but they rarely decide a big claim",
        (
            ItemDef("ambulance", "Ambulance", "Road ambulance to the hospital.", keywords=r"ambulance"),
            ItemDef(
                "ayush",
                "AYUSH treatment",
                "Ayurveda, Yoga, Unani, Siddha and Homeopathy in hospital.",
                keywords=r"ayush",
            ),
            ItemDef(
                "opd",
                "Doctor visits (OPD)",
                "Consultations and tests without admission.",
                keywords=r"\bopd\b|out-?patient",
            ),
            ItemDef(
                "home_healthcare",
                "Treatment at home",
                "Hospital-level treatment given at home.",
                keywords=r"home (health ?care|care|treatment)",
            ),
            ItemDef(
                "domiciliary",
                "Domiciliary care",
                "Treatment at home when you can't be moved to a hospital.",
                keywords=r"domiciliary",
            ),
        ),
    ),
    SectionDef(
        "personal",
        "Depends on your plans",
        "Matters for some families more than others",
        (
            ItemDef(
                "maternity",
                "Maternity",
                "Delivery and related expenses, usually after a waiting period.",
                keywords=r"maternity|delivery|pregnan",
            ),
        ),
    ),
)

LIFE: tuple[SectionDef, ...] = (
    SectionDef(
        "protection",
        "Your protection",
        "What your family receives and for how long",
        (
            ItemDef(
                "sum_assured",
                "Sum assured",
                "The amount paid to your nominee if something happens to you. "
                "A common rule of thumb is 10–15× yearly income.",
                "info",
            ),
            ItemDef(
                "death_benefit",
                "Death benefit",
                "How the payout to your family is worked out.",
                "info",
                r"death benefit",
            ),
            ItemDef("policy_term", "Policy term", "How long you are covered.", "info", r"policy term"),
            ItemDef(
                "premium_paying_term",
                "Premium paying term",
                "How many years you pay premiums.",
                "info",
                r"premium paying term",
            ),
            ItemDef("nominee", "Nominee", "Without a nominee, your family may need legal papers to claim.", "info"),
        ),
        rated=False,
    ),
    SectionDef(
        "costs",
        "Costs & charges",
        "What is deducted from your money",
        (
            ItemDef(
                "charges",
                "Charges",
                "Premium allocation, admin, fund management and mortality charges reduce " "what is invested.",
                "info",
                r"charges?",
            ),
            ItemDef("lock_in_period", "Lock-in", "Years before you can take money out.", "info", r"lock-?in"),
            ItemDef(
                "surrender",
                "Exit early (surrender)",
                "What you get back if you stop the policy early. Early " "exits usually lose money.",
                "info",
                r"surrender|discontinu",
            ),
        ),
        rated=False,
    ),
    SectionDef(
        "flexibility",
        "Flexibility & returns",
        "How your money grows and how you can access it",
        (
            ItemDef(
                "plan_category",
                "Plan type",
                "Term, endowment, money-back or ULIP — it decides how returns work.",
                "info",
            ),
            ItemDef("fund_options", "Fund options", "Funds you can invest in (ULIPs).", "info", r"fund option"),
            ItemDef(
                "partial_withdrawal",
                "Partial withdrawal",
                "Taking out part of the money before maturity.",
                "info",
                r"partial withdrawal",
            ),
            ItemDef(
                "bonus", "Bonus", "Extra amounts added by the insurer, usually not guaranteed.", "info", r"\bbonus"
            ),
            ItemDef(
                "maturity_benefit",
                "Maturity benefit",
                "What you get if you outlive the policy term.",
                "info",
                r"maturity",
            ),
            ItemDef(
                "riders", "Riders", "Add-on covers like accidental death or critical illness.", "info", r"\briders?\b"
            ),
        ),
        rated=False,
    ),
)

MOTOR: tuple[SectionDef, ...] = (
    SectionDef(
        "own_damage",
        "Own damage",
        "Damage to your own vehicle",
        (
            ItemDef("idv", "Insured value (IDV)", "The most you get if the vehicle is stolen or a total loss.", "info"),
            ItemDef(
                "own_damage_premium", "Own-damage premium", "The part of your premium for your own vehicle.", "info"
            ),
            ItemDef(
                "compulsory_deductible",
                "Deductible",
                "The part of each claim you pay yourself.",
                "info",
                r"deductible|excess",
            ),
            ItemDef(
                "ncb_percentage",
                "No-claim bonus",
                "Discount on renewal for claim-free years.",
                "info",
                r"no[- ]claim bonus|\bncb\b",
            ),
        ),
        rated=False,
    ),
    SectionDef(
        "third_party",
        "Third-party liability",
        "Injury or damage you cause to others (mandatory by law)",
        (
            ItemDef(
                "third_party_premium",
                "Third-party cover",
                "Required by law to drive on Indian roads.",
                "info",
                r"third[- ]party",
            ),
        ),
        rated=False,
    ),
    SectionDef(
        "add_ons",
        "Add-ons",
        "Extra covers that close common claim gaps",
        (
            ItemDef(
                "zero_depreciation",
                "Zero depreciation",
                "Without it, you pay for wear on replaced parts.",
                keywords=r"zero dep|nil dep|depreciation (cover|waiver)",
            ),
            ItemDef(
                "engine_protection",
                "Engine protection",
                "Covers engine damage from water or oil leaks, which " "a basic policy excludes.",
                keywords=r"engine (protect|secure|cover)",
            ),
            ItemDef(
                "return_to_invoice",
                "Return to invoice",
                "Pays the invoice price, not the depreciated value, " "on theft or total loss.",
                keywords=r"return to invoice|\brti\b",
            ),
            ItemDef(
                "consumables", "Consumables", "Nuts, bolts, oil and coolant used in repairs.", keywords=r"consumable"
            ),
            ItemDef(
                "roadside_assistance",
                "Roadside assistance",
                "Towing, flat tyre and fuel help on the road.",
                keywords=r"roadside|towing",
            ),
        ),
    ),
)

CATALOGUE: dict[str, tuple[SectionDef, ...]] = {"health": HEALTH, "life": LIFE, "motor": MOTOR}

# Everyday questions shown as cards at the top of the report, answered from the rows below.
SCENARIOS: dict[str, list[tuple[str, str, str]]] = {
    "health": [
        ("Will a delivery bill be paid?", "maternity", "maternity"),
        ("Is a private room paid in full?", "room_rent_limit", "room"),
        ("How long before existing illnesses are covered?", "ped_waiting_period", "clock"),
        ("Cover used up mid-year — what then?", "restoration", "refresh"),
        ("Do you pay a share of every bill?", "co_payment", "wallet"),
    ],
    "life": [
        ("How much would your family receive?", "sum_assured", "family"),
        ("Who receives the money?", "nominee", "nominee"),
        ("Can you exit early?", "surrender", "exit"),
        ("What is deducted as charges?", "charges", "wallet"),
        ("What do you get at the end of the term?", "maturity_benefit", "growth"),
    ],
    "motor": [
        ("Flood-damaged engine — are you covered?", "engine_protection", "engine"),
        ("Is depreciation on new parts covered?", "zero_depreciation", "parts"),
        ("Car stolen — do you get the invoice price?", "return_to_invoice", "theft"),
        ("Stuck on the highway?", "roadside_assistance", "tow"),
        ("What is your car insured for?", "idv", "car"),
    ],
}

DISCLAIMER = (
    "Based on the details we read from your document, for your understanding only. Your policy wording and the "
    "insurer's decision at claim time are final. This is not a recommendation to buy, keep or change a policy."
)
DEMO_NOTE = "Sample report with made-up policy details. Add your own policy to see your real cover."

_LIMIT_WORDS = re.compile(
    r"\bup ?to\b(?! (the )?(full )?(sum insured|si)\b)|sub-?limit|capped|limited to|waiting", re.I
)
_MONEY = re.compile(r"(?:rs\.?|inr|₹)\s*([0-9][0-9,]*)", re.I)


# ---- Formatting ------------------------------------------------------------------------------


def _inr(amount: Decimal | float | int) -> str:
    v = float(amount)
    if v >= 1e7:
        return f"₹{v / 1e7:g} crore"
    if v >= 1e5:
        return f"₹{v / 1e5:g} lakh"
    return f"₹{v:,.0f}"


def _text(value: Any) -> str:
    return ", ".join(map(str, value)) if isinstance(value, list) else str(value)


def _clip(v: str, limit: int = 24) -> str:
    if len(v) <= limit:
        return v
    cut = v[:limit].rsplit(" ", 1)[0].rstrip(",;:(")
    return cut + "…"


def _short(value: str, status: Status) -> str:
    """A short right-hand value for a row: 'Up to ₹50,000', '24 months', '1% of sum insured per day'…"""
    v = re.sub(r"\s+", " ", value).strip().rstrip(".")
    if len(v) <= 26:
        return v
    if status == "info":
        return _clip(v)
    patterns = [
        r"\d+(\.\d+)?\s*% of [a-z ]{2,24}",
        r"up ?to [^,.;]{1,24}",
        r"\d+\s*(days|months|years)",
        r"\d+(\.\d+)?\s*%",
    ]
    for p in patterns:
        m = re.search(p, v, re.I)
        if m:
            s = _clip(m.group(0).strip(), 28).rstrip("…").strip()
            return s[0].upper() + s[1:]
    m = _MONEY.search(v)
    if m:
        return f"₹{m.group(1)}"
    return {"good": "Covered", "limited": "Covered with limits", "missing": "Not covered"}.get(status, _clip(v))


# ---- Evaluation ------------------------------------------------------------------------------


def _find_clause(clauses: Sequence[Any], pattern: str | None) -> Any | None:
    if not pattern:
        return None
    rx = re.compile(pattern, re.I)
    for c in clauses:
        if rx.search(c.title or "") or rx.search(c.text or ""):
            return c
    return None


def _special_value(policy: Any, key: str) -> tuple[str | None, str | None]:
    """Values that live outside policy.details. Returns (value, detail)."""
    d = policy.details or {}
    if key == "sum_insured" and policy.sum_insured:
        return _inr(policy.sum_insured), None
    if key == "sum_assured":
        if policy.sum_insured:
            return _inr(policy.sum_insured), _text(d["sum_assured"]) if d.get("sum_assured") else None
    if key == "idv" and (d.get("idv") or policy.sum_insured):
        raw = d.get("idv")
        if raw and _MONEY.search(str(raw)) is None and re.fullmatch(r"[0-9,]+", str(raw).strip()):
            return _inr(Decimal(str(raw).replace(",", ""))), None
        return (_text(raw) if raw else _inr(policy.sum_insured)), None
    if key == "nominee":
        nominees = list(getattr(policy, "nominees", None) or [])
        if nominees:
            names = ", ".join(f"{n.full_name} ({n.share_percent}%)" for n in nominees)
            return f"{len(nominees)} added", names
    if key == "pre_post":
        pre, post = d.get("pre_hospitalisation_days"), d.get("post_hospitalisation_days")
        if pre or post:
            pre_days = re.search(r"\d+", str(pre or ""))
            post_days = re.search(r"\d+", str(post or ""))
            if pre_days and post_days:
                return f"{pre_days.group(0)}–{post_days.group(0)} days", f"Before: {pre}. After: {post}."
            return _text(pre or post), None
    return None, None


def _row(policy: Any, item: ItemDef, clauses: Sequence[Any]) -> Row:
    d = policy.details or {}
    clause = _find_clause(clauses, item.keywords)
    page = clause.page if clause is not None else None

    special, special_detail = _special_value(policy, item.key)
    raw = d.get(item.key)
    if special is None and raw in (None, "", []):
        if item.key == "nominee" and d.get("nominee"):
            raw = d["nominee"]
        elif clause is None:
            if item.key == "nominee":
                return Row(item.key, item.label, "missing", "None added", item.why, None, None, "none")
            return Row(item.key, item.label, "unknown", "Not found", item.why, None, None, "none")
        else:
            # Only the wording mentions it: classify from the clause itself.
            tags = clause.tags or [clause.clause_type]
            negative = "exclusion" in tags or bool(_NEG.search(clause.text))
            if item.kind == "info":
                status = "info"
            else:
                status = "missing" if negative else ("limited" if "limit" in tags else "good")
            return Row(item.key, item.label, status, _short(clause.text, status), item.why, clause.text, page, "clause")

    if special is not None:
        return Row(
            item.key,
            item.label,
            "good" if item.kind != "info" or item.key == "nominee" else "info",
            special,
            item.why,
            special_detail,
            page,
            "document",
        )

    text = _text(raw)
    if item.kind == "graded" and item.grade is not None:
        grade, explanation = item.grade(text)
        status = {"strong": "good", "attention": "limited", "not_covered": "missing"}[grade]
        return Row(
            item.key,
            item.label,
            status,
            _short(text, status),
            item.why,
            f"{explanation} {text}".strip(),
            page,
            "document",
        )
    if item.kind == "info":
        return Row(item.key, item.label, "info", _short(text, "info"), item.why, text, page, "document")
    status = "missing" if _NEG.search(text) else "good"
    if status == "good" and _LIMIT_WORDS.search(text):
        status = "limited"
    return Row(item.key, item.label, status, _short(text, status), item.why, text, page, "document")


def _rating(rows: list[Row], minimum: int = 1) -> str | None:
    graded = [r for r in rows if r.status in ("good", "limited", "missing")]
    if len(graded) < minimum:
        return None
    score = sum(1 if r.status == "good" else 0.5 if r.status == "limited" else 0 for r in graded) / len(graded)
    return "strong" if score >= 0.8 else "fair" if score >= 0.5 else "weak"


def _exclusions(policy: Any, clauses: Sequence[Any]) -> Section | None:
    rows: list[Row] = []
    listed = (policy.details or {}).get("exclusions")
    for text in (listed if isinstance(listed, list) else [listed] if listed else [])[:6]:
        rows.append(
            Row(
                f"exclusion_{len(rows)}",
                str(text)[:60],
                "missing",
                "Not covered",
                "Listed as an exclusion in your policy.",
                str(text),
                None,
                "document",
            )
        )
    for c in clauses:
        if len(rows) >= 6:
            break
        if c.clause_type == "exclusion":
            rows.append(
                Row(
                    f"exclusion_{len(rows)}",
                    c.title[:60],
                    "missing",
                    "Not covered",
                    "Listed as an exclusion in your policy.",
                    c.text,
                    c.page,
                    "clause",
                )
            )
    if not rows:
        return None
    return Section("exclusions", "Not covered", "Exclusions found in your policy", None, rows)


def _scenarios(policy_type: str, sections: list[Section]) -> list[dict]:
    rows = {r.key: r for s in sections for r in s.items}
    generic = {
        "good": "Yes, it's covered",
        "limited": "Covered, with limits",
        "missing": "No, it's not covered",
        "unknown": "Your document doesn't say",
    }
    out = []
    for question, key, art in SCENARIOS.get(policy_type, []):
        row = rows.get(key)
        if row is None:
            continue
        vague = row.value in ("Covered", "Not covered", "Not found", "Covered with limits")
        answer = generic.get(row.status, row.value) if vague or row.status == "unknown" else row.value
        out.append({"question": question, "item_key": key, "art": art, "status": row.status, "answer": answer})
    return out


def build_report(policy: Any, clauses: Sequence[Any] = (), demo: bool = False) -> dict:
    catalogue = CATALOGUE.get(policy.policy_type)
    if catalogue is None:
        return {
            "available": False,
            "policy_type": policy.policy_type,
            "demo": demo,
            "rating": None,
            "scenarios": [],
            "sections": [],
            "counts": {},
            "note": "Coverage reports are available for health, life and motor policies.",
            "disclaimer": DISCLAIMER,
        }
    sections = []
    for sd in catalogue:
        rows = [_row(policy, item, clauses) for item in sd.items]
        sections.append(Section(sd.key, sd.title, sd.subtitle, _rating(rows) if sd.rated else None, rows))
    if policy.policy_type in ("health", "motor"):
        excl = _exclusions(policy, clauses)
        if excl:
            sections.append(excl)

    rated_rows = [r for s in sections for r in s.items if s.key != "exclusions"]
    counts = {k: sum(1 for r in rated_rows if r.status == k) for k in ("good", "limited", "missing", "info", "unknown")}
    return {
        "available": True,
        "policy_type": policy.policy_type,
        "demo": demo,
        "title": getattr(policy, "plan_name", None) or getattr(policy, "insurer", None),
        "rating": _rating(rated_rows, minimum=3),
        "scenarios": _scenarios(policy.policy_type, sections),
        "sections": [
            {**{k: v for k, v in s.__dict__.items() if k != "items"}, "items": [r.__dict__ for r in s.items]}
            for s in sections
        ],
        "counts": counts,
        "note": DEMO_NOTE if demo else None,
        "disclaimer": DISCLAIMER,
    }


# ---- Sample policies for the demo report (fictional) ------------------------------------------

_DEMO_DETAILS: dict[str, tuple[Decimal, dict]] = {
    "health": (
        Decimal(1000000),
        {
            "room_rent_limit": "Single private room, up to 1% of sum insured per day",
            "co_payment": "No co-payment",
            "deductible": "Not applicable",
            "ped_waiting_period": "24 months",
            "pre_hospitalisation_days": "60 days",
            "post_hospitalisation_days": "180 days",
            "restoration": "Unlimited restoration of sum insured",
            "no_claim_bonus": "50% increase per claim-free year, up to 100%",
            "day_care": "All day-care procedures covered",
            "modern_treatment": "Covered up to 50% of sum insured",
            "specific_disease_waiting_period": "24 months",
            "ambulance": "Not covered",
            "ayush": "Covered up to sum insured",
            "opd": "Not covered",
            "home_healthcare": "Covered",
            "maternity": "Not covered",
            "exclusions": ["Cosmetic or plastic surgery", "Self-inflicted injury", "Treatment outside India"],
        },
    ),
    "life": (
        Decimal(5000000),
        {
            "death_benefit": "Higher of sum assured or 105% of premiums paid",
            "policy_term": "30 years",
            "premium_paying_term": "15 years",
            "plan_category": "ULIP",
            "charges": "Premium allocation, policy admin, fund management (1.35% p.a.) and mortality charges",
            "lock_in_period": "5 years",
            "surrender": "Allowed after 5 years; discontinuance charges apply earlier",
            "fund_options": "8 funds, 4 free switches a year",
            "partial_withdrawal": "Allowed after 5 years",
            "maturity_benefit": "Fund value at maturity",
            "riders": "Accidental death benefit",
        },
    ),
    "motor": (
        Decimal(650000),
        {
            "idv": "650000",
            "own_damage_premium": "₹9,840",
            "third_party_premium": "₹3,416",
            "compulsory_deductible": "₹1,000 per claim",
            "ncb_percentage": "25%",
            "zero_depreciation": "Covered",
            "engine_protection": "Not covered",
            "return_to_invoice": "Not covered",
            "consumables": "Covered",
            "roadside_assistance": "24x7 towing up to 50 km",
            "exclusions": ["Normal wear and tear", "Driving under the influence", "Driving without a valid licence"],
        },
    ),
}


def demo_report(policy_type: str) -> dict:
    sum_insured, details = _DEMO_DETAILS[policy_type]
    sample = SimpleNamespace(
        policy_type=policy_type,
        sum_insured=sum_insured,
        details=details,
        nominees=[],
        insurer=None,
        plan_name=f"Sample {policy_type} policy",
    )
    return build_report(sample, demo=True)
