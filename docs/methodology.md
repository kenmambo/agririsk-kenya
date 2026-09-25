# AgriRisk Kenya: Methodology & Modeling Architecture

This document describes the methodological principles, feature engineering logic, time-aware cross-validation design, and evaluation strategy implemented in **Milestone 2**.

---

## 1. Problem Formulation & Objective

The objective of AgriRisk Kenya is to provide **anticipatory decision support** for acute food insecurity in Kenya's Arid and Semi-Arid Lands (ASALs). 

We formulate the task as a supervised binary classification problem at the **county-month** level:
$$\hat{y}_{c, t} = f\left(\mathbf{X}_{c, \le t}\right) \in \{0, 1\}$$
where:
- $c \in \{\text{Turkana}, \text{Marsabit}, \text{Mandera}, \text{Garissa}, \text{Baringo}\}$ represents the administrative county.
- $t$ represents the monthly observation period ($YYYY\text{-}MM\text{-}01$).
- $\mathbf{X}_{c, \le t}$ is the feature vector constructed strictly from historical observations up to month $t$.
- $y_{c, t} = \text{target\_phase3plus} \in \{0, 1\}$ denotes whether the county is undergoing an acute food crisis:
  $$y_{c, t} = \begin{cases} 1, & \text{if } \text{IPC Phase} \ge 3 \text{ (Crisis, Emergency, Famine)} \\ 0, & \text{if } \text{IPC Phase} \le 2 \text{ (Minimal, Stressed)} \end{cases}$$

---

## 2. Ingestion & County Normalization

Data sources frequently enter the pipeline with disparate naming conventions (e.g. `"Muranga"`, `"Murang'a"`, `"Tharaka-Nithi"`, `"Tharaka Nithi"`). 

The `CountyStandardizer` module executes a strict normalization workflow:
1. Strips diacritics, special punctuation, and trailing whitespace.
2. Resolves county aliases against the official gazetted list of 47 Kenyan counties (`agririsk.core.constants.KENYA_COUNTIES`).
3. Rejects unmapped or ambiguous administrative units at the ingestion boundary before any merge occurs.

Raw streams are ingested independently by domain ingestors (`IPCIngestor`, `ClimateIngestor`, `VegetationIngestor`, `MarketIngestor`) before being harmonized into a unified multi-variate panel.

---

## 3. Feature Engineering Design

To mirror operational decision timelines, feature engineering adheres strictly to three principles:
1. **County Isolation**: All lag and rolling transformations are grouped strictly by `county_name`. No temporal shifts ever cross county boundaries.
2. **Leakage Elimination**: All leading indicators (e.g. `previous_ipc_phase`) are strictly lagged by at least 1 month ($t-1$) so that predictions for month $t$ never ingest future ground truth.
3. **Multi-Domain Triangulation**:
   - **Precipitation**: 1-month and 3-month lagged anomalies (`rainfall_anomaly_1m`, `rainfall_anomaly_3m`) track season onset; `rainfall_rolling_3m` measures absolute moisture volume; and `consecutive_dry_months` measures protracted moisture deficit.
   - **Vegetation**: `ndvi_anomaly_1m`, `ndvi_anomaly_3m`, and `ndvi_trend_3m` track pasture senescence and forage depletion.
   - **Markets**: `maize_price_change_1m`, `maize_price_change_3m`, and county-standardized `maize_price_zscore` quantify purchasing power erosion and food accessibility barriers.

---

## 4. Time-Aware Validation Strategy

### The Flaw of Random Splitting
Standard K-fold cross-validation or random train/test splits are **strictly prohibited** in AgriRisk Kenya. Random splitting introduces severe temporal autocorrelation leakage—training on month $t+1$ to predict month $t$ produces falsely inflated evaluation scores that collapse in live operational deployments.

### Chronological Splitting Protocol
We implement a strictly chronological, forward-chaining partition:
- **Training Set (Earliest Years):** 2019 – 2022 (captures baseline conditions and the historic 2021–2022 Horn of Africa multi-season drought).
- **Validation Set (Intermediate Year):** 2023 (captures the transitional phase from severe drought to late 2023 El Niño rains).
- **Test Set (Out-of-Sample Holdout):** 2024 (evaluates model generalization in an unseen future recovery horizon).

---

## 5. Modeling Architecture & Benchmark Algorithms

Two complementary baseline classifiers are evaluated:
1. **Regularized Logistic Regression**:
   - Features standardized via `StandardScaler`.
   - `class_weight='balanced'` to offset class imbalance.
   - Provides transparent, interpretable log-odds coefficients indicating the directional effect of each risk driver.
2. **Random Forest Classifier**:
   - Non-parametric ensemble of 100 decision trees (`max_depth=5`, `class_weight='balanced'`).
   - Captures non-linear thresholds and complex feature interactions (e.g. high food prices compounding severe consecutive dry months).
   - Generates Gini feature importance (Mean Decrease in Impurity).

---

## 6. Evaluation Metrics: The Priority of Recall in Early Warning

In conventional machine learning, overall Accuracy or F1 score is frequently optimized. In humanitarian early warning, however, classification errors have asymmetric real-world consequences:

$$\text{Asymmetric Costs}: \quad \text{Cost}(\text{False Negative}) \gg \text{Cost}(\text{False Positive})$$

- **False Negative (Type II Error)**: The model predicts "Non-Crisis" ($0$), but a Crisis ($1$) unfolds. Aid mobilization is delayed, anticipatory procurement is missed, and vulnerable households experience acute food deficits.
- **False Positive (Type I Error)**: The model predicts "Crisis" ($1$), but conditions remain Stressed ($0$). Field agronomists and disaster committees verify ground reports; precautionary monitoring is heightened with minimal downside.

Therefore, our primary diagnostic criteria are:
1. **Recall (Sensitivity)**: $\frac{\text{TP}}{\text{TP} + \text{FN}}$ — must be maximized (targeting $\ge 90\%$).
2. **False Negative Rate (FNR)**: $\frac{\text{FN}}{\text{TP} + \text{FN}}$ — must be minimized.
3. **ROC-AUC**: Evaluates ranking quality across varying decision thresholds, allowing operational agencies to choose custom sensitivity thresholds based on available contingency budgets.
