"""Script to execute time-aware baseline model training, evaluation, and reporting.

Usage:
    uv run python scripts/train_baseline_models.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from agririsk.core.logging import logger
from agririsk.modeling.baseline import BaselineModels, time_aware_train_val_test_split
from agririsk.modeling.evaluator import evaluate_model_predictions
from agririsk.modeling.reporting import ModelReporter
from scripts.build_modeling_dataset import build_dataset



def main():
    logger.info("Initializing baseline modeling pipeline...")
    data_path = PROJECT_ROOT / "data" / "processed" / "model_dataset.csv"

    if not data_path.exists():
        logger.info("Processed dataset not found. Generating model_dataset.csv...")
        df = build_dataset()
    else:
        logger.info("Loading existing modeling dataset from: %s", data_path)
        df = pd.read_csv(data_path)

    # 1. Time-aware Splitting
    splits = time_aware_train_val_test_split(
        df=df,
        train_years=(2019, 2020, 2021, 2022),
        val_years=(2023,),
        test_years=(2024,),
    )

    X_train, y_train = splits["train"]
    X_val, y_val = splits["val"]
    X_test, y_test = splits["test"]

    # 2. Fit Baseline Models
    models = BaselineModels(random_state=42)
    models.fit(X_train, y_train)

    # 3. Predict on Test set
    test_preds = models.predict(X_test)
    test_probs = models.predict_proba(X_test)

    # 4. Predict on Validation set
    val_preds = models.predict(X_val)
    val_probs = models.predict_proba(X_val)

    # 5. Evaluate Metrics
    metrics_summary = {
        "metadata": {
            "task": "Predict acute food insecurity (target_phase3plus == 1)",
            "pilot_counties": sorted(df["county_name"].unique().tolist()),
            "train_years": [2019, 2020, 2021, 2022],
            "validation_years": [2023],
            "test_years": [2024],
            "train_samples": int(len(X_train)),
            "validation_samples": int(len(X_val)),
            "test_samples": int(len(X_test)),
        },
        "test_results": {
            "logistic_regression": evaluate_model_predictions(
                y_true=y_test.values,
                y_pred=test_preds["logistic_regression"],
                y_prob=test_probs["logistic_regression"],
                model_name="Logistic Regression",
            ),
            "random_forest": evaluate_model_predictions(
                y_true=y_test.values,
                y_pred=test_preds["random_forest"],
                y_prob=test_probs["random_forest"],
                model_name="Random Forest",
            ),
        },
        "validation_results": {
            "logistic_regression": evaluate_model_predictions(
                y_true=y_val.values,
                y_pred=val_preds["logistic_regression"],
                y_prob=val_probs["logistic_regression"],
                model_name="Logistic Regression (Val)",
            ),
            "random_forest": evaluate_model_predictions(
                y_true=y_val.values,
                y_pred=val_preds["random_forest"],
                y_prob=val_probs["random_forest"],
                model_name="Random Forest (Val)",
            ),
        }
    }

    # 6. Save Model Artifact and JSON Metrics
    import joblib
    model_artifact_path = PROJECT_ROOT / "artifacts" / "models" / "baseline_models.joblib"
    model_artifact_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(models, model_artifact_path)
    logger.info("Saved model artifact to: %s", model_artifact_path)

    metrics_file = PROJECT_ROOT / "reports" / "model_results" / "baseline_metrics.json"
    ModelReporter.save_metrics_json(metrics_summary, metrics_file)
    logger.info("Saved baseline metrics report to: %s", metrics_file)

    # 7. Generate and Save Figures
    figures_dir = PROJECT_ROOT / "reports" / "figures"
    cm_file = figures_dir / "confusion_matrix.png"
    fi_file = figures_dir / "feature_importance.png"
    dist_file = figures_dir / "risk_probability_distribution.png"

    lr_cm = metrics_summary["test_results"]["logistic_regression"]["confusion_matrix"]["matrix_array"]
    rf_cm = metrics_summary["test_results"]["random_forest"]["confusion_matrix"]["matrix_array"]
    ModelReporter.plot_confusion_matrices(lr_cm, rf_cm, cm_file)
    logger.info("Saved confusion matrix plot to: %s", cm_file)

    rf_mdi = models.rf.feature_importances_
    lr_coef = models.log_reg.coef_[0]
    ModelReporter.plot_feature_importance(models.feature_names, rf_mdi, lr_coef, fi_file)
    logger.info("Saved feature importance plot to: %s", fi_file)

    ModelReporter.plot_risk_probability_distribution(
        y_test=y_test.values,
        rf_probs=test_probs["random_forest"],
        lr_probs=test_probs["logistic_regression"],
        output_path=dist_file,
    )
    logger.info("Saved risk probability distribution plot to: %s", dist_file)

    # Print Terminal Report
    lr_test = metrics_summary["test_results"]["logistic_regression"]
    rf_test = metrics_summary["test_results"]["random_forest"]

    print("\n" + "=" * 65)
    print("AGRIRISK KENYA - BASELINE MODEL EVALUATION RESULTS (TEST 2024)")
    print("=" * 65)
    print(f"{'Metric':<25} | {'Logistic Regression':<18} | {'Random Forest':<18}")
    print("-" * 65)
    print(f"{'Recall (Sensitivity)':<25} | {lr_test['recall']:<18.4f} | {rf_test['recall']:<18.4f}")
    print(f"{'Precision':<25} | {lr_test['precision']:<18.4f} | {rf_test['precision']:<18.4f}")
    print(f"{'F1 Score':<25} | {lr_test['f1']:<18.4f} | {rf_test['f1']:<18.4f}")
    print(f"{'ROC-AUC':<25} | {lr_test['roc_auc']:<18.4f} | {rf_test['roc_auc']:<18.4f}")
    print(f"{'False Negative Rate':<25} | {lr_test['early_warning_diagnostics']['false_negative_rate']:<18.4f} | {rf_test['early_warning_diagnostics']['false_negative_rate']:<18.4f}")
    print("=" * 65)
    print("\nEARLY WARNING DIAGNOSTIC DISCUSSION:")
    print(f"- Logistic Regression: {lr_test['early_warning_diagnostics']['commentary']}")
    print(f"- Random Forest:       {rf_test['early_warning_diagnostics']['commentary']}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
