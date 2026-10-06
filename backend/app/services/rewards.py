"""Coins for organising your own insurance (adding policies, nominees, family…).

Rewards are earned only for actions inside the app, never for buying, renewing or switching a policy
(rebates and inducements for buying insurance are restricted under Section 41 of the Insurance Act).
Coins have no cash value; redemption perks are announced separately.

Rewards are reconciled from the user's current data, so earning needs no hooks in other services, and
the (user, kind, ref) unique key makes it idempotent: deleting and re-adding the same policy earns once.
"""

import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import FamilyMember, Nominee, Policy, QaMessage, RewardEvent, User

POLICY_REWARD_CAP = 10  # policies that earn coins, per user


@dataclass(frozen=True)
class Task:
    kind: str
    title: str
    coins: int
    route: str  # where the app sends the user to complete it
    repeatable: bool = False


TASKS = [
    Task("profile", "Complete your profile", 20, "/settings/profile"),
    Task("policy_added", "Add a policy (each, up to 10)", 50, "/add", repeatable=True),
    Task("family_member", "Add a family member", 20, "/family"),
    Task("nominee", "Add a nominee to a policy", 20, "/portfolio"),
    Task("first_question", "Ask your first question about a policy", 10, "/portfolio"),
]
_COINS = {t.kind: t.coins for t in TASKS}

PERKS = [
    {"key": "health_checkup", "title": "Health check-up discounts", "icon": "lab"},
    {"key": "expert_review", "title": "Priority expert policy review", "icon": "expert"},
    {"key": "vouchers", "title": "Shopping vouchers", "icon": "gift"},
]


def _earned_now(db: Session, user: User) -> list[tuple[str, str]]:
    """(kind, ref) pairs the user qualifies for today."""
    out: list[tuple[str, str]] = []
    if user.full_name:
        out.append(("profile", ""))
    policy_ids = db.scalars(
        select(Policy.id).where(Policy.user_id == user.id, Policy.verified.is_(True)).order_by(Policy.created_at)
    ).all()
    out += [("policy_added", str(pid)) for pid in policy_ids]
    if db.scalar(select(func.count()).select_from(FamilyMember).where(FamilyMember.user_id == user.id)):
        out.append(("family_member", ""))
    has_nominee = db.scalar(
        select(func.count())
        .select_from(Nominee)
        .join(Policy, Nominee.policy_id == Policy.id)
        .where(Policy.user_id == user.id)
    )
    if has_nominee:
        out.append(("nominee", ""))
    if db.scalar(select(func.count()).select_from(QaMessage).where(QaMessage.user_id == user.id)):
        out.append(("first_question", ""))
    return out


def reconcile(db: Session, user: User) -> None:
    existing = set(db.execute(select(RewardEvent.kind, RewardEvent.ref).where(RewardEvent.user_id == user.id)).all())
    policy_rewards = sum(1 for kind, _ in existing if kind == "policy_added")
    rows = []
    for kind, ref in _earned_now(db, user):
        if (kind, ref) in existing:
            continue
        if kind == "policy_added":
            if policy_rewards >= POLICY_REWARD_CAP:
                continue
            policy_rewards += 1
        rows.append({"id": uuid.uuid4(), "user_id": user.id, "kind": kind, "ref": ref, "coins": _COINS[kind]})
    if rows:
        # ON CONFLICT DO NOTHING keeps two concurrent requests from failing on the unique key.
        db.execute(insert(RewardEvent).values(rows).on_conflict_do_nothing(constraint="uq_reward_event"))
        db.commit()


def summary(db: Session, user: User) -> dict:
    reconcile(db, user)
    events = db.scalars(
        select(RewardEvent).where(RewardEvent.user_id == user.id).order_by(RewardEvent.created_at.desc())
    ).all()
    done = {e.kind for e in events}
    policy_count = sum(1 for e in events if e.kind == "policy_added")
    titles = {t.kind: t.title for t in TASKS}
    return {
        "balance": sum(e.coins for e in events),
        "tasks": [
            {
                "kind": t.kind,
                "title": t.title,
                "coins": t.coins,
                "route": t.route,
                "done": (policy_count >= POLICY_REWARD_CAP) if t.repeatable else t.kind in done,
                "progress": f"{policy_count}/{POLICY_REWARD_CAP}" if t.repeatable else None,
            }
            for t in TASKS
        ],
        "history": [
            {"title": titles.get(e.kind, e.kind), "coins": e.coins, "created_at": e.created_at} for e in events[:50]
        ],
        "perks": PERKS,
        "note": "Coins have no cash value. Perks are being added — you'll be notified when you can use your coins.",
    }
