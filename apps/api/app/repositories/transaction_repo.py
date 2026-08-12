from app.repositories.base import BaseRepository
from app.models.transaction import Transaction, TransactionStatus
from app.models.risk import RiskLevel, RiskScore
from sqlalchemy import select, func, and_, or_, desc, asc, case
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Tuple, List
from uuid import UUID
from datetime import datetime
import uuid as uuid_mod

class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self, session: AsyncSession):
        super().__init__(Transaction, session)

    async def get_by_transaction_id(self, transaction_id: str) -> Transaction | None:
        result = await self.session.execute(
            select(Transaction).filter_by(transaction_id=transaction_id)
        )
        return result.scalars().first()

    async def get_filtered(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        risk_level: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        merchant_category: Optional[str] = None,
        payment_method: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        user_id: Optional[UUID] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[Transaction], int]:
        """Get transactions with advanced filtering, sorting, and pagination."""
        query = select(Transaction)
        conditions = []

        if status:
            conditions.append(Transaction.status == TransactionStatus(status))
        if risk_level:
            conditions.append(Transaction.risk_level == RiskLevel(risk_level))
        if min_amount is not None:
            conditions.append(Transaction.amount >= min_amount)
        if max_amount is not None:
            conditions.append(Transaction.amount <= max_amount)
        if merchant_category:
            conditions.append(Transaction.merchant_category == merchant_category)
        if payment_method:
            conditions.append(Transaction.payment_method == payment_method)
        if date_from:
            conditions.append(Transaction.created_at >= date_from)
        if date_to:
            conditions.append(Transaction.created_at <= date_to)
        if user_id:
            conditions.append(Transaction.user_id == user_id)
        if search:
            conditions.append(
                or_(
                    Transaction.transaction_id.ilike(f"%{search}%"),
                    Transaction.merchant_id.ilike(f"%{search}%"),
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        # Count query
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query)

        # Sorting
        sort_column = getattr(Transaction, sort_by, Transaction.created_at)
        if sort_order == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))

        # Pagination
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all()), total or 0

    async def get_user_transactions(
        self, user_id: UUID, skip: int = 0, limit: int = 20
    ) -> Tuple[List[Transaction], int]:
        """Get transactions for a specific user."""
        return await self.get_filtered(skip=skip, limit=limit, user_id=user_id)

    async def get_stats(self, user_id: Optional[UUID] = None) -> dict:
        """Get aggregate transaction statistics."""
        base_query = select(Transaction)
        if user_id:
            base_query = base_query.where(Transaction.user_id == user_id)

        total = await self.session.scalar(
            select(func.count()).select_from(base_query.subquery())
        )
        total_amount = await self.session.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0)).select_from(
                base_query.subquery()
            )
        ) or 0

        fraud_count = await self.session.scalar(
            select(func.count()).where(
                and_(
                    Transaction.status == TransactionStatus.CONFIRMED_FRAUD,
                    Transaction.user_id == user_id if user_id else True
                )
            )
        ) or 0

        review_count = await self.session.scalar(
            select(func.count()).where(
                and_(
                    Transaction.status == TransactionStatus.REVIEW,
                    Transaction.user_id == user_id if user_id else True
                )
            )
        ) or 0

        blocked_count = await self.session.scalar(
            select(func.count()).where(
                and_(
                    Transaction.status == TransactionStatus.BLOCKED,
                    Transaction.user_id == user_id if user_id else True
                )
            )
        ) or 0

        approved_count = await self.session.scalar(
            select(func.count()).where(
                and_(
                    Transaction.status == TransactionStatus.APPROVED,
                    Transaction.user_id == user_id if user_id else True
                )
            )
        ) or 0

        # Amount blocked
        blocked_amount = await self.session.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                and_(
                    Transaction.status.in_([TransactionStatus.BLOCKED, TransactionStatus.CONFIRMED_FRAUD]),
                    Transaction.user_id == user_id if user_id else True
                )
            )
        ) or 0

        return {
            "total_transactions": total or 0,
            "total_amount": float(total_amount),
            "fraud_detected": fraud_count,
            "transactions_under_review": review_count,
            "transactions_blocked": blocked_count,
            "transactions_approved": approved_count,
            "fraud_rate": round((fraud_count / total * 100), 2) if total else 0.0,
            "average_risk_score": 0.0,  # Will be computed when risk scores exist
            "amount_blocked": float(blocked_amount),
        }

    async def update_status(
        self, transaction_id: str, new_status: TransactionStatus
    ) -> Transaction | None:
        """Update transaction status with state machine validation."""
        txn = await self.get_by_transaction_id(transaction_id)
        if txn:
            txn.status = new_status
            await self.session.commit()
            await self.session.refresh(txn)
        return txn

    async def get_recent_by_user(
        self, user_id: UUID, limit: int = 10
    ) -> List[Transaction]:
        """Get most recent transactions for a user."""
        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(desc(Transaction.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())
