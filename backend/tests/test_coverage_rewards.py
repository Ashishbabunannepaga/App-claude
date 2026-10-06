from datetime import date, timedelta

from app.services.coverage_report import demo_report
from tests.test_intelligence import _manual, _upload_confirm


def _rows(report: dict) -> dict:
    return {r["key"]: r for s in report["sections"] for r in s["items"]}


def test_demo_reports_for_each_type(client, auth):
    for t in ("health", "life", "motor"):
        r = client.get(f"/api/v1/coverage/demo/{t}", headers=auth)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["demo"] and body["available"] and body["note"]
        assert len(body["scenarios"]) == 5
        assert all(s["item_key"] in _rows(body) for s in body["scenarios"])
    assert client.get("/api/v1/coverage/demo/other", headers=auth).status_code == 422
    assert client.get("/api/v1/coverage/demo/health").status_code == 401


def test_demo_health_grades():
    rows = _rows(demo_report("health"))
    assert rows["sum_insured"]["value"] == "₹10 lakh"
    assert rows["room_rent_limit"]["status"] == "limited"
    assert rows["co_payment"]["status"] == "good"
    assert rows["maternity"]["status"] == "missing"
    assert rows["opd"]["value"] == "Not covered"
    assert rows["pre_post"]["value"] == "60–180 days"
    motor = _rows(demo_report("motor"))
    assert motor["idv"]["value"] == "₹6.5 lakh"
    assert motor["engine_protection"]["status"] == "missing"


def test_report_from_uploaded_document_uses_document_and_never_guesses(client, auth):
    policy = _upload_confirm(client, auth)
    r = client.get(f"/api/v1/policies/{policy['id']}/coverage-report", headers=auth)
    assert r.status_code == 200, r.text
    body = r.json()
    assert not body["demo"] and body["note"] is None
    rows = _rows(body)
    # Mentioned in the wording on page 2 → found with a page reference.
    assert rows["maternity"]["status"] in ("good", "limited") and rows["maternity"]["page"] == 2
    assert rows["ambulance"]["page"] == 2
    # Not in the document at all → "unknown", not "not covered".
    assert rows["opd"]["status"] == "unknown" and rows["opd"]["value"] == "Not found"
    assert rows["opd"]["source"] == "none"
    excl = next(s for s in body["sections"] if s["key"] == "exclusions")
    assert any("cosmetic" in i["detail"].lower() for i in excl["items"])


def test_report_isolation_and_other_type(client, login):
    me = login("9876543210")["headers"]
    other = login("9123456780")["headers"]
    life = _manual(client, me, policy_type="life", insurer="LIC", sum_insured="5000000")
    assert client.get(f"/api/v1/policies/{life['id']}/coverage-report", headers=other).status_code == 404
    rows = _rows(client.get(f"/api/v1/policies/{life['id']}/coverage-report", headers=me).json())
    assert rows["sum_assured"]["value"] == "₹50 lakh"
    assert rows["nominee"]["status"] == "missing"
    client.post(
        f"/api/v1/policies/{life['id']}/nominees",
        json={"full_name": "Ravi Rao", "relation": "spouse", "share_percent": 100},
        headers=me,
    )
    rows = _rows(client.get(f"/api/v1/policies/{life['id']}/coverage-report", headers=me).json())
    assert rows["nominee"]["status"] == "good" and "Ravi Rao" in rows["nominee"]["detail"]

    misc = _manual(client, me, policy_type="other", insurer="X")
    body = client.get(f"/api/v1/policies/{misc['id']}/coverage-report", headers=me).json()
    assert body["available"] is False and body["sections"] == []


def test_rewards_are_earned_once_and_capped(client, auth):
    r = client.get("/api/v1/rewards", headers=auth).json()
    assert r["balance"] == 0 and not any(t["done"] for t in r["tasks"])

    client.patch("/api/v1/me", json={"full_name": "Asha Rao"}, headers=auth)
    p = _manual(client, auth, end_date=str(date.today() + timedelta(days=300)))
    client.post("/api/v1/me/family", json={"relation": "spouse", "full_name": "Ravi"}, headers=auth)
    r = client.get("/api/v1/rewards", headers=auth).json()
    assert r["balance"] == 20 + 50 + 20
    done = {t["kind"]: t["done"] for t in r["tasks"]}
    assert done["profile"] and done["family_member"] and not done["nominee"]
    assert len(r["history"]) == 3

    # Repeated reads and delete + re-add never double-count.
    assert client.get("/api/v1/rewards", headers=auth).json()["balance"] == 90
    client.delete(f"/api/v1/policies/{p['id']}", headers=auth)
    assert client.get("/api/v1/rewards", headers=auth).json()["balance"] == 90

    for _ in range(12):
        _manual(client, auth)
    r = client.get("/api/v1/rewards", headers=auth).json()
    assert r["balance"] == 20 + 20 + 10 * 50
    assert next(t for t in r["tasks"] if t["kind"] == "policy_added")["done"]
    assert "rewards" in client.get("/api/v1/me/export", headers=auth).json()


def test_expert_review_support_category(client, auth):
    r = client.post(
        "/api/v1/support", json={"category": "expert_review", "message": "Please review my health cover"}, headers=auth
    )
    assert r.status_code == 201
