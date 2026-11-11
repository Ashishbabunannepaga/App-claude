from fastapi import APIRouter, Request

from app.api.deps import DB, client_ip
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.schemas.auth import AuthOut, FirebaseSignIn, OtpRequest, OtpRequestOut, OtpVerify, RefreshRequest, TokenPair
from app.schemas.user import UserOut
from app.services import auth_service, firebase_auth

router = APIRouter(prefix="/auth", tags=["auth"])


def _expires_in() -> int:
    return get_settings().access_token_ttl_minutes * 60


@router.post("/otp/request", response_model=OtpRequestOut)
def request_otp(body: OtpRequest, request: Request, db: DB) -> OtpRequestOut:
    challenge = auth_service.request_otp(db, body.identifier, client_ip(request))
    s = get_settings()
    return OtpRequestOut(
        identifier=challenge.identifier, expires_in=s.otp_ttl_seconds, resend_after=s.otp_resend_cooldown_seconds
    )


@router.post("/otp/verify", response_model=AuthOut)
def verify_otp(body: OtpVerify, request: Request, db: DB) -> AuthOut:
    user, is_new = auth_service.verify_otp(
        db, body.identifier, body.code, body.consent, client_ip(request), contact_consent=body.contact_consent
    )
    access, refresh = auth_service.issue_tokens(db, user)
    return AuthOut(
        access_token=access,
        refresh_token=refresh,
        expires_in=_expires_in(),
        user=UserOut.model_validate(user),
        is_new_user=is_new,
    )


@router.post("/firebase", response_model=AuthOut)
def firebase_sign_in(body: FirebaseSignIn, request: Request, db: DB) -> AuthOut:
    """Sign in with a phone number Firebase has verified by SMS (the app sends Firebase's ID token)."""
    ip = client_ip(request)
    limiter.hit(f"firebase-signin:ip:{ip}", limit=60, window_seconds=3600)
    phone = auth_service.normalise_identifier(firebase_auth.verified_phone(body.id_token))
    user, is_new = auth_service.sign_in(
        db, phone, body.consent, ip, contact_consent=body.contact_consent, method="firebase"
    )
    access, refresh = auth_service.issue_tokens(db, user)
    return AuthOut(
        access_token=access,
        refresh_token=refresh,
        expires_in=_expires_in(),
        user=UserOut.model_validate(user),
        is_new_user=is_new,
    )


@router.post("/refresh", response_model=TokenPair)
def refresh(body: RefreshRequest, db: DB) -> TokenPair:
    _, access, new_refresh = auth_service.rotate_refresh_token(db, body.refresh_token)
    return TokenPair(access_token=access, refresh_token=new_refresh, expires_in=_expires_in())


@router.post("/logout", status_code=204)
def logout(body: RefreshRequest, db: DB) -> None:
    auth_service.revoke(db, body.refresh_token)
