from __future__ import annotations

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Date,
    Numeric,
    Enum as SAEnum,
    Index,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.models.base import Base
from app.db.models.mixins import TimestampMixin


class ScheduleType(str):
    single = "single"
    multiple = "multiple"


class ScheduleItemStatus(str):
    pending = "pending"
    processing = "processing"
    paid = "paid"
    failed = "failed"
    canceled = "canceled"


class RecurringDebitSchedule(Base, TimestampMixin):
    __tablename__ = "recurring_debit_schedules"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    loan_id = Column(Integer, ForeignKey("loans.id", ondelete="CASCADE"), nullable=False, index=True)
    mandate_id = Column(Integer, ForeignKey("direct_debit_mandates.id", ondelete="RESTRICT"), nullable=False, index=True)

    schedule_type = Column(String, nullable=False)  # single | multiple
    number_of_debits = Column(Integer, nullable=False, default=1)
    total_amount = Column(Numeric(12, 2), nullable=False)
    amount_per_debit = Column(Numeric(12, 2), nullable=False)

    loan = relationship("Loan")
    mandate = relationship("DirectDebitMandate")
    items = relationship("DebitScheduleItem", back_populates="schedule", cascade="all, delete-orphan")


class DebitScheduleItem(Base, TimestampMixin):
    __tablename__ = "debit_schedule_items"

    __table_args__ = (
        Index("ix_debit_items_due_date_status", "due_date", "status"),
    )

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("recurring_debit_schedules.id", ondelete="CASCADE"), nullable=False, index=True)
    due_date = Column(Date, nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String, nullable=False, default=ScheduleItemStatus.pending)
    idempotency_key = Column(String, nullable=False, unique=True, index=True)
    provider_txn_ref = Column(String, nullable=True, index=True)
    attempts = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)

    schedule = relationship("RecurringDebitSchedule", back_populates="items")
