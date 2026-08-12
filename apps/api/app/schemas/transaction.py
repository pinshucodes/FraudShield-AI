from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from enum import Enum

class LocationSchema(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

class TransactionCreateRequest(BaseModel):
    """Schema for creating a new transaction."""
    user_id: str = Field(..., description="User ID (e.g., USR-10234)")
    amount: Decimal = Field(..., gt=0, max_digits=15, decimal_places=2, description="Transaction amount")
    currency: str = Field(default="INR", max_length=3)
    merchant_id: Optional[str] = Field(None, description="Merchant ID")
    merchant_category: Optional[str] = Field(None, description="Merchant category (electronics, travel, etc.)")
    payment_method: Optional[str] = Field(None, description="Payment method (card, upi, netbanking, wallet)")
    device_id: Optional[str] = Field(None)
    ip_address: Optional[str] = Field(None)
    location: Optional[LocationSchema] = None
    timestamp: Optional[datetime] = Field(None, description="Transaction timestamp, defaults to now")

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: str) -> str:
        allowed = {'INR', 'USD', 'EUR', 'GBP', 'SGD', 'AED'}
        if v.upper() not in allowed:
            raise ValueError(f'Currency must be one of: {allowed}')
        return v.upper()

    @field_validator('payment_method')
    @classmethod 
    def validate_payment_method(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed = {'card', 'upi', 'netbanking', 'wallet', 'bank_transfer'}
            if v.lower() not in allowed:
                raise ValueError(f'Payment method must be one of: {allowed}')
            return v.lower()
        return v

class TransactionResponse(BaseModel):
    """Full transaction response."""
    id: UUID
    transaction_id: str
    user_id: UUID
    amount: float
    currency: str
    merchant_id: Optional[str] = None
    merchant_category: Optional[str] = None
    payment_method: Optional[str] = None
    device_id: Optional[str] = None
    ip_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: str
    risk_level: Optional[str] = None
    is_fraud_reported: bool = False
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TransactionListResponse(BaseModel):
    """Paginated transaction list."""
    success: bool = True
    data: List[TransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class TransactionFilterParams(BaseModel):
    """Query parameters for filtering transactions."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    status: Optional[str] = None
    risk_level: Optional[str] = None
    min_amount: Optional[float] = Field(None, ge=0)
    max_amount: Optional[float] = Field(None, ge=0)
    merchant_category: Optional[str] = None
    payment_method: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    user_id: Optional[UUID] = None
    search: Optional[str] = Field(None, description="Search by transaction_id or merchant_id")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="asc or desc")

class TransactionStatusUpdate(BaseModel):
    """Schema for analyst status updates."""
    status: str = Field(..., description="New status")
    reason: Optional[str] = Field(None, description="Reason for status change")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed_transitions = {'CONFIRMED_FRAUD', 'FALSE_POSITIVE', 'APPROVED', 'BLOCKED', 'REVIEW'}
        if v.upper() not in allowed_transitions:
            raise ValueError(f'Status must be one of: {allowed_transitions}')
        return v.upper()

class TransactionStatsResponse(BaseModel):
    """Aggregate transaction statistics."""
    total_transactions: int = 0
    total_amount: float = 0.0
    fraud_detected: int = 0
    transactions_under_review: int = 0
    transactions_blocked: int = 0
    transactions_approved: int = 0
    fraud_rate: float = 0.0
    average_risk_score: float = 0.0
    amount_blocked: float = 0.0

class ReportFraudRequest(BaseModel):
    """Customer reports a transaction as potentially fraudulent."""
    reason: str = Field(..., min_length=10, max_length=1000)
