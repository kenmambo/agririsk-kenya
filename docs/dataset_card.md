# Dataset Card: AgriRisk Kenya County-Month Longitudinal Panel

## 1. Dataset Description
- **Dataset Name**: AgriRisk Kenya Longitudinal ASAL Multi-Horizon Panel
- **Version**: v0.2.0 (Milestone 6 Processed Feature Store)
- **Primary Files**:
  - `data/processed/model_dataset.csv`: 360 county-month panel observations (2019–2024).
  - `data/processed/forecast_dataset.csv`: 1,080 multi-horizon forecast observations ($h \in \{1, 2, 3\}$).
- **Curators**: AgriRisk Kenya Research Team

## 2. Ingestion Sources & Attributions
| Domain | Product / Dataset | Primary Source | Access Protocol | License |
|---|---|---|---|---|
| **Precipitation** | CHIRPS v2.0 Monthly ($0.05^\circ$) | UCSB Climate Hazards Center / USGS | HTTP / GeoTIFF Zonal Mean | Open Access (CC0) |
| **Vegetation Health** | MODIS Terra/Aqua 250m NDVI (MOD13A2) | NASA LP DAAC / USGS EROS | NASA Earthdata / AppEEARS | NASA Open Data |
| **Market Prices** | Wholesale Dry White Maize (KES/90kg) | RATIN / Eastern Africa Grain Council | Trade Bulletins / CSV | Open Access for Research |
| **Food Security** | Acute Food Insecurity Phase Classifications | KFSSG / IPC Global Support Unit | IPC Portal / KFSSG LRA/SRA | CC BY 4.0 |
| **Boundaries** | Kenya 47 County Boundaries (IEBC 2010) | OCHA HDX / GADM Kenya | GeoJSON (EPSG:4326) | CC BY-IGO |

## 3. Spatial & Temporal Coverage
- **Spatial Coverage**: 5 pilot ASAL counties across Kenya:
  - `Turkana` (Arid / Northern Pastoral)
  - `Marsabit` (Arid / Northern Pastoral)
  - `Mandera` (Arid / Northeastern Pastoral)
  - `Garissa` (Arid / Eastern Pastoral)
  - `Baringo` (Semi-Arid / Rift Valley Agropastoral)
- **Temporal Coverage**: 72 consecutive calendar months from **January 2019 to December 2024**.
- **Temporal Regularity**: 100% complete continuous monthly series with zero missing time-steps across all 5 counties.

## 4. Key Transformations & Lineage
1. **Zonal Aggregation**: Area-weighted mean extraction of continuous raster satellite fields (rainfall and NDVI) over official county administrative polygons.
2. **Standardization & Price Normalization**: Wholesale staple commodity prices normalized strictly to **KES per 90kg bag**.
3. **Temporal Expansion**: Biannual seasonal IPC assessments forward-expanded into continuous monthly tracking states.
4. **Lag Feature Construction**: Strictly grouped by county to prevent cross-county leakage:
   - 1m, 2m, 3m percentage rainfall anomalies and rolling 3m/6m precipitation totals.
   - Consecutive dry months counter (months with rainfall anomaly $< -20\%$).
   - 1m, 2m, 3m NDVI anomalies and 3m/6m trajectory trends.
   - 1m, 3m, 6m maize wholesale price changes and historical z-scores.
5. **Spatial Neighbourhood Features**: Computed at observation time $t \le T_0$ using Queen contiguity and centroid distance-decay weights:
   - `neighbour_mean_rainfall_anomaly`
   - `neighbour_mean_ndvi_anomaly`
   - `neighbour_mean_price_change`
   - `neighbour_mean_previous_risk`
   - `number_of_high_risk_neighbours`

## 5. Known Biases & Sensor Limitations
- **Step-Function Ground Truth**: IPC classifications remain static between assessment cycles, masking rapid intra-seasonal deterioration or localized humanitarian pockets.
- **Optical Cloud Attenuation**: MODIS optical reflectance during the peak March–May "Long Rains" is subject to persistent cloud masking.
- **Urban Market Proxy**: Wholesale prices measured in regional reference hubs (e.g. Lodwar, Marsabit Town) under-represent transport markups incurred in remote pastoral settlements.

## 6. Appropriate & Inappropriate Uses
- **Appropriate**: Academic research, comparative machine learning benchmarking, anticipatory action workflow modeling, and sensitivity analysis.
- **Inappropriate**: Commercial staple grain speculation, ungrounded humanitarian resource allocation, or replacement of official KFSSG drought monitoring bulletins.
