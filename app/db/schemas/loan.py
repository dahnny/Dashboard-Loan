from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.db.models.loan import LoanStatus


class LoaneeCreate(BaseModel):
    full_name: str
    email: str | None = None
    phone_number: str | None = None
    address: str | None = None


class LoaneeResponse(BaseModel):
    id: UUID
    full_name: str
    email: str | None = None
    phone_number: str | None = None
    address: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LoanCreate(LoaneeCreate):
    amount: Decimal
    loan_term_weeks: int
    surcharge: int = 0
    penalty: int = 0
    # Optional inputs for calculating due_date
    start_date: date | None = None
    due_date: date | None = None
    auto_debit_enabled: bool = False


class LoanResponse(BaseModel):
    id: UUID
    loanee_id: UUID
    amount: Decimal
    loan_term_weeks: int
    surcharge: Decimal
    penalty: Decimal
    due_date: date
    status: LoanStatus
    auto_debit_enabled: bool
    total_payable: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LoanSummaryResponse(BaseModel):
    id: UUID
    amount: Decimal
    loan_term_weeks: int
    due_date: date
    status: LoanStatus
    total_payable: Decimal

    class Config:
        from_attributes = True


class LoanStatusTransitionRequest(BaseModel):
    to_status: LoanStatus
    message: str | None = None


class LoaneeUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone_number: str | None = None
    address: str | None = None


class LoaneeWithLoansResponse(LoaneeResponse):
    loans: list[LoanSummaryResponse] = []


class LoanDocumentResponse(BaseModel):
    id: UUID
    loanee_id: UUID
    loan_id: UUID | None = None
    document_type: str
    bucket: str
    uri: str
    content_type: str | None = None
    size_bytes: int | None = None
    checksum: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SignedUrlResponse(BaseModel):
    signed_url: str
