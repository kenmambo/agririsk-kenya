# AgriRisk Kenya: Technical & Operational Limitations

This document explicitly outlines the technical, statistical, and operational limitations of the AgriRisk Kenya prototype as of **Milestone 2**.

---

## 1. Non-Operational Research Disclaimer

> **⚠️ RESEARCH PROTOTYPE ONLY**  
> AgriRisk Kenya is an exploratory predictive modeling prototype developed for methodology research and software engineering evaluation. **Model outputs, risk probabilities, and classifications DO NOT constitute official IPC classifications, NDMA bulletins, or Government of Kenya early warning advisories.** This platform must not be used for operational resource allocation, humanitarian aid distribution, or statutory emergency declarations without institutional validation.

---

## 2. Inherent Data-Source Limitations

### A. Temporal Granularity & IPC Ground Truth Sparsity
- **Bi-Annual Ground Truth**: Official IPC Acute Food Insecurity assessments in Kenya are conducted by the Kenya Food Security Steering Group (KFSSG) / National Drought Management Authority (NDMA) bi-annually:
  1. **Long Rains Assessment (LRA)**: Conducted in July/August, valid through January/February.
  2. **Short Rains Assessment (SRA)**: Conducted in February/March, valid through July/August.
- **Step-Function Labels**: In a monthly modeling panel, ground truth labels remain constant across valid 5-to-6 month projection windows. As a result, sudden intra-seasonal shocks occurring mid-season cannot be reflected in official target labels until the subsequent formal assessment.

### B. Spatial Aggregation over Vast Landscapes
- **Broad County Polygons**: Kenyan ASAL counties are geographically vast:
  - Turkana: $\approx 68,680\text{ km}^2$
  - Marsabit: $\approx 66,923\text{ km}^2$
  - Mandera: $\approx 25,798\text{ km}^2$
- **Micro-Climate Averaging**: County-wide spatial averaging of satellite precipitation and NDVI averages over diverse micro-climates. Pastoralist lowlands may experience acute water stress while mountainous pockets receive localized convective rainfall, which county-level aggregates can obscure.

### C. Market Data Sparsity & Price Transmission Latency
- **Rural Market Disconnections**: In deep pastoral zones, physical livestock-for-grain terms of trade govern food access more directly than wholesale cash maize prices. 
- **Missing Market Observations**: Remote ASAL retail markets experience occasional reporting gaps due to transport disruption, flash floods, or localized conflict. Although forward-filling and county-level z-scores mitigate missingness, they introduce temporal smoothing.

### D. Satellite Optical Sensor Cloud Contamination
- **NDVI Cloud Cover**: Optical sensors (MODIS, Sentinel-2) suffer from cloud obscuration during the rainy seasons (MAM and OND). While composite smoothing is applied, early-season green-up signals can lag actual ground forage regeneration by several weeks.

---

## 3. Modeling Limitations & Ethical Boundaries

### A. Asymmetric Cost of False Negatives
- In humanitarian settings, failing to predict a crisis (**False Negative**) has catastrophic consequences for human lives, whereas false alarms (**False Positives**) simply trigger precautionary field verification.
- Baseline models must not be evaluated solely on overall Accuracy, which can look deceptively high in unbalanced datasets while masking critical false negatives.

### B. Distribution Shift & Climate Non-Stationarity
- Global climate disruption is increasing the frequency of compound extreme events (e.g. back-to-back 5 failed rainy seasons immediately followed by historic El Niño floods).
- Machine learning models trained on historical baselines (2019–2022) may experience performance degradation when unprecedented compound shocks alter standard market and ecological transmission mechanisms.
