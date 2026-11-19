"""FCM key from a file for local testing, and the test-push script."""

import json

import pytest

from app.core.config import get_settings
from app.scripts import push_test
from app.services import push


@pytest.fixture(autouse=True)
def _fresh_sender():
    push.get_push_sender.cache_clear()
    yield
    push.get_push_sender.cache_clear()


def test_key_is_read_from_a_file(tmp_path, monkeypatch):
    key = tmp_path / "firebase-service-account.json"
    key.write_text(json.dumps({"type": "service_account", "project_id": "capitup-683ca"}))
    s = get_settings()
    monkeypatch.setattr(s, "fcm_service_account_json", None)
    monkeypatch.setattr(s, "fcm_service_account_file", str(key))
    assert json.loads(push.service_account_json())["project_id"] == "capitup-683ca"


def test_json_setting_wins_and_a_missing_file_is_a_clear_error(tmp_path, monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "fcm_service_account_json", '{"from": "secrets manager"}')
    monkeypatch.setattr(s, "fcm_service_account_file", str(tmp_path / "nope.json"))
    assert push.service_account_json() == '{"from": "secrets manager"}'
    monkeypatch.setattr(s, "fcm_service_account_json", None)
    with pytest.raises(RuntimeError, match="not found"):
        push.service_account_json()


def test_fcm_without_a_key_refuses_to_start(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "push_sender", "fcm")
    monkeypatch.setattr(s, "fcm_project_id", "capitup-683ca")
    monkeypatch.setattr(s, "fcm_service_account_json", None)
    monkeypatch.setattr(s, "fcm_service_account_file", None)
    with pytest.raises(RuntimeError, match="FCM_SERVICE_ACCOUNT"):
        push.get_push_sender()


def test_push_test_script_sends_to_each_registered_device(client, login, capsys):
    auth = login("+919876543210")["headers"]
    client.post("/api/v1/me/devices", json={"token": "tok-android-123456", "platform": "android"}, headers=auth)
    assert push_test.main(["+919876543210"]) == 0  # log sender in tests: always "sent"
    out = capsys.readouterr().out
    assert "[OK]   android device tok-andr…" in out and "tok-android-123456" not in out
    assert push_test.main(["+910000000000"]) == 1
