"""Uncertainty estimation and temporal block bootstrap evaluation for early-warning risk forecasting.

Provides:
1. BlockBootstrapEvaluator: Generates 95% confidence intervals for performance metrics
   respecting the temporal structure (resampling time blocks rather than i.i.d. rows).
2. EnsembleUncertaintyEstimator: Produces lower and upper prediction uncertainty bounds
   from a committee of models or bootstrap replicates.
"""

from typing import Dict, Any, List, Tuple, Optional, Callable
import numpy as np
import pandas as pd
from sklearn.metrics import (
    recall_score,
    precision_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    brier_score_loss
)
from agririsk.core.logging import logger


class BlockBootstrapEvaluator:
    """Block bootstrap evaluator for time-series panel metrics confidence intervals."""

    def __init__(self, n_bootstraps: int = 500, random_state: int = 42, threshold: float = 0.5):
        self.n_bootstraps = n_bootstraps
        self.random_state = random_state
        self.threshold = threshold

    def evaluate_with_ci(
        self,
        df: pd.DataFrame,
        y_true_col: str,
        y_prob_col: str,
        block_col: str = "observation_date"
    ) -> Dict[str, Dict[str, float]]:
        """Compute performance metrics along with 95% block-bootstrap confidence intervals.

        Args:
            df: Evaluation DataFrame containing ground truth, predictions, and time block.
            y_true_col: Binary ground-truth target column.
            y_prob_col: Predicted probability column.
            block_col: Temporal grouping variable (e.g. observation_date or year_month).

        Returns:
            Dictionary mapping metric name to {'estimate', 'ci_lower', 'ci_upper', 'std'}.
        """
        rng = np.random.RandomState(self.random_state)
        clean_df = df.dropna(subset=[y_true_col, y_prob_col, block_col]).copy()

        unique_blocks = np.array(clean_df[block_col].unique())
        n_blocks = len(unique_blocks)

        if n_blocks < 2:
            logger.warning("Fewer than 2 temporal blocks available for block bootstrap.")
            # Fall back to single-point estimate
            return self._compute_single_estimate(clean_df, y_true_col, y_prob_col)

        # Baseline point estimates on full evaluation set
        point_estimates = self._compute_metrics(
            clean_df[y_true_col].values,
            clean_df[y_prob_col].values
        )

        bootstrap_metrics: Dict[str, List[float]] = {k: [] for k in point_estimates.keys()}

        # Group data by time block for fast sampling
        block_groups = {b: group for b, group in clean_df.groupby(block_col)}

        for _ in range(self.n_bootstraps):
            sampled_blocks = rng.choice(unique_blocks, size=n_blocks, replace=True)
            resampled_df = pd.concat([block_groups[b] for b in sampled_blocks], ignore_index=True)

            y_t = resampled_df[y_true_col].values
            y_p = resampled_df[y_prob_col].values

            # Skip iteration if resample has only one class (cannot compute ROC-AUC)
            if len(np.unique(y_t)) < 2:
                continue

            metrics = self._compute_metrics(y_t, y_p)
            for k, val in metrics.items():
                if not np.isnan(val):
                    bootstrap_metrics[k].append(val)

        results: Dict[str, Dict[str, float]] = {}
        for k, pt_val in point_estimates.items():
            vals = bootstrap_metrics[k]
            if len(vals) >= 10:
                ci_low = float(np.percentile(vals, 2.5))
                ci_high = float(np.percentile(vals, 97.5))
                std_err = float(np.std(vals))
            else:
                ci_low = pt_val
                ci_high = pt_val
                std_err = 0.0

            results[k] = {
                "estimate": round(float(pt_val), 4),
                "ci_lower": round(ci_low, 4),
                "ci_upper": round(ci_high, 4),
                "std": round(std_err, 4)
            }

        return results

    def _compute_metrics(self, y_true: np.ndarray, y_prob: np.ndarray) -> Dict[str, float]:
        """Compute standard evaluation metrics for binary classification."""
        y_pred = (y_prob >= self.threshold).astype(int)

        recall = recall_score(y_true, y_pred, zero_division=0)
        prec = precision_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        brier = brier_score_loss(y_true, y_prob)
        fnr = 1.0 - recall

        try:
            roc_auc = roc_auc_score(y_true, y_prob) if len(np.unique(y_true)) > 1 else np.nan
        except Exception:
            roc_auc = np.nan

        try:
            pr_auc = average_precision_score(y_true, y_prob) if len(np.unique(y_true)) > 1 else np.nan
        except Exception:
            pr_auc = np.nan

        return {
            "recall": float(recall),
            "precision": float(prec),
            "f1": float(f1),
            "roc_auc": float(roc_auc) if not np.isnan(roc_auc) else 0.5,
            "pr_auc": float(pr_auc) if not np.isnan(pr_auc) else 0.0,
            "brier_score": float(brier),
            "false_negative_rate": float(fnr)
        }

    def _compute_single_estimate(self, df: pd.DataFrame, y_true_col: str, y_prob_col: str) -> Dict[str, Dict[str, float]]:
        """Fallback point estimates when bootstrapping is not feasible."""
        pt = self._compute_metrics(df[y_true_col].values, df[y_prob_col].values)
        return {k: {"estimate": v, "ci_lower": v, "ci_upper": v, "std": 0.0} for k, v in pt.items()}


class EnsembleUncertaintyEstimator:
    """Computes prediction uncertainty intervals across an ensemble of heterogeneous classifiers."""

    def __init__(self, models: Dict[str, Any]):
        self.models = models

    def predict_with_uncertainty(self, X: pd.DataFrame) -> pd.DataFrame:
        """Generate point probabilities and epistemic model uncertainty bounds.

        Args:
            X: Predictor DataFrame.

        Returns:
            DataFrame containing:
            - risk_probability (mean ensemble probability)
            - lower_uncertainty_bound (minimum or lower empirical quantile)
            - upper_uncertainty_bound (maximum or upper empirical quantile)
            - uncertainty_spread (upper - lower)
            - model_agreement_std (standard deviation across models)
        """
        all_probs = []
        for name, m in self.models.items():
            try:
                if hasattr(m, "predict_proba"):
                    probs = m.predict_proba(X)[:, 1]
                else:
                    probs = m.predict(X)
                all_probs.append(probs)
            except Exception as e:
                logger.warning("Model %s failed in ensemble uncertainty: %s", name, e)

        if not all_probs:
            raise RuntimeError("No candidate models produced valid probabilities.")

        prob_matrix = np.column_stack(all_probs)  # Shape: (N, num_models)

        mean_prob = np.mean(prob_matrix, axis=1)
        min_prob = np.min(prob_matrix, axis=1)
        max_prob = np.max(prob_matrix, axis=1)
        std_prob = np.std(prob_matrix, axis=1)

        # 90% empirical bounds or [min, max]
        lower_bound = np.clip(mean_prob - 1.645 * std_prob, 0.0, 1.0)
        upper_bound = np.clip(mean_prob + 1.645 * std_prob, 0.0, 1.0)

        # Guarantee bounds encompass min/max
        lower_bound = np.minimum(lower_bound, min_prob)
        upper_bound = np.maximum(upper_bound, max_prob)

        spread = upper_bound - lower_bound

        return pd.DataFrame({
            "risk_probability": np.round(mean_prob, 4),
            "lower_uncertainty_bound": np.round(lower_bound, 4),
            "upper_uncertainty_bound": np.round(upper_bound, 4),
            "uncertainty_spread": np.round(spread, 4),
            "model_agreement_std": np.round(std_prob, 4)
        }, index=X.index)
