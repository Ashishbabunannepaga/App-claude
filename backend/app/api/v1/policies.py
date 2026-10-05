import re
import uuid
from typing import Literal

from fastapi import APIRouter, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.gateway import get_ai_gateway
from app.ai.providers.base import AIProviderError
from app.api.deps import DB, CurrentUser, client_ip
from app.core.errors import AppError
from app.core.rate_limit import limiter
from app.models import FamilyMember, Policy, QaMessage
from app.schemas.policy import (
    AnswerOut,
    AskRequest,
    HealthCheckOut,
    PolicyCreate,
    PolicyOut,
    PolicyUpdate,
    PortfolioSummary,
    RenewalUpdate,
    SummaryOut,
)
from app.services import qa_service
from app.services.audit import audit
from app.services.health_check import health_check
from app.services.policy_service import get_owned_policy, portfolio_summary, structured_view, to_out
from app.storage import get_storage

router = APIRouter(tags=["policies"])
_DEVANAGARI = re.compile("[\u0900-\u097f]")


def _apply(db: Session, policy: Policy, body: PolicyUpdate | PolicyCreate) -> None:
    changes = body.model_dump(exclude_unset=True)
    confidence = dict(policy.field_confidence or {})
    for field, value in changes.items():
        if field == "details":
            policy.details = {**(policy.details or {}), **(value or {})}
            continue
        if field == "member_ids":
            ids = set(value or [])
            members = db.scalars(
                select(FamilyMember).where(FamilyMember.id.in_(ids), FamilyMember.user_id == policy.user_id)
            ).all()
            if len(members) != len(ids):
                raise AppError("invalid_member", "Unknown family member", 422)
            policy.members = list(members)
            continue
        setattr(policy, field, value)
        confidence[field] = 1.0  # user-provided or user-corrected
    policy.field_confidence = confidence
    if policy.start_date and policy.end_date and policy.start_date >= policy.end_date:
        raise AppError("invalid_dates", "Start date must be before end date", 422)


def _answer_out(m: QaMessage) -> AnswerOut:
    return AnswerOut(
        id=m.id,
        question=m.question,
        answer=m.answer,
        answerable=m.answerable,
        confidence=m.confidence,
        citations=m.citations,
        disclaimer=qa_service.disclaimer("hi" if _DEVANAGARI.search(m.answer) else "en"),
        provider=m.provider,
        related_clauses=m.related_clauses or [],
        created_at=m.created_at,
    )


@router.get("/policies", response_model=list[PolicyOut])
def list_policies(
    user: CurrentUser, db: DB, type: Literal["health", "life", "motor", "other"] | None = Query(None)
) -> list[PolicyOut]:
    q = select(Policy).where(Policy.user_id == user.id)
    if type:
        q = q.where(Policy.policy_type == type)
    return [to_out(p) for p in db.scalars(q.order_by(Policy.end_date.asc().nulls_last(), Policy.created_at))]


@router.post("/policies", response_model=PolicyOut, status_code=201)
def create_manual(body: PolicyCreate, user: CurrentUser, db: DB) -> PolicyOut:
    policy = Policy(user_id=user.id, source="manual", verified=True, field_confidence={}, details={}, members=[])
    _apply(db, policy, body)
    db.add(policy)
    db.commit()
    return to_out(policy)


@router.get("/policies/{policy_id}", response_model=PolicyOut)
def get_policy(policy_id: uuid.UUID, user: CurrentUser, db: DB) -> PolicyOut:
    return to_out(get_owned_policy(db, user.id, policy_id))


@router.patch("/policies/{policy_id}", response_model=PolicyOut)
def update_policy(policy_id: uuid.UUID, body: PolicyUpdate, user: CurrentUser, db: DB) -> PolicyOut:
    policy = get_owned_policy(db, user.id, policy_id)
    _apply(db, policy, body)
    policy.summary = None
    db.commit()
    return to_out(policy)


@router.post("/policies/{policy_id}/confirm", response_model=PolicyOut)
def confirm_policy(policy_id: uuid.UUID, body: PolicyUpdate, user: CurrentUser, db: DB) -> PolicyOut:
    """User reviewed (and optionally corrected) the extracted fields."""
    policy = get_owned_policy(db, user.id, policy_id)
    _apply(db, policy, body)
    if not policy.insurer:
        raise AppError("insurer_required", "Please enter the insurer name", 422)
    policy.verified = True
    policy.summary = None
    db.commit()
    return to_out(policy)


@router.delete("/policies/{policy_id}", status_code=204)
def delete_policy(policy_id: uuid.UUID, user: CurrentUser, db: DB, request: Request) -> None:
    policy = get_owned_policy(db, user.id, policy_id)
    if policy.document is not None:
        get_storage().delete(policy.document.storage_key)
        db.delete(policy.document)
    db.delete(policy)
    audit(db, "policy_deleted", user.id, "policy", policy_id, ip=client_ip(request))
    db.commit()


@router.get("/policies/{policy_id}/summary", response_model=SummaryOut)
def get_summary(policy_id: uuid.UUID, user: CurrentUser, db: DB) -> SummaryOut:
    """Generated once per language and cached on the policy (invalidated when details change)."""
    policy = get_owned_policy(db, user.id, policy_id)
    language = user.preferred_language or "en"
    cache = dict(policy.summary or {})
    if "headline" in cache:  # summaries cached before per-language support
        cache = {"en": cache}
    if language not in cache:
        limiter.hit(f"summary:{user.id}", limit=30, window_seconds=3600)
        try:
            raw = get_ai_gateway().summarise(
                structured_view(policy), qa_service.summary_excerpts(db, policy.id), language
            )
        except AIProviderError as exc:
            raise AppError("ai_unavailable", "Summary is unavailable right now. Please try again.", 503) from exc
        cache[language] = {
            "provider": get_ai_gateway().provider_name,
            "headline": str(raw.get("headline") or ""),
            "key_points": [str(x) for x in raw.get("key_points") or []][:6],
            "watch_outs": [str(x) for x in raw.get("watch_outs") or []][:4],
        }
        policy.summary = cache
        db.commit()
    return SummaryOut(**cache[language], disclaimer=qa_service.disclaimer(language))


@router.get("/policies/{policy_id}/health", response_model=HealthCheckOut)
def get_health(policy_id: uuid.UUID, user: CurrentUser, db: DB) -> dict:
    return health_check(get_owned_policy(db, user.id, policy_id))


@router.put("/policies/{policy_id}/renewal", response_model=PolicyOut)
def set_renewal(policy_id: uuid.UUID, body: RenewalUpdate, user: CurrentUser, db: DB) -> PolicyOut:
    """Mark as renewed / not renewing (stops reminders), or back to pending."""
    policy = get_owned_policy(db, user.id, policy_id)
    policy.renewal_status = body.renewal_status
    db.commit()
    return to_out(policy)


@router.post("/policies/{policy_id}/ask", response_model=AnswerOut)
def ask(policy_id: uuid.UUID, body: AskRequest, user: CurrentUser, db: DB) -> AnswerOut:
    policy = get_owned_policy(db, user.id, policy_id)
    limiter.hit(f"ask:{user.id}", limit=60, window_seconds=3600)
    return _answer_out(qa_service.ask(db, policy, user.id, body.question.strip(), user.preferred_language or "en"))


@router.get("/policies/{policy_id}/messages", response_model=list[AnswerOut])
def messages(policy_id: uuid.UUID, user: CurrentUser, db: DB) -> list[AnswerOut]:
    policy = get_owned_policy(db, user.id, policy_id)
    rows = db.scalars(
        select(QaMessage).where(QaMessage.policy_id == policy.id).order_by(QaMessage.created_at).limit(200)
    )
    return [_answer_out(m) for m in rows]


@router.get("/portfolio/summary", response_model=PortfolioSummary)
def summary(user: CurrentUser, db: DB) -> PortfolioSummary:
    return portfolio_summary(db, user.id)
