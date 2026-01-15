from __future__ import annotations
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.loan import LoanDocument
from app.db.crud.loanee import get_loanee_by_email


def create_document(
    db: Session,
    *,
    organization_id: UUID,
    loanee_id: UUID,
    loan_id: UUID | None,
    document_type: str,
    bucket: str,
    uri: str,
    content_type: str | None,
    size_bytes: int | None,
    checksum: str | None,
) -> LoanDocument:
    doc = LoanDocument(
        organization_id=organization_id,
        loanee_id=loanee_id,
        loan_id=loan_id,
        document_type=document_type,
        bucket=bucket,
        uri=uri,
        content_type=content_type,
        size_bytes=size_bytes,
        checksum=checksum,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def list_documents_for_loanee(db: Session, *, organization_id: UUID, loanee_id: UUID) -> list[LoanDocument]:
    return (
        db.query(LoanDocument)
        .filter(LoanDocument.organization_id == organization_id)
        .filter(LoanDocument.loanee_id == loanee_id)
        .order_by(LoanDocument.id.desc())
        .all()
    )
    
def list_documents_for_loan(db: Session, *, organization_id: UUID, loan_id: UUID) -> list[LoanDocument]:
    return (
        db.query(LoanDocument)
        .filter(LoanDocument.organization_id == organization_id)
        .filter(LoanDocument.loan_id == loan_id)
        .order_by(LoanDocument.id.desc())
        .all()
    )


def list_documents_for_loanee_email(db: Session, *, organization_id: UUID, email: str) -> list[LoanDocument]:
    loanee = get_loanee_by_email(db, organization_id=organization_id, email=email)
    if not loanee:
        return []
    return (
        db.query(LoanDocument)
        .filter(LoanDocument.organization_id == organization_id)
        .filter(LoanDocument.loanee_id == loanee.id)
        .order_by(LoanDocument.id.desc())
        .all()
    )


def get_document(db: Session, *, organization_id: UUID, loanee_id: UUID, document_id: UUID) -> LoanDocument | None:
    return (
        db.query(LoanDocument)
        .filter(LoanDocument.organization_id == organization_id)
        .filter(LoanDocument.loanee_id == loanee_id)
        .filter(LoanDocument.id == document_id)
        .first()
    )


def get_document_for_loan(db: Session, *, organization_id: UUID, loan_id: UUID, document_id: UUID) -> LoanDocument | None:
    return (
        db.query(LoanDocument)
        .filter(LoanDocument.organization_id == organization_id)
        .filter(LoanDocument.loan_id == loan_id)
        .filter(LoanDocument.id == document_id)
        .first()
    )
