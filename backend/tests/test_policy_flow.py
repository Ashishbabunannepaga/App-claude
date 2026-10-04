from datetime import date, timedelta

from tests.conftest import make_pdf


def upload(client, auth, data: bytes, name="policy.pdf"):
    return client.post("/api/v1/documents", files={"file": (name, data, "application/pdf")}, headers=auth)


def test_upload_extract_verify_ask(client, auth):
    r = upload(client, auth, make_pdf())
    assert r.status_code == 201, r.text
    doc_id = r.json()["id"]

    doc = client.get(f"/api/v1/documents/{doc_id}", headers=auth).json()
    assert doc["status"] == "extracted", doc
    assert doc["page_count"] == 3 and doc["extraction_method"] == "text"

    policy = client.get(f"/api/v1/policies/{doc['policy_id']}", headers=auth).json()
    assert policy["verified"] is False
    assert policy["policy_type"] == "health"
    assert policy["insurer"] == "Star Health"
    assert policy["policy_number"] == "P/171100/01/2026/004521"
    assert policy["start_date"] == "2026-10-01" and policy["end_date"] == "2027-09-30"
    assert float(policy["sum_insured"]) == 1_000_000
    assert float(policy["premium"]) == 24_580
    assert 0 < policy["extraction_confidence"] <= 1

    r = client.post(
        f"/api/v1/policies/{policy['id']}/confirm", json={"plan_name": "Family Health Optima"}, headers=auth
    )
    assert r.status_code == 200
    assert r.json()["verified"] is True
    assert r.json()["field_confidence"]["plan_name"] == 1.0

    r = client.post(f"/api/v1/policies/{policy['id']}/ask", json={"question": "Is maternity covered?"}, headers=auth)
    assert r.status_code == 200
    answer = r.json()
    assert answer["answerable"] is True
    assert "Maternity" in answer["answer"] or "maternity" in answer["answer"]
    assert answer["citations"] and answer["citations"][0]["page"] == 2
    assert answer["disclaimer"]

    r = client.post(f"/api/v1/policies/{policy['id']}/ask", json={"question": "Is skydiving included?"}, headers=auth)
    assert r.json()["answerable"] is False
    assert r.json()["citations"] == []

    history = client.get(f"/api/v1/policies/{policy['id']}/messages", headers=auth).json()
    assert len(history) == 2

    summary = client.get(f"/api/v1/policies/{policy['id']}/summary", headers=auth).json()
    assert summary["headline"] and summary["disclaimer"]


def test_duplicate_upload_returns_existing(client, auth):
    data = make_pdf()
    first = upload(client, auth, data).json()
    second = upload(client, auth, data)
    assert second.json()["id"] == first["id"]


def test_rejects_unsupported_and_empty_pdf_text(client, auth):
    r = client.post("/api/v1/documents", files={"file": ("a.txt", b"hello world", "text/plain")}, headers=auth)
    assert r.status_code == 415

    blank = upload(client, auth, make_pdf([[""]])).json()
    doc = client.get(f"/api/v1/documents/{blank['id']}", headers=auth).json()
    assert doc["status"] == "failed"
    assert doc["error_code"] in ("no_text_found", "ocr_unavailable")
    assert client.post(f"/api/v1/documents/{blank['id']}/retry", headers=auth).status_code == 200


def test_other_users_cannot_access(client, login):
    alice = login("9876543210")["headers"]
    bob = login("9123456780")["headers"]
    doc = upload(client, alice, make_pdf()).json()
    doc = client.get(f"/api/v1/documents/{doc['id']}", headers=alice).json()

    assert client.get(f"/api/v1/documents/{doc['id']}", headers=bob).status_code == 404
    assert client.get(f"/api/v1/documents/{doc['id']}/url", headers=bob).status_code == 404
    assert client.get(f"/api/v1/policies/{doc['policy_id']}", headers=bob).status_code == 404
    assert (
        client.post(
            f"/api/v1/policies/{doc['policy_id']}/ask", json={"question": "maternity?"}, headers=bob
        ).status_code
        == 404
    )
    assert client.delete(f"/api/v1/policies/{doc['policy_id']}", headers=bob).status_code == 404
    assert client.get("/api/v1/policies", headers=bob).json() == []


def test_signed_url_serves_file(client, auth):
    data = make_pdf()
    doc = upload(client, auth, data).json()
    url = client.get(f"/api/v1/documents/{doc['id']}/url", headers=auth).json()["url"]
    r = client.get(url)
    assert r.status_code == 200 and r.content == data
    assert client.get(url.replace("sig=", "sig=0")).status_code == 403


def test_manual_policy_and_portfolio(client, auth):
    today = date.today()
    r = client.post(
        "/api/v1/policies",
        json={
            "policy_type": "motor",
            "insurer": "Acko",
            "premium": "8000",
            "sum_insured": "450000",
            "start_date": str(today - timedelta(days=345)),
            "end_date": str(today + timedelta(days=20)),
            "payment_frequency": "annual",
        },
        headers=auth,
    )
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "expiring_soon" and r.json()["verified"] is True

    client.post(
        "/api/v1/policies",
        json={
            "policy_type": "life",
            "insurer": "LIC",
            "premium": "1000",
            "payment_frequency": "monthly",
            "sum_insured": "10000000",
        },
        headers=auth,
    )

    s = client.get("/api/v1/portfolio/summary", headers=auth).json()
    assert s["total_policies"] == 2 and s["active_policies"] == 2
    assert s["expiring_soon"] == 1
    assert float(s["total_annual_premium"]) == 8000 + 12_000
    assert float(s["life_cover"]) == 10_000_000
    assert s["upcoming_renewals"][0]["days_to_expiry"] == 20

    bad = client.post(
        "/api/v1/policies",
        json={"policy_type": "life", "insurer": "LIC", "start_date": "2027-01-01", "end_date": "2026-01-01"},
        headers=auth,
    )
    assert bad.status_code == 422 and bad.json()["error"]["code"] == "validation_error"


def test_delete_policy_removes_document(client, auth):
    doc = upload(client, auth, make_pdf()).json()
    doc = client.get(f"/api/v1/documents/{doc['id']}", headers=auth).json()
    assert client.delete(f"/api/v1/policies/{doc['policy_id']}", headers=auth).status_code == 204
    assert client.get(f"/api/v1/documents/{doc['id']}", headers=auth).status_code == 404


def test_photo_upload_goes_through_ocr(client, auth):
    import io
    import shutil

    import pytest
    from PIL import Image, ImageDraw, ImageFont

    if not shutil.which("tesseract"):
        pytest.skip("tesseract not installed")
    img = Image.new("RGB", (1400, 400), "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=36)
    draw.text((30, 40), "Motor Insurance - Vehicle IDV Rs. 4,50,000", fill="black", font=font)
    draw.text((30, 120), "Policy No: MTR99887766", fill="black", font=font)
    draw.text((30, 200), "Own damage and third party cover", fill="black", font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    r = client.post("/api/v1/documents", files={"file": ("photo.png", buf.getvalue(), "image/png")}, headers=auth)
    doc = client.get(f"/api/v1/documents/{r.json()['id']}", headers=auth).json()
    assert doc["status"] == "extracted", doc
    assert doc["extraction_method"] == "ocr"
    policy = client.get(f"/api/v1/policies/{doc['policy_id']}", headers=auth).json()
    assert policy["policy_type"] == "motor"
    assert policy["policy_number"] == "MTR99887766"
