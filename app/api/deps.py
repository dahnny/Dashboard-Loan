from app.db.session import SessionLocal
from app.core.token import verify_access_token
from app.db.models.user import User
from app.core.supabase_auth import SupabasePrincipal, supabase_jwt_verifier
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.crud.user import get_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
supabase_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = verify_access_token(token, credentials_exception)
    user = get_user(db, token.id)
    if not user:
        raise credentials_exception
    
    return user


async def get_current_principal(token: str = Depends(supabase_oauth2_scheme)) -> SupabasePrincipal:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate Supabase credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        return await supabase_jwt_verifier.verify(token)
    except Exception:
        raise credentials_exception


def require_roles(*required: str):
    async def _dep(principal: SupabasePrincipal = Depends(get_current_principal)) -> SupabasePrincipal:
        if not required:
            return principal
        if not principal.roles.intersection(set(required)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role",
            )
        return principal

    return _dep



