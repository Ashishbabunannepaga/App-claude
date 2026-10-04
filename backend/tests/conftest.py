import os
import tempfile

os.environ.update(
    ENV="test",
    DATABASE_URL=os.environ.get("TEST_DATABASE_URL", "postgresql+psycopg://insure:insure@localhost:5432/insure_test"),
    AI_PROVIDER="mock",
    EMBEDDING_PROVIDER="hashing",
    TASKS_EAGER="true",
    STORAGE_BACKEND="local",
    LOCAL_STORAGE_PATH=tempfile.mkdtemp(prefix="insureiq-test-"),
    OTP_SENDER="console",
    OTP_RESEND_COOLDOWN_SECONDS="0",
)

import io  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.pdfgen import canvas  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.db import Base, engine  # noqa: E402
from app.core.rate_limit import limiter  # noqa: E402
from app.main import app  # noqa: E402
from app.services import auth_service  # noqa: E402

SAMPLE_POLICY_PAGES = [
    [
        "Star Health and Allied Insurance - Health Insurance Policy Schedule",
        "Plan: Family Health Optima",
        "Policy No: P/171100/01/2026/004521",
        "Period of Insurance: From 01/10/2026 To 30/09/2027",
        "Sum Insured: Rs. 10,00,000",
        "Total Premium: Rs. 24,580 (Annual)",
        "Insured members: Self, Spouse",
    ],
    [
        "SECTION 3 BENEFITS",
        "Room Rent: Single private AC room is covered up to 1% of the sum insured per day.",
        "Pre-hospitalisation expenses are covered for 30 days and post-hospitalisation for 60 days.",
        "Maternity Benefit: Maternity expenses are covered up to Rs. 50,000 per delivery after a",
        "waiting period of 24 months from the first policy inception.",
        "Ambulance charges are covered up to Rs. 2,000 per hospitalisation.",
    ],
    [
        "SECTION 5 EXCLUSIONS",
        "Cosmetic surgery and treatment for obesity are not covered.",
        "Pre-existing diseases are covered after a waiting period of 36 months.",
    ],
]


def make_pdf(pages=SAMPLE_POLICY_PAGES) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    for lines in pages:
        y = 800
        for line in lines:
            c.drawString(40, y, line)
            y -= 18
        c.showPage()
    c.save()
    return buf.getvalue()


@pytest.fixture(scope="session", autouse=True)
def _schema():
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture(autouse=True)
def _clean():
    yield
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE " + ", ".join(t.name for t in Base.metadata.sorted_tables) + " CASCADE"))
    limiter.reset()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class CapturingSender:
    def __init__(self):
        self.codes: dict[str, str] = {}

    def send(self, identifier: str, code: str) -> None:
        self.codes[identifier] = code


@pytest.fixture
def otp(monkeypatch) -> CapturingSender:
    sender = CapturingSender()
    monkeypatch.setattr(auth_service, "get_otp_sender", lambda: sender)
    return sender


@pytest.fixture
def login(client, otp):
    def _login(phone: str = "9876543210") -> dict:
        r = client.post("/api/v1/auth/otp/request", json={"identifier": phone})
        assert r.status_code == 200, r.text
        ident = r.json()["identifier"]
        r = client.post(
            "/api/v1/auth/otp/verify", json={"identifier": phone, "code": otp.codes[ident], "consent": True}
        )
        assert r.status_code == 200, r.text
        body = r.json()
        body["headers"] = {"Authorization": f"Bearer {body['access_token']}"}
        return body

    return _login


@pytest.fixture
def auth(login) -> dict:
    return login()["headers"]
