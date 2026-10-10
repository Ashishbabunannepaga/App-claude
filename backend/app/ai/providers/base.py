import json
import re
import time
from abc import ABC, abstractmethod
from typing import Any

import httpx


class AIProviderError(Exception):
    pass


class AIProvider(ABC):
    """A provider turns (system, prompt) into a JSON object.

    `task` and `context` are passed so that the MOCK provider can work offline; real providers
    rely only on `system` and `prompt`.
    """

    name: str

    @abstractmethod
    def complete_json(
        self, task: str, system: str, prompt: str, *, context: dict[str, Any], max_tokens: int = 2000
    ) -> dict[str, Any]: ...


_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def parse_json_object(text: str) -> dict[str, Any]:
    cleaned = _FENCE.sub("", text.strip())
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end == -1:
        raise AIProviderError("model did not return JSON")
    try:
        value = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError as exc:
        raise AIProviderError("model returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise AIProviderError("model returned non-object JSON")
    return value


RETRY_STATUS = {429, 500, 502, 503, 504}


def post_with_retry(
    url: str, *, headers: dict[str, str], json: dict[str, Any], timeout: float, attempts: int = 3, label: str
) -> httpx.Response:
    """POST with retries on rate limits, server errors and network failures (1 s, 2 s backoff).

    Errors name the provider and status only: the request body (policy text) and the key never reach logs.
    """
    for attempt in range(attempts):
        try:
            resp = httpx.post(url, headers=headers, json=json, timeout=timeout)
        except httpx.TransportError as exc:
            if attempt == attempts - 1:
                raise AIProviderError(f"{label} request failed: {type(exc).__name__}") from exc
        else:
            if resp.status_code < 400:
                return resp
            if resp.status_code not in RETRY_STATUS or attempt == attempts - 1:
                raise AIProviderError(f"{label} request failed: HTTP {resp.status_code}")
            retry_after = resp.headers.get("retry-after", "")
            if retry_after.isdigit():
                time.sleep(min(int(retry_after), 10))
                continue
        time.sleep(2**attempt)
    raise AIProviderError(f"{label} request failed")  # unreachable; keeps type checkers happy
