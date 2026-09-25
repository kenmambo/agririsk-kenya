"""Unit and integration tests for Milestone 6: Research Benchmarks, Spatial Effects, and Uncertainty."""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from agririsk.modeling.benchmarks import PersistenceBaseline, HistoricalFrequencyBaseline, SeasonalBaseline
from agririsk.geospatial.spatial_features import SpatialFeatureEngineer
from agririsk.experiments.uncertainty import BlockBootstrapEvaluator, EnsembleUncertaintyEstimator
from agririsk.experiments.explainability import ModelExplainer
from agririsk.experiments.runner import ExperimentRunner, FEATURE_GROUPS


def test_persistence_baseline():
    """Verify that PersistenceBaseline accurately propagates previous risk states."""
    X = pd.DataFrame({
        "previous_ipc_phase": [1.0, 2.0, 3.0, 4.0, 2.5]
    })
    model = PersistenceBaseline(current_risk_col="previous_ipc_phase", threshold_phase=3.0)
    model.fit(X)

    preds = model.predict(X)
    probs = model.predict_proba(X)

    # Phases 3.0 and 4.0 should predict crisis (1), others non-crisis (0)
    assert list(preds) == [0, 0, 1, 1, 0]
    assert probs[0, 1] == 0.0
    assert probs[2, 1] == 1.0


def test_historical_frequency_baseline():
    """Verify that HistoricalFrequencyBaseline assigns county empirical priors."""
    X_train = pd.DataFrame({
        "county_name": ["Turkana", "Turkana", "Marsabit", "Marsabit", "Baringo", "Baringo"]
    })
    y_train = pd.Series([1, 1, 1, 0, 0, 0])

    model = HistoricalFrequencyBaseline()
    model.fit(X_train, y_train)

    assert model.county_priors["Turkana"] == 1.0
    assert model.county_priors["Marsabit"] == 0.5
    assert model.county_priors["Baringo"] == 0.0

    X_test = pd.DataFrame({"county_name": ["Turkana", "Baringo", "UnknownCounty"]})
    probs = model.predict_proba(X_test)[:, 1]

    assert probs[0] > 0.9
    assert probs[1] < 0.1
    # Unknown county falls back to global prior (0.5)
    assert round(probs[2], 2) == 0.5


def test_seasonal_baseline():
    """Verify that SeasonalBaseline computes seasonal priors conditioned on month and county."""
    X_train = pd.DataFrame({
        "county_name": ["Turkana", "Turkana", "Turkana", "Marsabit"],
        "month": [3, 3, 10, 3]
    })
    y_train = pd.Series([1, 1, 0, 0])

    model = SeasonalBaseline()
    model.fit(X_train, y_train)

    # Turkana in month 3 has 100% historical risk
    X_test = pd.DataFrame({
        "county_name": ["Turkana", "Turkana", "Marsabit"],
        "month": [3, 10, 3]
    })
    probs = model.predict_proba(X_test)[:, 1]
    assert probs[0] > 0.9
    assert probs[1] < 0.1
    assert probs[2] < 0.1


def test_spatial_adjacency_matrix():
    """Verify that SpatialFeatureEngineer constructs valid 47-county Queen contiguity."""
    spatial_eng = SpatialFeatureEngineer()
    adj = spatial_eng.adjacency_matrix

    assert len(adj) == 47
    assert "Turkana" in adj
    assert "Marsabit" in adj["Turkana"]
    assert "Mandera" in adj["Marsabit"]

    # Effective neighbors within pilot subset
    pilot = ["Turkana", "Marsabit", "Mandera", "Garissa", "Baringo"]
    turkana_nbrs = spatial_eng.get_effective_neighbors("Turkana", pilot)
    assert "Marsabit" in turkana_nbrs

    # Garissa has no boundary pilot neighbor, so centroid k-NN fallback activates
    garissa_nbrs = spatial_eng.get_effective_neighbors("Garissa", pilot)
    assert len(garissa_nbrs) > 0
    assert "Garissa" not in garissa_nbrs


def test_spatial_feature_engineering_no_leakage():
    """Verify that spatial features are generated cleanly without target leakage."""
    sample_data = pd.DataFrame({
        "county_name": ["Turkana", "Marsabit", "Turkana", "Marsabit"],
        "observation_date": ["2024-01-01", "2024-01-01", "2024-02-01", "2024-02-01"],
        "rainfall_anomaly_lag1": [-15.0, -25.0, 10.0, 5.0],
        "ndvi_anomaly_lag1": [-5.0, -12.0, 2.0, -1.0],
        "maize_price_change_1m": [12.0, 8.0, 2.0, 1.0],
        "previous_ipc_phase": [3.0, 3.0, 2.0, 3.0],
        "target_phase3plus": [1, 1, 0, 1]
    })

    spatial_eng = SpatialFeatureEngineer()
    enriched = spatial_eng.add_spatial_features(sample_data)

    assert "neighbour_mean_rainfall_anomaly" in enriched.columns
    assert "number_of_high_risk_neighbours" in enriched.columns
    assert len(enriched) == 4

    is_clean, issues = SpatialFeatureEngineer.verify_no_spatial_leakage(enriched)
    assert is_clean is True
    assert len(issues) == 0


def test_block_bootstrap_evaluator():
    """Verify that BlockBootstrapEvaluator calculates bounded 95% empirical confidence intervals."""
    # Synthetic time-series predictions
    df_eval = pd.DataFrame({
        "observation_date": ["2024-01-01"] * 5 + ["2024-02-01"] * 5 + ["2024-03-01"] * 5,
        "y_true": [1, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0, 0],
        "y_prob": [0.8, 0.2, 0.7, 0.1, 0.3, 0.9, 0.85, 0.15, 0.2, 0.1, 0.75, 0.3, 0.65, 0.2, 0.15]
    })

    evaluator = BlockBootstrapEvaluator(n_bootstraps=50, random_state=42)
    res = evaluator.evaluate_with_ci(
        df=df_eval,
        y_true_col="y_true",
        y_prob_col="y_prob",
        block_col="observation_date"
    )

    assert "recall" in res
    assert "f1" in res
    assert "brier_score" in res

    rec = res["recall"]
    assert rec["ci_lower"] <= rec["estimate"] <= rec["ci_upper"]
    assert 0.0 <= rec["estimate"] <= 1.0


def test_ensemble_uncertainty_estimator():
    """Verify that EnsembleUncertaintyEstimator outputs valid prediction uncertainty bounds."""
    m1 = PersistenceBaseline()
    m2 = PersistenceBaseline()
    models = {"p1": m1, "p2": m2}

    estimator = EnsembleUncertaintyEstimator(models)
    X = pd.DataFrame({"previous_ipc_phase": [2.0, 3.5, 1.0]})

    unc_df = estimator.predict_with_uncertainty(X)

    assert "risk_probability" in unc_df.columns
    assert "lower_uncertainty_bound" in unc_df.columns
    assert "upper_uncertainty_bound" in unc_df.columns
    assert "uncertainty_spread" in unc_df.columns

    for _, row in unc_df.iterrows():
        assert row["lower_uncertainty_bound"] <= row["risk_probability"] <= row["upper_uncertainty_bound"]
        assert row["uncertainty_spread"] >= 0.0


def test_feature_stability_analysis():
    """Verify ModelExplainer feature stability categorization."""
    h1_imp = pd.DataFrame({
        "feature": ["previous_ipc_phase", "rainfall_anomaly_lag1"],
        "permutation_importance_mean": [0.25, 0.05]
    })
    h2_imp = pd.DataFrame({
        "feature": ["previous_ipc_phase", "rainfall_anomaly_lag1"],
        "permutation_importance_mean": [0.20, 0.04]
    })
    h3_imp = pd.DataFrame({
        "feature": ["previous_ipc_phase", "rainfall_anomaly_lag1"],
        "permutation_importance_mean": [0.18, 0.03]
    })

    stability_df = ModelExplainer.analyze_feature_stability({1: h1_imp, 2: h2_imp, 3: h3_imp})

    assert len(stability_df) == 2
    top = stability_df.iloc[0]
    assert top["feature"] == "previous_ipc_phase"
    assert top["mean_rank"] == 1.0
    assert top["stability_category"] == "Consistently Important"
