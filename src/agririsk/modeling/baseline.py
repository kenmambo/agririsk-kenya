"""Baseline modeling implementations and time-aware dataset splitting."""

from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from agririsk.core.logging import logger
from agririsk.features.engineering import FeatureEngineer


def time_aware_train_val_test_split(
    df: pd.DataFrame,
    train_years: Tuple[int, ...] = (2019, 2020, 2021, 2022),
    val_years: Tuple[int, ...] = (2023,),
    test_years: Tuple[int, ...] = (2024,),
    feature_cols: Optional[List[str]] = None,
    target_col: str = "target_phase3plus",
) -> Dict[str, Tuple[pd.DataFrame, pd.Series]]:
    """Split time-series panel dataset chronologically to avoid look-ahead data leakage.

    Args:
        df: Input feature DataFrame.
        train_years: Sequence of years to include in training set.
        val_years: Sequence of years to include in validation set.
        test_years: Sequence of years to include in test set.
        feature_cols: List of predictor column names. Defaults to FeatureEngineer.FEATURE_COLUMNS.
        target_col: Target column name.

    Returns:
        Dictionary with keys 'train', 'val', 'test', each mapping to a tuple (X, y).
    """
    features = feature_cols or FeatureEngineer.FEATURE_COLUMNS

    # Drop rows where lag features are missing (initial warm-up months per county)
    clean_df = df.dropna(subset=features + [target_col]).copy()

    train_mask = clean_df["year"].isin(train_years)
    val_mask = clean_df["year"].isin(val_years)
    test_mask = clean_df["year"].isin(test_years)

    splits = {
        "train": (clean_df.loc[train_mask, features], clean_df.loc[train_mask, target_col]),
        "val": (clean_df.loc[val_mask, features], clean_df.loc[val_mask, target_col]),
        "test": (clean_df.loc[test_mask, features], clean_df.loc[test_mask, target_col]),
    }

    logger.info(
        "Time-aware split complete -> Train: %d rows (years %s), Val: %d rows (years %s), Test: %d rows (years %s)",
        len(splits["train"][0]),
        train_years,
        len(splits["val"][0]),
        val_years,
        len(splits["test"][0]),
        test_years,
    )
    return splits


class BaselineModels:
    """Trainer and manager for baseline classification models."""

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.log_reg = LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=self.random_state
        )
        self.rf = RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            class_weight="balanced",
            random_state=self.random_state
        )
        self.feature_names: List[str] = []
        self.is_fitted: bool = False

    def fit(self, X_train: pd.DataFrame, y_train: pd.Series) -> "BaselineModels":
        """Fit scaler and baseline classifiers."""
        self.feature_names = list(X_train.columns)

        # Scale features for Logistic Regression
        X_train_scaled = self.scaler.fit_transform(X_train)

        logger.info("Fitting Logistic Regression baseline...")
        self.log_reg.fit(X_train_scaled, y_train)

        logger.info("Fitting Random Forest baseline...")
        self.rf.fit(X_train, y_train)

        self.is_fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> Dict[str, np.ndarray]:
        """Generate binary class predictions from both baselines."""
        if not self.is_fitted:
            raise RuntimeError("Models must be fitted before predict.")
        X_scaled = self.scaler.transform(X[self.feature_names])
        return {
            "logistic_regression": self.log_reg.predict(X_scaled),
            "random_forest": self.rf.predict(X[self.feature_names]),
        }

    def predict_proba(self, X: pd.DataFrame) -> Dict[str, np.ndarray]:
        """Generate class 1 (Phase 3+ Crisis) probability scores."""
        if not self.is_fitted:
            raise RuntimeError("Models must be fitted before predict_proba.")
        X_scaled = self.scaler.transform(X[self.feature_names])
        return {
            "logistic_regression": self.log_reg.predict_proba(X_scaled)[:, 1],
            "random_forest": self.rf.predict_proba(X[self.feature_names])[:, 1],
        }
