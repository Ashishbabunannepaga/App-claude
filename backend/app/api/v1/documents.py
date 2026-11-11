import hashlib
import io
import uuid
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, File, Request, UploadFile
from sqlalchemy import delete, select

from app.api.deps import DB, CurrentUser, client_ip
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.rate_limit import limiter
from app.core.security import now_utc
from app.models import Document, DocumentStatus, PolicyChunk
from app.schemas.policy import DocumentOut, SignedUrlOut
from app.services.audit import audit
from app.services.policy_service import get_owned_document
from app.storage import get_storage
from app.workers.tasks import enqueue_process_document

router = APIRouter(prefix="/documents", tags=["documents"])

_MAGIC = {
    b"%PDF-": ("application/pdf", "pdf"),
    b"\x89PNG": ("image/png", "png"),
    b"\xff\xd8\xff": ("image/jpeg", "jpg"),
}


def _sniff(data: bytes) -> tuple[str, str]:
    for magic, kind in _MAGIC.items():
        if data.startswith(magic):
            return kind
    raise AppError("unsupported_file", "Please upload a PDF, JPG or PNG file", 415)


MAX_PHOTO_PAGES = 10
# A document still "uploaded" or "processing" after this long lost its worker: let the user retry.
STALE_AFTER = timedelta(minutes=5)


def _photos_to_pdf(photos: list[bytes]) -> bytes:
    """Several photos of one policy become one PDF, a page per photo, so it is read as one document."""
    from PIL import Image, ImageOps

    pages = []
    for data in photos:
        with Image.open(io.BytesIO(data)) as img:
            pages.append(ImageOps.exif_transpose(img).convert("RGB"))
    out = io.BytesIO()
    pages[0].save(out, format="PDF", save_all=True, append_images=pages[1:], resolution=150)
    return out.getvalue()


async def _read(file: UploadFile, limit: int) -> bytes:
    data = await file.read(limit + 1)
    if len(data) > limit:
        raise AppError("file_too_large", f"File must be under {limit // (1024 * 1024)} MB", 413)
    if not data:
        raise AppError("empty_file", "The file is empty")
    return data


def _out(doc: Document) -> DocumentOut:
    out = DocumentOut.model_validate(doc)
    out.policy_id = doc.policy.id if doc.policy else None
    return out


@router.post("", response_model=DocumentOut, status_code=201)
async def upload(
    file: UploadFile,
    user: CurrentUser,
    db: DB,
    background: BackgroundTasks,
    request: Request,
    pages: Annotated[list[UploadFile] | None, File(description="More photos of the same policy, in order")] = None,
) -> DocumentOut:
    s = get_settings()
    limiter.hit(f"upload:{user.id}", limit=30, window_seconds=3600)
    data = await _read(file, s.max_upload_bytes)
    content_type, ext = _sniff(data)
    if pages:
        if len(pages) + 1 > MAX_PHOTO_PAGES:
            raise AppError("too_many_photos", f"Please send at most {MAX_PHOTO_PAGES} photos for one policy", 413)
        photos = [data]
        for page in pages:
            photos.append(await _read(page, s.max_upload_bytes))
            if sum(len(p) for p in photos) > s.max_upload_bytes * 2:
                raise AppError("file_too_large", "These photos are too large together. Please send fewer pages.", 413)
        if any(_sniff(p)[0] == "application/pdf" for p in photos):
            raise AppError("unsupported_file", "Add pages only as photos (JPG or PNG), not PDFs", 415)
        try:
            data = _photos_to_pdf(photos)
        except Exception as exc:  # noqa: BLE001 - a broken image is the user's file, not a server error
            raise AppError("unsupported_file", "One of the photos could not be opened", 415) from exc
        content_type, ext = "application/pdf", "pdf"
    digest = hashlib.sha256(data).hexdigest()

    existing = db.scalar(select(Document).where(Document.user_id == user.id, Document.sha256 == digest))
    if existing is not None:
        return _out(existing)

    doc_id = uuid.uuid4()
    key = f"users/{user.id}/documents/{doc_id}.{ext}"
    get_storage().put(key, data, content_type)
    doc = Document(
        id=doc_id,
        user_id=user.id,
        storage_key=key,
        original_filename=(file.filename or "")[:255] or None,
        content_type=content_type,
        size_bytes=len(data),
        sha256=digest,
        status=DocumentStatus.uploaded,
    )
    db.add(doc)
    audit(db, "document_uploaded", user.id, "document", doc_id, ip=client_ip(request), size=len(data))
    db.commit()
    enqueue_process_document(doc_id, background)
    return _out(doc)


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: uuid.UUID, user: CurrentUser, db: DB) -> DocumentOut:
    return _out(get_owned_document(db, user.id, document_id))


@router.post("/{document_id}/retry", response_model=DocumentOut)
def retry(document_id: uuid.UUID, user: CurrentUser, db: DB, background: BackgroundTasks) -> DocumentOut:
    doc = get_owned_document(db, user.id, document_id)
    stuck = doc.status in (DocumentStatus.uploaded, DocumentStatus.processing) and (
        doc.updated_at is None or doc.updated_at < now_utc() - STALE_AFTER
    )
    if doc.status != DocumentStatus.failed and not stuck:
        if doc.status == DocumentStatus.extracted:
            raise AppError("not_retryable", "This document has already been read", 409)
        raise AppError("still_processing", "We're still reading this document. Please wait a minute.", 409)
    doc.status, doc.error_code = DocumentStatus.uploaded, None
    db.commit()
    enqueue_process_document(doc.id, background)
    return _out(doc)


@router.get("/{document_id}/url", response_model=SignedUrlOut)
def signed_url(document_id: uuid.UUID, user: CurrentUser, db: DB, request: Request) -> SignedUrlOut:
    doc = get_owned_document(db, user.id, document_id)
    ttl = get_settings().signed_url_ttl_seconds
    audit(db, "document_url_issued", user.id, "document", doc.id, ip=client_ip(request))
    db.commit()
    return SignedUrlOut(url=get_storage().signed_url(doc.storage_key, ttl), expires_in=ttl)


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: uuid.UUID, user: CurrentUser, db: DB, request: Request) -> None:
    doc = get_owned_document(db, user.id, document_id)
    if doc.policy is not None:
        if doc.policy.verified:
            # Keep the user's confirmed policy, but drop all text derived from the document.
            db.execute(delete(PolicyChunk).where(PolicyChunk.policy_id == doc.policy.id))
            doc.policy.summary = None
        else:
            db.delete(doc.policy)  # an unconfirmed draft has no value without its document
    get_storage().delete(doc.storage_key)
    db.delete(doc)
    audit(db, "document_deleted", user.id, "document", document_id, ip=client_ip(request))
    db.commit()
