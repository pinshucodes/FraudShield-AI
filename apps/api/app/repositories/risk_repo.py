"""Repository for risk scores and fraud rules."""

from app.repositories.base import BaseRepository
from app.models.risk import RiskScore, RiskLevel
from app.models.rule import FraudRule
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Tuple, List
from uuid import UUID
import uuid as uuid_mod


class RiskScoreRepository(BaseRepository[RiskScore]):
    """Repository for risk score records."""

    def __init__(self, session: AsyncSession):
        super().__init__(RiskScore, session)

    async def get_by_transaction_id(self, transaction_id: UUID) -> RiskScore | None:
        result = await self.session.execute(
            select(RiskScore).filter_by(transaction_id=transaction_id)
        )
        return result.scalars().first()

    async def get_high_risk(self, limit: int = 50) -> List[RiskScore]:
        result = await self.session.execute(
            select(RiskScore)
            .where(RiskScore.risk_level == RiskLevel.HIGH)
            .order_by(desc(RiskScore.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_stats(self) -> dict:
        total = await self.session.scalar(select(func.count()).select_from(RiskScore)) or 0
        high = await self.session.scalar(
            select(func.count()).where(RiskScore.risk_level == RiskLevel.HIGH)
        ) or 0
        medium = await self.session.scalar(
            select(func.count()).where(RiskScore.risk_level == RiskLevel.MEDIUM)
        ) or 0
        low = await self.session.scalar(
            select(func.count()).where(RiskScore.risk_level == RiskLevel.LOW)
        ) or 0
        avg = await self.session.scalar(
            select(func.coalesce(func.avg(RiskScore.final_score), 0))
        ) or 0

        return {
            "total_scored": total,
            "high_risk_count": high,
            "medium_risk_count": medium,
            "low_risk_count": low,
            "average_score": round(float(avg), 2),
        }


class FraudRuleRepository(BaseRepository[FraudRule]):
    """Repository for fraud rules."""

    def __init__(self, session: AsyncSession):
        super().__init__(FraudRule, session)

    async def get_enabled_rules(self) -> List[FraudRule]:
        result = await self.session.execute(
            select(FraudRule).filter_by(enabled=True)
        )
        return list(result.scalars().all())

    async def get_by_rule_id(self, rule_id: str) -> FraudRule | None:
        result = await self.session.execute(
            select(FraudRule).filter_by(rule_id=rule_id)
        )
        return result.scalars().first()

    async def toggle_rule(self, rule_id: str, enabled: bool) -> FraudRule | None:
        rule = await self.get_by_rule_id(rule_id)
        if rule:
            rule.enabled = enabled
            await self.session.commit()
            await self.session.refresh(rule)
        return rule
