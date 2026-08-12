"""ML pipeline configuration."""

from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional

# Paths
ML_ROOT = Path(__file__).parent.parent
DATA_RAW = ML_ROOT / "data" / "raw"
DATA_PROCESSED = ML_ROOT / "data" / "processed"
DATA_FEATURES = ML_ROOT / "data" / "features"
MODEL_DIR = ML_ROOT / "models"

# Ensure directories exist
for d in [DATA_RAW, DATA_PROCESSED, DATA_FEATURES, MODEL_DIR]:
    d.mkdir(parents=True, exist_ok=True)


@dataclass
class DataConfig:
    """Configuration for data processing."""
    raw_file: str = "fraudTrain.csv"
    test_file: str = "fraudTest.csv"
    target_column: str = "is_fraud"
    id_columns: List[str] = field(default_factory=lambda: ["trans_num", "Unnamed: 0"])
    drop_columns: List[str] = field(default_factory=lambda: ["Unnamed: 0", "trans_num", "first", "last", "street", "zip", "dob", "cc_num"])
    test_size: float = 0.2
    random_state: int = 42
    

@dataclass
class FeatureConfig:
    """Configuration for feature engineering."""
    # Time-based windows for aggregation
    time_windows: List[int] = field(default_factory=lambda: [1, 6, 12, 24, 72, 168])  # hours
    
    # Amount percentiles for binning
    amount_bins: List[float] = field(default_factory=lambda: [0, 10, 50, 100, 250, 500, 1000, 2500, 5000, float('inf')])
    amount_labels: List[str] = field(default_factory=lambda: ['micro', 'tiny', 'small', 'medium', 'moderate', 'large', 'xlarge', 'premium', 'luxury'])
    
    # Category columns for encoding
    category_columns: List[str] = field(default_factory=lambda: ['category', 'gender', 'state'])
    
    # Numeric columns to scale
    numeric_columns: List[str] = field(default_factory=lambda: ['amt', 'lat', 'long', 'city_pop', 'merch_lat', 'merch_long'])


@dataclass
class ModelConfig:
    """Configuration for model training."""
    models_to_train: List[str] = field(default_factory=lambda: [
        'logistic_regression', 'random_forest', 'xgboost', 'lightgbm'
    ])
    cv_folds: int = 5
    scoring_metric: str = 'f1'
    threshold_optimization_metric: str = 'f1'
    random_state: int = 42
    
    # XGBoost params
    xgb_params: Dict = field(default_factory=lambda: {
        'n_estimators': 500,
        'max_depth': 6,
        'learning_rate': 0.05,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'min_child_weight': 5,
        'scale_pos_weight': 1,  # Will be computed from class ratio
        'eval_metric': 'aucpr',
        'random_state': 42,
        'n_jobs': -1,
    })
    
    # LightGBM params
    lgbm_params: Dict = field(default_factory=lambda: {
        'n_estimators': 500,
        'max_depth': 6,
        'learning_rate': 0.05,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'min_child_samples': 50,
        'is_unbalance': True,
        'random_state': 42,
        'n_jobs': -1,
        'verbose': -1,
    })
    
    # Random Forest params
    rf_params: Dict = field(default_factory=lambda: {
        'n_estimators': 300,
        'max_depth': 15,
        'min_samples_split': 10,
        'min_samples_leaf': 5,
        'class_weight': 'balanced',
        'random_state': 42,
        'n_jobs': -1,
    })
