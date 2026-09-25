# AgriRisk Kenya: Data Dictionary

This document details the schema, definitions, measurement units, and provenance for the county-month analytical dataset (`data/processed/model_dataset.csv`) developed in **Milestone 2**.

---

## 1. Primary Keys & Temporal Identifiers

| Column Name | Data Type | Physical Unit | Domain / Bounds | Description |
| :--- | :--- | :--- | :--- | :--- |
| `county_name` | String | Categorical | 47 Kenya Counties | Normalized official county administrative name (e.g., `Turkana`, `Marsabit`, `Mandera`, `Garissa`, `Baringo`). Standardized via `agririsk.ingestion.county_standardizer`. |
| `year` | Integer | Calendar Year | 2000 – 2030 | Gregorian calendar year of observation. |
| `month` | Integer | Calendar Month | 1 – 12 | Month of observation (1 = January, 12 = December). Represents monthly panel indexed at `YYYY-MM-01`. |

---

## 2. Climate & Precipitation Features

| Column Name | Data Type | Physical Unit | Domain / Bounds | Mathematical Formula & Description |
| :--- | :--- | :--- | :--- | :--- |
| `rainfall_anomaly_1m` | Float | Percentage (%) | $[-100.0, +\infty)$ | 1-month lagged precipitation anomaly relative to long-term monthly normal: $\text{RainAnom}_{t-1}$. |
| `rainfall_anomaly_3m` | Float | Percentage (%) | $[-100.0, +\infty)$ | 3-month lagged precipitation anomaly: $\text{RainAnom}_{t-3}$. Captures early-season onset performance. |
| `rainfall_rolling_3m` | Float | Millimeters (mm) | $[0.0, +\infty)$ | Rolling 3-month cumulative mean precipitation: $\frac{1}{3}\sum_{k=0}^{2} \text{Rainfall}_{t-k}$. Tracks total cumulative moisture availability. |
| `consecutive_dry_months` | Integer | Count (Months) | $[0, 36]$ | Count of continuous preceding unbroken months where rainfall anomaly was negative ($\text{RainAnom} < 0\%$). Direct indicator of protracted meteorological drought. |

---

## 3. Satellite Vegetation Features

| Column Name | Data Type | Physical Unit | Domain / Bounds | Mathematical Formula & Description |
| :--- | :--- | :--- | :--- | :--- |
| `ndvi_anomaly_1m` | Float | Percentage (%) | $[-100.0, +200.0]$ | 1-month lagged Normalized Difference Vegetation Index anomaly: $\text{NDVIAnom}_{t-1}$. Reflects recent pasture and rangeland forage health. |
| `ndvi_anomaly_3m` | Float | Percentage (%) | $[-100.0, +200.0]$ | 3-month lagged NDVI anomaly: $\text{NDVIAnom}_{t-3}$. |
| `ndvi_trend_3m` | Float | NDVI Index Diff | $[-1.0, +1.0]$ | 3-month absolute rate of change in mean NDVI: $\text{NDVI}_{t} - \text{NDVI}_{t-3}$. Identifies rapid green-up or rapid biomass senescence. |

---

## 4. Market & Staple-Food Price Features

| Column Name | Data Type | Physical Unit | Domain / Bounds | Mathematical Formula & Description |
| :--- | :--- | :--- | :--- | :--- |
| `maize_price_change_1m` | Float | Percentage (%) | $(-\infty, +\infty)$ | 1-month percentage change in wholesale dry maize price: $\frac{\text{Price}_t - \text{Price}_{t-1}}{\text{Price}_{t-1}} \times 100$. Signals sudden food price shocks. |
| `maize_price_change_3m` | Float | Percentage (%) | $(-\infty, +\infty)$ | 3-month percentage change in wholesale dry maize price: $\frac{\text{Price}_t - \text{Price}_{t-3}}{\text{Price}_{t-3}} \times 100$. Tracks sustained seasonal price inflation. |
| `maize_price_zscore` | Float | Standard Deviations | $[-5.0, +5.0]$ | Standardized commodity price relative to the county historical mean: $\frac{\text{Price}_t - \mu_{\text{county}}}{\sigma_{\text{county}}}$. Normalizes for baseline spatial price disparities between markets. |

---

## 5. Food Security State & Prediction Target

| Column Name | Data Type | Physical Unit | Domain / Bounds | Description |
| :--- | :--- | :--- | :--- | :--- |
| `previous_ipc_phase` | Float / Int | IPC Phase Scale | $\{1, 2, 3, 4, 5\}$ | Lagged prevailing IPC Acute Food Insecurity Phase ($t-1$): 1 = Minimal, 2 = Stressed, 3 = Crisis, 4 = Emergency, 5 = Famine. Eliminates look-ahead bias while providing baseline memory. |
| `target_phase3plus` | Integer | Binary Indicator | $\{0, 1\}$ | **Primary Prediction Target**: Binary flag indicating whether the county is in IPC Phase 3 or worse (Crisis, Emergency, Catastrophe).<br>• `1` = Elevated Acute Food Insecurity ($\text{IPC Phase} \ge 3$)<br>• `0` = Minimal / Stressed ($\text{IPC Phase} \le 2$). |

---

## 6. Raw Ingestion Sources & Reference Formats

| Stream | Ingestion Directory | Primary Format | Reference Real-World Source |
| :--- | :--- | :--- | :--- |
| **IPC Assessments** | `data/raw/ipc/` | CSV | FEWS NET / NDMA Kenya Food Security Steering Group (KFSSG) Assessments |
| **Climate Observations** | `data/raw/climate/` | CSV | CHIRPS (Climate Hazards Group InfraRed Precipitation with Station data) |
| **Vegetation Health** | `data/raw/vegetation/` | CSV | MODIS (MOD13Q1) / Sentinel-2 NDVI 16-day composites |
| **Market Prices** | `data/raw/market/` | CSV | WFP Vulnerability Analysis and Mapping (VAM) / KNBS Retail & Wholesale Food Monitors |
