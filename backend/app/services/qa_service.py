"""Retrieval-augmented, citation-enforced answers about a single policy."""

import re
import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.ai.embeddings import get_embedder
from app.ai.gateway import get_ai_gateway
from app.ai.providers.base import AIProviderError
from app.core.config import get_settings
from app.core.errors import AppError
from app.models import Policy, PolicyChunk, QaMessage
from app.services.policy_service import structured_view

DISCLAIMER = (
    "Based on your policy document. This is not advice — please confirm with your insurer "
    "before making a claim or financial decision."
)
NOT_FOUND = (
    "I couldn't find a clear answer to this in your policy document. "
    "Please check the full policy wording or contact your insurer."
)
_STOP = {
    "what",
    "does",
    "is",
    "my",
    "the",
    "and",
    "for",
    "how",
    "much",
    "are",
    "will",
    "with",
    "have",
    "policy",
    "covered",
    "cover",
    "this",
    "that",
    "can",
    "get",
    "any",
    "there",
}


def retrieve(db: Session, policy_id: uuid.UUID, question: str, k: int) -> list[PolicyChunk]:
    """Hybrid retrieval: vector similarity plus exact keyword hits, de-duplicated."""
    [qvec] = get_embedder().embed([question])
    vector_hits = db.scalars(
        select(PolicyChunk)
        .where(PolicyChunk.policy_id == policy_id)
        .order_by(PolicyChunk.embedding.cosine_distance(qvec))
        .limit(k)
    ).all()
    terms = [t for t in re.findall(r"[a-z]{4,}", question.lower()) if t not in _STOP][:5]
    keyword_hits = (
        db.scalars(
            select(PolicyChunk)
            .where(PolicyChunk.policy_id == policy_id, or_(*[PolicyChunk.content.ilike(f"%{t}%") for t in terms]))
            .order_by(PolicyChunk.chunk_index)
            .limit(3)
        ).all()
        if terms
        else []
    )
    seen: dict[uuid.UUID, PolicyChunk] = {}
    for chunk in [*keyword_hits, *vector_hits]:
        seen.setdefault(chunk.id, chunk)
    return list(seen.values())[: k + 2]


def ask(db: Session, policy: Policy, user_id: uuid.UUID, question: str) -> QaMessage:
    chunks = retrieve(db, policy.id, question, get_settings().rag_top_k)
    labelled = {f"C{i}": c for i, c in enumerate(chunks, start=1)}
    context = [
        (cid, f"(page {c.page}{', ' + c.section if c.section else ''}) {c.content}") for cid, c in labelled.items()
    ]
    try:
        raw = get_ai_gateway().answer_question(question, structured_view(policy), context)
    except AIProviderError as exc:
        raise AppError("ai_unavailable", "The assistant is unavailable right now. Please try again.", 503) from exc

    cited = [labelled[c] for c in raw.get("citations", []) if isinstance(c, str) and c in labelled]
    answerable = bool(raw.get("answerable")) and bool(cited)
    confidence = raw.get("confidence") if raw.get("confidence") in ("high", "medium", "low") else "low"
    answer = str(raw.get("answer") or "").strip()
    if not answerable or not answer:
        # Post-validation: an answer that cites nothing from the document is not shown as fact.
        answerable, answer, confidence, cited = False, NOT_FOUND, "low", []

    message = QaMessage(
        provider=get_ai_gateway().provider_name,
        policy_id=policy.id,
        user_id=user_id,
        question=question,
        answer=answer,
        answerable=answerable,
        confidence=confidence,
        citations=[{"page": c.page, "section": c.section, "excerpt": _excerpt(c.content)} for c in cited],
    )
    db.add(message)
    db.commit()
    return message


def summary_excerpts(db: Session, policy_id: uuid.UUID, limit: int = 12) -> str:
    chunks = db.scalars(
        select(PolicyChunk).where(PolicyChunk.policy_id == policy_id).order_by(PolicyChunk.chunk_index).limit(limit)
    ).all()
    return "\n\n".join(f"(page {c.page}) {c.content}" for c in chunks) or "(no document text)"


def _excerpt(text: str, limit: int = 280) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rsplit(" ", 1)[0] + "…"
