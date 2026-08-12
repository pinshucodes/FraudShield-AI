import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime, func
from datetime import datetime
from app.models.base import Base

class Device(Base):
    __tablename__ = "devices"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    device_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    device_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    transaction_count: Mapped[int] = mapped_column(Integer, default=0)
    is_trusted: Mapped[bool] = mapped_column(Boolean, default=False)
