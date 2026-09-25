"""Ingestion pipeline for staple-food market prices."""

from pathlib import Path
from typing import Optional, Union
import pandas as pd
from agririsk.core.logging import logger
from agririsk.ingestion.county_standardizer import normalize_county_name


class MarketIngestor:
    """Ingests and validates monthly staple-food wholesale market price observations."""

    EXPECTED_COLUMNS = [
        "county_name",
        "year",
        "month",
        "commodity",
        "price",
    ]

    @classmethod
    def load_from_csv(
        cls,
        filepath: Union[str, Path],
        target_commodity: Optional[str] = "Maize"
    ) -> pd.DataFrame:
        """Load and validate monthly market price observations from CSV.

        Args:
            filepath: Path to raw market price CSV.
            target_commodity: Optional filter for commodity (defaults to 'Maize').

        Returns:
            Validated DataFrame standardized by county_name, year, month, commodity, price.
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Market source file not found at: {path}")

        logger.info("Loading market price observations from: %s", path)
        df = pd.read_csv(path)

        missing_cols = [c for c in cls.EXPECTED_COLUMNS if c not in df.columns]
        if missing_cols:
            raise ValueError(f"Market file missing required columns: {missing_cols}")

        df = df.copy()

        # 1. Normalize county names
        df["county_name"] = df["county_name"].apply(normalize_county_name)

        # 2. Filter commodity if requested
        if target_commodity:
            df = df[df["commodity"].str.strip().str.lower() == target_commodity.lower()].copy()
            if df.empty:
                raise ValueError(f"No records found for commodity '{target_commodity}'.")

        # 3. Type conversions and range checks
        df["year"] = df["year"].astype(int)
        df["month"] = df["month"].astype(int)
        if not df["month"].between(1, 12).all():
            raise ValueError("Found invalid months outside range [1, 12].")

        df["price"] = df["price"].astype(float)
        if (df["price"] <= 0).any():
            raise ValueError("Found non-positive market prices.")

        # 4. Deduplicate
        initial_len = len(df)
        df = df.drop_duplicates(subset=["county_name", "year", "month", "commodity"], keep="last")
        if len(df) < initial_len:
            logger.warning("Dropped %d duplicate market rows.", initial_len - len(df))

        df = df.sort_values(by=["county_name", "year", "month"]).reset_index(drop=True)
        logger.info("Successfully ingested %d market records.", len(df))
        return df
