def test_otp_login_creates_user_with_consent(client, otp):
    r = client.post("/api/v1/auth/otp/request", json={"identifier": "98765 43210"})
    assert r.status_code == 200
    assert r.json()["identifier"] == "+919876543210"
    code = otp.codes["+919876543210"]

    r = client.post("/api/v1/auth/otp/verify", json={"identifier": "9876543210", "code": code})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "consent_required"

    r = client.post("/api/v1/auth/otp/verify", json={"identifier": "9876543210", "code": code, "consent": True})
    assert r.status_code == 200
    body = r.json()
    assert body["is_new_user"] is True
    assert body["user"]["phone"] == "+919876543210"

    me = client.get("/api/v1/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200


def test_wrong_code_and_attempt_limit(client, otp):
    client.post("/api/v1/auth/otp/request", json={"identifier": "9876543210"})
    for _ in range(5):
        r = client.post("/api/v1/auth/otp/verify", json={"identifier": "9876543210", "code": "000000", "consent": True})
        assert r.status_code == 400
    code = otp.codes["+919876543210"]
    r = client.post("/api/v1/auth/otp/verify", json={"identifier": "9876543210", "code": code, "consent": True})
    assert r.status_code == 400  # locked after max attempts


def test_invalid_identifier(client):
    r = client.post("/api/v1/auth/otp/request", json={"identifier": "12345"})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_identifier"


def test_otp_request_rate_limited(client, otp):
    for _ in range(5):
        assert client.post("/api/v1/auth/otp/request", json={"identifier": "9876543210"}).status_code == 200
    assert client.post("/api/v1/auth/otp/request", json={"identifier": "9876543210"}).status_code == 429


def test_refresh_rotation_and_reuse_detection(client, login):
    session = login()
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": session["refresh_token"]})
    assert r.status_code == 200
    rotated = r.json()["refresh_token"]

    # Re-using the old token revokes every session, including the rotated one.
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": session["refresh_token"]}).status_code == 401
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": rotated}).status_code == 401


def test_logout_revokes_refresh_token(client, login):
    session = login()
    assert client.post("/api/v1/auth/logout", json={"refresh_token": session["refresh_token"]}).status_code == 204
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": session["refresh_token"]}).status_code == 401


def test_requires_auth(client):
    assert client.get("/api/v1/me").status_code == 401
    assert client.get("/api/v1/me", headers={"Authorization": "Bearer nope"}).status_code == 401


def test_profile_update_and_account_deletion(client, auth):
    r = client.patch("/api/v1/me", json={"full_name": "Asha Rao", "city": "Pune"}, headers=auth)
    assert r.status_code == 200 and r.json()["full_name"] == "Asha Rao"
    assert client.delete("/api/v1/me", headers=auth).status_code == 202
    assert client.get("/api/v1/me", headers=auth).status_code == 401


def test_production_refuses_insecure_config():
    import pytest

    from app.core.config import Settings

    with pytest.raises(ValueError, match="MOCK"):
        Settings(
            env="production",
            jwt_secret="x" * 40,
            otp_hmac_secret="real",
            otp_sender="msg91",
            storage_backend="s3",
            tasks_eager=False,
            ai_provider="mock",
        )
