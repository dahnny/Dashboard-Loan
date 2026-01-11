from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import UploadFile, File
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.config import settings
from app.db.crud.document import create_document, get_document, list_documents_for_loanee
from app.db.crud.loanee import (
    create_loanee,
    delete_loanee,
    get_loanee,
    list_loanees,
    list_loans_for_loanee,
    update_loanee,
)
from app.db.schemas.loan import (
    LoanDocumentResponse,
    LoanResponse,
    LoaneeCreate,
    LoaneeResponse,
    LoaneeUpdate,
    SignedUrlResponse,
)
from app.integrations.supabase_storage import create_signed_url, sha256_hex, upload_object


router = APIRouter(prefix="/loanees", tags=["loanees"], dependencies=[Depends(require_roles("admin", "staff"))])


@router.post("/", response_model=LoaneeResponse, status_code=status.HTTP_201_CREATED)
def create_loanee_endpoint(payload: LoaneeCreate, db: Session = Depends(get_db)) -> LoaneeResponse:
    return create_loanee(db, payload)


@router.get("/", response_model=list[LoaneeResponse])
def list_loanees_endpoint(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> list[LoaneeResponse]:
    return list_loanees(db, limit=limit, offset=offset)


@router.get("/{loanee_id}", response_model=LoaneeResponse)
def get_loanee_endpoint(loanee_id: int, db: Session = Depends(get_db)) -> LoaneeResponse:
    loanee = get_loanee(db, loanee_id)
    if not loanee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loanee not found")
    return loanee


@router.patch("/{loanee_id}", response_model=LoaneeResponse)
def update_loanee_endpoint(
    loanee_id: int,
    payload: LoaneeUpdate,
    db: Session = Depends(get_db),
) -> LoaneeResponse:
    loanee = get_loanee(db, loanee_id)
    if not loanee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loanee not found")
    return update_loanee(db, loanee, payload)


@router.delete("/{loanee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_loanee_endpoint(loanee_id: int, db: Session = Depends(get_db)) -> None:
    loanee = get_loanee(db, loanee_id)
    if not loanee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loanee not found")
    delete_loanee(db, loanee)
    return None


@router.get("/{loanee_id}/loans", response_model=list[LoanResponse])
def list_loanee_loans_endpoint(loanee_id: int, db: Session = Depends(get_db)) -> list[LoanResponse]:
    # Ensure loanee exists in this org
    loanee = get_loanee(db, loanee_id)
    if not loanee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loanee not found")
    return list_loans_for_loanee(db, loanee_id)


@router.post("/{loanee_id}/documents/upload", response_model=LoanDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document_endpoint(
    loanee_id: int,
    document_type: str,
    loan_id: int | None = None,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> LoanDocumentResponse:
    loanee = get_loanee(db, loanee_id)
    if not loanee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loanee not found")

    content = await file.read()
    checksum = sha256_hex(content)
    bucket = settings.supabase_storage_bucket

    # Keep object keys stable and non-guessable enough: namespace by loanee + date + checksum.
    safe_name = (file.filename or "upload").replace("..", ".").replace("/", "_").replace("\\", "_")
    object_path = f"loanees/{loanee_id}/{datetime.utcnow().strftime('%Y%m%d')}/{checksum}_{safe_name}"

    await upload_object(
        bucket=bucket,
        object_path=object_path,
        content=content,
        content_type=file.content_type,
    )

    doc = create_document(
        db,
        loanee_id=loanee_id,
        loan_id=loan_id,
        document_type=document_type,
        bucket=bucket,
        uri=object_path,
        content_type=file.content_type,
        size_bytes=len(content),
        checksum=checksum,
    )
    return doc


@router.get("/{loanee_id}/documents", response_model=list[LoanDocumentResponse])
def list_documents_endpoint(loanee_id: int, db: Session = Depends(get_db)) -> list[LoanDocumentResponse]:
    loanee = get_loanee(db, loanee_id)
    if not loanee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loanee not found")
    return list_documents_for_loanee(db, loanee_id)


@router.get("/{loanee_id}/documents/{document_id}/signed-url", response_model=SignedUrlResponse)
async def get_document_signed_url_endpoint(
    loanee_id: int,
    document_id: int,
    expires_in: int = 60,
    db: Session = Depends(get_db),
) -> SignedUrlResponse:
    doc = get_document(db, loanee_id=loanee_id, document_id=document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    signed = await create_signed_url(bucket=doc.bucket, object_path=doc.uri, expires_in=expires_in)
    return SignedUrlResponse(signed_url=signed)
