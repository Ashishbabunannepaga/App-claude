"""Leads feed for CapitUp's LMS.

Only users who ticked "CapitUp may contact me" appear with contact details. Users who later
withdraw (or ask to delete their account) still appear once more, without any personal data,
so the LMS can stop calling them. Policy numbers, documents and AI conversations are never shared.

The LMS pulls this feed incrementally: pass the returned `next_cursor` back to get only what
changed since. Protected by a shared token (LEADS_API_TOKEN, header `X-Leads-Token`); every
call is audited.
"""

import base64
import hmac
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header, Query, Request
from pydantic import BaseModel
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import DB, client_ip
from app.core.config import get_settings
from app.core.errors import AppError
from app.models import Policy, User
from app.services.audit import audit

router = APIRouter(prefix="/partner/leads", tags=["leads"])

MAX_LIMIT = 200


def require_leads_token(request: Request, db: DB, x_leads_token: Annotated[str | None, Header()] = None) -> None:
    expected = get_settings().leads_api_token
    if not expected or not x_leads_token or not hmac.compare_digest(x_leads_token, expected):
        raise AppError("forbidden", "Leads feed access required", 403)
    audit(db, "leads_feed_access", None, ip=client_ip(request), path=request.url.path)
    db.commit()


class LeadPolicy(BaseModel):
    policy_type: str
    insurer: str | None
    plan_name: str | None
    start_date: date | None
    end_date: date | None
    sum_insured: Decimal | None
    premium: Decimal | None
    renewal_status: str
    verified: bool


class Lead(BaseModel):
    app_user_id: uuid.UUID
    status: Literal["active", "withdrawn"]
    changed_at: datetime
    # Only for status == "active"
    full_name: str | None = None
    phone: str | None = None
    email: str | None = None
    city: str | None = None
    state: str | None = None
    contact_consent_at: datetime | None = None
    contact_consent_version: str | None = None
    next_renewal_date: date | None = None
    policies: list[LeadPolicy] = []
    # Only for status == "withdrawn"
    withdrawn_at: datetime | None = None


class LeadPage(BaseModel):
    items: list[Lead]
    next_cursor: str | None
    has_more: bool


def _encode(changed_at: datetime, user_id: uuid.UUID) -> str:
    return base64.urlsafe_b64encode(f"{changed_at.isoformat()}|{user_id}".encode()).decode()


def _decode(cursor: str) -> tuple[datetime, uuid.UUID]:
    try:
        stamp, uid = base64.urlsafe_b64decode(cursor.encode()).decode().split("|")
        return datetime.fromisoformat(stamp), uuid.UUID(uid)
    except Exception as exc:  # noqa: BLE001 - any malformed cursor is the caller's error
        raise AppError("invalid_cursor", "That cursor is not valid", 400) from exc


def _is_active(u: User) -> bool:
    return u.contact_consent_at is not None and u.deletion_requested_at is None


def leads_page(db: Session, cursor: str | None, limit: int) -> LeadPage:
    last_policy_change = (
        select(Policy.user_id, func.max(Policy.updated_at).label("changed")).group_by(Policy.user_id).subquery()
    )
    changed_at = func.greatest(User.updated_at, func.coalesce(last_policy_change.c.changed, User.updated_at))
    q = (
        select(User, changed_at.label("changed_at"))
        .outerjoin(last_policy_change, last_policy_change.c.user_id == User.id)
        # Opted in now, or opted in once and has since withdrawn.
        .where(or_(User.contact_consent_at.is_not(None), User.contact_consent_withdrawn_at.is_not(None)))
        .order_by(changed_at, User.id)
        .limit(limit + 1)
    )
    if cursor:
        after_at, after_id = _decode(cursor)
        q = q.where(or_(changed_at > after_at, and_(changed_at == after_at, User.id > after_id)))
    rows = db.execute(q).all()
    has_more = len(rows) > limit
    rows = rows[:limit]

    active_ids = [u.id for u, _ in rows if _is_active(u)]
    by_user: dict[uuid.UUID, list[Policy]] = {}
    if active_ids:
        for p in db.scalars(
            select(Policy).where(Policy.user_id.in_(active_ids)).order_by(Policy.end_date.asc().nulls_last())
        ):
            by_user.setdefault(p.user_id, []).append(p)

    today = date.today()
    items: list[Lead] = []
    for u, at in rows:
        if _is_active(u):
            policies = by_user.get(u.id, [])
            upcoming = [p.end_date for p in policies if p.end_date and p.end_date >= today]
            items.append(
                Lead(
                    app_user_id=u.id,
                    status="active",
                    changed_at=at,
                    full_name=u.full_name,
                    phone=u.phone,
                    email=u.email,
                    city=u.city,
                    state=u.state,
                    contact_consent_at=u.contact_consent_at,
                    contact_consent_version=u.contact_consent_version,
                    next_renewal_date=min(upcoming) if upcoming else None,
                    policies=[
                        LeadPolicy(
                            policy_type=str(getattr(p.policy_type, "value", p.policy_type)),
                            insurer=p.insurer,
                            plan_name=p.plan_name,
                            start_date=p.start_date,
                            end_date=p.end_date,
                            sum_insured=p.sum_insured,
                            premium=p.premium,
                            renewal_status=p.renewal_status,
                            verified=p.verified,
                        )
                        for p in policies
                    ],
                )
            )
        else:
            items.append(
                Lead(
                    app_user_id=u.id,
                    status="withdrawn",
                    changed_at=at,
                    withdrawn_at=u.contact_consent_withdrawn_at or u.deletion_requested_at,
                )
            )
    next_cursor = _encode(rows[-1][1], rows[-1][0].id) if rows else cursor
    return LeadPage(items=items, next_cursor=next_cursor, has_more=has_more)


@router.get("", response_model=LeadPage, dependencies=[Depends(require_leads_token)])
def list_leads(
    db: DB,
    cursor: str | None = Query(None, max_length=200, description="next_cursor from the previous call"),
    limit: int = Query(100, ge=1, le=MAX_LIMIT),
) -> LeadPage:
    return leads_page(db, cursor, limit)
