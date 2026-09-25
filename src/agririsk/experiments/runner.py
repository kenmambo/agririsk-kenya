"""Experiment runner, rolling-origin evaluation, feature ablations, and experiment registry."""

from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import json
import uuid
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import (
    recall_score,
    precision_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix
)

from agririsk.core.logging import logger
from agririsk.modeling.benchmarks import PersistenceBaseline, HistoricalFrequencyBaseline, SeasonalBaseline
from agririsk.experiments.uncertainty import BlockBootstrapEvaluator, EnsembleUncertaintyEstimator
from agririsk.experiments.explainability import ModelExplainer

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
EXPERIMENTS_DIR = PROJECT_ROOT / "reports" / "experiments"
ANALYSIS_DIR = PROJECT_ROOT / "reports" / "analysis"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"


# Standard Feature Groups for Ablation
FEATURE_GROUPS = {
    "CLIMATE": [
        "rainfall_anomaly_lag1", "rainfall_anomaly_lag2", "rainfall_anomaly_lag3",
        "rainfall_rolling_3m", "rainfall_rolling_6m", "consecutive_dry_months"
    ],
    "VEGETATION": [
        "ndvi_anomaly_lag1", "ndvi_anomaly_lag2", "ndvi_anomaly_lag3",
        "ndvi_trend_3m", "ndvi_trend_6m"
    ],
    "MARKET": [
        "maize_price_change_1m", "maize_price_change_3m", "maize_price_change_6m",
        "maize_price_zscore"
    ],
    "HISTORICAL_RISK": [
        "previous_ipc_phase", "ipc_phase_lag2", "ipc_phase_lag3"
    ],
    "SPATIAL": [
        "neighbour_mean_rainfall_anomaly", "neighbour_mean_ndvi_anomaly",
        "neighbour_mean_price_change", "neighbour_mean_previous_risk",
        "number_of_high_risk_neighbours"
    ],
    "SEASONALITY": [
        "month", "quarter", "is_long_rains", "is_short_rains", "is_arid"
    ]
}


class CalibratedEnsemble:
    """Ensemble combining Logistic Regression, Random Forest, and Gradient Boosting."""

    def __init__(self, random_state: int = 42):
        self.imputer = SimpleImputer(strategy="median")
        self.scaler = StandardScaler()
        self.lr = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=random_state)
        self.rf = RandomForestClassifier(n_estimators=100, max_depth=5, class_weight="balanced", random_state=random_state)
        self.hgb = HistGradientBoostingClassifier(max_iter=100, max_depth=4, class_weight="balanced", random_state=random_state)
        self.classes_ = np.array([0, 1])

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "CalibratedEnsemble":
        X_imp = self.imputer.fit_transform(X)
        X_scaled = self.scaler.fit_transform(X_imp)
        self.lr.fit(X_scaled, y)
        self.rf.fit(X_imp, y)
        self.hgb.fit(X, y)
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        X_imp = self.imputer.transform(X)
        X_scaled = self.scaler.transform(X_imp)
        p_lr = self.lr.predict_proba(X_scaled)[:, 1]
        p_rf = self.rf.predict_proba(X_imp)[:, 1]
        p_hgb = self.hgb.predict_proba(X)[:, 1]
        p_ens = (p_lr * 0.2) + (p_rf * 0.4) + (p_hgb * 0.4)
        p0 = 1.0 - p_ens
        return np.column_stack([p0, p_ens])

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        probs = self.predict_proba(X)[:, 1]
        return (probs >= 0.5).astype(int)


class ExperimentRunner:
    """Orchestrates comprehensive multi-model benchmarking, ablations, and error auditing."""

    def __init__(self, forecast_df: pd.DataFrame, random_state: int = 42):
        self.forecast_df = forecast_df.copy()
        self.random_state = random_state
        EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
        ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
        FIGURES_DIR.mkdir(parents=True, exist_ok=True)

        self.registry_csv = EXPERIMENTS_DIR / "experiment_registry.csv"

    def get_candidate_models(self) -> Dict[str, Any]:
        """Instantiate candidate benchmark and advanced models."""
        return {
            "persistence": PersistenceBaseline(),
            "historical_frequency": HistoricalFrequencyBaseline(),
            "seasonal_baseline": SeasonalBaseline(),
            "logistic_regression": LogisticRegression(
                max_iter=1000, class_weight="balanced", random_state=self.random_state
            ),
            "random_forest": RandomForestClassifier(
                n_estimators=100, max_depth=5, class_weight="balanced", random_state=self.random_state
            ),
            "hist_gradient_boosting": HistGradientBoostingClassifier(
                max_iter=100, max_depth=4, class_weight="balanced", random_state=self.random_state
            ),
            "calibrated_ensemble": CalibratedEnsemble(random_state=self.random_state)
        }

    def run_all_experiments(self) -> Dict[str, Any]:
        """Execute full suite: benchmarks, model comparison, ablations, stability, and errors."""
        logger.info("==================================================================")
        logger.info("STARTING MILESTONE 6 RESEARCH EXPERIMENT SUITE")
        logger.info("==================================================================")

        all_features = []
        for grp in FEATURE_GROUPS.values():
            all_features.extend([f for f in grp if f in self.forecast_df.columns])

        # Define 2 expanding temporal folds
        folds = [
            {
                "fold_name": "fold1_drought_peak",
                "train_end": "2022-12-31",
                "val_end": "2023-12-31",
                "test_start": "2023-01-01",
                "test_end": "2023-12-31"
            },
            {
                "fold_name": "fold2_recovery_transition",
                "train_end": "2023-12-31",
                "val_end": "2024-12-31",
                "test_start": "2024-01-01",
                "test_end": "2024-12-31"
            }
        ]

        registry_entries = []
        detailed_results = {}
        all_test_predictions = []

        # 1. Main Model Comparison across Horizons and Folds
        for h in [1, 2, 3]:
            h_df = self.forecast_df[self.forecast_df["horizon_months"] == h].dropna(subset=["target_phase3plus"]).copy()
            h_df["observation_date"] = pd.to_datetime(h_df["observation_date"])

            for fold in folds:
                train_mask = h_df["observation_date"] <= pd.to_datetime(fold["train_end"])
                test_mask = (h_df["observation_date"] >= pd.to_datetime(fold["test_start"])) & (h_df["observation_date"] <= pd.to_datetime(fold["test_end"]))

                train_df = h_df[train_mask].copy()
                test_df = h_df[test_mask].copy()

                if train_df.empty or test_df.empty:
                    continue

                candidate_models = self.get_candidate_models()
                for model_name, model in candidate_models.items():
                    exp_id = f"exp_{h}m_{fold['fold_name']}_{model_name}_{uuid.uuid4().hex[:6]}"

                    # Preprocessing
                    X_tr = train_df[all_features].copy()
                    y_tr = train_df["target_phase3plus"].astype(int)
                    X_te = test_df[all_features].copy()
                    y_te = test_df["target_phase3plus"].astype(int)

                    imputer = SimpleImputer(strategy="median")
                    X_tr_imp = pd.DataFrame(imputer.fit_transform(X_tr), columns=all_features, index=X_tr.index)
                    X_te_imp = pd.DataFrame(imputer.transform(X_te), columns=all_features, index=X_te.index)

                    if model_name == "logistic_regression":
                        scaler = StandardScaler()
                        X_tr_fit = pd.DataFrame(scaler.fit_transform(X_tr_imp), columns=all_features, index=X_tr.index)
                        X_te_eval = pd.DataFrame(scaler.transform(X_te_imp), columns=all_features, index=X_te.index)
                    elif model_name in ["persistence", "historical_frequency", "seasonal_baseline"]:
                        X_tr_fit = X_tr
                        X_te_eval = X_te
                    else:
                        X_tr_fit = X_tr_imp
                        X_te_eval = X_te_imp

                    # Fit
                    if hasattr(model, "fit"):
                        model.fit(X_tr_fit, y_tr)

                    # Predict
                    if hasattr(model, "predict_proba"):
                        y_prob = model.predict_proba(X_te_eval)[:, 1]
                    else:
                        y_prob = model.predict(X_te_eval).astype(float)

                    y_pred = (y_prob >= 0.5).astype(int)

                    # Metrics
                    recall = float(recall_score(y_te, y_pred, zero_division=0))
                    prec = float(precision_score(y_te, y_pred, zero_division=0))
                    f1 = float(f1_score(y_te, y_pred, zero_division=0))
                    brier = float(brier_score_loss(y_te, y_prob))
                    fnr = 1.0 - recall

                    try:
                        roc = float(roc_auc_score(y_te, y_prob)) if len(np.unique(y_te)) > 1 else 0.5
                    except Exception:
                        roc = 0.5

                    try:
                        pr_auc = float(average_precision_score(y_te, y_prob)) if len(np.unique(y_te)) > 1 else 0.0
                    except Exception:
                        pr_auc = 0.0

                    entry = {
                        "experiment_id": exp_id,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "forecast_horizon": h,
                        "fold_name": fold["fold_name"],
                        "model_name": model_name,
                        "feature_set": "all_features",
                        "num_features": len(all_features),
                        "train_samples": len(train_df),
                        "test_samples": len(test_df),
                        "recall": round(recall, 4),
                        "precision": round(prec, 4),
                        "f1_score": round(f1, 4),
                        "roc_auc": round(roc, 4),
                        "pr_auc": round(pr_auc, 4),
                        "brier_score": round(brier, 4),
                        "false_negative_rate": round(fnr, 4)
                    }
                    registry_entries.append(entry)

                    # Save predictions for error and county audit (Fold 2 holdout 2024)
                    if fold["fold_name"] == "fold2_recovery_transition" and model_name == "random_forest":
                        for i, (_, row) in enumerate(test_df.iterrows()):
                            all_test_predictions.append({
                                "county_name": row["county_name"],
                                "observation_date": row["observation_date"].strftime("%Y-%m-%d"),
                                "horizon": h,
                                "target_phase3plus": int(y_te.iloc[i]),
                                "predicted_prob": round(float(y_prob[i]), 4),
                                "predicted_class": int(y_pred[i]),
                                "rainfall_anomaly_lag1": row.get("rainfall_anomaly_lag1", 0.0),
                                "ndvi_anomaly_lag1": row.get("ndvi_anomaly_lag1", 0.0),
                                "maize_price_zscore": row.get("maize_price_zscore", 0.0),
                                "previous_ipc_phase": row.get("previous_ipc_phase", 2.0),
                                "neighbour_mean_rainfall_anomaly": row.get("neighbour_mean_rainfall_anomaly", 0.0),
                                "number_of_high_risk_neighbours": row.get("number_of_high_risk_neighbours", 0)
                            })

                    # Write single JSON
                    with open(EXPERIMENTS_DIR / f"{exp_id}.json", "w", encoding="utf-8") as f:
                        json.dump(entry, f, indent=2)

        # 2. Feature Ablation Experiments (Horizon 1, Fold 2)
        h1_df = self.forecast_df[self.forecast_df["horizon_months"] == 1].dropna(subset=["target_phase3plus"]).copy()
        h1_df["observation_date"] = pd.to_datetime(h1_df["observation_date"])
        tr_df = h1_df[h1_df["observation_date"] <= pd.to_datetime("2023-12-31")].copy()
        te_df = h1_df[h1_df["observation_date"] >= pd.to_datetime("2024-01-01")].copy()

        ablation_configs = {
            "all_features": all_features,
            "minus_climate": [f for f in all_features if f not in FEATURE_GROUPS["CLIMATE"]],
            "minus_vegetation": [f for f in all_features if f not in FEATURE_GROUPS["VEGETATION"]],
            "minus_market": [f for f in all_features if f not in FEATURE_GROUPS["MARKET"]],
            "minus_historical_risk": [f for f in all_features if f not in FEATURE_GROUPS["HISTORICAL_RISK"]],
            "minus_spatial": [f for f in all_features if f not in FEATURE_GROUPS["SPATIAL"]],
            "minus_seasonality": [f for f in all_features if f not in FEATURE_GROUPS["SEASONALITY"]],
        }

        ablation_records = []
        for ab_name, ab_feats in ablation_configs.items():
            rf = RandomForestClassifier(n_estimators=100, max_depth=5, class_weight="balanced", random_state=self.random_state)
            ab_imputer = SimpleImputer(strategy="median")
            X_ab_tr = pd.DataFrame(ab_imputer.fit_transform(tr_df[ab_feats]), columns=ab_feats, index=tr_df.index)
            X_ab_te = pd.DataFrame(ab_imputer.transform(te_df[ab_feats]), columns=ab_feats, index=te_df.index)

            rf.fit(X_ab_tr, tr_df["target_phase3plus"].astype(int))
            probs = rf.predict_proba(X_ab_te)[:, 1]
            preds = (probs >= 0.5).astype(int)
            y_true = te_df["target_phase3plus"].astype(int).values

            rec = float(recall_score(y_true, preds, zero_division=0))
            f1 = float(f1_score(y_true, preds, zero_division=0))
            brier = float(brier_score_loss(y_true, probs))
            roc = float(roc_auc_score(y_true, probs))
            pr = float(average_precision_score(y_true, probs))

            ab_entry = {
                "ablation_set": ab_name,
                "feature_count": len(ab_feats),
                "recall": round(rec, 4),
                "f1_score": round(f1, 4),
                "roc_auc": round(roc, 4),
                "pr_auc": round(pr, 4),
                "brier_score": round(brier, 4)
            }
            ablation_records.append(ab_entry)

            # Record in master registry
            exp_id = f"ablation_h1_{ab_name}"
            reg_entry = dict(ab_entry)
            reg_entry.update({
                "experiment_id": exp_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "forecast_horizon": 1,
                "fold_name": "fold2_recovery_transition",
                "model_name": "random_forest_ablation",
                "feature_set": ab_name,
                "num_features": len(ab_feats),
                "train_samples": len(tr_df),
                "test_samples": len(te_df),
                "precision": round(float(precision_score(y_true, preds, zero_division=0)), 4),
                "false_negative_rate": round(1.0 - rec, 4)
            })
            registry_entries.append(reg_entry)

        # Save registry
        reg_df = pd.DataFrame(registry_entries)
        reg_df.to_csv(self.registry_csv, index=False)
        logger.info("Saved %d experiment records to: %s", len(reg_df), self.registry_csv)

        # Save ablation analysis
        pd.DataFrame(ablation_records).to_csv(ANALYSIS_DIR / "feature_ablation_summary.csv", index=False)

        # 3. County Performance & Error Analysis
        pred_df = pd.DataFrame(all_test_predictions)
        self._analyze_errors_and_county_performance(pred_df)

        # 4. Feature Stability
        self._compute_feature_stability(tr_df, te_df, all_features)

        logger.info("==================================================================")
        logger.info("MILESTONE 6 EXPERIMENT SUITE COMPLETED SUCCESSFULLY")
        logger.info("==================================================================")
        return {"registry_count": len(reg_df), "ablation_count": len(ablation_records)}

    def _analyze_errors_and_county_performance(self, pred_df: pd.DataFrame) -> None:
        """Generate structured county-level performance tables and detailed false negative/positive logs."""
        if pred_df.empty:
            return

        # County-level metrics across all horizons in test set
        county_records = []
        for county, group in pred_df.groupby("county_name"):
            y_t = group["target_phase3plus"].values
            y_p = group["predicted_prob"].values
            y_pred = group["predicted_class"].values

            rec = float(recall_score(y_t, y_pred, zero_division=0))
            prec = float(precision_score(y_t, y_pred, zero_division=0))
            f1 = float(f1_score(y_t, y_pred, zero_division=0))
            brier = float(brier_score_loss(y_t, y_p))
            fnr = 1.0 - rec

            county_records.append({
                "county_name": county,
                "test_observations": len(group),
                "positive_events": int(y_t.sum()),
                "recall": round(rec, 4),
                "precision": round(prec, 4),
                "f1_score": round(f1, 4),
                "brier_score": round(brier, 4),
                "false_negative_rate": round(fnr, 4),
                "mean_predicted_probability": round(float(y_p.mean()), 4)
            })

        county_df = pd.DataFrame(county_records)
        county_df.to_csv(ANALYSIS_DIR / "county_performance.csv", index=False)
        logger.info("Saved county performance report to: %s", ANALYSIS_DIR / "county_performance.csv")

        # False Negatives (Missed Crises)
        fn_df = pred_df[(pred_df["target_phase3plus"] == 1) & (pred_df["predicted_class"] == 0)].copy()
        fn_df.to_csv(ANALYSIS_DIR / "false_negatives.csv", index=False)
        logger.info("Saved %d false-negative failure cases to: %s", len(fn_df), ANALYSIS_DIR / "false_negatives.csv")

        # False Positives (False Alarms)
        fp_df = pred_df[(pred_df["target_phase3plus"] == 0) & (pred_df["predicted_class"] == 1)].copy()
        fp_df.to_csv(ANALYSIS_DIR / "false_positives.csv", index=False)
        logger.info("Saved %d false-positive records to: %s", len(fp_df), ANALYSIS_DIR / "false_positives.csv")

    def _compute_feature_stability(self, tr_df: pd.DataFrame, te_df: pd.DataFrame, features: List[str]) -> None:
        """Evaluate feature importance ranks across horizons h=1, h=2, h=3."""
        importance_by_horizon = {}
        for h in [1, 2, 3]:
            h_data = self.forecast_df[self.forecast_df["horizon_months"] == h].dropna(subset=["target_phase3plus"]).copy()
            h_data["observation_date"] = pd.to_datetime(h_data["observation_date"])

            h_tr = h_data[h_data["observation_date"] <= pd.to_datetime("2023-12-31")]
            h_te = h_data[h_data["observation_date"] >= pd.to_datetime("2024-01-01")]

            if h_tr.empty or h_te.empty:
                continue

            stab_imputer = SimpleImputer(strategy="median")
            X_stab_tr = pd.DataFrame(stab_imputer.fit_transform(h_tr[features]), columns=features, index=h_tr.index)
            X_stab_te = pd.DataFrame(stab_imputer.transform(h_te[features]), columns=features, index=h_te.index)

            rf = RandomForestClassifier(n_estimators=100, max_depth=5, class_weight="balanced", random_state=self.random_state)
            rf.fit(X_stab_tr, h_tr["target_phase3plus"].astype(int))

            explainer = ModelExplainer(features)
            imp_df = explainer.compute_global_importance(
                rf, X_stab_te, h_te["target_phase3plus"].astype(int)
            )
            importance_by_horizon[h] = imp_df

        if importance_by_horizon:
            stability_df = ModelExplainer.analyze_feature_stability(importance_by_horizon)
            stability_df.to_csv(ANALYSIS_DIR / "feature_stability.csv", index=False)
            logger.info("Saved feature importance stability to: %s", ANALYSIS_DIR / "feature_stability.csv")
