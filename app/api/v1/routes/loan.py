from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.db.crud.loan import create_loan, create_loanee, get_loan, list_loans
from app.db.models.loan import LoanStatus
from app.db.schemas.loan import (
    LoanCreate,
    LoanResponse,
    LoanStatusTransitionRequest,
    LoaneeCreate,
    LoaneeResponse,
)
from app.exceptions.loan_exceptions import InvalidLoanTransitionError
from app.services.loan_service import LoanService
from typing import Optional
from datetime import date
from app.core.redis import get_redis
import json


router = APIRouter(
    prefix="/loans",
    tags=["loans"],
    dependencies=[Depends(require_roles("admin", "staff"))],
)


@router.post(
    "/loanees", response_model=LoaneeResponse, status_code=status.HTTP_201_CREATED
)
def create_new_loanee(
    payload: LoaneeCreate, db: Session = Depends(get_db)
) -> LoaneeResponse:
    return create_loanee(db, payload)


@router.post("/", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
def create_new_loan(payload: LoanCreate, db: Session = Depends(get_db)) -> LoanResponse:
    service = LoanService(db)
    total_payable = service.compute_total_payable(
        amount=payload.amount, surcharge=payload.surcharge, penalty=payload.penalty
    )
    if payload.due_date is None:
        start = payload.start_date or date.today()
        due_date = start + service.term_to_timedelta(weeks=payload.loan_term_weeks)
        payload.due_date = due_date
    return create_loan(db, payload, total_payable=total_payable)


@router.post("/{loan_id}/transition", response_model=LoanResponse)
def transition_loan_status(
    loan_id: int,
    payload: LoanStatusTransitionRequest,
    db: Session = Depends(get_db),
) -> LoanResponse:
    loan = get_loan(db, loan_id)
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found"
        )

    service = LoanService(db)
    try:
        return service.transition_status(
            loan=loan,
            to_status=LoanStatus(payload.to_status),
            actor_user_id=payload.actor_user_id,
            message=payload.message,
        )
    except InvalidLoanTransitionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=list[LoanResponse])
def list_loans_endpoint(
    status: Optional[LoanStatus] = None,
    due_from: Optional[date] = None,
    due_to: Optional[date] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> list[LoanResponse]:
    return list_loans(db, status=status, due_from=due_from, due_to=due_to, limit=limit, offset=offset)


@router.get("/due-today", response_model=list[LoanResponse])
def due_today_endpoint(db: Session = Depends(get_db)) -> list[LoanResponse]:
    today = date.today()
    cache_key = f"due_today:{today.isoformat()}"
    r = get_redis()
    cached = r.get(cache_key)
    if cached:
        return [LoanResponse(**obj) for obj in json.loads(cached)]
    items = list_loans(db, status=LoanStatus.due, due_from=today, due_to=today, limit=500, offset=0)
    payload = [LoanResponse.from_orm(x).dict() for x in items]
    r.setex(cache_key, 60, json.dumps(payload))
    return items
