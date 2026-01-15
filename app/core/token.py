import hashlib
from typing import Optional
from fastapi import HTTPException, status, Request
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings
from app.core.redis import get_redis
from app.db.schemas.token import TokenData


SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = int(settings.access_token_expire_minutes)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def create_access_token(data:dict): 
    to_encode = data.copy()
    
    expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        SECRET_KEY, 
        algorithm=ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """Create a refresh token JWT.

    Uses a distinct `type` claim so that refresh tokens can be differentiated
    if additional validation logic is implemented later.
    """
    # Align refresh token expiry with access token expiry by default
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict | None:
    """Decode a JWT returning the payload or None if invalid."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": True},)
    except JWTError as e:
        print(f"JWTError: {e}")
        return None

def verify_access_token(token: str, credentials_exception):
    # print(token)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id: str = payload.get("organization_id")
        if id is None:
            raise credentials_exception
        token_data = TokenData(id=id)
    except JWTError:
        raise credentials_exception
    
    return token_data
    

    
def verify_password_reset_token(token: str, db):
    """Validate a password reset token and return the associated organization.

    Raises HTTP exceptions for invalid or expired tokens or if the organization cannot
    be found. Returns the matched `Organization` instance on success.
    """
    from sqlalchemy.orm import Session
    from app.db.models.organization import Organization
    try:
        payload = decode_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
        org_id: str | None = str(payload.get("organization_id"))
        email: str | None = payload.get("email")
        organization = (
            db.query(Organization)
            .filter(Organization.id == org_id, Organization.email == email)
            .first()
        )
        if organization is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found for the provided token",
            )
        return organization
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


def hash_refresh_token(token: str) -> str:
    """Return a SHA-256 hash of a refresh token for secure storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def store_refresh_token_redis(
    refresh_token: str,
    organization_id: str,
    ttl_seconds: Optional[int] = None,
) -> None:
    """Store a hashed refresh token in Redis with TTL.

    Key:   refresh:{sha256(token)}
    Value: <organization_id>
    TTL:   defaults to ACCESS_TOKEN_EXPIRE_MINUTES to align lifetimes
    """
    redis_client = get_redis()
    ttl = ttl_seconds or (ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    redis_client.setex(f"refresh:{organization_id}", ttl, refresh_token)


def revoke_refresh_token_redis(
    organization_id: str,
    refresh_token: str,
) -> bool:
    """Delete a stored refresh token from Redis. Returns True if deleted."""
    redis_client = get_redis()
    key = f"refresh:{organization_id}"
    val = redis_client.get(key)
    if val != refresh_token:
        return False
    removed = redis_client.delete(key)
    return bool(removed)


def is_refresh_token_active(
    organization_id: str,
) -> bool:
    """Check if a refresh token is currently active in Redis.

    Optionally verify that the stored organization id matches the token subject.
    """
    redis_client = get_redis()
    val = redis_client.get(f"refresh:{organization_id}")
    if not val:
        return False
    payload = decode_token(val)
    # Verify the token subject matches the organization id
    if payload.get("sub") != str(organization_id):
        return False
    return True


