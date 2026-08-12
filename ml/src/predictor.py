"""Real-time fraud prediction service.

Loads a trained model and provides prediction interface
for the FastAPI risk scoring engine.
"""

import numpy as np
import pandas as pd
import joblib
import json
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Any
import logging
import time

from ml.src.config import MODEL_DIR

logger = logging.getLogger(__name__)


class FraudPredictor:
    """Loads a trained model and provides fraud prediction."""

    def __init__(self, model_version: str = "v1"):
        self.model_version = model_version
        self.model = None
        self.threshold = 0.5
        self.metadata: Dict = {}
        self.is_loaded = False

    def load(self, model_dir: Optional[Path] = None) -> None:
        """Load model, threshold, and metadata from disk."""
        if model_dir is None:
            model_dir = MODEL_DIR / self.model_version

        model_path = model_dir / "model.joblib"
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found at {model_path}")

        self.model = joblib.load(model_path)

        # Load threshold
        threshold_path = model_dir / "threshold.json"
        if threshold_path.exists():
            with open(threshold_path) as f:
                self.threshold = json.load(f).get("threshold", 0.5)

        # Load metadata
        metadata_path = model_dir / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path) as f:
                self.metadata = json.load(f)

        self.is_loaded = True
        logger.info(
            f"Model loaded: {self.metadata.get('model_name', 'unknown')} "
            f"v{self.model_version} (threshold={self.threshold:.4f})"
        )

    def predict(self, features: pd.DataFrame) -> Dict[str, Any]:
        """Make fraud prediction on a single transaction's features.
        
        Returns:
            Dict with: fraud_probability, is_fraud, risk_level, risk_score,
                       inference_latency_ms, model_version
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load() first.")

        start_time = time.time()

        # Clean input
        features_clean = features.replace([np.inf, -np.inf], np.nan).fillna(0)

        # Predict probability
        if hasattr(self.model, 'predict_proba'):
            proba = float(self.model.predict_proba(features_clean)[:, 1][0])
        else:
            proba = float(self.model.decision_function(features_clean)[0])
            # Normalize to 0-1
            proba = 1 / (1 + np.exp(-proba))

        # Apply threshold
        is_fraud = proba >= self.threshold

        # Compute risk score (0-100)
        risk_score = min(100, max(0, proba * 100))

        # Determine risk level
        if risk_score <= 30:
            risk_level = "LOW"
        elif risk_score <= 70:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        latency_ms = (time.time() - start_time) * 1000

        return {
            "fraud_probability": round(proba, 6),
            "is_fraud": bool(is_fraud),
            "risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "inference_latency_ms": round(latency_ms, 2),
            "model_version": self.model_version,
            "model_name": self.metadata.get("model_name", "unknown"),
            "threshold": self.threshold,
        }

    def predict_batch(self, features: pd.DataFrame) -> pd.DataFrame:
        """Make predictions on a batch of transactions."""
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load() first.")

        features_clean = features.replace([np.inf, -np.inf], np.nan).fillna(0)

        if hasattr(self.model, 'predict_proba'):
            probas = self.model.predict_proba(features_clean)[:, 1]
        else:
            scores = self.model.decision_function(features_clean)
            probas = 1 / (1 + np.exp(-scores))

        results = pd.DataFrame({
            'fraud_probability': probas,
            'is_fraud': probas >= self.threshold,
            'risk_score': np.clip(probas * 100, 0, 100),
            'risk_level': pd.cut(
                probas * 100,
                bins=[0, 30, 70, 100],
                labels=['LOW', 'MEDIUM', 'HIGH'],
                include_lowest=True
            ),
        })

        return results

    def get_model_info(self) -> Dict:
        """Return model metadata."""
        return {
            "model_version": self.model_version,
            "model_name": self.metadata.get("model_name"),
            "is_loaded": self.is_loaded,
            "threshold": self.threshold,
            "metrics": self.metadata.get("metrics", {}),
        }
