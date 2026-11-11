import time

import pytest

from app.core.config import get_settings
from app.services import firebase_auth

PROJECT = "capitup-683ca"


def _claims(**over):
    now = time.time()
    claims = {
        "aud": PROJECT,
        "iss": f"https://securetoken.google.com/{PROJECT}",
        "sub": "firebase-uid-1",
        "auth_time": now - 5,
        "exp": now + 3600,
        "phone_number": "+919876500111",
        "firebase": {"sign_in_provider": "phone"},
    }
    claims.update(over)
    return claims


@pytest.fixture
def firebase(monkeypatch):
    """Firebase sign-in on, with Google's signature check replaced by the claims each test sets."""
    monkeypatch.setattr(get_settings(), "firebase_project_id", PROJECT)
    state = {"claims": _claims(), "error": None, "seen": []}

    def fake_verify(token, project_id):
        state["seen"].append((token, project_id))
        if state["error"]:
            raise state["error"]
        return state["claims"]

    monkeypatch.setattr(firebase_auth, "verify_with_google", fake_verify)
    return state


def _sign_in(client, **body):
    return client.post("/api/v1/auth/firebase", json={"id_token": "x" * 40, "consent": True, **body})


def test_new_phone_creates_a_profile_and_signs_in(client, firebase):
    r = _sign_in(client, contact_consent=True)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["is_new_user"] is True
    assert body["user"]["phone"] == "+919876500111"
    assert body["user"]["contact_consent"] is True
    assert firebase["seen"] == [("x" * 40, PROJECT)]
    me = client.get("/api/v1/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200 and me.json()["phone"] == "+919876500111"


def test_returning_phone_gets_the_same_profile_as_otp_login(client, login, firebase):
    first = login("9876500111")["user"]  # signed up earlier with our own OTP
    r = _sign_in(client, consent=False)  # consent is only needed for new users
    assert r.status_code == 200 and r.json()["user"]["id"] == first["id"] and r.json()["is_new_user"] is False


def test_new_user_must_accept_terms(client, firebase):
    r = _sign_in(client, consent=False)
    assert r.status_code == 400 and r.json()["error"]["code"] == "consent_required"


@pytest.mark.parametrize(
    "bad",
    [
        {"aud": "someone-elses-project"},
        {"iss": "https://securetoken.google.com/someone-elses-project"},
        {"sub": ""},
        {"auth_time": time.time() - 3600},  # SMS checked an hour ago: too old to sign in with
    ],
)
def test_tokens_for_other_projects_or_stale_ones_are_refused(client, firebase, bad):
    firebase["claims"] = _claims(**bad)
    r = _sign_in(client)
    assert r.status_code == 401 and r.json()["error"]["code"] == "firebase_token_invalid"


def test_a_bad_signature_is_refused(client, firebase):
    firebase["error"] = ValueError("Token signature invalid")
    r = _sign_in(client)
    assert r.status_code == 401 and r.json()["error"]["code"] == "firebase_token_invalid"


def test_a_token_without_a_verified_phone_is_refused(client, firebase):
    firebase["claims"] = _claims(phone_number=None, firebase={"sign_in_provider": "password"})
    r = _sign_in(client)
    assert r.status_code == 401 and r.json()["error"]["code"] == "firebase_no_phone"


def test_disabled_until_the_project_is_configured(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "firebase_project_id", None)
    r = _sign_in(client)
    assert r.status_code == 503 and r.json()["error"]["code"] == "firebase_disabled"
