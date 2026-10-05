"""Re-extract clauses for every processed document: `python -m app.scripts.backfill_clauses`.

Run after deploying a new clause-extraction version. Idempotent.
"""

import re

from sqlalchemy import delete, select

from app.core.db import SessionLocal
from app.models import Document, Policy, PolicyClause
from app.processing.clauses import extract_clauses

_PAGE = re.compile(r"\[Page \d+\]\n")


def main() -> None:
    with SessionLocal() as db:
        rows = db.execute(
            select(Policy, Document)
            .join(Document, Document.id == Policy.document_id)
            .where(Document.extracted_text.is_not(None))
        ).all()
        for policy, doc in rows:
            pages = [p for p in _PAGE.split(doc.extracted_text) if p.strip()]
            db.execute(delete(PolicyClause).where(PolicyClause.policy_id == policy.id))
            for c in extract_clauses(pages):
                db.add(
                    PolicyClause(
                        policy_id=policy.id,
                        clause_type=c.clause_type,
                        tags=c.tags,
                        title=c.title[:200],
                        text=c.text,
                        page=c.page,
                        section=(c.section or "")[:200] or None,
                        order=c.order,
                    )
                )
            db.commit()
        print(f"clauses rebuilt for {len(rows)} policies")


if __name__ == "__main__":
    main()
