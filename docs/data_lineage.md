# AgriRisk Kenya: End-to-End Data Lineage & Provenance

This document maps the complete data lifecycle of AgriRisk Kenya—from upstream provider raw data extraction to operational early-warning risk visualizations on the decision-support dashboard.

---

## 1. End-to-End Data Lineage Flow

```mermaid
flowchart TD
    subgraph Sources["1. Upstream Data Sources"]
        S_CHIRPS["CHIRPS Precipitation (UCSB CHG)"]
        S_MODIS["MODIS NDVI (NASA LP DAAC)"]
        S_RATIN["Market Wholesale Prices (RATIN / EAGC)"]
        S_IPC["IPC Food Insecurity (IPC Info Portal)"]
        S_GEO["Kenya County Boundaries (HDX / GADM)"]
    end

    subgraph RawVault["2. Versioned Raw Data Ingestion (Immutable)"]
        R_CHIRPS["data/raw/climate/YYYYMMDD_chirps_monthly.csv<br/>SHA-256 Checksum"]
        R_MODIS["data/raw/vegetation/YYYYMMDD_modis_ndvi.csv<br/>SHA-256 Checksum"]
        R_RATIN["data/raw/market/YYYYMMDD_market_prices.csv<br/>SHA-256 Checksum"]
        R_IPC["data/raw/ipc/YYYYMMDD_ipc_classifications.csv<br/>SHA-256 Checksum"]
        R_MANIFEST["data/manifest.json<br/>Operational Asset Register"]
    end

    subgraph Harmonization["3. Standardization & Geographic Normalization"]
        V_DRIFT["Drift & Schema Validation<br/>(agririsk.validation.drift_detector)"]
        V_GEO["Canonical County Registry<br/>(agririsk.geospatial.reference)"]
        T_NORM["Unit Harmonization & Currency Normalization<br/>(KES / 90kg Bag)"]
    end

    subgraph FeatureStore["4. Feature Engineering & Historical Datasets"]
        F_PANEL["Monthly County Panel Merge<br/>(2019-01 to 2024-12)"]
        F_LAG["Lagged Predictors & Rolling Windows<br/>(1m, 2m, 3m Lags; 3m Rolling Rainfall/NDVI)"]
        F_MODEL["data/processed/model_dataset.csv<br/>(360 County-Months)"]
        F_FCST["data/processed/forecast_dataset.csv<br/>(1,080 Multi-Horizon Observations)"]
    end

    subgraph Modeling["5. Model Training & Evaluation"]
        M_BASE["Baseline Classifiers<br/>(Logistic Regression, Random Forest)"]
        M_CALIB["Multi-Horizon Forecasters (t+1, t+2, t+3)<br/>Isotonic/Platt Probability Calibration"]
        M_ART["artifacts/models/<br/>forecast_model_h1..h3.joblib"]
    end

    subgraph DecisionSupport["6. Decision-Support Delivery"]
        UI_DASH["Interactive Streamlit Dashboard<br/>(app/Home.py & Pages)"]
        UI_API["FastAPI REST Endpoints<br/>(/api/v1/forecast, /api/v1/health)"]
        R_REPORTS["reports/data_quality/latest.json<br/>reports/pipeline/run_*.json"]
    end

    %% Connectors
    S_CHIRPS --> R_CHIRPS
    S_MODIS --> R_MODIS
    S_RATIN --> R_RATIN
    S_IPC --> R_IPC
    S_GEO --> V_GEO

    R_CHIRPS --> R_MANIFEST
    R_MODIS --> R_MANIFEST
    R_RATIN --> R_MANIFEST
    R_IPC --> R_MANIFEST

    R_CHIRPS --> V_DRIFT
    R_MODIS --> V_DRIFT
    R_RATIN --> V_DRIFT
    R_IPC --> V_DRIFT

    V_DRIFT --> V_GEO
    V_GEO --> T_NORM
    T_NORM --> F_PANEL
    F_PANEL --> F_LAG
    F_LAG --> F_MODEL
    F_MODEL --> F_FCST

    F_MODEL --> M_BASE
    F_FCST --> M_CALIB
    M_CALIB --> M_ART

    M_ART --> UI_DASH
    M_ART --> UI_API
    F_FCST --> UI_DASH
    R_MANIFEST --> R_REPORTS
    R_REPORTS --> UI_DASH
```

---

## 2. Transformation Stages & Invariants

| Stage | Input Assets | Processing Module | Output Assets | Quality & Integrity Guarantees |
|---|---|---|---|---|
| **1. Ingestion** | Remote HTTP/FTP/API or local cached fallbacks | `agririsk.ingestion.base` | `data/raw/<domain>/YYYYMMDD_<name>.csv` | Checksum verification; timestamped immutable storage; no synthetic replacement |
| **2. Provenance Tracking** | Ingested raw files | `agririsk.ingestion.manifest` | `data/manifest.json` | SHA-256 fingerprinting; deduplication; staleness monitoring against update cadence |
| **3. Validation & Harmonization** | Raw dataframes & County Registry | `agririsk.validation.drift_detector`, `agririsk.geospatial.reference` | Standardized in-memory DataFrames | Schema validation; bounds checking; strict 47-county canonical alias resolution |
| **4. Feature Engineering** | Harmonized dataframes | `agririsk.features.engineering` | `data/processed/model_dataset.csv` | Cross-domain panel joins (county-month); zero future leakage; temporal alignment |
| **5. Forecast Preparation** | Model dataset | `agririsk.forecasting.features` | `data/processed/forecast_dataset.csv` | Multi-horizon projection ($t+1, t+2, t+3$); historical vulnerability anchoring |
| **6. Model Training** | Processed datasets | `agririsk.forecasting.models` | `artifacts/models/*.joblib` | Rolling-origin time-aware cross-validation; Brier calibration; F1 threshold optimization |
| **7. Serving & Visualization** | Trained models & Forecast data | `app/Home.py`, `app/pages/*` | Interactive decision-support views | Disclaimers enforced; distinct model probability vs official IPC; dynamic fresh/stale audits |

---

## 3. Data Integrity & Reproducibility Principles

1. **Raw Immutability**: Files under `data/raw/` are write-once and versioned by timestamp prefix (`YYYYMMDD_*`). Ingestion never overwrites existing raw data in-place.
2. **Deterministic Fingerprinting**: Every ingested asset computes a SHA-256 digest. Identical files are identified to prevent redundant feature rebuilding.
3. **No Silent Synthetic Imputation**: If an upstream data provider experiences downtime or API failures, the pipeline logs the failure, falls back to the most recent valid raw cache, and tags the dataset as `Warning (Stale)` or `Cached Fallback` in `data/manifest.json` and `reports/data_quality/latest.json`.
4. **Zero Look-Ahead Leakage**: All rolling calculations (3-month rainfall sums, NDVI anomalies, price inflation indices) and lagged predictors rely strictly on data available at period $t \le T_0$ for forecasting targets at $T_0 + h$.
5. **Strict Geographic Verification**: Any spelling variation (e.g., *Elegeyo-Marakwet*, *Tharaka Nithi*) is resolved through `CountyReferenceRegistry`. Unmatched jurisdictions cause automated audit flags and are never dropped silently.
