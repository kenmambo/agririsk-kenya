# AgriRisk Kenya: Climate-Resilient Agriculture & Food Security Decision Support

[![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Package Manager](https://img.shields.io/badge/uv-managed-purple.svg)](https://github.com/astral-sh/uv)
[![Code Style](https://img.shields.io/badge/code%20style-production--quality-green.svg)](https://docs.astral.sh/uv/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

> **⚠️ RESEARCH & DECISION-SUPPORT PROTOTYPE ONLY**  
> AgriRisk Kenya is an exploratory data science and software engineering prototype developed for methodology research and architecture demonstration. Model outputs and synthetic benchmark fixtures **DO NOT** constitute official Integrated Food Security Phase Classification (IPC) classifications, National Drought Management Authority (NDMA) bulletins, or government early-warning alerts. This prototype must **NOT** be used for operational humanitarian aid allocation or policy deployment without exhaustive empirical ground-truthing and institutional sign-off.

---

## 1. Development Problem

Kenya faces acute vulnerability to climate variability and extreme weather shocks. Over 80% of Kenya's landmass is categorized as **Arid and Semi-Arid Lands (ASALs)**, sustaining pastoral and agropastoral communities whose livelihoods rely directly on the bimodal rainfall cycles:
- **Long Rains:** March – May (MAM)
- **Short Rains:** October – December (OND)

In recent years, the Horn of Africa has experienced unprecedented climatic volatility: consecutive failed rainy seasons leading to catastrophic pasture depletion, crop failure, livestock mortality, and staple-food price surges, followed abruptly by severe El Niño floods. 

Humanitarian response and agricultural mitigation often suffer from **reaction latency**—interventions mobilize only after acute malnutrition or harvest failure is widespread. Building predictive, multi-source early warning mechanisms provides an empirical basis for **anticipatory action**, enabling regional governments, agronomists, and aid agencies to prepare before food security crises peak.

---

## 2. Project Objective

**AgriRisk Kenya** creates a modular, production-grade early-warning decision-support architecture. By ingesting and harmonizing multi-domain indicators across climate, satellite vegetation health, wholesale food markets, and baseline socioeconomic vulnerability, the platform aims to:
1. Provide county-level monthly risk indexing and IPC phase estimation across all 47 counties of Kenya.
2. Provide transparent, explainable feature indicators (e.g., rainfall anomaly lags, 3-month VCI trends, staple-food price shocks).
3. Offer decoupled APIs (FastAPI) and an intuitive decision-maker dashboard (Streamlit & Plotly) for interactive what-if exploration.

---

## 3. System Architecture

The platform adheres to a decoupled **`src`-layout**, strictly separating data ingestion, validation, processing, feature engineering, machine learning modeling, geospatial mapping, and user presentation.

```
                           +----------------------------------------+
                           |           Planned Data Feeds           |
                           | (CHIRPS, MODIS/NDVI, WFP/KNBS, NDMA)   |
                           +----------------------------------------+
                                               |
                                               v
+---------------------------------------------------------------------------------------+
| Ingestion & Schema Validation Layer (Pydantic & BaseIngestor)                         |
| - Boundary checking (e.g., rainfall >= 0, NDVI in [-0.2, 1.0], VCI in [0, 100])       |
| - Provenance tracking (`is_synthetic`, `data_source`)                                |
+---------------------------------------------------------------------------------------+
                                               |
                                               v
+---------------------------------------------------------------------------------------+
| Storage & Harmonization Panel (SQLAlchemy + SQLite / PostgreSQL)                      |
| - Tables: counties, climate_obs, vegetation_obs, market_obs, ipc_obs, model_features  |
| - Panel Alignment: Monthly (YYYY-MM-01) indexed by `county_code`                     |
+---------------------------------------------------------------------------------------+
                                               |
                                               v
+---------------------------------------------------------------------------------------+
| Feature Engineering Pipeline (`FeatureEngineer`)                                      |
| - Temporal Lags: 1m, 3m precipitation lags, 1m VCI lag                                |
| - Rolling Statistics: 3m precipitation rolling average, 6m maize price percent change |
| - Domain Indices: Composite Drought Index, Price Surge Index                          |
+---------------------------------------------------------------------------------------+
                                               |
                                               v
+---------------------------------------------------------------------------------------+
| Modeling & Evaluation Layer (`BaseRiskModel`)                                         |
| - Benchmark 1: Transparent Domain Heuristic Model                                     |
| - Benchmark 2: Scikit-Learn Ensemble Classifier (Random Forest)                       |
| - Evaluation: Macro F1, Precision, Recall, Confusion Matrix                           |
+---------------------------------------------------------------------------------------+
                        |                                       |
                        v                                       v
+-----------------------------------+   +-----------------------------------------------+
| FastAPI Service (`/api/v1`)       |   | Streamlit Decision-Support UI (`streamlit`)   |
| - `/health`                       |   | - 47 County Geospatial Vulnerability Map      |
| - `/api/v1/health`                |   | - Early Warning Indicators & Filtering        |
| - REST endpoints for predictions  |   | - Transparent Methodological Disclaimers      |
+-----------------------------------+   +-----------------------------------------------+
```

---

## 4. Repository Structure

```text
AgriRiskKenya/
├── .env.example                     # Environment template
├── .gitignore                       # Standard ignore rules (SQLite, virtualenv, caches)
├── .python-version                  # Pins Python 3.12 for uv
├── pyproject.toml                   # Project metadata and dependencies managed via uv
├── README.md                        # Documentation and architecture specification
├── config/
│   ├── base.yaml                    # Global base parameters (paths, CRS, seed)
│   ├── development.yaml             # Development settings
│   └── test.yaml                    # Test environment configuration (in-memory SQLite)
├── data/
│   ├── raw/                         # Raw ingested data snapshots (gitignored)
│   ├── processed/                   # Harmonized analytical panel datasets
│   ├── fixtures/                    # Clearly labeled synthetic fixtures for test suites
│   └── agririsk.db                  # Local SQLite database instance (gitignored)
├── artifacts/
│   └── models/                      # Serialized model checkpoints (.joblib)
├── scripts/
│   └── seed_db.py                   # CLI tool to initialize DB and seed county records
├── src/
│   └── agririsk/
│       ├── core/                    # Config (YAML+Pydantic), logging, DB models, constants
│       ├── ingestion/               # Ingestion contracts & synthetic fixture generators
│       ├── validation/              # Pydantic schemas enforcing domain value ranges
│       ├── processing/              # Cleaning, date normalization, stream harmonization
│       ├── features/                # Lag calculations, rolling metrics, drought indices
│       ├── modeling/                # BaseRiskModel, Random Forest baseline, evaluation
│       ├── geospatial/              # GeoPandas county boundaries & coordinate utilities
│       ├── api/                     # FastAPI application & health check routes
│       └── ui/                      # Streamlit interactive landing page & map
└── tests/
    ├── conftest.py                  # Pytest fixtures (in-memory DB, client, fixtures)
    └── unit/
        ├── test_config.py           # Configuration loading & overrides
        ├── test_database.py         # SQLAlchemy tables & constraint enforcement
        ├── test_validation.py       # Pydantic schema validation tests
        ├── test_geospatial.py       # GeoDataFrame & coordinate integrity
        ├── test_health_api.py       # FastAPI endpoint tests
        ├── test_processing_and_features.py # Stream harmonization & lag calculations
        └── test_models.py           # Model fit, predict, save, load, and metrics
```

---

## 5. Planned Real-World Data Sources

| Domain | Data Stream | Provider / Source | Cadence & Resolution |
| :--- | :--- | :--- | :--- |
| **Climate** | Rainfall / Precipitation | [CHIRPS](https://www.chc.ucsb.edu/data/chirps) (UCSB Climate Hazards Group) | Daily/Monthly, 0.05° (~5.3 km) |
| **Climate** | Surface Temperature | ERA5-Land (ECMWF) / NASA POWER | Monthly, 0.1° |
| **Vegetation** | NDVI & 3-month VCI | MODIS (MOD13Q1) / Sentinel-2 via Google Earth Engine | 16-day composite, 250 m |
| **Market** | Wholesale Maize & Bean Prices | WFP VAM (Vulnerability Analysis and Mapping) & KNBS | Monthly per county market |
| **Ground Truth**| Acute Food Insecurity Phase | FEWS NET / Kenya IPC Technical Working Group (NDMA) | Bi-annual / seasonal assessment |

---

## 6. Modelling Approach & Baselines

To uphold scientific integrity and avoid "black-box" overconfidence:
1. **Rule-Based Heuristic Benchmark (`BaselineHeuristicModel`):**
   - Implements established humanitarian rule thresholds combining 3-month precipitation deficit and localized price surge.
   - Provides an interpretable floor against which machine learning models are evaluated.
2. **Supervised Classifier (`BaselineRiskClassifier`):**
   - Scikit-learn Random Forest Classifier trained on temporal lag features, rolling statistics, and domain drought indices.
   - Outputs both categorical IPC phase predictions and probability distributions to reflect predictive uncertainty.
3. **Temporal Isolation:**
   - All rolling calculations and lags are grouped strictly by `county_code` to eliminate temporal data leakage.

---

## 7. Ethical Limitations & Responsible Humanitarian AI

1. **No Operational Mandate:** This system is an academic and portfolio research prototype. It does not replace the statutory authority of the Government of Kenya, the Kenya Meteorological Department (KMD), or the National Drought Management Authority (NDMA).
2. **False Negative Risk:** In humanitarian decision support, a false negative (predicting "Phase 1 - Minimal" when a crisis is unfolding) carries severe human costs. Models must be calibrated for recall and high sensitivity in crisis states.
3. **Synthetic Data Transparency:** Where real live API feeds have not yet been integrated, all test and benchmark data are generated deterministically and explicitly flagged with `is_synthetic = True` and `data_source = "SYNTHETIC_BENCHMARK"`.

---

## 8. Getting Started

### Prerequisites
- Python 3.12
- [`uv`](https://github.com/astral-sh/uv) (Extremely fast Python package installer and resolver)

### 1. Installation
Clone the repository and synchronize dependencies using `uv`:
```bash
# Clone the repository
git clone https://github.com/your-username/AgriRiskKenya.git
cd AgriRiskKenya

# Synchronize virtual environment with Python 3.12 and all dependencies
uv sync
```

### 2. Environment Setup
Copy the environment template:
```bash
cp .env.example .env
```

### 3. Initialize & Seed Local SQLite Database
Seed reference metadata for all 47 counties and test fixtures:
```bash
uv run python scripts/seed_db.py
```

### 4. Run the Pytest Test Suite
Execute all unit tests across configuration, database, schemas, API, and models:
```bash
uv run pytest
```

### 5. Launch the FastAPI Backend
Start the REST API service:
```bash
uv run uvicorn agririsk.api.app:app --host 127.0.0.1 --port 8000 --reload
```
Access the interactive API documentation at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)  
Test health status at: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 6. Launch the Streamlit Decision-Support Dashboard
Start the interactive dashboard:
```bash
uv run streamlit run src/agririsk/ui/streamlit_app.py
```
Open your browser at: [http://localhost:8501](http://localhost:8501)
