"""Geospatial choropleth map generation and spatial validation for AgriRisk Kenya."""

import json
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from agririsk.core.constants import KENYA_COUNTIES
from agririsk.core.logging import logger
from agririsk.geospatial.boundaries import validate_county_spatial_join, GEOJSON_PATH
from agririsk.dashboard.formatting import RISK_COLORS, assign_risk_band

# Discrete color mapping for choropleth including unmonitored status
MAP_COLOR_DISCRETE = {
    "High": RISK_COLORS["High"],
    "Elevated": RISK_COLORS["Elevated"],
    "Moderate": RISK_COLORS["Moderate"],
    "Low": RISK_COLORS["Low"],
    "Not Monitored": "#e2e8f0"  # Neutral slate-gray
}

MAP_CATEGORY_ORDERS = {
    "risk_band": ["High", "Elevated", "Moderate", "Low", "Not Monitored"]
}


def load_county_geojson_dict() -> Dict[str, Any]:
    """Load Kenya county boundary GeoJSON dictionary for Plotly mapping.

    Returns:
        GeoJSON dict representation.
    """
    if not GEOJSON_PATH.exists():
        from scripts.generate_county_geojson import generate_kenya_county_geojson
        generate_kenya_county_geojson(GEOJSON_PATH)

    with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def prepare_map_geodata(snapshot_df: pd.DataFrame) -> Tuple[pd.DataFrame, bool, List[str]]:
    """Join snapshot dataset with all 47 counties for complete choropleth visualization.

    Validates that model counties match the geographic boundary names.

    Args:
        snapshot_df: Latest snapshot DataFrame containing monitored counties.

    Returns:
        Tuple of (merged_df: pd.DataFrame, is_valid: bool, unmatched: List[str]).
    """
    # 47 Kenya counties master list
    all_counties = [c["name"] for c in KENYA_COUNTIES]
    master_df = pd.DataFrame({"county_name": all_counties})

    model_counties = snapshot_df["county_name"].unique().tolist()
    is_valid, unmatched = validate_county_spatial_join(model_counties, all_counties)

    if not is_valid:
        logger.warning("Spatial join mismatch: %d counties missing in boundary layer: %s", len(unmatched), unmatched)

    # Merge snapshot with all 47 counties
    merged = master_df.merge(snapshot_df, on="county_name", how="left")

    # Set defaults for unmonitored counties
    merged["is_monitored"] = merged["county_name"].isin(model_counties)
    merged["risk_band"] = merged["risk_band"].fillna("Not Monitored")
    merged["risk_prob_display"] = merged["model_risk_prob"].apply(
        lambda p: f"{p * 100:.1f}%" if pd.notnull(p) else "Not Monitored"
    )
    merged["ipc_display"] = merged["previous_ipc_phase"].apply(
        lambda x: str(int(x)) if pd.notnull(x) else "N/A"
    )
    merged["rain_anom_display"] = merged["rainfall_anomaly_3m"].apply(
        lambda x: f"{x:+.1f}%" if pd.notnull(x) else "N/A"
    )
    merged["ndvi_anom_display"] = merged["ndvi_anomaly_3m"].apply(
        lambda x: f"{x:+.1f}%" if pd.notnull(x) else "N/A"
    )
    merged["price_z_display"] = merged["maize_price_zscore"].apply(
        lambda x: f"{x:+.2f} \u03c3" if pd.notnull(x) else "N/A"
    )

    return merged, is_valid, unmatched


def create_county_choropleth_map(
    snapshot_df: pd.DataFrame,
    selected_county: Optional[str] = None
) -> Tuple[go.Figure, bool, List[str]]:
    """Generate interactive Plotly choropleth map of Kenyan counties.

    Args:
        snapshot_df: Snapshot DataFrame of county risk estimates.
        selected_county: Optional county to highlight or focus.

    Returns:
        Tuple of (fig: go.Figure, is_valid_join: bool, unmatched_counties: List[str]).
    """
    geojson = load_county_geojson_dict()
    map_data, is_valid, unmatched = prepare_map_geodata(snapshot_df)

    fig = px.choropleth(
        map_data,
        geojson=geojson,
        locations="county_name",
        featureidkey="properties.county_name",
        color="risk_band",
        color_discrete_map=MAP_COLOR_DISCRETE,
        category_orders=MAP_CATEGORY_ORDERS,
        hover_name="county_name",
        hover_data={
            "risk_band": True,
            "risk_prob_display": True,
            "ipc_display": True,
            "rain_anom_display": True,
            "ndvi_anom_display": True,
            "price_z_display": True,
            "county_name": False,
        },
        labels={
            "risk_band": "Risk Classification",
            "risk_prob_display": "Model Risk Probability",
            "ipc_display": "Prior IPC Phase",
            "rain_anom_display": "3M Rainfall Anomaly",
            "ndvi_anom_display": "3M NDVI Anomaly",
            "price_z_display": "Maize Price Z-Score",
        }
    )

    # Style map geometry
    fig.update_geos(
        fitbounds="locations",
        visible=False,
        showcountries=False,
        showsubunits=False,
        showcoastlines=False,
        projection_type="mercator"
    )

    fig.update_layout(
        margin={"r": 0, "t": 20, "l": 0, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            title=dict(text="<b>Model Risk Band</b>", font=dict(size=12)),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#d0d7de",
            borderwidth=1
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="sans-serif"
        ),
        height=540,
    )

    return fig, is_valid, unmatched
