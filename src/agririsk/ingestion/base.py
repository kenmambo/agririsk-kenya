"""Abstract BaseDataSource and provider adapters for automated, reproducible ingestion."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import yaml
import pandas as pd
import numpy as np

from agririsk.core.logging import logger
from agririsk.ingestion.manifest import calculate_sha256, DataManifestManager
from agririsk.geospatial.reference import CountyReferenceRegistry
from agririsk.validation.drift_detector import DriftDetector, SchemaDriftError

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
REGISTRY_PATH = PROJECT_ROOT / "config" / "data_sources.yaml"


def load_registry_config() -> Dict[str, Any]:
    """Load data source registry configuration."""
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(f"Registry configuration missing: {REGISTRY_PATH}")
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f).get("sources", {})


class BaseDataSource(ABC):
    """Abstract base class for all reproducible, versioned data source ingestors."""

    def __init__(self, source_key: str, manifest_mgr: Optional[DataManifestManager] = None):
        self.source_key = source_key
        self.manifest_mgr = manifest_mgr or DataManifestManager()
        self.registry = load_registry_config().get(source_key, {})
        if not self.registry:
            raise KeyError(f"Source '{source_key}' not found in config/data_sources.yaml")

        self.name = self.registry["name"]
        self.provider = self.registry["provider"]
        self.url = self.registry["url"]
        self.local_raw_dir = PROJECT_ROOT / self.registry["local_raw_dir"]
        self.default_filename = self.registry.get("default_filename", f"{source_key}.csv")
        self.expected_columns = self.registry.get("expected_columns", [])
        self.staleness_warning_days = self.registry.get("staleness_warning_days", 60)

    @abstractmethod
    def fetch(self, force_refresh: bool = False) -> Tuple[Path, str]:
        """Fetch remote data or locate valid local snapshot.

        Returns:
            Tuple of (file_path: Path, status: 'success'|'stale_fallback'|'failed').
        """
        pass

    @abstractmethod
    def normalise(self, df: pd.DataFrame) -> pd.DataFrame:
        """Harmonize units, geography, and timestamps into standardized schema."""
        pass

    def validate_raw(self, filepath: Path) -> pd.DataFrame:
        """Load and validate raw file schema against contractual expectations."""
        if not filepath.exists():
            raise FileNotFoundError(f"Asset file not found at: {filepath}")

        df = pd.read_csv(filepath)
        DriftDetector.validate_schema(
            df=df,
            dataset_name=self.source_key,
            expected_columns=self.expected_columns,
            raise_error=True
        )
        return df

    def save_raw_immutable(self, content: bytes, original_filename: str) -> Path:
        """Save raw downloaded content to a timestamp-versioned immutable path.

        Never overwrites existing files.

        Args:
            content: Raw file byte stream.
            original_filename: Upstream source filename.

        Returns:
            Path to the saved versioned file.
        """
        self.local_raw_dir.mkdir(parents=True, exist_ok=True)
        today_prefix = datetime.now(timezone.utc).strftime("%Y%m%d")
        versioned_name = f"{today_prefix}_{original_filename}"
        target_path = self.local_raw_dir / versioned_name

        if target_path.exists():
            logger.info("Versioned raw file %s already exists. Preserving existing copy.", target_path)
            return target_path

        with open(target_path, "wb") as f:
            f.write(content)

        logger.info("Saved immutable raw asset: %s (%d bytes)", target_path, len(content))
        return target_path

    def compute_staleness_days(self, latest_date_str: str) -> Tuple[int, bool]:
        """Calculate days elapsed since latest record and compare against staleness threshold."""
        try:
            # Handle YYYY-MM or YYYY-MM-DD
            if len(latest_date_str) == 7:
                dt = datetime.strptime(latest_date_str + "-01", "%Y-%m-%d").replace(tzinfo=timezone.utc)
            else:
                dt = datetime.strptime(latest_date_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            days = max(0, (now - dt).days)
            is_stale = days > self.staleness_warning_days
            return days, is_stale
        except Exception:
            return 0, False

    def ingest_and_manifest(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Execute full ingestion pipeline: fetch, validate, manifest, and return standardized records."""
        file_path, status = self.fetch(force_refresh=force_refresh)
        raw_df = self.validate_raw(file_path)

        # Geographic audit
        geo_audit = CountyReferenceRegistry.audit_geographic_coverage(raw_df["county_name"].tolist())

        # Dates
        if "year" in raw_df.columns and "month" in raw_df.columns:
            start_date = f"{raw_df['year'].min()}-{str(raw_df['month'].min()).zfill(2)}"
            end_date = f"{raw_df['year'].max()}-{str(raw_df['month'].max()).zfill(2)}"
        elif "period_start" in raw_df.columns and "period_end" in raw_df.columns:
            start_date = str(raw_df["period_start"].min())
            end_date = str(raw_df["period_end"].max())
        else:
            start_date = "Unknown"
            end_date = "Unknown"

        staleness_days, is_stale = self.compute_staleness_days(end_date)
        if status == "stale_fallback":
            is_stale = True

        norm_df = self.normalise(raw_df)

        # Record in manifest
        asset_meta = self.manifest_mgr.record_asset(
            dataset_name=self.source_key,
            source_provider=self.provider,
            source_url=self.url,
            file_path=file_path,
            date_coverage_start=start_date,
            date_coverage_end=end_date,
            geographic_coverage=geo_audit["matched_counties"],
            row_count=len(norm_df),
            schema_version="1.0",
            ingestion_status=status,
            staleness_days=staleness_days,
            is_stale=is_stale
        )

        return {
            "metadata": asset_meta,
            "data": norm_df,
            "geo_audit": geo_audit
        }


# --- Domain Provider Implementations ---

class CHIRPSRainfallSource(BaseDataSource):
    """Adapter for CHIRPS gridded monthly rainfall data."""

    def __init__(self, manifest_mgr: Optional[DataManifestManager] = None):
        super().__init__("rainfall_chirps", manifest_mgr=manifest_mgr)

    def fetch(self, force_refresh: bool = False) -> Tuple[Path, str]:
        """Fetch rainfall data. In pilot/offline environments, locates local file or cached snapshot."""
        default_file = self.local_raw_dir / self.default_filename
        if default_file.exists():
            return default_file, "success"

        # Check for any versioned snapshot in directory
        existing = sorted(self.local_raw_dir.glob("*.csv"))
        if existing:
            logger.warning("Remote CHIRPS fetch unavailable. Falling back to cached snapshot: %s", existing[-1])
            return existing[-1], "stale_fallback"

        raise FileNotFoundError(f"No rainfall source available at {default_file}")

    def normalise(self, df: pd.DataFrame) -> pd.DataFrame:
        clean = df.copy()
        clean["county_name"] = clean["county_name"].apply(
            lambda c: CountyReferenceRegistry.match_county(c)[0] or c
        )
        clean["year"] = clean["year"].astype(int)
        clean["month"] = clean["month"].astype(int)
        clean["rainfall_mm"] = clean["rainfall_mm"].astype(float).clip(lower=0.0)
        clean["rainfall_anomaly"] = clean["rainfall_anomaly"].astype(float)
        return clean.sort_values(["county_name", "year", "month"]).reset_index(drop=True)


class MODISVegetationSource(BaseDataSource):
    """Adapter for MODIS NDVI vegetation health observations."""

    def __init__(self, manifest_mgr: Optional[DataManifestManager] = None):
        super().__init__("vegetation_modis", manifest_mgr=manifest_mgr)

    def fetch(self, force_refresh: bool = False) -> Tuple[Path, str]:
        default_file = self.local_raw_dir / self.default_filename
        if default_file.exists():
            return default_file, "success"

        existing = sorted(self.local_raw_dir.glob("*.csv"))
        if existing:
            return existing[-1], "stale_fallback"

        raise FileNotFoundError(f"No vegetation source available at {default_file}")

    def normalise(self, df: pd.DataFrame) -> pd.DataFrame:
        clean = df.copy()
        clean["county_name"] = clean["county_name"].apply(
            lambda c: CountyReferenceRegistry.match_county(c)[0] or c
        )
        clean["year"] = clean["year"].astype(int)
        clean["month"] = clean["month"].astype(int)
        # Handle both ndvi and ndvi_mean
        if "ndvi_mean" in clean.columns and "ndvi" not in clean.columns:
            clean["ndvi"] = clean["ndvi_mean"]
        elif "ndvi" in clean.columns and "ndvi_mean" not in clean.columns:
            clean["ndvi_mean"] = clean["ndvi"]
        clean["ndvi_mean"] = clean["ndvi_mean"].astype(float).clip(-1.0, 1.0)
        clean["ndvi"] = clean["ndvi_mean"]
        clean["ndvi_anomaly"] = clean["ndvi_anomaly"].astype(float)
        return clean.sort_values(["county_name", "year", "month"]).reset_index(drop=True)


class MarketPriceSource(BaseDataSource):
    """Adapter for staple dry maize wholesale commodity prices."""

    COMMODITY_MAPPING = {
        "maize": "Maize",
        "dry maize": "Maize",
        "white maize": "Maize",
        "corn": "Maize"
    }

    def __init__(self, manifest_mgr: Optional[DataManifestManager] = None):
        super().__init__("market_prices", manifest_mgr=manifest_mgr)

    def fetch(self, force_refresh: bool = False) -> Tuple[Path, str]:
        default_file = self.local_raw_dir / self.default_filename
        if default_file.exists():
            return default_file, "success"

        existing = sorted(self.local_raw_dir.glob("*.csv"))
        if existing:
            return existing[-1], "stale_fallback"

        raise FileNotFoundError(f"No market price source available at {default_file}")

    def normalise(self, df: pd.DataFrame) -> pd.DataFrame:
        clean = df.copy()
        clean["county_name"] = clean["county_name"].apply(
            lambda c: CountyReferenceRegistry.match_county(c)[0] or c
        )
        clean["commodity"] = clean["commodity"].apply(
            lambda c: self.COMMODITY_MAPPING.get(str(c).lower().strip(), c)
        )
        clean["year"] = clean["year"].astype(int)
        clean["month"] = clean["month"].astype(int)
        # Handle both price and price_kes_per_90kg
        if "price" in clean.columns and "price_kes_per_90kg" not in clean.columns:
            clean["price_kes_per_90kg"] = clean["price"]
        elif "price_kes_per_90kg" in clean.columns and "price" not in clean.columns:
            clean["price"] = clean["price_kes_per_90kg"]
        clean["price"] = clean["price"].astype(float).clip(lower=0.0)
        clean["price_kes_per_90kg"] = clean["price"]
        clean["unit"] = "90kg bag"
        clean["currency"] = "KES"
        return clean.sort_values(["county_name", "year", "month"]).reset_index(drop=True)


class IPCFoodSecuritySource(BaseDataSource):
    """Adapter for official IPC acute food security classifications."""

    def __init__(self, manifest_mgr: Optional[DataManifestManager] = None):
        super().__init__("ipc_food_security", manifest_mgr=manifest_mgr)

    def fetch(self, force_refresh: bool = False) -> Tuple[Path, str]:
        default_file = self.local_raw_dir / self.default_filename
        if default_file.exists():
            return default_file, "success"

        existing = sorted(self.local_raw_dir.glob("*.csv"))
        if existing:
            return existing[-1], "stale_fallback"

        raise FileNotFoundError(f"No IPC source file available at {default_file}")

    def normalise(self, df: pd.DataFrame) -> pd.DataFrame:
        clean = df.copy()
        clean["county_name"] = clean["county_name"].apply(
            lambda c: CountyReferenceRegistry.match_county(c)[0] or c
        )
        clean["period_start"] = pd.to_datetime(clean["period_start"]).dt.strftime("%Y-%m-%d")
        clean["period_end"] = pd.to_datetime(clean["period_end"]).dt.strftime("%Y-%m-%d")
        clean["ipc_phase"] = clean["ipc_phase"].astype(int).clip(1, 5)
        clean["phase3plus_population"] = clean["phase3plus_population"].astype(int).clip(lower=0)
        clean["phase3plus_percent"] = clean["phase3plus_percent"].astype(float).clip(0.0, 100.0)
        clean["target_phase3plus"] = (clean["ipc_phase"] >= 3).astype(int)
        return clean.sort_values(["county_name", "period_start"]).reset_index(drop=True)
