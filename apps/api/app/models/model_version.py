import uuid
from enum import Enum as PyEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, Enum, JSON, ForeignKey, DateTime, func
from datetime import datetime
from app.models.base import Base

class ModelStatus(str, PyEnum):
    TRAINING = "TRAINING"
    STAGED = "STAGED"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"

class ModelVersion(Base):
    __tablename__ = "model_versions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    version: Mapped[str] = mapped_column(String(20), unique=True)
    algorithm: Mapped[str] = mapped_column(String(100))
    status: Mapped[ModelStatus] = mapped_column(Enum(ModelStatus), default=ModelStatus.TRAINING)
    metrics: Mapped[dict] = mapped_column(JSON)
    hyperparameters: Mapped[dict] = mapped_column(JSON)
    artifact_path: Mapped[str] = mapped_column(String(500))
    training_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    dataset_version: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
