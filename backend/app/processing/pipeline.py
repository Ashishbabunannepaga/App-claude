import logging
import uuid

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.ai.embeddings import get_embedder
from app.ai.gateway import get_ai_gateway
from app.ai.providers.base import AIProviderError
from app.models import Document, DocumentStatus, Policy, PolicyChunk
from app.processing.chunking import chunk_pages
from app.processing.extraction import validate_extraction
from app.processing.text_extraction import ExtractionError, extract_text
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
