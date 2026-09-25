"""AgriRisk Kenya End-to-End Pipeline Orchestrator CLI.

Usage:
    python -m agririsk.pipeline run
    python -m agririsk.pipeline run --source rainfall --dry-run
    python -m agririsk.pipeline run --force-refresh
"""

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd

from agririsk.core.logging import logger
from agririsk.ingestion.manifest import DataManifestManager
from agririsk.ingestion.base import (
    CHIRPSRainfallSource,
    MODISVegetationSource,
    MarketPriceSource,
    IPCFoodSecuritySource
)
from agririsk.ingestion.ipc_ingestor import IPCIngestor
from agririsk.features.engineering import FeatureEngineer
from agririsk.forecasting.features import ForecastFeatureEngineer
from agririsk.validation.data_validator import DataValidator

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REPORTS_PIPELINE_DIR = PROJECT_ROOT / "reports" / "pipeline"
REPORTS_DQ_DIR = PROJECT_ROOT / "reports" / "data_quality"
LOGS_DIR = PROJECT_ROOT / "logs"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


class PipelineOrchestrator:
    """Orchestrates ingestion, validation, harmonization, feature engineering, and quality scoring."""

    def __init__(
        self,
        sources: Optional[List[str]] = None,
        force_refresh: bool = False,
        dry_run: bool = False,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        step: str = "all"
    ):
        self.run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        self.sources = sources or ["all"]
        self.force_refresh = force_refresh
        self.dry_run = dry_run
        self.from_date = from_date
        self.to_date = to_date
        self.step = step.lower()

        self.manifest_mgr = DataManifestManager()
        self.run_report: Dict[str, Any] = {
            "run_id": self.run_id,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "sources_attempted": [],
            "successful_sources": [],
            "failed_sources": [],
            "rows_processed": {},
            "validation_issues": {},
            "dry_run": self.dry_run,
            "status": "in_progress"
        }

    def execute(self) -> Dict[str, Any]:
        """Execute all configured pipeline stages."""
        logger.info("=================================================================")
        logger.info("STARTING AGRIRISK PIPELINE EXECUTION (Run ID: %s)", self.run_id)
        if self.dry_run:
            logger.info(">>> DRY RUN MODE ACTIVE - No processed files will be written <<<")
        logger.info("=================================================================")

        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        REPORTS_PIPELINE_DIR.mkdir(parents=True, exist_ok=True)
        REPORTS_DQ_DIR.mkdir(parents=True, exist_ok=True)
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

        adapters = {
            "rainfall": CHIRPSRainfallSource(self.manifest_mgr),
            "vegetation": MODISVegetationSource(self.manifest_mgr),
            "market": MarketPriceSource(self.manifest_mgr),
            "ipc": IPCFoodSecuritySource(self.manifest_mgr),
        }

        active_keys = list(adapters.keys()) if "all" in self.sources else [s for s in self.sources if s in adapters]
        self.run_report["sources_attempted"] = active_keys

        ingested_dfs = {}

        should_ingest = self.step in ["all", "ingest", "validate"]
        should_features = self.step in ["all", "features"]
        should_validate = self.step in ["all", "validate"]
        should_train = self.step in ["all", "train"]

        # Stage 1: Ingestion & In-Flight Drift Validation
        if should_ingest:
            for key in active_keys:
                adapter = adapters[key]
                logger.info("\n--- [Stage 1: Ingest & Validate] Source: %s ---", adapter.name)
                try:
                    res = adapter.ingest_and_manifest(force_refresh=self.force_refresh)
                    ingested_dfs[key] = res["data"]
                    self.run_report["successful_sources"].append(key)
                    self.run_report["rows_processed"][key] = len(res["data"])

                    if not res["geo_audit"]["is_valid"]:
                        self.run_report["validation_issues"][key] = {
                            "unmatched_counties": res["geo_audit"]["unmatched_entities"]
                        }
                except Exception as e:
                    logger.error("Failed to ingest %s: %s", key, e)
                    self.run_report["failed_sources"].append(key)
                    self.run_report["validation_issues"][key] = {"error": str(e)}
        elif should_features:
            # Load from adapters without re-manifesting if only running feature step
            for key in ["rainfall", "vegetation", "market", "ipc"]:
                ingested_dfs[key] = adapters[key].fetch()

        if should_features and not self.dry_run and all(k in ingested_dfs for k in ["rainfall", "vegetation", "market", "ipc"]):
            # Stage 2: Feature Engineering & Dataset Rebuild
            logger.info("\n--- [Stage 2: Feature Engineering & Dataset Build] ---")
            ipc_monthly = IPCIngestor.expand_to_monthly(ingested_dfs["ipc"])

            feature_df = FeatureEngineer.transform(
                climate_df=ingested_dfs["rainfall"],
                vegetation_df=ingested_dfs["vegetation"],
                market_df=ingested_dfs["market"],
                ipc_df=ipc_monthly
            )

            # Apply date filters if specified
            if self.from_date:
                feature_df = feature_df[feature_df["year"] >= int(self.from_date[:4])]
            if self.to_date:
                feature_df = feature_df[feature_df["year"] <= int(self.to_date[:4])]

            # Validate generated modeling dataset
            is_valid, issues = DataValidator.validate_modeling_dataset(feature_df, raise_error=False)
            model_dataset_path = PROCESSED_DIR / "model_dataset.csv"
            feature_df.to_csv(model_dataset_path, index=False)
            logger.info("Saved updated model dataset: %s (%d rows)", model_dataset_path, len(feature_df))
            self.run_report["model_dataset_rows"] = len(feature_df)

            # Stage 3: Multi-Horizon Forecasting Dataset Rebuild
            logger.info("\n--- [Stage 3: Forecast Dataset Rebuild] ---")
            forecast_df = ForecastFeatureEngineer.build_forecast_dataset(
                input_csv=model_dataset_path,
                output_csv=PROCESSED_DIR / "forecast_dataset.csv"
            )
            self.run_report["forecast_dataset_rows"] = len(forecast_df)

        # Stage 4: Data Quality Scoring & Freshness Audit
        if should_validate:
            logger.info("\n--- [Stage 4: Data Quality Scoring & Freshness Audit] ---")
            dq_report = self._compute_quality_scores(ingested_dfs)
            latest_dq_file = REPORTS_DQ_DIR / "latest.json"
            with open(latest_dq_file, "w", encoding="utf-8") as f:
                json.dump(dq_report, f, indent=2)
            logger.info("Updated data quality report: %s", latest_dq_file)

        # Stage 5: Model Training
        if should_train and not self.dry_run:
            logger.info("\n--- [Stage 5: Baseline and Multi-Horizon Model Training] ---")
            import subprocess
            logger.info("Running baseline model training...")
            subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "train_baseline_models.py")], check=True)
            logger.info("Running forecast model training...")
            subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "train_forecast_models.py")], check=True)
            self.run_report["models_trained"] = True

        # Finalize run report
        self.run_report["end_time"] = datetime.now(timezone.utc).isoformat()
        self.run_report["status"] = "success" if not self.run_report["failed_sources"] else "partial_failure"

        report_file = REPORTS_PIPELINE_DIR / f"{self.run_id}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(self.run_report, f, indent=2)
        logger.info("Saved pipeline run report to: %s", report_file)

        logger.info("=================================================================")
        logger.info("PIPELINE EXECUTION COMPLETED: Status = %s", self.run_report["status"].upper())
        logger.info("=================================================================")

        return self.run_report

    def _compute_quality_scores(self, dfs: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Compute structured health, freshness, and completeness metrics per source."""
        manifest_data = self.manifest_mgr.manifest_data["assets"]
        quality_summary = {
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "sources": {}
        }

        registry_map = {
            "rainfall": "rainfall_chirps",
            "vegetation": "vegetation_modis",
            "market": "market_prices",
            "ipc": "ipc_food_security",
        }

        for short_k, reg_k in registry_map.items():
            records = manifest_data.get(reg_k, [])
            latest_asset = records[-1] if records else {}

            df = dfs.get(short_k, pd.DataFrame())
            completeness = round(float((1.0 - df.isnull().mean().mean()) * 100), 1) if not df.empty else 0.0

            staleness_days = latest_asset.get("staleness_days", 0)
            is_stale = latest_asset.get("is_stale", False)

            if is_stale:
                status = "Warning (Stale)"
            elif latest_asset.get("ingestion_status") == "stale_fallback":
                status = "Warning (Cached Fallback)"
            elif latest_asset.get("ingestion_status") == "failed":
                status = "Failed"
            else:
                status = "Current"

            quality_summary["sources"][reg_k] = {
                "name": latest_asset.get("dataset_name", reg_k),
                "provider": latest_asset.get("source_provider", "Unknown"),
                "status": status,
                "staleness_days": staleness_days,
                "is_stale": is_stale,
                "row_count": len(df),
                "completeness_pct": completeness,
                "date_coverage_end": latest_asset.get("date_coverage_end", "Unknown"),
                "sha256_prefix": latest_asset.get("sha256_checksum", "")[:8]
            }

        return quality_summary


def main():
    parser = argparse.ArgumentParser(description="AgriRisk Kenya End-to-End Pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run data ingestion, feature pipeline, and validation")
    run_parser.add_argument(
        "--step",
        choices=["all", "ingest", "validate", "features", "train"],
        default="all",
        help="Pipeline step to execute (default: all)"
    )
    run_parser.add_argument(
        "--source",
        choices=["all", "rainfall", "vegetation", "market", "ipc"],
        default="all",
        help="Target data source to ingest (default: all)"
    )
    run_parser.add_argument("--force-refresh", action="store_true", help="Force remote fetch and bypass checksum cache")
    run_parser.add_argument("--dry-run", action="store_true", help="Validate and manifest without rebuilding processed datasets")
    run_parser.add_argument("--from-date", type=str, default=None, help="Filter start period (YYYY-MM)")
    run_parser.add_argument("--to-date", type=str, default=None, help="Filter end period (YYYY-MM)")

    args = parser.parse_args()

    if args.command == "run":
        orchestrator = PipelineOrchestrator(
            sources=[args.source],
            force_refresh=args.force_refresh,
            dry_run=args.dry_run,
            from_date=args.from_date,
            to_date=args.to_date,
            step=args.step
        )
        report = orchestrator.execute()
        if report["status"] == "failed":
            sys.exit(1)


if __name__ == "__main__":
    main()
