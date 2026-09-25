"""Lagged feature engineering and forecast dataset construction for AgriRisk Kenya."""

from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np

from agririsk.core.logging import logger
from agririsk.core.constants import KENYA_COUNTIES

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
RAW_MODEL_DATASET_PATH = PROJECT_ROOT / "data" / "processed" / "model_dataset.csv"
FORECAST_DATASET_PATH = PROJECT_ROOT / "data" / "processed" / "forecast_dataset.csv"

# Canonical feature list for short-horizon forecasting models
FORECAST_FEATURE_COLUMNS: List[str] = [
    # Climate lags & rolling indicators
    "rainfall_anomaly_lag1",
    "rainfall_anomaly_lag2",
    "rainfall_anomaly_lag3",
    "rainfall_rolling_3m",
    "rainfall_rolling_6m",
    "consecutive_dry_months",
    # Vegetation lags & trend indicators
    "ndvi_anomaly_lag1",
    "ndvi_anomaly_lag2",
    "ndvi_anomaly_lag3",
    "ndvi_trend_3m",
    "ndvi_trend_6m",
    # Market price indicators
    "maize_price_change_1m",
    "maize_price_change_3m",
    "maize_price_change_6m",
    "maize_price_zscore",
    # Food security history
    "previous_ipc_phase",
    "ipc_phase_lag2",
    "ipc_phase_lag3",
    # Seasonality
    "month",
    "quarter",
    "is_long_rains",
    "is_short_rains",
    # Ecological context
    "is_arid",
    # Spatial neighbourhood context (Milestone 6)
    "neighbour_mean_rainfall_anomaly",
    "neighbour_mean_ndvi_anomaly",
    "neighbour_mean_price_change",
    "neighbour_mean_previous_risk",
    "number_of_high_risk_neighbours",
]


def determine_season(month: int) -> str:
    """Classify Kenyan agro-ecological calendar season.

    Args:
        month: 1-indexed calendar month (1 to 12).

    Returns:
        Season code: 'MAM' (Long Rains), 'OND' (Short Rains),
        'JF' (Post-Short Rains Dry), 'JJAS' (Post-Long Rains Dry).
    """
    if month in (3, 4, 5):
        return "MAM"
    elif month in (10, 11, 12):
        return "OND"
    elif month in (1, 2):
        return "JF"
    else:
        return "JJAS"


class ForecastFeatureEngineer:
    """Generates lagged features and multi-horizon forward targets without temporal leakage."""

    @staticmethod
    def engineer_lagged_features(df: pd.DataFrame) -> pd.DataFrame:
        """Create lagged climate, vegetation, market, and IPC predictors per county.

        All rolling and lag operations are applied strictly within each county group
        sorted chronologically from past to present.

        Args:
            df: Scored or processed county-month DataFrame (must contain year, month, county_name).

        Returns:
            pd.DataFrame with all required lagged features and forward targets.
        """
        records = []
        # Map county ASAL categories
        asal_map = {c["name"]: (1 if c["asal_category"] == "Arid" else 0) for c in KENYA_COUNTIES}

        for county_name, group in df.groupby("county_name"):
            g = group.sort_values(by=["year", "month"]).copy().reset_index(drop=True)

            # Observation date
            g["observation_date"] = pd.to_datetime(
                g["year"].astype(str) + "-" + g["month"].astype(str).str.zfill(2) + "-01"
            )
            g["observation_period"] = g["year"].astype(str) + "-" + g["month"].astype(str).str.zfill(2)

            # 1. Climate Lags & Rolling
            g["rainfall_anomaly_lag1"] = g["rainfall_anomaly_1m"].shift(1)
            g["rainfall_anomaly_lag2"] = g["rainfall_anomaly_1m"].shift(2)
            g["rainfall_anomaly_lag3"] = g["rainfall_anomaly_1m"].shift(3)
            # 6-month rolling rainfall sum
            g["rainfall_rolling_6m"] = g["rainfall_rolling_3m"] + g["rainfall_rolling_3m"].shift(3)

            # 2. Vegetation Lags & Trends
            g["ndvi_anomaly_lag1"] = g["ndvi_anomaly_1m"].shift(1)
            g["ndvi_anomaly_lag2"] = g["ndvi_anomaly_1m"].shift(2)
            g["ndvi_anomaly_lag3"] = g["ndvi_anomaly_1m"].shift(3)
            # 6-month NDVI change
            g["ndvi_trend_6m"] = g["ndvi_anomaly_1m"] - g["ndvi_anomaly_1m"].shift(6)

            # 3. Market Lags
            # 6-month maize price change
            g["maize_price_change_6m"] = g["maize_price_change_3m"] + g["maize_price_change_3m"].shift(3)

            # 4. Food Security History Lags
            # previous_ipc_phase is already lag 1 (phase at t-1)
            g["ipc_phase_lag2"] = g["previous_ipc_phase"].shift(1)
            g["ipc_phase_lag3"] = g["previous_ipc_phase"].shift(2)

            # 5. Seasonality & Context
            g["quarter"] = g["observation_date"].dt.quarter
            g["season"] = g["month"].apply(determine_season)
            g["is_long_rains"] = (g["season"] == "MAM").astype(int)
            g["is_short_rains"] = (g["season"] == "OND").astype(int)
            g["is_arid"] = asal_map.get(county_name, 1)

            # 6. Forward Targets (strictly target_date > observation_date)
            # target_phase3plus_t1: target 1 month ahead (t+1)
            # target_phase3plus_t2: target 2 months ahead (t+2)
            # target_phase3plus_t3: target 3 months ahead (t+3)
            g["target_phase3plus_t1"] = g["target_phase3plus"].shift(-1)
            g["target_phase3plus_t2"] = g["target_phase3plus"].shift(-2)
            g["target_phase3plus_t3"] = g["target_phase3plus"].shift(-3)

            records.append(g)

        result_df = pd.concat(records).sort_values(by=["county_name", "observation_date"]).reset_index(drop=True)
        return result_df

    @classmethod
    def build_forecast_dataset(
        cls,
        input_csv: Optional[Path] = None,
        output_csv: Optional[Path] = None
    ) -> pd.DataFrame:
        """Construct the long-format multi-horizon forecast dataset.

        Each row represents:
        county-month-prediction_horizon (horizon_months in {1, 2, 3})

        Args:
            input_csv: Path to input model_dataset.csv (defaults to RAW_MODEL_DATASET_PATH).
            output_csv: Target output path (defaults to FORECAST_DATASET_PATH).

        Returns:
            pd.DataFrame containing long-format multi-horizon forecasting observations.
        """
        source_path = input_csv or RAW_MODEL_DATASET_PATH
        out_path = output_csv or FORECAST_DATASET_PATH

        if not source_path.exists():
            raise FileNotFoundError(f"Input modeling dataset not found: {source_path}")

        raw_df = pd.read_csv(source_path)
        wide_df = cls.engineer_lagged_features(raw_df)

        long_rows = []
        for _, row in wide_df.iterrows():
            obs_date = row["observation_date"]
            county = row["county_name"]

            # Feature dictionary for this observation period
            features = {feat: row.get(feat, np.nan) for feat in FORECAST_FEATURE_COLUMNS}

            for h in (1, 2, 3):
                target_col = f"target_phase3plus_t{h}"
                target_val = row.get(target_col, np.nan)
                target_date = obs_date + pd.DateOffset(months=h)

                # Strict validation: target_date MUST be strictly in the future of observation_date
                if not (target_date > obs_date):
                    raise ValueError(
                        f"Temporal leakage detected! target_date ({target_date}) <= obs_date ({obs_date})"
                    )

                long_record = {
                    "county_name": county,
                    "observation_date": obs_date.strftime("%Y-%m-%d"),
                    "observation_period": obs_date.strftime("%Y-%m"),
                    "horizon_months": h,
                    "target_date": target_date.strftime("%Y-%m-%d"),
                    "target_period": target_date.strftime("%Y-%m"),
                    "target_phase3plus": target_val,
                    **features
                }
                long_rows.append(long_record)

        forecast_df = pd.DataFrame(long_rows)

        # Enrich with leakage-safe spatial features
        try:
            from agririsk.geospatial.spatial_features import SpatialFeatureEngineer
            spatial_eng = SpatialFeatureEngineer()
            forecast_df = spatial_eng.add_spatial_features(forecast_df)
        except Exception as e:
            logger.warning("Spatial feature enrichment skipped: %s", e)

        # Save to disk
        out_path.parent.mkdir(parents=True, exist_ok=True)
        forecast_df.to_csv(out_path, index=False)
        logger.info(
            "Constructed forecast dataset with %d rows saved to %s",
            len(forecast_df),
            out_path
        )

        return forecast_df


def load_forecast_dataset() -> pd.DataFrame:
    """Load or generate the long-format forecast dataset.

    Returns:
        pd.DataFrame of multi-horizon forecast observations.
    """
    if FORECAST_DATASET_PATH.exists():
        return pd.read_csv(FORECAST_DATASET_PATH)
    return ForecastFeatureEngineer.build_forecast_dataset()
