import logging
from abc import ABC, abstractmethod

import httpx

from app.core.config import get_settings
from app.core.errors import AppError

log = logging.getLogger(__name__)


class OtpSender(ABC):
    @abstractmethod
    def send(self, identifier: str, code: str) -> None: ...


class ConsoleOtpSender(OtpSender):
    """DEV ONLY — prints the OTP to the server log. Refused in production by config."""

    def send(self, identifier: str, code: str) -> None:
        log.warning("DEV OTP for %s: %s", identifier, code)


class Msg91OtpSender(OtpSender):
    """SMS via MSG91 Flow API using a DLT-approved template with an `otp` variable.

    Needs MSG91_AUTH_KEY and MSG91_TEMPLATE_ID. Not exercised by automated tests (requires a live account).
    """

    url = "https://control.msg91.com/api/v5/flow"

    def __init__(self, auth_key: str, template_id: str):
        self.auth_key, self.template_id = auth_key, template_id

    def send(self, identifier: str, code: str) -> None:
        if "@" in identifier:
            raise AppError(
                "email_login_unavailable", "Email login is not available yet. Please use your mobile number."
            )
        try:
            resp = httpx.post(
                self.url,
                headers={"authkey": self.auth_key, "content-type": "application/json"},
                json={
                    "template_id": self.template_id,
                    "recipients": [{"mobiles": identifier.lstrip("+"), "otp": code}],
                },
                timeout=10,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            log.error("MSG91 send failed: %s", type(exc).__name__)
            raise AppError("otp_send_failed", "Couldn't send the code. Please try again.", 503) from exc


def get_otp_sender() -> OtpSender:
    s = get_settings()
    if s.otp_sender == "msg91":
        if not (s.msg91_auth_key and s.msg91_template_id):
            raise RuntimeError("MSG91_AUTH_KEY and MSG91_TEMPLATE_ID are required")
        return Msg91OtpSender(s.msg91_auth_key, s.msg91_template_id)
    return ConsoleOtpSender()
