import enum
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    BigInteger,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.models.base import Base
from app.db.models.mixins import TimestampMixin


class LoanStatus(str, enum.Enum):
    not_due = "not_due"
    due = "due"
    paid = "paid"
    defaulted = "defaulted"


class Loanee(Base, TimestampMixin):
    __tablename__ = "loanees"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, unique=True)

    full_name = Column(String, nullable=False)
    email = Column(String, nullable=True, index=True)
    phone_number = Column(String, nullable=True)
    address = Column(Text, nullable=True)

    user = relationship("User")
    organization = relationship("Organization")
    loans = relationship("Loan", back_populates="loanee", cascade="all, delete-orphan")
    documents = relationship("LoanDocument", back_populates="loanee", cascade="all, delete-orphan")
    direct_debit_mandates = relationship(
        "DirectDebitMandate",
        back_populates="loanee",
        cascade="all, delete-orphan",
    )


class Loan(Base, TimestampMixin):
    __tablename__ = "loans"

    __table_args__ = (
        Index("ix_loans_due_date_status", "due_date", "status"),
        Index("ix_loans_org_due_date_status", "organization_id", "due_date", "status"),
    )

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    loanee_id = Column(Integer, ForeignKey("loanees.id", ondelete="RESTRICT"), nullable=False, index=True)

    amount = Column(Numeric(12, 2), nullable=False)
    loan_term_weeks = Column(Integer, nullable=False)
    surcharge = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    penalty = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))

    due_date = Column(Date, nullable=False, index=True)
    status = Column(Enum(LoanStatus, name="loan_status"), nullable=False, default=LoanStatus.not_due)
    auto_debit_enabled = Column(Boolean, nullable=False, default=False)

    # Stored (derived) value for audit stability: amount + surcharge (+ penalty at time of storing).
    total_payable = Column(Numeric(12, 2), nullable=False)

    loanee = relationship("Loanee", back_populates="loans")
    organization = relationship("Organization")
    documents = relationship("LoanDocument", back_populates="loan", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="loan", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="loan", cascade="all, delete-orphan")


class LoanDocument(Base, TimestampMixin):
    __tablename__ = "loan_documents"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    loanee_id = Column(Integer, ForeignKey("loanees.id", ondelete="CASCADE"), nullable=False, index=True)
    loan_id = Column(Integer, ForeignKey("loans.id", ondelete="SET NULL"), nullable=True, index=True)

    document_type = Column(String, nullable=False)
    # Storage object key/path (not a permanent public URL)
    uri = Column(String, nullable=False)
    bucket = Column(String, nullable=False)
    content_type = Column(String, nullable=True)
    size_bytes = Column(BigInteger, nullable=True)
    checksum = Column(String, nullable=True)

    loanee = relationship("Loanee", back_populates="documents")
    loan = relationship("Loan", back_populates="documents")
    organization = relationship("Organization")


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    loan_id = Column(Integer, ForeignKey("loans.id", ondelete="CASCADE"), nullable=False, index=True)

    amount = Column(Numeric(12, 2), nullable=False)
    reference = Column(String, nullable=True, index=True)
    source = Column(String, nullable=False, default="manual")

    loan = relationship("Loan", back_populates="payments")
    organization = relationship("Organization")


class DirectDebitMandate(Base, TimestampMixin):
    __tablename__ = "direct_debit_mandates"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    loanee_id = Column(Integer, ForeignKey("loanees.id", ondelete="CASCADE"), nullable=False, index=True)

    provider = Column(String, nullable=False)
    mandate_reference = Column(String, nullable=False, unique=True, index=True)
    active = Column(Boolean, nullable=False, default=True)

    loanee = relationship("Loanee", back_populates="direct_debit_mandates")
    organization = relationship("Organization")


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    actor_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    loan_id = Column(Integer, ForeignKey("loans.id", ondelete="CASCADE"), nullable=True, index=True)

    action = Column(String, nullable=False)
    from_status = Column(Enum(LoanStatus, name="loan_status"), nullable=True)
    to_status = Column(Enum(LoanStatus, name="loan_status"), nullable=True)
    message = Column(Text, nullable=True)

    actor_user = relationship("User")
    loan = relationship("Loan", back_populates="audit_logs")
    organization = relationship("Organization")
