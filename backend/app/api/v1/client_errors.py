"""Crash reports from the mobile app, forwarded to error tracking.

The app sends Dart errors here instead of bundling a native crash SDK (the native SDK needed a newer Android
minimum, CMake and the Android 35 platform, and broke the Android build). No login is required, since crashes
can happen before sign-in, so the endpoint is rate limited per IP and every text field is size-capped and
scrubbed of numbers and email addresses (policy numbers, phone numbers) before it is logged or forwarded.
"""

import logging
import re

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.api.deps import client_ip
from app.core.rate_limit import limiter

router = APIRouter(tags=["ops"])
log = logging.getLogger("client_errors")

_DIGITS = re.compile(r"\d[\d\s/\-]{4,}\d")  # policy, phone and account numbers
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


def scrub(text: str) -> str:
    return _EMAIL.sub("[email]", _DIGITS.sub("[number]", text))


class ClientErrorIn(BaseModel):
    error_type: str = Field(max_length=120)
    message: str = Field(default="", max_length=1000)
    stack: str = Field(default="", max_length=12000)
    app_version: str = Field(default="", max_length=40)
    platform: str = Field(default="", max_length=20)
    fatal: bool = False


@router.post("/client-errors", status_code=202)
def report_client_error(body: ClientErrorIn, request: Request) -> dict:
    limiter.hit(f"client-errors:{client_ip(request) or 'unknown'}", limit=30, window_seconds=3600)
    message = scrub(body.message)[:300]
    stack = scrub(body.stack)
    log.warning(
        "app error %s (%s %s, fatal=%s): %s", body.error_type, body.platform, body.app_version, body.fatal, message
    )
    try:
        import sentry_sdk

        if sentry_sdk.get_client().is_active():
            with sentry_sdk.new_scope() as scope:
                scope.set_tag("component", "mobile")
                scope.set_tag("platform", body.platform or "unknown")
                scope.set_tag("app_version", body.app_version or "unknown")
                scope.set_context("app_error", {"type": body.error_type, "fatal": body.fatal, "stack": stack[:8000]})
                sentry_sdk.capture_message(
                    f"[app] {body.error_type}: {message}", level="fatal" if body.fatal else "error"
                )
    except ImportError:  # sentry-sdk is optional in local setups
        pass
    return {"status": "accepted"}
