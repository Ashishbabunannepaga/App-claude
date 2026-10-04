import logging
import uuid

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.ai.embeddings import get_embedder
from app.ai.gateway import get_ai_gateway
from app.ai.providers.base import AIProviderError
from app.models import Document, DocumentStatus, Policy, PolicyChunk, User
from app.processing.chunking import chunk_pages
from app.processing.extraction import validate_extraction
from app.processing.text_extraction import ExtractionError, extract_text
from app.services.notification_service import notify
from app.storage import get_storage

log = logging.getLogger(__name__)


def process_document(db: Session, document_id: uuid.UUID) -> None:
    """Text → classification + extraction → validation → chunks + embeddings → draft policy.

    Idempotent: re-running replaces the draft policy's extracted fields and chunks.
    """
    doc = db.get(Document, document_id)
    if doc is None:
        return
    doc.status, doc.error_code = DocumentStatus.processing, None
    db.commit()

    try:
        data = get_storage().get(doc.storage_key)
        extracted = extract_text(data, doc.content_type)
        doc.page_count, doc.extraction_method = len(extracted.pages), extracted.method
        doc.extracted_text = extracted.full_text

        raw = get_ai_gateway().extract_policy(extracted.full_text)
        result = validate_extraction(raw, extracted.full_text)

        policy = doc.policy or Policy(user_id=doc.user_id, document_id=doc.id, source="upload")
        if not policy.verified:  # never overwrite fields the user already confirmed
            policy.policy_type = result.policy_type
            for name, value in result.values.items():
                setattr(policy, name, value)
            policy.field_confidence = result.confidence
            policy.extraction_confidence = result.overall_confidence
            policy.details = result.details
            policy.summary = None
        db.add(policy)
        db.flush()

        chunks = chunk_pages(extracted.pages)
        vectors = get_embedder().embed([c.content for c in chunks]) if chunks else []
        db.execute(delete(PolicyChunk).where(PolicyChunk.policy_id == policy.id))
        db.add_all(
            PolicyChunk(
                policy_id=policy.id,
                chunk_index=c.index,
                page=c.page,
                section=c.section,
                content=c.content,
                embedding=v,
            )
            for c, v in zip(chunks, vectors, strict=True)
        )
        doc.status = DocumentStatus.extracted
        db.commit()
        _notify(db, doc, ok=True, policy_id=policy.id)
    except ExtractionError as exc:
        db.rollback()
        _fail(db, document_id, exc.code)
    except AIProviderError:
        db.rollback()
        log.exception("AI provider failed for document %s", document_id)
        _fail(db, document_id, "ai_unavailable")
    except Exception:
        db.rollback()
        log.exception("processing failed for document %s", document_id)
        _fail(db, document_id, "processing_failed")


def _fail(db: Session, document_id: uuid.UUID, code: str) -> None:
    doc = db.get(Document, document_id)
    if doc:
        doc.status, doc.error_code = DocumentStatus.failed, code
        db.commit()
        _notify(db, doc, ok=False)


def _notify(db: Session, doc: Document, ok: bool, policy_id: uuid.UUID | None = None) -> None:
    user = db.get(User, doc.user_id)
    if user is None or not user.notify_processing:
        return
    try:
        notify(
            db,
            doc.user_id,
            kind="processing_done" if ok else "processing_failed",
            title="Your policy is ready to review" if ok else "We couldn't read your document",
            body="Check the details we found and confirm them." if ok else "Open the app to retry or enter details.",
            dedupe_key=f"processing:{doc.id}:{doc.updated_at.isoformat()}",
            policy_id=policy_id,
            deep_link=f"/policy/{policy_id}/verify" if ok else f"/add/processing/{doc.id}",
        )
    except Exception:
        db.rollback()
        log.exception("processing notification failed for document %s", doc.id)
