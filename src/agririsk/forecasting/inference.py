"""Inference service, multi-horizon risk scoring, and early-warning signal generation."""

from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

from agririsk.core.logging import logger
from agririsk.core.constants import KENYA_COUNTIES
from agririsk.dashboard.formatting import assign_risk_band
from agririsk.forecasting.features import load_forecast_dataset, FORECAST_FEATURE_COLUMNS
from agririsk.forecasting.models import HorizonForecaster, MODEL_ARTIFACTS_DIR

FORECAST_MODELS_CACHE: Dict[int, HorizonForecaster] = {}


def load_forecaster(horizon: int) -> HorizonForecaster:
    """Load serialized horizon forecaster from disk or cache."""
    if horizon in FORECAST_MODELS_CACHE:
        return FORECAST_MODELS_CACHE[horizon]

    model_path = MODEL_ARTIFACTS_DIR / f"forecast_model_h{horizon}.joblib"
    if model_path.exists():
        forecaster = HorizonForecaster.load(model_path)
    else:
        logger.warning("Forecast model h=%d not found on disk, training default instance...", horizon)
        df = load_forecast_dataset()
        train_sub = df[(df["horizon_months"] == horizon) & df["target_phase3plus"].notnull()]
        forecaster = HorizonForecaster(horizon=horizon, model_name="random_forest")
        forecaster.fit(train_sub)
        forecaster.save(model_path)

    FORECAST_MODELS_CACHE[horizon] = forecaster
    return forecaster


def load_all_forecasters() -> Dict[int, HorizonForecaster]:
    """Load forecasters for horizons 1, 2, and 3."""
    return {h: load_forecaster(h) for h in (1, 2, 3)}


def generate_county_multi_horizon_forecast(
    county_name: str,
    observation_period: Optional[str] = None
) -> Dict[str, Any]:
    """Generate 1M, 2M, and 3M forward forecasts for a single county.

    Args:
        county_name: Canonical county name.
        observation_period: Optional period ('YYYY-MM'). If omitted, uses latest available.

    Returns:
        Dictionary containing 1M, 2M, 3M forecast outputs and summary trend.
    """
    df = load_forecast_dataset()
    county_df = df[df["county_name"] == county_name].copy()

    if observation_period is None:
        obs_period = county_df["observation_period"].max()
    else:
        obs_period = observation_period

    forecasters = load_all_forecasters()
    forecasts = {}

    for h in (1, 2, 3):
        h_forecaster = forecasters[h]
        row_match = county_df[
            (county_df["observation_period"] == obs_period) &
            (county_df["horizon_months"] == h)
        ]
        if row_match.empty:
            continue

        row = row_match.iloc[0]
        out = h_forecaster.generate_forecast_output(row)
        forecasts[f"h{h}"] = out

    # Determine trend across 1M -> 2M -> 3M
    probs = [forecasts[f"h{h}"]["risk_probability"] for h in (1, 2, 3) if f"h{h}" in forecasts]
    if len(probs) >= 2:
        diff = probs[-1] - probs[0]
        if diff > 0.10:
            trend = "Increasing Risk (+)"
        elif diff < -0.10:
            trend = "Decreasing Risk (-)"
        else:
            trend = "Stable (=)"
    else:
        trend = "Stable (=)"

    return {
        "county": county_name,
        "observation_period": obs_period,
        "trend": trend,
        "forecasts": forecasts
    }


def generate_early_warning_summary_table(
    observation_period: Optional[str] = None
) -> pd.DataFrame:
    """Generate early-warning comparison table across all monitored counties.

    Columns:
        County | 1M Risk | 2M Risk | 3M Risk | Trend | Main Signals | Alert Status
    """
    df = load_forecast_dataset()
    counties = sorted(df["county_name"].unique().tolist())

    if observation_period is None:
        obs_period = df["observation_period"].max()
    else:
        obs_period = observation_period

    rows = []
    for c in counties:
        summary = generate_county_multi_horizon_forecast(c, observation_period=obs_period)
        fcasts = summary.get("forecasts", {})

        p1 = fcasts.get("h1", {}).get("risk_probability", np.nan)
        p2 = fcasts.get("h2", {}).get("risk_probability", np.nan)
        p3 = fcasts.get("h3", {}).get("risk_probability", np.nan)

        alert1 = fcasts.get("h1", {}).get("predicted_crisis_alert", False)
        alert2 = fcasts.get("h2", {}).get("predicted_crisis_alert", False)
        alert3 = fcasts.get("h3", {}).get("predicted_crisis_alert", False)
        is_elevated = any([alert1, alert2, alert3])

        signals = fcasts.get("h1", {}).get("top_risk_signals", ["Normal seasonal bounds"])
        main_signals_str = "; ".join(signals[:2])

        rows.append({
            "County": c,
            "1M Risk (t+1)": f"{p1 * 100:.1f}%" if pd.notnull(p1) else "N/A",
            "2M Risk (t+2)": f"{p2 * 100:.1f}%" if pd.notnull(p2) else "N/A",
            "3M Risk (t+3)": f"{p3 * 100:.1f}%" if pd.notnull(p3) else "N/A",
            "Trend": summary.get("trend", "Stable"),
            "Main Signals": main_signals_str,
            "Early-Warning Signal": "Elevated Model Signal [Alert]" if is_elevated else "Normal Monitoring [OK]",
            "_max_prob": max([p for p in [p1, p2, p3] if pd.notnull(p)], default=0.0)
        })

    out_df = pd.DataFrame(rows).sort_values(by="_max_prob", ascending=False).drop(columns=["_max_prob"])
    return out_df
