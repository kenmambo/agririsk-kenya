"""Script to build, validate, and export the county-month modeling dataset.

Outputs:
    data/processed/model_dataset.csv
"""

import sys
from pathlib import Path
import pandas as pd
from agririsk.core.logging import logger
from agririsk.core.config import settings
from agririsk.ingestion.ipc_ingestor import IPCIngestor
from agririsk.ingestion.climate_ingestor import ClimateIngestor
from agririsk.ingestion.vegetation_ingestor import VegetationIngestor
from agririsk.ingestion.market_ingestor import MarketIngestor
from agririsk.features.engineering import FeatureEngineer
from agririsk.validation.data_validator import DataValidator

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def build_dataset() -> pd.DataFrame:
    """Execute end-to-end data ingestion, harmonization, feature engineering, and validation."""
    raw_dir = PROJECT_ROOT / "data" / "raw"
    processed_dir = PROJECT_ROOT / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    # 1. Ingest Raw Streams
    ipc_file = raw_dir / "ipc" / "kenya_asal_ipc_historical.csv"
    climate_file = raw_dir / "climate" / "kenya_asal_monthly_rainfall.csv"
    veg_file = raw_dir / "vegetation" / "kenya_asal_monthly_ndvi.csv"
    market_file = raw_dir / "market" / "kenya_asal_maize_prices.csv"

    logger.info("Starting ingestion of raw pilot datasets...")
    ipc_raw = IPCIngestor.load_from_csv(ipc_file)
    ipc_monthly = IPCIngestor.expand_to_monthly(ipc_raw)

    climate_df = ClimateIngestor.load_from_csv(climate_file)
    veg_df = VegetationIngestor.load_from_csv(veg_file)
    market_df = MarketIngestor.load_from_csv(market_file, target_commodity="Maize")

    # 2. Feature Engineering
    feature_df = FeatureEngineer.transform(
        climate_df=climate_df,
        vegetation_df=veg_df,
        market_df=market_df,
        ipc_df=ipc_monthly,
    )

    # 3. Validation
    logger.info("Validating generated feature dataset...")
    is_valid, issues = DataValidator.validate_modeling_dataset(feature_df, raise_error=True)

    # 4. Save to processed directory
    output_path = processed_dir / "model_dataset.csv"
    feature_df.to_csv(output_path, index=False)
    logger.info("Successfully exported modeling dataset to: %s (%d rows)", output_path, len(feature_df))

    # Summary report
    print("\n" + "=" * 60)
    print("AGRIRISK KENYA - MODELING DATASET GENERATED")
    print("=" * 60)
    print(f"Destination: {output_path}")
    print(f"Total Rows:  {len(feature_df)}")
    print(f"Counties:    {feature_df['county_name'].unique().tolist()}")
    print(f"Year Range:  {feature_df['year'].min()} - {feature_df['year'].max()}")
    print("\nTarget Distribution (target_phase3plus):")
    print(feature_df["target_phase3plus"].value_counts(normalize=True).round(3).to_dict())
    print("=" * 60 + "\n")

    return feature_df


if __name__ == "__main__":
    try:
        build_dataset()
    except Exception as e:
        logger.error("Dataset generation failed: %s", e, exc_info=True)
        sys.exit(1)
