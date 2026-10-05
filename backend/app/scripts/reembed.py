"""Re-embed every stored chunk with the current EMBEDDING_PROVIDER: `python -m app.scripts.reembed`.

Required after switching embedding model (e.g. hashing/openai → local bge-m3), because vectors from
different models are not comparable. Processes in batches and commits per policy.
"""

from sqlalchemy import select

from app.ai.embeddings import get_embedder
from app.core.db import SessionLocal
from app.models import PolicyChunk


def main(batch: int = 64) -> None:
    embedder = get_embedder()
    with SessionLocal() as db:
        policy_ids = db.scalars(select(PolicyChunk.policy_id).distinct()).all()
        total = 0
        for policy_id in policy_ids:
            chunks = db.scalars(select(PolicyChunk).where(PolicyChunk.policy_id == policy_id)).all()
            for i in range(0, len(chunks), batch):
                part = chunks[i : i + batch]
                for chunk, vector in zip(part, embedder.embed([c.content for c in part]), strict=True):
                    chunk.embedding = vector
            db.commit()
            total += len(chunks)
        print(f"re-embedded {total} chunks across {len(policy_ids)} policies")


if __name__ == "__main__":
    main()
