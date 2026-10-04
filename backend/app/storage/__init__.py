from functools import lru_cache

from app.core.config import get_settings
from app.storage.base import StorageBackend


@lru_cache
def get_storage() -> StorageBackend:
    s = get_settings()
    if s.storage_backend == "s3":
        from app.storage.s3 import S3Storage

        if not s.s3_bucket:
            raise RuntimeError("S3_BUCKET is required for the s3 storage backend")
        return S3Storage(s.s3_bucket, s.s3_region, s.s3_endpoint_url)
    from app.storage.local import LocalStorage

    return LocalStorage(s.local_storage_path)
