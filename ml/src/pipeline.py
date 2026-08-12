"""End-to-end ML pipeline orchestrator.

Orchestrates the entire workflow:
1. Load data
2. Engineer features
3. Split data
4. Train models
5. Evaluate and compare
6. Save best model
7. Initialize explainer

Usage:
    from ml.src.pipeline import FraudDetectionPipeline
    pipeline = FraudDetectionPipeline()
    pipeline.run()
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from pathlib import Path
import logging
import json
import time

from ml.src.config import DataConfig, FeatureConfig, ModelConfig, DATA_RAW, MODEL_DIR
from ml.src.data_loader import DataLoader
from ml.src.feature_engineering import FeatureEngineer
from ml.src.data_splitter import DataSplitter
from ml.src.trainer import FraudModelTrainer
from ml.src.predictor import FraudPredictor
from ml.src.explainer import FraudExplainer

logger = logging.getLogger(__name__)


class FraudDetectionPipeline:
    """Orchestrates the entire fraud detection ML pipeline."""

    def __init__(
        self,
        data_config: Optional[DataConfig] = None,
        feature_config: Optional[FeatureConfig] = None,
        model_config: Optional[ModelConfig] = None,
    ):
        self.data_config = data_config or DataConfig()
        self.feature_config = feature_config or FeatureConfig()
        self.model_config = model_config or ModelConfig()

        self.loader = DataLoader(self.data_config)
        self.feature_engineer = FeatureEngineer(self.feature_config)
        self.splitter = DataSplitter(self.data_config)
        self.trainer = FraudModelTrainer(self.model_config)
        self.predictor = FraudPredictor()
        self.explainer = FraudExplainer()

        self.run_metadata: Dict = {}

    def run(
        self,
        model_version: str = "v1",
        use_smote: bool = False,
        smote_ratio: float = 0.3,
        save_intermediates: bool = True,
    ) -> Dict:
        """Execute the complete pipeline."""
        pipeline_start = time.time()
        logger.info("\n" + "="*80)
        logger.info("  FraudShield AI — ML Pipeline")
        logger.info("="*80 + "\n")

        # Step 1: Load and clean data
        logger.info("[Step 1/6] Loading and cleaning data...")
        df = self.loader.load_and_clean()
        data_summary = self.loader.get_data_summary(df)

        if save_intermediates:
            self.loader.save_processed(df)

        # Step 2: Feature engineering
        logger.info("\n[Step 2/6] Engineering features...")
        df_features = self.feature_engineer.transform(df)

        if save_intermediates:
            self.feature_engineer.save_features(df_features)

        # Step 3: Remove non-numeric and non-feature columns
        logger.info("\n[Step 3/6] Preparing train/test split...")
        # Drop any remaining non-numeric columns except target
        target = self.data_config.target_column
        drop_cols = [c for c in df_features.columns
                     if df_features[c].dtype == 'object' or c == 'trans_date_trans_time']
        drop_cols = [c for c in drop_cols if c != target]
        df_final = df_features.drop(columns=drop_cols, errors='ignore')

        # Handle inf/nan
        df_final = df_final.replace([np.inf, -np.inf], np.nan)
        df_final = df_final.fillna(0)

        X_train, X_test, y_train, y_test = self.splitter.split(df_final, target)

        # Step 4: Handle class imbalance (optional)
        scale_pos_weight = self.splitter.get_scale_pos_weight(y_train)

        if use_smote:
            logger.info("\n[Step 3b] Applying SMOTE...")
            X_train, y_train = self.splitter.apply_smote(X_train, y_train, smote_ratio)

        # Step 5: Train models
        logger.info("\n[Step 4/6] Training models...")
        results = self.trainer.train_all(X_train, y_train, X_test, y_test, scale_pos_weight)

        # Step 6: Save best model
        logger.info("\n[Step 5/6] Saving models...")
        model_dir = self.trainer.save_best_model(model_version)
        self.trainer.save_all_models(model_version)

        # Step 7: Initialize predictor and explainer
        logger.info("\n[Step 6/6] Initializing predictor and explainer...")
        self.predictor = FraudPredictor(model_version)
        self.predictor.load(model_dir)

        if self.trainer.best_model_name and self.trainer.best_model_name in self.trainer.models:
            best_model = self.trainer.models[self.trainer.best_model_name]
            # For pipeline-wrapped models, extract the actual model
            if hasattr(best_model, 'named_steps'):
                actual_model = best_model.named_steps.get('clf', best_model)
            else:
                actual_model = best_model
            self.explainer.initialize(actual_model, X_train.sample(min(100, len(X_train))))

        # Compile metadata
        pipeline_time = time.time() - pipeline_start
        comparison_table = self.trainer.get_comparison_table()

        self.run_metadata = {
            "pipeline_version": model_version,
            "total_time_seconds": round(pipeline_time, 1),
            "data_summary": data_summary,
            "feature_count": len(self.feature_engineer.get_feature_names()),
            "model_results": results,
            "best_model": self.trainer.best_model_name,
            "best_threshold": self.trainer.best_threshold,
        }

        # Save pipeline metadata
        meta_path = model_dir / "pipeline_metadata.json"
        with open(meta_path, 'w') as f:
            json.dump(self.run_metadata, f, indent=2, default=str)

        # Print summary
        logger.info("\n" + "="*80)
        logger.info("  Pipeline Complete!")
        logger.info(f"  Time:     {pipeline_time:.0f}s")
        logger.info(f"  Best:     {self.trainer.best_model_name}")
        logger.info(f"  PR-AUC:   {results[self.trainer.best_model_name]['pr_auc']:.4f}")
        logger.info(f"  F1:       {results[self.trainer.best_model_name]['f1']:.4f}")
        logger.info(f"  Saved to: {model_dir}")
        logger.info("="*80 + "\n")

        if not comparison_table.empty:
            logger.info("\nModel Comparison:")
            logger.info(comparison_table[['pr_auc', 'roc_auc', 'f1', 'precision', 'recall', 'train_time_seconds']].to_string())

        return self.run_metadata

    def predict_single(self, features: pd.DataFrame) -> Dict:
        """Make a prediction on a single transaction."""
        prediction = self.predictor.predict(features)
        explanation = self.explainer.explain(features)
        return {
            **prediction,
            "explanation": explanation,
        }
