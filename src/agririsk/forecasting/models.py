"""Multi-horizon forecasting models, training pipeline, and calibrated risk prediction."""

from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV

from agririsk.core.logging import logger
from agririsk.dashboard.formatting import assign_risk_band
from agririsk.forecasting.features import FORECAST_FEATURE_COLUMNS, load_forecast_dataset
from agririsk.forecasting.backtesting import (
    RollingOriginSplitter,
    ThresholdOptimizer,
    ForecastEvaluator
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MODEL_ARTIFACTS_DIR = PROJECT_ROOT / "artifacts" / "models"


def get_available_classifiers(random_state: int = 42) -> Dict[str, Any]:
    """Instantiate candidate classifiers supporting class-imbalance weighting."""
    candidates = {
        "logistic_regression": LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=random_state
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            class_weight="balanced",
            random_state=random_state
        ),
        "hist_gradient_boosting": HistGradientBoostingClassifier(
            max_iter=100,
            max_depth=4,
            class_weight="balanced",
            random_state=random_state
        ),
    }

    # Optionally add XGBoost if available
    try:
        from xgboost import XGBClassifier
        candidates["xgboost"] = XGBClassifier(
            n_estimators=100,
            max_depth=4,
            scale_pos_weight=1.2,
            random_state=random_state,
            eval_metric="logloss"
        )
    except ImportError:
        pass

    return candidates


class PlattCalibrator:
    """Platt scaling (logistic sigmoid) calibrator for post-hoc probability calibration."""

    def __init__(self):
        self.lr = LogisticRegression(random_state=42)
        self.is_fitted = False

    def fit(self, probs: np.ndarray, y: np.ndarray) -> "PlattCalibrator":
        X = np.asarray(probs).reshape(-1, 1)
        self.lr.fit(X, y)
        self.is_fitted = True
        return self

    def predict_proba(self, probs: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            return probs
        X = np.asarray(probs).reshape(-1, 1)
        return self.lr.predict_proba(X)[:, 1]


class HorizonForecaster:
    """Manages training, calibration, threshold selection, and prediction for a single forecast horizon."""

    def __init__(
        self,
        horizon: int,
        model_name: str = "random_forest",
        features: Optional[List[str]] = None,
        random_state: int = 42
    ):
        self.horizon = horizon
        self.model_name = model_name
        self.features = features or FORECAST_FEATURE_COLUMNS
        self.random_state = random_state

        self.scaler = StandardScaler()
        self.base_model: Optional[Any] = None
        self.calibrated_model: Optional[Any] = None
        self.optimal_threshold: float = 0.50
        self.threshold_metrics: Dict[str, Any] = {}
        self.is_fitted: bool = False

    def _prepare_X(self, df: pd.DataFrame, is_train: bool = False) -> np.ndarray:
        """Extract and scale predictor matrix, handling NaNs via forward/backward filling."""
        X_df = df[self.features].copy()
        # Impute residual warm-up NaNs with training median / zero
        X_df = X_df.fillna(0.0)

        if self.model_name == "logistic_regression":
            if is_train:
                return self.scaler.fit_transform(X_df)
            return self.scaler.transform(X_df)
        return X_df.values

    def fit(
        self,
        train_df: pd.DataFrame,
        val_df: Optional[pd.DataFrame] = None
    ) -> "HorizonForecaster":
        """Fit candidate model and optimize decision threshold using validation data.

        Args:
            train_df: Training partition.
            val_df: Validation partition (for calibration and threshold selection).
        """
        X_train = self._prepare_X(train_df, is_train=True)
        y_train = train_df["target_phase3plus"].values.astype(int)

        classifiers = get_available_classifiers(random_state=self.random_state)
        if self.model_name not in classifiers:
            logger.warning("Model %s not found, falling back to random_forest", self.model_name)
            self.model_name = "random_forest"

        self.base_model = classifiers[self.model_name]
        logger.info("Fitting Horizon %d with %s (train samples: %d)", self.horizon, self.model_name, len(X_train))
        self.base_model.fit(X_train, y_train)

        # Optimize threshold & calibrate on validation partition if provided
        if val_df is not None and not val_df.empty:
            X_val = self._prepare_X(val_df, is_train=False)
            y_val = val_df["target_phase3plus"].values.astype(int)

            val_probs = self.base_model.predict_proba(X_val)[:, 1]
            opt_th, th_metrics = ThresholdOptimizer.select_optimal_threshold(
                y_val, val_probs, min_recall=0.80
            )
            self.optimal_threshold = opt_th
            self.threshold_metrics = th_metrics
            logger.info("Horizon %d tuned threshold: %.2f (Validation Recall: %.2f)", self.horizon, opt_th, th_metrics.get("recall", 0))

            # Calibrate using sigmoid Platt scaling on validation fold
            try:
                self.calibrator = PlattCalibrator()
                self.calibrator.fit(val_probs, y_val)
            except Exception as e:
                logger.warning("Calibration failed (%s). Using base model.", e)
                self.calibrator = None

        self.is_fitted = True
        return self

    def predict_proba(self, df: pd.DataFrame, use_calibrated: bool = True) -> np.ndarray:
        """Predict acute food insecurity risk probability (class 1)."""
        if not self.is_fitted:
            raise RuntimeError("HorizonForecaster must be fitted before predict_proba.")
        X = self._prepare_X(df, is_train=False)
        base_probs = self.base_model.predict_proba(X)[:, 1]
        if use_calibrated and hasattr(self, "calibrator") and self.calibrator is not None:
            return self.calibrator.predict_proba(base_probs)
        return base_probs

    def predict(self, df: pd.DataFrame, threshold: Optional[float] = None) -> np.ndarray:
        """Predict binary classification using optimized or custom threshold."""
        th = threshold if threshold is not None else self.optimal_threshold
        probs = self.predict_proba(df)
        return (probs >= th).astype(int)

    def extract_top_signals(self, row: pd.Series, top_k: int = 3) -> List[str]:
        """Extract top risk-elevating indicators for a single observation."""
        signals = []

        rain_3m = row.get("rainfall_rolling_3m")
        rain_lag1 = row.get("rainfall_anomaly_lag1")
        ndvi_lag1 = row.get("ndvi_anomaly_lag1")
        ndvi_tr3m = row.get("ndvi_trend_3m")
        price_z = row.get("maize_price_zscore")
        price_chg3m = row.get("maize_price_change_3m")
        dry_streak = row.get("consecutive_dry_months", 0)
        prev_ipc = row.get("previous_ipc_phase", 2)

        if rain_lag1 is not None and rain_lag1 < -20:
            signals.append(f"Precipitation deficit ({rain_lag1:+.1f}% anomaly)")
        if dry_streak is not None and dry_streak >= 2:
            signals.append(f"Extended dry spell ({int(dry_streak)} consecutive months)")
        if ndvi_lag1 is not None and ndvi_lag1 < -10:
            signals.append(f"Vegetation stress ({ndvi_lag1:+.1f}% NDVI anomaly)")
        if ndvi_tr3m is not None and ndvi_tr3m < -5:
            signals.append("Deteriorating 3-month vegetation trend")
        if price_z is not None and price_z > 1.0:
            signals.append(f"Elevated staple food price ({price_z:+.2f} \u03c3)")
        if price_chg3m is not None and price_chg3m > 15:
            signals.append(f"Sharp quarterly price inflation ({price_chg3m:+.1f}%)")
        if prev_ipc is not None and prev_ipc >= 3:
            signals.append(f"Prior IPC Phase {int(prev_ipc)} vulnerability anchor")

        if not signals:
            signals.append("Climate and market indicators within normal seasonal bounds")

        return signals[:top_k]

    def generate_forecast_output(self, row: pd.Series) -> Dict[str, Any]:
        """Produce standardized JSON forecast output dictionary conforming to schema."""
        prob = float(self.predict_proba(pd.DataFrame([row]))[0])
        band = assign_risk_band(prob)

        return {
            "county": str(row["county_name"]),
            "observation_date": str(row["observation_period"]),
            "forecast_horizon_months": int(self.horizon),
            "target_date": str(row["target_period"]),
            "risk_probability": round(prob, 4),
            "risk_band": band,
            "decision_threshold": self.optimal_threshold,
            "predicted_crisis_alert": bool(prob >= self.optimal_threshold),
            "model_version": f"v1.0-{self.model_name}-h{self.horizon}",
            "top_risk_signals": self.extract_top_signals(row)
        }

    def save(self, filepath: Optional[Path] = None) -> Path:
        """Serialize forecaster artifact to disk."""
        target = filepath or (MODEL_ARTIFACTS_DIR / f"forecast_model_h{self.horizon}.joblib")
        target.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, target)
        logger.info("Saved forecast model for horizon %d to %s", self.horizon, target)
        return target

    @classmethod
    def load(cls, filepath: Path) -> "HorizonForecaster":
        """Load serialized forecaster artifact from disk."""
        return joblib.load(filepath)
