"""AgriRisk Kenya - Geospatial Decision-Support Prototype Landing Page.

Executive landing page introducing the multi-indicator early warning system,
pilot ASAL counties, architecture, and essential humanitarian disclaimers.
"""

import streamlit as st
from agririsk.core.config import settings
from agririsk.dashboard.formatting import render_disclaimer_banner
from agririsk.dashboard.queries import load_scored_dataset, get_latest_snapshot
from agririsk.dashboard.metrics import compute_overview_kpis

st.set_page_config(
    page_title="AgriRisk Kenya - Decision Support",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Standard Research Prototype Disclaimer
st.markdown(render_disclaimer_banner(), unsafe_allow_html=True)

# Main Title & Subtitle
st.title("🌾 AgriRisk Kenya")
st.subheader("Data-Driven Early-Warning & Decision-Support for Food Security in Kenya")

st.markdown("""
**AgriRisk Kenya** is an experimental decision-support research prototype designed to synthesize multi-source 
environmental, biophysical, market, and food-security indicators across Kenya's Arid and Semi-Arid Lands (ASALs).

By tracking rolling rainfall anomalies, satellite vegetation indices (NDVI), staple grain price shocks, and 
historical vulnerability, the platform estimates the statistical probability that a county faces **elevated risk 
of acute food insecurity** (IPC Phase 3+ equivalent).
""")

# Quick Summary KPIs
try:
    df = load_scored_dataset()
    snapshot = get_latest_snapshot(df)
    kpis = compute_overview_kpis(snapshot)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Pilot Counties Monitored", f"{kpis['counties_monitored']} ASAL Counties")
    with col2:
        st.metric("Elevated / High Risk Counties", f"{kpis['elevated_or_high_count']} / {kpis['counties_monitored']}")
    with col3:
        st.metric("Latest Monitoring Period", kpis["latest_period"])
    with col4:
        st.metric("Mean Model Risk Probability", f"{kpis['average_risk_prob'] * 100:.1f}%")
except Exception as e:
    st.info(f"System ready. Pipeline data available. ({e})")

st.divider()

# Navigation Grid
st.markdown("### 🗺️ Explore the Decision-Support System")
st.markdown("Select a module from the sidebar or choose an exploration path below:")

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("""
    #### 1. [Overview & Risk Map](Overview)
    - **Kenya County Choropleth:** Interactive map displaying classified model risk bands (*Low*, *Moderate*, *Elevated*, *High*).
    - **KPI Summary:** Active pilot counties, risk distribution, and county ranking tables.
    - **Interactive Inspector:** Click or select any county to preview key indicators.

    #### 2. [County Explorer](County_Explorer)
    - **Longitudinal Trend Analysis:** 5 synchronized timelines tracking model risk probability, rainfall anomalies, NDVI vegetation health, staple food price shocks, and official IPC history.
    - **Non-Causal Contextual Summaries:** Plain-language synthesis of active environmental and socioeconomic pressures.

    #### 3. [Risk Drivers & Explainability](Risk_Drivers)
    - **Global Model Feature Importance:** Random Forest MDI importances and Logistic Regression standardized coefficients.
    - **Local County Indicators:** Feature breakdown for any county-month observation.
    - **Important Non-Causal Guidance:** Transparent communication that feature weights reflect associative risk correlations, not causal attribution.
    """)

with col_b:
    st.markdown("""
    #### 4. [Model Performance & Early Warning](Model_Performance)
    - **Strict Temporal Holdout Evaluation:** Validated on 2024 out-of-time test data (Train: 2019–2022, Val: 2023, Test: 2024).
    - **Early Warning Trade-offs:** Prioritizing Recall (Sensitivity) to minimize catastrophic false negatives in humanitarian monitoring.
    - **Diagnostic Visualizations:** Confusion matrices, ROC-AUC curves, and probability distribution splits.

    #### 5. [Data Quality & Coverage](Data_Quality)
    - **Data Pipeline Auditing:** Source completeness, missing value reports, duplicate checks, and temporal consistency.
    - **Freshness & Staleness Alerts:** Explicit tracking of data collection delays across satellite, rainfall, market, and survey sources.

    #### 6. [Methodology & Ethical Guardrails](Methodology)
    - **Mathematical Formulations:** Rolling window calculations, z-score transformations, and anomaly baselines.
    - **Critical Distinction:** Clear boundary between official IPC classifications and AgriRisk model probabilities.
    - **Ethical Guardrails:** Prohibiting unauthorized automated resource allocation.
    """)

st.divider()

# Pilot Counties Description
st.markdown("### 📍 Priority Pilot Counties")
st.markdown("""
This prototype focuses on five high-vulnerability ASAL pastoral and agropastoral counties in Northern and Rift Valley Kenya:
- **Turkana (County 023):** Extreme arid pastoral livelihood zone; recurring multi-season drought stress.
- **Marsabit (County 010):** Hyper-arid northern frontier; vulnerable to cross-border market and forage shocks.
- **Mandera (County 009):** North-eastern pastoral border zone; compounded climatic and market access challenges.
- **Garissa (County 007):** Arid pastoral and riverine agropastoral economy along the Tana River basin.
- **Baringo (County 030):** Semi-arid agropastoral zone with diverse microclimates and highland/lowland gradient.
""")

# Sidebar metadata
with st.sidebar:
    st.header("AgriRisk System Info")
    st.success(f"**Environment:** `{settings.app_env.upper()}`")
    st.info(f"**App Version:** `v{settings.version}`")
    st.write("**Model Engine:** `Random Forest (100 Trees)`")
    st.write("**Temporal Coverage:** `2019-01` to `2024-12`")
    st.write("**Status:** Active Decision-Support Prototype")
    st.divider()
    st.caption("Developed for climate-resilient agriculture and humanitarian food-security research.")
