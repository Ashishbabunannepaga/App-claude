import uuid

from sqlalchemy.orm import Session

from app.models import AuditLog


def audit(
    db: Session,
    action: str,
    user_id: uuid.UUID | None,
    entity: str | None = None,
    entity_id: uuid.UUID | None = None,
    ip: str | None = None,
    **meta: object,
) -> None:
    """Record a security-relevant event. Never put document text, OTPs or tokens in `meta`."""
    db.add(AuditLog(user_id=user_id, action=action, entity=entity, entity_id=entity_id, ip=ip, meta=meta))
