import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache

import httpx

from app.core.config import get_settings

log = logging.getLogger(__name__)


@dataclass
class PushMessage:
    title: str
    body: str
    deep_link: str | None = None


class InvalidToken(Exception):
    """The device token is no longer valid and should be deleted."""


class PushSender(ABC):
    @abstractmethod
    def send(self, token: str, message: PushMessage) -> None: ...


class LogPushSender(PushSender):
    """DEV ONLY — logs pushes instead of sending them."""

    def send(self, token: str, message: PushMessage) -> None:
        log.info("DEV PUSH to %s…: %s", token[:8], message.title)


class FcmPushSender(PushSender):
    """Firebase Cloud Messaging HTTP v1 (Android directly, iOS via APNs key uploaded to Firebase)."""

    scope = "https://www.googleapis.com/auth/firebase.messaging"

    def __init__(self, project_id: str, service_account_json: str):
        from google.oauth2 import service_account

        self.url = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
        self._creds = service_account.Credentials.from_service_account_info(
            json.loads(service_account_json), scopes=[self.scope]
        )
        self._token_expiry = 0.0

    def _access_token(self) -> str:
        if not self._creds.valid or time.time() > self._token_expiry:
            from google.auth.transport.requests import Request

            self._creds.refresh(Request())
            self._token_expiry = time.time() + 50 * 60
        return self._creds.token

    def send(self, token: str, message: PushMessage) -> None:
        payload = {
            "message": {
                "token": token,
                "notification": {"title": message.title, "body": message.body},
                "data": {"deep_link": message.deep_link or ""},
                "android": {"priority": "normal"},
                "apns": {"payload": {"aps": {"sound": "default"}}},
            }
        }
        resp = httpx.post(
            self.url, json=payload, headers={"Authorization": f"Bearer {self._access_token()}"}, timeout=10
        )
        # 404 UNREGISTERED: app uninstalled / token rotated; 400 INVALID_ARGUMENT: malformed token.
        if resp.status_code == 404 or (resp.status_code == 400 and "registration token" in resp.text.lower()):
            raise InvalidToken()
        resp.raise_for_status()


@lru_cache
def get_push_sender() -> PushSender:
    s = get_settings()
    if s.push_sender == "fcm":
        if not (s.fcm_project_id and s.fcm_service_account_json):
            raise RuntimeError("FCM_PROJECT_ID and FCM_SERVICE_ACCOUNT_JSON are required")
        return FcmPushSender(s.fcm_project_id, s.fcm_service_account_json)
    return LogPushSender()
