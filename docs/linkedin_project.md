# LinkedIn Project Showcase: AgriRisk Kenya

---

## 1. Professional Headline & Project Title
**AgriRisk Kenya: Bridging the Humanitarian Latency Gap with Machine Learning and Satellite Earth Observation**

---

## 2. Short LinkedIn Update (~100 Words)

How can data science help prevent climate shocks from escalating into severe hunger?

I built **AgriRisk Kenya**, an open-source machine learning early-warning prototype designed for Anticipatory Action across Kenya's Arid and Semi-Arid Lands (ASALs). 

By uniting CHIRPS satellite rainfall, MODIS vegetation indices, WFP staple grain prices, and Queen spatial contiguity across a 13-year historical panel (780 county-months), the system forecasts acute food-insecurity risk 1 to 3 months ahead.

Evaluated on held-out 2024 data, our calibrated Random Forest model delivered **83.3% Recall** in crisis detection—outperforming operational persistence baselines by 42.9% while cutting probability prediction error by 70%.

Explore the repo: https://github.com/kenmambo/agririsk-kenya

---

## 3. Comprehensive LinkedIn Post (~300 Words)

In Kenya's Arid and Semi-Arid Lands (ASALs), over 16 million people depend on vulnerable bimodal rainfall cycles. When consecutive rains fail, acute malnutrition and livestock depletion surge.

Yet conventional humanitarian response faces a persistent bottleneck: **reaction latency**. Authoritative consensus assessments (IPC / NDMA) require extensive field surveys taking 4 to 8 weeks. Interventions often mobilize only after crises are deeply entrenched.

To support **Anticipatory Action**, I developed **AgriRisk Kenya**—an empirical decision-support architecture that predicts county-level food-insecurity risk at 1-, 2-, and 3-month lead times.

### Key Technical Highlights:
1. **Multi-Modal Data Integration:** Harmonized 13 years of longitudinal data (780 county-months) spanning CHIRPS pentad rainfall (0.05°), MODIS 250m NDVI/VCI, WFP cereal transaction price shocks, and historical IPC ground truth.
2. **Spatial Spillover Modeling:** Constructed first-order Queen contiguity adjacency graphs across Kenya's 47 counties to capture cross-border pasture migration and market contagion.
3. **Rigorous Temporal Evaluation:** Applied expanding-origin backtesting with zero look-ahead leakage. On held-out 2024 data, the calibrated ensemble achieved:
   - **Recall:** 0.8333 (vs. 0.5833 for persistence benchmarks—a 42.9% relative gain)
   - **F1-Score:** 0.7692
   - **Calibration Error (Brier Score):** 0.1250 (a 70% error reduction vs. 0.4167)
4. **Domain Ablation Insights:** Discovered that removing cereal price dynamics drops recall from 0.90 to 0.70, proving market volatility acts as a vital leading indicator before physical vegetation deficits appear.

The project is fully open-source, complete with an interactive Streamlit geospatial dashboard, FastAPI microservice, Model/Dataset Cards, and 90 automated unit tests.

Feedback, contributions, and discussions are warmly welcome!

---

## 4. Suggested Hashtags
`#DataScience` `#MachineLearning` `#ClimateChange` `#FoodSecurity` `#RemoteSensing` `#AnticipatoryAction` `#AIForGood` `#Python` `#GeospatialAI` `#EarthObservation` `#Kenya` `#HumanitarianTech`
