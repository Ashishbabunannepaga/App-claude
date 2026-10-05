from fastapi import APIRouter, Request

from app.api.deps import DB, CurrentUser, client_ip
from app.core.security import now_utc
from app.schemas.user import UserOut, UserUpdate
from app.services.audit import audit
from app.services.auth_service import revoke_all

router = APIRouter(prefix="/me", tags=["profile"])


@router.get("", response_model=UserOut)
def get_me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)


@router.patch("", response_model=UserOut)
def update_me(body: UserUpdate, user: CurrentUser, db: DB) -> UserOut:
    if body.preferred_language is None and "preferred_language" in body.model_fields_set:
        body.preferred_language = "en"
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    return UserOut.model_validate(user)


@router.delete("", status_code=202)
def delete_me(user: CurrentUser, request: Request, db: DB) -> dict:
    """Disable now; data is purged by `purge_deleted_accounts` after the grace period.

    TODO(Week 8): require OTP re-confirmation from the app before calling this.
    """
    user.deletion_requested_at = now_utc()
    revoke_all(db, user.id)
    audit(db, "account_deletion_requested", user.id, ip=client_ip(request))
    db.commit()
    return {"status": "scheduled", "grace_period_days": 7}


@router.get("/export")
def export_my_data(user: CurrentUser, db: DB, request: Request) -> dict:
    """DPDP right of access: everything we hold about the user, except document files
    (downloadable individually via signed URLs)."""
    from sqlalchemy import select

    from app.models import FamilyMember, Notification, Policy, QaMessage
    from app.services.policy_service import to_out

    audit(db, "data_exported", user.id, ip=client_ip(request))
    db.commit()
    policies = db.scalars(select(Policy).where(Policy.user_id == user.id)).all()
    return {
        "profile": UserOut.model_validate(user).model_dump(mode="json"),
        "family": [
            {"relation": m.relation, "full_name": m.full_name, "date_of_birth": m.date_of_birth}
            for m in db.scalars(select(FamilyMember).where(FamilyMember.user_id == user.id))
        ],
        "policies": [to_out(p).model_dump(mode="json") for p in policies],
        "questions": [
            {"policy_id": str(q.policy_id), "question": q.question, "answer": q.answer, "asked_at": q.created_at}
            for q in db.scalars(select(QaMessage).where(QaMessage.user_id == user.id))
        ],
        "notifications": [
            {"title": n.title, "body": n.body, "created_at": n.created_at}
            for n in db.scalars(select(Notification).where(Notification.user_id == user.id))
        ],
    }
