from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.organization import Organization


DEFAULT_ORG_SLUG = "default"
DEFAULT_ORG_NAME = "Default Organization"


def get_default_organization(db: Session) -> Organization | None:
    return db.query(Organization).filter(Organization.slug == DEFAULT_ORG_SLUG).first()


def get_or_create_default_organization(db: Session) -> Organization:
    org = get_default_organization(db)
    if org:
        return org

    org = Organization(name=DEFAULT_ORG_NAME, slug=DEFAULT_ORG_SLUG)
    db.add(org)
    db.commit()
    db.refresh(org)
    return org
