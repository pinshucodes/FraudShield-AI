import uuid
from enum import Enum as PyEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, Enum, Text, DateTime, func
from datetime import datetime
from app.models.base import Base

class FraudCaseStatus(str, PyEnum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    CONFIRMED_FRAUD = "CONFIRMED_FRAUD"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    CLOSED = "CLOSED"

class CasePriority(str, PyEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class FraudCase(Base):
    __tablename__ = "fraud_cases"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    case_id: Mapped[str] = mapped_column(String(50), unique=True)
    transaction_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("transactions.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    assigned_analyst_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    status: Mapped[FraudCaseStatus] = mapped_column(Enum(FraudCaseStatus), default=FraudCaseStatus.OPEN)
    priority: Mapped[CasePriority] = mapped_column(Enum(CasePriority), default=CasePriority.MEDIUM)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class InvestigationNote(Base):
    __tablename__ = "investigation_notes"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("fraud_cases.id"))
    analyst_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
