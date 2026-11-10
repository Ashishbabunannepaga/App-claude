"""The optional "CapitUp may contact me" consent.

Kept separate from the privacy/terms consent: using a user's number and renewal dates for
sales follow-up is a different purpose, so under the DPDP Act it needs its own, freely given,
withdrawable consent. Every change is audited.
"""

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import now_utc
from app.models import User
from app.services.audit import audit


def set_contact_consent(db: Session, user: User, granted: bool, *, ip: str | None = None, source: str = "app") -> bool:
    """Grant or withdraw. Returns True if anything changed. The caller commits."""
    if granted and user.contact_consent_at is None:
        user.contact_consent_at = now_utc()
        user.contact_consent_version = get_settings().contact_consent_version
        user.contact_consent_withdrawn_at = None
        audit(db, "contact_consent_granted", user.id, ip=ip, source=source, version=user.contact_consent_version)
        return True
    if not granted and user.contact_consent_at is not None:
        user.contact_consent_at = None
        user.contact_consent_withdrawn_at = now_utc()
        audit(db, "contact_consent_withdrawn", user.id, ip=ip, source=source)
        return True
    return False
