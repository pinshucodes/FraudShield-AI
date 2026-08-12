"""Transaction API endpoints.

Provides CRUD operations for transactions with RBAC.
Customers can only see their own transactions.
Analysts and admins can see all transactions and change statuses.
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional
from datetime import datetime

from app.schemas.transaction import (
    TransactionCreateRequest,
    TransactionResponse,
    TransactionListResponse,
    TransactionFilterParams,
    TransactionStatusUpdate,
    TransactionStatsResponse,
    ReportFraudRequest,
)
from app.schemas.common import APIResponse
from app.services.transaction_service import TransactionService
from app.core.database import get_db
from app.repositories.transaction_repo import TransactionRepository
from app.repositories.user_repo import UserRepository
from app.core.dependencies import get_current_active_user, require_role
from app.models.user import User, UserRole

router = APIRouter()


def get_txn_service(db: AsyncSession = Depends(get_db)) -> TransactionService:
    return TransactionService(TransactionRepository(db), UserRepository(db))


@router.post("", response_model=APIResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_transaction(
    request: TransactionCreateRequest,
    current_user: User = Depends(get_current_active_user),
    service: TransactionService = Depends(get_txn_service),
):
    """Create a new transaction.
    
    Validates input, generates a unique transaction ID, and saves the transaction.
    The transaction is created with status RECEIVED and will be processed asynchronously.
    """
    txn = await service.create_transaction(
        data=request.model_dump(),
        requesting_user_id=current_user.id,
    )
    return APIResponse(
        message="Transaction received and queued for processing.",
        data=TransactionResponse.model_validate(txn),
    )


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by status"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level (LOW/MEDIUM/HIGH)"),
    min_amount: Optional[float] = Query(None, ge=0),
    max_amount: Optional[float] = Query(None, ge=0),
    merchant_category: Optional[str] = None,
    payment_method: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    search: Optional[str] = Query(None, description="Search by transaction_id or merchant_id"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="asc or desc"),
    current_user: User = Depends(get_current_active_user),
    service: TransactionService = Depends(get_txn_service),
):
    """List transactions with filtering, sorting, and pagination.
    
    Customers see only their own transactions.
    Analysts and admins see all transactions.
    """
    filters = {
        "page": page,
        "page_size": page_size,
        "status": status,
        "risk_level": risk_level,
        "min_amount": min_amount,
        "max_amount": max_amount,
        "merchant_category": merchant_category,
        "payment_method": payment_method,
        "date_from": date_from,
        "date_to": date_to,
        "search": search,
        "sort_by": sort_by,
        "sort_order": sort_order,
    }
    # Customers can only see their own transactions
    if current_user.role == UserRole.CUSTOMER:
        filters["user_id"] = current_user.id

    # Remove None values
    filters = {k: v for k, v in filters.items() if v is not None}
    return await service.list_transactions(filters)


@router.get("/stats", response_model=APIResponse)
async def get_transaction_stats(
    current_user: User = Depends(get_current_active_user),
    service: TransactionService = Depends(get_txn_service),
):
    """Get aggregate transaction statistics.
    
    Customers see stats for their own transactions only.
    Analysts and admins see global stats.
    """
    user_id = current_user.id if current_user.role == UserRole.CUSTOMER else None
    stats = await service.get_stats(user_id)
    return APIResponse(data=TransactionStatsResponse(**stats))


@router.get("/{transaction_id}", response_model=APIResponse)
async def get_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_active_user),
    service: TransactionService = Depends(get_txn_service),
):
    """Get transaction details by transaction ID (TXN-XXXXX format).
    
    Customers can only view their own transactions.
    """
    txn = await service.get_transaction(transaction_id)
    if not service.validate_user_access(txn, current_user.id, current_user.role.value):
        from app.core.exceptions import ForbiddenError
        raise ForbiddenError(message="You do not have access to this transaction.")
    return APIResponse(data=TransactionResponse.model_validate(txn))


@router.patch("/{transaction_id}/status", response_model=APIResponse)
async def update_transaction_status(
    transaction_id: str,
    request: TransactionStatusUpdate,
    current_user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
    service: TransactionService = Depends(get_txn_service),
):
    """Update transaction status (analyst/admin only).
    
    Validates state machine transitions:
    - REVIEW -> CONFIRMED_FRAUD, FALSE_POSITIVE, APPROVED, BLOCKED
    - BLOCKED -> CONFIRMED_FRAUD, FALSE_POSITIVE
    """
    txn = await service.update_status(
        transaction_id=transaction_id,
        new_status_str=request.status,
        analyst_id=current_user.id,
        reason=request.reason,
    )
    return APIResponse(
        message=f"Transaction status updated to {request.status}.",
        data=TransactionResponse.model_validate(txn),
    )


@router.post("/{transaction_id}/report-fraud", response_model=APIResponse)
async def report_fraud(
    transaction_id: str,
    request: ReportFraudRequest,
    current_user: User = Depends(get_current_active_user),
    service: TransactionService = Depends(get_txn_service),
):
    """Customer reports a transaction as potentially fraudulent.
    
    Only the transaction owner can report their transaction.
    If the transaction was approved, it moves to REVIEW status.
    """
    txn = await service.report_fraud(
        transaction_id=transaction_id,
        user_id=current_user.id,
        reason=request.reason,
    )
    return APIResponse(
        message="Fraud report submitted. The transaction will be reviewed.",
        data=TransactionResponse.model_validate(txn),
    )
