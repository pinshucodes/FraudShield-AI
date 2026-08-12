"""Risk scoring and fraud rules API endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from app.schemas.risk import (
    RiskScoreResponse,
    RiskAssessmentResponse,
    FraudRuleCreate,
    FraudRuleResponse,
    FraudRuleUpdate,
    RiskDashboardStats,
)
from app.schemas.common import APIResponse
from app.services.risk_engine import RiskEngine
from app.repositories.risk_repo import RiskScoreRepository, FraudRuleRepository
from app.repositories.transaction_repo import TransactionRepository
from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.models.user import User, UserRole
from app.models.rule import FraudRule
import random
import string

router = APIRouter()


@router.post("/{transaction_id}/assess", response_model=APIResponse)
async def assess_transaction_risk(
    transaction_id: str,
    current_user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger risk assessment for a transaction."""
    txn_repo = TransactionRepository(db)
    txn = await txn_repo.get_by_transaction_id(transaction_id)
    if not txn:
        from app.core.exceptions import NotFoundError
        raise NotFoundError(message=f"Transaction {transaction_id} not found")

    engine = RiskEngine(db)
    result = await engine.assess_risk(txn)
    return APIResponse(data=RiskAssessmentResponse(**result))


@router.get("/{transaction_id}/score", response_model=APIResponse)
async def get_risk_score(
    transaction_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get risk score for a transaction."""
    txn_repo = TransactionRepository(db)
    txn = await txn_repo.get_by_transaction_id(transaction_id)
    if not txn:
        from app.core.exceptions import NotFoundError
        raise NotFoundError(message=f"Transaction {transaction_id} not found")

    risk_repo = RiskScoreRepository(db)
    score = await risk_repo.get_by_transaction_id(txn.id)
    if not score:
        from app.core.exceptions import NotFoundError
        raise NotFoundError(message="Risk score not yet computed")

    return APIResponse(data=RiskScoreResponse.model_validate(score))


@router.get("/stats", response_model=APIResponse)
async def get_risk_stats(
    current_user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Get risk scoring statistics."""
    engine = RiskEngine(db)
    stats = await engine.get_risk_stats()
    return APIResponse(data=RiskDashboardStats(**stats))


@router.get("/high-risk", response_model=APIResponse)
async def get_high_risk_transactions(
    current_user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Get recent high-risk transactions."""
    risk_repo = RiskScoreRepository(db)
    scores = await risk_repo.get_high_risk(limit=50)
    return APIResponse(data=[RiskScoreResponse.model_validate(s) for s in scores])


# --- Fraud Rules CRUD ---

@router.get("/rules", response_model=APIResponse)
async def list_rules(
    current_user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """List all fraud detection rules."""
    rule_repo = FraudRuleRepository(db)
    rules, total = await rule_repo.get_all()
    return APIResponse(data=[FraudRuleResponse.model_validate(r) for r in rules])


@router.post("/rules", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    request: FraudRuleCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Create a new fraud detection rule."""
    rule_repo = FraudRuleRepository(db)
    rule_id = f"RULE-{''.join(random.choices(string.digits, k=6))}"
    rule = await rule_repo.create(
        rule_id=rule_id,
        name=request.name,
        description=request.description,
        rule_type=request.rule_type,
        severity=request.severity,
        enabled=request.enabled,
        config=request.config,
        created_by=current_user.id,
    )
    return APIResponse(data=FraudRuleResponse.model_validate(rule))


@router.put("/rules/{rule_id}", response_model=APIResponse)
async def update_rule(
    rule_id: str,
    request: FraudRuleUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Update a fraud detection rule."""
    rule_repo = FraudRuleRepository(db)
    rule = await rule_repo.get_by_rule_id(rule_id)
    if not rule:
        from app.core.exceptions import NotFoundError
        raise NotFoundError(message=f"Rule {rule_id} not found")

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)
    await db.commit()
    await db.refresh(rule)
    return APIResponse(data=FraudRuleResponse.model_validate(rule))


@router.delete("/rules/{rule_id}", response_model=APIResponse)
async def delete_rule(
    rule_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Delete a fraud detection rule."""
    rule_repo = FraudRuleRepository(db)
    rule = await rule_repo.get_by_rule_id(rule_id)
    if not rule:
        from app.core.exceptions import NotFoundError
        raise NotFoundError(message=f"Rule {rule_id} not found")
    await db.delete(rule)
    await db.commit()
    return APIResponse(message=f"Rule {rule_id} deleted")
