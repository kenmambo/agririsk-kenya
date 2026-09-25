"""Unit tests for feature engineering pipeline."""

import pandas as pd
import numpy as np
from agririsk.features.engineering import FeatureEngineer


def test_consecutive_dry_months_logic():
    """Verify unbroken streak calculation for negative anomalies."""
    anomalies = pd.Series([-10.0, -25.0, -5.0, 15.0, -12.0, -8.0])
    streaks = FeatureEngineer._compute_consecutive_dry_months(anomalies)

    # Expected streaks prior to current index:
    # idx 0: streak 0
    # idx 1: streak 1 (after -10)
    # idx 2: streak 2 (after -25)
    # idx 3: streak 3 (after -5)
    # idx 4: streak 0 (reset by 15.0)
    # idx 5: streak 1 (after -12)
    expected = [0, 1, 2, 3, 0, 1]
    assert streaks.tolist() == expected


def test_feature_engineering_full_transform():
    """Verify transformation of raw panels into official feature table."""
    dates = pd.date_range("2022-01-01", "2023-12-01", freq="MS")
    n = len(dates)

    clim = pd.DataFrame({
        "county_name": ["Turkana"] * n,
        "year": dates.year,
        "month": dates.month,
        "rainfall_mm": [25.0] * n,
        "rainfall_anomaly": [-15.0] * n,
    })

    veg = pd.DataFrame({
        "county_name": ["Turkana"] * n,
        "year": dates.year,
        "month": dates.month,
        "ndvi_mean": [0.25] * n,
        "ndvi_anomaly": [-8.0] * n,
    })

    mkt = pd.DataFrame({
        "county_name": ["Turkana"] * n,
        "year": dates.year,
        "month": dates.month,
        "commodity": ["Maize"] * n,
        "price": [5000.0] * n,
    })

    ipc = pd.DataFrame({
        "county_name": ["Turkana"] * n,
        "year": dates.year,
        "month": dates.month,
        "ipc_phase": [3] * n,
        "target_phase3plus": [1] * n,
    })

    table = FeatureEngineer.transform(clim, veg, mkt, ipc)

    # Verify all 15 required table columns exist
    for col in FeatureEngineer.ALL_TABLE_COLUMNS:
        assert col in table.columns

    assert len(table) == n
    # Verify previous_ipc_phase shifts by 1
    assert pd.isna(table.loc[0, "previous_ipc_phase"])
    assert table.loc[1, "previous_ipc_phase"] == 3
