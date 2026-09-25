"""Unit tests for dataset validation rules."""

from pathlib import Path
import pandas as pd
import pytest
from agririsk.validation.data_validator import DataValidator

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def test_valid_dataset_passes():
    """Verify clean dataset passes validation without issues."""
    data_path = PROJECT_ROOT / "data" / "processed" / "model_dataset.csv"
    assert data_path.exists()

    df = pd.read_csv(data_path)
    is_valid, issues = DataValidator.validate_modeling_dataset(df, raise_error=False)
    assert is_valid
    assert len(issues) == 0


def test_duplicate_row_detection():
    """Verify duplicates on county_name, year, month are flagged."""
    data_path = PROJECT_ROOT / "data" / "processed" / "model_dataset.csv"
    df = pd.read_csv(data_path).iloc[:5].copy()

    # Create a duplicate
    duplicate_row = df.iloc[[0]]
    bad_df = pd.concat([df, duplicate_row], ignore_index=True)

    is_valid, issues = DataValidator.validate_modeling_dataset(bad_df, raise_error=False)
    assert not is_valid
    assert any("duplicate" in i.lower() for i in issues)


def test_invalid_month_detection():
    """Verify invalid month numbers outside [1, 12] are caught."""
    data_path = PROJECT_ROOT / "data" / "processed" / "model_dataset.csv"
    df = pd.read_csv(data_path).iloc[:5].copy()
    df.loc[0, "month"] = 13  # Invalid month

    is_valid, issues = DataValidator.validate_modeling_dataset(df, raise_error=False)
    assert not is_valid
    assert any("month" in i.lower() for i in issues)


def test_missing_county_name_detection():
    """Verify missing or unrecognized county names are caught."""
    data_path = PROJECT_ROOT / "data" / "processed" / "model_dataset.csv"
    df = pd.read_csv(data_path).iloc[:5].copy()
    df.loc[0, "county_name"] = "Atlantis"  # Non-Kenyan county

    is_valid, issues = DataValidator.validate_modeling_dataset(df, raise_error=False)
    assert not is_valid
    assert any("unrecognized" in i.lower() for i in issues)


def test_missing_target_value_detection():
    """Verify missing or invalid target values are caught."""
    data_path = PROJECT_ROOT / "data" / "processed" / "model_dataset.csv"
    df = pd.read_csv(data_path).iloc[:5].copy()
    df.loc[0, "target_phase3plus"] = None

    is_valid, issues = DataValidator.validate_modeling_dataset(df, raise_error=False)
    assert not is_valid
    assert any("target" in i.lower() for i in issues)
