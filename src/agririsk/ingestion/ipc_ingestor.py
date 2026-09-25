"""Ingestion module for historical IPC acute food insecurity observations."""

from pathlib import Path
from typing import Optional, Union
import pandas as pd
from agririsk.core.logging import logger
from agririsk.ingestion.county_standardizer import normalize_county_name


class IPCIngestor:
    """Ingests and validates historical IPC Acute Food Insecurity assessment data."""

    EXPECTED_COLUMNS = [
        "county_name",
        "period_start",
        "period_end",
        "ipc_phase",
        "phase3plus_population",
        "phase3plus_percent",
    ]

    @classmethod
    def load_from_csv(cls, filepath: Union[str, Path]) -> pd.DataFrame:
        """Load and parse IPC observations from CSV file.

        Args:
            filepath: Path to the raw IPC assessment CSV.

        Returns:
            Validated and standardized DataFrame with 'target_phase3plus' binary flag.
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"IPC source file not found at: {path}")

        logger.info("Loading raw IPC data from: %s", path)
        df = pd.read_csv(path)

        # Verify required columns exist
        missing_cols = [c for c in cls.EXPECTED_COLUMNS if c not in df.columns]
        if missing_cols:
            raise ValueError(f"IPC file missing required columns: {missing_cols}")

        df = df.copy()

        # 1. Normalize county names
        df["county_name"] = df["county_name"].apply(normalize_county_name)

        # 2. Parse dates
        df["period_start"] = pd.to_datetime(df["period_start"]).dt.date
        df["period_end"] = pd.to_datetime(df["period_end"]).dt.date

        # 3. Validate IPC phase (1 to 5)
        df["ipc_phase"] = df["ipc_phase"].astype(int)
        invalid_phases = df[~df["ipc_phase"].between(1, 5)]
        if not invalid_phases.empty:
            raise ValueError(f"Found invalid IPC phases outside [1, 5]: {invalid_phases['ipc_phase'].tolist()}")

        # 4. Derive binary early-warning target: Phase 3+ (Crisis or worse)
        # Phase 1 (Minimal): 0
        # Phase 2 (Stressed): 0
        # Phase 3 (Crisis): 1
        # Phase 4 (Emergency): 1
        # Phase 5 (Famine): 1
        df["target_phase3plus"] = (df["ipc_phase"] >= 3).astype(int)

        logger.info("Successfully ingested %d IPC assessment records.", len(df))
        return df

    @classmethod
    def expand_to_monthly(cls, ipc_df: pd.DataFrame) -> pd.DataFrame:
        """Expand bi-annual IPC assessment validity periods into monthly records (year, month).

        Enables precise time-series alignment with monthly climate, vegetation, and market streams.
        """
        monthly_records = []

        for _, row in ipc_df.iterrows():
            county = row["county_name"]
            p_start = pd.to_datetime(row["period_start"])
            p_end = pd.to_datetime(row["period_end"])
            phase = row["ipc_phase"]
            target = row["target_phase3plus"]
            pop = row["phase3plus_population"]
            pct = row["phase3plus_percent"]

            # Monthly date range covering the assessment period
            date_range = pd.date_range(p_start, p_end, freq="MS")
            for dt in date_range:
                monthly_records.append({
                    "county_name": county,
                    "year": dt.year,
                    "month": dt.month,
                    "ipc_phase": phase,
                    "target_phase3plus": target,
                    "phase3plus_population": pop,
                    "phase3plus_percent": pct,
                })

        expanded_df = pd.DataFrame(monthly_records)
        # Drop duplicates if overlapping periods occur, keeping latest
        expanded_df = expanded_df.drop_duplicates(subset=["county_name", "year", "month"], keep="last")
        expanded_df = expanded_df.sort_values(by=["county_name", "year", "month"]).reset_index(drop=True)
        return expanded_df
