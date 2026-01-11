from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.core.celery_worker import celery_app
from app.db.session import SessionLocal
from app.db.models.debit import DebitScheduleItem, ScheduleItemStatus
from app.services.direct_debit_service import DirectDebitService


def _db() -> Session:
    return SessionLocal()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_due_debits(self):
    db = _db()
    try:
        today = date.today()
        items = (
            db.query(DebitScheduleItem)
            .filter(DebitScheduleItem.due_date <= today)
            .filter(DebitScheduleItem.status == ScheduleItemStatus.pending)
            .limit(100)
            .all()
        )
        service = DirectDebitService(db)
        for item in items:
            # We call async function via loop.run_until_complete in a quick-and-dirty way if needed
            import asyncio

            asyncio.get_event_loop().run_until_complete(service.execute_item(item=item))
    finally:
        db.close()
