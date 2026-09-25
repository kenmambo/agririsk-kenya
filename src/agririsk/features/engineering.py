"""Feature engineering pipeline for county-month agricultural risk indicators."""

from typing import List, Tuple, Optional
import numpy as np
import pandas as pd
from agririsk.core.logging import logger


class FeatureEngineer:
    """Transforms raw monthly observations into analytical time-series features per county."""

    FEATURE_COLUMNS: List[str] = [
        "rainfall_anomaly_1m",
        "rainfall_anomaly_3m",
        "rainfall_rolling_3m",
        "consecutive_dry_months",
        "ndvi_anomaly_1m",
        "ndvi_anomaly_3m",
        "ndvi_trend_3m",
        "maize_price_change_1m",
        "maize_price_change_3m",
        "maize_price_zscore",
        "previous_ipc_phase",
    ]

    ALL_TABLE_COLUMNS: List[str] = [
        "county_name",
        "year",
        "month",
        "rainfall_anomaly_1m",
        "rainfall_anomaly_3m",
        "rainfall_rolling_3m",
        "consecutive_dry_months",
        "ndvi_anomaly_1m",
        "ndvi_anomaly_3m",
        "ndvi_trend_3m",
        "maize_price_change_1m",
        "maize_price_change_3m",
        "maize_price_zscore",
        "previous_ipc_phase",
        "target_phase3plus",
    ]

    @staticmethod
    def _compute_consecutive_dry_months(anomalies: pd.Series) -> pd.Series:
        """Compute the unbroken run of consecutive preceding dry months (anomaly < 0).

        For any month t, counts consecutive negative anomaly months in [t-streak ... t-1].
        """
        streaks = []
        current_streak = 0

        # We look at historical prior conditions up to t-1
        for anom in anomalies:
            streaks.append(current_streak)
            if pd.isna(anom):
                current_streak = 0
            elif anom < 0.0:
                current_streak += 1
            else:
                current_streak = 0

        return pd.Series(streaks, index=anomalies.index)

    @classmethod
    def transform(
        cls,
        climate_df: pd.DataFrame,
        vegetation_df: pd.DataFrame,
        market_df: pd.DataFrame,
        ipc_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Join all raw observation streams and engineer county-month features.

        Grouping is strictly by county_name to guarantee temporal isolation.

        Returns:
            Master feature table matching Milestone 2 specification.
        """
        logger.info("Merging raw observation streams for feature engineering...")

        # 1. Merge climate, vegetation, market
        merged = climate_df.merge(
            vegetation_df,
            on=["county_name", "year", "month"],
            how="inner"
        )
        merged = merged.merge(
            market_df,
            on=["county_name", "year", "month"],
            how="inner"
        )

        # 2. Merge IPC monthly ground truth
        merged = merged.merge(
            ipc_df,
            on=["county_name", "year", "month"],
            how="inner"
        )

        # 3. Sort chronologically
        merged = merged.sort_values(by=["county_name", "year", "month"]).reset_index(drop=True)

        county_frames = []

        for county, grp in merged.groupby("county_name", as_index=False):
            df = grp.copy().sort_values(by=["year", "month"]).reset_index(drop=True)

            # Climate Features
            df["rainfall_anomaly_1m"] = df["rainfall_anomaly"].shift(1)
            df["rainfall_anomaly_3m"] = df["rainfall_anomaly"].shift(3)
            df["rainfall_rolling_3m"] = df["rainfall_mm"].rolling(window=3, min_periods=1).mean()
            df["consecutive_dry_months"] = cls._compute_consecutive_dry_months(df["rainfall_anomaly"])

            # Vegetation Features
            df["ndvi_anomaly_1m"] = df["ndvi_anomaly"].shift(1)
            df["ndvi_anomaly_3m"] = df["ndvi_anomaly"].shift(3)
            df["ndvi_trend_3m"] = df["ndvi_mean"] - df["ndvi_mean"].shift(3)

            # Market Features (Maize Price Dynamics)
            price_prev1 = df["price"].shift(1)
            price_prev3 = df["price"].shift(3)
            df["maize_price_change_1m"] = ((df["price"] - price_prev1) / price_prev1) * 100.0
            df["maize_price_change_3m"] = ((df["price"] - price_prev3) / price_prev3) * 100.0
            df["rolling_price_mean_3m"] = df["price"].rolling(window=3, min_periods=1).mean()

            # Price z-score relative to county historical baseline
            county_mean_price = df["price"].mean()
            county_std_price = df["price"].std(ddof=1) or 1.0
            df["maize_price_zscore"] = (df["price"] - county_mean_price) / county_std_price

            # Food Security Lag
            df["previous_ipc_phase"] = df["ipc_phase"].shift(1)

            county_frames.append(df)

        result_df = pd.concat(county_frames, ignore_index=True)

        # Select only the official table columns
        feature_table = result_df[cls.ALL_TABLE_COLUMNS].copy()

        logger.info(
            "Feature engineering complete. Total rows: %d, feature columns: %d",
            len(feature_table),
            len(cls.FEATURE_COLUMNS),
        )
        return feature_table
