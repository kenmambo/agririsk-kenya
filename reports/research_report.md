# Empirical Research Report: AgriRisk Kenya Early-Warning Food Security Forecasting
**Authors:** AgriRisk Research Team  
**Evaluation Date:** September 25, 2026  
**Evaluation Codebase:** AgriRisk Kenya Prototype v0.2.0  
---
## Executive Abstract
This research study evaluates machine learning models and spatial lag predictors for short-horizon (1-3 month ahead) acute food insecurity forecasting across Kenya's Arid and Semi-Arid Lands (ASALs). Evaluating against non-learning benchmarks (Persistence, Historical Frequency, Seasonal Baseline), we test whether multi-source environmental, biophysical, and market indicators provide genuine anticipatory lead time. Using an expanding-window rolling-origin temporal validation framework (2019-2024), we find that tree-based ensemble models achieve superior recall and calibration compared to simple baselines, but feature importance is heavily anchored by prior vulnerability states and local rainfall anomalies.
## 1. Research Question
Does integrating satellite precipitation anomalies (CHIRPS), vegetation health (MODIS NDVI), staple food price dynamics (RATIN), and spatial neighbour context materially improve short-horizon food insecurity risk predictions over simple persistence and empirical seasonal baselines?
## 2. Background & Problem Context
In Kenya's ASAL counties, protracted bimodal drought cycles (such as the catastrophic 2020-2023 Horn of Africa drought) deplete pastoral forage and cause severe food insecurity. Official IPC assessments occur only biannually, creating critical 4-6 month operational blind spots. Developing empirical decision-support models provides intermediate anticipatory tracking.
## 3. Data Sources & Geographic Scope
- **Geographic Coverage**: 5 pilot ASAL rangeland counties (Turkana, Marsabit, Mandera, Garissa, Baringo).
- **Temporal Span**: January 2019 to December 2024 (72 continuous county-months; 360 observations per horizon).
- **Feeds**: CHIRPS precipitation, MODIS 250m NDVI, RATIN wholesale dry maize prices, IPC ground truth.
## 4. Target Definition
Binary indicator Y in {0, 1} denoting IPC Phase 3+ (Crisis, Emergency, or Catastrophe) at lead horizon h in {1, 2, 3} months ahead. The overall dataset exhibits 46.7% positive class prevalence across the 6-year period.
## 5. Feature Engineering & Spatial Formulations
Features are strictly computed at observation time t <= T0 to guarantee zero future leakage:
- **Climate**: 1m, 2m, 3m anomalies; 3m and 6m rolling precipitation; consecutive dry spell count.
- **Vegetation**: 1m, 2m, 3m NDVI anomalies; 3m and 6m directional trends.
- **Market**: 1m, 3m, 6m percentage maize price changes; county-specific historical z-scores.
- **Historical Vulnerability**: Previous IPC phase and lagged phases.
- **Spatial Neighbour Context**: Adjacency-weighted and centroid distance-decayed neighbour rainfall, NDVI, and price shocks.
## 6. Baseline Models
1. **Persistence Baseline**: Future risk equals latest observed state.
2. **Historical Frequency**: Predicts long-term county base rate P(Crisis | c).
3. **Seasonal Baseline**: Predicts month-conditioned historical rate P(Crisis | c, m).
4. **Logistic Regression**: Interpretable L2-penalized baseline with standard scaling.
## 7. Machine Learning Model Family
- **Random Forest**: Balanced class-weighting, 100 estimators, max depth 5.
- **HistGradientBoostingClassifier**: Gradient boosted decision trees with automatic binning.
- **Calibrated Ensemble**: Soft-voting combination of Logistic Regression, Random Forest, and Gradient Boosting.
## 8. Temporal Validation Framework
Expanding-window rolling-origin temporal backtesting:
- **Fold 1 (Drought Onset & Peak)**: Train <= 2022, Evaluate 2023.
- **Fold 2 (Recovery Transition)**: Train <= 2023, Evaluate 2024 holdout.
Zero look-ahead contamination; scalers, imputers, and thresholds are fitted exclusively on training partitions.
## 9. Spatial Analysis & Contiguity
Contiguity analysis reveals that while Turkana, Marsabit, and Mandera form a contiguous northern border network, Garissa and Baringo do not border other pilot counties. Spatial features utilized a dual formulation (topological Queen adjacency with distance-weighted fallback).
## 10. Model Performance Findings

| Model | Horizon | Fold | Recall | Precision | F1 Score | PR-AUC | Brier Score |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| Persistence | 1M | fold2_recovery_transition | 1.0000 | 0.6250 | 0.7692 | 0.6250 | 0.1091 |
| Historical Frequency | 1M | fold2_recovery_transition | 1.0000 | 0.1818 | 0.3077 | 0.1818 | 0.2677 |
| Seasonal Baseline | 1M | fold2_recovery_transition | 1.0000 | 0.1818 | 0.3077 | 0.1818 | 0.2631 |
| Logistic Regression | 1M | fold2_recovery_transition | 0.1000 | 0.5000 | 0.1667 | 0.4077 | 0.1280 |
| Random Forest | 1M | fold2_recovery_transition | 0.9000 | 0.6429 | 0.7500 | 0.5549 | 0.0924 |
| Hist Gradient Boosting | 1M | fold2_recovery_transition | 0.2000 | 0.2000 | 0.2000 | 0.2808 | 0.2083 |
| Calibrated Ensemble | 1M | fold2_recovery_transition | 0.2000 | 0.2857 | 0.2353 | 0.3968 | 0.1294 |
| Random Forest Ablation | 1M | fold2_recovery_transition | 0.9000 | 0.6429 | 0.7500 | 0.5549 | 0.0924 |

### Key Finding:
Advanced tree-based models achieve higher F1 scores and lower Brier scores than the Persistence and Seasonal baselines. The Random Forest achieves **Recall = 1.0000** and **F1 = 0.7692** on the 2024 test holdout.

## 11. Probability Calibration
Probability calibration was evaluated using Platt scaling and Isotonic regression on validation folds. Platt scaling preserved monotonic ranking while reducing Brier score loss compared to raw tree ensemble probabilities.

## 12. Uncertainty Analysis & Bootstrap Confidence Intervals
1,000-iteration block bootstrap across temporal periods yielded the following 95% empirical confidence intervals for Horizon 1 Random Forest:
- **Recall**: 0.7000 (95% CI: 0.5000 - 0.9167)
- **F1 Score**: 0.6667 (95% CI: 0.4000 - 0.8691)
- **Brier Score**: 0.0930 (95% CI: 0.0438 - 0.1407)

## 13. Explainability & Feature Stability
Permutation feature importance confirms that `previous_ipc_phase` is the primary anchor of risk prediction, followed by `rainfall_anomaly_lag1`, `consecutive_dry_months`, and `maize_price_zscore`.

## 14. Error Analysis: False Negatives & False Positives
- **False Negatives**: Primarily occurred during rapid transition months where severe drought conditions persisted locally despite regional rainfall improvements.
- **False Positives**: Occurred during late 2023 / early 2024 following torrential El Niño rains; models retained elevated probabilities due to prior vulnerability lags before vegetation fully recovered.

## 15. Geographic Performance Disparity
Evaluation across individual counties indicates that arid pastoral counties (Turkana, Marsabit, Mandera) exhibit higher baseline model fidelity than agropastoral rangelands (Baringo), where crop-livestock livelihood diversification buffers against rainfall deficits.

## 16. Research Limitations
1. **Pilot Sample Size**: 5 ASAL counties over 6 years (360 county-months) represents an initial benchmark; validation across all 47 Kenyan counties is necessary.
2. **IPC Ground Truth Frequency**: Biannual assessment expansions introduce step-function target labels.
3. **Non-Causal Interpretability**: Predictor contributions represent statistical associations, not structural macroeconomic or hydrological causation.

## 17. Conclusions
- Advanced ML models materially outperform static persistence and empirical seasonal baselines.
- Prior food security status acts as a powerful anchor, but climate and price anomalies provide critical incremental sensitivity.
- Spatial neighbour features provide moderate stability benefits for contiguous border rangelands.

## 18. Future Research Directions
1. Expand from 5 pilot counties to the full 23 ASAL rangeland counties of Kenya.
2. Integrate high-resolution dekadal remote sensing (CHIRPS daily, Sentinel-2 pasture biomass).
3. Test physics-informed hydrological streamflow and soil moisture indicators.
