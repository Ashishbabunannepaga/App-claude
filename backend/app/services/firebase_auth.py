"""Sign-in with a phone number verified by Firebase Authentication.

The app asks Firebase to send the SMS and check the code (Google is the DLT-registered sender, so no
SMS registration of our own is needed). Firebase then gives the app a signed ID token. We check that
token here: Google's signature, our project as audience and issuer, not expired, and a phone number
in it. Only then do we treat the number as verified and sign the user in with our own tokens.
"""

import time
from collections.abc import Callable
from typing import Any

from app.core.config import get_settings
from app.core.errors import AppError

# Tokens older than this (since the SMS check) are refused even if not yet expired.
MAX_AUTH_AGE_SECONDS = 10 * 60
CLOCK_SKEW_SECONDS = 60

_request = None


def _google_verify(token: str, project_id: str) -> dict[str, Any]:
    """Signature, audience and expiry, against Google's published Firebase keys (one fetch per sign-in)."""
    global _request
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token

    if _request is None:
        _request = google_requests.Request()
    return id_token.verify_firebase_token(
        token, _request, audience=project_id, clock_skew_in_seconds=CLOCK_SKEW_SECONDS
    )


# Swapped in tests; production always uses Google's keys.
verify_with_google: Callable[[str, str], dict[str, Any]] = _google_verify


def verified_phone(id_token: str) -> str:
    """The E.164 phone number from a valid Firebase ID token, or AppError."""
    project_id = get_settings().firebase_project_id
    if not project_id:
        raise AppError("firebase_disabled", "Phone sign-in with Firebase is not set up on this server", 503)
    invalid = AppError("firebase_token_invalid", "We couldn't confirm your phone number. Please try again.", 401)
    try:
        claims = verify_with_google(id_token, project_id)
    except AppError:
        raise
    except Exception as exc:  # noqa: BLE001 - any verification failure is the same answer to the app
        raise invalid from exc
    if not claims:
        raise invalid
    now = time.time()
    if (
        claims.get("aud") != project_id
        or claims.get("iss") != f"https://securetoken.google.com/{project_id}"
        or not claims.get("sub")
        or float(claims.get("auth_time", 0)) > now + CLOCK_SKEW_SECONDS
        or now - float(claims.get("auth_time", 0)) > MAX_AUTH_AGE_SECONDS
    ):
        raise invalid
    phone = claims.get("phone_number")
    if not phone or (claims.get("firebase") or {}).get("sign_in_provider") != "phone":
        raise AppError("firebase_no_phone", "This sign-in did not verify a phone number", 401)
    return str(phone)
