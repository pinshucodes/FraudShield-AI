"""Model training pipeline for fraud detection.

Trains multiple classifiers, performs cross-validation,
optimizes thresholds, and saves the best model.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import joblib
import json
import time
import logging

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    roc_auc_score, precision_recall_curve, f1_score,
    average_precision_score, classification_report
)

try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

try:
    from lightgbm import LGBMClassifier
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False

from ml.src.config import ModelConfig, MODEL_DIR

logger = logging.getLogger(__name__)


class FraudModelTrainer:
    """Trains and evaluates multiple fraud detection models."""

    def __init__(self, config: Optional[ModelConfig] = None):
        self.config = config or ModelConfig()
        self.models: Dict[str, Any] = {}
        self.results: Dict[str, Dict] = {}
        self.best_model_name: Optional[str] = None
        self.best_threshold: float = 0.5
        self.scaler = StandardScaler()

    def _build_models(self, scale_pos_weight: float = 1.0) -> Dict[str, Any]:
        """Initialize all model instances."""
        models = {}

        # Logistic Regression (with scaling)
        models['logistic_regression'] = Pipeline([
            ('scaler', StandardScaler()),
            ('clf', LogisticRegression(
                max_iter=1000,
                class_weight='balanced',
                random_state=self.config.random_state,
                solver='lbfgs',
                n_jobs=-1,
            ))
        ])

        # Random Forest
        rf_params = self.config.rf_params.copy()
        models['random_forest'] = RandomForestClassifier(**rf_params)

        # XGBoost
        if HAS_XGBOOST:
            xgb_params = self.config.xgb_params.copy()
            xgb_params['scale_pos_weight'] = scale_pos_weight
            models['xgboost'] = XGBClassifier(**xgb_params)

        # LightGBM
        if HAS_LIGHTGBM:
            lgbm_params = self.config.lgbm_params.copy()
            models['lightgbm'] = LGBMClassifier(**lgbm_params)

        return models

    def train_all(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        scale_pos_weight: float = 1.0,
    ) -> Dict[str, Dict]:
        """Train all models, evaluate, and find the best one."""
        models = self._build_models(scale_pos_weight)
        results = {}

        # Handle any remaining inf/nan
        X_train = X_train.replace([np.inf, -np.inf], np.nan).fillna(0)
        X_test = X_test.replace([np.inf, -np.inf], np.nan).fillna(0)

        for name, model in models.items():
            if name not in self.config.models_to_train:
                continue
            logger.info(f"\n{'='*60}")
            logger.info(f"Training: {name}")
            logger.info(f"{'='*60}")

            start_time = time.time()

            # Train
            model.fit(X_train, y_train)
            train_time = time.time() - start_time

            # Predict
            if hasattr(model, 'predict_proba'):
                y_proba = model.predict_proba(X_test)[:, 1]
            else:
                y_proba = model.decision_function(X_test)

            # Find optimal threshold
            optimal_threshold = self._find_optimal_threshold(y_test, y_proba)
            y_pred = (y_proba >= optimal_threshold).astype(int)

            # Evaluate
            metrics = self._evaluate(y_test, y_pred, y_proba)
            metrics['train_time_seconds'] = round(train_time, 2)
            metrics['optimal_threshold'] = round(optimal_threshold, 4)
            metrics['n_features'] = X_train.shape[1]

            results[name] = metrics
            self.models[name] = model

            logger.info(f"  ROC-AUC:  {metrics['roc_auc']:.4f}")
            logger.info(f"  PR-AUC:   {metrics['pr_auc']:.4f}")
            logger.info(f"  F1:       {metrics['f1']:.4f}")
            logger.info(f"  Precision:{metrics['precision']:.4f}")
            logger.info(f"  Recall:   {metrics['recall']:.4f}")
            logger.info(f"  Threshold:{optimal_threshold:.4f}")
            logger.info(f"  Time:     {train_time:.1f}s")

        self.results = results
        self._select_best_model()
        return results

    def cross_validate(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        model_name: str = 'xgboost',
    ) -> Dict[str, float]:
        """Perform stratified k-fold cross-validation."""
        models = self._build_models()
        model = models.get(model_name)
        if not model:
            raise ValueError(f"Model '{model_name}' not found")

        X_clean = X.replace([np.inf, -np.inf], np.nan).fillna(0)

        cv = StratifiedKFold(n_splits=self.config.cv_folds, shuffle=True, random_state=self.config.random_state)
        scoring = ['f1', 'roc_auc', 'precision', 'recall', 'average_precision']

        cv_results = cross_validate(
            model, X_clean, y, cv=cv, scoring=scoring,
            return_train_score=True, n_jobs=-1
        )

        summary = {}
        for metric in scoring:
            test_key = f'test_{metric}'
            summary[f'{metric}_mean'] = float(np.mean(cv_results[test_key]))
            summary[f'{metric}_std'] = float(np.std(cv_results[test_key]))

        logger.info(f"\nCross-validation results for {model_name}:")
        for k, v in summary.items():
            logger.info(f"  {k}: {v:.4f}")

        return summary

    def _find_optimal_threshold(self, y_true: pd.Series, y_proba: np.ndarray) -> float:
        """Find the threshold that maximizes F1 score."""
        precisions, recalls, thresholds = precision_recall_curve(y_true, y_proba)

        # Compute F1 for each threshold
        f1_scores = 2 * (precisions * recalls) / (precisions + recalls + 1e-8)
        best_idx = np.argmax(f1_scores)

        if best_idx < len(thresholds):
            return float(thresholds[best_idx])
        return 0.5

    def _evaluate(self, y_true: pd.Series, y_pred: np.ndarray, y_proba: np.ndarray) -> Dict[str, float]:
        """Compute comprehensive evaluation metrics."""
        from sklearn.metrics import (
            accuracy_score, precision_score, recall_score,
            f1_score, confusion_matrix, matthews_corrcoef
        )

        cm = confusion_matrix(y_true, y_pred)
        tn, fp, fn, tp = cm.ravel()

        return {
            'accuracy': round(float(accuracy_score(y_true, y_pred)), 4),
            'precision': round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
            'recall': round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
            'f1': round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
            'roc_auc': round(float(roc_auc_score(y_true, y_proba)), 4),
            'pr_auc': round(float(average_precision_score(y_true, y_proba)), 4),
            'mcc': round(float(matthews_corrcoef(y_true, y_pred)), 4),
            'true_positives': int(tp),
            'false_positives': int(fp),
            'true_negatives': int(tn),
            'false_negatives': int(fn),
            'false_positive_rate': round(float(fp / (fp + tn + 1e-8)), 4),
            'false_negative_rate': round(float(fn / (fn + tp + 1e-8)), 4),
        }

    def _select_best_model(self) -> None:
        """Select best model based on PR-AUC (better for imbalanced data)."""
        if not self.results:
            return

        best_name = max(self.results, key=lambda k: self.results[k].get('pr_auc', 0))
        self.best_model_name = best_name
        self.best_threshold = self.results[best_name].get('optimal_threshold', 0.5)

        logger.info(f"\n{'='*60}")
        logger.info(f"Best model: {best_name} (PR-AUC: {self.results[best_name]['pr_auc']:.4f})")
        logger.info(f"{'='*60}")

    def save_best_model(self, version: str = "v1") -> Path:
        """Save the best model, threshold, and metadata."""
        if not self.best_model_name:
            raise ValueError("No model trained yet")

        model_dir = MODEL_DIR / version
        model_dir.mkdir(parents=True, exist_ok=True)

        model = self.models[self.best_model_name]

        # Save model
        model_path = model_dir / "model.joblib"
        joblib.dump(model, model_path)

        # Save metadata
        metadata = {
            "model_name": self.best_model_name,
            "version": version,
            "threshold": self.best_threshold,
            "metrics": self.results[self.best_model_name],
            "all_results": self.results,
            "feature_count": self.results[self.best_model_name].get('n_features', 0),
        }
        metadata_path = model_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)

        # Save threshold
        threshold_path = model_dir / "threshold.json"
        with open(threshold_path, 'w') as f:
            json.dump({"threshold": self.best_threshold}, f)

        logger.info(f"Model saved to {model_dir}")
        return model_dir

    def save_all_models(self, version: str = "v1") -> None:
        """Save all trained models."""
        for name, model in self.models.items():
            model_dir = MODEL_DIR / version / name
            model_dir.mkdir(parents=True, exist_ok=True)
            joblib.dump(model, model_dir / "model.joblib")
            if name in self.results:
                with open(model_dir / "metrics.json", 'w') as f:
                    json.dump(self.results[name], f, indent=2, default=str)
        logger.info(f"All {len(self.models)} models saved.")

    def get_comparison_table(self) -> pd.DataFrame:
        """Return a comparison table of all model results."""
        if not self.results:
            return pd.DataFrame()
        df = pd.DataFrame(self.results).T
        df = df.sort_values('pr_auc', ascending=False)
        return df
