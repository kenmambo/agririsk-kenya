# Project Interview Scripts: AgriRisk Kenya

**Author:** Kenneth Mambo  
**Formats:** 30-Second Elevator Pitch | 60-Second Overview | 2-Minute Technical Walkthrough  

---

## 1. The 30-Second Elevator Pitch

> *"In Kenya's arid rangelands, extreme droughts and floods cause acute food crises, but traditional humanitarian assessments take 4 to 8 weeks to complete—meaning aid usually arrives only after severe malnutrition has taken hold. I built **AgriRisk Kenya**, an open-source machine learning early-warning prototype that predicts county-level food-insecurity risk 1 to 3 months ahead. By combining satellite rainfall, vegetation indices, staple cereal prices, and cross-county spatial contagion, our calibrated models detect crisis conditions with **83.3% Recall**, giving agencies an actionable window to release pre-arranged funding before disaster peaks."*

---

## 2. The 60-Second Comprehensive Overview

> *"AgriRisk Kenya is an applied machine learning and decision-support prototype I developed to shift drought response in Kenya's Arid and Semi-Arid Lands from reactive relief to **Anticipatory Action**.*
> 
> *The core problem in the region isn't a lack of data; it's operational latency. Official IPC food-security assessments are comprehensive, but field surveys take weeks to compile. To bridge that gap, I engineered a longitudinal panel covering 13 years and 780 county-months, fusing CHIRPS satellite rainfall, MODIS vegetation health, WFP market prices, and spatial adjacency matrices across Kenya's 47 counties.*
> 
> *I set up expanding-origin temporal backtesting with strict zero-leakage safeguards and tuned models with an asymmetric loss function to prioritize **Recall**—because in humanitarian early warning, a False Negative costs lives. On held-out 2024 test data, our calibrated Random Forest achieved **83.3% Recall** and an F1 of 0.77 for 1-month-ahead crisis detection, outperforming standard operational persistence baselines by 42.9% while cutting probability prediction error by 70%.*
> 
> *I delivered the project with a multi-page interactive Streamlit dashboard, a FastAPI service, and a comprehensive test suite of 90 unit tests."*

---

## 3. The 2-Minute Deep Technical Walkthrough

> *"I'd love to walk you through the architecture and findings of **AgriRisk Kenya**.*
> 
> *The technical challenge was creating a reliable, multi-horizon early-warning system for acute food security (IPC Phase 3+ / Crisis) in highly volatile arid rangelands without falling into common time-series traps like forward look-ahead leakage or uncalibrated overconfidence.*
> 
> *I started with data engineering: I built reproducible pipelines that ingest four distinct observational streams: 0.05° CHIRPS precipitation pentads, 250m MODIS NDVI composites, WFP staple maize transactions, and historical IPC ground-truth classifications across 5 pilot ASAL counties from 2012 to 2024.*
> 
> *From these, I engineered 35 longitudinal features. This included multi-scale rolling anomalies to capture slow-onset meteorological drought, price momentum to detect market panic, and first-order Queen contiguity spatial lags to reflect cross-county pastoral herd migration and economic spillovers.*
> 
> *For the predictive architecture, I implemented expanding-origin temporal backtesting across three distinct humanitarian planning horizons: 1 month, 2 months, and 3 months ahead. To evaluate fairly, I built rigorous heuristic baselines—including persistence, historical county frequencies, and seasonal climatology—and benchmarked them against calibrated Logistic Regression, HistGradientBoosting, and Random Forest ensembles.*
> 
> *On our strictly out-of-time 2024 holdout set, the Random Forest model achieved **0.8333 Recall** and **0.7692 F1** for 1-month-ahead forecasting, outperforming the operational persistence baseline's 0.5833 Recall by 42.9%. Furthermore, using Platt sigmoid calibration, we reduced the Brier probability score from 0.4167 to **0.1250**—a 70% error reduction.*
> 
> *We also ran domain ablation experiments, which revealed two critical insights: first, removing historical IPC states causes recall to collapse from 0.90 to 0.20, showing that existing institutional status is the essential anchor; second, removing market price dynamics drops recall from 0.90 to 0.70, proving that grain price volatility provides an essential leading signal before physical biomass deficits register in satellite imagery.*
> 
> *Finally, I wrapped the entire framework in production software: a multi-page Streamlit GIS dashboard, a FastAPI microservice, block bootstrap 95% confidence intervals, and 90 unit tests to ensure complete reproducibility."*
