"""Schema drift detection, type enforcement, and value-boundary verification."""

from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np
from agririsk.core.logging import logger


class SchemaDriftError(Exception):
    """Raised when an incoming raw or processed dataset deviates from the expected contract."""
    pass


class DriftDetector:
    """Detects breaking upstream schema changes, type alterations, and anomalous value bounds."""

    @staticmethod
    def validate_schema(
        df: pd.DataFrame,
        dataset_name: str,
        expected_columns: List[str],
        type_constraints: Optional[Dict[str, type]] = None,
        numeric_bounds: Optional[Dict[str, Tuple[float, float]]] = None,
        raise_error: bool = True
    ) -> Tuple[bool, List[str]]:
        """Verify that an incoming dataset adheres strictly to its contractual schema.

        Args:
            df: Incoming DataFrame to inspect.
            dataset_name: Identifier for the source asset.
            expected_columns: List of required column names.
            type_constraints: Optional mapping of column name to required Python type.
            numeric_bounds: Optional mapping of column name to (min_val, max_val).
            raise_error: If True, raises SchemaDriftError upon failure.

        Returns:
            Tuple of (is_valid: bool, issues: List[str]).
        """
        issues = []

        if df.empty:
            issues.append(f"[{dataset_name}] Dataset is completely empty (0 rows).")

        # 1. Missing columns
        missing = [col for col in expected_columns if col not in df.columns]
        if missing:
            issues.append(f"[{dataset_name}] Missing required columns: {missing}")

        # 2. Type constraints
        if type_constraints and not missing:
            for col, expected_type in type_constraints.items():
                if col in df.columns:
                    # Check if column values can be cast or conform
                    non_nulls = df[col].dropna()
                    if not non_nulls.empty:
                        try:
                            if expected_type in (int, "int"):
                                if not pd.api.types.is_integer_dtype(df[col]):
                                    # Check if convertible
                                    pd.to_numeric(non_nulls, downcast="integer")
                            elif expected_type in (float, "float"):
                                if not pd.api.types.is_numeric_dtype(df[col]):
                                    pd.to_numeric(non_nulls)
                        except Exception:
                            issues.append(
                                f"[{dataset_name}] Column '{col}' failed type check for {expected_type}."
                            )

        # 3. Numeric bounds checks
        if numeric_bounds:
            for col, (min_val, max_val) in numeric_bounds.items():
                if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                    below_min = (df[col] < min_val).sum()
                    above_max = (df[col] > max_val).sum()
                    if below_min > 0:
                        issues.append(
                            f"[{dataset_name}] Column '{col}' contains {below_min} values below minimum {min_val}."
                        )
                    if above_max > 0:
                        issues.append(
                            f"[{dataset_name}] Column '{col}' contains {above_max} values above maximum {max_val}."
                        )

        is_valid = len(issues) == 0

        if not is_valid:
            error_msg = f"Schema drift detected in {dataset_name}:\n" + "\n".join(f" - {iss}" for iss in issues)
            logger.error(error_msg)
            if raise_error:
                raise SchemaDriftError(error_msg)

        return is_valid, issues
