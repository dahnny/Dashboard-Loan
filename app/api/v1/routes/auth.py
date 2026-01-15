from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.db.schemas.user import UserCreate, UserLogin, UserResponse
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    auth_service = AuthService(db=db)
    return auth_service.register_user(user=payload)


@router.post("/login")
async def login(payload: UserLogin, db: Session = Depends(get_db)):
    auth_service = AuthService(db=db)
    return auth_service.authenticate_user(email=payload.email, password=payload.password)


@router.post("/logout")
async def logout(payload: dict, user=Depends(get_current_user)):
    # user is provided by internal JWT dependency, not Supabase
    auth_service = AuthService(db=None)  # no DB needed for token revocation
    return auth_service.logout_user(payload=payload, user=user)
