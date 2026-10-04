from datetime import date, timedelta

import pytest

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.services.notification_service import renewal_reminders
from tests.conftest import make_pdf


def _upload_and_confirm(client, auth) -> dict:
    doc = client.post(
        "/api/v1/documents", files={"file": ("p.pdf", make_pdf(), "application/pdf")}, headers=auth
    ).json()
    doc = client.get(f"/api/v1/documents/{doc['id']}", headers=auth).json()
    return client.post(f"/api/v1/policies/{doc['policy_id']}/confirm", json={}, headers=auth).json()


def _manual(client, auth, days_left: int, **extra) -> dict:
    today = date.today()
    body = {
        "policy_type": "health",
        "insurer": "Niva Bupa",
        "sum_insured": "500000",
        "start_date": str(today - timedelta(days=365 - days_left)),
        "end_date": str(today + timedelta(days=days_left)),
        **extra,
    }
    r = client.post("/api/v1/policies", json=body, headers=auth)
    assert r.status_code == 201, r.text
    return r.json()


def test_family_members_and_policy_linking(client, login):
    auth = login("9876543210")["headers"]
    other = login("9123456780")["headers"]
    spouse = client.post("/api/v1/me/family", json={"relation": "spouse", "full_name": "Ravi Rao"}, headers=auth)
    assert spouse.status_code == 201
    spouse = spouse.json()
    assert client.get("/api/v1/me/family", headers=auth).json()[0]["full_name"] == "Ravi Rao"
    assert client.get("/api/v1/me/family", headers=other).json() == []

    policy = _manual(client, auth, 200, member_ids=[spouse["id"]])
    assert [m["full_name"] for m in policy["members"]] == ["Ravi Rao"]

    # Someone else's member can't be attached.
    foreign = client.post("/api/v1/me/family", json={"relation": "self", "full_name": "Bob"}, headers=other).json()
    r = client.patch(f"/api/v1/policies/{policy['id']}", json={"member_ids": [foreign["id"]]}, headers=auth)
    assert r.status_code == 422
    assert client.patch(f"/api/v1/me/family/{spouse['id']}", json={"full_name": "X"}, headers=other).status_code == 404

    assert client.delete(f"/api/v1/me/family/{spouse['id']}", headers=auth).status_code == 204
    assert client.get(f"/api/v1/policies/{policy['id']}", headers=auth).json()["members"] == []


def test_processing_creates_notification(client, auth):
    _upload_and_confirm(client, auth)
    items = client.get("/api/v1/notifications", headers=auth).json()
    assert items[0]["kind"] == "processing_done"
    assert items[0]["deep_link"].endswith("/verify")
    assert client.get("/api/v1/notifications/unread-count", headers=auth).json()["count"] == 1
    assert client.post(f"/api/v1/notifications/{items[0]['id']}/read", headers=auth).status_code == 204
    assert client.get("/api/v1/notifications/unread-count", headers=auth).json()["count"] == 0


def test_renewal_reminders_bucketed_and_deduplicated(client, auth):
    soon = _manual(client, auth, 20)
    _manual(client, auth, 200)  # too far away: no reminder
    with SessionLocal() as db:
        assert renewal_reminders(db) == 1
        assert renewal_reminders(db) == 0  # same bucket never re-sent
        assert renewal_reminders(db, today=date.today() + timedelta(days=5)) == 1  # 15-day bucket
    reminders = [n for n in client.get("/api/v1/notifications", headers=auth).json() if n["kind"] == "renewal"]
    assert len(reminders) == 2 and reminders[0]["policy_id"] == soon["id"]
    assert "Niva Bupa" in reminders[0]["body"] and "500000" not in reminders[0]["body"]

    # Marked renewed / reminders off → no more reminders, and it leaves the renewal list.
    r = client.put(f"/api/v1/policies/{soon['id']}/renewal", json={"renewal_status": "renewed"}, headers=auth)
    assert r.json()["renewal_status"] == "renewed"
    with SessionLocal() as db:
        assert renewal_reminders(db, today=date.today() + timedelta(days=13)) == 0
    assert client.get("/api/v1/portfolio/summary", headers=auth).json()["upcoming_renewals"] == []


def test_renewal_reminders_respect_user_preference(client, auth):
    _manual(client, auth, 10)
    client.patch("/api/v1/me", json={"notify_renewals": False}, headers=auth)
    with SessionLocal() as db:
        assert renewal_reminders(db) == 0


def test_device_registration(client, login):
    a = login("9876543210")["headers"]
    b = login("9123456780")["headers"]
    body = {"token": "fcm-token-1234567890", "platform": "android"}
    assert client.post("/api/v1/me/devices", json=body, headers=a).status_code == 204
    assert client.post("/api/v1/me/devices", json=body, headers=b).status_code == 204  # reassigned
    assert client.delete("/api/v1/me/devices/fcm-token-1234567890", headers=a).status_code == 204


def test_policy_health_check(client, auth):
    policy = _upload_and_confirm(client, auth)
    health = client.get(f"/api/v1/policies/{policy['id']}/health", headers=auth).json()
    assert health["available"] is True and 0 <= health["score"] <= 100
    strong = {f["key"] for f in health["strong"]}
    attention = {f["key"] for f in health["attention"]}
    assert {"sum_insured", "maternity", "ambulance"} <= strong
    assert {"key": "sum_insured", "label": "Sum insured", "grade": "strong", "detail": "₹10 lakh cover."} in health[
        "strong"
    ]
    assert {"room_rent_limit", "ped_waiting_period"} <= attention
    assert "OPD / doctor visits" in health["not_mentioned"]  # never guessed

    life = _manual(client, auth, 100, policy_type="life", insurer="LIC")
    assert client.get(f"/api/v1/policies/{life['id']}/health", headers=auth).json()["available"] is False


def test_summary_and_answers_are_labelled_with_provider(client, auth):
    policy = _upload_and_confirm(client, auth)
    assert client.get(f"/api/v1/policies/{policy['id']}/summary", headers=auth).json()["provider"] == "mock"
    a = client.post(f"/api/v1/policies/{policy['id']}/ask", json={"question": "Is ambulance covered?"}, headers=auth)
    assert a.json()["provider"] == "mock"
    assert "Ambulance" in a.json()["answer"]


def test_support_and_export(client, auth):
    assert (
        client.post(
            "/api/v1/support", json={"category": "question", "message": "How do I renew?"}, headers=auth
        ).status_code
        == 201
    )
    _manual(client, auth, 100)
    data = client.get("/api/v1/me/export", headers=auth).json()
    assert data["profile"]["phone"] == "+919876543210"
    assert len(data["policies"]) == 1


@pytest.fixture
def admin_token(monkeypatch):
    monkeypatch.setattr(get_settings(), "admin_api_token", "a" * 40)
    return {"X-Admin-Token": "a" * 40}


def test_admin_requires_token_and_masks_pii(client, auth, admin_token):
    client.post("/api/v1/support", json={"category": "problem", "message": "Upload fails"}, headers=auth)
    assert client.get("/api/v1/admin/stats").status_code == 403
    assert client.get("/api/v1/admin/stats", headers={"X-Admin-Token": "wrong"}).status_code == 403
    stats = client.get("/api/v1/admin/stats", headers=admin_token).json()
    assert stats["users"] == 1 and stats["open_support_requests"] == 1
    support = client.get("/api/v1/admin/support", headers=admin_token).json()
    assert support[0]["user"] == "+91******10"
    r = client.patch(f"/api/v1/admin/support/{support[0]['id']}", json={"status": "closed"}, headers=admin_token)
    assert r.json()["status"] == "closed"
    assert client.get("/admin").status_code == 200
