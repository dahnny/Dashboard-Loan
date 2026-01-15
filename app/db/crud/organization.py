from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.db.models.organization import Organization
from app.core.security import hash_password
from app.db.schemas.organization import OrganizationCreate


def get_organization(db: Session, organization_id: str) -> Organization | None:
    return db.query(Organization).filter(Organization.id == organization_id).first()


def get_organization_by_email(db: Session, email: str) -> Organization | None:
    return db.query(Organization).filter(Organization.email == email).first()


def get_organization_by_slug(db: Session, slug: str) -> Organization | None:
    return db.query(Organization).filter(Organization.slug == slug).first()


def create_organization(db: Session, payload: OrganizationCreate) -> Organization:
    hashed_password = hash_password(payload.password)
    base_slug = payload.name.lower().strip().replace(" ", "-") or "org"
    slug = base_slug
    if get_organization_by_slug(db, slug):
        slug = f"{base_slug}-{str(uuid.uuid4())[:8]}"
    org = Organization(
        name=payload.name,
        slug=slug,
        email=payload.email,
        password=hashed_password,
        phone_number=payload.phone_number,
        address=payload.address,
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org
