# AgriRisk Kenya: Climate-Resilient Agriculture & Food Security Decision Support

[![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Package Manager](https://img.shields.io/badge/uv-managed-purple.svg)](https://github.com/astral-sh/uv)
[![Code Style](https://img.shields.io/badge/code%20style-production--quality-green.svg)](https://docs.astral.sh/uv/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

> **⚠️ RESEARCH & DECISION-SUPPORT PROTOTYPE ONLY**  
> AgriRisk Kenya is an exploratory data science and software engineering prototype developed for methodology research and architecture demonstration. Model outputs and synthetic benchmark fixtures **DO NOT** constitute official Integrated Food Security Phase Classification (IPC) classifications, National Drought Management Authority (NDMA) bulletins, or government early-warning alerts. This prototype must **NOT** be used for operational humanitarian aid allocation or policy deployment without exhaustive empirical ground-truthing and institutional sign-off.

---

## 1. Development Problem

Kenya faces acute vulnerability to climate variability and extreme weather shocks. Over 80% of Kenya's landmass is categorized as **Arid and Semi-Arid Lands (ASALs)**, sustaining pastoral and agropastoral communities whose livelihoods rely directly on bimodal rainfall cycles:
- **Long Rains:** March – May (MAM)
- **Short Rains:** October – December (OND)

In recent years, the Horn of Africa has experienced unprecedented climatic volatility: consecutive failed rainy seasons leading to catastrophic pasture depletion, crop failure, livestock mortality, and staple-food price surges, followed abruptly by severe El Niño floods. 

Humanitarian response and agricultural mitigation often suffer from **reaction latency**—interventions mobilize only after acute malnutrition or harvest failure is widespread. Building predictive, multi-source early warning mechanisms provides an empirical basis for **anticipatory action**, enabling regional governments, agronomists, and aid agencies to prepare before food security crises peak.

---

## 2. Project Objective & Milestone Status

**AgriRisk Kenya** creates a modular, production-grade early-warning decision-support architecture.

### Milestone Progress
- [x] **Milestone 1:** Production repository scaffolding, YAML configuration, structured logging, SQLite database setup, County model & 47-county seeder, Pydantic schemas, FastAPI health & county catalog endpoints, Streamlit geospatial landing page, and unit test suite.
- [x] **Milestone 2:** Multi-source data ingestion pipelines, county name standardizer, feature engineering pipeline, data validator, reproducible modeling dataset (`data/processed/model_dataset.csv`), time-aware baseline modeling (Logistic Regression & Random Forest), evaluation metrics emphasizing Recall and False Negative diagnostics, visual report figures, and comprehensive documentation (`docs/`).
- [x] **Milestone 3:** Interactive multi-page geospatial decision-support dashboard in Streamlit (`app/Home.py` and 6 specialized pages), Kenya county choropleth risk map, longitudinal multi-indicator timelines, explainability & non-causal attribution panels, data quality & latency audit, and 63 unit tests.
- [x] **Milestone 4:** Short-horizon food-security risk forecasting (1M, 2M, and 3M ahead), lagged climate/vegetation/market/IPC predictors, expanding-window rolling-origin backtesting, recall-prioritized threshold tuning, Platt probability calibration, multi-horizon metrics and reliability curves, early-warning dashboard (`app/pages/7_Forecast.py`), and 73 unit tests.
- [x] **Milestone 5:** Automated data ingestion, data source registry (`config/data_sources.yaml`), raw file immutability, operational manifest (`data/manifest.json`), schema drift detection (`agririsk.validation.drift_detector`), canonical county reference registry (`agririsk.geospatial.reference`), end-to-end pipeline orchestrator (`agririsk.pipeline`), Docker containerization (`Dockerfile`, `docker-compose.yml`), task runner (`Makefile`), dynamic dashboard freshness audit, and 82 unit tests.

---

## 3. Pilot ASAL Counties (Milestone 2)

Milestone 2 focuses on five high-vulnerability pilot ASAL counties across Kenya's pastoral and agropastoral rangelands:
1. **Turkana** (Code: `023` | Arid | Northwestern pastoral)
2. **Marsabit** (Code: `010` | Arid | Northern pastoral)
3. **Mandera** (Code: `009` | Arid | Northeastern pastoral borderland)
4. **Garissa** (Code: `007` | Arid | Eastern pastoral)
5. **Baringo** (Code: `030` | Semi-Arid | Rift Valley agropastoral)

---

## 4. System Architecture

The platform adheres to a decoupled **`src`-layout**, strictly separating data ingestion, validation, processing, feature engineering, machine learning modeling, geospatial mapping, and user presentation.

```
                           +----------------------------------------+
                           |          Pilot Raw Data Feeds          |
                           |   (IPC, CHIRPS, MODIS NDVI, Markets)   |
                           +----------------------------------------+
                                               |
                                               v
+---------------------------------------------------------------------------------------+
| Ingestion & Normalization Layer (`agririsk.ingestion`)                                |
| - `CountyStandardizer`: Normalizes aliases/spelling variants to official Kenya names   |
| - Domain Ingestors: `IPCIngestor`, `ClimateIngestor`, `VegetationIngestor`, `Market`  |
+---------------------------------------------------------------------------------------+
                                               |
                                               v
+---------------------------------------------------------------------------------------+
| Feature Engineering Pipeline (`agririsk.features.FeatureEngineer`)                    |
| - Strictly grouped by county to eliminate cross-county leakage                        |
| - Lags (1m, 3m), 3m rolling rainfall, consecutive dry months                          |
| - NDVI anomalies and 3m trend; Maize price 1m/3m changes and price z-score            |
| - Derived Binary Target: `target_phase3plus` (1 if IPC Phase >= 3 else 0)             |
+---------------------------------------------------------------------------------------+
                                               |
                                               v
+---------------------------------------------------------------------------------------+
| Data Quality & Boundary Validator (`agririsk.validation.DataValidator`)              |
| - Rejects duplicates, impossible dates, missing counties, invalid phases, extremes   |
| - Outputs: `data/processed/model_dataset.csv` (360 county-month panel records)        |
+---------------------------------------------------------------------------------------+
                                               |
                                               v
+---------------------------------------------------------------------------------------+
| Time-Aware Baseline Modeling (`agririsk.modeling`)                                    |
| - Forward-chaining chronological split (Train: 2019-2022, Val: 2023, Test: 2024)       |
| - Baseline Classifiers: Balanced Logistic Regression & Balanced Random Forest         |
| - Diagnostics: Recall, Precision, F1, ROC-AUC, False Negative Rate (FNR)              |
| - Outputs: `reports/model_results/` & `reports/figures/`                              |
+---------------------------------------------------------------------------------------+
                        |                                       |
                        v                                       v
+-----------------------------------+   +-----------------------------------------------+
| FastAPI Service (`/api/v1`)       |   | Streamlit Decision-Support UI (`streamlit`)   |
| - `/health` & `/api/v1/health`    |   | - 47 County Geospatial Vulnerability Map      |
| - `/api/v1/counties`              |   | - Early Warning Indicators & Filtering        |
| - Interactive Swagger Docs        |   | - Transparent Methodological Disclaimers      |
+-----------------------------------+   +-----------------------------------------------+
```

---

## 5. Milestone 2 Baseline Modeling Results

### Test Set Evaluation (Holdout Year: 2024)
Chronological split: **Train (2019–2022: 225 rows)** $\to$ **Validation (2023: 60 rows)** $\to$ **Test (2024: 60 rows)**.

| Metric | Logistic Regression (Balanced) | Random Forest (Balanced) | Priority in Early Warning |
| :--- | :---: | :---: | :--- |
| **Recall (Sensitivity)** | 0.0000 | **1.0000** | **Highest** (Captures true crisis events) |
| **Precision** | 0.0000 | **0.7500** | Moderate (Tolerates precautionary monitoring) |
| **F1 Score** | 0.0000 | **0.8571** | High (Harmonic mean) |
| **ROC-AUC** | 0.9236 | **0.9575** | High (Threshold-independent discriminative power) |
| **False Negative Rate (FNR)** | 1.0000 (Missed 12/12) | **0.0000 (Missed 0/12)** | **Critical** (Goal is FNR $\to 0$) |

### Early Warning Diagnostic Discussion
- **The Criticality of Recall and False Negatives**: In famine and drought early warning, a **False Negative** (failing to sound the alarm on an unfolding Phase 3+ crisis) costs lives and exhausts coping capacities. Conversely, a **False Positive** merely prompts ground verification and heightened monitoring.
- **Model Comparison**:
  - While **Logistic Regression** achieved a strong ranking capacity ($\text{ROC-AUC} = 0.9236$), under the standard default decision cutoff ($p = 0.5$) its calibrated probabilities hovered between 0.35 and 0.48 due to post-2023 El Niño shifts, missing all 12 crisis county-months in 2024.
  - **Random Forest** successfully captured non-linear threshold effects between consecutive dry months, pasture forage depletion (`ndvi_anomaly_3m`), and market price spikes, achieving **100% Recall** with **0 False Negatives** on the out-of-sample test horizon.

### Generated Artifacts & Visualizations
- Detailed metrics JSON: [`reports/model_results/baseline_metrics.json`](file:///c:/Users/kexma/code/AgriRiskKenya/reports/model_results/baseline_metrics.json)
- Confusion Matrix: [`reports/figures/confusion_matrix.png`](file:///c:/Users/kexma/code/AgriRiskKenya/reports/figures/confusion_matrix.png)
- Feature Importance: [`reports/figures/feature_importance.png`](file:///c:/Users/kexma/code/AgriRiskKenya/reports/figures/feature_importance.png)
- Risk Probability Distribution: [`reports/figures/risk_probability_distribution.png`](file:///c:/Users/kexma/code/AgriRiskKenya/reports/figures/risk_probability_distribution.png)

---

## 6. Documentation Reference

- **[Data Dictionary](file:///c:/Users/kexma/code/AgriRiskKenya/docs/data_dictionary.md)**: Column specifications, data types, physical measurement units, and formulas.
- **[Data Lineage & Provenance](file:///c:/Users/kexma/code/AgriRiskKenya/docs/data_lineage.md)**: End-to-end data lifecycle, Mermaid architecture flow, and integrity invariants.
- **[Data Sources Specification](file:///c:/Users/kexma/code/AgriRiskKenya/docs/data_sources.md)**: Provider attribution, update cadences, staleness thresholds, and licensing.
- **[Methodology Specification](file:///c:/Users/kexma/code/AgriRiskKenya/docs/methodology.md)**: Time-aware validation design, feature mathematics, and recall optimization rationale.
- **[Limitations & Ethical Guardrails](file:///c:/Users/kexma/code/AgriRiskKenya/docs/limitations.md)**: Known sensor constraints, spatial aggregation issues, and humanitarian disclaimer.
- **[Multi-Horizon Forecasting Methodology](file:///c:/Users/kexma/code/AgriRiskKenya/docs/forecasting.md)**: Forward target definition, rolling-origin backtesting, threshold tuning, Platt calibration, and early-warning matrix.

---

## 7. Execution Guide

### Prerequisites
- Python 3.12
- [`uv`](https://github.com/astral-sh/uv) package manager
- Docker & Docker Compose (optional for containerized deployment)

### Automated Pipeline Execution
```bash
# Execute the full automated pipeline (ingest, validate, feature store, train)
uv run python -m agririsk.pipeline run

# Target specific steps or sources
uv run python -m agririsk.pipeline run --step validate --dry-run
uv run python -m agririsk.pipeline run --source rainfall --force-refresh
```

### Make / Task Runner
```bash
make setup      # Install dependencies via uv
make ingest     # Ingest external sources to raw versioned storage
make validate   # Check schemas and detect data drift
make features   # Build model_dataset.csv and forecast_dataset.csv
make train      # Train baseline and multi-horizon models
make dashboard  # Launch Streamlit decision-support dashboard
make test       # Run 82 unit and integration tests with pytest
```

### Docker Execution
```bash
# Build and launch dashboard service
docker compose up dashboard

# Run the data pipeline container
docker compose run --rm pipeline
```

### Step-by-Step Manual Commands
```bash
# 1. Install all dependencies using uv
uv sync && uv pip install -e .

# 2. Setup SQLite database and seed 47 Kenya counties
uv run python scripts/setup_db.py

# 3. Ingest data and rebuild feature store via orchestrator
uv run python -m agririsk.pipeline run

# 4. Run the complete pytest test suite (82 unit tests)
uv run pytest

# 5. Start the FastAPI backend
uv run uvicorn agririsk.api.main:app --host 127.0.0.1 --port 8000 --reload

# 6. Launch the interactive multi-page Decision-Support Dashboard
uv run streamlit run app/Home.py
```
