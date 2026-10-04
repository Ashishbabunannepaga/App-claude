"""Read-mostly operations API for authorised staff. PII is masked.

Protected by a shared admin token (ADMIN_API_TOKEN). TODO(before scaling the team): put behind
SSO + MFA (e.g. Cloudflare Access / Google IAP) and per-staff identities.
"""

import hmac
import uuid
from datetime import timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.deps import DB, client_ip
from app.core.config import get_settings
from app.core.errors import AppError, NotFound
from app.core.security import now_utc
from app.models import Document, Notification, Policy, QaMessage, SupportRequest, User
from app.services.audit import audit

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(request: Request, db: DB, x_admin_token: Annotated[str | None, Header()] = None) -> None:
    expected = get_settings().admin_api_token
    if not expected or not x_admin_token or not hmac.compare_digest(x_admin_token, expected):
        raise AppError("forbidden", "Admin access required", 403)
    audit(db, "admin_access", None, ip=client_ip(request), path=request.url.path)
    db.commit()


Admin = Depends(require_admin)


def mask_phone(phone: str | None) -> str | None:
    return f"{phone[:3]}******{phone[-2:]}" if phone and len(phone) > 6 else phone


@router.get("/stats", dependencies=[Admin])
def stats(db: DB) -> dict:
    week_ago = now_utc() - timedelta(days=7)
    count = lambda q: db.scalar(q) or 0  # noqa: E731
    docs_week = count(select(func.count()).select_from(Document).where(Document.created_at >= week_ago))
    failed_week = count(
        select(func.count()).select_from(Document).where(Document.created_at >= week_ago, Document.status == "failed")
    )
    return {
        "users": count(select(func.count()).select_from(User)),
        "users_pending_deletion": count(select(func.count()).where(User.deletion_requested_at.is_not(None))),
        "policies_by_type": dict(
            db.execute(select(Policy.policy_type, func.count()).group_by(Policy.policy_type)).all()
        ),
        "policies_verified": count(select(func.count()).where(Policy.verified.is_(True))),
        "documents_by_status": dict(db.execute(select(Document.status, func.count()).group_by(Document.status)).all()),
        "documents_last_7_days": docs_week,
        "processing_failure_rate_7d": round(failed_week / docs_week, 3) if docs_week else 0,
        "questions_last_7_days": count(select(func.count()).where(QaMessage.created_at >= week_ago)),
        "unanswerable_rate_7d": _rate(db, week_ago),
        "renewal_reminders_last_7_days": count(
            select(func.count()).where(Notification.kind == "renewal", Notification.created_at >= week_ago)
        ),
        "open_support_requests": count(select(func.count()).where(SupportRequest.status == "open")),
    }


def _rate(db, since) -> float:
    total = db.scalar(select(func.count()).where(QaMessage.created_at >= since)) or 0
    no = db.scalar(select(func.count()).where(QaMessage.created_at >= since, QaMessage.answerable.is_(False))) or 0
    return round(no / total, 3) if total else 0


@router.get("/documents/failed", dependencies=[Admin])
def failed_documents(db: DB) -> list[dict]:
    rows = db.scalars(
        select(Document).where(Document.status == "failed").order_by(Document.created_at.desc()).limit(100)
    )
    return [
        {
            "id": str(d.id),
            "user_id": str(d.user_id),
            "error_code": d.error_code,
            "content_type": d.content_type,
            "size_bytes": d.size_bytes,
            "page_count": d.page_count,
            "created_at": d.created_at,
        }
        for d in rows
    ]


@router.get("/support", dependencies=[Admin])
def support_requests(db: DB, status: Literal["open", "closed"] = "open") -> list[dict]:
    rows = db.execute(
        select(SupportRequest, User.phone)
        .outerjoin(User, User.id == SupportRequest.user_id)
        .where(SupportRequest.status == status)
        .order_by(SupportRequest.created_at.desc())
        .limit(200)
    ).all()
    return [
        {
            "id": str(r.id),
            "category": r.category,
            "message": r.message,
            "status": r.status,
            "user": mask_phone(phone),
            "created_at": r.created_at,
        }
        for r, phone in rows
    ]


class SupportStatus(BaseModel):
    status: Literal["open", "closed"]


@router.patch("/support/{request_id}", dependencies=[Admin])
def update_support(request_id: uuid.UUID, body: SupportStatus, db: DB) -> dict:
    req = db.get(SupportRequest, request_id)
    if req is None:
        raise NotFound("Support request")
    req.status = body.status
    db.commit()
    return {"id": str(req.id), "status": req.status}
