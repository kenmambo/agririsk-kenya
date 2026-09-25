"""Simple benchmark models for food security risk forecasting.

Provides non-learning and simple statistical baselines:
1. PersistenceBaseline: Assumes future risk equals latest observed state.
2. HistoricalFrequencyBaseline: Predicts county-specific empirical base rate.
3. SeasonalBaseline: Predicts empirical risk rate conditioned on month/season.
"""

from typing import Dict, Any, Optional, Union
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin


class PersistenceBaseline(BaseEstimator, ClassifierMixin):
    """Persistence baseline: future risk status equals current/latest observed risk."""

    def __init__(self, current_risk_col: str = "previous_ipc_phase", threshold_phase: float = 3.0):
        self.current_risk_col = current_risk_col
        self.threshold_phase = threshold_phase
        self.classes_ = np.array([0, 1])

    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None) -> "PersistenceBaseline":
        """No statistical training required for pure persistence."""
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Return binary probabilities: 1.0 if previous phase >= 3, else 0.0."""
        if self.current_risk_col in X.columns:
            prev_phase = X[self.current_risk_col].values
            p1 = np.where(prev_phase >= self.threshold_phase, 1.0, 0.0)
        else:
            # Fallback if specific column absent
            p1 = np.full(len(X), 0.5)

        p0 = 1.0 - p1
        return np.column_stack([p0, p1])

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Return binary classification {0, 1}."""
        probs = self.predict_proba(X)[:, 1]
        return (probs >= 0.5).astype(int)


class HistoricalFrequencyBaseline(BaseEstimator, ClassifierMixin):
    """Predicts historical empirical frequency of Phase 3+ crisis by county."""

    def __init__(self, county_col: str = "county_name", target_col: str = "target_phase3plus"):
        self.county_col = county_col
        self.target_col = target_col
        self.county_priors: Dict[str, float] = {}
        self.global_prior: float = 0.5
        self.classes_ = np.array([0, 1])

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "HistoricalFrequencyBaseline":
        """Calculate historical empirical crisis frequencies per county from training fold."""
        df = X.copy()
        df["_target"] = y.values

        self.global_prior = float(y.mean()) if len(y) > 0 else 0.5

        if self.county_col in df.columns:
            grouped = df.groupby(self.county_col)["_target"].mean()
            self.county_priors = grouped.to_dict()
        else:
            self.county_priors = {}

        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Assign county-specific historical risk base rates."""
        if self.county_col in X.columns:
            p1 = X[self.county_col].map(self.county_priors).fillna(self.global_prior).values
        else:
            p1 = np.full(len(X), self.global_prior)

        p1 = np.clip(p1, 0.001, 0.999)
        p0 = 1.0 - p1
        return np.column_stack([p0, p1])

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict binary class using 0.5 threshold."""
        probs = self.predict_proba(X)[:, 1]
        return (probs >= 0.5).astype(int)


class SeasonalBaseline(BaseEstimator, ClassifierMixin):
    """Predicts empirical crisis risk conditioned on month/season and county."""

    def __init__(
        self,
        month_col: str = "month",
        county_col: str = "county_name"
    ):
        self.month_col = month_col
        self.county_col = county_col
        self.seasonal_county_priors: Dict[tuple, float] = {}
        self.month_priors: Dict[int, float] = {}
        self.global_prior: float = 0.5
        self.classes_ = np.array([0, 1])

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "SeasonalBaseline":
        """Compute crisis rates by (county, month) and by month."""
        df = X.copy()
        df["_target"] = y.values

        self.global_prior = float(y.mean()) if len(y) > 0 else 0.5

        if self.month_col in df.columns:
            self.month_priors = df.groupby(self.month_col)["_target"].mean().to_dict()

        if self.county_col in df.columns and self.month_col in df.columns:
            grouped = df.groupby([self.county_col, self.month_col])["_target"].mean()
            self.seasonal_county_priors = grouped.to_dict()

        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Assign seasonal empirical probabilities."""
        probs = []
        for _, row in X.iterrows():
            c = row.get(self.county_col)
            m = row.get(self.month_col)

            # 1. County x Month lookup
            if (c, m) in self.seasonal_county_priors:
                p = self.seasonal_county_priors[(c, m)]
            # 2. Month-only lookup
            elif m in self.month_priors:
                p = self.month_priors[m]
            # 3. Global prior fallback
            else:
                p = self.global_prior
            probs.append(p)

        p1 = np.clip(np.array(probs, dtype=float), 0.001, 0.999)
        p0 = 1.0 - p1
        return np.column_stack([p0, p1])

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict binary classification."""
        probs = self.predict_proba(X)[:, 1]
        return (probs >= 0.5).astype(int)
