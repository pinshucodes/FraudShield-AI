"""Feature engineering pipeline for fraud detection.

Generates 40+ features across these categories:
1. Temporal features (hour, day, weekend, time since last txn)
2. Amount features (log transform, z-score, ratio to average)
3. Frequency/velocity features (txn count in time windows)
4. Geographic features (distance from home, merchant distance)
5. Behavioral features (deviation from user's typical patterns)
6. Merchant features (merchant fraud rate, category risk)
7. Interaction features (cross-category)
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict
from math import radians, cos, sin, asin, sqrt
import logging
import warnings

from ml.src.config import FeatureConfig, DATA_FEATURES

logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore', category=pd.errors.PerformanceWarning)


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on earth (km)."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * 6371 * asin(sqrt(a))


class FeatureEngineer:
    """Generates fraud detection features from transaction data."""

    def __init__(self, config: Optional[FeatureConfig] = None):
        self.config = config or FeatureConfig()
        self.feature_names: List[str] = []

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply all feature engineering transformations."""
        logger.info(f"Starting feature engineering on {len(df):,} rows")
        df = df.copy()

        # Ensure datetime column
        if 'trans_date_trans_time' in df.columns:
            df['trans_date_trans_time'] = pd.to_datetime(df['trans_date_trans_time'])

        # Apply feature groups
        df = self._temporal_features(df)
        df = self._amount_features(df)
        df = self._geographic_features(df)
        df = self._frequency_features(df)
        df = self._behavioral_features(df)
        df = self._merchant_features(df)
        df = self._interaction_features(df)
        df = self._encode_categoricals(df)

        # Track feature names (exclude target and datetime)
        exclude = {'is_fraud', 'trans_date_trans_time', 'cc_num', 'merchant', 'city', 'job'}
        self.feature_names = [c for c in df.columns if c not in exclude]

        logger.info(f"Feature engineering complete. {len(self.feature_names)} features generated.")
        return df

    def _temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract temporal features from transaction timestamp."""
        dt = df['trans_date_trans_time']

        # Basic time features
        df['hour'] = dt.dt.hour
        df['day_of_week'] = dt.dt.dayofweek
        df['day_of_month'] = dt.dt.day
        df['month'] = dt.dt.month
        df['is_weekend'] = (dt.dt.dayofweek >= 5).astype(int)

        # Time-of-day categories
        df['is_night'] = ((df['hour'] >= 22) | (df['hour'] <= 5)).astype(int)
        df['is_business_hours'] = ((df['hour'] >= 9) & (df['hour'] <= 17) & (df['is_weekend'] == 0)).astype(int)

        # Cyclical encoding for hour and day
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)

        # Time since last transaction per user (cc_num)
        if 'cc_num' in df.columns:
            df = df.sort_values(['cc_num', 'trans_date_trans_time'])
            df['time_since_last_txn'] = df.groupby('cc_num')['trans_date_trans_time'].diff().dt.total_seconds().fillna(0)
            df['time_since_last_txn_hours'] = df['time_since_last_txn'] / 3600

        logger.info("  [+] Temporal features: 13 features")
        return df

    def _amount_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer amount-based features."""
        # Log transform (handles skewness)
        df['amt_log'] = np.log1p(df['amt'])

        # Amount bins
        df['amt_bin'] = pd.cut(
            df['amt'],
            bins=self.config.amount_bins,
            labels=self.config.amount_labels,
            include_lowest=True
        ).astype(str)

        # Z-score of amount (global)
        amt_mean = df['amt'].mean()
        amt_std = df['amt'].std()
        df['amt_zscore'] = (df['amt'] - amt_mean) / (amt_std + 1e-8)

        # Is the amount a round number?
        df['amt_is_round'] = ((df['amt'] % 10 == 0) | (df['amt'] % 100 == 0)).astype(int)

        # Amount percentile rank
        df['amt_percentile'] = df['amt'].rank(pct=True)

        # Per-user amount statistics
        if 'cc_num' in df.columns:
            user_stats = df.groupby('cc_num')['amt'].agg(['mean', 'std', 'median', 'max']).reset_index()
            user_stats.columns = ['cc_num', 'user_avg_amt', 'user_std_amt', 'user_median_amt', 'user_max_amt']
            df = df.merge(user_stats, on='cc_num', how='left')

            # Ratio of current amount to user's average
            df['amt_ratio_to_avg'] = df['amt'] / (df['user_avg_amt'] + 1e-8)
            df['amt_ratio_to_max'] = df['amt'] / (df['user_max_amt'] + 1e-8)
            df['amt_deviation'] = (df['amt'] - df['user_avg_amt']) / (df['user_std_amt'] + 1e-8)

        logger.info("  [+] Amount features: 11 features")
        return df

    def _geographic_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer geographic features."""
        # Distance between cardholder and merchant
        if all(c in df.columns for c in ['lat', 'long', 'merch_lat', 'merch_long']):
            df['distance_to_merchant'] = df.apply(
                lambda r: haversine(r['lat'], r['long'], r['merch_lat'], r['merch_long']),
                axis=1
            )
            df['distance_log'] = np.log1p(df['distance_to_merchant'])

            # Is the merchant far away? (> 100km)
            df['is_far_merchant'] = (df['distance_to_merchant'] > 100).astype(int)

            # Per-user average distance
            if 'cc_num' in df.columns:
                user_dist = df.groupby('cc_num')['distance_to_merchant'].mean().reset_index()
                user_dist.columns = ['cc_num', 'user_avg_distance']
                df = df.merge(user_dist, on='cc_num', how='left')
                df['distance_ratio_to_avg'] = df['distance_to_merchant'] / (df['user_avg_distance'] + 1e-8)

        # City population features
        if 'city_pop' in df.columns:
            df['city_pop_log'] = np.log1p(df['city_pop'])
            df['is_small_city'] = (df['city_pop'] < 50000).astype(int)

        logger.info("  [+] Geographic features: 7 features")
        return df

    def _frequency_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute transaction frequency/velocity features per user."""
        if 'cc_num' not in df.columns:
            return df

        df = df.sort_values(['cc_num', 'trans_date_trans_time'])

        for window_hours in self.config.time_windows:
            window_td = pd.Timedelta(hours=window_hours)
            col_name = f'txn_count_{window_hours}h'
            amt_col_name = f'txn_amt_sum_{window_hours}h'

            # Rolling count of transactions per user in window
            # Using a more efficient approach with groupby + rolling
            df[col_name] = (
                df.set_index('trans_date_trans_time')
                .groupby('cc_num')['amt']
                .transform(lambda x: x.rolling(window_td, min_periods=1).count())
                .values
            )

            # Rolling sum of amounts in window
            df[amt_col_name] = (
                df.set_index('trans_date_trans_time')
                .groupby('cc_num')['amt']
                .transform(lambda x: x.rolling(window_td, min_periods=1).sum())
                .values
            )

        logger.info(f"  [+] Frequency features: {len(self.config.time_windows) * 2} features")
        return df

    def _behavioral_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Features capturing deviation from user's typical behavior."""
        if 'cc_num' not in df.columns:
            return df

        # User's typical transaction hour
        user_hour_mode = df.groupby('cc_num')['hour'].agg(lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else 12).reset_index()
        user_hour_mode.columns = ['cc_num', 'user_typical_hour']
        df = df.merge(user_hour_mode, on='cc_num', how='left')
        df['hour_deviation'] = abs(df['hour'] - df['user_typical_hour'])

        # User's typical category (most common)
        if 'category' in df.columns:
            user_cat = df.groupby('cc_num')['category'].agg(lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else 'unknown').reset_index()
            user_cat.columns = ['cc_num', 'user_typical_category']
            df = df.merge(user_cat, on='cc_num', how='left')
            df['is_unusual_category'] = (df['category'] != df['user_typical_category']).astype(int)

        # Total transactions per user (experience)
        user_txn_count = df.groupby('cc_num').cumcount()
        df['user_txn_sequence'] = user_txn_count
        df['is_new_user'] = (user_txn_count < 5).astype(int)

        logger.info("  [+] Behavioral features: 5 features")
        return df

    def _merchant_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Features related to merchant risk profile."""
        if 'merchant' not in df.columns or 'is_fraud' not in df.columns:
            return df

        # Merchant fraud rate (use historical data, avoid leakage with expanding window)
        df = df.sort_values('trans_date_trans_time')
        df['merchant_fraud_rate'] = (
            df.groupby('merchant')['is_fraud']
            .transform(lambda x: x.expanding().mean().shift(1))
            .fillna(0)
        )

        # Category fraud rate (expanding to avoid leakage)
        if 'category' in df.columns:
            df['category_fraud_rate'] = (
                df.groupby('category')['is_fraud']
                .transform(lambda x: x.expanding().mean().shift(1))
                .fillna(0)
            )

            # Category risk level (static encoding from training data knowledge)
            high_risk = ['shopping_net', 'grocery_pos', 'misc_net', 'shopping_pos']
            df['is_high_risk_category'] = df['category'].isin(high_risk).astype(int)

        logger.info("  [+] Merchant features: 3 features")
        return df

    def _interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cross-feature interactions."""
        # Amount × Distance interaction
        if 'amt_log' in df.columns and 'distance_log' in df.columns:
            df['amt_distance_interaction'] = df['amt_log'] * df['distance_log']

        # Night × High Amount
        if 'is_night' in df.columns:
            df['night_high_amt'] = df['is_night'] * (df['amt'] > df['amt'].quantile(0.95)).astype(int)

        # Weekend × Amount deviation
        if 'is_weekend' in df.columns and 'amt_deviation' in df.columns:
            df['weekend_amt_deviation'] = df['is_weekend'] * df['amt_deviation']

        # Velocity × Amount (rapid expensive transactions)
        if 'txn_count_1h' in df.columns:
            df['velocity_amount_risk'] = df['txn_count_1h'] * df['amt_log']

        logger.info("  [+] Interaction features: 4 features")
        return df

    def _encode_categoricals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Encode categorical variables."""
        for col in self.config.category_columns:
            if col in df.columns:
                # Frequency encoding (more robust than one-hot for high cardinality)
                freq = df[col].value_counts(normalize=True)
                df[f'{col}_freq'] = df[col].map(freq).fillna(0)

        # Drop raw string columns that can't go into models
        string_cols = df.select_dtypes(include=['object']).columns.tolist()
        # Keep 'amt_bin' encoded, drop others
        cols_to_encode_then_drop = [c for c in string_cols if c not in ['is_fraud']]
        
        # One-hot encode amt_bin
        if 'amt_bin' in df.columns:
            amt_dummies = pd.get_dummies(df['amt_bin'], prefix='amt_bin', dtype=int)
            df = pd.concat([df, amt_dummies], axis=1)

        # Drop all remaining string columns
        string_cols_final = df.select_dtypes(include=['object']).columns.tolist()
        df = df.drop(columns=string_cols_final)

        logger.info(f"  [+] Categorical encoding complete. Final shape: {df.shape}")
        return df

    def get_feature_names(self) -> List[str]:
        """Return list of engineered feature names."""
        return self.feature_names

    def save_features(self, df: pd.DataFrame, filename: str = "features.parquet") -> None:
        """Save engineered features to parquet."""
        filepath = DATA_FEATURES / filename
        df.to_parquet(filepath, index=False)
        logger.info(f"Saved features to {filepath} ({len(df):,} rows, {len(df.columns)} columns)")

    def load_features(self, filename: str = "features.parquet") -> pd.DataFrame:
        """Load previously engineered features."""
        filepath = DATA_FEATURES / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Features not found at {filepath}")
        return pd.read_parquet(filepath)
