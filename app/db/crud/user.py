from sqlalchemy.orm import Session
from app.db.models.user import User
from app.db.schemas.user import UserCreate
from app.core.security import hash_password
from app.db.crud.organization import get_or_create_default_organization


def get_user(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate) -> User:
    hashed_password = hash_password(user.password)
    org = get_or_create_default_organization(db)
    db_user = User(
        organization_id=org.id,
        email=user.email,
        password=hashed_password,
        phone_number=user.phone_number
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


