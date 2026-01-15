from __future__ import annotations
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.core.token import (
    create_access_token,
    revoke_refresh_token_redis,
    store_refresh_token_redis,
)
from app.db.crud.organization import create_organization, get_organization_by_email
from app.db.models.organization import Organization
from app.db.schemas.organization import OrganizationCreate, OrganizationResponse
from app.core.redis import get_redis
from app.core.token import create_refresh_token


class AuthService:
    def __init__(self, db: Session):
        self._db = db

    def register_organization(self, *, organization: OrganizationCreate) -> OrganizationResponse:
        if organization.password != organization.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match"
            )
        existing_org = get_organization_by_email(self._db, email=organization.email)
        if existing_org:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        new_org = create_organization(self._db, payload=organization)
        return OrganizationResponse.from_orm(new_org)

    def authenticate_organization(
        self,
        *,
        email: str,
        password: str,
    ) -> dict:
        organization: Organization | None = get_organization_by_email(self._db, email=email)
        if not organization or not verify_password(password, organization.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        access_token = create_access_token(data={"organization_id": str(organization.id)})
        refresh_token = create_refresh_token(subject=str(organization.id))

        store_refresh_token_redis(
            refresh_token,
            str(organization.id),
        )
        return {
            "organization": OrganizationResponse.from_orm(organization),
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    def logout_organization(self, payload: dict, organization: Organization) -> dict:
        """Delete a stored refresh token for the given organization if present (Redis)."""
        refresh_token = str(payload.get("refresh_token"))
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refresh token is required",
            )
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Organization not authenticated",
            )

        deleted = revoke_refresh_token_redis(str(organization.id), refresh_token)
        return deleted
