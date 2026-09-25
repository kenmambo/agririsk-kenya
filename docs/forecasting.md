# Multi-Horizon Food Security Risk Forecasting Methodology

## 1. Forecasting Objective

The objective of **Milestone 4** is to transition AgriRisk Kenya from retrospective and contemporaneous risk estimation to **prospective short-horizon risk forecasting** at the county level.

Specifically, the system estimates the statistical probability that a monitored county will move into or remain in **elevated acute food insecurity (IPC Phase 3+ equivalent)** across three explicit planning horizons:
- **1-Month Ahead (\(t+1\)):** Immediate operational preparedness and logistical readiness.
- **2-Months Ahead (\(t+2\)):** Medium-term pre-positioning and contingency stock mobilisation.
- **3-Months Ahead (\(t+3\)):** Early-warning trigger for inter-agency assessments and anticipatory cash transfers.

> **CRITICAL INSTITUTIONAL NOTICE:**  
> AgriRisk Kenya forecasting models are research decision-support prototypes. Model-generated forward risk probabilities **DO NOT** constitute official Integrated Food Security Phase Classification (IPC) projections or official emergency declarations by the Government of Kenya. Official food security classifications and projections are determined solely by the Kenya Food Security Steering Group (KFSSG) and the IPC Global Support Unit.

---

## 2. Multi-Horizon Target Construction

Let \(t\) represent the calendar observation month (e.g., March 2024). For each county \(c\) and forecast horizon \(h \in \{1, 2, 3\}\):

$$\text{target\_phase3plus\_t}h_{c, t} = y_{c, t+h}$$

Where \(y_{c, t+h}\) is the binary ground-truth indicator:
- \(y_{c, t+h} = 1\) if official IPC Acute Phase \(\ge 3\) (Crisis, Emergency, or Catastrophe) at month \(t+h\).
- \(y_{c, t+h} = 0\) if official IPC Acute Phase \(< 3\) (Minimal or Stressed) at month \(t+h\).

### Long-Format Forecast Architecture (`data/processed/forecast_dataset.csv`)

To prevent temporal leakage and support horizon-specific modeling, observations are structured in long tabular format:

$$\text{county\_name} \times \text{observation\_date} \times \text{horizon\_months}$$

Every record enforces the strict physical constraint:
$$\text{target\_date} = \text{observation\_date} + h \text{ months} > \text{observation\_date}$$

Records for forward unobserved periods (e.g., December 2024 predicting January–March 2025) are preserved with `target = NaN` for forward live inference.

---

## 3. Predictor Engineering & Leakage Prevention

All predictor features are constructed strictly from month \(t\) and earlier (\(t, t-1, t-2, \dots\)). No future information enters any feature calculation.

| Predictor Category | Feature Name | Description & Formula | Temporal Window |
| :--- | :--- | :--- | :--- |
| **Climate** | `rainfall_anomaly_lag1` | 1-month lag of precipitation percentage anomaly | \(t-1\) |
| | `rainfall_anomaly_lag2` | 2-month lag of precipitation percentage anomaly | \(t-2\) |
| | `rainfall_anomaly_lag3` | 3-month lag of precipitation percentage anomaly | \(t-3\) |
| | `rainfall_rolling_3m` | Cumulative 3-month precipitation sum | \([t-2, t]\) |
| | `rainfall_rolling_6m` | Cumulative 6-month precipitation sum | \([t-5, t]\) |
| | `consecutive_dry_months` | Streak count of months with anomaly \(< -20\%\) | Backward streak to \(t\) |
| **Vegetation** | `ndvi_anomaly_lag1` | 1-month lag of MODIS NDVI percentage anomaly | \(t-1\) |
| | `ndvi_anomaly_lag2` | 2-month lag of MODIS NDVI percentage anomaly | \(t-2\) |
| | `ndvi_anomaly_lag3` | 3-month lag of MODIS NDVI percentage anomaly | \(t-3\) |
| | `ndvi_trend_3m` | 3-month vegetative slope | \([t-2, t]\) |
| | `ndvi_trend_6m` | 6-month vegetative change (\(\text{NDVI}_t - \text{NDVI}_{t-6}\)) | \([t-5, t]\) |
| **Market** | `maize_price_change_1m`| 1-month percentage change in wholesale dry maize price | \([t-1, t]\) |
| | `maize_price_change_3m`| 3-month percentage change in wholesale dry maize price | \([t-3, t]\) |
| | `maize_price_change_6m`| 6-month percentage change in wholesale dry maize price | \([t-6, t]\) |
| | `maize_price_zscore` | Standardized maize price deviation from county baseline | \(t\) |
| **Food Security** | `previous_ipc_phase` | IPC acute phase at month \(t-1\) (structural vulnerability anchor) | \(t-1\) |
| | `ipc_phase_lag2` | IPC acute phase at month \(t-2\) | \(t-2\) |
| | `ipc_phase_lag3` | IPC acute phase at month \(t-3\) | \(t-3\) |
| **Seasonality** | `month` | Calendar month (1 to 12) | \(t\) |
| | `quarter` | Calendar quarter (1 to 4) | \(t\) |
| | `is_long_rains` | Binary flag for March–May (MAM) agricultural season | \(t\) |
| | `is_short_rains`| Binary flag for October–December (OND) agricultural season | \(t\) |
| **Ecology** | `is_arid` | Binary flag (1 for pastoral Arid counties, 0 for Semi-Arid) | Constant |

---

## 4. Expanding-Window Rolling-Origin Validation

Standard random K-Fold cross-validation is **strictly prohibited** because it violates the arrow of time, leaking future climate and economic shocks into past models.

AgriRisk Kenya implements **expanding-window chronological backtesting**:

```
[2019-07 ----------------- 2022-12] ---> [2023-01 ------- 2023-12]  (Fold 1: Val 2023)
  Train: 180 county-months                 Val: 60 county-months
  (Captures baseline to peak drought)       (Transition from peak drought to El Niño)

[2019-07 -------------------------------- 2023-12] ---> [2024-01 ------- 2024-12]  (Fold 2: Test 2024)
  Train: 240 county-months                               Test: 60 county-months
  (Full historical training corpus)                       (Prospective recovery holdout)
```

1. **Burn-in Period (`2019-01` to `2019-06`):** Reserved to initialize 6-month rolling lags without imputation.
2. **Validation Fold (`val_2023`):** Used to compare candidate model families (`LogisticRegression`, `RandomForestClassifier`, `HistGradientBoostingClassifier`), tune decision thresholds, and fit probability calibrators.
3. **Out-of-Time Test Fold (`test_2024`):** Strictly held out until final evaluation to assess model generalization under novel post-flood recovery conditions.

---

## 5. Threshold Selection & Asymmetric Early-Warning Loss

In humanitarian early warning, classification errors are fundamentally asymmetric:
- **False Negative (Missed Crisis):** Communities face acute hunger without pre-positioned aid, leading to preventable malnutrition, distress livestock sales, and humanitarian catastrophe.
- **False Positive (Precautionary Alert):** Early-warning verification missions and heightened monitoring are initiated—a minor operational inconvenience that does not harm lives.

Consequently, AgriRisk Kenya **does not use an uncalibrated default 0.50 cutoff**. Decision thresholds are optimized using the criterion:

$$\theta^* = \arg\max_{\theta \in [0.10, 0.90]} F_1(\theta) \quad \text{subject to} \quad \text{Recall}(\theta) \ge 0.80$$

If no threshold achieves 80% recall, the threshold maximizing recall is selected.

---

## 6. Probability Calibration (Platt Scaling)

Raw tree probabilities often suffer from miscalibration (clustering around extremes or over-confidence). To produce reliable Bayesian risk estimates:

1. A 1D logistic calibrator is fit on out-of-fold validation probabilities:
   $$\hat{P}(y=1 \mid \hat{p}) = \frac{1}{1 + \exp\left(-(A \hat{p} + B)\right)}$$
2. Reliability is quantified using the **Brier Score**:
   $$\text{Brier} = \frac{1}{N} \sum_{i=1}^N (\hat{P}_i - y_i)^2$$
3. Reliability diagrams (calibration curves) verify that predicted probabilities match observed frequencies across probability deciles.

---

## 7. Model Performance Summary (2024 Prospective Holdout)

| Horizon | Selected Model | Tuned Cutoff | Test Recall | Test Precision | Test F1 | Test ROC-AUC | Brier Score | False Negatives |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1-Month (\(t+1\))** | HistGradientBoosting | 0.10 | **100.0%** | 18.2% | 0.3077 | 0.7733 | 0.1707 | **0 / 12** |
| **2-Months (\(t+2\))**| HistGradientBoosting | 0.10 | **100.0%** | 16.0% | 0.2759 | 0.6964 | 0.1678 | **0 / 12** |
| **3-Months (\(t+3\))**| Random Forest | 0.35 | **100.0%** | 27.3% | 0.4286 | 0.7778 | 0.1800 | **0 / 12** |

*Key Diagnostic Finding:* Across all three forecasting horizons, the calibrated models successfully flagged **100% of the acute crisis periods in the 2024 holdout (0 false negatives)**, demonstrating high sensitivity for anticipatory humanitarian monitoring.

---

## 8. Important Research Limitations

1. **Temporal Discrepancy (Cadence Mismatch):** Satellite rainfall and NDVI update monthly or dekadally, while official IPC classifications update biannually. Forward targets carry 6-month step persistence between assessments.
2. **Sparse Ground-Truth Transitions:** Over 6 years, each county has only 12 official IPC assessment periods. True regime shifts (\(0 \to 1\) or \(1 \to 0\)) are relatively rare events.
3. **Spatial Autocorrelation:** Northern Kenyan pastoral counties (Turkana, Marsabit, Mandera) share contiguous rangelands and grazing corridors. Shocks in Marsabit frequently correlate with Turkana through inter-county livestock migration and terms-of-trade contagion.
4. **Omitted Confounders:** The current feature set does not model localized armed insecurity, cross-border cattle rustling, human or livestock disease epidemics, or humanitarian aid delivery volumes.
5. **Non-Causal Interpretation:** Feature weights and signals represent statistical correlations. They must never be interpreted as proving causal mechanisms or sufficient conditions for acute food insecurity.
