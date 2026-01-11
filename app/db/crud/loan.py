from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.loan import Loan, Loanee
from app.db.schemas.loan import LoanCreate, LoaneeCreate
from app.db.crud.organization import get_or_create_default_organization
from datetime import date
from typing import Iterable, Optional
from app.db.models.loan import LoanStatus


def create_loanee(db: Session, loanee: LoaneeCreate) -> Loanee:
    org = get_or_create_default_organization(db)
    db_loanee = Loanee(
        organization_id=org.id,
        full_name=loanee.full_name,
        email=loanee.email,
        phone_number=loanee.phone_number,
        address=loanee.address,
        user_id=loanee.user_id,
    )
    db.add(db_loanee)
    db.commit()
    db.refresh(db_loanee)
    return db_loanee


def get_loanee(db: Session, loanee_id: int) -> Loanee | None:
    return db.query(Loanee).filter(Loanee.id == loanee_id).first()


def create_loan(db: Session, loan: LoanCreate, *, total_payable) -> Loan:
    org = get_or_create_default_organization(db)
    db_loan = Loan(
        organization_id=org.id,
        loanee_id=loan.loanee_id,
        amount=loan.amount,
        loan_term_weeks=loan.loan_term_weeks,
        surcharge=loan.surcharge,
        penalty=loan.penalty,
        due_date=loan.due_date,
        auto_debit_enabled=loan.auto_debit_enabled,
        total_payable=total_payable,
    )
    db.add(db_loan)
    db.commit()
    db.refresh(db_loan)
    return db_loan


def get_loan(db: Session, loan_id: int) -> Loan | None:
    return db.query(Loan).filter(Loan.id == loan_id).first()


def list_loans(
    db: Session,
    *,
    status: Optional[LoanStatus] = None,
    due_from: Optional[date] = None,
    due_to: Optional[date] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Loan]:
    org = get_or_create_default_organization(db)
    q = db.query(Loan).filter(Loan.organization_id == org.id)
    if status is not None:
        q = q.filter(Loan.status == status)
    if due_from is not None:
        q = q.filter(Loan.due_date >= due_from)
    if due_to is not None:
        q = q.filter(Loan.due_date <= due_to)
    return q.order_by(Loan.id.desc()).offset(offset).limit(limit).all()
