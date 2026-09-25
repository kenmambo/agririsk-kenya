"""Ingestion pipeline for satellite vegetation (NDVI) indicators."""

from pathlib import Path
from typing import Union
import pandas as pd
from agririsk.core.logging import logger
from agririsk.ingestion.county_standardizer import normalize_county_name


class VegetationIngestor:
    """Ingests and validates monthly NDVI and vegetation anomaly observations."""

    EXPECTED_COLUMNS = [
        "county_name",
        "year",
        "month",
        "ndvi_mean",
        "ndvi_anomaly",
    ]

    @classmethod
    def load_from_csv(cls, filepath: Union[str, Path]) -> pd.DataFrame:
        """Load and validate monthly vegetation records from CSV.

        Args:
            filepath: Path to raw monthly vegetation CSV file.

        Returns:
            Validated DataFrame standardized by county_name, year, month.
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Vegetation source file not found at: {path}")

        logger.info("Loading vegetation observations from: %s", path)
        df = pd.read_csv(path)

        missing_cols = [c for c in cls.EXPECTED_COLUMNS if c not in df.columns]
        if missing_cols:
            raise ValueError(f"Vegetation file missing required columns: {missing_cols}")

        df = df.copy()

        # 1. Normalize county names
        df["county_name"] = df["county_name"].apply(normalize_county_name)

        # 2. Type conversions and range checks
        df["year"] = df["year"].astype(int)
        df["month"] = df["month"].astype(int)
        if not df["month"].between(1, 12).all():
            raise ValueError("Found invalid months outside range [1, 12].")

        df["ndvi_mean"] = df["ndvi_mean"].astype(float)
        if not df["ndvi_mean"].between(-0.2, 1.0).all():
            raise ValueError("Found NDVI values outside physical bounds [-0.2, 1.0].")

        df["ndvi_anomaly"] = df["ndvi_anomaly"].astype(float)

        # 3. Deduplicate
        initial_len = len(df)
        df = df.drop_duplicates(subset=["county_name", "year", "month"], keep="last")
        if len(df) < initial_len:
            logger.warning("Dropped %d duplicate vegetation rows.", initial_len - len(df))

        df = df.sort_values(by=["county_name", "year", "month"]).reset_index(drop=True)
        logger.info("Successfully ingested %d vegetation records.", len(df))
        return df
