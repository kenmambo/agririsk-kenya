# 5-Minute Live Demo Walkthrough Script: AgriRisk Kenya

**Target Audience:** Technical Recruiters, Scholarship Panels, Academic Admissions, Humanitarian Program Officers  
**Presenter:** Kenneth Mambo  
**Prerequisites:** Streamlit app launched (`uv run streamlit run app/Home.py`) or Terminal Demo (`make demo`)  
**Duration:** Exactly 5 Minutes  

---

## Preparation Checklist
- [ ] Open browser to `http://localhost:8501` (full screen).
- [ ] Ensure terminal is open in background with `make demo` ready.
- [ ] Verify test suite is passing (`uv run pytest`).

---

## Minute 0:00 – 1:00 | Context, Latency Bottleneck & Executive Landing
**Screen:** `Home.py` (Executive Overview)  
**Action:** Point to the top KPI cards and the Responsible Use Disclaimer banner.

> **Spoken Narrative:**  
> *"Welcome! I'm excited to demonstrate **AgriRisk Kenya**, an applied machine learning and decision-support prototype built to shift disaster response in Kenya's Arid and Semi-Arid Lands from reactive emergency relief to **Anticipatory Action**.*
> 
> *The fundamental bottleneck in East African drought management isn't a shortage of data; it's **reaction latency**. Authoritative consensus food-security assessments—like the Integrated Food Security Phase Classification (IPC)—take 4 to 8 weeks to conduct household surveys, harmonize data, and gazette bulletins. By then, acute malnutrition and livestock mortality are already underway.*
> 
> *Here on the executive landing page, you see our operational scope: monitoring key ASAL counties across 13 years of historical panels, tracking elevated risk flags, and emphasizing upfront that our model provides decision support, not autonomous alerts."*

---

## Minute 1:00 – 2:00 | Geospatial Choropleth & Spatial Neighbor Contagion
**Screen:** Navigate to `1_Geospatial.py` (Kenya County Choropleth Map)  
**Action:** Filter by latest period. Hover over Turkana and Marsabit to display risk bands. Toggle spatial neighbor view.

> **Spoken Narrative:**  
> *"Moving to our geospatial layer, we map risk classifications across Kenya's counties into four calibrated risk bands: Low, Moderate, Elevated, and High.*
> 
> *Crucially, pastoral rangelands don't exist as isolated administrative islands. When severe drought desiccates pasture in Marsabit, pastoralists migrate thousands of livestock into Samburu or Turkana, altering local pasture availability and transmitting economic shocks.*
> 
> *To capture this, we engineered first-order **Queen Contiguity spatial lag features** across Kenya's 47 counties. When a bordering county moves into crisis, our model dynamically updates the neighboring risk multiplier, smoothing administrative boundaries and detecting regional contagion before it spreads."*

---

## Minute 2:00 – 3:00 | County Deep Dive & Multi-Sensor Longitudinal Analytics
**Screen:** Navigate to `2_County_Deep_Dive.py`  
**Action:** Select `Turkana`. Scroll through the multi-panel time-series chart showing CHIRPS rainfall, MODIS NDVI, and WFP maize prices.

> **Spoken Narrative:**  
> *"Let's drill down into a specific county—here, Turkana.*
> 
> *Our framework integrates four independent data streams into a standardized monthly panel: 0.05° CHIRPS precipitation pentads, 250-meter MODIS satellite vegetation condition (NDVI and VCI), WFP staple cereal prices, and historical IPC ground truth.*
> 
> *Notice this multi-indicator timeline: during the historic 2021–2022 drought, rainfall deficits drop below the 20th percentile. Shortly after, vegetation indices collapse. But notice the third panel: staple maize prices surged 3 months *before* the satellite vegetation deficit reached its trough. Our domain ablation research proved that grain market dynamics serve as vital leading tripwires for impending household food deficits."*

---

## Minute 3:00 – 4:00 | Short-Horizon Forecasting & Probability Calibration
**Screen:** Navigate to `7_Forecast.py` (Multi-Horizon Early Warning)  
**Action:** Toggle between 1-Month ($t+1$), 2-Month ($t+2$), and 3-Month ($t+3$) horizons. Show calibrated probability gauge and 95% bootstrap confidence intervals.

> **Spoken Narrative:**  
> *"Here is the predictive core: our multi-horizon direct early warning engine.*
> 
> *Rather than a single static forecast, we model three actionable humanitarian horizons: 1 month, 2 months, and 3 months ahead. To eliminate error compounding, we train separate direct models for each lead time under expanding-origin temporal backtesting with zero look-ahead leakage.*
> 
> *Notice that we don't output uncalibrated scores. In Forecast-based Financing, disbursements depend on exact probability thresholds. Using **Platt Sigmoid Scaling**, we cut probability prediction error (Brier score) by 70%—from 0.4167 down to **0.1250**. Furthermore, every prediction is bounded by **95% stationary block bootstrap confidence intervals**, ensuring decision-makers understand prediction uncertainty before deploying contingent funds."*

---

## Minute 4:00 – 5:00 | Research Insights, Empirical Benchmarks & Responsible AI
**Screen:** Navigate to `8_Research_Insights.py`  
**Action:** Point to the Model Comparison table, the Domain Ablation bar chart, and the Geographic Equity table.

> **Spoken Narrative:**  
> *"Finally, let's inspect our research-grade evaluation deck.*
> 
> *Does machine learning actually beat simple operational heuristics? Yes: on our strictly held-out 2024 test year, our calibrated Random Forest achieved **83.3% Recall** in crisis detection, compared to only 58.3% for the operational persistence baseline—a **42.9% relative gain**.*
> 
> *Our ablation experiments show that omitting prior food security drops recall from 90% to 20%, while omitting market dynamics drops it from 90% to 70%. Furthermore, our geographic equity audit confirms high responsiveness in arid pastoral rangelands like Turkana and Marsabit, while accurately reflecting post-El Niño agricultural recovery in agropastoral Baringo with an ultra-low Brier error of 0.0163.*
> 
> *The entire system is backed by 90 automated tests, comprehensive Model and Dataset Cards, and explicit ethical governance prohibiting autonomous execution. Thank you, and I welcome any technical or policy questions!"*

---

## Fast Q&A Pivot Guide
- **If asked about deployment:** Emphasize that this is an offline research prototype designed to assist NDMA/WFP analysts, not replace them.
- **If asked about Deep Learning:** State clearly that tree ensembles and linear baselines were chosen for sample efficiency on 780 county-months, reserving Graph Neural Networks for future 47-county expanded panels.
- **If asked about False Positives:** Explain the asymmetric loss function—in early warning, missing a famine (False Negative) is catastrophic, while precautionary monitoring (False Positive) is low-cost and protective.
