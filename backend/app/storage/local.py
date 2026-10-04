import hashlib
import hmac
import shutil
import time
from pathlib import Path

from app.core.config import get_settings
from app.storage.base import StorageBackend


class LocalStorage(StorageBackend):
    """Filesystem storage for local development only (refused in production by config)."""

    def __init__(self, root: str):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("invalid storage key")
        return path

    def put(self, key: str, data: bytes, content_type: str) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)

    def delete_prefix(self, prefix: str) -> None:
        shutil.rmtree(self._path(prefix), ignore_errors=True)

    def signed_url(self, key: str, ttl_seconds: int) -> str:
        expires = int(time.time()) + ttl_seconds
        sig = local_signature(key, expires)
        return f"/api/v1/files/{key}?expires={expires}&sig={sig}"


def local_signature(key: str, expires: int) -> str:
    secret = get_settings().jwt_secret.encode()
    return hmac.new(secret, f"{key}:{expires}".encode(), hashlib.sha256).hexdigest()
