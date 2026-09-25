"""Generate pilot raw datasets for Turkana, Marsabit, Mandera, Garissa, and Baringo (2019-2024).

These raw files populate:
- data/raw/ipc/kenya_asal_ipc_historical.csv
- data/raw/climate/kenya_asal_monthly_rainfall.csv
- data/raw/vegetation/kenya_asal_monthly_ndvi.csv
- data/raw/market/kenya_asal_maize_prices.csv
"""

from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PILOT_COUNTIES = ["Turkana", "Marsabit", "Mandera", "Garissa", "Baringo"]


def generate_raw_data():
    raw_dir = PROJECT_ROOT / "data" / "raw"
    (raw_dir / "ipc").mkdir(parents=True, exist_ok=True)
    (raw_dir / "climate").mkdir(parents=True, exist_ok=True)
    (raw_dir / "vegetation").mkdir(parents=True, exist_ok=True)
    (raw_dir / "market").mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(42)

    # 1. Historical IPC Assessments (Bi-annual cycles: SRA and LRA, 2019-2024)
    # Kenya IPC assessment windows:
    # 2019: Feb-Jul (SRA), Aug-Jan 2020 (LRA)
    # 2020: Feb-Jul (SRA), Aug-Jan 2021 (LRA)
    # 2021: Feb-Jul (SRA), Aug-Jan 2022 (LRA)
    # 2022: Feb-Jul (SRA), Aug-Jan 2023 (LRA) -> Peak drought
    # 2023: Feb-Jul (SRA), Aug-Jan 2024 (LRA)
    # 2024: Feb-Jul (SRA), Aug-Dec 2024 (LRA)
    periods = [
        ("2019-01-01", "2019-06-30", 2),
        ("2019-07-01", "2019-12-31", 2),
        ("2020-01-01", "2020-06-30", 2),
        ("2020-07-01", "2020-12-31", 2),
        ("2021-01-01", "2021-06-30", 3),
        ("2021-07-01", "2021-12-31", 3),
        ("2022-01-01", "2022-06-30", 3),
        ("2022-07-01", "2022-12-31", 4),  # Peak Emergency/Crisis
        ("2023-01-01", "2023-06-30", 3),
        ("2023-07-01", "2023-12-31", 3),
        ("2024-01-01", "2024-06-30", 2),
        ("2024-07-01", "2024-12-31", 2),
    ]

    ipc_rows = []
    # County population baselines (approx):
    county_pops = {
        "Turkana": 926000,
        "Marsabit": 459000,
        "Mandera": 867000,
        "Garissa": 841000,
        "Baringo": 666000,
    }

    for county in PILOT_COUNTIES:
        base_pop = county_pops[county]
        for p_start, p_end, default_phase in periods:
            # Adjust phase based on county severity (Marsabit/Turkana/Mandera hit harder in 2022)
            if county in ["Turkana", "Marsabit", "Mandera"] and "2022" in p_start:
                phase = 4  # Emergency
                pct = float(np.round(rng.uniform(42.0, 58.0), 1))
            elif county in ["Garissa", "Baringo"] and "2022" in p_start:
                phase = 3  # Crisis
                pct = float(np.round(rng.uniform(30.0, 42.0), 1))
            elif "2021" in p_start or "2023" in p_start:
                phase = 3 if county != "Baringo" else 2
                pct = float(np.round(rng.uniform(22.0, 36.0), 1))
            elif "2024-01-01" in p_start and county in ["Turkana", "Marsabit"]:
                phase = 3
                pct = float(np.round(rng.uniform(24.0, 32.0), 1))
            else:
                phase = 2  # Stressed
                pct = float(np.round(rng.uniform(12.0, 22.0), 1))

            pop_phase3plus = int(round(base_pop * (pct / 100.0)))
            ipc_rows.append({
                "county_name": county,
                "period_start": p_start,
                "period_end": p_end,
                "ipc_phase": phase,
                "phase3plus_population": pop_phase3plus,
                "phase3plus_percent": pct,
            })

    ipc_df = pd.DataFrame(ipc_rows)
    ipc_file = raw_dir / "ipc" / "kenya_asal_ipc_historical.csv"
    ipc_df.to_csv(ipc_file, index=False)
    print(f"Created {ipc_file} ({len(ipc_df)} rows)")

    # 2. Monthly Rainfall, Vegetation, and Market (2019 to 2024, 72 months)
    dates = pd.date_range("2019-01-01", "2024-12-01", freq="MS")

    climate_rows = []
    veg_rows = []
    market_rows = []

    # County climatological normals
    # Pastoral Arid: Turkana, Marsabit, Mandera, Garissa (low base rainfall)
    # Agro-pastoral: Baringo (slightly higher rainfall)
    county_profiles = {
        "Turkana": {"rain_norm": 22.0, "rain_season_mult": 2.5, "ndvi_norm": 0.24, "maize_base": 4800.0},
        "Marsabit": {"rain_norm": 24.0, "rain_season_mult": 2.6, "ndvi_norm": 0.26, "maize_base": 4900.0},
        "Mandera": {"rain_norm": 20.0, "rain_season_mult": 2.8, "ndvi_norm": 0.22, "maize_base": 5100.0},
        "Garissa": {"rain_norm": 26.0, "rain_season_mult": 2.7, "ndvi_norm": 0.28, "maize_base": 4700.0},
        "Baringo": {"rain_norm": 55.0, "rain_season_mult": 2.2, "ndvi_norm": 0.44, "maize_base": 4200.0},
    }

    for county in PILOT_COUNTIES:
        prof = county_profiles[county]
        for dt in dates:
            yr = dt.year
            m = dt.month

            # Seasonal baseline
            if m in [3, 4, 5]:  # MAM Long Rains
                s_factor = prof["rain_season_mult"]
            elif m in [10, 11, 12]:  # OND Short Rains
                s_factor = prof["rain_season_mult"] * 0.85
            else:  # Dry seasons
                s_factor = 0.35

            normal_rain = prof["rain_norm"] * s_factor

            # Year climate anomaly factor:
            # 2019: Positive anomaly (+25% to +50%)
            # 2020: Normal/Slightly negative (-10%)
            # 2021-2022: Multi-season severe drought (-40% to -75%)
            # 2023: Early drought (-30%), Late OND El Nino (+60%)
            # 2024: Above normal (+15% to +35%)
            if yr == 2019:
                anom_mult = 1.35
            elif yr == 2020:
                anom_mult = 0.90
            elif yr in [2021, 2022]:
                anom_mult = 0.38
            elif yr == 2023:
                anom_mult = 0.70 if m < 10 else 1.65
            else:  # 2024
                anom_mult = 1.25

            # Random variability
            noise = rng.normal(1.0, 0.15)
            actual_rain = max(0.0, round(float(normal_rain * anom_mult * noise), 1))
            rain_anomaly = round(float(((actual_rain - normal_rain) / max(normal_rain, 1.0)) * 100.0), 1)

            climate_rows.append({
                "county_name": county,
                "year": yr,
                "month": m,
                "rainfall_mm": actual_rain,
                "rainfall_anomaly": rain_anomaly,
            })

            # Vegetation (NDVI follows rainfall with ~1 month inertia)
            ndvi_norm = prof["ndvi_norm"]
            ndvi_resp = (rain_anomaly / 400.0)
            actual_ndvi = float(np.clip(round(ndvi_norm + ndvi_resp + rng.normal(0, 0.02), 3), 0.08, 0.85))
            ndvi_anomaly = round(float(((actual_ndvi - ndvi_norm) / ndvi_norm) * 100.0), 1)

            veg_rows.append({
                "county_name": county,
                "year": yr,
                "month": m,
                "ndvi_mean": actual_ndvi,
                "ndvi_anomaly": ndvi_anomaly,
            })

            # Maize Wholesale Market Price (KES per 90kg bag)
            # Baseline + general inflation trend + drought scarcity surge in 2021-2022
            inflation_factor = (yr - 2019) * 220.0
            drought_markup = max(0.0, -rain_anomaly * 18.0) if yr in [2021, 2022, 2023] else 0.0
            price = round(float(prof["maize_base"] + inflation_factor + drought_markup + rng.normal(0, 80.0)), 0)

            market_rows.append({
                "county_name": county,
                "year": yr,
                "month": m,
                "commodity": "Maize",
                "price": price,
            })

    clim_df = pd.DataFrame(climate_rows)
    clim_file = raw_dir / "climate" / "kenya_asal_monthly_rainfall.csv"
    clim_df.to_csv(clim_file, index=False)
    print(f"Created {clim_file} ({len(clim_df)} rows)")

    veg_df = pd.DataFrame(veg_rows)
    veg_file = raw_dir / "vegetation" / "kenya_asal_monthly_ndvi.csv"
    veg_df.to_csv(veg_file, index=False)
    print(f"Created {veg_file} ({len(veg_df)} rows)")

    mkt_df = pd.DataFrame(market_rows)
    mkt_file = raw_dir / "market" / "kenya_asal_maize_prices.csv"
    mkt_df.to_csv(mkt_file, index=False)
    print(f"Created {mkt_file} ({len(mkt_df)} rows)")


if __name__ == "__main__":
    generate_raw_data()
