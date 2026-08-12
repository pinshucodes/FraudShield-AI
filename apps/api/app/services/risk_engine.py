"""Risk Engine — combines ML, rules, behavioral, and anomaly signals.

The risk engine produces a unified risk score (0-100) by weighting:
- ML Model Score (60% weight): XGBoost/LightGBM fraud probability
- Rule Engine Score (20% weight): Configurable threshold/velocity/geo rules
- Behavioral Score (10% weight): Deviation from user's typical patterns
- Anomaly Score (10% weight): Statistical outlier detection

The final score determines the risk level:
- LOW: 0-30
- MEDIUM: 31-70
- HIGH: 71-100
"""

import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import uuid
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.risk import RiskScore, RiskLevel, TransactionFeature, ModelPrediction
from app.models.transaction import Transaction, TransactionStatus
from app.models.rule import FraudRule
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("risk_engine")

# Scoring weights
ML_WEIGHT = 0.60
RULE_WEIGHT = 0.20
BEHAVIORAL_WEIGHT = 0.10
ANOMALY_WEIGHT = 0.10


class RuleEngine:
    """Evaluates configurable fraud detection rules."""

    # Default rules applied when no database rules are configured
    DEFAULT_RULES = [
        {
            "name": "High Amount",
            "type": "threshold",
            "config": {"field": "amount", "operator": ">", "value": 50000},
            "score": 30,
            "severity": "MEDIUM",
        },
        {
            "name": "Very High Amount",
            "type": "threshold",
            "config": {"field": "amount", "operator": ">", "value": 100000},
            "score": 60,
            "severity": "HIGH",
        },
        {
            "name": "Night Transaction",
            "type": "time",
            "config": {"start_hour": 0, "end_hour": 5},
            "score": 15,
            "severity": "LOW",
        },
        {
            "name": "High Risk Category",
            "type": "category",
            "config": {"categories": ["electronics", "jewelry", "gaming"]},
            "score": 10,
            "severity": "LOW",
        },
        {
            "name": "International Transaction",
            "type": "geo",
            "config": {"max_distance_km": 500},
            "score": 25,
            "severity": "MEDIUM",
        },
    ]

    def evaluate(self, transaction_data: Dict[str, Any]) -> tuple[float, List[Dict]]:
        """Evaluate all rules against a transaction. Returns (score 0-100, triggered_rules)."""
        triggered = []
        total_score = 0

        for rule in self.DEFAULT_RULES:
            result = self._evaluate_rule(rule, transaction_data)
            if result:
                triggered.append({
                    "rule_name": rule["name"],
                    "severity": rule["severity"],
                    "score": rule["score"],
                    "reason": result,
                })
                total_score += rule["score"]

        # Cap at 100
        return min(total_score, 100), triggered

    def _evaluate_rule(self, rule: Dict, data: Dict) -> Optional[str]:
        """Evaluate a single rule. Returns reason string if triggered, None otherwise."""
        rule_type = rule["type"]
        config = rule["config"]

        if rule_type == "threshold":
            field = config["field"]
            value = data.get(field, 0)
            threshold = config["value"]
            op = config.get("operator", ">")
            if op == ">" and value > threshold:
                return f"{field} ({value}) exceeds threshold ({threshold})"
            elif op == "<" and value < threshold:
                return f"{field} ({value}) below threshold ({threshold})"

        elif rule_type == "time":
            hour = data.get("hour", 12)
            if config["start_hour"] <= hour <= config["end_hour"]:
                return f"Transaction at {hour}:00 (risky hours {config['start_hour']}-{config['end_hour']})"

        elif rule_type == "category":
            category = data.get("merchant_category", "")
            if category in config.get("categories", []):
                return f"High-risk category: {category}"

        elif rule_type == "geo":
            distance = data.get("distance_km", 0)
            max_dist = config.get("max_distance_km", 500)
            if distance > max_dist:
                return f"Distance {distance:.0f}km exceeds {max_dist}km threshold"

        return None


class BehavioralScorer:
    """Scores transactions based on deviation from user's typical behavior."""

    def score(self, transaction_data: Dict[str, Any]) -> float:
        """Compute behavioral anomaly score (0-100)."""
        scores = []

        # Amount deviation
        amt_ratio = transaction_data.get("amt_ratio_to_avg", 1.0)
        if amt_ratio > 5:
            scores.append(80)
        elif amt_ratio > 3:
            scores.append(50)
        elif amt_ratio > 2:
            scores.append(30)
        else:
            scores.append(0)

        # Hour deviation
        hour_dev = transaction_data.get("hour_deviation", 0)
        if hour_dev > 8:
            scores.append(40)
        elif hour_dev > 4:
            scores.append(20)
        else:
            scores.append(0)

        # Unusual category
        if transaction_data.get("is_unusual_category", 0):
            scores.append(30)

        # New device
        if transaction_data.get("is_new_device", 0):
            scores.append(40)

        # Velocity
        txn_1h = transaction_data.get("txn_count_1h", 1)
        if txn_1h > 5:
            scores.append(70)
        elif txn_1h > 3:
            scores.append(40)

        return min(np.mean(scores) if scores else 0, 100)


class AnomalyScorer:
    """Statistical anomaly detection scoring."""

    def score(self, transaction_data: Dict[str, Any]) -> float:
        """Compute anomaly score (0-100) based on statistical outliers."""
        anomaly_signals = []

        # Amount z-score
        zscore = abs(transaction_data.get("amt_zscore", 0))
        if zscore > 3:
            anomaly_signals.append(90)
        elif zscore > 2:
            anomaly_signals.append(60)
        elif zscore > 1.5:
            anomaly_signals.append(30)
        else:
            anomaly_signals.append(0)

        # Distance anomaly
        dist_ratio = transaction_data.get("distance_ratio_to_avg", 1.0)
        if dist_ratio > 10:
            anomaly_signals.append(80)
        elif dist_ratio > 5:
            anomaly_signals.append(50)
        elif dist_ratio > 2:
            anomaly_signals.append(20)
        else:
            anomaly_signals.append(0)

        # Time anomaly
        time_since = transaction_data.get("time_since_last_txn_hours", 24)
        if time_since < 0.05:  # Less than 3 minutes
            anomaly_signals.append(70)
        elif time_since < 0.17:  # Less than 10 minutes
            anomaly_signals.append(40)

        return min(np.mean(anomaly_signals) if anomaly_signals else 0, 100)


class RiskEngine:
    """Unified risk scoring engine combining ML, rules, behavioral, and anomaly signals."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.rule_engine = RuleEngine()
        self.behavioral_scorer = BehavioralScorer()
        self.anomaly_scorer = AnomalyScorer()

    async def assess_risk(self, transaction: Transaction, features: Optional[Dict] = None) -> Dict[str, Any]:
        """Perform full risk assessment on a transaction.
        
        Args:
            transaction: The Transaction ORM object
            features: Optional pre-computed features dict
            
        Returns:
            Complete risk assessment result
        """
        import time
        start = time.time()

        # Build transaction data dict for rule evaluation
        txn_data = {
            "amount": float(transaction.amount),
            "merchant_category": transaction.merchant_category,
            "hour": datetime.now(timezone.utc).hour,
            "device_id": transaction.device_id,
            "ip_address": transaction.ip_address,
            **(features or {}),
        }

        # 1. ML Score (placeholder — will use FraudPredictor when model is trained)
        ml_score = features.get("fraud_probability", 0.0) * 100 if features else 0.0

        # 2. Rule Score
        rule_score, triggered_rules = self.rule_engine.evaluate(txn_data)

        # 3. Behavioral Score
        behavioral_score = self.behavioral_scorer.score(txn_data)

        # 4. Anomaly Score
        anomaly_score = self.anomaly_scorer.score(txn_data)

        # Weighted combination
        final_score = (
            ml_score * ML_WEIGHT +
            rule_score * RULE_WEIGHT +
            behavioral_score * BEHAVIORAL_WEIGHT +
            anomaly_score * ANOMALY_WEIGHT
        )
        final_score = round(min(max(final_score, 0), 100), 2)

        # Determine risk level
        if final_score <= settings.RISK_LOW_MAX:
            risk_level = RiskLevel.LOW
            action = "APPROVE"
        elif final_score <= settings.RISK_MEDIUM_MAX:
            risk_level = RiskLevel.MEDIUM
            action = "REVIEW"
        else:
            risk_level = RiskLevel.HIGH
            action = "BLOCK"

        latency_ms = (time.time() - start) * 1000

        # Persist risk score
        risk_record = RiskScore(
            transaction_id=transaction.id,
            ml_score=round(ml_score, 4),
            rule_score=round(rule_score, 4),
            behavioral_score=round(behavioral_score, 4),
            anomaly_score=round(anomaly_score, 4),
            final_score=final_score,
            risk_level=risk_level,
            explanation={
                "triggered_rules": triggered_rules,
                "ml_score": ml_score,
                "rule_score": rule_score,
                "behavioral_score": behavioral_score,
                "anomaly_score": anomaly_score,
            },
        )
        self.db.add(risk_record)

        # Update transaction status based on risk
        if action == "APPROVE":
            transaction.status = TransactionStatus.APPROVED
            transaction.risk_level = RiskLevel.LOW
        elif action == "REVIEW":
            transaction.status = TransactionStatus.REVIEW
            transaction.risk_level = RiskLevel.MEDIUM
        else:
            transaction.status = TransactionStatus.BLOCKED
            transaction.risk_level = RiskLevel.HIGH

        await self.db.commit()
        await self.db.refresh(risk_record)

        logger.info(
            "risk_assessed",
            transaction_id=transaction.transaction_id,
            final_score=final_score,
            risk_level=risk_level.value,
            action=action,
        )

        return {
            "transaction_id": transaction.transaction_id,
            "risk_score": final_score,
            "risk_level": risk_level.value,
            "is_fraud_predicted": final_score > settings.RISK_MEDIUM_MAX,
            "fraud_probability": ml_score / 100,
            "ml_score": round(ml_score, 2),
            "rule_score": round(rule_score, 2),
            "behavioral_score": round(behavioral_score, 2),
            "anomaly_score": round(anomaly_score, 2),
            "triggered_rules": triggered_rules,
            "explanation": risk_record.explanation,
            "recommended_action": action,
            "inference_latency_ms": round(latency_ms, 2),
            "model_version": "v1",
        }

    async def get_risk_stats(self) -> Dict:
        """Get risk scoring statistics."""
        total = await self.db.scalar(select(func.count()).select_from(RiskScore)) or 0
        high = await self.db.scalar(
            select(func.count()).where(RiskScore.risk_level == RiskLevel.HIGH)
        ) or 0
        medium = await self.db.scalar(
            select(func.count()).where(RiskScore.risk_level == RiskLevel.MEDIUM)
        ) or 0
        low = await self.db.scalar(
            select(func.count()).where(RiskScore.risk_level == RiskLevel.LOW)
        ) or 0
        avg_score = await self.db.scalar(
            select(func.coalesce(func.avg(RiskScore.final_score), 0))
        ) or 0

        return {
            "total_scored": total,
            "high_risk_count": high,
            "medium_risk_count": medium,
            "low_risk_count": low,
            "average_score": round(float(avg_score), 2),
        }
