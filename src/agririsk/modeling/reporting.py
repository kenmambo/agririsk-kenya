"""Reporting and visualization generator for baseline model results."""

import json
from pathlib import Path
from typing import Dict, Any, List
import matplotlib
matplotlib.use("Agg")  # Headless backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class ModelReporter:
    """Generates evaluation metric JSON artifacts and diagnostic visualization figures."""

    @staticmethod
    def save_metrics_json(metrics: Dict[str, Any], filepath: Path) -> None:
        """Serialize metrics dictionary to JSON."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)

    @staticmethod
    def plot_confusion_matrices(
        log_reg_cm: List[List[int]],
        rf_cm: List[List[int]],
        output_path: Path
    ) -> None:
        """Plot side-by-side confusion matrices for both baseline models."""
        fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), constrained_layout=True)

        classes = ["Phase 1/2\n(Non-Crisis)", "Phase 3+\n(Crisis)"]

        models_data = [
            ("Logistic Regression", log_reg_cm, axes[0]),
            ("Random Forest", rf_cm, axes[1]),
        ]

        for title, cm_array, ax in models_data:
            cm = np.array(cm_array)
            im = ax.imshow(cm, interpolation="nearest", cmap="Blues")
            ax.set_title(title, fontsize=12, fontweight="bold")
            fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

            tick_marks = np.arange(len(classes))
            ax.set_xticks(tick_marks)
            ax.set_xticklabels(classes, fontsize=10)
            ax.set_yticks(tick_marks)
            ax.set_yticklabels(classes, fontsize=10)

            thresh = cm.max() / 2.0
            for i in range(cm.shape[0]):
                for j in range(cm.shape[1]):
                    ax.text(
                        j, i, format(cm[i, j], "d"),
                        ha="center", va="center",
                        color="white" if cm[i, j] > thresh else "black",
                        fontsize=14, fontweight="bold"
                    )

            ax.set_ylabel("True Ground Truth Label", fontsize=11)
            ax.set_xlabel("Model Predicted Label", fontsize=11)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=200)
        plt.close(fig)

    @staticmethod
    def plot_feature_importance(
        feature_names: List[str],
        rf_importances: np.ndarray,
        log_reg_coefs: np.ndarray,
        output_path: Path
    ) -> None:
        """Plot Random Forest feature importance and Logistic Regression standardized coefficients."""
        fig, axes = plt.subplots(1, 2, figsize=(12, 5.5), constrained_layout=True)

        # 1. Random Forest MDI Feature Importance
        rf_df = pd.DataFrame({"feature": feature_names, "importance": rf_importances})
        rf_df = rf_df.sort_values(by="importance", ascending=True)

        axes[0].barh(rf_df["feature"], rf_df["importance"], color="#2b5c8f")
        axes[0].set_title("Random Forest - Feature Importance (MDI)", fontsize=11, fontweight="bold")
        axes[0].set_xlabel("Relative Importance Score", fontsize=10)
        axes[0].grid(axis="x", linestyle="--", alpha=0.6)

        # 2. Logistic Regression Coefficients
        lr_df = pd.DataFrame({"feature": feature_names, "coefficient": log_reg_coefs})
        lr_df = lr_df.sort_values(by="coefficient", ascending=True)

        colors = ["#d95f02" if c > 0 else "#1b9e77" for c in lr_df["coefficient"]]
        axes[1].barh(lr_df["feature"], lr_df["coefficient"], color=colors)
        axes[1].axvline(0, color="black", linestyle="-", linewidth=0.8)
        axes[1].set_title("Logistic Regression - Standardized Coefficients", fontsize=11, fontweight="bold")
        axes[1].set_xlabel("Coefficient Magnitude (Log-Odds Impact)", fontsize=10)
        axes[1].grid(axis="x", linestyle="--", alpha=0.6)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=200)
        plt.close(fig)

    @staticmethod
    def plot_risk_probability_distribution(
        y_test: np.ndarray,
        rf_probs: np.ndarray,
        lr_probs: np.ndarray,
        output_path: Path
    ) -> None:
        """Plot predicted risk probability distribution for Actual Crisis vs Non-Crisis classes."""
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), constrained_layout=True)

        data = [
            ("Logistic Regression", lr_probs, axes[0]),
            ("Random Forest", rf_probs, axes[1]),
        ]

        for title, probs, ax in data:
            non_crisis_probs = probs[y_test == 0]
            crisis_probs = probs[y_test == 1]

            ax.hist(
                non_crisis_probs, bins=10, alpha=0.65, label="Actual Phase 1/2 (Non-Crisis)",
                color="#2ca02c", edgecolor="black", range=(0, 1)
            )
            ax.hist(
                crisis_probs, bins=10, alpha=0.65, label="Actual Phase 3+ (Crisis)",
                color="#d62728", edgecolor="black", range=(0, 1)
            )

            ax.axvline(0.5, color="black", linestyle="--", label="Decision Threshold (0.5)")
            ax.set_title(f"{title}\nPredicted Risk Probability Distribution", fontsize=11, fontweight="bold")
            ax.set_xlabel("Predicted Probability of Phase 3+ Crisis", fontsize=10)
            ax.set_ylabel("Count of County-Months", fontsize=10)
            ax.legend(fontsize=9, loc="upper right")
            ax.grid(axis="y", linestyle="--", alpha=0.6)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=200)
        plt.close(fig)
