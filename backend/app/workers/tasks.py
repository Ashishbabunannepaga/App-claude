import uuid

from fastapi import BackgroundTasks

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.processing.pipeline import process_document
from app.workers.celery_app import celery_app


def run_process_document(document_id: str) -> None:
    with SessionLocal() as db:
        process_document(db, uuid.UUID(document_id))


@celery_app.task(name="process_document", autoretry_for=(ConnectionError,), max_retries=3, retry_backoff=True)
def process_document_task(document_id: str) -> None:
    run_process_document(document_id)


def enqueue_process_document(document_id: uuid.UUID, background: BackgroundTasks) -> None:
    """Celery in staging/production; FastAPI background task when TASKS_EAGER (dev/test)."""
    if get_settings().tasks_eager:
        background.add_task(run_process_document, str(document_id))
    else:
        process_document_task.delay(str(document_id))


@celery_app.task(name="purge_deleted_accounts")
def purge_deleted_accounts_task() -> int:
    from app.services.account_service import purge_deleted_accounts

    with SessionLocal() as db:
        return purge_deleted_accounts(db)


celery_app.conf.beat_schedule = {
    "purge-deleted-accounts": {"task": "purge_deleted_accounts", "schedule": 6 * 3600},
    # TODO(Week 7): "renewal-reminders" daily at 09:00 IST.
}
