# Data Science Project Card: AgriRisk Kenya

**Schema Version:** 1.0  
**Project Name:** AgriRisk Kenya  
**Live Demo:** [agririsk-kenya.streamlit.app](https://agririsk-kenya.streamlit.app)  
**Repository:** [github.com/kenmambo/agririsk-kenya](https://github.com/kenmambo/agririsk-kenya)  
**Technical Report:** [reports/technical_report.md](../reports/technical_report.md)  
**Primary Author:** Kenneth Mambo  
**Status:** Completed Research Prototype (Milestone 8 Deployment Ready)  

---

## 1. Project Overview & Scope
- **Problem Domain:** Agricultural Early Warning, Climate-Induced Food Insecurity, Anticipatory Humanitarian Action.
- **Geographic Focus:** Kenya's Arid and Semi-Arid Lands (ASALs), with 47-county geospatial adjacency and 5 pilot ASAL panel backtests (Turkana, Marsabit, Samburu, Wajir, Baringo).
- **Target Users:** Humanitarian program planners (WFP, NDMA, KFSSG, Red Cross), agricultural economists, research scholars, and disaster risk financing analysts.
- **Intended Use:** Inter-census early warning decision support across 1- to 3-month forecasting horizons ($t+1, t+2, t+3$).
- **Out-of-Scope Use:** Autonomous algorithmic aid distribution, official gazetted early warning alerts, replacement of consensus-based IPC assessments.

---

## 2. Machine Learning Architecture
- **Problem Formulation:** Direct multi-horizon binary classification of acute crisis state ($\mathbb{I}(IPC \ge 3)$).
- **Primary Model:** Balanced Random Forest Classifier (100 estimators, max depth 8, class-weighted, Platt calibrated).
- **Benchmark Suite:** Operational Persistence Heuristic, Historical County Frequency Baseline, Seasonal Monthly Climatology Baseline, Calibrated Logistic Regression (L2).
- **Backtesting Protocol:** Expanding-origin temporal cross-validation with an out-of-time test fold (calendar year 2024; 60 county-months).
- **Calibration Engine:** Platt sigmoid probability calibration optimizing Brier reliability scores.
- **Uncertainty Quantification:** 300-iteration stationary block bootstrapping generating 95% empirical confidence intervals.

---

## 3. Data & Feature Specifications
- **Longitudinal Scope:** 13 years (2012–2024; 780 county-months).
- **Feature Dimensionality:** 35 engineered indicators per county-month.
- **Input Feeds:**
  - *Precipitation:* CHIRPS v2.0 pentads (0.05° resolution).
  - *Vegetation:* MODIS 250m 16-day composite NDVI / VCI.
  - *Markets:* WFP VAM retail and wholesale maize transaction prices ($KES/kg$).
  - *Prior State:* Historical IPC acute food insecurity phase classifications.
  - *Spatial Contiguity:* First-order Queen adjacency graph across 47 Kenyan counties with distance-decay spatial lags.

---

## 4. Validated Performance Summary (2024 Holdout Year)
- **1-Month Horizon ($t+1$):**
  - **Recall:** 0.8333 (95% CI: $[0.6000, 1.0000]$) vs. 0.5833 (Persistence).
  - **F1-Score:** 0.7692 vs. 0.5385 (Persistence).
  - **PR-AUC:** 0.7500 vs. 0.3000 (Persistence).
  - **ROC-AUC:** 0.9575 vs. 0.6750 (Persistence).
  - **Brier Score:** 0.1250 vs. 0.4167 (Persistence) — **70.0% Error Reduction**.
- **Lead-Time Degradation:**
  - $h=1$ (1 Month): Recall = 0.8333, F1 = 0.7692, Brier = 0.1250
  - $h=2$ (2 Months): Recall = 0.8333, F1 = 0.7143, Brier = 0.1438
  - $h=3$ (3 Months): Recall = 0.6667, F1 = 0.6154, Brier = 0.1654

---

## 5. Software Stack & Reproducibility
- **Programming Language:** Python 3.12.
- **Package Manager:** `uv` with locked transitive dependency resolution (`uv.lock`).
- **Data & Geospatial Stack:** Scikit-Learn, Pandas, NumPy, GeoPandas, Shapely, Folium.
- **Delivery Frameworks:** Streamlit (Multi-Page UI), FastAPI (REST microservice), Docker & Docker-Compose.
- **Testing & Quality:** Pytest (90 automated tests passing), Pydantic v2 schema validation.
- **Licensing:** MIT License for source code; third-party data subject to source attribution terms.
