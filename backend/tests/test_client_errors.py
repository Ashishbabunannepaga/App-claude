from app.api.v1.client_errors import scrub


def test_scrub_masks_numbers_and_emails():
    out = scrub("Policy P/171100/01/2026/004521 for +91 98765 43210 asha@example.com failed")
    assert "004521" not in out and "43210" not in out and "asha@" not in out
    assert "[number]" in out and "[email]" in out


def test_app_crash_report_is_accepted_without_login(client):
    r = client.post(
        "/api/v1/client-errors",
        json={"error_type": "StateError", "message": "Bad state: policy 123456789", "stack": "#0 main", "fatal": True},
    )
    assert r.status_code == 202


def test_app_crash_report_rejects_oversized_fields(client):
    r = client.post("/api/v1/client-errors", json={"error_type": "x" * 500})
    assert r.status_code == 422
