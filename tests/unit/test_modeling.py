"""Unit tests for baseline modeling and evaluation."""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from agririsk.modeling.baseline import BaselineModels, time_aware_train_val_test_split
from agririsk.modeling.evaluator import evaluate_model_predictions
from agririsk.modeling.reporting import ModelReporter

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def test_time_aware_train_val_test_split():
    """Verify chronological split leaves no overlap across train, val, and test years."""
    data_path = PROJECT_ROOT / "data" / "processed" / "model_dataset.csv"
    assert data_path.exists()

    df = pd.read_csv(data_path)
    splits = time_aware_train_val_test_split(
        df=df,
        train_years=(2019, 2020, 2021, 2022),
        val_years=(2023,),
        test_years=(2024,),
    )

    X_train, y_train = splits["train"]
    X_val, y_val = splits["val"]
    X_test, y_test = splits["test"]

    assert len(X_train) > 0
    assert len(X_val) > 0
    assert len(X_test) > 0

    # Ensure no temporal overlap
    assert len(X_train) + len(X_val) + len(X_test) <= len(df)


def test_baseline_models_fit_and_predict():
    """Verify fitting and predicting with Logistic Regression and Random Forest."""
    data_path = PROJECT_ROOT / "data" / "processed" / "model_dataset.csv"
    df = pd.read_csv(data_path)

    splits = time_aware_train_val_test_split(
        df=df,
        train_years=(2019, 2020, 2021, 2022),
        val_years=(2023,),
        test_years=(2024,),
    )
    X_train, y_train = splits["train"]
    X_test, y_test = splits["test"]

    models = BaselineModels(random_state=42)
    models.fit(X_train, y_train)
    assert models.is_fitted

    preds = models.predict(X_test)
    assert "logistic_regression" in preds
    assert "random_forest" in preds
    assert len(preds["random_forest"]) == len(X_test)

    probs = models.predict_proba(X_test)
    assert "random_forest" in probs
    assert (probs["random_forest"] >= 0.0).all() and (probs["random_forest"] <= 1.0).all()


def test_evaluator_metrics_calculation():
    """Verify calculation of precision, recall, F1, ROC-AUC, and false negative diagnostics."""
    y_true = np.array([0, 1, 0, 1, 1, 0])
    y_pred = np.array([0, 1, 0, 0, 1, 0])  # 2 TP, 1 FN, 3 TN, 0 FP
    y_prob = np.array([0.1, 0.9, 0.2, 0.4, 0.85, 0.15])

    metrics = evaluate_model_predictions(y_true, y_pred, y_prob, model_name="TestModel")

    assert metrics["precision"] == 1.0
    assert metrics["recall"] == pytest.approx(2 / 3, rel=1e-3)
    assert metrics["confusion_matrix"]["true_positives"] == 2
    assert metrics["confusion_matrix"]["false_negatives"] == 1
    assert "early_warning_diagnostics" in metrics
    assert metrics["early_warning_diagnostics"]["false_negative_rate"] == pytest.approx(1 / 3, rel=1e-3)


def test_model_reporter_artifacts_creation(tmp_path):
    """Verify export of metrics JSON and visual figures."""
    metrics_file = tmp_path / "metrics.json"
    dummy_metrics = {"test": {"recall": 1.0}}
    ModelReporter.save_metrics_json(dummy_metrics, metrics_file)
    assert metrics_file.exists()

    cm_file = tmp_path / "confusion_matrix.png"
    cm1 = [[10, 2], [1, 8]]
    cm2 = [[11, 1], [0, 9]]
    ModelReporter.plot_confusion_matrices(cm1, cm2, cm_file)
    assert cm_file.exists()
