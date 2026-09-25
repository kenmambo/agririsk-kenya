"""Risk Drivers & Explainability Page - Global & Local Feature Attribution."""

import streamlit as st
import pandas as pd
import numpy as np
from agririsk.dashboard.formatting import (
    render_disclaimer_banner,
    render_risk_badge,
    format_anomaly,
    format_zscore
)
from agririsk.dashboard.queries import (
    load_scored_dataset,
    load_model_artifact,
    get_available_counties,
    get_available_periods,
    filter_dataset
)
from agririsk.dashboard.charts import (
    plot_global_feature_importance,
    plot_local_feature_contributions,
    FEATURE_LABEL_MAP
)

st.set_page_config(
    page_title="Risk Drivers & Explainability - AgriRisk Kenya",
    page_icon="🔍",
    layout="wide"
)

# Research Disclaimer Banner
st.markdown(render_disclaimer_banner(), unsafe_allow_html=True)

st.title("🔍 Risk Drivers & Model Explainability")
st.markdown(
    "Understanding the environmental, biophysical, and economic signals influencing "
    "model risk probability estimates at both national and county levels."
)

# Load data and models
@st.cache_data
def get_dashboard_data():
    return load_scored_dataset()

@st.cache_resource
def get_model():
    return load_model_artifact()

df = get_dashboard_data()
models = get_model()

# Important Non-Causal Guidance Callout
st.warning(
    "⚠️ **CRITICAL NON-CAUSAL INTERPRETATION GUIDANCE:**\n\n"
    "Feature importance values and indicator breakdowns represent **statistical associations** "
    "learned from historical training data (2019–2022). They **do not prove causal mechanisms** or direct "
    "attribution. Acute food insecurity is driven by compounding humanitarian, geopolitical, "
    "market, and livelihood dynamics that cannot be fully captured by correlational statistical models alone."
)

tab_global, tab_local = st.tabs(["🌐 Global Feature Importance", "📍 Local County Risk Breakdown"])

with tab_global:
    st.subheader("Global Predictor Importance Across All ASAL Counties")
    st.markdown(
        "Relative contribution of each predictor in determining whether a county-month observation "
        "is classified into elevated acute food insecurity (IPC Phase 3+)."
    )

    # Extract feature importances from fitted Random Forest
    rf = models.rf
    feature_names = models.feature_names
    importances = rf.feature_importances_
    importance_dict = dict(zip(feature_names, importances))

    col_chart, col_table = st.columns([1.5, 1.0])

    with col_chart:
        fig_imp = plot_global_feature_importance(importance_dict)
        st.plotly_chart(fig_imp, use_container_width=True)

    with col_table:
        st.markdown("#### Feature Importance Weights")
        sorted_imp = sorted(
            [{"Feature": FEATURE_LABEL_MAP.get(k, k), "Code": k, "Weight": f"{v:.4f}"} for k, v in importance_dict.items()],
            key=lambda x: float(x["Weight"]),
            reverse=True
        )
        st.dataframe(pd.DataFrame(sorted_imp), use_container_width=True, hide_index=True)

    st.divider()

    st.subheader("💡 Key Insights from Global Model Analysis")
    st.markdown("""
    1. **Pre-Existing Vulnerability (`previous_ipc_phase`):** The prior food security phase acts as a strong temporal anchor, 
       capturing structural vulnerability and persistent livelihood depletion.
    2. **Multi-Month Cumulative Deficits (`rainfall_anomaly_3m`, `consecutive_dry_months`):** In ASAL pastoralist systems, 
       a single dry month rarely triggers a crisis; cumulative seasonal failure across 3+ consecutive months degrades pasture and browse.
    3. **Vegetation Decline (`ndvi_anomaly_3m`):** Sustained negative vegetative anomalies reflect biomass loss and forage depletion, 
       reducing livestock body condition and milk yields.
    4. **Market Pressure (`maize_price_zscore`):** Spikes in staple grain prices diminish terms-of-trade for pastoralists 
       who must sell more livestock at depressed prices to purchase expensive grain.
    """)

with tab_local:
    st.subheader("County & Month Specific Indicator Breakdown")
    st.markdown("Select a specific county and observation period to examine active risk indicators:")

    col_sel_c, col_sel_m = st.columns(2)
    with col_sel_c:
        selected_county = st.selectbox("Select County:", options=get_available_counties(df), key="local_c")
    with col_sel_m:
        selected_period = st.selectbox("Select Period:", options=get_available_periods(df), index=len(get_available_periods(df)) - 1, key="local_p")

    match = df[(df["county_name"] == selected_county) & (df["period"] == selected_period)]

    if match.empty:
        st.info("No observation recorded for this county and period.")
    else:
        row = match.iloc[0]
        risk_band = row["risk_band"]
        risk_prob = row["model_risk_prob"]

        col_badge, col_prob, col_ipc = st.columns(3)
        with col_badge:
            st.markdown(f"**Risk Classification:** {render_risk_badge(risk_band)}", unsafe_allow_html=True)
        with col_prob:
            st.metric("Model Risk Probability", f"{risk_prob * 100:.1f}%")
        with col_ipc:
            st.metric("Prior IPC Phase", f"Phase {int(row['previous_ipc_phase']) if pd.notnull(row['previous_ipc_phase']) else 'N/A'}")

        st.plotly_chart(plot_local_feature_contributions(row), use_container_width=True)

        st.markdown("#### Detailed Environmental & Market Indicators")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("1M Rain Anomaly", format_anomaly(row["rainfall_anomaly_1m"]))
        c1.metric("3M Rain Anomaly", format_anomaly(row["rainfall_anomaly_3m"]))
        c2.metric("Dry Spell Streak", f"{int(row['consecutive_dry_months'])} Months")
        c2.metric("3M Rolling Rain", f"{row['rainfall_rolling_3m']:.1f} mm" if pd.notnull(row['rainfall_rolling_3m']) else "N/A")
        c3.metric("1M NDVI Anomaly", format_anomaly(row["ndvi_anomaly_1m"]))
        c3.metric("3M NDVI Anomaly", format_anomaly(row["ndvi_anomaly_3m"]))
        c4.metric("Maize Price Z-Score", format_zscore(row["maize_price_zscore"]))
        c4.metric("3M Price Change", format_anomaly(row["maize_price_change_3m"]))
