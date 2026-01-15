from __future__ import annotations
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.core.token import (
    create_access_token,
    revoke_refresh_token_redis,
    store_refresh_token_redis,
)
from app.db.crud.user import create_user, get_user_by_email
from app.db.models.user import User
from app.db.schemas.user import UserCreate, UserResponse
from app.core.redis import get_redis
from app.core.token import create_refresh_token


class AuthService:
    def __init__(self, db: Session):
        self._db = db

    def register_user(self, *, user: UserCreate) -> UserResponse:
        if user.password != user.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match"
            )
        existing_user = get_user_by_email(self._db, email=user.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        new_user = create_user(self._db, user=user)
        return UserResponse.from_orm(new_user)

    def authenticate_user(
        self,
        *,
        email: str,
        password: str,
    ) -> dict:
        user: User | None = get_user_by_email(self._db, email=email)
        if not user or not verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        access_token = create_access_token(data={"user_id": str(user.id)})
        refresh_token = create_refresh_token(subject=str(user.id))

        store_refresh_token_redis(
            refresh_token,
            str(user.id),
        )
        return {
            "user": UserResponse.from_orm(user),
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    def logout_user(self, payload: dict, user: User) -> dict:
        """Delete a stored refresh token for the given user if present (Redis)."""
        refresh_token = str(payload.get("refresh_token"))
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refresh token is required",
            )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated",
            )

        deleted = revoke_refresh_token_redis(str(user.id), refresh_token)
        return deleted
