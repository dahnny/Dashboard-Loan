import uuid

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID

from app.db.models.base import Base
from app.db.models.mixins import TimestampMixin


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False, unique=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)
    address = Column(String, nullable=True)
