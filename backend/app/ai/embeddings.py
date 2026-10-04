import hashlib
import math
import re
from abc import ABC, abstractmethod
from functools import lru_cache

import httpx

from app.ai.providers.base import AIProviderError
from app.core.config import get_settings

_TOKEN = re.compile(r"[a-z0-9]+")


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class OpenAIEmbedder(EmbeddingProvider):
    url = "https://api.openai.com/v1/embeddings"

    def __init__(self, api_key: str, model: str, dim: int, timeout: float):
        self.api_key, self.model, self.dim, self.timeout = api_key, model, dim, timeout

    def embed(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for i in range(0, len(texts), 64):
            try:
                resp = httpx.post(
                    self.url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"model": self.model, "input": texts[i : i + 64], "dimensions": self.dim},
                    timeout=self.timeout,
                )
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                raise AIProviderError(f"embedding request failed: {type(exc).__name__}") from exc
            out.extend(d["embedding"] for d in sorted(resp.json()["data"], key=lambda d: d["index"]))
        return out


class HashingEmbedder(EmbeddingProvider):
    """MOCK — lexical bag-of-words hashed into a vector. Development/tests only.

    Gives keyword-level retrieval so the RAG flow can be exercised without an API key.
    Refused in production by config validation.
    """

    def __init__(self, dim: int):
        self.dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._one(t) for t in texts]

    def _one(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for token in _TOKEN.findall(text.lower()):
            h = int.from_bytes(hashlib.md5(token.encode(), usedforsecurity=False).digest()[:4], "little")
            vec[h % self.dim] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


@lru_cache
def get_embedder() -> EmbeddingProvider:
    s = get_settings()
    if s.embedding_provider == "openai":
        if not s.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for openai embeddings")
        return OpenAIEmbedder(s.openai_api_key, s.openai_embedding_model, s.embedding_dim, s.ai_timeout_seconds)
    return HashingEmbedder(s.embedding_dim)
