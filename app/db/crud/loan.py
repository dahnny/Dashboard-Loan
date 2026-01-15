from __future__ import annotations

from sqlalchemy.orm import Session
from uuid import UUID

from app.db.crud.loanee import create_loanee, get_loanee_by_email
from app.db.models.loan import Loan, Loanee
from app.db.models.organization import Organization
from app.db.schemas.loan import LoanCreate, LoaneeCreate
from app.db.crud.organization import get_organization_by_email
from datetime import date
from typing import Optional
from app.db.models.loan import LoanStatus



def create_loan(db: Session, loan: LoanCreate, *, total_payable, organization: Organization) -> Loan:
    payload = LoaneeCreate(
        full_name=loan.full_name,
        email=loan.email,
        phone_number=loan.phone_number,
        address=loan.address,
    )
    loanee = get_loanee_by_email(db, organization_id=organization.id, email=loan.email)
    if not loanee:
        loanee = create_loanee(db, organization=organization, payload=payload)
    db_loan = Loan(
        organization_id=organization.id,
        loanee_id=loanee.id,
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


def get_loan(db: Session, loan_id: UUID) -> Loan | None:
    return db.query(Loan).filter(Loan.id == loan_id).first()


def list_loans(
    db: Session,
    *,
    organization_id: str,
    status: Optional[LoanStatus] = None,
    due_from: Optional[date] = None,
    due_to: Optional[date] = None,
    loan_term_weeks: Optional[int] = None,
    loanee_email: Optional[str] = None,
    payment_due: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Loan]:
    q = db.query(Loan).filter(Loan.organization_id == organization_id)
    if status is not None:
        q = q.filter(Loan.status == status)
    if payment_due:
        q = q.filter(Loan.status == LoanStatus.due)
    if due_from is not None:
        q = q.filter(Loan.due_date >= due_from)
    if due_to is not None:
        q = q.filter(Loan.due_date <= due_to)
    if loan_term_weeks is not None:
        q = q.filter(Loan.loan_term_weeks == loan_term_weeks)
    if loanee_email:
        q = q.join(Loanee, Loan.loanee_id == Loanee.id).filter(Loanee.email.ilike(loanee_email))
    return q.order_by(Loan.id.desc()).offset(offset).limit(limit).all()


def list_loans_for_organization_email(
    db: Session,
    *,
    organization_email: str,
    limit: int = 50,
    offset: int = 0,
) -> list[Loan]:
    org = get_organization_by_email(db, organization_email)
    if not org:
        return []
    return (
        db.query(Loan)
        .filter(Loan.organization_id == org.id)
        .order_by(Loan.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def list_loans_for_organization_id(
    db: Session,
    *,
    organization_id: str,
    limit: int = 50,
    offset: int = 0,
) -> list[Loan]:
    return (
        db.query(Loan)
        .filter(Loan.organization_id == organization_id)
        .order_by(Loan.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


