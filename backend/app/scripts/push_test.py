"""Sends one test notification to a user's registered phones: `python -m app.scripts.push_test +919876543210`.

Use it after setting PUSH_SENDER=fcm, FCM_PROJECT_ID and FCM_SERVICE_ACCOUNT_FILE in .env. The phone must have
signed in to the app and allowed notifications (that registers its token). Prints the result per device, never
the key or the full token.
"""

import sys

from sqlalchemy import select

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.models import DeviceToken, User
from app.services.push import InvalidToken, PushMessage, get_push_sender


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__)
        return 2
    identifier = argv[0].strip()
    s = get_settings()
    print(f"Push sender: {s.push_sender}" + ("" if s.push_sender == "fcm" else "  (log only: set PUSH_SENDER=fcm)"))
    with SessionLocal() as db:
        user = db.scalar(select(User).where((User.phone == identifier) | (User.email == identifier)))
        if user is None:
            print(f"No user with {identifier}. Use the number as stored, e.g. +919876543210.")
            return 1
        tokens = db.scalars(select(DeviceToken).where(DeviceToken.user_id == user.id)).all()
        if not tokens:
            print("That user has no registered device. Open the app on the phone, sign in and allow notifications.")
            return 1
        sender = get_push_sender()
        message = PushMessage("CapitUp test notification", "If you can read this, push works.", "/notifications")
        failures = 0
        for t in tokens:
            label = f"{t.platform} device {t.token[:8]}…"
            try:
                sender.send(t.token, message)
                print(f"[OK]   {label}")
            except InvalidToken:
                failures += 1
                print(f"[GONE] {label}: token no longer valid (app reinstalled?). Sign in again on that phone.")
            except Exception as exc:  # noqa: BLE001 - report every failure, keep going
                failures += 1
                print(f"[FAIL] {label}: {type(exc).__name__}: {str(exc)[:200]}")
        return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
