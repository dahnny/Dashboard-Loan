from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.db.crud.loan import get_loan
from app.db.models.loan import DirectDebitMandate, Loanee
from app.db.schemas.loan import LoanResponse
from app.integrations.mono import create_mandate_link
from app.services.direct_debit_service import DirectDebitService


router = APIRouter(prefix="/dd", tags=["direct-debit"], dependencies=[Depends(require_roles("admin", "staff"))])


@router.post("/mono/mandates/start")
async def start_mono_mandate(loanee_id: int, db: Session = Depends(get_db)) -> dict:
    loanee: Loanee = db.query(Loanee).get(loanee_id)
    if not loanee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loanee not found")
    if not loanee.email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Loanee requires email for Mono mandate")
    link = await create_mandate_link(customer_email=loanee.email, customer_name=loanee.full_name)
    return {"link": link}


@router.post("/schedules")
def create_debit_schedule(
    loan_id: int,
    mandate_id: int,
    number_of_debits: int = 1,
    first_due_date: date | None = None,
    db: Session = Depends(get_db),
):
    loan = get_loan(db, loan_id)
    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
    mandate = db.query(DirectDebitMandate).get(mandate_id)
    if not mandate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mandate not found")
    service = DirectDebitService(db)
    sched = service.create_schedule(loan=loan, mandate=mandate, number_of_debits=number_of_debits, first_due_date=first_due_date)
    return {"schedule_id": sched.id}
