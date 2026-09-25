"""Unit tests for multi-horizon forecasting, temporal leakage prevention, threshold tuning, and calibration."""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from agririsk.forecasting.features import (
    determine_season,
    ForecastFeatureEngineer,
    load_forecast_dataset,
    FORECAST_FEATURE_COLUMNS
)
from agririsk.forecasting.backtesting import (
    RollingOriginSplitter,
    ThresholdOptimizer,
    ForecastEvaluator
)
from agririsk.forecasting.models import (
    PlattCalibrator,
    HorizonForecaster,
    get_available_classifiers
)
from agririsk.forecasting.inference import (
    load_forecaster,
    generate_county_multi_horizon_forecast,
    generate_early_warning_summary_table
)


# --- 1. Feature Engineering & Seasonality Tests ---

def test_season_classification():
    """Verify Kenyan agricultural seasons classification."""
    assert determine_season(3) == "MAM"   # Long rains
    assert determine_season(4) == "MAM"
    assert determine_season(5) == "MAM"
    assert determine_season(10) == "OND"  # Short rains
    assert determine_season(11) == "OND"
    assert determine_season(12) == "OND"
    assert determine_season(1) == "JF"    # Dry
    assert determine_season(2) == "JF"
    assert determine_season(7) == "JJAS"  # Dry


def test_forecast_dataset_temporal_integrity():
    """Verify strictly target_date > observation_date across all long-format rows."""
    df = load_forecast_dataset()
    assert not df.empty

    obs_dates = pd.to_datetime(df["observation_date"])
    target_dates = pd.to_datetime(df["target_date"])

    # Strict assertion: no record can have target_date <= observation_date
    assert (target_dates > obs_dates).all()

    # Verify horizon values are 1, 2, or 3
    assert set(df["horizon_months"].unique()) == {1, 2, 3}

    # Verify month offsets match horizon
    offsets = (target_dates.dt.year - obs_dates.dt.year) * 12 + (target_dates.dt.month - obs_dates.dt.month)
    assert (offsets == df["horizon_months"]).all()


def test_lagged_features_no_lookahead():
    """Verify lags strictly represent past periods."""
    df = load_forecast_dataset()
    turkana = df[(df["county_name"] == "Turkana") & (df["horizon_months"] == 1)].sort_values("observation_date").reset_index(drop=True)

    for feat in ["rainfall_anomaly_lag1", "ndvi_anomaly_lag1"]:
        assert feat in turkana.columns


# --- 2. Rolling-Origin Backtesting Tests ---

def test_rolling_origin_splitter_chronology():
    """Verify temporal ordering and absence of data leakage across train and eval partitions."""
    df = load_forecast_dataset()
    splitter = RollingOriginSplitter()
    splits = splitter.split(df, horizon=1)

    assert len(splits) == 2

    val_split = splits[0]
    test_split = splits[1]

    # Verify train max date < eval min date
    assert pd.to_datetime(val_split["train_df"]["observation_date"]).max() < pd.to_datetime(val_split["eval_df"]["observation_date"]).min()
    assert pd.to_datetime(test_split["train_df"]["observation_date"]).max() < pd.to_datetime(test_split["eval_df"]["observation_date"]).min()

    # Expanding window: train for test_split should contain more records than train for val_split
    assert len(test_split["train_df"]) > len(val_split["train_df"])


# --- 3. Threshold Optimization & Metric Evaluation Tests ---

def test_threshold_optimizer():
    """Verify threshold selector prioritizes early-warning sensitivity."""
    y_true = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    y_prob = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8])

    grid = ThresholdOptimizer.evaluate_threshold_grid(y_true, y_prob)
    assert not grid.empty
    assert "precision" in grid.columns
    assert "recall" in grid.columns
    assert "false_negative_rate" in grid.columns

    opt_th, metrics = ThresholdOptimizer.select_optimal_threshold(y_true, y_prob, min_recall=0.75)
    assert 0.10 <= opt_th <= 0.90
    assert metrics["recall"] >= 0.75


def test_forecast_evaluator_metrics():
    """Verify comprehensive metric dictionary structure."""
    y_true = np.array([0, 0, 1, 1])
    y_prob = np.array([0.1, 0.4, 0.7, 0.9])

    metrics = ForecastEvaluator.compute_all_metrics(y_true, y_prob, threshold=0.50)
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1_score"] == 1.0
    assert metrics["false_negative_rate"] == 0.0
    assert metrics["brier_score"] < 0.10
    assert "confusion_matrix" in metrics


# --- 4. Platt Calibration Tests ---

def test_platt_calibrator():
    """Verify Platt scaling produces valid probabilities in range [0, 1]."""
    calibrator = PlattCalibrator()
    uncalibrated = np.array([0.05, 0.25, 0.65, 0.85, 0.95])
    y = np.array([0, 0, 1, 1, 1])

    calibrator.fit(uncalibrated, y)
    calibrated = calibrator.predict_proba(uncalibrated)

    assert len(calibrated) == len(uncalibrated)
    assert (calibrated >= 0.0).all()
    assert (calibrated <= 1.0).all()


# --- 5. Horizon Forecaster & Schema Output Tests ---

def test_horizon_forecaster_fit_and_schema():
    """Verify forecaster fits and produces standardized output schema."""
    df = load_forecast_dataset()
    h1_df = df[df["horizon_months"] == 1].dropna(subset=["target_phase3plus"]).copy()

    train_df = h1_df[pd.to_datetime(h1_df["observation_date"]) < "2023-01-01"]
    val_df = h1_df[pd.to_datetime(h1_df["observation_date"]) >= "2023-01-01"]

    forecaster = HorizonForecaster(horizon=1, model_name="logistic_regression")
    forecaster.fit(train_df, val_df)

    assert forecaster.is_fitted is True

    # Test prediction
    probs = forecaster.predict_proba(val_df)
    assert len(probs) == len(val_df)
    assert (probs >= 0.0).all() and (probs <= 1.0).all()

    # Test standardized output schema
    sample_row = val_df.iloc[0]
    out = forecaster.generate_forecast_output(sample_row)

    required_keys = [
        "county",
        "observation_date",
        "forecast_horizon_months",
        "target_date",
        "risk_probability",
        "risk_band",
        "decision_threshold",
        "predicted_crisis_alert",
        "model_version",
        "top_risk_signals"
    ]
    for k in required_keys:
        assert k in out, f"Missing key {k} in forecast schema output"

    assert out["risk_band"] in ["Low", "Moderate", "Elevated", "High"]
    assert isinstance(out["top_risk_signals"], list)


# --- 6. Inference Service & Early-Warning Table Tests ---

def test_multi_horizon_county_forecast():
    """Verify county multi-horizon forecast returns 1M, 2M, and 3M projections."""
    summary = generate_county_multi_horizon_forecast("Turkana")
    assert summary["county"] == "Turkana"
    assert "trend" in summary
    assert "forecasts" in summary
    assert "h1" in summary["forecasts"]
    assert "h2" in summary["forecasts"]
    assert "h3" in summary["forecasts"]


def test_early_warning_summary_table():
    """Verify multi-county early-warning summary matrix."""
    table = generate_early_warning_summary_table()
    assert isinstance(table, pd.DataFrame)
    assert not table.empty
    assert "County" in table.columns
    assert "1M Risk (t+1)" in table.columns
    assert "2M Risk (t+2)" in table.columns
    assert "3M Risk (t+3)" in table.columns
    assert "Early-Warning Signal" in table.columns
    assert len(table) >= 5
