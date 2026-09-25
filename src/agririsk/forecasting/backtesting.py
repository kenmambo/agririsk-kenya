"""Rolling-origin temporal backtesting, threshold tuning, and probability calibration."""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix
)
from sklearn.calibration import calibration_curve, CalibratedClassifierCV
from agririsk.core.logging import logger


class RollingOriginSplitter:
    """Expanding-window rolling-origin temporal backtester for multi-horizon forecasting."""

    DEFAULT_FOLDS = [
        {
            "fold_name": "val_2023",
            "train_start": "2019-07-01",
            "train_end": "2022-12-31",
            "eval_start": "2023-01-01",
            "eval_end": "2023-12-31",
            "split_type": "validation"
        },
        {
            "fold_name": "test_2024",
            "train_start": "2019-07-01",
            "train_end": "2023-12-31",
            "eval_start": "2024-01-01",
            "eval_end": "2024-12-31",
            "split_type": "test"
        }
    ]

    def __init__(self, folds: Optional[List[Dict[str, Any]]] = None):
        self.folds = folds or self.DEFAULT_FOLDS

    def split(
        self,
        df: pd.DataFrame,
        horizon: int
    ) -> List[Dict[str, Any]]:
        """Generate chronological train/eval data splits for a specific forecast horizon.

        Args:
            df: Long-format forecast dataset.
            horizon: Forecast horizon (1, 2, or 3).

        Returns:
            List of dictionaries containing fold metadata, train_df, and eval_df.
        """
        # Filter strictly for the specified horizon
        h_df = df[df["horizon_months"] == horizon].copy()
        h_df["observation_date"] = pd.to_datetime(h_df["observation_date"])

        # Filter out rows with unobserved target (e.g. forward projection into future)
        h_df = h_df.dropna(subset=["target_phase3plus"]).copy()

        split_results = []
        for fold in self.folds:
            tr_start = pd.to_datetime(fold["train_start"])
            tr_end = pd.to_datetime(fold["train_end"])
            ev_start = pd.to_datetime(fold["eval_start"])
            ev_end = pd.to_datetime(fold["eval_end"])

            train_mask = (h_df["observation_date"] >= tr_start) & (h_df["observation_date"] <= tr_end)
            eval_mask = (h_df["observation_date"] >= ev_start) & (h_df["observation_date"] <= ev_end)

            train_sub = h_df[train_mask].copy()
            eval_sub = h_df[eval_mask].copy()

            if train_sub.empty or eval_sub.empty:
                logger.warning(
                    "Fold %s for horizon %d produced empty partition (train=%d, eval=%d)",
                    fold["fold_name"], horizon, len(train_sub), len(eval_sub)
                )

            split_results.append({
                "fold_name": fold["fold_name"],
                "split_type": fold["split_type"],
                "horizon": horizon,
                "train_df": train_sub,
                "eval_df": eval_sub,
                "train_count": len(train_sub),
                "eval_count": len(eval_sub)
            })

        return split_results


class ThresholdOptimizer:
    """Evaluates classification thresholds prioritizing early-warning recall and low false-negative rate."""

    @staticmethod
    def evaluate_threshold_grid(
        y_true: np.ndarray,
        y_prob: np.ndarray,
        thresholds: Optional[np.ndarray] = None
    ) -> pd.DataFrame:
        """Compute precision, recall, F1, and false negative rate across candidate probability cutoffs.

        Args:
            y_true: Binary ground-truth labels.
            y_prob: Predicted class 1 risk probabilities.
            thresholds: Array of thresholds to evaluate.

        Returns:
            pd.DataFrame of threshold metrics.
        """
        if thresholds is None:
            thresholds = np.linspace(0.10, 0.90, 17)

        rows = []
        total_positives = int(np.sum(y_true == 1))

        for th in thresholds:
            y_pred = (y_prob >= th).astype(int)

            prec = precision_score(y_true, y_pred, zero_division=0)
            rec = recall_score(y_true, y_pred, zero_division=0)
            f1 = f1_score(y_true, y_pred, zero_division=0)

            # False Negatives
            fn = int(np.sum((y_true == 1) & (y_pred == 0)))
            fn_rate = (fn / total_positives) if total_positives > 0 else 0.0

            rows.append({
                "threshold": round(float(th), 2),
                "precision": round(float(prec), 4),
                "recall": round(float(rec), 4),
                "f1_score": round(float(f1), 4),
                "false_negative_rate": round(float(fn_rate), 4),
                "false_negatives": fn,
            })

        return pd.DataFrame(rows)

    @classmethod
    def select_optimal_threshold(
        cls,
        y_true: np.ndarray,
        y_prob: np.ndarray,
        min_recall: float = 0.80
    ) -> Tuple[float, Dict[str, float]]:
        """Select optimal decision threshold emphasizing early-warning sensitivity.

        Selects the threshold maximizing F1 among those achieving recall >= min_recall.
        Falls back to threshold maximizing F1 if min_recall cannot be satisfied.

        Args:
            y_true: Binary ground-truth labels.
            y_prob: Predicted risk probabilities.
            min_recall: Minimum acceptable recall threshold (default 80%).

        Returns:
            Tuple of (optimal_threshold: float, metrics_at_threshold: dict).
        """
        grid = cls.evaluate_threshold_grid(y_true, y_prob)

        # Candidates meeting minimum recall
        candidates = grid[grid["recall"] >= min_recall]
        if candidates.empty:
            # Fallback: pick maximum recall with highest F1
            best_idx = grid["recall"].idxmax()
        else:
            best_idx = candidates["f1_score"].idxmax()

        best_row = grid.loc[best_idx].to_dict()
        return float(best_row["threshold"]), best_row


class ForecastEvaluator:
    """Comprehensive performance evaluator for multi-horizon food security risk models."""

    @staticmethod
    def compute_all_metrics(
        y_true: np.ndarray,
        y_prob: np.ndarray,
        threshold: float = 0.50
    ) -> Dict[str, Any]:
        """Compute all required classification, calibration, and early-warning metrics.

        Args:
            y_true: Binary ground-truth labels (0 or 1).
            y_prob: Continuous risk probabilities [0.0, 1.0].
            threshold: Decision cutoff threshold.

        Returns:
            Dictionary containing metrics.
        """
        y_true = np.asarray(y_true).astype(int)
        y_prob = np.asarray(y_prob).clip(0.0, 1.0)
        y_pred = (y_prob >= threshold).astype(int)

        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)

        # ROC-AUC & PR-AUC
        try:
            roc_auc = roc_auc_score(y_true, y_prob) if len(np.unique(y_true)) > 1 else np.nan
        except Exception:
            roc_auc = np.nan

        try:
            pr_auc = average_precision_score(y_true, y_prob) if len(np.unique(y_true)) > 1 else np.nan
        except Exception:
            pr_auc = np.nan

        brier = brier_score_loss(y_true, y_prob)

        # False negatives & Confusion Matrix
        cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
        tn, fp, fn, tp = cm.ravel()
        total_p = fn + tp
        fn_rate = (fn / total_p) if total_p > 0 else 0.0

        return {
            "threshold": float(threshold),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1_score": round(float(f1), 4),
            "roc_auc": round(float(roc_auc), 4) if not np.isnan(roc_auc) else None,
            "pr_auc": round(float(pr_auc), 4) if not np.isnan(pr_auc) else None,
            "brier_score": round(float(brier), 4),
            "false_negative_rate": round(float(fn_rate), 4),
            "true_positives": int(tp),
            "false_negatives": int(fn),
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "confusion_matrix": cm.tolist()
        }

    @staticmethod
    def compute_calibration_curve(
        y_true: np.ndarray,
        y_prob: np.ndarray,
        n_bins: int = 5
    ) -> Dict[str, Any]:
        """Compute calibration reliability curve data."""
        y_true = np.asarray(y_true).astype(int)
        y_prob = np.asarray(y_prob).clip(0.0, 1.0)

        try:
            prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=n_bins, strategy="uniform")
            return {
                "prob_true": prob_true.tolist(),
                "prob_pred": prob_pred.tolist(),
                "brier_score": round(float(brier_score_loss(y_true, y_prob)), 4)
            }
        except Exception as e:
            logger.warning("Calibration curve calculation failed: %s", e)
            return {"prob_true": [], "prob_pred": [], "brier_score": np.nan}
