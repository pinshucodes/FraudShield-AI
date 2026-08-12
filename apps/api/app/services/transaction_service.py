"""Transaction business logic including validation, ID generation, and state machine."""

import uuid
import random
import string
from datetime import datetime, timezone
from typing import Optional
from decimal import Decimal

from app.repositories.transaction_repo import TransactionRepository
from app.repositories.user_repo import UserRepository
from app.models.transaction import Transaction, TransactionStatus
from app.models.risk import RiskLevel
from app.core.exceptions import NotFoundError, ValidationError, ForbiddenError
from app.core.logging import get_logger
from app.services.websocket import manager

logger = get_logger("transaction_service")

# Valid state transitions
STATE_TRANSITIONS = {
    TransactionStatus.RECEIVED: {TransactionStatus.PROCESSING},
    TransactionStatus.PROCESSING: {TransactionStatus.SCORED},
    TransactionStatus.SCORED: {TransactionStatus.APPROVED, TransactionStatus.REVIEW, TransactionStatus.BLOCKED},
    TransactionStatus.APPROVED: set(),  # Terminal
    TransactionStatus.REVIEW: {TransactionStatus.CONFIRMED_FRAUD, TransactionStatus.FALSE_POSITIVE, TransactionStatus.APPROVED, TransactionStatus.BLOCKED},
    TransactionStatus.BLOCKED: {TransactionStatus.CONFIRMED_FRAUD, TransactionStatus.FALSE_POSITIVE},
    TransactionStatus.CONFIRMED_FRAUD: set(),  # Terminal
    TransactionStatus.FALSE_POSITIVE: set(),  # Terminal
}


def generate_transaction_id() -> str:
    """Generate a unique transaction ID in TXN-XXXXX format."""
    chars = string.digits
    random_part = ''.join(random.choices(chars, k=8))
    return f"TXN-{random_part}"


class TransactionService:
    def __init__(self, txn_repo: TransactionRepository, user_repo: Optional[UserRepository] = None):
        self.txn_repo = txn_repo
        self.user_repo = user_repo

    async def create_transaction(self, data: dict, requesting_user_id: Optional[uuid.UUID] = None) -> Transaction:
        """Create a new transaction with validation."""
        # Generate unique transaction ID
        transaction_id = generate_transaction_id()
        while await self.txn_repo.get_by_transaction_id(transaction_id):
            transaction_id = generate_transaction_id()

        # Resolve user_id: if the requesting user is a customer, use their own ID
        user_id = requesting_user_id
        if not user_id:
            # For API-submitted transactions, try to look up user by external user_id
            external_user_id = data.pop("user_id", None)
            if self.user_repo and external_user_id:
                # In a real system, we'd map external user IDs to internal UUIDs
                # For now, we'll just use the requesting user's ID
                pass
            if not user_id:
                raise ValidationError(message="User ID is required")

        # Extract location
        location = data.pop("location", None)
        latitude = location.get("latitude") if location else None
        longitude = location.get("longitude") if location else None

        # Remove fields not in model
        data.pop("user_id", None)
        data.pop("timestamp", None)

        # Create transaction
        txn = await self.txn_repo.create(
            transaction_id=transaction_id,
            user_id=user_id,
            amount=float(data.get("amount", 0)),
            currency=data.get("currency", "INR"),
            merchant_id=data.get("merchant_id"),
            merchant_category=data.get("merchant_category"),
            payment_method=data.get("payment_method"),
            device_id=data.get("device_id"),
            ip_address=data.get("ip_address"),
            latitude=latitude,
            longitude=longitude,
            status=TransactionStatus.RECEIVED,
        )

        logger.info("transaction_created", transaction_id=transaction_id, amount=float(data.get("amount", 0)))
        
        # Broadcast the new transaction
        await manager.broadcast({
            "type": "NEW_TRANSACTION",
            "data": {
                "id": str(txn.id),
                "transaction_id": txn.transaction_id,
                "amount": float(txn.amount),
                "currency": txn.currency,
                "merchant_id": txn.merchant_id,
                "status": txn.status.value,
                "timestamp": txn.timestamp.isoformat() if txn.timestamp else None
            }
        })
        
        return txn

    async def get_transaction(self, transaction_id: str) -> Transaction:
        """Get a transaction by its public transaction ID (TXN-XXXXX)."""
        txn = await self.txn_repo.get_by_transaction_id(transaction_id)
        if not txn:
            raise NotFoundError(message=f"Transaction {transaction_id} does not exist.")
        return txn

    async def get_transaction_by_uuid(self, id: uuid.UUID) -> Transaction:
        """Get a transaction by internal UUID."""
        txn = await self.txn_repo.get_by_id(id)
        if not txn:
            raise NotFoundError(message="Transaction not found.")
        return txn

    async def list_transactions(self, filters: dict) -> dict:
        """List transactions with filtering and pagination."""
        page = filters.pop("page", 1)
        page_size = filters.pop("page_size", 20)
        skip = (page - 1) * page_size

        transactions, total = await self.txn_repo.get_filtered(
            skip=skip, limit=page_size, **filters
        )

        return {
            "success": True,
            "data": transactions,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total else 0,
        }

    async def update_status(
        self, transaction_id: str, new_status_str: str, analyst_id: uuid.UUID, reason: Optional[str] = None
    ) -> Transaction:
        """Update transaction status with state machine validation."""
        txn = await self.get_transaction(transaction_id)
        new_status = TransactionStatus(new_status_str)
        current_status = txn.status

        # Validate state transition
        allowed = STATE_TRANSITIONS.get(current_status, set())
        if new_status not in allowed:
            raise ValidationError(
                message=f"Cannot transition from {current_status.value} to {new_status.value}. "
                        f"Allowed transitions: {[s.value for s in allowed]}"
            )

        txn = await self.txn_repo.update_status(transaction_id, new_status)
        logger.info(
            "transaction_status_updated",
            transaction_id=transaction_id,
            old_status=current_status.value,
            new_status=new_status.value,
            analyst_id=str(analyst_id),
        )
        
        await manager.broadcast({
            "type": "UPDATE_TRANSACTION",
            "data": {
                "transaction_id": txn.transaction_id,
                "status": txn.status.value
            }
        })
        
        return txn

    async def report_fraud(
        self, transaction_id: str, user_id: uuid.UUID, reason: str
    ) -> Transaction:
        """Customer reports a transaction as potentially fraudulent."""
        txn = await self.get_transaction(transaction_id)

        # Verify the transaction belongs to this user
        if txn.user_id != user_id:
            raise ForbiddenError(message="You can only report your own transactions.")

        if txn.is_fraud_reported:
            raise ValidationError(message="This transaction has already been reported.")

        txn.is_fraud_reported = True
        # If transaction is approved, move it to review
        if txn.status == TransactionStatus.APPROVED:
            txn.status = TransactionStatus.REVIEW

        await self.txn_repo.session.commit()
        await self.txn_repo.session.refresh(txn)

        logger.info("fraud_reported", transaction_id=transaction_id, user_id=str(user_id))
        return txn

    async def get_stats(self, user_id: Optional[uuid.UUID] = None) -> dict:
        """Get transaction statistics."""
        return await self.txn_repo.get_stats(user_id)

    def validate_user_access(self, txn: Transaction, user_id: uuid.UUID, role: str) -> bool:
        """Check if user has access to this transaction."""
        if role in ("analyst", "admin"):
            return True
        return txn.user_id == user_id
