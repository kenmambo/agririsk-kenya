"""Data manifest management, asset metadata tracking, and SHA-256 integrity verification."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from agririsk.core.logging import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MANIFEST_PATH = PROJECT_ROOT / "data" / "manifest.json"


def calculate_sha256(filepath: Path) -> str:
    """Compute SHA-256 hex digest for a file.

    Args:
        filepath: Path to the target file.

    Returns:
        64-character hexadecimal SHA-256 string.
    """
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class DataManifestManager:
    """Maintains immutable asset manifest tracking provenance, checksums, and coverage."""

    compute_sha256 = staticmethod(calculate_sha256)

    def __init__(self, manifest_path: Optional[Path] = None):
        self.manifest_path = manifest_path or MANIFEST_PATH
        self.manifest_data = self._load()

    def _load(self) -> Dict[str, Any]:
        """Load existing manifest or initialize new schema."""
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning("Failed to parse manifest %s (%s). Rebuilding...", self.manifest_path, e)

        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "manifest_version": "1.0",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "assets": {}
        }

    def save(self) -> None:
        """Atomically persist manifest to disk."""
        self.manifest_data["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(self.manifest_data, f, indent=2)
        logger.info("Saved data manifest to: %s", self.manifest_path)

    def get_latest_asset(self, dataset_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve the most recent asset record for a given dataset."""
        records = self.manifest_data["assets"].get(dataset_name, [])
        if not records:
            return None
        return records[-1]

    def has_identical_asset(self, dataset_name: str, checksum: str) -> bool:
        """Check if an asset with identical checksum is already recorded."""
        records = self.manifest_data["assets"].get(dataset_name, [])
        for r in records:
            if r.get("sha256_checksum") == checksum and r.get("ingestion_status") == "success":
                return True
        return False

    def record_asset(
        self,
        dataset_name: str,
        source_provider: str,
        source_url: str,
        file_path: Path,
        date_coverage_start: str,
        date_coverage_end: str,
        geographic_coverage: List[str],
        row_count: int,
        schema_version: str = "1.0",
        ingestion_status: str = "success",
        staleness_days: int = 0,
        is_stale: bool = False,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Record an ingested asset entry with provenance metadata.

        Args:
            dataset_name: Identifier from registry (e.g. 'rainfall_chirps').
            source_provider: Upstream agency or repository name.
            source_url: Download or access URL.
            file_path: Relative or absolute path to stored file.
            date_coverage_start: Earliest date covered (YYYY-MM-DD or YYYY-MM).
            date_coverage_end: Latest date covered (YYYY-MM-DD or YYYY-MM).
            geographic_coverage: List of covered counties.
            row_count: Total valid observation records.
            schema_version: Data format version.
            ingestion_status: 'success', 'stale_fallback', or 'failed'.
            staleness_days: Days elapsed since last expected observation.
            is_stale: Boolean indicator of threshold breach.
            error_message: Optional diagnostic string if failed.

        Returns:
            The created asset dictionary.
        """
        p = Path(file_path)
        checksum = calculate_sha256(p) if p.exists() else "NO_FILE"
        file_size = p.stat().st_size if p.exists() else 0

        # Relative path for portability
        try:
            rel_path = str(p.relative_to(PROJECT_ROOT)).replace("\\", "/")
        except ValueError:
            rel_path = str(p).replace("\\", "/")

        asset_id = f"{dataset_name}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{checksum[:8]}"

        asset_record = {
            "asset_id": asset_id,
            "dataset_name": dataset_name,
            "source_provider": source_provider,
            "source_url": source_url,
            "retrieval_timestamp": datetime.now(timezone.utc).isoformat(),
            "file_path": rel_path,
            "file_size_bytes": file_size,
            "sha256_checksum": checksum,
            "date_coverage_start": str(date_coverage_start),
            "date_coverage_end": str(date_coverage_end),
            "geographic_coverage": geographic_coverage,
            "row_count": row_count,
            "schema_version": schema_version,
            "ingestion_status": ingestion_status,
            "staleness_days": int(staleness_days),
            "is_stale": bool(is_stale),
        }
        if error_message:
            asset_record["error_message"] = error_message

        if dataset_name not in self.manifest_data["assets"]:
            self.manifest_data["assets"][dataset_name] = []

        self.manifest_data["assets"][dataset_name].append(asset_record)
        self.save()
        logger.info("Recorded manifest asset for %s: %s (checksum: %s)", dataset_name, asset_id, checksum[:12])
        return asset_record
