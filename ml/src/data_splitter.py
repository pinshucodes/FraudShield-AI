"""Data splitting and class imbalance handling."""

import pandas as pd
import numpy as np
from typing import Tuple, Optional
from sklearn.model_selection import train_test_split
import logging

from ml.src.config import DataConfig

logger = logging.getLogger(__name__)


class DataSplitter:
    """Handles train/test splitting and class imbalance."""

    def __init__(self, config: Optional[DataConfig] = None):
        self.config = config or DataConfig()

    def split(
        self,
        df: pd.DataFrame,
        target_column: Optional[str] = None,
        test_size: Optional[float] = None,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """Split data into train/test with stratification."""
        target = target_column or self.config.target_column
        size = test_size or self.config.test_size

        X = df.drop(columns=[target])
        y = df[target]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=size, random_state=self.config.random_state,
            stratify=y
        )

        logger.info(f"Train: {len(X_train):,} rows ({y_train.mean():.4%} fraud)")
        logger.info(f"Test:  {len(X_test):,} rows ({y_test.mean():.4%} fraud)")

        return X_train, X_test, y_train, y_test

    def apply_smote(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        sampling_strategy: float = 0.3,
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """Apply SMOTE oversampling to handle class imbalance.
        
        Falls back to random oversampling if imblearn is not installed.
        """
        try:
            from imblearn.over_sampling import SMOTE
            smote = SMOTE(
                sampling_strategy=sampling_strategy,
                random_state=self.config.random_state,
                n_jobs=-1,
            )
            X_resampled, y_resampled = smote.fit_resample(X_train, y_train)
            logger.info(
                f"SMOTE applied: {len(X_train):,} -> {len(X_resampled):,} rows "
                f"(fraud: {y_train.sum():,} -> {y_resampled.sum():,})"
            )
            return pd.DataFrame(X_resampled, columns=X_train.columns), pd.Series(y_resampled, name=y_train.name)
        except ImportError:
            logger.warning("imblearn not installed. Using random oversampling as fallback.")
            return self._random_oversample(X_train, y_train, sampling_strategy)

    def _random_oversample(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        ratio: float = 0.3,
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """Simple random oversampling of minority class."""
        minority = X_train[y_train == 1]
        majority = X_train[y_train == 0]

        target_minority_count = int(len(majority) * ratio)
        current_minority_count = len(minority)

        if current_minority_count >= target_minority_count:
            return X_train, y_train

        # Oversample minority
        oversampled = minority.sample(
            n=target_minority_count - current_minority_count,
            replace=True,
            random_state=self.config.random_state,
        )

        X_resampled = pd.concat([X_train, oversampled], ignore_index=True)
        y_resampled = pd.concat(
            [y_train, pd.Series([1] * len(oversampled), name=y_train.name)],
            ignore_index=True,
        )

        logger.info(f"Random oversample: {len(X_train):,} -> {len(X_resampled):,} rows")
        return X_resampled, y_resampled

    def compute_class_weights(self, y: pd.Series) -> dict:
        """Compute class weights for imbalanced classification."""
        from sklearn.utils.class_weight import compute_class_weight
        classes = np.unique(y)
        weights = compute_class_weight('balanced', classes=classes, y=y)
        weight_dict = dict(zip(classes, weights))
        logger.info(f"Class weights: {weight_dict}")
        return weight_dict

    def get_scale_pos_weight(self, y: pd.Series) -> float:
        """Get scale_pos_weight for XGBoost (ratio of negative to positive)."""
        neg_count = (y == 0).sum()
        pos_count = (y == 1).sum()
        ratio = neg_count / pos_count
        logger.info(f"scale_pos_weight: {ratio:.1f} (neg={neg_count:,}, pos={pos_count:,})")
        return ratio
