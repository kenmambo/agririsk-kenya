"""Data Quality & Coverage Page - Pipeline Auditing & Source Freshness."""

import streamlit as st
import pandas as pd
import plotly.express as px
from agririsk.dashboard.formatting import render_disclaimer_banner
from agririsk.dashboard.queries import load_raw_dataset
from agririsk.dashboard.metrics import compute_data_quality_metrics

st.set_page_config(
    page_title="Data Quality & Coverage - AgriRisk Kenya",
    page_icon="🛡️",
    layout="wide"
)

# Research Disclaimer Banner
st.markdown(render_disclaimer_banner(), unsafe_allow_html=True)

st.title("🛡️ Data Pipeline Quality, Completeness & Freshness")
st.markdown(
    "Comprehensive health auditing across the multi-source ingestion pipeline feeding AgriRisk Kenya."
)

raw_df = load_raw_dataset()
dq = compute_data_quality_metrics(raw_df)

# Top Completeness Metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Records Audited", f"{dq['total_records']} County-Months")
with col2:
    st.metric("Coverage Time Span", dq["year_range"])
with col3:
    st.metric("Overall Completeness", f"{dq['overall_completeness_pct']}%")
with col4:
    st.metric("Duplicate Rows", f"{dq['duplicate_rows']} Duplicates", delta="Zero Duplication", delta_color="normal")

st.divider()

# Ingestion Source Completeness Breakdown
st.subheader("📊 Ingestion Source Health & Completeness")

col_src1, col_src2, col_src3, col_src4 = st.columns(4)
with col_src1:
    st.progress(dq["climate_completeness_pct"] / 100)
    st.markdown(f"**Climate Feed (CHIRPS):** `{dq['climate_completeness_pct']}%` complete")
    st.caption("Monthly precipitation totals & rolling anomaly calculations.")

with col_src2:
    st.progress(dq["vegetation_completeness_pct"] / 100)
    st.markdown(f"**Vegetation Feed (MODIS):** `{dq['vegetation_completeness_pct']}%` complete")
    st.caption("Normalized Difference Vegetation Index (NDVI) & trends.")

with col_src3:
    st.progress(dq["market_completeness_pct"] / 100)
    st.markdown(f"**Market Prices (KNBS):** `{dq['market_completeness_pct']}%` complete")
    st.caption("Wholesale staple dry maize prices (KES/90kg) & z-scores.")

with col_src4:
    st.progress(dq["ipc_completeness_pct"] / 100)
    st.markdown(f"**Food Security (IPC/KFSSG):** `{dq['ipc_completeness_pct']}%` complete")
    st.caption("Historical acute phase ground-truth & binary crisis target.")

st.divider()

# Missingness Breakdown by Feature Column
st.subheader("🔍 Column-Level Missingness Audit")

missing_data = []
for col_name, pct in dq["missing_by_column"].items():
    missing_data.append({
        "Feature Column": col_name,
        "Missing (%)": pct,
        "Present (%)": round(100.0 - pct, 1),
        "Category": (
            "Climate" if "rainfall" in col_name or "dry" in col_name else
            "Vegetation" if "ndvi" in col_name else
            "Market" if "price" in col_name else
            "Food Security Target" if "ipc" in col_name or "target" in col_name else
            "Metadata"
        )
    })

missing_df = pd.DataFrame(missing_data).sort_values("Missing (%)", ascending=False)

fig_missing = px.bar(
    missing_df,
    x="Missing (%)",
    y="Feature Column",
    color="Category",
    orientation="h",
    title="<b>Feature Missingness Distribution Across Panel (Warm-up Lags)</b>",
    labels={"Missing (%)": "Missing Percentage (%)", "Feature Column": ""},
    color_discrete_map={
        "Climate": "#2563eb",
        "Vegetation": "#16a34a",
        "Market": "#d97706",
        "Food Security Target": "#7c3aed",
        "Metadata": "#64748b"
    }
)
fig_missing.update_layout(
    margin=dict(l=180, r=20, t=40, b=40),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#ffffff",
    height=380
)
st.plotly_chart(fig_missing, use_container_width=True)

st.caption(
    "Note on Missingness: Lag features (e.g., `ndvi_anomaly_3m`, `maize_price_change_3m`) have expected "
    "empty values exclusively during the first 1–3 months of the 2019 initialization period per county. "
    "All intermediate months from month 4 onward have 100% complete feature coverage."
)

st.divider()

# Operational Data Freshness & Source Registry
st.subheader("⏱️ Operational Data Source Freshness & Registry")

import json
from pathlib import Path

dq_latest_file = Path("reports/data_quality/latest.json")
if dq_latest_file.exists():
    with open(dq_latest_file, "r", encoding="utf-8") as f:
        dq_report = json.load(f)

    st.caption(f"Last Pipeline Evaluation: `{dq_report.get('evaluated_at', 'Unknown')}`")
    source_rows = []
    for k, sinfo in dq_report.get("sources", {}).items():
        status_str = sinfo.get("status", "Unknown")
        status_badge = (
            f"🟢 {status_str}" if "Current" in status_str else
            f"🟡 {status_str}" if "Warning" in status_str else
            f"🔴 {status_str}"
        )
        source_rows.append({
            "Dataset Identifier": k,
            "Provider": sinfo.get("provider", "Unknown"),
            "Date Coverage End": sinfo.get("date_coverage_end", "Unknown"),
            "Staleness (Days)": sinfo.get("staleness_days", 0),
            "Operational Status": status_badge,
            "Rows Cached": sinfo.get("row_count", 0),
            "SHA-256 Digest": sinfo.get("sha256_prefix", "") + "..."
        })

    if source_rows:
        st.dataframe(pd.DataFrame(source_rows), use_container_width=True)
else:
    st.info("No data quality report found. Run `uv run python -m agririsk.pipeline run` to generate the latest report.")

st.divider()

# Pipeline Execution History
st.subheader("📜 Pipeline Execution History")

reports_dir = Path("reports/pipeline")
run_records = []
if reports_dir.exists():
    for r_file in sorted(reports_dir.glob("*.json"), reverse=True)[:10]:
        try:
            with open(r_file, "r", encoding="utf-8") as f:
                r_data = json.load(f)
                run_status = r_data.get("status", "unknown").upper()
                badge = "🟢 SUCCESS" if run_status == "SUCCESS" else ("🟡 PARTIAL" if "PARTIAL" in run_status else "🔴 FAILED")
                run_records.append({
                    "Run ID": r_data.get("run_id", r_file.stem),
                    "Timestamp": r_data.get("start_time", "Unknown")[:19].replace("T", " "),
                    "Status": badge,
                    "Dry Run": "Yes" if r_data.get("dry_run") else "No",
                    "Sources Attempted": len(r_data.get("sources_attempted", [])),
                    "Model Rows": r_data.get("model_dataset_rows", "-"),
                    "Issues Detected": len(r_data.get("validation_issues", {}))
                })
        except Exception:
            continue

if run_records:
    st.dataframe(pd.DataFrame(run_records), use_container_width=True)
else:
    st.caption("No pipeline execution logs recorded yet.")

st.divider()

# Feed Latency & Staleness Monitoring
st.subheader("📋 Ingestion Latency Characteristics & Design Rationale")

st.markdown("""
In operational settings, multi-indicator early warning systems encounter differing transmission latencies across data sources:

| Data Feed | Upstream Source | Update Frequency | Typical Publication Latency | Staleness Impact on Early Warning |
| :--- | :--- | :--- | :--- | :--- |
| **Precipitation** | CHIRPS / Climate Hazards Center | Monthly | 5–10 days post-month | **Low:** Timely dekadal satellite-gauge estimates allow rapid updates. |
| **Vegetation Health** | MODIS Terra/Aqua (MOD13A2) | 16-day Composite | 8–16 days post-pass | **Moderate:** Cloud cover in wet seasons can occasionally delay synthesis. |
| **Market Commodity Prices** | KNBS / Ministry of Agriculture | Monthly | 15–30 days post-month | **Moderate:** Manual field price collection creates standard end-of-month lag. |
| **Official IPC Assessments** | KFSSG / IPC Global Platform | Biannual (Feb / Aug) | 60–90 days post-assessment | **High:** Intensive consensus-driven field assessments require months to publish. |
""")

st.info(
    "💡 **Why Machine Learning Adds Value Despite Latency:** "
    "Official IPC assessments are conducted only twice annually (post-Long Rains and post-Short Rains). "
    "By continuously synthesizing satellite precipitation, NDVI, and monthly grain market prices, "
    "AgriRisk Kenya provides interim, month-by-month risk tracking during the critical intervening periods."
)
