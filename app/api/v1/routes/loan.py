from __future__ import annotations
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_organization, get_db
from app.db.crud.document import (
    create_document,
    get_document_for_loan,
    list_documents_for_loan,
    list_documents_for_loanee_email,
)
from app.db.crud.loan import (
    create_loan,
    get_loan,
    list_loans,
    list_loans_for_organization_id,
)
from app.db.crud.loan import list_loans_for_organization_email
from app.db.crud.loanee import get_loanee, list_loans_for_loanee_email
from app.db.models.loan import LoanStatus
from app.core.config import settings
from app.db.schemas.loan import (
    LoanCreate,
    LoanDocumentResponse,
    LoanResponse,
    LoanStatusTransitionRequest,
    LoaneeCreate,
    LoaneeResponse,
    SignedUrlResponse,
)
from app.exceptions.loan_exceptions import InvalidLoanTransitionError
from app.integrations.supabase_storage import (
    create_signed_url,
    sha256_hex,
    upload_object,
)
from app.services.loan_service import LoanService
from typing import Optional
from datetime import date, datetime
from app.core.redis import get_redis
import json


router = APIRouter(
    prefix="/loans",
    tags=["loans"],
    dependencies=[Depends(get_current_organization)],
)


@router.post("/", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
def create_new_loan(
    payload: LoanCreate,
    db: Session = Depends(get_db),
    organization=Depends(get_current_organization),
) -> LoanResponse:
    service = LoanService(db)
    total_payable = service.compute_total_payable(
        amount=payload.amount, surcharge=payload.surcharge, penalty=payload.penalty
    )
    if payload.due_date is None:
        start = payload.start_date or date.today()
        due_date = start + service.term_to_timedelta(weeks=payload.loan_term_weeks)
        payload.due_date = due_date
    return create_loan(db, payload, total_payable=total_payable, organization=organization)


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
            message=payload.message,
        )
    except InvalidLoanTransitionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=list[LoanResponse])
def list_loans_endpoint(
    status: Optional[LoanStatus] = None,
    due_from: Optional[date] = None,
    due_to: Optional[date] = None,
    loan_term_weeks: Optional[int] = None,
    loanee_email: Optional[str] = None,
    payment_due: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    organization=Depends(get_current_organization),
) -> list[LoanResponse]:
    return list_loans(
        db,
        organization_id=str(organization.id),
        status=status,
        due_from=due_from,
        due_to=due_to,
        loan_term_weeks=loan_term_weeks,
        loanee_email=loanee_email,
        payment_due=payment_due,
        limit=limit,
        offset=offset,
    )


@router.get("/by-loanee", response_model=list[LoanResponse])
def list_loans_by_loanee_email_endpoint(
    email: str,
    db: Session = Depends(get_db),
    organization=Depends(get_current_organization),
) -> list[LoanResponse]:
    return list_loans_for_loanee_email(db, organization_id=organization.id, email=email)


@router.get("/by-organization", response_model=list[LoanResponse])
def list_loans_by_organization_email_endpoint(
    email: str,
    db: Session = Depends(get_db),
) -> list[LoanResponse]:
    return list_loans_for_organization_email(db, organization_email=email)


@router.get("/by-organization-id", response_model=list[LoanResponse])
def list_loans_by_organization_id_endpoint(
    organization_id: UUID,
    db: Session = Depends(get_db),
) -> list[LoanResponse]:
    return list_loans_for_organization_id(db, organization_id=str(organization_id))


@router.get("/{loan_id}", response_model=LoanResponse)
def get_loan_endpoint(loan_id: UUID, db: Session = Depends(get_db)) -> LoanResponse:
    loan = get_loan(db, loan_id)
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found"
        )
    return loan


@router.get("/due-today", response_model=list[LoanResponse])
def due_today_endpoint(
    db: Session = Depends(get_db),
    organization=Depends(get_current_organization),
) -> list[LoanResponse]:
    today = date.today()
    cache_key = f"due_today:{organization.id}:{today.isoformat()}"
    r = get_redis()
    cached = r.get(cache_key)
    if cached:
        return [LoanResponse(**obj) for obj in json.loads(cached)]
    items = list_loans(
        db,
        organization_id=str(organization.id),
        status=LoanStatus.due,
        due_from=today,
        due_to=today,
        limit=500,
        offset=0,
    )
    payload = [LoanResponse.from_orm(x).dict() for x in items]
    r.setex(cache_key, 60, json.dumps(payload))
    return items


@router.post(
    "/{loan_id}/documents/upload",
    response_model=LoanDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document_endpoint(
    document_type: str,
    loan_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    organization=Depends(get_current_organization),
) -> LoanDocumentResponse:
    loan = get_loan(db, loan_id)
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found"
        )
    if loan.is_document_uploaded:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document already uploaded for this loan",
        )

    content = await file.read()
    checksum = sha256_hex(content)
    bucket = settings.supabase_storage_bucket

    # Keep object keys stable and non-guessable enough: namespace by loanee + date + checksum.
    safe_name = (
        (file.filename or "upload")
        .replace("..", ".")
        .replace("/", "_")
        .replace("\\", "_")
    )
    object_path = f"loans/{loan_id}/{datetime.utcnow().strftime('%Y%m%d')}/{checksum}_{safe_name}"

    await upload_object(
        bucket=bucket,
        object_path=object_path,
        content=content,
        content_type=file.content_type,
    )

    doc = create_document(
        db,
        organization_id=organization.id,
        loanee_id=loan.loanee_id,
        loan_id=loan_id,
        document_type=document_type,
        bucket=bucket,
        uri=object_path,
        content_type=file.content_type,
        size_bytes=len(content),
        checksum=checksum,
    )
    # Mark loan as having document uploaded
    loan.is_document_uploaded = True
    db.add(loan)
    db.commit()

    return doc


@router.get("/{loan_id}/documents", response_model=list[LoanDocumentResponse])
def list_documents_endpoint(
    loan_id: UUID,
    db: Session = Depends(get_db),
    organization=Depends(get_current_organization),
) -> list[LoanDocumentResponse]:
    loan = get_loan(db, loan_id)
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found"
        )
    return list_documents_for_loan(db, organization_id=organization.id, loan_id=loan_id)


@router.get("/documents/by-loanee", response_model=list[LoanDocumentResponse])
def list_documents_by_loanee_email_endpoint(
    email: str,
    db: Session = Depends(get_db),
    organization=Depends(get_current_organization),
) -> list[LoanDocumentResponse]:
    return list_documents_for_loanee_email(db, organization_id=organization.id, email=email)

@router.get(
    "/{loan_id}/documents/{document_id}/signed-url", response_model=SignedUrlResponse
)
async def get_document_signed_url_endpoint(
    loan_id: UUID,
    document_id: UUID,
    expires_in: int = 60,
    db: Session = Depends(get_db),
    organization=Depends(get_current_organization),
) -> SignedUrlResponse:
    loan = get_loan(db, loan_id)
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found"
        )
    doc = get_document_for_loan(
        db, organization_id=organization.id, loan_id=loan_id, document_id=document_id
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    signed = await create_signed_url(
        bucket=doc.bucket, object_path=doc.uri, expires_in=expires_in
    )
    return SignedUrlResponse(signed_url=signed)
