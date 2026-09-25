# AgriRisk Kenya: Portfolio Summary

**Author:** Kenneth Mambo  
**Role:** Applied Machine Learning & Data Systems Engineer  
**Scope:** $\le 250$ Words | First-Person Narrative  

---

I developed **AgriRisk Kenya**, an open-source machine learning early-warning prototype designed to bridge the critical 4-to-8-week reaction-latency gap in humanitarian drought response across Kenya's Arid and Semi-Arid Lands (ASALs).

Traditional consensus assessments (IPC/NDMA) rely on time-intensive household surveys, often delivering crisis declarations after severe malnutrition and livestock loss have already occurred. To enable **Anticipatory Action**, I built an end-to-end data pipeline that ingests, validates, and harmonizes multi-source observational streams across a 13-year longitudinal panel (2012–2024; 780 county-months): CHIRPS satellite rainfall (0.05°), MODIS 250m vegetation condition (NDVI/VCI), WFP staple food market price shocks, and first-order Queen contiguity spatial lags capturing cross-county livestock migration.

Using an expanding-origin temporal backtesting scheme with strict zero-leakage boundaries, I evaluated machine learning ensembles against standard operational baselines across 1- to 3-month lead-time horizons. On held-out 2024 data, my calibrated Random Forest model achieved a **Recall of 0.8333** (95% CI: 0.60–1.00) and **F1 of 0.7692** for 1-month-ahead crisis anticipation—a **42.9% relative gain in crisis detection** and a **70% reduction in probability prediction error (Brier Score 0.1250 vs. 0.4167)** compared to the persistence baseline.

I packaged the system with a multi-page interactive Streamlit dashboard, a FastAPI microservice, 90 passing unit tests, and comprehensive Model/Dataset Cards. AgriRisk Kenya demonstrates how rigorous, calibrated machine learning can transform climate disaster response from reactive relief into proactive, anticipatory protection.
