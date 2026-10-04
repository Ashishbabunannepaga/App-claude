import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFound
from app.models import Document, Policy
from app.schemas.policy import PolicyOut, PortfolioSummary, RenewalItem

EXPIRING_SOON_DAYS = 30
RENEWAL_WINDOW_DAYS = 90


def get_owned_policy(db: Session, user_id: uuid.UUID, policy_id: uuid.UUID) -> Policy:
    policy = db.scalar(select(Policy).where(Policy.id == policy_id, Policy.user_id == user_id))
    if policy is None:
        raise NotFound("Policy")
    return policy


def get_owned_document(db: Session, user_id: uuid.UUID, document_id: uuid.UUID) -> Document:
    doc = db.scalar(select(Document).where(Document.id == document_id, Document.user_id == user_id))
    if doc is None:
        raise NotFound("Document")
    return doc


def days_to_expiry(policy: Policy, today: date | None = None) -> int | None:
    if policy.end_date is None:
        return None
    return (policy.end_date - (today or date.today())).days


def policy_status(policy: Policy, today: date | None = None) -> str:
    days = days_to_expiry(policy, today)
    if days is None:
        return "unknown"
    if days < 0:
        return "expired"
    return "expiring_soon" if days <= EXPIRING_SOON_DAYS else "active"


def to_out(policy: Policy) -> PolicyOut:
    data = {c: getattr(policy, c) for c in PolicyOut.model_fields if hasattr(policy, c)}
    data.update(status=policy_status(policy), days_to_expiry=days_to_expiry(policy))
    data["field_confidence"] = policy.field_confidence or {}
    data["details"] = policy.details or {}
    data["members"] = sorted(policy.members, key=lambda m: m.full_name)
    return PolicyOut.model_validate(data)


def annual_premium(policy: Policy) -> Decimal:
    if policy.premium is None:
        return Decimal(0)
    factor = {"monthly": 12, "quarterly": 4, "half_yearly": 2}.get(policy.payment_frequency or "", 1)
    return policy.premium * factor if policy.payment_frequency != "single" else Decimal(0)


def portfolio_summary(db: Session, user_id: uuid.UUID) -> PortfolioSummary:
    policies = db.scalars(select(Policy).where(Policy.user_id == user_id)).all()
    verified = [p for p in policies if p.verified]
    live = [p for p in verified if policy_status(p) in ("active", "expiring_soon", "unknown")]
    due = [p for p in live if p.renewal_status == "pending"]
    by_type: dict[str, int] = {}
    for p in policies:
        by_type[p.policy_type] = by_type.get(p.policy_type, 0) + 1
    renewals = sorted(
        (
            RenewalItem(
                policy_id=p.id,
                policy_type=p.policy_type,
                insurer=p.insurer,
                end_date=p.end_date,
                days_to_expiry=days_to_expiry(p),
            )
            for p in due
            if p.end_date and 0 <= days_to_expiry(p) <= RENEWAL_WINDOW_DAYS
        ),
        key=lambda r: r.days_to_expiry,
    )
    return PortfolioSummary(
        total_policies=len(policies),
        active_policies=len(live),
        expiring_soon=sum(1 for p in due if policy_status(p) == "expiring_soon"),
        pending_verification=len(policies) - len(verified),
        total_annual_premium=sum((annual_premium(p) for p in live), Decimal(0)),
        health_cover=sum((p.sum_insured or 0 for p in live if p.policy_type == "health"), Decimal(0)),
        life_cover=sum((p.sum_insured or 0 for p in live if p.policy_type == "life"), Decimal(0)),
        by_type=by_type,
        upcoming_renewals=renewals,
    )


def structured_view(policy: Policy) -> dict:
    """Policy facts given to the LLM as context (no user personal data)."""
    return {
        "policy_type": policy.policy_type,
        "insurer": policy.insurer,
        "plan_name": policy.plan_name,
        "policy_number": policy.policy_number,
        "start_date": policy.start_date,
        "end_date": policy.end_date,
        "premium": policy.premium,
        "sum_insured": policy.sum_insured,
        "payment_frequency": policy.payment_frequency,
        **(policy.details or {}),
    }
