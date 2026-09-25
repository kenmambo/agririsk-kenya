"""Data loading, caching, querying, and risk scoring for AgriRisk Kenya dashboard."""

from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import joblib
import numpy as np
import pandas as pd
from agririsk.core.logging import logger
from agririsk.features.engineering import FeatureEngineer
from agririsk.modeling.baseline import BaselineModels, time_aware_train_val_test_split
from agririsk.dashboard.formatting import assign_risk_band

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "model_dataset.csv"
MODEL_PATH = PROJECT_ROOT / "artifacts" / "models" / "baseline_models.joblib"
METRICS_PATH = PROJECT_ROOT / "reports" / "model_results" / "baseline_metrics.json"


def load_raw_dataset() -> pd.DataFrame:
    """Load the processed county-month modeling dataset.

    Returns:
        pd.DataFrame with raw columns.
    """
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Model dataset not found at {DATA_PATH}. Run pipeline first.")
    df = pd.read_csv(DATA_PATH)
    return df


def load_model_artifact() -> BaselineModels:
    """Load pre-trained BaselineModels artifact or fit if not present.

    Returns:
        Fitted BaselineModels instance.
    """
    if MODEL_PATH.exists():
        try:
            models = joblib.load(MODEL_PATH)
            if hasattr(models, "is_fitted") and models.is_fitted:
                return models
        except Exception as e:
            logger.warning("Could not load model artifact from %s: %s. Re-fitting...", MODEL_PATH, e)

    logger.info("Fitting baseline models for dashboard inference...")
    df = load_raw_dataset()
    splits = time_aware_train_val_test_split(df)
    models = BaselineModels(random_state=42)
    models.fit(splits["train"][0], splits["train"][1])

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        joblib.dump(models, MODEL_PATH)
    except Exception as e:
        logger.warning("Failed to save re-fitted models: %s", e)

    return models


def load_scored_dataset() -> pd.DataFrame:
    """Load dataset, add derived temporal columns, and score with baseline model risk probabilities.

    Returns:
        pd.DataFrame enriched with:
        - 'period' (str: YYYY-MM)
        - 'period_dt' (datetime)
        - 'model_risk_prob' (float: 0.0 - 1.0)
        - 'risk_band' (str: Low, Moderate, Elevated, High)
    """
    df = load_raw_dataset().copy()

    # Create formatted temporal columns
    df["period"] = df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2)
    df["period_dt"] = pd.to_datetime(df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2) + "-01")

    # Load model and score
    models = load_model_artifact()
    features = models.feature_names or FeatureEngineer.FEATURE_COLUMNS

    # For scoring, handle warm-up NaNs cleanly via forward/backward fill per county
    X_imputed = df.groupby("county_name", group_keys=False)[features].apply(
        lambda g: g.bfill().ffill()
    )
    # Any residual NaNs (if entire county column is empty) fill with 0.0
    X_imputed = X_imputed.fillna(0.0)

    try:
        probas = models.predict_proba(X_imputed)
        # Use Random Forest as primary baseline probability
        df["model_risk_prob"] = probas["random_forest"]
        df["model_risk_prob_lr"] = probas["logistic_regression"]
    except Exception as e:
        logger.error("Scoring failed: %s. Using default 0.0 probabilities.", e)
        df["model_risk_prob"] = 0.0
        df["model_risk_prob_lr"] = 0.0

    df["risk_band"] = df["model_risk_prob"].apply(assign_risk_band)

    # Sort deterministically
    df = df.sort_values(by=["county_name", "period_dt"]).reset_index(drop=True)
    return df


def get_latest_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    """Extract the most recent observation for every county in the dataset.

    Args:
        df: Scored dataset.

    Returns:
        pd.DataFrame containing 1 row per county at its latest observed period.
    """
    latest_period = df["period"].max()
    latest_df = df[df["period"] == latest_period].copy()
    if latest_df.empty:
        # Fallback to per-county max period if dates differ
        latest_df = df.sort_values("period_dt").groupby("county_name").last().reset_index()
    return latest_df.sort_values("county_name").reset_index(drop=True)


def get_available_counties(df: pd.DataFrame) -> List[str]:
    """Return sorted list of distinct county names in the dataset."""
    return sorted(df["county_name"].unique().tolist())


def get_available_periods(df: pd.DataFrame) -> List[str]:
    """Return chronologically sorted list of distinct periods (YYYY-MM)."""
    return sorted(df["period"].unique().tolist())


def filter_dataset(
    df: pd.DataFrame,
    county: Optional[str] = None,
    start_period: Optional[str] = None,
    end_period: Optional[str] = None,
) -> pd.DataFrame:
    """Filter dataset by county and date period range.

    Args:
        df: Scored dataset.
        county: Optional canonical county name.
        start_period: Optional starting period string ('YYYY-MM').
        end_period: Optional ending period string ('YYYY-MM').

    Returns:
        Filtered DataFrame.
    """
    filtered = df.copy()
    if county and county != "All Counties":
        filtered = filtered[filtered["county_name"] == county]

    if start_period:
        filtered = filtered[filtered["period"] >= start_period]
    if end_period:
        filtered = filtered[filtered["period"] <= end_period]

    return filtered.reset_index(drop=True)


def get_county_timeseries(df: pd.DataFrame, county: str) -> pd.DataFrame:
    """Return chronological timeseries observations for a single county."""
    subset = df[df["county_name"] == county].sort_values("period_dt").reset_index(drop=True)
    return subset


def load_model_evaluation_metrics() -> Dict[str, Any]:
    """Load baseline model evaluation metrics JSON report.

    Returns:
        Dictionary of baseline metrics or fallback placeholder.
    """
    import json
    if METRICS_PATH.exists():
        try:
            with open(METRICS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Failed to parse metrics file %s: %s", METRICS_PATH, e)
    return {}
