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
