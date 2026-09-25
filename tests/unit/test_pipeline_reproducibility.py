"""Unit and integration tests for Milestone 5: Automated Ingestion, Reproducibility, and Manifest Tracking."""

import json
from pathlib import Path
from datetime import datetime, timezone
import pytest
import pandas as pd

from agririsk.ingestion.manifest import DataManifestManager, calculate_sha256
from agririsk.geospatial.reference import CountyReferenceRegistry
from agririsk.validation.drift_detector import DriftDetector, SchemaDriftError
from agririsk.ingestion.base import CHIRPSRainfallSource, BaseDataSource
from agririsk.pipeline import PipelineOrchestrator


def test_sha256_computation(tmp_path: Path):
    """Verify deterministic SHA-256 fingerprinting of files."""
    test_file = tmp_path / "sample.txt"
    test_file.write_text("AgriRisk Kenya Reproducibility Test", encoding="utf-8")

    checksum1 = DataManifestManager.compute_sha256(test_file)
    checksum2 = calculate_sha256(test_file)

    assert checksum1 == checksum2
    assert len(checksum1) == 64
    assert isinstance(checksum1, str)


def test_manifest_registration_and_retrieval(tmp_path: Path):
    """Verify asset registration, persistence, and querying in DataManifestManager."""
    manifest_file = tmp_path / "manifest.json"
    mgr = DataManifestManager(manifest_path=manifest_file)

    dummy_raw = tmp_path / "dummy_raw.csv"
    dummy_raw.write_text("county_name,rainfall_mm\nTurkana,45.2\nMarsabit,12.1\n", encoding="utf-8")

    asset = mgr.record_asset(
        dataset_name="rainfall_chirps",
        source_provider="UCSB Climate Hazards Center",
        source_url="https://data.chc.ucsb.edu/products/CHIRPS-2.0/",
        file_path=dummy_raw,
        date_coverage_start="2024-01",
        date_coverage_end="2024-02",
        geographic_coverage=["Turkana", "Marsabit"],
        row_count=2,
        schema_version="1.0",
        ingestion_status="success",
        staleness_days=10,
        is_stale=False
    )

    assert asset["row_count"] == 2
    assert asset["dataset_name"] == "rainfall_chirps"
    assert asset["sha256_checksum"] == calculate_sha256(dummy_raw)

    # Verify reloading from disk
    mgr_reload = DataManifestManager(manifest_path=manifest_file)
    latest = mgr_reload.get_latest_asset("rainfall_chirps")
    assert latest is not None
    assert latest["asset_id"] == asset["asset_id"]
    assert latest["row_count"] == 2


def test_identical_file_detection(tmp_path: Path):
    """Verify duplicate file detection via SHA-256 fingerprint."""
    manifest_file = tmp_path / "manifest.json"
    mgr = DataManifestManager(manifest_path=manifest_file)

    dummy_raw = tmp_path / "rainfall.csv"
    dummy_raw.write_text("county_name,rainfall_mm\nTurkana,45.2\n", encoding="utf-8")
    checksum = calculate_sha256(dummy_raw)

    mgr.record_asset(
        dataset_name="rainfall_chirps",
        source_provider="UCSB",
        source_url="https://example.com/test",
        file_path=dummy_raw,
        date_coverage_start="2024-01",
        date_coverage_end="2024-01",
        geographic_coverage=["Turkana"],
        row_count=1,
        staleness_days=5,
        is_stale=False
    )

    # Identical file should be detected
    assert mgr.has_identical_asset("rainfall_chirps", checksum) is True

    # Different content checksum should not be duplicate
    dummy_modified = tmp_path / "rainfall_mod.csv"
    dummy_modified.write_text("county_name,rainfall_mm\nTurkana,99.9\n", encoding="utf-8")
    checksum_mod = calculate_sha256(dummy_modified)
    assert mgr.has_identical_asset("rainfall_chirps", checksum_mod) is False


def test_county_reference_canonicalization():
    """Verify canonical county name resolution and alias handling."""
    # Direct canonical lookup
    assert CountyReferenceRegistry.canonicalize("Turkana") == "Turkana"
    assert CountyReferenceRegistry.canonicalize("turkana") == "Turkana"
    assert CountyReferenceRegistry.canonicalize(" TURKANA ") == "Turkana"

    # Known alias resolutions
    assert CountyReferenceRegistry.canonicalize("Elgeyo Marakwet") == "Elgeyo-Marakwet"
    assert CountyReferenceRegistry.canonicalize("Keiyo-Marakwet") == "Elgeyo-Marakwet"
    assert CountyReferenceRegistry.canonicalize("Tharaka Nithi") == "Tharaka-Nithi"
    assert CountyReferenceRegistry.canonicalize("taita-taveta") == "Taita Taveta"

    # Total 47 constitutional counties
    all_counties = CountyReferenceRegistry.all_counties()
    assert len(all_counties) == 47
    assert "Turkana" in all_counties
    assert "Nairobi" in all_counties

    # Geographic coverage audit
    valid_names = ["Turkana", "Marsabit", "Mandera", "Garissa", "Baringo"]
    audit = CountyReferenceRegistry.audit_geographic_coverage(valid_names)
    assert audit["is_valid"] is True
    assert len(audit["unmatched_entities"]) == 0

    invalid_names = ["Turkana", "UnknownCountyXYZ", "Atlantis"]
    audit_bad = CountyReferenceRegistry.audit_geographic_coverage(invalid_names)
    assert audit_bad["is_valid"] is False
    assert "UnknownCountyXYZ" in audit_bad["unmatched_entities"]
    assert "Atlantis" in audit_bad["unmatched_entities"]


def test_schema_drift_detection_missing_columns():
    """Verify that DriftDetector raises SchemaDriftError when required columns are absent."""
    df_missing = pd.DataFrame({
        "county_name": ["Turkana", "Marsabit"],
        # 'month' and 'rainfall_mm' are missing
    })

    with pytest.raises(SchemaDriftError) as exc_info:
        DriftDetector.validate_schema(
            df=df_missing,
            dataset_name="rainfall_chirps",
            expected_columns=["county_name", "year", "month", "rainfall_mm"],
            raise_error=True
        )
    assert "Missing required columns" in str(exc_info.value)


def test_schema_drift_detection_bounds_breach():
    """Verify that DriftDetector detects value breaches outside allowable physical ranges."""
    df_invalid_bounds = pd.DataFrame({
        "county_name": ["Turkana", "Marsabit"],
        "year": [2024, 2024],
        "month": [1, 1],
        "rainfall_mm": [-25.0, 50.0],  # Negative precipitation is physically invalid
        "rainfall_anomaly": [0.0, 5.0]
    })

    is_valid, issues = DriftDetector.validate_schema(
        df=df_invalid_bounds,
        dataset_name="rainfall_chirps",
        expected_columns=["county_name", "year", "month", "rainfall_mm"],
        numeric_bounds={"rainfall_mm": (0.0, 2000.0)},
        raise_error=False
    )
    assert is_valid is False
    assert any("rainfall_mm" in str(issue) for issue in issues)


def test_staleness_calculation():
    """Verify staleness duration logic against configured thresholds."""
    adapter = CHIRPSRainfallSource()

    # Dataset from recent date -> not stale
    now = datetime.now(timezone.utc)
    recent_date_str = f"{now.year:04d}-{now.month:02d}"

    days, is_stale = adapter.compute_staleness_days(recent_date_str)
    assert days <= 45
    assert is_stale is False

    # Historical dataset from 2020 -> stale
    days_old, is_stale_old = adapter.compute_staleness_days("2020-01")
    assert days_old > 300
    assert is_stale_old is True


def test_raw_file_immutability(tmp_path: Path):
    """Verify that saving raw data generates timestamped non-overwriting files."""
    adapter = CHIRPSRainfallSource()
    adapter.local_raw_dir = tmp_path / "raw_climate"

    content = b"county_name,rainfall_mm\nTurkana,12.5\n"
    file1 = adapter.save_raw_immutable(content, "chirps_monthly.csv")

    assert file1.exists()
    assert file1.name.endswith("_chirps_monthly.csv")

    # Saving again with same filename preserves file without corruption
    file2 = adapter.save_raw_immutable(b"Different content", "chirps_monthly.csv")
    assert file2 == file1
    assert file1.read_bytes() == content


def test_pipeline_orchestrator_dry_run():
    """Verify that PipelineOrchestrator executes successfully in dry-run mode."""
    orchestrator = PipelineOrchestrator(
        sources=["all"],
        dry_run=True,
        step="validate"
    )
    report = orchestrator.execute()

    assert report["status"] == "success"
    assert report["dry_run"] is True
    assert "rainfall" in report["successful_sources"]
    assert "vegetation" in report["successful_sources"]
    assert "market" in report["successful_sources"]
    assert "ipc" in report["successful_sources"]
