"""SHAP-based model explainability for fraud predictions.

Provides human-readable explanations for why a transaction
was flagged as suspicious. Uses SHAP values to identify
the most impactful features.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
import logging
import warnings

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False

from ml.src.config import MODEL_DIR

logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')


# Human-readable feature name mapping
FEATURE_DESCRIPTIONS = {
    'amt': 'Transaction amount',
    'amt_log': 'Transaction amount (log scale)',
    'amt_zscore': 'Amount deviation from average',
    'amt_ratio_to_avg': 'Amount vs. user average ratio',
    'amt_ratio_to_max': 'Amount vs. user maximum ratio',
    'amt_deviation': 'Amount standard deviation from user norm',
    'distance_to_merchant': 'Distance to merchant (km)',
    'distance_log': 'Distance to merchant (log km)',
    'is_far_merchant': 'Merchant is far from home',
    'distance_ratio_to_avg': 'Distance vs. usual distance ratio',
    'hour': 'Hour of transaction',
    'is_night': 'Transaction made at night',
    'is_weekend': 'Transaction on weekend',
    'is_business_hours': 'Transaction during business hours',
    'time_since_last_txn_hours': 'Hours since last transaction',
    'txn_count_1h': 'Transactions in last 1 hour',
    'txn_count_6h': 'Transactions in last 6 hours',
    'txn_count_24h': 'Transactions in last 24 hours',
    'txn_count_168h': 'Transactions in last 7 days',
    'merchant_fraud_rate': 'Merchant historical fraud rate',
    'category_fraud_rate': 'Category historical fraud rate',
    'is_high_risk_category': 'High-risk merchant category',
    'hour_deviation': 'Unusual transaction time for user',
    'is_unusual_category': 'Unusual category for user',
    'is_new_user': 'New user (< 5 transactions)',
    'amt_is_round': 'Round transaction amount',
    'night_high_amt': 'High amount at night',
    'velocity_amount_risk': 'Rapid expensive transactions',
    'city_pop_log': 'City population (log)',
    'is_small_city': 'Small city transaction',
}


class FraudExplainer:
    """Generates SHAP-based explanations for fraud predictions."""

    def __init__(self):
        self.explainer = None
        self.expected_value = None

    def initialize(self, model: Any, X_background: Optional[pd.DataFrame] = None) -> None:
        """Initialize SHAP explainer with the trained model."""
        if not HAS_SHAP:
            logger.warning("SHAP not installed. Explanations will use feature importance fallback.")
            return

        try:
            # Try TreeExplainer first (fastest for tree-based models)
            if hasattr(model, 'get_booster') or hasattr(model, 'booster_'):
                self.explainer = shap.TreeExplainer(model)
            elif hasattr(model, 'estimators_'):  # RandomForest
                self.explainer = shap.TreeExplainer(model)
            elif X_background is not None:
                # KernelExplainer for other models (slower)
                background = shap.sample(X_background, min(100, len(X_background)))
                self.explainer = shap.KernelExplainer(
                    model.predict_proba if hasattr(model, 'predict_proba') else model.predict,
                    background
                )
            else:
                logger.warning("Cannot determine explainer type. Background data needed.")
                return

            if hasattr(self.explainer, 'expected_value'):
                ev = self.explainer.expected_value
                self.expected_value = ev[1] if isinstance(ev, (list, np.ndarray)) else ev

            logger.info("SHAP explainer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SHAP explainer: {e}")

    def explain(
        self,
        features: pd.DataFrame,
        top_n: int = 10,
        feature_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate explanation for a single prediction."""
        if self.explainer is None:
            return self._fallback_explanation(features, feature_names)

        try:
            shap_values = self.explainer.shap_values(features)

            # Handle binary classification (take positive class)
            if isinstance(shap_values, list):
                shap_values = shap_values[1]

            if len(shap_values.shape) > 1:
                values = shap_values[0]
            else:
                values = shap_values

            names = feature_names or list(features.columns)

            # Build explanation
            feature_impacts = []
            for i, (name, value) in enumerate(zip(names, values)):
                feature_impacts.append({
                    "feature": name,
                    "display_name": FEATURE_DESCRIPTIONS.get(name, name),
                    "shap_value": round(float(value), 6),
                    "feature_value": round(float(features.iloc[0, i]), 4) if pd.notna(features.iloc[0, i]) else None,
                    "direction": "increases_risk" if value > 0 else "decreases_risk",
                    "abs_impact": round(abs(float(value)), 6),
                })

            # Sort by absolute impact
            feature_impacts.sort(key=lambda x: x['abs_impact'], reverse=True)

            # Generate natural language explanation
            top_features = feature_impacts[:top_n]
            risk_factors = [f for f in top_features if f['direction'] == 'increases_risk'][:5]
            protective_factors = [f for f in top_features if f['direction'] == 'decreases_risk'][:3]

            explanation_text = self._generate_narrative(risk_factors, protective_factors)

            return {
                "top_features": top_features,
                "all_features": feature_impacts,
                "explanation_text": explanation_text,
                "risk_factors": risk_factors,
                "protective_factors": protective_factors,
                "base_value": round(float(self.expected_value), 6) if self.expected_value is not None else None,
                "method": "shap",
            }
        except Exception as e:
            logger.error(f"SHAP explanation failed: {e}")
            return self._fallback_explanation(features, feature_names)

    def _generate_narrative(self, risk_factors: List[Dict], protective_factors: List[Dict]) -> str:
        """Generate a human-readable narrative from SHAP results."""
        parts = []

        if risk_factors:
            parts.append("This transaction was flagged due to:")
            for i, f in enumerate(risk_factors, 1):
                display = f['display_name']
                val = f.get('feature_value')
                if val is not None:
                    parts.append(f"  {i}. {display} = {val}")
                else:
                    parts.append(f"  {i}. {display}")

        if protective_factors:
            parts.append("\nFactors reducing risk:")
            for f in protective_factors:
                display = f['display_name']
                parts.append(f"  - {display}")

        return "\n".join(parts) if parts else "No significant risk factors identified."

    def _fallback_explanation(self, features: pd.DataFrame, feature_names: Optional[List[str]] = None) -> Dict:
        """Simple feature importance-based explanation when SHAP isn't available."""
        names = feature_names or list(features.columns)
        values = features.iloc[0].values

        feature_impacts = []
        for name, value in zip(names, values):
            feature_impacts.append({
                "feature": name,
                "display_name": FEATURE_DESCRIPTIONS.get(name, name),
                "feature_value": round(float(value), 4) if pd.notna(value) else None,
                "abs_impact": abs(float(value)) if pd.notna(value) else 0,
                "direction": "unknown",
            })

        feature_impacts.sort(key=lambda x: x['abs_impact'], reverse=True)

        return {
            "top_features": feature_impacts[:10],
            "all_features": feature_impacts,
            "explanation_text": "SHAP not available. Showing raw feature values.",
            "risk_factors": [],
            "protective_factors": [],
            "method": "feature_values_fallback",
        }

    def explain_batch(self, features: pd.DataFrame, top_n: int = 5) -> List[Dict]:
        """Generate explanations for a batch of predictions."""
        results = []
        for i in range(len(features)):
            row = features.iloc[[i]]
            results.append(self.explain(row, top_n=top_n))
        return results
