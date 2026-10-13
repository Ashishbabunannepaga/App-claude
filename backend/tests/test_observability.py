from app.core.observability import before_send


def test_error_events_carry_no_personal_data():
    event = {
        "request": {
            "url": "/api/v1/policies/1/ask",
            "data": {"question": "Is my wife's maternity covered?"},
            "headers": {"Authorization": "Bearer x"},
            "cookies": {"s": "1"},
        },
        "user": {"id": "u1", "phone": "+919876543210"},
        "exception": {"values": [{"stacktrace": {"frames": [{"function": "f", "vars": {"text": "policy text"}}]}}]},
        "extra": {"text": "full policy document", "policy_id": "p1"},
        "breadcrumbs": {"values": [{"message": "x" * 500, "data": {"phone": "+91..."}}]},
    }
    out = before_send(event, {})
    assert out["request"] == {"url": "/api/v1/policies/1/ask"}
    assert "user" not in out
    assert "vars" not in out["exception"]["values"][0]["stacktrace"]["frames"][0]
    assert out["extra"] == {"text": "[removed]", "policy_id": "p1"}
    crumb = out["breadcrumbs"]["values"][0]
    assert crumb["data"] == {"phone": "[removed]"} and len(crumb["message"]) < 220


def test_tracking_is_off_without_dsn():
    from app.core.observability import init_error_tracking

    assert init_error_tracking("api") is False
