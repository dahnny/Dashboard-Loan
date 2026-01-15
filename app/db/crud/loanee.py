from __future__ import annotations
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.crud.organization import get_or_create_default_organization
from app.db.models.loan import Loan, Loanee
from app.db.schemas.loan import LoaneeCreate, LoaneeUpdate


def _default_org_id(db: Session) -> UUID:
    return get_or_create_default_organization(db).id


def create_loanee(db: Session, payload: LoaneeCreate) -> Loanee | None:
    org_id = _default_org_id(db)
    existing_loanee = get_loanee_by_email(db, payload.email)
    if existing_loanee:
        return None
    loanee = Loanee(
        organization_id=org_id,
        full_name=payload.full_name,
        email=payload.email,
        phone_number=payload.phone_number,
        address=payload.address,
    )
    db.add(loanee)
    db.commit()
    db.refresh(loanee)
    return loanee


def list_loanees(db: Session, *, limit: int = 100, offset: int = 0) -> list[Loanee]:
    org_id = _default_org_id(db)
    return (
        db.query(Loanee)
        .filter(Loanee.organization_id == org_id)
        .order_by(Loanee.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_loanee(db: Session, loanee_id: UUID) -> Loanee | None:
    org_id = _default_org_id(db)
    return (
        db.query(Loanee)
        .filter(Loanee.organization_id == org_id)
        .filter(Loanee.id == loanee_id)
        .first()
    )

def get_loanee_by_email(db: Session, email: str) -> Loanee | None:
    org_id = _default_org_id(db)
    return (
        db.query(Loanee)
        .filter(Loanee.organization_id == org_id)
        .filter(Loanee.email == email)
        .first()
    )

def update_loanee(db: Session, loanee: Loanee, payload: LoaneeUpdate) -> Loanee:
    data = payload.dict(exclude_unset=True)
    for key, value in data.items():
        setattr(loanee, key, value)
    db.add(loanee)
    db.commit()
    db.refresh(loanee)
    return loanee


def delete_loanee(db: Session, loanee: Loanee) -> None:
    db.delete(loanee)
    db.commit()


def list_loans_for_loanee(db: Session, loanee_id: UUID) -> list[Loan]:
    org_id = _default_org_id(db)
    return (
        db.query(Loan)
        .filter(Loan.organization_id == org_id)
        .filter(Loan.loanee_id == loanee_id)
        .order_by(Loan.id.desc())
        .all()
    )
