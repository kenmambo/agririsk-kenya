# AgriRisk Kenya: External Data Sources Specification

This document details the external datasets integrated into the AgriRisk Kenya decision-support platform, including provider attributions, update cadences, spatial/temporal resolutions, access mechanisms, licensing requirements, and operational limitations.

---

## 1. Summary Registry

| Source Identifier | Dataset Name | Primary Provider | Temporal Cadence | Staleness Threshold | Primary Units | Access Method |
|---|---|---|---|---|---|---|
| `rainfall_chirps` | CHIRPS Precipitation | UCSB Climate Hazards Center / USGS | Monthly | 45 Days | Millimeters ($mm$), Anomaly ($\%$) | HTTP / Direct Download / Fallback |
| `vegetation_modis` | MODIS NDVI (MOD13A2 / MYD13A2) | NASA LP DAAC / USGS | 16-Day (Aggregated Monthly) | 45 Days | NDVI Index ($-1.0$ to $+1.0$), Anomaly ($\%$) | NASA Earthdata / AppEEARS / Fallback |
| `market_prices` | Wholesale Staple Food Prices | Regional Agricultural Trade Intelligence Network (RATIN) / EAGC | Monthly (Wholesale) | 60 Days | KES per 90kg bag (Maize, Beans) | Web Portal / CSV Ingestion / Fallback |
| `ipc_food_security` | Acute Food Insecurity Classifications | IPC Global Support Unit / Kenya KFSSG | Seasonal / Biannual | 120 Days | IPC Phase ($1$ to $5$), Population in Phase 3+ | IPC Public Portal / Fallback |
| `county_boundaries` | Kenya County Administrative Boundaries | OCHA HDX / GADM Kenya (IEBC 47 Counties) | Static (Constitutional 2010) | 365 Days | MultiPolygon GeoJSON / Shapefile | HDX / Humanitarian Data Exchange |

---

## 2. Source-by-Source Specifications

### 2.1 Climate: CHIRPS Monthly Rainfall (`rainfall_chirps`)
- **Provider & Attribution**: Climate Hazards Center, University of California Santa Barbara (UCSB) and U.S. Geological Survey (USGS).
- **Citation**: Funk, C., et al. (2015). "The climate hazards group infrared precipitation with stations—a new environmental record for monitoring extremes." *Scientific Data*, 2, 150066.
- **Coverage**: 2019-01 to 2024-12 (Kenya nationwide: $50^\circ\text{S} - 50^\circ\text{N}$, $0.05^\circ$ grid).
- **Spatial Resolution**: $0.05^\circ \approx 5.3\text{ km}$, aggregated to county administrative polygons using area-weighted zonal means.
- **Temporal Resolution**: Calendar monthly totals ($mm$) and long-term percentage anomalies relative to the baseline climatology ($2019-2024$).
- **Access Protocol**: HTTP directory (`https://data.chc.ucsb.edu/products/CHIRPS-2.0/`) or pre-extracted county zonal time-series in `data/raw/climate/`.
- **License**: Public Domain (Creative Commons Zero / Open Access).
- **Known Limitations**:
  - Preliminary CHIRPS estimates are updated within 5 days of month end; final calibrated station-blended versions have an approximate 3-4 week latency.
  - Convective precipitation in complex mountainous terrain (e.g., Mount Kenya, Cherang'any Hills) may exhibit localized smoothing.

### 2.2 Vegetation: MODIS 250m NDVI (`vegetation_modis`)
- **Provider & Attribution**: NASA Land Processes Distributed Active Archive Center (LP DAAC), USGS Earth Resources Observation and Science (EROS) Center.
- **Product**: MOD13Q1 / MYD13A2 Version 6.1 (16-day Composite Normalized Difference Vegetation Index).
- **Spatial Resolution**: 250m sinusoidal grid, aggregated to county boundaries using mean cloud-masked pixel values.
- **Temporal Resolution**: 16-day compositing window, harmonized to county-month means.
- **Access Protocol**: NASA Earthdata Login via AppEEARS API or structured fallback ingest in `data/raw/vegetation/`.
- **License**: Open Data Policy (NASA Worldview / LP DAAC).
- **Known Limitations**:
  - Persistent cloud cover during the peak "Long Rains" (April–May) can attenuate optical surface reflectance; QA band filtering is required to eliminate aerosol contamination.
  - Non-vegetated sandy and rocky terrain in northern arid lands (e.g., Chalbi Desert in Marsabit) yields low dynamic NDVI range, necessitating baseline anomaly scaling.

### 2.3 Market: RATIN Wholesale Staple Food Prices (`market_prices`)
- **Provider & Attribution**: Regional Agricultural Trade Intelligence Network (RATIN), Eastern Africa Grain Council (EAGC), and Kenya Ministry of Agriculture.
- **Coverage**: Urban and cross-border wholesale reference markets across ASAL counties (Lodwar, Marsabit Town, Mandera Town, Garissa Market, Marigat).
- **Commodity Standard**: Dry White Maize and Dry Beans, standardized strictly to **KES per 90kg bag**.
- **Temporal Resolution**: Monthly average wholesale spot price.
- **Access Protocol**: Periodic API extract or CSV ingest from `data/raw/market/`.
- **License**: Proprietary open-access trade bulletin; attributed use permitted for non-commercial early-warning research.
- **Known Limitations**:
  - High transport costs and insecurity can cause intermittent reporting gaps in remote border markets (Mandera, Moyale).
  - Wholesale prices do not fully capture retail markups paid by pastoralist households in remote off-grid settlements.

### 2.4 Food Security: IPC Acute Food Insecurity Classifications (`ipc_food_security`)
- **Provider & Attribution**: Integrated Food Security Phase Classification (IPC) Global Support Unit, in partnership with the Kenya Food Security Steering Group (KFSSG) and NDMA.
- **Key Fields**:
  - `county_name`: Canonical administrative county name.
  - `period_start` & `period_end`: Validity dates for seasonal assessment window.
  - `ipc_phase`: Consensus acute food insecurity phase ($1$: Minimal, $2$: Stressed, $3$: Crisis, $4$: Emergency, $5$: Catastrophe).
  - `phase3plus_population`: Estimated human population in Phase 3 or worse.
  - `phase3plus_percent`: Percentage of county population in Phase 3 or worse.
- **Derived Target**: `target_phase3plus` ($= 1$ if Phase $\ge 3$, else $0$).
- **Temporal Cadence**: Biannual assessments following the Long Rains Assessment (LRA in July/August) and Short Rains Assessment (SRA in February/March), forward-expanded to monthly resolution.
- **Access Protocol**: IPC Public API (`https://api.ipcinfo.org/`) or official KFSSG assessment reports in `data/raw/ipc/`.
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0).
- **Known Limitations**:
  - Step-function temporal structure: classifications remain fixed between assessment cycles, obscuring intra-seasonal volatility.
  - Area-level consensus classifications do not denote universal household distress; sub-county vulnerabilities may be masked.

### 2.5 Administrative Boundaries: Kenya County Boundaries (`county_boundaries`)
- **Provider & Attribution**: Independent Electoral and Boundaries Commission (IEBC) via United Nations OCHA Humanitarian Data Exchange (HDX).
- **Resolution**: Canonical 47 Kenyan Counties (Constitutional boundaries 2010).
- **Format**: GeoJSON (EPSG:4326 WGS84).
- **License**: Creative Commons Attribution for Intergovernmental Organisations (CC BY-IGO).

---

## 3. Downtime & Ingestion Fallback Policy

1. **Deterministic Cache Fallback**: When external network or provider endpoints are unavailable, the ingestion adapters (`CHIRPSRainfallSource`, `MODISVegetationSource`, `MarketPriceSource`, `IPCFoodSecuritySource`) immediately fallback to the latest known-good immutable asset under `data/raw/`.
2. **Explicit Staleness Marking**: If the elapsed duration since the latest observation period exceeds `staleness_threshold_days`, the dataset status is set to `Warning (Stale)` and recorded in `data/manifest.json`.
3. **No Synthetic Imputation**: The system **strictly forbids** fabricating climate, vegetation, price, or IPC observations during pipeline runs. Failed sources will halt downstream feature generation if critical joins cannot be satisfied, logging an explicit audit trail in `reports/pipeline/<run_id>.json`.
