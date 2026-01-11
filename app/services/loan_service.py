from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.db.models.loan import AuditLog, Loan, LoanStatus, Payment
from app.exceptions.loan_exceptions import InvalidLoanTransitionError


class LoanService:
    _ALLOWED_TRANSITIONS: dict[LoanStatus, set[LoanStatus]] = {
        LoanStatus.not_due: {LoanStatus.due, LoanStatus.paid},
        LoanStatus.due: {LoanStatus.paid, LoanStatus.defaulted},
        LoanStatus.paid: set(),
        LoanStatus.defaulted: set(),
    }

    def __init__(self, db: Session):
        self._db = db

    def compute_total_payable(self, *, amount: Decimal, surcharge: Decimal, penalty: Decimal) -> Decimal:
        return (amount or Decimal("0")) + (surcharge or Decimal("0")) + (penalty or Decimal("0"))

    def term_to_timedelta(self, *, weeks: int):
        from datetime import timedelta
        return timedelta(weeks=weeks)

    def assert_can_transition(self, *, from_status: LoanStatus, to_status: LoanStatus) -> None:
        allowed = self._ALLOWED_TRANSITIONS.get(from_status, set())
        if to_status not in allowed:
            raise InvalidLoanTransitionError(from_status=from_status.value, to_status=to_status.value)

    def transition_status(
        self,
        *,
        loan: Loan,
        to_status: LoanStatus,
        actor_user_id: int | None = None,
        message: str | None = None,
    ) -> Loan:
        from_status = loan.status
        if from_status == to_status:
            return loan

        self.assert_can_transition(from_status=from_status, to_status=to_status)

        loan.status = to_status

        audit = AuditLog(
            actor_user_id=actor_user_id,
            loan_id=loan.id,
            action="loan_status_transition",
            from_status=from_status,
            to_status=to_status,
            message=message,
        )
        self._db.add(audit)
        if to_status == LoanStatus.paid:
            payment = Payment(
                organization_id=loan.organization_id,
                loan_id=loan.id,
                amount=loan.total_payable,
                reference="manual-status-update",
                source="manual",
            )
            self._db.add(payment)
        self._db.add(loan)
        self._db.commit()
        self._db.refresh(loan)
        return loan
