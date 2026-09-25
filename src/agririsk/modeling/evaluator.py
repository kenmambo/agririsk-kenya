"""Model evaluation utilities for early-warning food security classifications."""

from typing import Dict, Any
import numpy as np
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)


def evaluate_model_predictions(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray,
    model_name: str = "Model",
) -> Dict[str, Any]:
    """Calculate early-warning classification metrics.

    In humanitarian early warning, a False Negative (failing to alert of an emerging Crisis)
    is substantially more catastrophic than a False Positive (initiating precautionary monitoring).
    Therefore, Recall and False Negative Rate are treated as priority indicators.

    Args:
        y_true: Ground truth binary labels (0 = Phase 1/2, 1 = Phase 3+).
        y_pred: Predicted binary labels.
        y_prob: Predicted probability of positive class (Phase 3+).
        model_name: Identifier for the model.

    Returns:
        Structured evaluation metrics dictionary.
    """
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1])

    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))

    try:
        auc = float(roc_auc_score(y_true, y_prob))
    except Exception:
        auc = 0.5

    actual_positives = fn + tp
    actual_negatives = tn + fp

    fnr = float(fn / actual_positives) if actual_positives > 0 else 0.0
    fpr = float(fp / actual_negatives) if actual_negatives > 0 else 0.0

    return {
        "model_name": model_name,
        "sample_size": int(len(y_true)),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "roc_auc": round(auc, 4),
        "confusion_matrix": {
            "true_negatives": tn,
            "false_positives": fp,
            "false_negatives": fn,
            "true_positives": tp,
            "matrix_array": cm.tolist(),
        },
        "early_warning_diagnostics": {
            "false_negative_rate": round(fnr, 4),
            "false_positive_rate": round(fpr, 4),
            "commentary": (
                f"Recall is {rec*100:.1f}%. Out of {actual_positives} true Crisis periods, "
                f"the model correctly flagged {tp} and missed {fn} (False Negative Rate: {fnr*100:.1f}%)."
            ),
        },
    }
