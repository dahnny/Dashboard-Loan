from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_organization
from app.db.schemas.organization import OrganizationCreate, OrganizationLogin, OrganizationResponse
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: OrganizationCreate, db: Session = Depends(get_db)) -> OrganizationResponse:
    auth_service = AuthService(db=db)
    return auth_service.register_organization(organization=payload)


@router.post("/login")
async def login(payload: OrganizationLogin, db: Session = Depends(get_db)):
    auth_service = AuthService(db=db)
    return auth_service.authenticate_organization(email=payload.email, password=payload.password)


@router.post("/logout")
async def logout(payload: dict, organization=Depends(get_current_organization)):
    auth_service = AuthService(db=None)  # no DB needed for token revocation
    return auth_service.logout_organization(payload=payload, organization=organization)
