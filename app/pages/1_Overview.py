"""Overview Page - Kenya County Choropleth Risk Map & Executive Summary."""

import streamlit as st
import pandas as pd
from agririsk.dashboard.formatting import render_disclaimer_banner, render_risk_badge, format_anomaly, format_zscore
from agririsk.dashboard.queries import load_scored_dataset, get_latest_snapshot, get_available_counties
from agririsk.dashboard.metrics import compute_overview_kpis, build_county_ranking_table
from agririsk.dashboard.maps import create_county_choropleth_map

st.set_page_config(
    page_title="Overview & Choropleth Map - AgriRisk Kenya",
    page_icon="🗺️",
    layout="wide"
)

# Research Disclaimer Banner
st.markdown(render_disclaimer_banner(), unsafe_allow_html=True)

st.title("🗺️ National & County Risk Overview")
st.markdown(
    "Synthesizing climate, vegetation, and market indicators into a unified model-estimated "
    "acute food insecurity risk classification across monitored Kenyan counties."
)

# Load data with caching
@st.cache_data
def get_dashboard_data():
    return load_scored_dataset()

df = get_dashboard_data()
snapshot_df = get_latest_snapshot(df)
kpis = compute_overview_kpis(snapshot_df)

# Top KPI Metric Cards
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Counties Monitored", f"{kpis['counties_monitored']} ASAL Counties")
with col2:
    st.metric("Elevated / High Risk Counties", f"{kpis['elevated_or_high_count']} Counties",
              delta=f"{kpis['high_risk_count']} High Risk", delta_color="inverse")
with col3:
    st.metric("Latest Monitoring Period", kpis["latest_period"])
with col4:
    st.metric("Average Model Risk", f"{kpis['average_risk_prob'] * 100:.1f}%")

st.divider()

# Layout: Left column for Choropleth Map, Right column for Selected County Detail Inspector
col_map, col_detail = st.columns([1.6, 1.0])

available_counties = get_available_counties(snapshot_df)

with col_detail:
    st.subheader("🔍 County Inspector")
    selected_county = st.selectbox(
        "Select a county to inspect:",
        options=available_counties,
        index=0,
        help="Select a monitored ASAL county to view current status and key environmental indicators."
    )

    county_row = snapshot_df[snapshot_df["county_name"] == selected_county].iloc[0]

    # Inspection Card
    risk_band = county_row["risk_band"]
    risk_prob = county_row["model_risk_prob"]

    st.markdown(
        f"""
        <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <h3 style="margin: 0; color: #0f172a;">{selected_county}</h3>
                {render_risk_badge(risk_band)}
            </div>
            <p style="margin: 0 0 10px 0; color: #64748b; font-size: 0.9rem;">Period: <strong>{county_row['period']}</strong></p>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.9rem;">
                <div><strong>Model Risk Prob:</strong> <code>{risk_prob * 100:.1f}%</code></div>
                <div><strong>Prior IPC Phase:</strong> <code>Phase {int(county_row['previous_ipc_phase']) if pd.notnull(county_row['previous_ipc_phase']) else 'N/A'}</code></div>
                <div><strong>3M Rain Anomaly:</strong> <code>{format_anomaly(county_row['rainfall_anomaly_3m'])}</code></div>
                <div><strong>3M NDVI Anomaly:</strong> <code>{format_anomaly(county_row['ndvi_anomaly_3m'])}</code></div>
                <div><strong>Maize Price Z-Score:</strong> <code>{format_zscore(county_row['maize_price_zscore'])}</code></div>
                <div><strong>Dry Spell Streak:</strong> <code>{int(county_row['consecutive_dry_months'])} months</code></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.info(
        f"💡 **Indicator Insight:** {selected_county} shows a 3-month rainfall anomaly of "
        f"{format_anomaly(county_row['rainfall_anomaly_3m'])} and vegetation anomaly of "
        f"{format_anomaly(county_row['ndvi_anomaly_3m'])}. "
        f"Staple maize prices are {format_zscore(county_row['maize_price_zscore'])} from historical seasonal levels."
    )

with col_map:
    st.subheader("🗺️ Kenya County Risk Map")
    fig_map, is_valid_join, unmatched = create_county_choropleth_map(snapshot_df, selected_county=selected_county)

    if not is_valid_join:
        st.warning(f"⚠️ Spatial Join Warning: Some model counties failed to match geographic layer: {unmatched}")

    st.plotly_chart(fig_map, use_container_width=True)
    st.caption("Grey polygons indicate Kenyan counties not included in the current 5-county ASAL pilot study.")

st.divider()

# County Risk Ranking Table
st.subheader("📋 County Risk Rankings (Current Snapshot)")
ranking_table = build_county_ranking_table(snapshot_df)

# Format numerical columns for table view
display_table = ranking_table.copy()
display_table["Model Risk Prob"] = display_table["Model Risk Prob"].apply(lambda x: f"{x * 100:.1f}%")
display_table["Rainfall Anom (3M)"] = display_table["Rainfall Anom (3M)"].apply(lambda x: format_anomaly(x))
display_table["NDVI Anom (3M)"] = display_table["NDVI Anom (3M)"].apply(lambda x: format_anomaly(x))
display_table["Price Z-Score"] = display_table["Price Z-Score"].apply(lambda x: format_zscore(x))

st.dataframe(
    display_table,
    use_container_width=True,
    hide_index=True
)

st.caption(
    "Rankings are sorted by model risk probability descending. "
    "Prior IPC Phase reflects historical benchmark classifications, whereas Model Risk Prob is a statistical estimation."
)
