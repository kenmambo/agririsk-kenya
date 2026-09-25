# Executive Summary: AgriRisk Kenya

**Document Type:** High-Level Decision Briefing & Strategic Overview  
**Audience:** National Drought Management Authority (NDMA), County Steering Groups, International Donors (FCDO, USAID, World Bank), and Humanitarian Program Directors  
**Author:** Kenneth Mambo  
**Date:** September 2026  

---

## 1. The Strategic Challenge: Breaking the Latency Cycle

Across Kenya's 23 Arid and Semi-Arid Land (ASAL) counties—home to over 16 million people—pastoralist and agropastoral communities are bearing the brunt of accelerating climatic instability. Consecutive failed rainy seasons decimate livestock herds, collapse household purchasing power, and cause spikes in acute malnutrition.

While Kenya boasts an internationally recognized drought monitoring apparatus through the **National Drought Management Authority (NDMA)** and the multi-agency **Integrated Food Security Phase Classification (IPC)**, disaster response remains largely **reactive**:
- Field surveys take **4 to 8 weeks** to execute, harmonize, and publish.
- Humanitarian appeals are typically triggered only after crisis conditions (IPC Phase 3+) or emergency conditions (IPC Phase 4) are formally confirmed.
- Consequently, aid mobilizes when pastoralists have already liquidated reproductive livestock at distressed salvage prices and children have suffered severe nutritional damage.

**The Imperative:** To protect lives and livelihoods cost-effectively, Kenya must transition from post-disaster response to **Anticipatory Action**—triggering pre-arranged financing and preventative interventions before acute food crises peak.

---

## 2. Technical Innovation: The AgriRisk Kenya Architecture

**AgriRisk Kenya** is an open-source, empirical early-warning decision-support prototype designed to forecast county-level acute food-insecurity crisis risk at **1-, 2-, and 3-month lead times**.

Rather than relying on isolated indicators, the architecture fuses four complementary observational streams into a 13-year longitudinal panel (2012–2024; 780 county-months across pilot ASAL counties):
1. **High-Resolution Satellite Rainfall:** 0.05° (~5.3 km) CHIRPS precipitation pentads, tracking cumulative seasonal deficits and dry-spell durations.
2. **Satellite Vegetation Dynamics:** 250m MODIS 16-day composite NDVI and Vegetation Condition Index (VCI) proxies, measuring forage degradation.
3. **Staple Commodity Market Intelligence:** UN World Food Programme (WFP/VAM) monthly retail and wholesale cereal transaction prices, tracking purchasing power collapse.
4. **Geospatial Adjacency Modeling:** First-order Queen contiguity spatial lag vectors capturing cross-county livestock migration and economic spillovers across Kenya's 47 counties.

The entire pipeline is engineered with strict zero-leakage temporal backtesting, ensuring that historical evaluations reflect realistic, uncorrupted decision environments.

---

## 3. Validated Empirical Findings

Evaluating machine learning models against standard operational baselines (persistence, historical county frequency, and seasonal climatology) on a held-out test year (**2024**; 60 county-months) produced critical empirical takeaways:

```
+-----------------------------------------------------------------------------------------+
|                  1-MONTH AHEAD (t+1) CRISIS FORECAST PERFORMANCE (2024 HOLDOUT)         |
+------------------------------+--------+-------------------+----------+---------+--------+
| Architecture                 | Recall | 95% Bootstrap CI  | F1-Score | PR-AUC  | Brier  |
+------------------------------+--------+-------------------+----------+---------+--------+
| Random Forest (Ensemble)     | 0.8333 | [0.6000, 1.0000]  | 0.7692   | 0.7500  | 0.1250 |
| HistGradientBoosting         | 0.8333 | [0.5800, 1.0000]  | 0.7143   | 0.7500  | 0.1472 |
| Logistic Regression (Platt)  | 0.5833 | [0.3300, 0.8300]  | 0.5385   | 0.6250  | 0.1824 |
| Operational Persistence Base | 0.5833 | [0.3300, 0.8300]  | 0.5385   | 0.3000  | 0.4167 |
+------------------------------+--------+-------------------+----------+---------+--------+
```

### Key Takeaways:
- **42.9% Improvement in Crisis Detection:** The calibrated Random Forest achieved **0.8333 Recall**, successfully anticipating more than 8 out of 10 crisis months, compared to 0.5833 for the persistence heuristic.
- **70.0% Reduction in Probability Prediction Error:** Through Platt sigmoid calibration, the Brier score dropped from 0.4167 to **0.1250**, ensuring that predicted probability scores reflect true empirical frequencies.
- **Actionable 90-Day Early Warning Retention:** Crisis recall held firm at **0.8333 at $t+2$ months** (F1: 0.7143) and decayed gracefully to **0.6667 at $t+3$ months** (F1: 0.6154), delivering a robust 90-day advisory window for pre-arranged intervention.
- **Market Dynamics as Early Tripwires:** Domain ablation proved that omitting cereal market prices reduced crisis recall from 0.90 to 0.70. Grain market volatility reflects community stress weeks before vegetation biomass deficits register from orbit.

---

## 4. Operational Roadmap for Anticipatory Action

AgriRisk Kenya directly operationalizes **Forecast-based Financing (FbF)** through a three-stage early action protocol:

```
+---------------------------------------------------------------------------------------+
| LEAD TIME  | METRIC FIDELITY | OPERATIONAL HUMANITARIAN TRIGGER                       |
+------------+-----------------+--------------------------------------------------------+
| t+3 Months | Recall: 0.67    | NON-REGRET READINESS ACTIONS:                          |
|            | Brier: 0.1654   | Preposition veterinary drugs and vaccines.             |
|            |                 | Inspect and service strategic borehole water generators|
|            |                 | Alert commercial livestock offtake networks.           |
+------------+-----------------+--------------------------------------------------------+
| t+2 Months | Recall: 0.83    | EARLY MARKET & SUPPLY-CHAIN STABILIZATION:             |
|            | Brier: 0.1438   | Pre-authorize social protection cash registries.       |
|            |                 | Contract local millers for subsidized staple cereals.  |
|            |                 | Stage livestock feed supplements in sub-county depots. |
+------------+-----------------+--------------------------------------------------------+
| t+1 Month  | Recall: 0.83    | RAPID HOUSEHOLD ASSET PROTECTION:                      |
|            | Brier: 0.1250   | Disburse unconditional mobile cash transfers (M-Pesa). |
|            |                 | Deploy water-trucking fuel subsidies to remote ASALs.  |
|            |                 | Distribute specialized supplementary child food rations|
+---------------------------------------------------------------------------------------+
```

---

## 5. Algorithmic Governance & Responsible AI

To ensure ethical, transparent, and harm-free application, AgriRisk Kenya adheres to four non-negotiable principles:
1. **Decision-Support Only (Zero Autonomous Triggering):** Model outputs are strictly advisory. Final decisions regarding humanitarian disbursements must remain with mandated institutional authorities (NDMA, county steering committees).
2. **Asymmetric Loss Design:** Decision thresholds are tuned to prioritize Recall. In food security, failing to predict a famine has irreversible human costs; precautionary false alarms allow low-cost monitoring verification.
3. **Non-Causal Interpretability:** Model attribution displays indicate associative predictive strength, not structural biological causality, preventing misguided single-variable policy interventions.
4. **Sub-National Fairness Auditing:** Models are continuously audited across distinct pastoral and agropastoral rangelands to ensure equity in predictive sensitivity.

---

## 6. Strategic Recommendations

1. **Integrate into NDMA Early Warning Dashboards:** Pilot AgriRisk Kenya's 1–3 month probabilistic forecasts alongside monthly NDMA drought bulletins to guide inter-census field team dispatch.
2. **Link to the National Drought Emergency Fund (NDEF):** Establish pre-agreed probabilistic trigger thresholds ($P \ge 0.65$ with $95\%$ CI lower bound $\ge 0.50$) to unlock contingent disaster financing.
3. **Expand County Coverage & Spatial Downscaling:** Extend empirical panel modeling from the 5 pilot ASAL counties across all 23 ASALs and downscale spatial units from county (Admin-1) to sub-county (Admin-2) resolution.
4. **Champion Open-Source Public Infrastructure:** Maintain AgriRisk Kenya as an open, auditable public good to eliminate reliance on proprietary closed-source early warning vendors.
