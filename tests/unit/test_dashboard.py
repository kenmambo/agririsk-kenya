"""Unit tests for AgriRisk Kenya dashboard analytics, querying, maps, charts, and formatting."""

import pytest
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from agririsk.dashboard.formatting import (
    assign_risk_band,
    get_risk_color,
    render_risk_badge,
    render_disclaimer_banner,
    format_anomaly,
    format_zscore,
    format_currency,
    generate_non_causal_interpretation,
)
from agririsk.geospatial.boundaries import validate_county_spatial_join
from agririsk.dashboard.queries import (
    load_scored_dataset,
    get_latest_snapshot,
    get_available_counties,
    get_available_periods,
    filter_dataset,
    get_county_timeseries,
    load_model_evaluation_metrics,
)
from agririsk.dashboard.metrics import (
    compute_overview_kpis,
    build_county_ranking_table,
    compute_data_quality_metrics,
)
from agririsk.dashboard.maps import (
    create_county_choropleth_map,
    prepare_map_geodata,
)
from agririsk.dashboard.charts import (
    plot_risk_probability_timeline,
    plot_rainfall_anomaly_timeline,
    plot_ndvi_anomaly_timeline,
    plot_market_price_timeline,
    plot_ipc_classification_timeline,
    plot_global_feature_importance,
    plot_local_feature_contributions,
    plot_confusion_matrix_heatmap,
)


# --- 1. Risk Banding & Formatting Tests ---

def test_risk_band_thresholds():
    """Verify continuous probability maps to correct discrete risk bands."""
    assert assign_risk_band(0.10) == "Low"
    assert assign_risk_band(0.249) == "Low"
    assert assign_risk_band(0.25) == "Moderate"
    assert assign_risk_band(0.499) == "Moderate"
    assert assign_risk_band(0.50) == "Elevated"
    assert assign_risk_band(0.749) == "Elevated"
    assert assign_risk_band(0.75) == "High"
    assert assign_risk_band(0.95) == "High"
    assert assign_risk_band(1.0) == "High"


def test_get_risk_color():
    """Verify colors exist for each risk band."""
    for band in ["Low", "Moderate", "Elevated", "High"]:
        color = get_risk_color(band)
        assert color.startswith("#")
    assert get_risk_color("Unknown") == "#6c757d"


def test_render_risk_badge():
    """Verify badge HTML string format."""
    badge = render_risk_badge("High")
    assert "High Risk" in badge
    assert "<span" in badge


def test_render_disclaimer_banner():
    """Verify disclaimer banner contains core research prototype text."""
    banner = render_disclaimer_banner()
    assert "RESEARCH PROTOTYPE" in banner
    assert "NOT AN OPERATIONAL WARNING" in banner
    assert "KFSSG" in banner


def test_number_formatters():
    """Verify anomaly and z-score string formatting."""
    assert format_anomaly(15.24) == "+15.2%"
    assert format_anomaly(-25.88) == "-25.9%"
    assert format_anomaly(None) == "N/A"
    assert format_anomaly(np.nan) == "N/A"

    assert "+1.45 \u03c3" in format_zscore(1.45)
    assert "-0.80 \u03c3" in format_zscore(-0.80)
    assert format_zscore(None) == "N/A"

    assert format_currency(3500.50) == "KES 3,500.50"
    assert format_currency(None) == "N/A"


def test_non_causal_interpretation_generator():
    """Verify non-causal contextual text generation."""
    indicators = {
        "rainfall_anomaly_3m": -35.0,
        "consecutive_dry_months": 3,
        "ndvi_anomaly_3m": -15.0,
        "maize_price_zscore": 1.5,
        "previous_ipc_phase": "Crisis"
    }
    text = generate_non_causal_interpretation("Turkana", "2024-12", "High", 0.88, indicators)
    assert "Turkana" in text
    assert "88.0%" in text
    assert "High Risk" in text
    assert "Non-Causal Note" in text
    assert "does not imply direct causality" in text


# --- 2. Spatial Join Validation Tests ---

def test_spatial_join_validation_valid():
    """Verify valid spatial join returns True and empty unmatched list."""
    model_counties = ["Turkana", "Marsabit", "Garissa"]
    geo_counties = ["turkana", "marsabit", "garissa", "mandera", "nairobi"]
    is_valid, unmatched = validate_county_spatial_join(model_counties, geo_counties)
    assert is_valid is True
    assert unmatched == []


def test_spatial_join_validation_unmatched():
    """Verify missing county is caught and returned."""
    model_counties = ["Turkana", "AtlantisCounty"]
    geo_counties = ["Turkana", "Marsabit"]
    is_valid, unmatched = validate_county_spatial_join(model_counties, geo_counties)
    assert is_valid is False
    assert unmatched == ["AtlantisCounty"]


# --- 3. Queries and Scored Dataset Tests ---

def test_load_scored_dataset():
    """Verify scored dataset loads with required derived columns."""
    df = load_scored_dataset()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "period" in df.columns
    assert "model_risk_prob" in df.columns
    assert "risk_band" in df.columns
    # Check probability range
    assert df["model_risk_prob"].min() >= 0.0
    assert df["model_risk_prob"].max() <= 1.0


def test_latest_snapshot_extraction():
    """Verify latest snapshot contains exactly 1 row per county."""
    df = load_scored_dataset()
    snapshot = get_latest_snapshot(df)
    assert not snapshot.empty
    assert snapshot["county_name"].nunique() == len(snapshot)
    assert snapshot["period"].nunique() == 1


def test_dataset_filtering():
    """Verify dataset slicing helpers."""
    df = load_scored_dataset()
    all_counties = get_available_counties(df)
    assert "Turkana" in all_counties
    assert "Marsabit" in all_counties

    # Single county filter
    turkana_df = filter_dataset(df, county="Turkana")
    assert (turkana_df["county_name"] == "Turkana").all()

    # Time range filter
    sliced_df = filter_dataset(df, county="Turkana", start_period="2023-01", end_period="2023-12")
    assert len(sliced_df) == 12
    assert sliced_df["period"].min() == "2023-01"
    assert sliced_df["period"].max() == "2023-12"


# --- 4. Overview & Data Quality Metrics Tests ---

def test_compute_overview_kpis():
    """Verify KPI aggregation dictionary structure and logic."""
    df = load_scored_dataset()
    snapshot = get_latest_snapshot(df)
    kpis = compute_overview_kpis(snapshot)

    assert kpis["counties_monitored"] == len(snapshot)
    assert 0.0 <= kpis["average_risk_prob"] <= 1.0
    assert kpis["elevated_or_high_count"] <= kpis["counties_monitored"]
    assert kpis["latest_period"] != "N/A"


def test_build_county_ranking_table():
    """Verify ranking table ordering."""
    df = load_scored_dataset()
    snapshot = get_latest_snapshot(df)
    ranking = build_county_ranking_table(snapshot)

    assert not ranking.empty
    assert "County" in ranking.columns
    assert "Model Risk Prob" in ranking.columns
    # Verify descending sort
    probs = ranking["Model Risk Prob"].tolist()
    assert probs == sorted(probs, reverse=True)


def test_compute_data_quality_metrics():
    """Verify data quality auditor."""
    df = load_scored_dataset()
    dq = compute_data_quality_metrics(df)

    assert dq["total_records"] == len(df)
    assert dq["counties_count"] >= 5
    assert dq["duplicate_rows"] == 0
    assert dq["overall_completeness_pct"] > 80.0
    assert "missing_by_column" in dq


# --- 5. Map & Chart Generator Tests ---

def test_create_county_choropleth_map():
    """Verify choropleth map figure creation."""
    df = load_scored_dataset()
    snapshot = get_latest_snapshot(df)
    fig, is_valid, unmatched = create_county_choropleth_map(snapshot)

    assert isinstance(fig, go.Figure)
    assert is_valid is True
    assert unmatched == []


def test_trend_chart_generators():
    """Verify all 5 County Explorer timeline charts generate valid Plotly figures."""
    df = load_scored_dataset()
    turkana = get_county_timeseries(df, "Turkana")

    fig1 = plot_risk_probability_timeline(turkana, "Turkana")
    fig2 = plot_rainfall_anomaly_timeline(turkana, "Turkana")
    fig3 = plot_ndvi_anomaly_timeline(turkana, "Turkana")
    fig4 = plot_market_price_timeline(turkana, "Turkana")
    fig5 = plot_ipc_classification_timeline(turkana, "Turkana")

    for fig in [fig1, fig2, fig3, fig4, fig5]:
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0


def test_explainability_and_performance_charts():
    """Verify explainability and confusion matrix charts."""
    importance_dict = {
        "previous_ipc_phase": 0.45,
        "rainfall_anomaly_3m": 0.25,
        "maize_price_zscore": 0.15,
        "ndvi_anomaly_3m": 0.10,
        "consecutive_dry_months": 0.05
    }
    fig_imp = plot_global_feature_importance(importance_dict)
    assert isinstance(fig_imp, go.Figure)

    df = load_scored_dataset()
    sample_row = df.iloc[0]
    fig_contrib = plot_local_feature_contributions(sample_row)
    assert isinstance(fig_contrib, go.Figure)

    cm = [[44, 4], [0, 12]]
    fig_cm = plot_confusion_matrix_heatmap(cm)
    assert isinstance(fig_cm, go.Figure)
