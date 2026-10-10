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
from app.models import Policy, PolicyChunk, PolicyClause, QaMessage
from app.processing.glossary import english_terms
from app.services.policy_service import structured_view

DISCLAIMERS = {
    "en": "Based on your policy document. This is not advice — please confirm with your insurer "
    "before making a claim or financial decision.",
    "hi": "यह आपके पॉलिसी दस्तावेज़ पर आधारित है, सलाह नहीं। क्लेम या कोई वित्तीय निर्णय लेने से पहले " "अपनी बीमा कंपनी से पुष्टि करें।",
}
NOT_FOUND_TEXT = {
    "en": "I couldn't find a clear answer to this in your policy document. "
    "Please check the full policy wording or contact your insurer.",
    "hi": "इसका स्पष्ट उत्तर आपके पॉलिसी दस्तावेज़ में नहीं मिला। कृपया पूरी पॉलिसी शर्तें देखें या " "अपनी बीमा कंपनी से संपर्क करें।",
}
DISCLAIMER = DISCLAIMERS["en"]
NOT_FOUND = NOT_FOUND_TEXT["en"]


def disclaimer(language: str) -> str:
    return DISCLAIMERS.get(language, DISCLAIMER)


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
    """Hybrid retrieval: vector similarity plus exact keyword hits, de-duplicated.

    Indian-language questions are expanded with English glossary terms, since wordings are English."""
    question = f"{question} {english_terms(question)}".strip()
    qvec = get_embedder().embed_query(question)
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


def related_clauses(db: Session, policy_id: uuid.UUID, question: str, limit: int = 2) -> list[dict]:
    """Typed clauses sharing the most distinct terms with the question — shown under the answer."""
    expanded = f"{question} {english_terms(question)}".lower()
    terms = {t for t in re.findall(r"[a-z][a-z\-]{3,}", expanded) if t not in _STOP}
    if not terms:
        return []
    clauses = db.scalars(select(PolicyClause).where(PolicyClause.policy_id == policy_id)).all()
    scored = sorted(
        ((len({t for t in terms if t in c.text.lower()}), -c.order, c) for c in clauses),
        key=lambda x: x[:2],
        reverse=True,
    )
    best = scored[0][0] if scored else 0
    # Only the strongest matches: a clause sharing one generic word ("treatment") is noise.
    return [
        {"type": c.clause_type, "title": c.title, "text": c.text, "page": c.page}
        for score, _, c in scored[:limit]
        if score > 0 and score == best
    ]


def ask(db: Session, policy: Policy, user_id: uuid.UUID, question: str, language: str = "en") -> QaMessage:
    chunks = retrieve(db, policy.id, question, get_settings().rag_top_k)
    labelled = {f"C{i}": c for i, c in enumerate(chunks, start=1)}
    context = [
        (cid, f"(page {c.page}{', ' + c.section if c.section else ''}) {c.content}") for cid, c in labelled.items()
    ]
    try:
        raw = get_ai_gateway().answer_question(question, structured_view(policy), context, language)
    except AIProviderError as exc:
        raise AppError("ai_unavailable", "The assistant is unavailable right now. Please try again.", 503) from exc

    cited = [labelled[c] for c in raw.get("citations", []) if isinstance(c, str) and c in labelled]
    answerable = bool(raw.get("answerable")) and bool(cited)
    confidence = raw.get("confidence") if raw.get("confidence") in ("high", "medium", "low") else "low"
    answer = str(raw.get("answer") or "").strip()
    if not answerable or not answer:
        # Post-validation: an answer that cites nothing from the document is not shown as fact.
        answerable, answer, confidence, cited = False, NOT_FOUND_TEXT.get(language, NOT_FOUND), "low", []

    message = QaMessage(
        provider=get_ai_gateway().provider_name,
        policy_id=policy.id,
        user_id=user_id,
        question=question,
        answer=answer,
        answerable=answerable,
        confidence=confidence,
        citations=[{"page": c.page, "section": c.section, "excerpt": _excerpt(c.content)} for c in cited],
        related_clauses=related_clauses(db, policy.id, question) if answerable else [],
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
