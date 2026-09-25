# Model Card: AgriRisk Kenya Food-Security Risk Forecasting Framework

## 1. Model Details
- **Model Name**: AgriRisk Kenya Multi-Horizon Early-Warning Forecaster
- **Version**: v0.2.0 (Milestone 6 Research Benchmark)
- **Model Architecture**: Balanced Random Forest, HistGradientBoostingClassifier, Logistic Regression, and Calibrated Committee Ensemble.
- **Lead Horizons**: 1-month ($t+1$), 2-month ($t+2$), and 3-month ($t+3$) ahead projections.
- **Maintainers**: AgriRisk Kenya Open Research Team
- **Date**: September 2026

## 2. Intended Use & Scope
- **Intended Use**: Research-oriented early-warning decision support for identifying elevated probabilities of acute food insecurity (IPC Phase 3+ equivalent) across Kenya's Arid and Semi-Arid Lands (ASALs).
- **Intended Users**: Humanitarian analysts, agro-meteorologists, early warning task forces, and academic researchers evaluating multi-source anticipatory action.
- **Out-of-Scope / Non-Intended Use**:
  - Must **NOT** be used as official humanitarian warnings or legal famine declarations.
  - Must **NOT** replace formal field-based assessments conducted by the Kenya Food Security Steering Group (KFSSG) or the Integrated Food Security Phase Classification (IPC) Global Support Unit.
  - Must **NOT** be utilized for autonomous food aid allocation without ground validation.

## 3. Training & Validation Data
- **Spatial Coverage**: 5 pilot ASAL rangeland counties (Turkana, Marsabit, Mandera, Garissa, Baringo).
- **Temporal Range**: January 2019 to December 2024 (72 continuous monthly time-steps per county; 360 county-months).
- **Input Feeds**:
  - Satellite Precipitation: CHIRPS monthly rainfall totals ($mm$) and rolling percentage anomalies.
  - Satellite Vegetation: MODIS 250m 16-day composite NDVI and 3m/6m trajectory trends.
  - Market Dynamics: RATIN wholesale white maize prices (standardized to KES/90kg bag) and historical z-scores.
  - Prior Vulnerability: Preceding IPC acute food insecurity phase classifications ($1$ to $5$).
  - Spatial Neighbourhood: Contiguity- and centroid distance-weighted neighbour rainfall, vegetation, and price shocks.
- **Validation Methodology**: Expanding-window rolling-origin temporal backtesting (Fold 1: Train $\le 2022$, Val 2023; Fold 2: Train $\le 2023$, Test 2024 holdout).

## 4. Evaluation Metrics & Performance Summary
Evaluation emphasizes early-warning sensitivity (**Recall** and **False Negative Rate**) to avoid missed humanitarian alarms:
- **Horizon 1 ($t+1$, 2024 Holdout)**:
  - Random Forest: Recall = **0.8333** (95% CI: 0.60–1.00), F1 = **0.7692** (95% CI: 0.55–0.92), PR-AUC = **0.7500**, Brier Score = **0.1250**.
  - Simple Baselines: Persistence (Recall = 0.5833, F1 = 0.5385), Seasonal (Recall = 0.5000, F1 = 0.4615).
- **Horizon Degradation**: Recall remains high at 1M and 2M (0.8333) before moderating at 3M (0.6667) as meteorological lead time decays.

## 5. Explainability & Ethical Considerations
- **Non-Causal Interpretation**: Predictor importances (e.g. via permutation importance) represent **statistical associations** with the target distribution. The model does not assert physical, macroeconomic, or clinical causation.
- **Feature Hierarchy**: `previous_ipc_phase` is the primary anchor of risk, while local precipitation deficits (`rainfall_anomaly_lag1`), prolonged dry spells, and grain price z-scores provide incremental sensitivity.
- **Geographic Disparity**: Pastoral rangeland counties (Turkana, Marsabit) demonstrate higher model sensitivity than agropastoral rangelands (Baringo), where livelihood diversification buffers against drought.
- **Uncertainty Bounds**: Model outputs provide empirical epistemic uncertainty bounds (`[lower, upper]`), reflecting model committee dispersion rather than formal humanitarian population confidence intervals.
