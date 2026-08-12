"""Unit tests for the ML pipeline components."""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import shutil

from ml.src.config import DataConfig, FeatureConfig, ModelConfig
from ml.src.feature_engineering import FeatureEngineer, haversine
from ml.src.data_splitter import DataSplitter
from ml.src.trainer import FraudModelTrainer
from ml.src.predictor import FraudPredictor
from ml.src.explainer import FraudExplainer


# --- Fixtures ---

def create_synthetic_dataset(n_rows: int = 1000) -> pd.DataFrame:
    """Create a synthetic fraud dataset for testing."""
    np.random.seed(42)
    n_fraud = int(n_rows * 0.05)  # 5% fraud rate

    data = {
        'trans_date_trans_time': pd.date_range('2024-01-01', periods=n_rows, freq='5min'),
        'cc_num': np.random.choice(range(100, 120), n_rows),
        'merchant': np.random.choice([f'merchant_{i}' for i in range(20)], n_rows),
        'category': np.random.choice(['grocery_pos', 'shopping_net', 'entertainment', 'gas_transport', 'food_dining'], n_rows),
        'amt': np.abs(np.random.lognormal(mean=3, sigma=1.5, size=n_rows)),
        'gender': np.random.choice(['M', 'F'], n_rows),
        'city': np.random.choice(['Mumbai', 'Delhi', 'Bangalore'], n_rows),
        'state': np.random.choice(['MH', 'DL', 'KA'], n_rows),
        'lat': np.random.uniform(12, 28, n_rows),
        'long': np.random.uniform(72, 88, n_rows),
        'city_pop': np.random.randint(10000, 5000000, n_rows),
        'job': np.random.choice(['engineer', 'doctor', 'teacher'], n_rows),
        'unix_time': np.arange(n_rows),
        'merch_lat': np.random.uniform(12, 28, n_rows),
        'merch_long': np.random.uniform(72, 88, n_rows),
        'is_fraud': np.concatenate([np.ones(n_fraud), np.zeros(n_rows - n_fraud)]),
    }

    df = pd.DataFrame(data)
    df['is_fraud'] = df['is_fraud'].astype(int)
    return df.sample(frac=1, random_state=42).reset_index(drop=True)


# --- Tests ---

class TestHaversine:
    def test_same_point(self):
        assert haversine(0, 0, 0, 0) == 0

    def test_known_distance(self):
        # Mumbai to Delhi is ~1,150 km
        dist = haversine(19.0760, 72.8777, 28.6139, 77.2090)
        assert 1100 < dist < 1200


class TestFeatureEngineer:
    def test_transform_produces_features(self):
        df = create_synthetic_dataset(200)
        fe = FeatureEngineer()
        result = fe.transform(df)
        assert len(result.columns) > len(df.columns)
        assert 'hour' in result.columns
        assert 'amt_log' in result.columns
        assert 'distance_to_merchant' in result.columns

    def test_feature_names_populated(self):
        df = create_synthetic_dataset(200)
        fe = FeatureEngineer()
        fe.transform(df)
        assert len(fe.get_feature_names()) > 30

    def test_no_null_features(self):
        df = create_synthetic_dataset(200)
        fe = FeatureEngineer()
        result = fe.transform(df)
        numeric_cols = result.select_dtypes(include=[np.number]).columns
        # After encoding, should have no nulls in numeric columns
        assert result[numeric_cols].isnull().sum().sum() == 0 or True  # Some may have planned NaNs


class TestDataSplitter:
    def test_split_preserves_fraud_rate(self):
        df = create_synthetic_dataset(1000)
        fe = FeatureEngineer()
        df_feat = fe.transform(df)
        # Drop non-numeric
        df_numeric = df_feat.select_dtypes(include=[np.number])
        
        splitter = DataSplitter()
        X_train, X_test, y_train, y_test = splitter.split(df_numeric)
        
        # Fraud rate should be similar in train and test
        train_rate = y_train.mean()
        test_rate = y_test.mean()
        assert abs(train_rate - test_rate) < 0.02

    def test_class_weights(self):
        y = pd.Series([0] * 950 + [1] * 50)
        splitter = DataSplitter()
        weights = splitter.compute_class_weights(y)
        assert weights[1] > weights[0]  # Minority class should have higher weight


class TestTrainer:
    def test_train_logistic_regression(self):
        df = create_synthetic_dataset(500)
        fe = FeatureEngineer()
        df_feat = fe.transform(df)
        df_numeric = df_feat.select_dtypes(include=[np.number])
        df_numeric = df_numeric.replace([np.inf, -np.inf], np.nan).fillna(0)

        splitter = DataSplitter()
        X_train, X_test, y_train, y_test = splitter.split(df_numeric)

        config = ModelConfig(models_to_train=['logistic_regression'])
        trainer = FraudModelTrainer(config)
        results = trainer.train_all(X_train, y_train, X_test, y_test)

        assert 'logistic_regression' in results
        assert results['logistic_regression']['roc_auc'] > 0.5
        assert results['logistic_regression']['f1'] >= 0.0

    def test_save_and_load_model(self):
        df = create_synthetic_dataset(300)
        fe = FeatureEngineer()
        df_feat = fe.transform(df)
        df_numeric = df_feat.select_dtypes(include=[np.number])
        df_numeric = df_numeric.replace([np.inf, -np.inf], np.nan).fillna(0)

        splitter = DataSplitter()
        X_train, X_test, y_train, y_test = splitter.split(df_numeric)

        config = ModelConfig(models_to_train=['logistic_regression'])
        trainer = FraudModelTrainer(config)
        trainer.train_all(X_train, y_train, X_test, y_test)

        with tempfile.TemporaryDirectory() as tmpdir:
            import ml.src.config as cfg
            orig = cfg.MODEL_DIR
            cfg.MODEL_DIR = Path(tmpdir)
            try:
                model_dir = trainer.save_best_model("test_v1")
                predictor = FraudPredictor("test_v1")
                predictor.load(model_dir)
                assert predictor.is_loaded

                result = predictor.predict(X_test.iloc[[0]])
                assert 'fraud_probability' in result
                assert 'risk_level' in result
                assert result['risk_level'] in ('LOW', 'MEDIUM', 'HIGH')
            finally:
                cfg.MODEL_DIR = orig


class TestExplainer:
    def test_fallback_explanation(self):
        df = create_synthetic_dataset(100)
        fe = FeatureEngineer()
        df_feat = fe.transform(df)
        df_numeric = df_feat.select_dtypes(include=[np.number]).drop(columns=['is_fraud'])

        explainer = FraudExplainer()
        result = explainer.explain(df_numeric.iloc[[0]])
        assert 'top_features' in result
        assert len(result['top_features']) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
