"""Data validation module for county-month modeling datasets."""

from typing import List, Tuple
import pandas as pd
from agririsk.core.logging import logger
from agririsk.core.constants import COUNTY_NAME_MAP


class DataValidator:
    """Enforces strict data quality and domain constraints on the feature dataset."""

    @classmethod
    def validate_modeling_dataset(
        cls,
        df: pd.DataFrame,
        raise_error: bool = False
    ) -> Tuple[bool, List[str]]:
        """Validate modeling dataset against data quality rules.

        Checks:
        1. Duplicate county-month rows
        2. Impossible dates (year, month)
        3. Missing or unrecognized county names
        4. Invalid IPC phases
        5. Extreme/unexpected indicator values
        6. Missing target values

        Args:
            df: DataFrame to validate.
            raise_error: If True, raises ValueError upon any validation failure.

        Returns:
            Tuple of (is_valid: bool, list_of_issue_messages: List[str]).
        """
        issues: List[str] = []

        # 1. Duplicate county-month check
        duplicates = df[df.duplicated(subset=["county_name", "year", "month"], keep=False)]
        if not duplicates.empty:
            issues.append(
                f"Found {len(duplicates)} duplicate records for county-year-month combinations."
            )

        # 2. Impossible dates
        if not df["month"].between(1, 12).all():
            invalid_months = df[~df["month"].between(1, 12)]["month"].tolist()
            issues.append(f"Found invalid month values: {invalid_months}")

        if not df["year"].between(2000, 2100).all():
            invalid_years = df[~df["year"].between(2000, 2100)]["year"].tolist()
            issues.append(f"Found implausible year values: {invalid_years}")

        # 3. Missing or unrecognized county names
        if df["county_name"].isna().any() or (df["county_name"].str.strip() == "").any():
            issues.append("Found missing or empty county names.")

        valid_canonical_counties = {c["name"] for c in COUNTY_NAME_MAP.values()}
        unrecognized = set(df["county_name"]) - valid_canonical_counties
        if unrecognized:
            issues.append(f"Found unrecognized county names: {list(unrecognized)}")

        # 4. Invalid IPC phases (previous_ipc_phase where not null should be 1-5)
        valid_phases = df["previous_ipc_phase"].dropna()
        if not valid_phases.isin([1, 2, 3, 4, 5]).all():
            invalid = valid_phases[~valid_phases.isin([1, 2, 3, 4, 5])].tolist()
            issues.append(f"Found invalid previous_ipc_phase values outside [1, 5]: {invalid}")

        # 5. Extreme / unexpected physical values
        if (df["rainfall_rolling_3m"].dropna() < 0).any():
            issues.append("Found impossible negative 3-month rolling rainfall values.")

        if (df["maize_price_zscore"].dropna().abs() > 10.0).any():
            issues.append("Found extreme maize price z-scores (|z| > 10.0).")

        # 6. Missing or invalid target values
        if df["target_phase3plus"].isna().any():
            missing_targets = df["target_phase3plus"].isna().sum()
            issues.append(f"Found {missing_targets} records with missing target_phase3plus values.")

        invalid_targets = df[~df["target_phase3plus"].isin([0, 1])]
        if not invalid_targets.empty:
            issues.append("Found target_phase3plus values outside allowed binary set {0, 1}.")

        is_valid = len(issues) == 0

        if not is_valid:
            for issue in issues:
                logger.warning("Data Validation Issue: %s", issue)
            if raise_error:
                raise ValueError("Validation failed with issues:\n" + "\n".join(issues))
        else:
            logger.info("Dataset validation passed successfully: %d records checked.", len(df))

        return is_valid, issues
