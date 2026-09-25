"""Training, rolling-origin backtesting, threshold tuning, and calibration for multi-horizon forecasting."""

from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from agririsk.core.logging import logger
from agririsk.forecasting.features import load_forecast_dataset, FORECAST_FEATURE_COLUMNS
from agririsk.forecasting.backtesting import (
    RollingOriginSplitter,
    ThresholdOptimizer,
    ForecastEvaluator
)
from agririsk.forecasting.models import (
    HorizonForecaster,
    get_available_classifiers,
    MODEL_ARTIFACTS_DIR
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports" / "forecasting"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"


def main():
    logger.info("Starting Milestone 4 Multi-Horizon Forecasting Training Pipeline...")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load long-format forecast dataset
    forecast_df = load_forecast_dataset()
    logger.info("Loaded forecast dataset with %d rows", len(forecast_df))

    splitter = RollingOriginSplitter()
    candidate_model_names = ["logistic_regression", "random_forest", "hist_gradient_boosting"]

    all_backtest_records = []
    all_calibration_records = []
    best_forecasters: dict[int, HorizonForecaster] = {}
    horizon_metrics_summary = {}

    for h in (1, 2, 3):
        logger.info("\n=======================================================")
        logger.info("EVALUATING HORIZON %d MONTHS AHEAD (t+%d)", h, h)
        logger.info("=======================================================")

        splits = splitter.split(forecast_df, horizon=h)
        val_split = splits[0]   # Train: 2019-2022, Val: 2023
        test_split = splits[1]  # Train: 2019-2023, Test: 2024

        best_model_name = "random_forest"
        best_val_f1 = -1.0
        model_eval_results = {}

        # A. Compare candidate models on Validation fold
        for m_name in candidate_model_names:
            forecaster = HorizonForecaster(horizon=h, model_name=m_name)
            forecaster.fit(val_split["train_df"], val_split["eval_df"])

            # Evaluate on Validation split
            val_probs = forecaster.predict_proba(val_split["eval_df"])
            val_y = val_split["eval_df"]["target_phase3plus"].values
            val_metrics = ForecastEvaluator.compute_all_metrics(
                val_y, val_probs, threshold=forecaster.optimal_threshold
            )
            val_metrics["model"] = m_name
            val_metrics["horizon"] = h
            val_metrics["split"] = "val_2023"
            all_backtest_records.append(val_metrics)

            logger.info(
                "[%s | h=%d | Val 2023] Recall: %.4f, Prec: %.4f, F1: %.4f, ROC-AUC: %s, Brier: %.4f (th=%.2f)",
                m_name, h, val_metrics["recall"], val_metrics["precision"],
                val_metrics["f1_score"], val_metrics["roc_auc"], val_metrics["brier_score"],
                forecaster.optimal_threshold
            )

            # Model selection criterion: Prioritize F1 and Recall
            if val_metrics["f1_score"] > best_val_f1 or (val_metrics["f1_score"] == best_val_f1 and val_metrics["recall"] >= 0.8):
                best_val_f1 = val_metrics["f1_score"]
                best_model_name = m_name

        logger.info("--> Selected best model for Horizon %d: %s (Val F1: %.4f)", h, best_model_name, best_val_f1)

        # B. Train selected best model on expanding window through 2023 and evaluate on 2024 Test holdout
        best_forecaster = HorizonForecaster(horizon=h, model_name=best_model_name)
        # Use val_split eval_df for threshold calibration, train on full pre-2024
        best_forecaster.fit(test_split["train_df"], val_split["eval_df"])
        best_forecaster.save()
        best_forecasters[h] = best_forecaster

        # Test set evaluation (Holdout 2024)
        test_y = test_split["eval_df"]["target_phase3plus"].values
        test_probs = best_forecaster.predict_proba(test_split["eval_df"])
        test_metrics = ForecastEvaluator.compute_all_metrics(
            test_y, test_probs, threshold=best_forecaster.optimal_threshold
        )
        test_metrics["model"] = best_model_name
        test_metrics["horizon"] = h
        test_metrics["split"] = "test_2024"
        all_backtest_records.append(test_metrics)

        # Calibration curve data
        calib_data = ForecastEvaluator.compute_calibration_curve(test_y, test_probs, n_bins=5)
        for p_pred, p_true in zip(calib_data["prob_pred"], calib_data["prob_true"]):
            all_calibration_records.append({
                "horizon": h,
                "model": best_model_name,
                "pred_prob_bin": round(p_pred, 4),
                "true_prob_bin": round(p_true, 4),
                "brier_score": calib_data["brier_score"]
            })

        logger.info(
            "===> [TEST 2024 HOLDOUT | h=%d | %s] Recall: %.4f, Prec: %.4f, F1: %.4f, ROC-AUC: %s, Brier: %.4f",
            h, best_model_name, test_metrics["recall"], test_metrics["precision"],
            test_metrics["f1_score"], test_metrics["roc_auc"], test_metrics["brier_score"]
        )

        # Save individual horizon JSON report
        h_summary = {
            "horizon_months": h,
            "best_model": best_model_name,
            "optimal_threshold": best_forecaster.optimal_threshold,
            "threshold_selection_rationale": "Max F1 subject to min recall >= 0.80 on validation partition",
            "validation_2023_metrics": [r for r in all_backtest_records if r["horizon"] == h and r["split"] == "val_2023"],
            "test_2024_metrics": test_metrics,
            "calibration": calib_data,
        }
        horizon_metrics_summary[f"horizon_{h}"] = h_summary
        h_file = REPORTS_DIR / f"horizon_{h}_metrics.json"
        with open(h_file, "w", encoding="utf-8") as f:
            json.dump(h_summary, f, indent=2)
        logger.info("Saved metrics JSON to %s", h_file)

    # 2. Save Aggregate CSV Reports
    backtest_df = pd.DataFrame(all_backtest_records)
    backtest_csv = REPORTS_DIR / "backtest_results.csv"
    backtest_df.to_csv(backtest_csv, index=False)
    logger.info("Saved backtest results table to %s", backtest_csv)

    calib_df = pd.DataFrame(all_calibration_records)
    calib_csv = REPORTS_DIR / "calibration_results.csv"
    calib_df.to_csv(calib_csv, index=False)
    logger.info("Saved calibration results table to %s", calib_csv)

    # 3. Generate Diagnostic Visual Figures
    _plot_forecast_performance_by_horizon(horizon_metrics_summary)
    _plot_recall_by_horizon(horizon_metrics_summary)
    for h in (1, 2, 3):
        _plot_calibration_curve(horizon_metrics_summary[f"horizon_{h}"], h)

    logger.info("All Milestone 4 training, backtesting, and visualization tasks completed successfully!")


def _plot_forecast_performance_by_horizon(summary: dict):
    """Plot precision, recall, F1, and ROC-AUC across forecast horizons."""
    horizons = [1, 2, 3]
    f1s = [summary[f"horizon_{h}"]["test_2024_metrics"]["f1_score"] for h in horizons]
    recalls = [summary[f"horizon_{h}"]["test_2024_metrics"]["recall"] for h in horizons]
    precisions = [summary[f"horizon_{h}"]["test_2024_metrics"]["precision"] for h in horizons]
    rocs = [summary[f"horizon_{h}"]["test_2024_metrics"]["roc_auc"] or 0.0 for h in horizons]

    x = np.arange(len(horizons))
    width = 0.2

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    ax.bar(x - 1.5 * width, recalls, width, label="Recall (Sensitivity)", color="#dc2626")
    ax.bar(x - 0.5 * width, precisions, width, label="Precision", color="#2563eb")
    ax.bar(x + 0.5 * width, f1s, width, label="F1 Score", color="#16a34a")
    ax.bar(x + 1.5 * width, rocs, width, label="ROC-AUC", color="#d97706")

    ax.set_xlabel("Forecast Horizon (Months Ahead)", fontweight="bold")
    ax.set_ylabel("Score", fontweight="bold")
    ax.set_title("AgriRisk Kenya - Test Set Performance by Forecast Horizon (2024 Holdout)", fontweight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(["1-Month (t+1)", "2-Month (t+2)", "3-Month (t+3)"])
    ax.set_ylim(0, 1.1)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.legend(loc="lower right")

    plt.tight_layout()
    out_file = FIGURES_DIR / "forecast_performance_by_horizon.png"
    plt.savefig(out_file)
    plt.close()
    logger.info("Saved %s", out_file)


def _plot_recall_by_horizon(summary: dict):
    """Plot early-warning recall and false-negative rate progression."""
    horizons = [1, 2, 3]
    recalls = [summary[f"horizon_{h}"]["test_2024_metrics"]["recall"] * 100 for h in horizons]
    fn_rates = [summary[f"horizon_{h}"]["test_2024_metrics"]["false_negative_rate"] * 100 for h in horizons]

    fig, ax = plt.subplots(figsize=(7, 4), dpi=150)
    ax.plot(["1 Month", "2 Months", "3 Months"], recalls, marker="o", linewidth=2.5, color="#16a34a", label="Recall (% Crises Detected)")
    ax.plot(["1 Month", "2 Months", "3 Months"], fn_rates, marker="s", linewidth=2.5, color="#dc2626", label="False Negative Rate (% Missed)")

    ax.set_xlabel("Prediction Horizon", fontweight="bold")
    ax.set_ylabel("Percentage (%)", fontweight="bold")
    ax.set_title("Early-Warning Sensitivity vs False Negative Rate by Horizon", fontweight="bold", pad=12)
    ax.set_ylim(-5, 105)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="center right")

    plt.tight_layout()
    out_file = FIGURES_DIR / "recall_by_horizon.png"
    plt.savefig(out_file)
    plt.close()
    logger.info("Saved %s", out_file)


def _plot_calibration_curve(h_summary: dict, horizon: int):
    """Plot reliability diagram for probability calibration."""
    calib = h_summary["calibration"]
    pred = calib.get("prob_pred", [])
    true = calib.get("prob_true", [])
    brier = calib.get("brier_score", 0.0)

    fig, ax = plt.subplots(figsize=(5.5, 4.5), dpi=150)
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Perfectly Calibrated")
    if pred and true:
        ax.plot(pred, true, marker="o", linewidth=2, color="#2563eb", label=f"Model (Brier={brier:.4f})")

    ax.set_xlabel("Mean Predicted Probability", fontweight="bold")
    ax.set_ylabel("Fraction of Positives", fontweight="bold")
    ax.set_title(f"Probability Calibration: Horizon {horizon} Month Ahead", fontweight="bold", pad=12)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="upper left")

    plt.tight_layout()
    out_file = FIGURES_DIR / f"calibration_curve_h{horizon}.png"
    plt.savefig(out_file)
    plt.close()
    logger.info("Saved %s", out_file)


if __name__ == "__main__":
    main()
