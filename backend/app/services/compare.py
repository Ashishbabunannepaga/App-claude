"""Side-by-side comparison of the user's OWN policies (no market products)."""

from app.ai.prompts import DETAIL_FIELDS
from app.core.errors import AppError
from app.models import Policy
from app.services.health_check import health_check
from app.services.policy_service import annual_premium


def _fmt_money(v) -> str | None:
    """Indian digit grouping: 1000000 → ₹10,00,000."""
    if v is None:
        return None
    digits = str(round(float(v)))
    head, tail = digits[:-3], digits[-3:]
    groups = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    return "₹" + ",".join([g for g in [head, *groups] if g] + [tail]) if head or groups else f"₹{tail}"


def compare_policies(policies: list[Policy]) -> dict:
    if not 2 <= len(policies) <= 3:
        raise AppError("compare_count", "Choose 2 or 3 policies to compare", 422)
    types = {p.policy_type for p in policies}
    if len(types) > 1:
        raise AppError("compare_types", "Choose policies of the same type to compare", 422)
    ptype = types.pop()

    rows: list[dict] = []

    def add(
        label: str, values: list, best: str | None = None, section: str = "Overview", grades: list | None = None
    ) -> None:
        shown = [v if v not in (None, "") else None for v in values]
        best_index = None
        if (
            best
            and all(isinstance(v, int | float) for v in values if v is not None)
            and any(v is not None for v in values)
        ):
            candidates = [(v, i) for i, v in enumerate(values) if v is not None]
            pick = max(candidates) if best == "max" else min(candidates)
            if [v for v, _ in candidates].count(pick[0]) == 1 and len(candidates) > 1:
                best_index = pick[1]
        rows.append(
            {
                "section": section,
                "label": label,
                "values": shown,
                "best_index": best_index,
                "grades": grades or [None] * len(values),
            }
        )

    cover_label = {"motor": "IDV", "life": "Sum assured"}.get(ptype, "Sum insured")
    add("Plan", [p.plan_name for p in policies])
    add(cover_label, [float(p.sum_insured) if p.sum_insured else None for p in policies], "max")
    add("Annual premium", [float(annual_premium(p)) or None for p in policies], "min")
    add("Valid till", [f"{p.end_date.day} {p.end_date:%b %Y}" if p.end_date else None for p in policies])
    add("Covered members", [", ".join(m.full_name for m in p.members) or None for p in policies])

    if ptype in ("health", "motor"):
        checks = [health_check(p) for p in policies]
        add("Policy health score", [c["score"] for c in checks], "max", "Policy health")
        features: dict[str, tuple[list, list]] = {}
        for i, c in enumerate(checks):
            for grade in ("strong", "attention", "not_covered"):
                for f in (f for f in c[grade] if f["key"] != "sum_insured"):  # already in the overview
                    values, grades = features.setdefault(f["label"], ([None] * len(policies), [None] * len(policies)))
                    values[i] = "Not covered" if grade == "not_covered" else f["detail"]
                    grades[i] = grade
        for label, (values, grades) in features.items():
            add(label, values, section="Features", grades=grades)
    else:
        for key in DETAIL_FIELDS[ptype]:
            values = [(p.details or {}).get(key) for p in policies]
            if any(values):
                add(key.replace("_", " ").capitalize(), [str(v) if v else None for v in values], section="Details")

    return {
        "policy_type": ptype,
        "policies": [{"id": str(p.id), "insurer": p.insurer, "plan_name": p.plan_name} for p in policies],
        "rows": [
            {
                **r,
                "values": [_fmt_money(v) if r["label"] in (cover_label, "Annual premium") else v for v in r["values"]],
            }
            for r in rows
        ],
        "disclaimer": "Compares only what we read from your documents. Check the full policy wordings before deciding.",
    }
