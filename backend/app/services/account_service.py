from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import now_utc
from app.models import User
from app.services.audit import audit
from app.storage import get_storage

DELETION_GRACE_DAYS = 7


def purge_deleted_accounts(db: Session) -> int:
    """Hard-delete users whose deletion grace period has passed: files, then rows (FK cascade)."""
    cutoff = now_utc() - timedelta(days=DELETION_GRACE_DAYS)
    users = db.scalars(
        select(User).where(User.deletion_requested_at.is_not(None), User.deletion_requested_at < cutoff)
    ).all()
    for user in users:
        get_storage().delete_prefix(f"users/{user.id}/")
        audit(db, "account_purged", None, "user", user.id)
        db.delete(user)
        db.commit()
    return len(users)
