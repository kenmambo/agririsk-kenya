"""KPI metric computation and summary ranking calculations for AgriRisk Kenya."""

from typing import Dict, Any, List
import pandas as pd
import numpy as np


def compute_overview_kpis(snapshot_df: pd.DataFrame) -> Dict[str, Any]:
    """Compute top executive KPI summary statistics for the overview dashboard.

    Args:
        snapshot_df: DataFrame of current county snapshot records.

    Returns:
        Dictionary containing overview KPIs.
    """
    if snapshot_df.empty:
        return {
            "counties_monitored": 0,
            "elevated_or_high_count": 0,
            "latest_period": "N/A",
            "average_risk_prob": 0.0,
            "high_risk_count": 0,
            "elevated_risk_count": 0,
            "moderate_risk_count": 0,
            "low_risk_count": 0,
        }

    total_counties = len(snapshot_df)
    latest_period = str(snapshot_df["period"].iloc[0]) if "period" in snapshot_df.columns else "N/A"
    avg_prob = float(snapshot_df["model_risk_prob"].mean()) if "model_risk_prob" in snapshot_df.columns else 0.0

    bands = snapshot_df["risk_band"].value_counts().to_dict() if "risk_band" in snapshot_df.columns else {}
    high_count = bands.get("High", 0)
    elevated_count = bands.get("Elevated", 0)
    moderate_count = bands.get("Moderate", 0)
    low_count = bands.get("Low", 0)

    elevated_or_high = high_count + elevated_count

    return {
        "counties_monitored": total_counties,
        "elevated_or_high_count": elevated_or_high,
        "latest_period": latest_period,
        "average_risk_prob": avg_prob,
        "high_risk_count": high_count,
        "elevated_risk_count": elevated_count,
        "moderate_risk_count": moderate_count,
        "low_risk_count": low_count,
    }


def build_county_ranking_table(snapshot_df: pd.DataFrame) -> pd.DataFrame:
    """Build a sorted county risk ranking table formatted for display.

    Args:
        snapshot_df: Latest snapshot DataFrame.

    Returns:
        Formatted DataFrame sorted by model risk descending.
    """
    if snapshot_df.empty:
        return pd.DataFrame()

    df = snapshot_df.copy()
    df = df.sort_values(by="model_risk_prob", ascending=False).reset_index(drop=True)

    ranking_cols = [
        "county_name",
        "risk_band",
        "model_risk_prob",
        "previous_ipc_phase",
        "rainfall_anomaly_3m",
        "ndvi_anomaly_3m",
        "maize_price_zscore",
        "consecutive_dry_months",
    ]
    present_cols = [c for c in ranking_cols if c in df.columns]
    table = df[present_cols].copy()

    # Friendly column names
    col_rename = {
        "county_name": "County",
        "risk_band": "Risk Band",
        "model_risk_prob": "Model Risk Prob",
        "previous_ipc_phase": "Prior IPC Phase",
        "rainfall_anomaly_3m": "Rainfall Anom (3M)",
        "ndvi_anomaly_3m": "NDVI Anom (3M)",
        "maize_price_zscore": "Price Z-Score",
        "consecutive_dry_months": "Dry Streak (Mo)",
    }
    table = table.rename(columns=col_rename)
    return table


def compute_data_quality_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute data quality, completeness, and missingness metrics across dataset.

    Args:
        df: Raw or scored dataset.

    Returns:
        Dictionary with data quality diagnostics.
    """
    total_rows = len(df)
    total_counties = df["county_name"].nunique() if "county_name" in df.columns else 0
    min_year = df["year"].min() if "year" in df.columns else 0
    max_year = df["year"].max() if "year" in df.columns else 0

    # Duplicates check
    dups = df.duplicated(subset=["county_name", "year", "month"]).sum() if "county_name" in df.columns else 0

    # Missingness summary per column
    missing_pct = (df.isnull().sum() / total_rows * 100).round(1).to_dict()

    # Source completeness
    climate_cols = ["rainfall_anomaly_1m", "rainfall_anomaly_3m", "rainfall_rolling_3m"]
    vegetation_cols = ["ndvi_anomaly_1m", "ndvi_anomaly_3m", "ndvi_trend_3m"]
    market_cols = ["maize_price_change_1m", "maize_price_change_3m", "maize_price_zscore"]
    ipc_cols = ["previous_ipc_phase", "target_phase3plus"]

    def calc_source_completeness(cols: List[str]) -> float:
        present = [c for c in cols if c in df.columns]
        if not present:
            return 0.0
        missing = df[present].isnull().mean().mean()
        return round(float((1.0 - missing) * 100), 1)

    return {
        "total_records": total_rows,
        "counties_count": total_counties,
        "year_range": f"{min_year} - {max_year}",
        "duplicate_rows": int(dups),
        "overall_completeness_pct": round(float((1.0 - df.isnull().mean().mean()) * 100), 1),
        "climate_completeness_pct": calc_source_completeness(climate_cols),
        "vegetation_completeness_pct": calc_source_completeness(vegetation_cols),
        "market_completeness_pct": calc_source_completeness(market_cols),
        "ipc_completeness_pct": calc_source_completeness(ipc_cols),
        "missing_by_column": missing_pct,
    }
