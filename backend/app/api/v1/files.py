import hmac
import time

from fastapi import APIRouter
from fastapi.responses import Response

from app.core.config import get_settings
from app.core.errors import AppError
from app.storage import get_storage
from app.storage.local import local_signature

router = APIRouter(tags=["files"], include_in_schema=False)


@router.get("/files/{key:path}")
def serve_local_file(key: str, expires: int, sig: str) -> Response:
    """Serves signed URLs for the LOCAL storage backend (development only)."""
    if get_settings().storage_backend != "local":
        raise AppError("not_found", "Not found", 404)
    if expires < time.time() or not hmac.compare_digest(sig, local_signature(key, expires)):
        raise AppError("forbidden", "Link expired", 403)
    media = "application/pdf" if key.endswith(".pdf") else "image/png" if key.endswith(".png") else "image/jpeg"
    return Response(get_storage().get(key), media_type=media, headers={"Cache-Control": "private, no-store"})
