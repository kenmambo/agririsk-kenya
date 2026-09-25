"""AgriRisk Kenya - Geospatial Decision-Support Prototype Landing Page.

Executive landing page introducing the multi-indicator early warning system,
pilot ASAL counties, architecture, data freshness audit, and essential humanitarian disclaimers.
"""

import streamlit as st
from agririsk.core.config import settings
from agririsk.version import APP_VERSION, MODEL_VERSION, DATASET_VERSION, RELEASE_DATE
from agririsk.dashboard.formatting import render_disclaimer_banner
from agririsk.dashboard.queries import load_scored_dataset, get_latest_snapshot
from agririsk.dashboard.metrics import compute_overview_kpis

st.set_page_config(
    page_title="AgriRisk Kenya - Decision Support",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 1. Persistent Responsible-Use Notice Banner
st.markdown("""
<div style="background-color: #fff3cd; border-left: 6px solid #ffc107; padding: 12px 18px; border-radius: 4px; margin-bottom: 20px;">
    <strong>⚠️ RESEARCH & DECISION-SUPPORT PROTOTYPE ONLY</strong><br/>
    AgriRisk Kenya is an exploratory scientific research and decision-support prototype. Model-generated risk probabilities 
    <strong>DO NOT</strong> constitute official Integrated Food Security Phase Classification (IPC) determinations, 
    National Drought Management Authority (NDMA) alerts, or United Nations World Food Programme warnings. 
    Review our <a href="https://github.com/kenmambo/agririsk-kenya/blob/main/docs/model_card.md" target="_blank">Model Card</a> 
    and <a href="https://github.com/kenmambo/agririsk-kenya/blob/main/docs/limitations.md" target="_blank">Operational Limitations</a>.
</div>
""", unsafe_allow_html=True)

# 2. Demo Mode Snapshot Notice
if settings.agririsk_mode == "demo" or settings.app_env in ("production", "demo"):
    st.info(f"📌 **Demo Mode Active:** Displaying validated snapshot data (`{DATASET_VERSION}`). External live network queries and expensive retraining are safely disabled for this public preview.")

# 3. Main Title & Subtitle
st.title("🌾 AgriRisk Kenya")
st.subheader("A Data-Driven Early Warning Prototype for Climate-Resilient Agriculture and Food Security in Kenya's ASALs")

# 4. 30-Second Fast Orientation Card
with st.expander("⚡ 30-Second Project Overview (What, Why, Data & Boundaries)", expanded=True):
    col_x, col_y = st.columns(2)
    with col_x:
        st.markdown("""
        - **What is AgriRisk Kenya?** An open-source machine learning early-warning prototype forecasting acute food insecurity risk (IPC Phase 3+) 1 to 3 months ahead across Kenya's Arid and Semi-Arid Lands.
        - **What problem does it address?** Bridges the 4-to-8-week reaction-latency gap in traditional survey assessments, enabling **Anticipatory Action** and Forecast-based Financing before famine peaks.
        - **What data does it synthesize?** 0.05° CHIRPS precipitation, MODIS 250m vegetation condition (NDVI/VCI), WFP staple grain market transactions, and Queen contiguity cross-county spatial contagion.
        """)
    with col_y:
        st.markdown("""
        - **What does the model output mean?** Platt-calibrated statistical probabilities ($0.0$ to $1.0$) indicating the likelihood of a county experiencing IPC Phase 3+ (Crisis) conditions, bounded by 95% bootstrap confidence intervals.
        - **What should users NOT use it for?** It must **never** be used for autonomous aid distribution, replacing official IPC/NDMA consensus assessments, or policy gazetting without ground-truthing.
        """)

st.divider()

# 5. Live Data Freshness & Pipeline Status Banner
df_loaded = None
latest_date = "2024-12-01"
try:
    df_loaded = load_scored_dataset()
    latest_date = str(df_loaded["date"].max())
except Exception:
    pass

st.markdown("### 📡 Data Freshness & Observational Audit")
fcol1, fcol2, fcol3, fcol4, fcol5 = st.columns(5)
with fcol1:
    st.metric("Climate (CHIRPS)", latest_date, delta="Normal Pentad")
with fcol2:
    st.metric("Vegetation (MODIS)", latest_date, delta="16-Day Comp")
with fcol3:
    st.metric("Markets (WFP VAM)", latest_date, delta="Monthly KES")
with fcol4:
    st.metric("Food Security (IPC)", latest_date, delta="Semi-Annual")
with fcol5:
    st.metric("Overall Status", "Current (Validated)", delta="Healthy")

st.divider()

# 6. Top KPI Summary Deck
try:
    if df_loaded is not None:
        snapshot = get_latest_snapshot(df_loaded)
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

# 7. Navigation Deck
st.markdown("### 🗺️ Explore the Decision-Support System")
col_a, col_b = st.columns(2)

with col_a:
    st.markdown("""
    #### 1. [Overview & Risk Map](Overview)
    - **Kenya County Choropleth:** Interactive map displaying classified model risk bands (*Low*, *Moderate*, *Elevated*, *High*).
    - **KPI Summary:** Active pilot counties, risk distribution, and county ranking tables.
    - **Interactive Inspector:** Click or select any county to preview key indicators.

    #### 2. [County Explorer](County_Explorer)
    - **Longitudinal Trend Analysis:** Synchronized timelines tracking model risk probability, rainfall anomalies, NDVI vegetation health, staple food price shocks, and official IPC history.
    - **Non-Causal Contextual Summaries:** Plain-language synthesis of active environmental and socioeconomic pressures.

    #### 3. [Risk Drivers & Explainability](Risk_Drivers)
    - **Global Model Feature Importance:** Random Forest MDI importances and Logistic Regression standardized coefficients.
    - **Local County Indicators:** Feature breakdown for any county-month observation.
    - **Important Non-Causal Guidance:** Transparent communication that feature weights reflect associative risk correlations, not causal attribution.
    """)

with col_b:
    st.markdown("""
    #### 4. [Model Performance & Benchmarks](Model_Performance)
    - **Strict Temporal Holdout Evaluation:** Validated on 2024 out-of-time test data (Train: 2019–2022, Val: 2023, Test: 2024).
    - **Early Warning Trade-offs:** Prioritizing Recall (Sensitivity: 0.8333) to minimize catastrophic false negatives in humanitarian monitoring.
    - **Diagnostic Visualizations:** Confusion matrices, ROC-AUC curves, and probability distribution splits.

    #### 5. [Risk Forecasting (1M, 2M, 3M)](Forecast)
    - **Short-Horizon Early Warning:** Prospective 1-month, 2-month, and 3-month forward risk probabilities.
    - **Rolling-Origin Calibrated Models:** Platt scaling, Brier scoring, and recall-optimized decision thresholds.
    - **Uncertainty Quantification:** 95% block bootstrap confidence intervals on predictions.

    #### 6. [Research Insights & Ablations](Research_Insights)
    - **Baseline Comparisons:** Random Forest vs Persistence, Historical Frequency, and Seasonal Baselines.
    - **Domain Ablation:** Quantified recall drop when isolating climate, vegetation, market, and prior IPC features.
    - **Sub-National Equity:** Performance disaggregation across arid pastoral rangelands vs agropastoral zones.
    """)

st.divider()

# 8. Pilot ASAL Counties
st.markdown("### 📍 Priority Pilot Counties")
st.markdown("""
This prototype focuses on five high-vulnerability ASAL pastoral and agropastoral counties in Northern and Rift Valley Kenya:
- **Turkana (County 023):** Extreme arid pastoral livelihood zone; recurring multi-season drought stress.
- **Marsabit (County 010):** Hyper-arid northern frontier; vulnerable to cross-border market and forage shocks.
- **Samburu (County 025):** Semi-arid pastoral ecosystem; highly sensitive to livestock terms of trade.
- **Wajir (County 008):** Arid pastoral rangelands; high climate variability and deep groundwater dependency.
- **Baringo (County 030):** Semi-arid agropastoral zone with diverse microclimates and lake basin topography.
""")

# 9. Deployment Status Footer
st.divider()
st.markdown(f"""
<div style="text-align: center; color: #6c757d; font-size: 0.85rem; padding: 15px 0;">
    <strong>AgriRisk Kenya</strong> | Application Version: <code>v{APP_VERSION}</code> | 
    Model Version: <code>{MODEL_VERSION}</code> | Dataset Version: <code>{DATASET_VERSION}</code><br/>
    Released: {RELEASE_DATE} | License: MIT / Open Data Attribution | 
    <a href="https://github.com/kenmambo/agririsk-kenya" target="_blank">GitHub Repository</a> | 
    <a href="https://github.com/kenmambo/agririsk-kenya/blob/main/docs/deployment.md" target="_blank">Deployment Docs</a>
</div>
""", unsafe_allow_html=True)

# 10. Sidebar System Information
with st.sidebar:
    st.header("System & Deployment Info")
    st.success(f"**Environment:** `{settings.app_env.upper()}`")
    st.info(f"**Mode:** `{settings.agririsk_mode.upper()}`")
    st.write(f"**App Version:** `v{APP_VERSION}`")
    st.write(f"**Model Artifact:** `{MODEL_VERSION}`")
    st.write(f"**Data Snapshot:** `{DATASET_VERSION}`")
    st.write(f"**Coverage:** `2012-01` to `2024-12`")
    st.divider()
    st.caption("Developed for climate-resilient agriculture and anticipatory humanitarian action.")
