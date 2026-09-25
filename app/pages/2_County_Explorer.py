"""County Explorer Page - Longitudinal Multi-Indicator Analysis."""

import streamlit as st
import pandas as pd
from agririsk.dashboard.formatting import (
    render_disclaimer_banner,
    render_risk_badge,
    generate_non_causal_interpretation,
    format_anomaly,
    format_zscore
)
from agririsk.dashboard.queries import (
    load_scored_dataset,
    get_available_counties,
    get_available_periods,
    filter_dataset
)
from agririsk.dashboard.charts import (
    plot_risk_probability_timeline,
    plot_rainfall_anomaly_timeline,
    plot_ndvi_anomaly_timeline,
    plot_market_price_timeline,
    plot_ipc_classification_timeline
)

st.set_page_config(
    page_title="County Explorer - AgriRisk Kenya",
    page_icon="📈",
    layout="wide"
)

# Research Disclaimer Banner
st.markdown(render_disclaimer_banner(), unsafe_allow_html=True)

st.title("📈 County Risk Explorer")
st.markdown(
    "Explore longitudinal trajectories of climate anomalies, vegetation stress, food prices, "
    "and model-estimated acute food insecurity risk for individual ASAL counties."
)

@st.cache_data
def get_dashboard_data():
    return load_scored_dataset()

df = get_dashboard_data()
all_counties = get_available_counties(df)
all_periods = get_available_periods(df)

# Top Filter Bar
col_c, col_d1, col_d2 = st.columns([1.5, 1.2, 1.2])

with col_c:
    selected_county = st.selectbox(
        "Select County:",
        options=all_counties,
        index=0,
        help="Select a pilot ASAL county to view multi-indicator time series."
    )

with col_d1:
    start_period = st.selectbox(
        "Start Period:",
        options=all_periods,
        index=0
    )

with col_d2:
    end_period = st.selectbox(
        "End Period:",
        options=all_periods,
        index=len(all_periods) - 1
    )

# Filter dataset
filtered_df = filter_dataset(df, county=selected_county, start_period=start_period, end_period=end_period)

if filtered_df.empty:
    st.warning("No data points available for the selected filters.")
    st.stop()

latest_row = filtered_df.iloc[-1]
risk_band = latest_row["risk_band"]
risk_prob = latest_row["model_risk_prob"]

# Status Banner Card
st.markdown(
    f"""
    <div style="background: linear-gradient(90deg, #f1f5f9 0%, #e2e8f0 100%); border-radius: 8px; padding: 14px 20px; margin: 15px 0; display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h3 style="margin: 0; color: #0f172a;">{selected_county} County — Current Status ({latest_row['period']})</h3>
            <p style="margin: 4px 0 0 0; color: #475569; font-size: 0.95rem;">
                Model Estimated Risk: <strong>{risk_prob * 100:.1f}%</strong> | 
                Prior IPC Benchmark: <strong>Phase {int(latest_row['previous_ipc_phase']) if pd.notnull(latest_row['previous_ipc_phase']) else 'N/A'}</strong> |
                Rainfall Anomaly (3M): <strong>{format_anomaly(latest_row['rainfall_anomaly_3m'])}</strong> |
                Price Z-Score: <strong>{format_zscore(latest_row['maize_price_zscore'])}</strong>
            </p>
        </div>
        <div>
            {render_risk_badge(risk_band)}
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# 1. Model Risk Probability Timeline
st.plotly_chart(
    plot_risk_probability_timeline(filtered_df, selected_county),
    use_container_width=True
)

st.divider()

# 2. Climate & Vegetation Timelines side by side
col_rain, col_ndvi = st.columns(2)

with col_rain:
    st.plotly_chart(
        plot_rainfall_anomaly_timeline(filtered_df, selected_county),
        use_container_width=True
    )

with col_ndvi:
    st.plotly_chart(
        plot_ndvi_anomaly_timeline(filtered_df, selected_county),
        use_container_width=True
    )

# 3. Market & IPC Timelines side by side
col_mkt, col_ipc = st.columns(2)

with col_mkt:
    st.plotly_chart(
        plot_market_price_timeline(filtered_df, selected_county),
        use_container_width=True
    )

with col_ipc:
    st.plotly_chart(
        plot_ipc_classification_timeline(filtered_df, selected_county),
        use_container_width=True
    )

st.divider()

# Non-Causal Contextual Interpretation Panel
st.subheader("📝 Contextual Indicator Synthesis")

interpretation_text = generate_non_causal_interpretation(
    county_name=selected_county,
    period=str(latest_row["period"]),
    risk_band=risk_band,
    risk_prob=risk_prob,
    indicators=latest_row.to_dict()
)

st.markdown(interpretation_text)
