import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Float, Integer, JSON, ForeignKey, DateTime, func
from datetime import datetime
from app.models.base import Base

class UserBehaviorProfile(Base):
    __tablename__ = "user_behavior_profiles"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    avg_transaction_amount: Mapped[float] = mapped_column(Float, default=0.0)
    median_transaction_amount: Mapped[float] = mapped_column(Float, default=0.0)
    max_transaction_amount: Mapped[float] = mapped_column(Float, default=0.0)
    min_transaction_amount: Mapped[float] = mapped_column(Float, default=0.0)
    total_transaction_count: Mapped[int] = mapped_column(Integer, default=0)
    typical_transaction_hours: Mapped[dict] = mapped_column(JSON, default=list)
    typical_locations: Mapped[dict] = mapped_column(JSON, default=list)
    typical_merchants: Mapped[dict] = mapped_column(JSON, default=list)
    typical_devices: Mapped[dict] = mapped_column(JSON, default=list)
    avg_transactions_per_day: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
