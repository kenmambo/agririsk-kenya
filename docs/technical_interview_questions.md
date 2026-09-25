# Technical Interview Questions & In-Depth Answers: AgriRisk Kenya

**Author:** Kenneth Mambo  
**Domain:** Applied Machine Learning, Geospatial Data Science, Time-Series Forecasting  
**Context:** Technical Interview Preparation & Defense  

---

### Q1: Why couldn't you use standard $k$-fold cross-validation for this problem? How did you prevent temporal and spatial leakage?
**Answer:**  
Standard $k$-fold cross-validation randomly shuffles observations across the dataset. In geospatial time-series data like county food security, this causes catastrophic **data leakage** through two mechanisms:
1. **Temporal Look-Ahead Leakage:** Shuffling allows the model to train on future observations (e.g., December 2023) to predict past states (e.g., January 2023). Autoregressive drought indices and vegetation signals are highly auto-correlated over multiple months, resulting in artificially inflated performance that fails in production.
2. **Spatial Contagion Leakage:** If Turkana in March 2022 is in the training set while adjacent Marsabit in March 2022 is in the test set, shared regional climate shocks and cross-county pastoral migration bleed information across folds.

To eliminate leakage, I implemented an **expanding-origin temporal backtesting framework**. All training splits strictly precede test splits chronologically. Scaling parameters, imputation statistics, feature encodings, and Platt calibration mappings were fit exclusively on training slices. Finally, an out-of-time test fold (the complete year 2024; 60 county-months) was held out untouched until final benchmark evaluation.

---

### Q2: Why did you prioritize Recall over Precision or ROC-AUC in your objective function?
**Answer:**  
In humanitarian early-warning and disaster risk management, the real-world cost matrix is deeply **asymmetric**:
- **False Negative (Missed Crisis):** The model predicts "Low Risk", but a severe food emergency strikes. Humanitarian agencies fail to mobilize, emergency funds are withheld, and vulnerable pastoral households suffer catastrophic livestock asset depletion, severe acute child malnutrition, or excess mortality.
- **False Positive (False Alarm):** The model predicts "High Risk", but conditions remain manageable. The consequence is non-catastrophic: agronomists conduct low-cost verification visits, supply chains are put on precautionary alert, and monitoring is intensified.

Because the human and economic cost of a False Negative vastly exceeds a False Positive, I explicitly optimized classification decision thresholds to maximize **Recall** for the minority crisis class (IPC Phase 3+), while monitoring Precision-Recall AUC (PR-AUC) and Brier calibration to prevent runaway false alarms.

---

### Q3: How did you handle class imbalance between crisis and non-crisis months?
**Answer:**  
In our 780 county-month panel, acute food insecurity (IPC Phase 3+) represents approximately 22% of total observations, with significant temporal clustering around severe multi-year drought events. I tackled this through a three-tiered approach:
1. **Cost-Sensitive Learning:** I utilized `class_weight='balanced'` in tree ensembles and logistic regression, weighting loss inversely proportional to class frequencies to penalize errors on crisis months.
2. **Post-Hoc Decision Threshold Tuning:** Rather than defaulting to the arbitrary 0.50 probability threshold, I performed grid searches across validation splits to select decision thresholds that maximized Recall under bounded false-alarm rates ($Precision \ge 0.60$).
3. **Evaluating on PR-AUC instead of ROC-AUC:** ROC-AUC is known to be overly optimistic on imbalanced data because true negatives dominate the false positive rate. I prioritized the Area Under the Precision-Recall Curve (PR-AUC) as our primary ranking metric.

---

### Q4: What is Platt Calibration, why is the Brier Score critical, and how did you apply it?
**Answer:**  
Tree-based ensembles like Random Forest do not output true Bayesian posterior probabilities; they output leaf node vote proportions, which tend to push probabilities away from 0 and 1, resulting in under-confident or poorly calibrated scores.

In Forecast-based Financing (FbF), humanitarian disbursements are triggered when predicted risk crosses quantitative thresholds (e.g., $P \ge 0.65$). If an uncalibrated model outputs 0.65 when the true empirical probability of famine is only 0.35, millions of dollars of emergency aid could be misallocated.

I applied **Platt Scaling** (fitting a logistic sigmoid $P(y=1|f) = \frac{1}{1 + \exp(A \cdot f + B)}$ on cross-validated validation fold predictions) to calibrate the raw ensemble scores. Calibration quality was quantified using the **Brier Score** ($BS = \frac{1}{N} \sum (p_i - y_i)^2$). Platt calibration reduced the Brier score by 70%, from 0.4167 (persistence baseline) to **0.1250** (calibrated Random Forest), producing well-calibrated reliability curves across all bins.

---

### Q5: How were the Queen contiguity spatial features constructed, and why not jump straight to Graph Neural Networks (GNNs)?
**Answer:**  
I constructed a canonical topological spatial graph for Kenya's 47 counties using first-order **Queen Contiguity** (two counties are neighbors if they share a common boundary edge or point). From this graph, I generated dynamic spatial lag features:
1. `spatial_neighbor_crisis_ratio`: The proportion of bordering counties currently classified in IPC Phase 3+ at time $t$.
2. `spatial_neighbor_ndvi_anomaly`: Distance-decay weighted average of neighbor vegetation condition anomalies.

Regarding GNNs: with 5 pilot ASAL counties and 156 monthly timestamps (780 records total), deep Spatio-Temporal Graph Neural Networks (such as ST-GCN or GAT) introduce extreme overparameterization risks, high sample inefficiency, and opacity. By engineering explicit topological spatial lag features and feeding them to regularized tree ensembles, we gained the predictive power of spatial contagion while preserving sample efficiency, rapid backtesting, and full interpretability. GNNs remain on our research roadmap once national 47-county panels are fully operationalized.

---

### Q6: How did you formulate multi-horizon forecasting (direct vs. recursive), and why?
**Answer:**  
I used a **Direct Multi-Horizon Forecasting architecture**, training separate, dedicated models for each lead time:
- $M_1$ predicts $y_{t+1}$ using features known at time $t$.
- $M_2$ predicts $y_{t+2}$ using features known at time $t$.
- $M_3$ predicts $y_{t+3}$ using features known at time $t$.

The alternative—a *Recursive Strategy*—trains a single 1-step-ahead model and iteratively feeds its own predictions back as lagged inputs for subsequent steps. In food security forecasting, recursive architectures suffer from severe **error compounding**: if the model makes a slight error in predicting vegetation stress at $t+1$, that error pollutes the $t+2$ prediction, and by $t+3$ the forecast collapses into erratic hallucinations. The direct strategy avoids error compounding and allows each model to discover horizon-specific feature relationships.

---

### Q7: What did your feature group ablation study reveal about satellite vs. market indicators?
**Answer:**  
We systematically trained and evaluated models omitting one feature domain at a time on the 2024 holdout test set:
1. **Omitting Historical Food Security Lags:** Recall collapsed from **0.90 to 0.20** (F1 dropped from 0.75 to 0.2353). This proved that current institutional vulnerability is the primary baseline anchor; without it, models cannot calibrate baseline poverty versus acute shock.
2. **Omitting Market Features (WFP Prices):** Recall dropped from **0.90 to 0.70** (F1 dropped from 0.75 to 0.6364). This revealed that market price momentum is a vital **leading indicator**. Grain traders and pastoralists react to impending drought before biomass depletion fully manifests in satellite vegetation indices, making market price spikes an early tripwire.
3. **Omitting Spatial Lags:** Modestly degraded boundary stability and increased false alarms along adjacent county borders (e.g., Turkana–Marsabit border).

---

### Q8: How did you quantify prediction uncertainty and construct confidence intervals?
**Answer:**  
Point forecasts are insufficient for humanitarian risk planning; decision-makers need confidence bounds. Because time-series data exhibits temporal autocorrelation, standard independent and identically distributed (i.i.d.) bootstrap resampling yields artificially narrow confidence intervals.

I implemented **Stationary Block Bootstrapping**:
- Continuous temporal blocks of county observations were sampled with replacement across 300 bootstrap iterations.
- For each bootstrap resample, performance metrics (Recall, F1, PR-AUC, Brier) were re-evaluated on the holdout partition.
- Empirical 95% confidence intervals were extracted from the 2.5th and 97.5th percentiles (e.g., Random Forest 1M Recall: $[0.6000, 1.0000]$).
- In the Streamlit UI, prediction uncertainty is displayed as error bands around the calibrated probability point estimates.

---

### Q9: Why did regularized tree ensembles outperform logistic regression?
**Answer:**  
Food insecurity dynamics are governed by **threshold effects and non-linear interactions**:
- A 20% drop in rainfall in an agropastoral area with high baseline pasture may cause zero food distress. However, that same 20% drop occurring when staple maize prices are already elevated by 50% triggers rapid household destitution.
- A linear model (even with L2 regularization) fits hyperplanes: it assumes each feature contributes additively and independently unless interaction terms are manually specified.
- Tree-based ensembles (Random Forest and HistGradientBoosting) naturally partition the feature space into recursive conditional splits, effortlessly capturing compound non-linear interactions (e.g., `IF rain_anomaly < -1.5 AND maize_spike == 1 AND prior_ipc >= 3`). Consequently, Random Forest achieved **0.8333 Recall** compared to Logistic Regression's **0.5833 Recall**.

---

### Q10: How did you address observational latency differences across sources?
**Answer:**  
In real-world operations, data streams do not arrive synchronously:
- **CHIRPS rainfall:** 5 to 10 days latency.
- **MODIS NDVI composites:** 8 to 16 days processing lag.
- **WFP market price bulletins:** 2 to 4 weeks collection lag.
- **IPC / NDMA assessments:** Published semi-annually with 4 to 8 weeks analysis lag.

To maintain real-world fidelity during backtesting, we constructed our historical feature matrices using strictly backward-looking lag definitions ($t-1, t-2, t-3$). If an observation was at time $t$ (e.g., May 1st), the features ingested represented data fully finalized by the end of month $t-1$ (April 30th). This deliberate temporal buffer ensures that when the model is asked to forecast $t+1$, all predictor data would have been genuinely available to an analyst.

---

### Q11: How do you detect and handle schema drift or corrupted data in the pipeline?
**Answer:**  
I implemented an automated validation and drift detection module (`agririsk.validation.drift_detector`):
1. **Schema Integrity:** Verifies required columns, expected dtypes, and non-null constraints for canonical county identifiers and dates.
2. **Physical Range Bounds:** Applies deterministic domain checks (e.g., precipitation $\ge 0$, NDVI $\in [-1.0, 1.0]$, maize prices $> 0$).
3. **Statistical Distribution Drift:** Computes Population Stability Index (PSI) and Kolmogorov-Smirnov tests comparing incoming raw batches against established baseline distributions. If a feature's PSI exceeds 0.25, the pipeline flags severe drift and alerts the orchestrator.
4. **Graceful Fallback:** If an external download fails or is corrupted, the system logs the failure, marks the source as stale in `data/manifest.json`, and preserves the last-known valid raw snapshot rather than hallucinating synthetic data.

---

### Q12: Why did you choose `uv` as the package manager, and how is reproducibility guaranteed?
**Answer:**  
`uv` is an extremely fast, Rust-based Python package and project manager developed by Astral. I chose `uv` because:
- **Deterministic Lockfiles:** `uv.lock` freezes exact transitive dependencies, hashes, and platform markers, eliminating the "works on my machine" failure mode across Windows, Linux, and macOS.
- **Execution Speed:** `uv sync` resolves and installs dependencies 10–50x faster than traditional pip, accelerating CI/CD pipelines.
- **Isolated Python Runtimes:** Pinning `.python-version` to Python 3.12 ensures consistent bytecode and C-extension behavior across developer workstations and Docker containers.

---

### Q13: What specific failure modes did you identify in false negatives and false positives?
**Answer:**  
Reviewing our diagnostic outputs (`reports/analysis/false_negatives.csv` and `false_positives.csv`):
- **False Negatives (Missed Crises):** Occurred predominantly during sudden onset micro-climatic shocks in Samburu where localized flash floods disrupted market access roads, even though satellite vegetation indices appeared green and favorable.
- **False Positives (False Alarms):** Occurred in Marsabit following severe satellite-measured rainfall deficits, where local communities averted crisis due to unmodeled county government emergency water-trucking and NGO cash distributions. Because external aid interventions are not currently captured in our feature store, the model anticipated a famine that aid successfully mitigated.

---

### Q14: How did you audit sub-national geographic equity and algorithmic fairness?
**Answer:**  
A major risk in regional early warning is that a model might perform exceptionally well in populous, data-rich counties while failing completely in remote, marginalized pastoral counties.

I implemented an automated geographic equity audit (`reports/analysis/county_performance.csv`):
- Disaggregated performance across all pilot ASAL counties.
- Verified that purely pastoral rangelands (Turkana: 0.8333 Recall; Marsabit: 0.7500 Recall) achieved robust early detection on biophysical signals.
- In Baringo (agropastoral), the model correctly adapted to post-El Niño agricultural recovery in 2024, recording zero false alarms and an ultra-low Brier score (0.0163).
- Displayed these county-by-county breakdowns directly on the Streamlit Research Insights page to prevent regional bias from being concealed behind aggregate averages.

---

### Q15: Why is it scientifically dangerous to interpret SHAP values or feature importance as causal mechanisms in early warning?
**Answer:**  
Machine learning explainability methods—such as SHAP (SHapley Additive exPlanations) or permutation importance—measure **associative contribution to model variance**, not **structural causal effects**:
- If high maize prices show a strong positive SHAP value for food insecurity, it means *observing* high prices increases the model's predicted probability of a crisis.
- It does **not** prove that subsidizing maize prices alone will prevent the crisis if the underlying driver is catastrophic groundwater exhaustion or conflict-driven market isolation.
- Treating associative features as causal levers can lead policymakers to enact ineffective or counter-productive interventions. In our documentation and dashboard, we explicitly label all attribution panels as "Non-Causal Associative Contributions" to uphold scientific integrity.
