"""AgriRisk Kenya - Streamlit Decision-Support Prototype Landing Page.

Milestone 1: Project Scaffolding & County Overview.
"""

from typing import List, Dict, Any
import streamlit as st
import pandas as pd
import plotly.express as px
from agririsk.core.constants import KENYA_COUNTIES
from agririsk.core.config import settings

# Page setup
st.set_page_config(
    page_title="AgriRisk Kenya - Milestone 1",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Prominent Research Disclaimer
st.warning(
    "⚠️ **RESEARCH & DECISION-SUPPORT PROTOTYPE ONLY**\n\n"
    "AgriRisk Kenya is an exploratory research platform. "
    "Outputs from this platform **DO NOT** constitute official Integrated Food Security Phase Classification (IPC) "
    "classifications or National Drought Management Authority (NDMA) early warning bulletins. "
    "This system must **NOT** be used for operational humanitarian aid allocation."
)

# Header
st.title("🌾 AgriRisk Kenya")
st.markdown(
    "### Early-Warning & Decision-Support Prototype for Climate-Resilient Agriculture\n"
    "*Milestone 1: Core Foundation, County Geospatial Mapping & Service Architecture*"
)

# Sidebar metadata
with st.sidebar:
    st.header("System Status")
    st.success(f"**Environment:** `{settings.app_env}`")
    st.info(f"**Version:** `{settings.version}`")
    st.write(f"**Database:** `{settings.database.url.split('///')[-1]}`")

    st.divider()
    st.subheader("Filter Counties")
    selected_asal: List[str] = st.multiselect(
        "ASAL Ecological Category",
        options=["Arid", "Semi-Arid", "Non-ASAL"],
        default=["Arid", "Semi-Arid", "Non-ASAL"],
        help="Arid: Extreme drought vulnerability (~85-100% arid); Semi-Arid: Mixed agropastoral; Non-ASAL: High agricultural potential."
    )

# Metrics bar
counties_df = pd.DataFrame(KENYA_COUNTIES)
filtered_df = counties_df[counties_df["asal_category"].isin(selected_asal)]

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Counties", len(KENYA_COUNTIES))
with col2:
    arid_count = sum(1 for c in KENYA_COUNTIES if c["asal_category"] == "Arid")
    st.metric("Arid (Pastoral / High Risk)", arid_count)
with col3:
    semi_arid_count = sum(1 for c in KENYA_COUNTIES if c["asal_category"] == "Semi-Arid")
    st.metric("Semi-Arid (Agropastoral)", semi_arid_count)
with col4:
    non_asal_count = sum(1 for c in KENYA_COUNTIES if c["asal_category"] == "Non-ASAL")
    st.metric("Non-ASAL (High Potential)", non_asal_count)

st.divider()

# Interactive Plotly Geospatial Map
st.subheader("Geographical Distribution: Kenya's 47 Counties")

if not filtered_df.empty:
    fig = px.scatter_geo(
        filtered_df,
        lat="lat",
        lon="lon",
        hover_name="name",
        hover_data={"code": True, "asal_category": True, "lat": False, "lon": False},
        color="asal_category",
        color_discrete_map={
            "Arid": "#d62728",
            "Semi-Arid": "#ff7f0e",
            "Non-ASAL": "#2ca02c"
        },
        category_orders={"asal_category": ["Arid", "Semi-Arid", "Non-ASAL"]},
        size_max=12,
        scope="africa",
        title="County Centroids & Ecological Vulnerability Categories (WGS84)"
    )

    fig.update_geos(
        center=dict(lat=0.5, lon=37.8),
        projection_scale=16,
        showcountries=True,
        showcoastlines=True,
        showland=True,
        landcolor="#f8f9fa",
        countrycolor="#cccccc"
    )
    fig.update_layout(height=480, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No counties match the current filter selection.")

# Navigation tabs
tab_catalog, tab_roadmap, tab_api = st.tabs(["County Catalog", "Project Roadmap", "API Integration"])

with tab_catalog:
    st.markdown(f"Displaying **{len(filtered_df)}** counties matching filter:")
    st.dataframe(
        filtered_df[["code", "name", "asal_category", "lat", "lon"]].rename(
            columns={
                "code": "County Code",
                "name": "County Name",
                "asal_category": "Ecological Category",
                "lat": "Latitude",
                "lon": "Longitude"
            }
        ),
        use_container_width=True,
        hide_index=True
    )

with tab_roadmap:
    st.markdown("""
    #### AgriRisk Kenya Incremental Roadmap
    - [x] **Milestone 1 (Current):** Repository scaffolding, YAML configuration, structured logging, SQLAlchemy SQLite database setup, County model & 47-county seeder, Pydantic schemas, FastAPI health & county endpoints, minimal Streamlit home page, and unit test suite.
    - [ ] **Milestone 2:** Ingestion pipelines for Climate (CHIRPS precipitation & ERA5 temperature), Vegetation (MODIS/Sentinel NDVI & VCI), Wholesale Market Prices, and IPC ground truth benchmarks.
    - [ ] **Milestone 3:** Harmonization panel cleaner and feature engineering pipeline (temporal lags, rolling averages, and composite drought indices).
    - [ ] **Milestone 4:** Machine learning baseline interface (`BaseRiskModel`), heuristic early warning benchmark, and Random Forest classifier with evaluation metrics.
    - [ ] **Milestone 5:** Decision-support early-warning dashboard with interactive county drill-downs and what-if climate shock simulation.
    """)

with tab_api:
    st.markdown("""
    #### FastAPI Service Integration
    The backend service exposes standardized REST endpoints:
    - `GET /health` & `GET /api/v1/health`: Service health and database connectivity check.
    - `GET /api/v1/counties`: Retrieve all 47 counties with optional `?asal_category=` filtering.
    - `GET /api/v1/counties/{code}`: Retrieve individual county metadata.
    
    Interactive documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
    """)

st.caption("AgriRisk Kenya Platform • Built with Python 3.12, GeoPandas, SQLAlchemy, FastAPI, and Streamlit.")
