from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.crud.organization import get_or_create_default_organization
from app.db.models.loan import LoanDocument


def _default_org_id(db: Session) -> int:
    return get_or_create_default_organization(db).id


def create_document(
    db: Session,
    *,
    loanee_id: int,
    loan_id: int | None,
    document_type: str,
    bucket: str,
    uri: str,
    content_type: str | None,
    size_bytes: int | None,
    checksum: str | None,
) -> LoanDocument:
    org_id = _default_org_id(db)
    doc = LoanDocument(
        organization_id=org_id,
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


def list_documents_for_loanee(db: Session, loanee_id: int) -> list[LoanDocument]:
    org_id = _default_org_id(db)
    return (
        db.query(LoanDocument)
        .filter(LoanDocument.organization_id == org_id)
        .filter(LoanDocument.loanee_id == loanee_id)
        .order_by(LoanDocument.id.desc())
        .all()
    )


def get_document(db: Session, *, loanee_id: int, document_id: int) -> LoanDocument | None:
    org_id = _default_org_id(db)
    return (
        db.query(LoanDocument)
        .filter(LoanDocument.organization_id == org_id)
        .filter(LoanDocument.loanee_id == loanee_id)
        .filter(LoanDocument.id == document_id)
        .first()
    )
