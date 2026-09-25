# Research Abstract: AgriRisk Kenya

**Title:** Multi-Source Machine Learning for Anticipatory Food Security Risk Forecasting in Kenya's Arid and Semi-Arid Lands  
**Author:** Kenneth Mambo  
**Target:** Academic Conference / Journal Submission ($\le 300$ Words)  

---

Acute food insecurity across Kenya's Arid and Semi-Arid Lands (ASALs) is exacerbated by accelerating climate volatility and severe operational latency in traditional humanitarian assessments. Official consensus-based Integrated Food Security Phase Classification (IPC) determinations require comprehensive household surveys with publication lags of 4 to 8 weeks, frequently delaying relief mobilization until severe malnutrition and irreversible livestock asset depletion have occurred. 

This paper introduces **AgriRisk Kenya**, an empirical early-warning decision-support architecture designed to forecast acute food-insecurity crisis risk (IPC Phase 3+) at 1-, 2-, and 3-month lead times to support Anticipatory Action. We construct a 13-year longitudinal panel (2012–2024; 780 county-months) synthesizing 0.05° CHIRPS precipitation pentads, MODIS 250m Normalized Difference Vegetation Index (NDVI) composites, World Food Programme (WFP) staple cereal transaction prices, and first-order Queen contiguity spatial lag matrices. 

Using an expanding-origin temporal backtesting framework with strict zero-leakage boundaries, we benchmark Platt-calibrated machine learning ensembles against operational heuristics (persistence, historical frequency, and seasonal baselines). On held-out 2024 test data, our calibrated Random Forest model achieves a **Recall of 0.8333** (95% bootstrap CI: $[0.6000, 1.0000]$) and an **F1-score of 0.7692** for 1-month-ahead crisis detection—a **42.9% relative improvement in crisis recall** and a **70.0% reduction in Brier score probability error (0.1250 vs. 0.4167)** over the persistence baseline. 

Ablation experiments reveal that omitting cereal price dynamics reduces recall from 0.90 to 0.70, establishing market volatility as a vital leading indicator before physical vegetation deficits appear. While spatial lags enhance regional stability, sub-national audits reveal distinct performance variations between arid pastoral rangelands and agropastoral transition zones. We conclude with ethical governance principles prohibiting autonomous execution, establishing the framework as an auditable, open-source decision-support copilot for disaster risk financing.
