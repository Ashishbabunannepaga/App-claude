import json
import re
from abc import ABC, abstractmethod
from typing import Any


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
