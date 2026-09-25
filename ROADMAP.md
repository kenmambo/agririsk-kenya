# AgriRisk Kenya: Project Roadmap & Research Horizons

**Current Status:** Research Prototype (Milestone 7 Completed)  
**Maintained by:** Kenneth Mambo & Open-Source Contributors  
**Last Updated:** September 2026  

---

## 1. Current State: What is Completed (Milestones 1–7)

- [x] **Milestone 1:** Production repository architecture, Pydantic schemas, SQLite/FastAPI endpoints, Streamlit skeleton, unit test suite.
- [x] **Milestone 2:** Multi-source data ingestion pipelines, canonical county name standardization, feature engineering, baseline classification, evaluation metrics.
- [x] **Milestone 3:** Interactive multi-page Streamlit GIS dashboard, Kenya county choropleth risk map, longitudinal timelines, data freshness audit.
- [x] **Milestone 4:** Short-horizon food security risk forecasting (1M, 2M, 3M ahead), expanding-origin backtesting, Platt probability calibration, reliability curves.
- [x] **Milestone 5:** Automated reproducible data ingestion, source registry (`config/data_sources.yaml`), immutable raw storage, manifest checksum tracking, schema drift detection.
- [x] **Milestone 6:** Research-grade benchmarking against simple baselines (Persistence, Historical Frequency, Seasonal), Queen contiguity spatial features, feature group ablation studies, 300-iteration block bootstrap 95% CIs, geographic equity audits, Model Card, and Dataset Card.
- [x] **Milestone 7:** Public-facing portfolio packaging, technical report, case study, CV project entries, interview Q&As, demo mode, and open-source documentation.

---

## 2. Phase 1: Near-Term Enhancements (Q4 2026 – Q1 2027)

### 2.1 Geographic Expansion to All 23 ASAL Counties
- Scale the longitudinal panel from the current 5 pilot ASAL counties across all 23 official ASAL counties (including Garissa, Mandera, Isiolo, Kitui, Tana River, and Kajiado).
- Re-fit Queen contiguity spatial lag matrices and verify regional cross-border migration corridors across northern and eastern borders.

### 2.2 Sub-County (Admin-2) Spatial Disaggregation
- Downscale analysis from County (Admin-1) level to Sub-County (Admin-2) units (e.g., Turkana North, Turkana Central, Turkana West).
- Address spatial masking where vast arid counties conceal severe localized micro-climate crises.

### 2.3 Automated Ingestion Scheduling
- Implement automated cron or GitHub Actions workflows to poll UCSB CHIRPS pentads and NASA MODIS 16-day composites as new granules are published.
- Automated anomaly generation and schema drift alerting.

---

## 3. Phase 2: Methodological & Algorithmic Innovations (Q2 – Q3 2027)

### 3.1 High-Resolution Sentinel-2 Biophysical Indices
- Ingest 10-meter European Space Agency (ESA) Sentinel-2 optical imagery to compute localized crop-vigor and pasture-fraction indices, distinguishing palatable perennial grasses from invasive *Prosopis juliflora*.

### 3.2 Armed Conflict & Market Blockade Integration
- Ingest Armed Conflict Location & Event Data (ACLED) for Kenya to quantify banditry, cattle-rustling incidents, and road interdictions.
- Engineer spatial conflict density features to capture non-climatic market isolation.

### 3.3 Spatio-Temporal Graph Neural Networks (ST-GCN)
- Transition from tabular spatial lag heuristics to deep Spatio-Temporal Graph Convolutional Networks (ST-GCN) or Graph Attention Networks (GAT) trained over the full 47-county Queen adjacency topology.

### 3.4 Conformal Prediction for Guaranteed Uncertainty Bounds
- Upgrade stationary block bootstrap intervals with Split Conformal Prediction, providing distribution-free coverage guarantees (e.g., exact finite-sample 90% confidence bands) on early warning probabilities.

---

## 4. Phase 3: Institutional Pilot & Field Validation (Q4 2027+)

### 4.1 NDMA Technical Shadow Pilot
- Deploy AgriRisk Kenya in a non-operational "shadow evaluation mode" alongside the National Drought Management Authority's monthly bulletin cycle to benchmark early warning leads against real-world field observations.

### 4.2 Multi-Stakeholder KFSSG Engagement
- Conduct consultative workshops with the Kenya Food Security Steering Group (KFSSG), World Food Programme (WFP Kenya), and FEWS NET to align predictive feature definitions with operational Long Rains and Short Rains assessment criteria.

### 4.3 Low-Bandwidth Alerting Prototypes
- Prototype low-bandwidth USSD or SMS alerting pipelines for sub-county agricultural extension officers and pastoralist rangeland associations.
