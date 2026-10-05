"""Portfolio-level coverage insights (rules-based, product-neutral).

Insights describe gaps in what the user already has. They never name, rank or recommend an
insurer or product — that would be regulated advice (IRDAI) and needs a licensed structure first.
"""

import uuid
from dataclasses import asdict, dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import FamilyMember, Policy
from app.services.health_check import health_check
from app.services.policy_service import days_to_expiry, policy_status

SEVERITY_ORDER = {"high": 0, "medium": 1, "info": 2}
DISCLAIMER = (
    "These insights are based only on the policies you have added. They are for your understanding and are "
    "not a recommendation to buy any insurance product."
)


@dataclass
class Insight:
    id: str
    severity: str  # high | medium | info
    category: str  # gap | renewal | nominee | review | policy_health
    title: str
    detail: str
    action_label: str | None = None
    action_link: str | None = None
    policy_id: str | None = None


def _lakh(amount: Decimal) -> str:
    value = float(amount)
    return f"₹{value / 1e7:g} crore" if value >= 1e7 else f"₹{value / 1e5:g} lakh"


def portfolio_insights(db: Session, user_id: uuid.UUID) -> list[dict]:
    policies = db.scalars(select(Policy).where(Policy.user_id == user_id)).all()
    family = db.scalars(select(FamilyMember).where(FamilyMember.user_id == user_id)).all()
    verified = [p for p in policies if p.verified]
    live = [p for p in verified if policy_status(p) != "expired"]
    health = [p for p in live if p.policy_type == "health"]
    life = [p for p in live if p.policy_type == "life"]
    out: list[Insight] = []

    # Renewals first: they are time-critical.
    for p in verified:
        days = days_to_expiry(p)
        if p.renewal_status != "pending" or days is None:
            continue
        if days < 0:
            out.append(
                Insight(
                    f"expired:{p.id}",
                    "high",
                    "renewal",
                    f"{p.insurer or 'A'} {p.policy_type} policy has expired",
                    "You may not be covered. If you renewed it, mark it as renewed and add the new document.",
                    "View policy",
                    f"/policy/{p.id}",
                    str(p.id),
                )
            )
        elif days <= 30:
            out.append(
                Insight(
                    f"renewal:{p.id}",
                    "high",
                    "renewal",
                    f"{p.insurer or 'A'} {p.policy_type} policy expires in {days} days",
                    "Renew before the end date to avoid a break in cover and keep any no-claim bonus.",
                    "Renewal details",
                    f"/policy/{p.id}",
                    str(p.id),
                )
            )

    if not health:
        out.append(
            Insight(
                "gap:no-health",
                "high",
                "gap",
                "No health insurance found",
                "Hospital bills are the most common financial shock. Add your health policy if you have one, "
                "including any cover from your employer.",
                "Add policy",
                "/add",
            )
        )
    else:
        total = sum((p.sum_insured or Decimal(0) for p in health), Decimal(0))
        covered = {m.id for p in health for m in p.members}
        people = max(len(family), len(covered), 1)
        if total and people >= 3 and total < Decimal(1_000_000):
            out.append(
                Insight(
                    "gap:low-health-cover",
                    "medium",
                    "gap",
                    f"{_lakh(total)} health cover for {people} people",
                    "A single serious hospitalisation in a large city can cost more than this. Check whether "
                    "your cover matches your family's needs.",
                )
            )
        uncovered = [m for m in family if m.id not in covered]
        if health and uncovered:
            names = ", ".join(m.full_name for m in uncovered[:3])
            out.append(
                Insight(
                    "gap:uncovered-members",
                    "medium",
                    "gap",
                    f"{len(uncovered)} family member{'s' if len(uncovered) > 1 else ''} not linked to a health policy",
                    f"{names}. Link them to the policy that covers them, or add their policy.",
                    "Open family",
                    "/family",
                )
            )

    dependents = [m for m in family if m.relation in ("spouse", "child", "parent")]
    if dependents and not life:
        out.append(
            Insight(
                "gap:no-life",
                "medium",
                "gap",
                "No life cover found",
                f"{len(dependents)} family member{'s' if len(dependents) > 1 else ''} may depend on your income. "
                "Add your term or life policy if you have one.",
                "Add policy",
                "/add",
            )
        )

    for p in life:
        if not p.nominees:
            out.append(
                Insight(
                    f"nominee:{p.id}",
                    "high",
                    "nominee",
                    f"No nominee recorded for {p.insurer or 'your life policy'}",
                    "Record who the nominee is so your family knows how to claim. Check that it matches the "
                    "insurer's records.",
                    "Add nominee",
                    f"/policy/{p.id}/nominees",
                    str(p.id),
                )
            )
        elif sum(n.share_percent for n in p.nominees) != 100:
            out.append(
                Insight(
                    f"nominee-share:{p.id}",
                    "medium",
                    "nominee",
                    f"Nominee shares don't add up to 100% for {p.insurer}",
                    "Update the shares so they match your policy.",
                    "Review nominees",
                    f"/policy/{p.id}/nominees",
                    str(p.id),
                )
            )

    for p in [p for p in live if p.policy_type in ("health", "motor")]:
        check = health_check(p)
        issues = check["attention"] + check["not_covered"]
        if issues:
            first = issues[0]
            out.append(
                Insight(
                    f"health:{p.id}",
                    "info",
                    "policy_health",
                    f"{first['label']} · {p.insurer}",
                    first["detail"],
                    "Policy health",
                    f"/policy/{p.id}/health",
                    str(p.id),
                )
            )

    pending = [p for p in policies if not p.verified]
    if pending:
        out.append(
            Insight(
                "review:pending",
                "info",
                "review",
                f"{len(pending)} {'policy needs' if len(pending) == 1 else 'policies need'} your review",
                "Check the details we read from your documents.",
                "Review",
                f"/policy/{pending[0].id}/verify",
                str(pending[0].id),
            )
        )

    out.sort(key=lambda i: SEVERITY_ORDER[i.severity])
    return [asdict(i) for i in out]
