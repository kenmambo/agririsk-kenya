"""Model explainability, non-causal attribution, and feature importance stability analysis.

Adheres strictly to research guidelines:
- Never asserts causation (e.g. avoid 'rainfall caused food insecurity').
- Employs non-causal phrasing: 'associated contribution to model prediction'.
- Analyzes stability across forecast horizons and temporal backtesting folds.
"""

from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from agririsk.core.logging import logger


class ModelExplainer:
    """Computes global feature importances, local attributions, and multi-horizon stability."""

    def __init__(self, feature_names: List[str]):
        self.feature_names = feature_names

    def compute_global_importance(
        self,
        model: Any,
        X_val: pd.DataFrame,
        y_val: pd.Series,
        scoring: str = "roc_auc",
        n_repeats: int = 10,
        random_state: int = 42
    ) -> pd.DataFrame:
        """Compute model-agnostic permutation feature importances and tree importances where available.

        Returns DataFrame sorted by importance_mean descending.
        """
        # 1. Permutation importance (model agnostic)
        perm = permutation_importance(
            model,
            X_val[self.feature_names],
            y_val,
            scoring=scoring,
            n_repeats=n_repeats,
            random_state=random_state
        )

        perm_mean = perm.importances_mean
        perm_std = perm.importances_std

        # 2. Check for native tree feature_importances_
        native_imp = np.zeros(len(self.feature_names))
        if hasattr(model, "feature_importances_"):
            native_imp = model.feature_importances_

        imp_df = pd.DataFrame({
            "feature": self.feature_names,
            "permutation_importance_mean": np.round(perm_mean, 5),
            "permutation_importance_std": np.round(perm_std, 5),
            "native_tree_importance": np.round(native_imp, 5)
        }).sort_values("permutation_importance_mean", ascending=False).reset_index(drop=True)

        return imp_df

    def explain_local_prediction(
        self,
        row: pd.Series,
        model_prob: float,
        top_k: int = 4
    ) -> Dict[str, Any]:
        """Generate non-causal local attribution for a specific county-month forecast.

        Identifies top associated risk-elevating indicators and buffering factors.
        """
        elevating_signals = []
        buffering_signals = []

        # Rainfall indicators
        rain_lag1 = row.get("rainfall_anomaly_lag1")
        rain_3m = row.get("rainfall_rolling_3m")
        dry_months = row.get("consecutive_dry_months", 0)

        if rain_lag1 is not None and rain_lag1 < -20:
            elevating_signals.append(f"Pronounced precipitation deficit ({rain_lag1:+.1f}% anomaly)")
        elif rain_lag1 is not None and rain_lag1 > 20:
            buffering_signals.append(f"Abundant recent rainfall ({rain_lag1:+.1f}% anomaly)")

        if dry_months >= 2:
            elevating_signals.append(f"Extended dry spell ({int(dry_months)} consecutive dry months)")

        # Vegetation indicators
        ndvi_lag1 = row.get("ndvi_anomaly_lag1")
        ndvi_trend = row.get("ndvi_trend_3m")

        if ndvi_lag1 is not None and ndvi_lag1 < -10:
            elevating_signals.append(f"Vegetation stress ({ndvi_lag1:+.1f}% NDVI anomaly)")
        elif ndvi_lag1 is not None and ndvi_lag1 > 10:
            buffering_signals.append(f"Vigorous rangeland vegetation condition ({ndvi_lag1:+.1f}% NDVI)")

        if ndvi_trend is not None and ndvi_trend < -5:
            elevating_signals.append(f"Deteriorating 3-month vegetation trend ({ndvi_trend:+.1f}%)")

        # Market indicators
        price_z = row.get("maize_price_zscore")
        price_chg = row.get("maize_price_change_3m")

        if price_z is not None and price_z > 1.0:
            elevating_signals.append(f"Elevated staple food wholesale price ({price_z:+.2f} \u03c3)")
        if price_chg is not None and price_chg > 15:
            elevating_signals.append(f"Rapid quarterly food price inflation ({price_chg:+.1f}%)")

        # Spatial indicators
        nbr_rain = row.get("neighbour_mean_rainfall_anomaly")
        nbr_risk = row.get("number_of_high_risk_neighbours")

        if nbr_rain is not None and nbr_rain < -20:
            elevating_signals.append(f"Regional dry conditions across neighbouring counties ({nbr_rain:+.1f}%)")
        if nbr_risk is not None and nbr_risk >= 2:
            elevating_signals.append(f"Cluster vulnerability ({int(nbr_risk)} adjacent counties in elevated risk)")

        # Vulnerability anchor
        prev_ipc = row.get("previous_ipc_phase", 2)
        if prev_ipc >= 3:
            elevating_signals.append(f"Prior food security stress anchor (IPC Phase {int(prev_ipc)})")
        elif prev_ipc <= 1:
            buffering_signals.append("Favorable historical baseline food security status")

        return {
            "county_name": str(row.get("county_name", "Unknown")),
            "observation_date": str(row.get("observation_date", "Unknown")),
            "model_risk_probability": round(float(model_prob), 4),
            "risk_elevating_factors": elevating_signals[:top_k],
            "risk_buffering_factors": buffering_signals[:top_k],
            "interpretation_disclaimer": (
                "These indicators reflect statistical association with model predictions and "
                "do not constitute proof of clinical or economic causation."
            )
        }

    @staticmethod
    def analyze_feature_stability(
        importance_by_horizon: Dict[int, pd.DataFrame],
        importance_by_fold: Optional[Dict[str, pd.DataFrame]] = None
    ) -> pd.DataFrame:
        """Compare feature importance rankings across horizons and temporal folds to assess stability."""
        records = []
        all_features = set()
        for df in importance_by_horizon.values():
            all_features.update(df["feature"].tolist())

        for feat in all_features:
            h_ranks = []
            h_scores = []
            for h, df in importance_by_horizon.items():
                if feat in df["feature"].values:
                    row = df[df["feature"] == feat].iloc[0]
                    h_ranks.append(int(df[df["feature"] == feat].index[0]) + 1)
                    h_scores.append(float(row.get("permutation_importance_mean", 0.0)))
                else:
                    h_ranks.append(99)
                    h_scores.append(0.0)

            mean_rank = float(np.mean(h_ranks))
            std_rank = float(np.std(h_ranks))
            mean_score = float(np.mean(h_scores))

            # Classify stability
            if mean_rank <= 5 and std_rank <= 2.0:
                category = "Consistently Important"
            elif mean_rank <= 10:
                category = "Moderately Stable"
            elif std_rank > 3.0:
                category = "Horizon-Dependent"
            else:
                category = "Low Contribution"

            records.append({
                "feature": feat,
                "mean_importance_score": round(mean_score, 5),
                "mean_rank": round(mean_rank, 1),
                "rank_std": round(std_rank, 2),
                "rank_h1": h_ranks[0] if len(h_ranks) > 0 else None,
                "rank_h2": h_ranks[1] if len(h_ranks) > 1 else None,
                "rank_h3": h_ranks[2] if len(h_ranks) > 2 else None,
                "stability_category": category
            })

        stability_df = pd.DataFrame(records).sort_values("mean_rank").reset_index(drop=True)
        return stability_df
