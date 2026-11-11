"""Upload edge cases from the delivery plan (T022): each gives the right message or a sensible result."""

import io
import shutil
from datetime import timedelta

import pytest
from pypdf import PdfReader, PdfWriter

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.security import now_utc
from app.models import Document
from tests.conftest import SAMPLE_POLICY_PAGES, make_pdf


def _upload(client, auth, data: bytes, name="p.pdf", mime="application/pdf", pages=None):
    files = [("file", (name, data, mime))]
    for i, (pdata, pmime) in enumerate(pages or []):
        files.append(("pages", (f"page{i + 2}.png", pdata, pmime)))
    return client.post("/api/v1/documents", files=files, headers=auth)


def _doc(client, auth, response) -> dict:
    assert response.status_code == 201, response.text
    return client.get(f"/api/v1/documents/{response.json()['id']}", headers=auth).json()


def _encrypt(data: bytes, user_password: str) -> bytes:
    writer = PdfWriter(clone_from=PdfReader(io.BytesIO(data)))
    writer.encrypt(user_password=user_password, owner_password="insurer-owner", algorithm="AES-128")
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def _photo(lines: list[str]) -> bytes:
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (1500, 80 + 70 * len(lines)), "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=34)
    for i, line in enumerate(lines):
        draw.text((30, 40 + 70 * i), line, fill="black", font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_pdf_locked_only_against_editing_is_read(client, auth):
    """Insurers often lock PDFs against printing/editing; they open without a password."""
    doc = _doc(client, auth, _upload(client, auth, _encrypt(make_pdf(), user_password="")))
    assert doc["status"] == "extracted", doc


def test_pdf_that_needs_a_password_is_refused(client, auth):
    doc = _doc(client, auth, _upload(client, auth, _encrypt(make_pdf(), user_password="DOB01011990")))
    assert doc["status"] == "failed" and doc["error_code"] == "pdf_password_protected"


def test_page_limit(client, auth, monkeypatch):
    monkeypatch.setattr(get_settings(), "max_pdf_pages", 3)
    ok = _doc(client, auth, _upload(client, auth, make_pdf(SAMPLE_POLICY_PAGES)))
    assert ok["status"] == "extracted" and ok["page_count"] == 3
    too_many = _doc(client, auth, _upload(client, auth, make_pdf([*SAMPLE_POLICY_PAGES, ["Annexure page"]])))
    assert too_many["status"] == "failed" and too_many["error_code"] == "pdf_too_many_pages"


def test_file_over_the_size_limit_is_refused_before_storing(client, auth, monkeypatch):
    monkeypatch.setattr(get_settings(), "max_upload_bytes", 1024 * 1024)
    big = b"%PDF-1.4\n" + b"0" * (1024 * 1024 + 10)
    r = _upload(client, auth, big)
    assert r.status_code == 413 and r.json()["error"]["code"] == "file_too_large"


def test_a_bank_statement_is_not_a_policy(client, auth):
    statement = make_pdf(
        [
            [
                "State Bank of India - Account Statement",
                "Account No: 30012345678  Branch: Ameerpet, Hyderabad",
                "Statement period: 01/10/2026 to 31/10/2026",
                "01/10/2026  UPI/Swiggy/Food order        Debit 450.00   Balance 52,310.00",
                "03/10/2026  NEFT salary credit           Credit 85,000.00 Balance 1,37,310.00",
                "05/10/2026  ATM withdrawal Kukatpally    Debit 5,000.00 Balance 1,32,310.00",
            ]
        ]
    )
    doc = _doc(client, auth, _upload(client, auth, statement))
    assert doc["status"] == "failed" and doc["error_code"] == "not_a_policy"
    assert doc["policy_id"] is None  # no junk draft policy left behind


def test_several_photos_become_one_document(client, auth):
    if not shutil.which("tesseract"):
        pytest.skip("tesseract not installed")
    page1 = _photo(["Motor Insurance Policy Schedule", "Policy No: MTR99887766", "Vehicle IDV Rs. 4,50,000"])
    page2 = _photo(["Own damage and third party cover", "Premium paid: Rs. 8,400", "Nominee: Sita Kumar"])
    doc = _doc(client, auth, _upload(client, auth, page1, "page1.png", "image/png", pages=[(page2, "image/png")]))
    assert doc["status"] == "extracted", doc
    assert doc["content_type"] == "application/pdf" and doc["page_count"] == 2
    assert doc["extraction_method"] == "ocr"


def test_extra_pages_must_be_photos_and_not_too_many(client, auth):
    photo = _photo(["Health insurance"])
    r = _upload(client, auth, photo, "a.png", "image/png", pages=[(make_pdf(), "application/pdf")])
    assert r.status_code == 415
    r = _upload(client, auth, photo, "a.png", "image/png", pages=[(photo, "image/png")] * 10)
    assert r.status_code == 413 and r.json()["error"]["code"] == "too_many_photos"


def test_a_stuck_document_can_be_retried_but_a_busy_one_cannot(client, auth):
    doc = _doc(client, auth, _upload(client, auth, make_pdf()))
    with SessionLocal() as db:
        row = db.get(Document, doc["id"])
        row.status = "processing"
        db.commit()
    r = client.post(f"/api/v1/documents/{doc['id']}/retry", headers=auth)
    assert r.status_code == 409 and r.json()["error"]["code"] == "still_processing"

    with SessionLocal() as db:
        row = db.get(Document, doc["id"])
        row.updated_at = now_utc() - timedelta(minutes=6)
        db.commit()
    r = client.post(f"/api/v1/documents/{doc['id']}/retry", headers=auth)
    assert r.status_code == 200
    assert client.get(f"/api/v1/documents/{doc['id']}", headers=auth).json()["status"] == "extracted"
