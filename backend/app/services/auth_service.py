import hmac
import re
from datetime import timedelta

from email_validator import EmailNotValidError, validate_email
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError, Unauthorized
from app.core.rate_limit import limiter
from app.core.security import (
    create_access_token,
    generate_otp,
    hash_otp,
    hash_token,
    new_refresh_token,
    now_utc,
)
from app.models import OtpChallenge, RefreshToken, User
from app.services.audit import audit
from app.services.otp_sender import get_otp_sender

_E164 = re.compile(r"^\+[1-9]\d{7,14}$")


def normalise_identifier(raw: str) -> str:
    raw = raw.strip()
    if "@" in raw:
        try:
            return validate_email(raw, check_deliverability=False).normalized.lower()
        except EmailNotValidError as exc:
            raise AppError("invalid_identifier", "Enter a valid email address") from exc
    digits = re.sub(r"[\s\-()]", "", raw)
    if re.fullmatch(r"[6-9]\d{9}", digits):  # Indian mobile without country code
        digits = "+91" + digits
    elif re.fullmatch(r"91[6-9]\d{9}", digits):
        digits = "+" + digits
    if not _E164.match(digits):
        raise AppError("invalid_identifier", "Enter a valid mobile number")
    return digits


def _is_review_login(identifier: str) -> bool:
    s = get_settings()
    return bool(s.review_login_identifier and s.review_login_code and identifier == s.review_login_identifier)


def request_otp(db: Session, raw_identifier: str, ip: str | None) -> OtpChallenge:
    s = get_settings()
    identifier = normalise_identifier(raw_identifier)
    limiter.hit(f"otp:ip:{ip}", limit=20, window_seconds=3600)
    limiter.hit(f"otp:id:{identifier}", limit=s.otp_max_requests_per_hour, window_seconds=3600)

    last = db.scalar(
        select(OtpChallenge).where(OtpChallenge.identifier == identifier).order_by(OtpChallenge.created_at.desc())
    )
    if last and (now_utc() - last.created_at).total_seconds() < s.otp_resend_cooldown_seconds:
        raise AppError("otp_cooldown", "Please wait before requesting another code", 429)

    code = s.review_login_code if _is_review_login(identifier) else generate_otp()
    challenge = OtpChallenge(
        identifier=identifier,
        code_hash=hash_otp(identifier, code),
        expires_at=now_utc() + timedelta(seconds=s.otp_ttl_seconds),
    )
    db.add(challenge)
    db.commit()
    if not _is_review_login(identifier):
        get_otp_sender().send(identifier, code)
    return challenge


def verify_otp(db: Session, raw_identifier: str, code: str, consent: bool, ip: str | None) -> tuple[User, bool]:
    s = get_settings()
    identifier = normalise_identifier(raw_identifier)
    limiter.hit(f"otp-verify:ip:{ip}", limit=60, window_seconds=3600)
    challenge = db.scalar(
        select(OtpChallenge)
        .where(OtpChallenge.identifier == identifier, OtpChallenge.consumed_at.is_(None))
        .order_by(OtpChallenge.created_at.desc())
        .with_for_update()
    )
    invalid = AppError("otp_invalid", "Invalid or expired code", 400)
    if challenge is None or challenge.expires_at < now_utc() or challenge.attempts >= s.otp_max_attempts:
        raise invalid
    challenge.attempts += 1
    if not hmac.compare_digest(challenge.code_hash, hash_otp(identifier, code)):
        db.commit()
        raise invalid
    challenge.consumed_at = now_utc()

    field = User.email if "@" in identifier else User.phone
    user = db.scalar(select(User).where(field == identifier))
    is_new = user is None
    if is_new:
        if not consent:
            db.rollback()
            raise AppError("consent_required", "Please accept the privacy notice and terms to continue")
        user = User(consent_at=now_utc(), consent_version=s.privacy_policy_version)
        if "@" in identifier:
            user.email = identifier
        else:
            user.phone = identifier
        db.add(user)
        db.flush()
    elif user.deletion_requested_at is not None:
        user.deletion_requested_at = None  # logging in during the grace period cancels deletion
        audit(db, "account_deletion_cancelled", user.id, ip=ip)
    audit(db, "login", user.id, ip=ip, new_user=is_new)
    db.commit()
    return user, is_new


def issue_tokens(db: Session, user: User) -> tuple[str, str]:
    refresh = new_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh),
            expires_at=now_utc() + timedelta(days=get_settings().refresh_token_ttl_days),
        )
    )
    db.commit()
    return create_access_token(user.id), refresh


def rotate_refresh_token(db: Session, refresh: str) -> tuple[User, str, str]:
    token = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh)).with_for_update())
    if token is None:
        raise Unauthorized("Invalid session")
    if token.revoked_at is not None:
        # Reuse of a rotated token: assume theft, revoke every session of this user.
        revoke_all(db, token.user_id)
        audit(db, "refresh_token_reuse", token.user_id)
        db.commit()
        raise Unauthorized("Session expired. Please log in again.")
    if token.expires_at < now_utc():
        raise Unauthorized("Session expired. Please log in again.")
    token.revoked_at = now_utc()
    user = db.get(User, token.user_id)
    access, new_refresh = issue_tokens(db, user)
    return user, access, new_refresh


def revoke(db: Session, refresh: str) -> None:
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.token_hash == hash_token(refresh), RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now_utc())
    )
    db.commit()


def revoke_all(db: Session, user_id) -> None:
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now_utc())
    )
