from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
import uuid

from sqlalchemy.orm import Session

from app.db.models.loan import DirectDebitMandate, Loan, Payment
from app.db.models.debit import (
    DebitScheduleItem,
    RecurringDebitSchedule,
    ScheduleItemStatus,
)
from app.integrations.mono import charge_mandate


class DirectDebitService:
    def __init__(self, db: Session):
        self._db = db

    def create_schedule(
        self,
        *,
        loan: Loan,
        mandate: DirectDebitMandate,
        number_of_debits: int = 1,
        first_due_date: date | None = None,
    ) -> RecurringDebitSchedule:
        org_id = loan.organization_id
        total = Decimal(loan.total_payable)
        if number_of_debits <= 1:
            schedule_type = "single"
            per = total
            number_of_debits = 1
        else:
            schedule_type = "multiple"
            # split with last catching remainder cents
            per = (total / number_of_debits).quantize(Decimal("0.01"))

        sched = RecurringDebitSchedule(
            organization_id=org_id,
            loan_id=loan.id,
            mandate_id=mandate.id,
            schedule_type=schedule_type,
            number_of_debits=number_of_debits,
            total_amount=total,
            amount_per_debit=per,
        )
        self._db.add(sched)
        self._db.flush()

        start = first_due_date or date.today()
        remaining = total
        for i in range(number_of_debits):
            amt = per if i < number_of_debits - 1 else remaining
            remaining -= amt
            item = DebitScheduleItem(
                schedule_id=sched.id,
                due_date=start + timedelta(weeks=i),
                amount=amt,
                status=ScheduleItemStatus.pending,
                idempotency_key=str(uuid.uuid4()),
            )
            self._db.add(item)

        self._db.commit()
        self._db.refresh(sched)
        return sched

    async def execute_item(self, *, item: DebitScheduleItem) -> DebitScheduleItem:
        # lock item in processing state
        item.status = ScheduleItemStatus.processing
        self._db.add(item)
        self._db.commit()
        self._db.refresh(item)

        sched = self._db.query(RecurringDebitSchedule).get(item.schedule_id)
        loan = self._db.query(Loan).get(sched.loan_id)
        mandate = self._db.query(DirectDebitMandate).get(sched.mandate_id)

        amount_minor = int(Decimal(item.amount) * 100)
        try:
            resp = await charge_mandate(
                mandate_reference=mandate.mandate_reference,
                amount_minor=amount_minor,
                idempotency_key=item.idempotency_key,
            )
            txn_ref = str(resp.get("id") or resp.get("reference") or "")
            item.provider_txn_ref = txn_ref
            item.status = ScheduleItemStatus.paid
            item.attempts += 1

            # create payment record
            payment = Payment(
                organization_id=sched.organization_id,
                loan_id=loan.id,
                amount=item.amount,
                reference=txn_ref or "mono-dd",
                source="direct_debit",
            )
            self._db.add(payment)
            self._db.add(item)
            self._db.commit()
            self._db.refresh(item)
            return item
        except Exception as exc:  # noqa: BLE001 - capture integration errors
            item.attempts += 1
            item.status = ScheduleItemStatus.failed
            item.last_error = str(exc)
            self._db.add(item)
            self._db.commit()
            self._db.refresh(item)
            return item
