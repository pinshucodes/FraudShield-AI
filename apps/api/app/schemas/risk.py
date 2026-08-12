"""Schemas for risk scoring and fraud rules."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


class RiskScoreResponse(BaseModel):
    """Risk score for a transaction."""
    id: UUID
    transaction_id: UUID
    ml_score: Optional[float] = None
    rule_score: Optional[float] = None
    behavioral_score: Optional[float] = None
    anomaly_score: Optional[float] = None
    final_score: float
    risk_level: str
    explanation: Optional[Dict[str, Any]] = None
    model_version_id: Optional[UUID] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RiskAssessmentResponse(BaseModel):
    """Complete risk assessment result."""
    transaction_id: str
    risk_score: float = Field(..., ge=0, le=100)
    risk_level: str
    is_fraud_predicted: bool
    fraud_probability: float
    ml_score: float
    rule_score: float
    behavioral_score: float
    anomaly_score: float
    triggered_rules: List[Dict[str, Any]] = []
    explanation: Dict[str, Any] = {}
    recommended_action: str
    inference_latency_ms: float
    model_version: str


class FraudRuleCreate(BaseModel):
    """Schema for creating a fraud rule."""
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    rule_type: str = Field(..., description="threshold, velocity, geo, pattern")
    severity: str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH")
    enabled: bool = True
    config: Dict[str, Any] = Field(..., description="Rule configuration parameters")


class FraudRuleResponse(BaseModel):
    """Fraud rule response."""
    id: UUID
    rule_id: str
    name: str
    description: Optional[str] = None
    enabled: bool
    severity: str
    rule_type: str
    config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class FraudRuleUpdate(BaseModel):
    """Schema for updating a fraud rule."""
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    severity: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class RiskDashboardStats(BaseModel):
    """Risk dashboard statistics."""
    total_scored: int = 0
    high_risk_count: int = 0
    medium_risk_count: int = 0
    low_risk_count: int = 0
    average_score: float = 0.0
    fraud_detected_today: int = 0
    false_positive_rate: float = 0.0
    model_accuracy: float = 0.0
    active_rules: int = 0
