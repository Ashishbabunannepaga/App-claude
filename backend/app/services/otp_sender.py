import logging
from abc import ABC, abstractmethod

from app.core.config import get_settings

log = logging.getLogger(__name__)


class OtpSender(ABC):
    @abstractmethod
    def send(self, identifier: str, code: str) -> None: ...


class ConsoleOtpSender(OtpSender):
    """DEV ONLY — prints the OTP to the server log. Refused in production by config."""

    def send(self, identifier: str, code: str) -> None:
        log.warning("DEV OTP for %s: %s", identifier, code)


class Msg91OtpSender(OtpSender):
    """TODO(Week 2): implement with DLT-approved template. Requires MSG91_AUTH_KEY in env."""

    def send(self, identifier: str, code: str) -> None:
        raise NotImplementedError("MSG91 sender not implemented yet")


def get_otp_sender() -> OtpSender:
    if get_settings().otp_sender == "msg91":
        return Msg91OtpSender()
    if get_settings().otp_sender == "twilio":
        raise NotImplementedError("Twilio sender not implemented yet")  # TODO
    return ConsoleOtpSender()
