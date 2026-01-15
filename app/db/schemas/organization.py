from uuid import UUID
from pydantic import BaseModel, EmailStr
from datetime import datetime


class OrganizationBase(BaseModel):
    name: str
    email: EmailStr
    address: str | None = None
    phone_number: str | None = None


class OrganizationCreate(OrganizationBase):
    password: str
    confirm_password: str


class OrganizationResponse(OrganizationBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrganizationLogin(BaseModel):
    email: EmailStr
    password: str

    class Config:
        from_attributes = True
