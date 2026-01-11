from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

from pydantic import BaseModel

from app.db.models.loan import LoanStatus


class LoaneeCreate(BaseModel):
    full_name: str
    email: str | None = None
    phone_number: str | None = None
    address: str | None = None
    user_id: int | None = None


class LoaneeResponse(BaseModel):
    id: int
    full_name: str
    email: str | None = None
    phone_number: str | None = None
    address: str | None = None
    user_id: int | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class LoanCreate(BaseModel):
    loanee_id: int
    amount: Decimal
    loan_term_weeks: int
    surcharge: Decimal = Decimal("0.00")
    penalty: Decimal = Decimal("0.00")
    # Optional inputs for calculating due_date
    start_date: date | None = None
    due_date: date | None = None
    auto_debit_enabled: bool = False


class LoanResponse(BaseModel):
    id: int
    loanee_id: int
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
        orm_mode = True


class LoanStatusTransitionRequest(BaseModel):
    to_status: LoanStatus
    actor_user_id: int | None = None
    message: str | None = None


class LoaneeUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone_number: str | None = None
    address: str | None = None


class LoanDocumentResponse(BaseModel):
    id: int
    loanee_id: int
    loan_id: int | None = None
    document_type: str
    bucket: str
    uri: str
    content_type: str | None = None
    size_bytes: int | None = None
    checksum: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class SignedUrlResponse(BaseModel):
    signed_url: str
