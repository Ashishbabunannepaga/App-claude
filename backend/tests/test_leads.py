from datetime import date, timedelta

import pytest

from app.core.config import get_settings

TOKEN = "l" * 40


@pytest.fixture
def feed(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "leads_api_token", TOKEN)

    def _get(cursor=None, limit=100, token=TOKEN):
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        return client.get("/api/v1/partner/leads", params=params, headers={"X-Leads-Token": token})

    return _get


def _signup(client, otp, phone, contact_consent):
    r = client.post("/api/v1/auth/otp/request", json={"identifier": phone})
    ident = r.json()["identifier"]
    r = client.post(
        "/api/v1/auth/otp/verify",
        json={"identifier": phone, "code": otp.codes[ident], "consent": True, "contact_consent": contact_consent},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    return body["user"], {"Authorization": f"Bearer {body['access_token']}"}


def _policy(client, auth, days_left=40):
    today = date.today()
    r = client.post(
        "/api/v1/policies",
        json={
            "policy_type": "motor",
            "insurer": "ICICI Lombard",
            "policy_number": "SECRET-123",
            "premium": "8400",
            "start_date": str(today - timedelta(days=365 - days_left)),
            "end_date": str(today + timedelta(days=days_left)),
        },
        headers=auth,
    )
    assert r.status_code == 201, r.text


def test_contact_consent_is_optional_and_off_by_default(client, login):
    body = login("9876500001")
    assert body["user"]["contact_consent"] is False
    me = client.get("/api/v1/me", headers=body["headers"]).json()
    assert me["contact_consent"] is False and me["contact_consent_at"] is None


def test_feed_requires_token(client, feed, monkeypatch):
    assert feed(token="wrong" * 8).status_code == 403
    monkeypatch.setattr(get_settings(), "leads_api_token", None)
    assert feed().status_code == 403  # feed disabled when no token is configured


def test_only_opted_in_users_are_leads(client, otp, feed):
    user, auth = _signup(client, otp, "9876500002", contact_consent=True)
    _policy(client, auth)
    _signup(client, otp, "9876500003", contact_consent=False)

    page = feed().json()
    assert [i["app_user_id"] for i in page["items"]] == [user["id"]]
    lead = page["items"][0]
    assert lead["status"] == "active" and lead["phone"].endswith("9876500002")
    assert lead["contact_consent_version"] == get_settings().contact_consent_version
    assert lead["next_renewal_date"] == str(date.today() + timedelta(days=40))
    assert lead["policies"][0]["insurer"] == "ICICI Lombard"
    assert "SECRET-123" not in str(page)  # policy numbers are never shared


def test_opt_in_from_profile_then_withdraw_removes_personal_data(client, login, feed):
    body = login("9876500004")
    auth = body["headers"]
    r = client.patch("/api/v1/me", json={"contact_consent": True, "full_name": "Ravi"}, headers=auth)
    assert r.status_code == 200 and r.json()["contact_consent"] is True and r.json()["full_name"] == "Ravi"

    first = feed().json()
    assert first["items"][0]["status"] == "active"
    cursor = first["next_cursor"]
    assert feed(cursor=cursor).json()["items"] == []  # nothing new since

    client.patch("/api/v1/me", json={"contact_consent": False}, headers=auth)
    later = feed(cursor=cursor).json()["items"]
    assert len(later) == 1 and later[0]["status"] == "withdrawn"
    assert later[0]["phone"] is None and later[0]["full_name"] is None and later[0]["withdrawn_at"]


def test_deletion_request_turns_lead_into_withdrawn(client, otp, feed):
    _, auth = _signup(client, otp, "9876500005", contact_consent=True)
    client.delete("/api/v1/me", headers=auth)
    item = feed().json()["items"][0]
    assert item["status"] == "withdrawn" and item["phone"] is None


def test_policy_change_brings_lead_back_into_the_feed(client, otp, feed):
    _, auth = _signup(client, otp, "9876500006", contact_consent=True)
    cursor = feed().json()["next_cursor"]
    _policy(client, auth, days_left=90)
    items = feed(cursor=cursor).json()["items"]
    assert len(items) == 1 and len(items[0]["policies"]) == 1


def test_paging(client, otp, feed):
    for n in range(3):
        _signup(client, otp, f"98765001{n}0", contact_consent=True)
    page1 = feed(limit=2).json()
    assert len(page1["items"]) == 2 and page1["has_more"] is True
    page2 = feed(cursor=page1["next_cursor"], limit=2).json()
    assert len(page2["items"]) == 1 and page2["has_more"] is False
    assert feed(cursor="not-a-cursor").status_code == 400
