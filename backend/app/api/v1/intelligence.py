"""Nominees, clause library, portfolio insights and comparison of the user's own policies."""

import uuid
from typing import Literal

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import DB, CurrentUser
from app.core.errors import AppError, NotFound
from app.models import FamilyMember, Nominee, Policy, PolicyClause
from app.schemas.policy import ClauseOut, CompareOut, InsightsOut, NomineeIn, NomineeOut
from app.services import insights as insights_service
from app.services.compare import compare_policies
from app.services.policy_service import get_owned_policy

router = APIRouter(tags=["intelligence"])


# ---- Nominees -------------------------------------------------------------------------------


def _check_nominee(db, user_id: uuid.UUID, policy: Policy, body: NomineeIn, exclude: uuid.UUID | None = None) -> None:
    others = sum(n.share_percent for n in policy.nominees if n.id != exclude)
    if others + body.share_percent > 100:
        raise AppError("share_exceeds", f"Shares can't exceed 100%. {100 - others}% is left to assign.", 422)
    if body.family_member_id:
        owner = db.scalar(select(FamilyMember.user_id).where(FamilyMember.id == body.family_member_id))
        if owner != user_id:
            raise AppError("invalid_member", "Unknown family member", 422)


@router.get("/policies/{policy_id}/nominees", response_model=list[NomineeOut])
def list_nominees(policy_id: uuid.UUID, user: CurrentUser, db: DB) -> list[Nominee]:
    return list(get_owned_policy(db, user.id, policy_id).nominees)


@router.post("/policies/{policy_id}/nominees", response_model=NomineeOut, status_code=201)
def add_nominee(policy_id: uuid.UUID, body: NomineeIn, user: CurrentUser, db: DB) -> Nominee:
    policy = get_owned_policy(db, user.id, policy_id)
    _check_nominee(db, user.id, policy, body)
    nominee = Nominee(policy_id=policy.id, **body.model_dump())
    policy.nominees.append(nominee)
    db.commit()
    return nominee


@router.put("/policies/{policy_id}/nominees/{nominee_id}", response_model=NomineeOut)
def update_nominee(policy_id: uuid.UUID, nominee_id: uuid.UUID, body: NomineeIn, user: CurrentUser, db: DB) -> Nominee:
    policy = get_owned_policy(db, user.id, policy_id)
    nominee = next((n for n in policy.nominees if n.id == nominee_id), None)
    if nominee is None:
        raise NotFound("Nominee")
    _check_nominee(db, user.id, policy, body, exclude=nominee.id)
    for field, value in body.model_dump().items():
        setattr(nominee, field, value)
    db.commit()
    return nominee


@router.delete("/policies/{policy_id}/nominees/{nominee_id}", status_code=204)
def delete_nominee(policy_id: uuid.UUID, nominee_id: uuid.UUID, user: CurrentUser, db: DB) -> None:
    policy = get_owned_policy(db, user.id, policy_id)
    nominee = next((n for n in policy.nominees if n.id == nominee_id), None)
    if nominee is None:
        raise NotFound("Nominee")
    policy.nominees.remove(nominee)
    db.commit()


# ---- Clause library -------------------------------------------------------------------------


@router.get("/policies/{policy_id}/clauses", response_model=list[ClauseOut])
def list_clauses(
    policy_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    type: Literal["benefit", "exclusion", "waiting_period", "limit", "condition", "definition"] | None = None,
) -> list[PolicyClause]:
    policy = get_owned_policy(db, user.id, policy_id)
    q = select(PolicyClause).where(PolicyClause.policy_id == policy.id).order_by(PolicyClause.order)
    clauses = db.scalars(q).all()
    return [c for c in clauses if type is None or type in (c.tags or [c.clause_type])]


# ---- Portfolio insights & comparison ----------------------------------------------------------


@router.get("/portfolio/insights", response_model=InsightsOut)
def portfolio_insights(user: CurrentUser, db: DB) -> dict:
    return {
        "insights": insights_service.portfolio_insights(db, user.id),
        "disclaimer": insights_service.DISCLAIMER,
    }


@router.get("/policies/compare", response_model=CompareOut)
def compare(user: CurrentUser, db: DB, ids: list[uuid.UUID] = Query(..., max_length=3)) -> dict:
    policies = db.scalars(select(Policy).where(Policy.id.in_(ids), Policy.user_id == user.id)).all()
    if len(policies) != len(set(ids)):
        raise NotFound("Policy")
    order = {pid: i for i, pid in enumerate(ids)}
    return compare_policies(sorted(policies, key=lambda p: order[p.id]))
