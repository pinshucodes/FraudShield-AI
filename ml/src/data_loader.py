"""Data loading, validation, and initial cleaning for the Sparkov fraud dataset.

The Sparkov dataset has these columns:
- Unnamed: 0, trans_date_trans_time, cc_num, merchant, category,
  amt, first, last, gender, street, city, state, zip, lat, long,
  city_pop, job, dob, trans_num, unix_time, merch_lat, merch_long, is_fraud
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
import logging

from ml.src.config import DataConfig, DATA_RAW, DATA_PROCESSED

logger = logging.getLogger(__name__)


class DataLoader:
    """Loads and validates the Sparkov fraud detection dataset."""

    EXPECTED_COLUMNS = [
        'trans_date_trans_time', 'cc_num', 'merchant', 'category',
        'amt', 'first', 'last', 'gender', 'street', 'city', 'state',
        'zip', 'lat', 'long', 'city_pop', 'job', 'dob', 'trans_num',
        'unix_time', 'merch_lat', 'merch_long', 'is_fraud'
    ]

    def __init__(self, config: Optional[DataConfig] = None):
        self.config = config or DataConfig()

    def load_raw(self, filename: Optional[str] = None) -> pd.DataFrame:
        """Load raw CSV dataset with validation."""
        filepath = DATA_RAW / (filename or self.config.raw_file)
        if not filepath.exists():
            raise FileNotFoundError(
                f"Dataset not found at {filepath}. "
                f"Download the Sparkov dataset and place it in {DATA_RAW}"
            )

        logger.info(f"Loading dataset from {filepath}")
        df = pd.read_csv(filepath)
        logger.info(f"Loaded {len(df):,} rows, {len(df.columns)} columns")

        self._validate(df)
        return df

    def _validate(self, df: pd.DataFrame) -> None:
        """Validate dataset schema."""
        missing = set(self.EXPECTED_COLUMNS) - set(df.columns)
        if missing:
            logger.warning(f"Missing expected columns: {missing}")

        # Check for target column
        if self.config.target_column not in df.columns:
            raise ValueError(f"Target column '{self.config.target_column}' not found")

        # Log class distribution
        fraud_rate = df[self.config.target_column].mean()
        fraud_count = df[self.config.target_column].sum()
        logger.info(f"Class distribution: {fraud_count:,} fraud ({fraud_rate:.4%}) / {len(df) - fraud_count:,} legitimate")

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and preprocess the raw dataset."""
        df = df.copy()

        # Parse datetime
        df['trans_date_trans_time'] = pd.to_datetime(df['trans_date_trans_time'])

        # Drop unnecessary columns (PII, IDs)
        cols_to_drop = [c for c in self.config.drop_columns if c in df.columns]
        df = df.drop(columns=cols_to_drop)

        # Handle missing values
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())

        categorical_cols = df.select_dtypes(include=['object']).columns
        df[categorical_cols] = df[categorical_cols].fillna('unknown')

        # Remove duplicates
        before = len(df)
        df = df.drop_duplicates()
        if len(df) < before:
            logger.info(f"Removed {before - len(df):,} duplicate rows")

        # Sort by time
        df = df.sort_values('trans_date_trans_time').reset_index(drop=True)

        logger.info(f"Cleaned dataset: {len(df):,} rows, {len(df.columns)} columns")
        return df

    def load_and_clean(self, filename: Optional[str] = None) -> pd.DataFrame:
        """Load, validate, and clean in one step."""
        df = self.load_raw(filename)
        return self.clean(df)

    def save_processed(self, df: pd.DataFrame, filename: str = "processed.parquet") -> Path:
        """Save processed data to parquet format."""
        filepath = DATA_PROCESSED / filename
        df.to_parquet(filepath, index=False)
        logger.info(f"Saved processed data to {filepath} ({len(df):,} rows)")
        return filepath

    def load_processed(self, filename: str = "processed.parquet") -> pd.DataFrame:
        """Load previously processed data."""
        filepath = DATA_PROCESSED / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Processed data not found at {filepath}")
        return pd.read_parquet(filepath)

    def get_data_summary(self, df: pd.DataFrame) -> dict:
        """Generate a data summary report."""
        target = self.config.target_column
        return {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "fraud_count": int(df[target].sum()),
            "legitimate_count": int(len(df) - df[target].sum()),
            "fraud_rate": float(df[target].mean()),
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "missing_values": df.isnull().sum().to_dict(),
            "memory_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
        }
