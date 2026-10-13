"""Error tracking with Sentry, off unless SENTRY_DSN is set.

Policy documents are sensitive financial and health data, so events carry no personal data: no request
bodies, cookies, headers, user details or local variables, and long strings are cut. Stack traces and
error types are enough to fix bugs.
"""

from typing import Any

from app.core.config import get_settings

_SENSITIVE_KEYS = {"text", "extracted_text", "question", "answer", "content", "prompt", "summary", "phone", "email"}


def _scrub(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: ("[removed]" if k.lower() in _SENSITIVE_KEYS else _scrub(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [_scrub(v) for v in value]
    if isinstance(value, str) and len(value) > 200:
        return value[:200] + "…[cut]"
    return value


def before_send(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any]:
    request = event.get("request") or {}
    for key in ("data", "cookies", "headers", "query_string", "env"):
        request.pop(key, None)
    event.pop("user", None)
    for exc in (event.get("exception") or {}).get("values", []):
        for frame in (exc.get("stacktrace") or {}).get("frames", []):
            frame.pop("vars", None)
    if "extra" in event:
        event["extra"] = _scrub(event["extra"])
    for crumb in (event.get("breadcrumbs") or {}).get("values", []):
        if "data" in crumb:
            crumb["data"] = _scrub(crumb["data"])
        if isinstance(crumb.get("message"), str):
            crumb["message"] = _scrub(crumb["message"])
    return event


def init_error_tracking(component: str) -> bool:
    s = get_settings()
    if not s.sentry_dsn:
        return False
    import sentry_sdk

    sentry_sdk.init(
        dsn=s.sentry_dsn,
        environment=s.env,
        send_default_pii=False,
        include_local_variables=False,
        max_request_body_size="never",
        traces_sample_rate=s.sentry_traces_sample_rate,
        before_send=before_send,
    )
    sentry_sdk.set_tag("component", component)
    return True
