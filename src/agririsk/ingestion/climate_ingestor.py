"""Ingestion pipeline for county-level monthly rainfall and climate data."""

from pathlib import Path
from typing import Union
import pandas as pd
from agririsk.core.logging import logger
from agririsk.ingestion.county_standardizer import normalize_county_name


class ClimateIngestor:
    """Ingests and validates monthly rainfall and precipitation anomaly observations."""

    EXPECTED_COLUMNS = [
        "county_name",
        "year",
        "month",
        "rainfall_mm",
        "rainfall_anomaly",
    ]

    @classmethod
    def load_from_csv(cls, filepath: Union[str, Path]) -> pd.DataFrame:
        """Load and validate monthly climate records from CSV.

        Args:
            filepath: Path to raw monthly climate CSV file.

        Returns:
            Validated DataFrame standardized by county_name, year, month.
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Climate source file not found at: {path}")

        logger.info("Loading climate observations from: %s", path)
        df = pd.read_csv(path)

        missing_cols = [c for c in cls.EXPECTED_COLUMNS if c not in df.columns]
        if missing_cols:
            raise ValueError(f"Climate file missing required columns: {missing_cols}")

        df = df.copy()

        # 1. Normalize county names
        df["county_name"] = df["county_name"].apply(normalize_county_name)

        # 2. Type conversions and range checks
        df["year"] = df["year"].astype(int)
        df["month"] = df["month"].astype(int)
        if not df["month"].between(1, 12).all():
            raise ValueError("Found invalid months outside range [1, 12].")

        df["rainfall_mm"] = df["rainfall_mm"].astype(float)
        if (df["rainfall_mm"] < 0).any():
            raise ValueError("Found invalid negative rainfall values.")

        df["rainfall_anomaly"] = df["rainfall_anomaly"].astype(float)

        # 3. Deduplicate
        initial_len = len(df)
        df = df.drop_duplicates(subset=["county_name", "year", "month"], keep="last")
        if len(df) < initial_len:
            logger.warning("Dropped %d duplicate climate rows.", initial_len - len(df))

        df = df.sort_values(by=["county_name", "year", "month"]).reset_index(drop=True)
        logger.info("Successfully ingested %d climate records.", len(df))
        return df
