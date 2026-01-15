from __future__ import annotations
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.db.models.organization import Organization
from app.db.models.loan import Loan, Loanee
from app.db.schemas.loan import LoaneeCreate, LoaneeUpdate


def _org_id(organization: Organization) -> UUID:
    return organization.id


def create_loanee(db: Session, *, organization: Organization, payload: LoaneeCreate) -> Loanee | None:
    org_id = _org_id(organization)
    existing_loanee = get_loanee_by_email(db, organization_id=org_id, email=payload.email)
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


def list_loanees(db: Session, *, organization_id: UUID, limit: int = 100, offset: int = 0) -> list[Loanee]:
    org_id = organization_id
    return (
        db.query(Loanee)
        .filter(Loanee.organization_id == org_id)
        .order_by(Loanee.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_loanee(db: Session, *, organization_id: UUID, loanee_id: UUID) -> Loanee | None:
    org_id = organization_id
    return (
        db.query(Loanee)
        .filter(Loanee.organization_id == org_id)
        .filter(Loanee.id == loanee_id)
        .first()
    )

def get_loanee_by_email(db: Session, *, organization_id: UUID, email: str) -> Loanee | None:
    org_id = organization_id
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


def list_loans_for_loanee(db: Session, *, organization_id: UUID, loanee_id: UUID) -> list[Loan]:
    org_id = organization_id
    return (
        db.query(Loan)
        .filter(Loan.organization_id == org_id)
        .filter(Loan.loanee_id == loanee_id)
        .order_by(Loan.id.desc())
        .all()
    )


def list_loans_for_loanee_email(db: Session, *, organization_id: UUID, email: str) -> list[Loan]:
    loanee = get_loanee_by_email(db, organization_id=organization_id, email=email)
    if not loanee:
        return []
    return list_loans_for_loanee(db, organization_id=organization_id, loanee_id=loanee.id)


def list_loanees_with_loans(db: Session, *, organization_id: UUID, limit: int = 100, offset: int = 0) -> list[Loanee]:
    org_id = organization_id
    return (
        db.query(Loanee)
        .options(joinedload(Loanee.loans))
        .filter(Loanee.organization_id == org_id)
        .order_by(Loanee.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
