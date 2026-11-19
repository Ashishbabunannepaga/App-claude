"""Ops review queue: low-confidence readings, only for clients who opted in to be contacted."""

import pytest

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.models import AuditLog, Policy
from tests.conftest import SAMPLE_POLICY_PAGES, make_pdf

ADMIN = {"X-Admin-Token": "a" * 40}


@pytest.fixture(autouse=True)
def admin(monkeypatch):
    monkeypatch.setattr(get_settings(), "admin_api_token", "a" * 40)


def _signup(client, otp, phone, contact_consent):
    ident = client.post("/api/v1/auth/otp/request", json={"identifier": phone}).json()["identifier"]
    body = client.post(
        "/api/v1/auth/otp/verify",
        json={"identifier": phone, "code": otp.codes[ident], "consent": True, "contact_consent": contact_consent},
    ).json()
    return {"Authorization": f"Bearer {body['access_token']}"}


def _uploaded_policy(client, auth, pdf: bytes, *, overall: float, conf: dict | None = None) -> str:
    doc = client.post("/api/v1/documents", files={"file": ("p.pdf", pdf, "application/pdf")}, headers=auth).json()
    policy_id = client.get(f"/api/v1/documents/{doc['id']}", headers=auth).json()["policy_id"]
    with SessionLocal() as db:
        p = db.get(Policy, policy_id)
        p.extraction_confidence = overall
        p.field_confidence = conf if conf is not None else {k: 0.95 for k in p.field_confidence}
        db.commit()
    return policy_id


def _pdf(n: int) -> bytes:  # a different file each time (uploads are de-duplicated by content)
    first = [line.replace("004521", f"00452{n}") for line in SAMPLE_POLICY_PAGES[0]]
    return make_pdf([first, *SAMPLE_POLICY_PAGES[1:]])


def test_only_opted_in_low_confidence_readings_are_queued(client, otp):
    opted_in = _signup(client, otp, "+919800000001", True)
    private = _signup(client, otp, "+919800000002", False)
    unsure = _uploaded_policy(client, opted_in, _pdf(1), overall=0.5, conf={"insurer": 0.9, "premium": 0.3})
    _uploaded_policy(client, opted_in, _pdf(2), overall=0.97)  # confident: not queued
    _uploaded_policy(client, private, _pdf(3), overall=0.2)  # unsure, but no contact consent: never shown

    assert client.get("/api/v1/admin/review").status_code == 403
    queue = client.get("/api/v1/admin/review", headers=ADMIN).json()
    assert [q["id"] for q in queue] == [unsure]
    item = queue[0]
    assert "premium" in item["low_fields"] and "insurer" not in item["low_fields"]
    assert item["user"] == "+91******01"  # phone masked


def test_review_is_recorded_audited_and_leaves_the_policy_untouched(client, otp):
    auth = _signup(client, otp, "+919800000003", True)
    policy_id = _uploaded_policy(client, auth, _pdf(4), overall=0.4)
    before = client.get(f"/api/v1/policies/{policy_id}", headers=auth).json()

    url = client.get(f"/api/v1/admin/review/{policy_id}/document", headers=ADMIN).json()["url"]
    assert url
    r = client.post(
        f"/api/v1/admin/review/{policy_id}",
        json={"outcome": "needs_client_check", "note": "Premium looks like GST only"},
        headers=ADMIN,
    )
    assert r.status_code == 200 and r.json()["outcome"] == "needs_client_check"
    assert client.get("/api/v1/admin/review", headers=ADMIN).json() == []  # reviewed: out of the queue
    after = client.get(f"/api/v1/policies/{policy_id}", headers=auth).json()
    assert {k: after[k] for k in ("insurer", "premium", "verified")} == {
        k: before[k] for k in ("insurer", "premium", "verified")
    }
    with SessionLocal() as db:
        actions = {a.action for a in db.query(AuditLog).all()}
    assert {"admin_document_viewed", "policy_reviewed"} <= actions


def test_withdrawing_consent_closes_the_document_to_staff(client, otp):
    auth = _signup(client, otp, "+919800000004", True)
    policy_id = _uploaded_policy(client, auth, _pdf(5), overall=0.4)
    assert client.patch("/api/v1/me", json={"contact_consent": False}, headers=auth).status_code == 200
    assert client.get("/api/v1/admin/review", headers=ADMIN).json() == []
    assert client.get(f"/api/v1/admin/review/{policy_id}/document", headers=ADMIN).status_code == 404
    r = client.post(f"/api/v1/admin/review/{policy_id}", json={"outcome": "correct"}, headers=ADMIN)
    assert r.status_code == 404
