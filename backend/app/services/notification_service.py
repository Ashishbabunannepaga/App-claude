import logging
import uuid
from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import now_utc
from app.models import DeviceToken, Notification, Policy, User
from app.services.push import InvalidToken, PushMessage, get_push_sender

log = logging.getLogger(__name__)


def notify(
    db: Session,
    user_id: uuid.UUID,
    *,
    kind: str,
    title: str,
    body: str,
    dedupe_key: str,
    policy_id: uuid.UUID | None = None,
    deep_link: str | None = None,
    push: bool = True,
) -> Notification | None:
    """Create an in-app notification (once per dedupe_key) and push it to the user's devices.

    Push text must never contain policy numbers, amounts or health details.
    """
    stmt = (
        insert(Notification)
        .values(
            id=uuid.uuid4(),
            user_id=user_id,
            policy_id=policy_id,
            kind=kind,
            title=title,
            body=body,
            deep_link=deep_link,
            dedupe_key=dedupe_key,
        )
        .on_conflict_do_nothing(index_elements=["dedupe_key"])
        .returning(Notification.id)
    )
    new_id = db.execute(stmt).scalar()
    if new_id is None:
        return None  # already sent
    notification = db.get(Notification, new_id)
    if push:
        _push(db, user_id, PushMessage(title, body, deep_link))
        notification.sent_at = now_utc()
    db.commit()
    return notification


def _push(db: Session, user_id: uuid.UUID, message: PushMessage) -> None:
    sender = get_push_sender()
    for device in db.scalars(select(DeviceToken).where(DeviceToken.user_id == user_id)).all():
        try:
            sender.send(device.token, message)
        except InvalidToken:
            db.execute(delete(DeviceToken).where(DeviceToken.id == device.id))
        except Exception:  # one failing device must not block the others
            log.exception("push failed")


def renewal_reminders(db: Session, today: date | None = None) -> int:
    """Daily job: remind users N days before a verified policy expires (N from settings)."""
    today = today or date.today()
    offsets = sorted(set(get_settings().renewal_reminder_days))
    sent = 0
    rows = db.execute(
        select(Policy, User)
        .join(User, User.id == Policy.user_id)
        .where(
            Policy.verified.is_(True),
            Policy.renewal_status == "pending",
            Policy.end_date.is_not(None),
            User.notify_renewals.is_(True),
            User.deletion_requested_at.is_(None),
        )
    ).all()
    for policy, user in rows:
        days = (policy.end_date - today).days
        # Bucket = smallest reminder offset >= days left. Each bucket fires once (dedupe key), so a
        # missed daily run, or a policy added 20 days before expiry, still gets one timely reminder.
        buckets = [o for o in offsets if o >= days]
        if days < 0 or not buckets:
            continue
        bucket = buckets[0]
        name = policy.insurer or "Your"
        kind_label = {"health": "health", "life": "life", "motor": "motor"}.get(policy.policy_type, "insurance")
        when = "tomorrow" if days == 1 else f"in {days} days"
        if notify(
            db,
            user.id,
            kind="renewal",
            title=f"{kind_label.title()} policy renewal due {when}",
            body=f"{name} {kind_label} policy expires {when}. Renew on time to stay covered.",
            dedupe_key=f"renewal:{policy.id}:{policy.end_date.isoformat()}:{bucket}",
            policy_id=policy.id,
            deep_link=f"/policy/{policy.id}",
        ):
            sent += 1
    return sent
