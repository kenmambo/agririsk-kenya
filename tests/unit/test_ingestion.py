"""Unit tests for data ingestion modules (IPC, Climate, Vegetation, Market)."""

from pathlib import Path
import pandas as pd
import pytest
from agririsk.ingestion.ipc_ingestor import IPCIngestor
from agririsk.ingestion.climate_ingestor import ClimateIngestor
from agririsk.ingestion.vegetation_ingestor import VegetationIngestor
from agririsk.ingestion.market_ingestor import MarketIngestor

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def test_ipc_ingestor_loads_and_derives_target():
    """Verify loading IPC observations and deriving binary target_phase3plus."""
    ipc_file = PROJECT_ROOT / "data" / "raw" / "ipc" / "kenya_asal_ipc_historical.csv"
    assert ipc_file.exists()

    df = IPCIngestor.load_from_csv(ipc_file)
    assert not df.empty
    assert "target_phase3plus" in df.columns

    # Verify binary target logic
    # Phase 1, 2 -> 0; Phase 3, 4, 5 -> 1
    phase1_2 = df[df["ipc_phase"].isin([1, 2])]
    assert (phase1_2["target_phase3plus"] == 0).all()

    phase3_plus = df[df["ipc_phase"] >= 3]
    assert (phase3_plus["target_phase3plus"] == 1).all()


def test_ipc_expand_to_monthly():
    """Verify expanding bi-annual IPC assessment windows into monthly records."""
    ipc_file = PROJECT_ROOT / "data" / "raw" / "ipc" / "kenya_asal_ipc_historical.csv"
    raw_df = IPCIngestor.load_from_csv(ipc_file)
    monthly_df = IPCIngestor.expand_to_monthly(raw_df)

    assert not monthly_df.empty
    assert "year" in monthly_df.columns
    assert "month" in monthly_df.columns
    assert monthly_df["month"].between(1, 12).all()
    # 5 counties * 72 months = 360 monthly records
    assert len(monthly_df) == 360


def test_climate_ingestor():
    """Verify loading and validating monthly climate records."""
    clim_file = PROJECT_ROOT / "data" / "raw" / "climate" / "kenya_asal_monthly_rainfall.csv"
    assert clim_file.exists()

    df = ClimateIngestor.load_from_csv(clim_file)
    assert not df.empty
    assert (df["rainfall_mm"] >= 0).all()
    assert df["month"].between(1, 12).all()
    assert df["county_name"].nunique() == 5


def test_vegetation_ingestor():
    """Verify loading and validating monthly vegetation NDVI records."""
    veg_file = PROJECT_ROOT / "data" / "raw" / "vegetation" / "kenya_asal_monthly_ndvi.csv"
    assert veg_file.exists()

    df = VegetationIngestor.load_from_csv(veg_file)
    assert not df.empty
    assert df["ndvi_mean"].between(-0.2, 1.0).all()
    assert "ndvi_anomaly" in df.columns


def test_market_ingestor():
    """Verify loading and validating monthly wholesale maize prices."""
    mkt_file = PROJECT_ROOT / "data" / "raw" / "market" / "kenya_asal_maize_prices.csv"
    assert mkt_file.exists()

    df = MarketIngestor.load_from_csv(mkt_file, target_commodity="Maize")
    assert not df.empty
    assert (df["price"] > 0).all()
    assert (df["commodity"] == "Maize").all()
