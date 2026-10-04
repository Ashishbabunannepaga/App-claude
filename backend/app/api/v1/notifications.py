import uuid

from fastapi import APIRouter
from sqlalchemy import func, select, update

from app.api.deps import DB, CurrentUser
from app.core.security import now_utc
from app.models import DeviceToken, Notification
from app.schemas.account import DeviceIn, NotificationOut

router = APIRouter(tags=["notifications"])


@router.post("/me/devices", status_code=204)
def register_device(body: DeviceIn, user: CurrentUser, db: DB) -> None:
    """Idempotent. A token moving to another account (shared phone) is re-assigned."""
    device = db.scalar(select(DeviceToken).where(DeviceToken.token == body.token))
    if device is None:
        db.add(DeviceToken(user_id=user.id, token=body.token, platform=body.platform))
    else:
        device.user_id, device.platform, device.last_seen_at = user.id, body.platform, now_utc()
    db.commit()


@router.delete("/me/devices/{token}", status_code=204)
def unregister_device(token: str, user: CurrentUser, db: DB) -> None:
    device = db.scalar(select(DeviceToken).where(DeviceToken.token == token, DeviceToken.user_id == user.id))
    if device:
        db.delete(device)
        db.commit()


@router.get("/notifications", response_model=list[NotificationOut])
def list_notifications(user: CurrentUser, db: DB) -> list[Notification]:
    return list(
        db.scalars(
            select(Notification)
            .where(Notification.user_id == user.id)
            .order_by(Notification.created_at.desc())
            .limit(100)
        )
    )


@router.get("/notifications/unread-count")
def unread_count(user: CurrentUser, db: DB) -> dict:
    count = db.scalar(select(func.count()).where(Notification.user_id == user.id, Notification.read_at.is_(None)))
    return {"count": count}


@router.post("/notifications/{notification_id}/read", status_code=204)
def mark_read(notification_id: uuid.UUID, user: CurrentUser, db: DB) -> None:
    db.execute(
        update(Notification)
        .where(Notification.id == notification_id, Notification.user_id == user.id, Notification.read_at.is_(None))
        .values(read_at=now_utc())
    )
    db.commit()


@router.post("/notifications/read-all", status_code=204)
def mark_all_read(user: CurrentUser, db: DB) -> None:
    db.execute(
        update(Notification)
        .where(Notification.user_id == user.id, Notification.read_at.is_(None))
        .values(read_at=now_utc())
    )
    db.commit()
