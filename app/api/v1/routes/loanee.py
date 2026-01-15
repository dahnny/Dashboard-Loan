from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi import UploadFile, File
from sqlalchemy.orm import Session

from app.api.deps import get_current_organization, get_db
from app.core.config import settings
from app.db.crud.document import (
    create_document,
    get_document,
    list_documents_for_loanee,
)
from app.db.crud.loanee import (
    create_loanee,
    delete_loanee,
    get_loanee,
    list_loanees,
    list_loanees_with_loans,
    list_loans_for_loanee,
    update_loanee,
)
from app.db.schemas.loan import (
    LoanDocumentResponse,
    LoanResponse,
    LoaneeCreate,
    LoaneeResponse,
    LoaneeUpdate,
    LoaneeWithLoansResponse,
    SignedUrlResponse,
)
from app.integrations.supabase_storage import (
    create_signed_url,
    sha256_hex,
    upload_object,
)


router = APIRouter(
    prefix="/loanees", tags=["loanees"], dependencies=[Depends(get_current_organization)]
)


@router.post("/", response_model=LoaneeResponse, status_code=status.HTTP_201_CREATED)
def create_loanee_endpoint(
    payload: LoaneeCreate,
    db: Session = Depends(get_db),
    organization=Depends(get_current_organization),
) -> LoaneeResponse:
    loanee = create_loanee(db, organization=organization, payload=payload)
    if not loanee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Loanee with this email already exists",
        )
    return LoaneeResponse.from_orm(loanee)


@router.get("/", response_model=list[LoaneeResponse])
def list_loanees_endpoint(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    organization=Depends(get_current_organization),
) -> list[LoaneeResponse]:
    return list_loanees(db, organization_id=organization.id, limit=limit, offset=offset)


@router.get("/with-loans", response_model=list[LoaneeWithLoansResponse])
def list_loanees_with_loans_endpoint(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    organization=Depends(get_current_organization),
) -> list[LoaneeWithLoansResponse]:
    return list_loanees_with_loans(
        db, organization_id=organization.id, limit=limit, offset=offset
    )


@router.get("/{loanee_id}", response_model=LoaneeResponse)
def get_loanee_endpoint(
    loanee_id: UUID,
    db: Session = Depends(get_db),
    organization=Depends(get_current_organization),
) -> LoaneeResponse:
    loanee = get_loanee(db, organization_id=organization.id, loanee_id=loanee_id)
    if not loanee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Loanee not found"
        )
    return loanee


@router.patch("/{loanee_id}", response_model=LoaneeResponse)
def update_loanee_endpoint(
    loanee_id: UUID,
    payload: LoaneeUpdate,
    db: Session = Depends(get_db),
    organization=Depends(get_current_organization),
) -> LoaneeResponse:
    loanee = get_loanee(db, organization_id=organization.id, loanee_id=loanee_id)
    if not loanee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Loanee not found"
        )
    return update_loanee(db, loanee, payload)


@router.delete(
    "/{loanee_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
def delete_loanee_endpoint(
    loanee_id: UUID,
    db: Session = Depends(get_db),
    organization=Depends(get_current_organization),
) -> Response:
    loanee = get_loanee(db, organization_id=organization.id, loanee_id=loanee_id)
    if not loanee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Loanee not found"
        )
    delete_loanee(db, loanee)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{loanee_id}/loans", response_model=list[LoanResponse])
def list_loanee_loans_endpoint(
    loanee_id: UUID,
    db: Session = Depends(get_db),
    organization=Depends(get_current_organization),
) -> list[LoanResponse]:
    # Ensure loanee exists in this org
    loanee = get_loanee(db, organization_id=organization.id, loanee_id=loanee_id)
    if not loanee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Loanee not found"
        )
    return list_loans_for_loanee(db, organization_id=organization.id, loanee_id=loanee_id)
