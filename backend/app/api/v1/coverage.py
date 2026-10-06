"""Coverage report (own policy + sample) and rewards."""

import uuid
from typing import Literal

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import DB, CurrentUser
from app.models import PolicyClause
from app.schemas.coverage import CoverageReportOut, RewardsOut
from app.services import rewards
from app.services.coverage_report import build_report, demo_report
from app.services.policy_service import get_owned_policy

router = APIRouter(tags=["coverage"])


@router.get("/policies/{policy_id}/coverage-report", response_model=CoverageReportOut)
def coverage_report(policy_id: uuid.UUID, user: CurrentUser, db: DB) -> dict:
    policy = get_owned_policy(db, user.id, policy_id)
    clauses = db.scalars(
        select(PolicyClause).where(PolicyClause.policy_id == policy.id).order_by(PolicyClause.order)
    ).all()
    return build_report(policy, clauses)


@router.get("/coverage/demo/{policy_type}", response_model=CoverageReportOut)
def coverage_demo(policy_type: Literal["health", "life", "motor"], user: CurrentUser) -> dict:
    return demo_report(policy_type)


@router.get("/rewards", response_model=RewardsOut)
def my_rewards(user: CurrentUser, db: DB) -> dict:
    return rewards.summary(db, user)
