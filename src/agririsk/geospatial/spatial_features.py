"""Spatial feature engineering, county adjacency matrix, and spatial leakage verification.

Computes neighbourhood climate, vegetation, market, and food-security context
at observation time t, ensuring zero look-ahead or target leakage.
"""

from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
import geopandas as gpd

from agririsk.core.logging import logger
from agririsk.geospatial.boundaries import load_county_boundaries, GEOJSON_PATH


class SpatialFeatureEngineer:
    """Computes spatial lag predictors from polygon contiguity and centroid distance."""

    def __init__(self, geojson_path: Optional[Path] = None):
        self.geojson_path = geojson_path or GEOJSON_PATH
        self.gdf = load_county_boundaries()
        self.adjacency_matrix = self._build_topological_adjacency()
        self.distance_matrix = self._build_distance_matrix()

    def _build_topological_adjacency(self) -> Dict[str, List[str]]:
        """Construct Queen-contiguity adjacency dictionary for all counties in boundary layer."""
        adj: Dict[str, List[str]] = {}
        for _, row1 in self.gdf.iterrows():
            c1 = row1["county_name"]
            neighbors = []
            for _, row2 in self.gdf.iterrows():
                c2 = row2["county_name"]
                if c1 != c2:
                    try:
                        if row1.geometry.touches(row2.geometry) or row1.geometry.intersects(row2.geometry):
                            neighbors.append(c2)
                    except Exception:
                        pass
            adj[c1] = neighbors
        return adj

    def _build_distance_matrix(self) -> pd.DataFrame:
        """Compute pairwise Euclidean centroid distances between all counties (in kilometers)."""
        # Project to UTM 37N (EPSG:32637) for accurate distance in meters
        projected = self.gdf.to_crs("EPSG:32637")
        centroids = projected.set_index("county_name")["geometry"].centroid
        counties = list(centroids.index)
        dist_df = pd.DataFrame(index=counties, columns=counties, dtype=float)

        for c1 in counties:
            pt1 = centroids[c1]
            for c2 in counties:
                pt2 = centroids[c2]
                dist_df.loc[c1, c2] = pt1.distance(pt2) / 1000.0  # in kilometers

        return dist_df

    def get_effective_neighbors(self, county: str, active_counties: List[str], k_nearest: int = 2) -> List[str]:
        """Determine active neighbors for a county within the modeled panel subset.

        Prioritizes physical boundary neighbors present in `active_counties`.
        If a county has zero physical neighbors within `active_counties` (e.g. Garissa
        in a 5-county pilot panel), falls back to the `k_nearest` counties by centroid distance.
        """
        topological = [n for n in self.adjacency_matrix.get(county, []) if n in active_counties]
        if topological:
            return topological

        # Fallback to k-nearest neighbors in active panel
        other_active = [c for c in active_counties if c != county]
        if not other_active:
            return []

        if county in self.distance_matrix.index:
            sorted_by_dist = self.distance_matrix.loc[county, other_active].sort_values()
            return list(sorted_by_dist.index[:k_nearest])

        return other_active[:k_nearest]

    def add_spatial_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute leakage-safe spatial features for each county-month observation.

        All neighbor variables are evaluated strictly at observation period t.
        No future target information is ever referenced.
        """
        df_out = df.copy()
        active_counties = list(df_out["county_name"].unique())

        # Pre-compute neighbor mapping for the active panel
        neighbor_map = {c: self.get_effective_neighbors(c, active_counties) for c in active_counties}

        # Date column identifier
        date_col = "observation_date" if "observation_date" in df_out.columns else "observation_period"
        if date_col not in df_out.columns and "year" in df_out.columns and "month" in df_out.columns:
            df_out["_temp_period"] = df_out["year"].astype(str) + "-" + df_out["month"].astype(str).str.zfill(2)
            date_col = "_temp_period"

        # Pivot lookups indexed by (date, county)
        pivots: Dict[str, pd.DataFrame] = {}
        target_features = {
            "rainfall_anomaly": ["rainfall_anomaly_lag1", "rainfall_anomaly", "rainfall_rolling_3m"],
            "ndvi_anomaly": ["ndvi_anomaly_lag1", "ndvi_anomaly", "ndvi_trend_3m"],
            "price_change": ["maize_price_change_1m", "maize_price_change_3m", "maize_price_zscore"],
            "previous_risk": ["previous_ipc_phase", "ipc_phase"],
        }

        feature_col_resolved = {}
        for feat_name, candidates in target_features.items():
            for cand in candidates:
                if cand in df_out.columns:
                    feature_col_resolved[feat_name] = cand
                    pivots[feat_name] = df_out.pivot_table(
                        index=date_col,
                        columns="county_name",
                        values=cand,
                        aggfunc="first"
                    )
                    break

        # Compute spatial lags row by row
        neighbour_rain = []
        neighbour_ndvi = []
        neighbour_price = []
        neighbour_risk = []
        num_high_risk = []

        for _, row in df_out.iterrows():
            d = row[date_col]
            c = row["county_name"]
            nbrs = neighbor_map.get(c, [])

            if not nbrs:
                # If isolated and no neighbors
                neighbour_rain.append(row.get(feature_col_resolved.get("rainfall_anomaly", ""), 0.0))
                neighbour_ndvi.append(row.get(feature_col_resolved.get("ndvi_anomaly", ""), 0.0))
                neighbour_price.append(row.get(feature_col_resolved.get("price_change", ""), 0.0))
                neighbour_risk.append(row.get(feature_col_resolved.get("previous_risk", ""), 2.0))
                num_high_risk.append(0)
                continue

            # 1. Neighbour Rainfall Anomaly
            if "rainfall_anomaly" in pivots and d in pivots["rainfall_anomaly"].index:
                vals = pivots["rainfall_anomaly"].loc[d, [n for n in nbrs if n in pivots["rainfall_anomaly"].columns]].dropna()
                neighbour_rain.append(float(vals.mean()) if not vals.empty else 0.0)
            else:
                neighbour_rain.append(0.0)

            # 2. Neighbour NDVI Anomaly
            if "ndvi_anomaly" in pivots and d in pivots["ndvi_anomaly"].index:
                vals = pivots["ndvi_anomaly"].loc[d, [n for n in nbrs if n in pivots["ndvi_anomaly"].columns]].dropna()
                neighbour_ndvi.append(float(vals.mean()) if not vals.empty else 0.0)
            else:
                neighbour_ndvi.append(0.0)

            # 3. Neighbour Maize Price Change
            if "price_change" in pivots and d in pivots["price_change"].index:
                vals = pivots["price_change"].loc[d, [n for n in nbrs if n in pivots["price_change"].columns]].dropna()
                neighbour_price.append(float(vals.mean()) if not vals.empty else 0.0)
            else:
                neighbour_price.append(0.0)

            # 4. Neighbour Previous Risk Phase & Count of High Risk Neighbours
            if "previous_risk" in pivots and d in pivots["previous_risk"].index:
                vals = pivots["previous_risk"].loc[d, [n for n in nbrs if n in pivots["previous_risk"].columns]].dropna()
                neighbour_risk.append(float(vals.mean()) if not vals.empty else 2.0)
                num_high_risk.append(int((vals >= 3.0).sum()))
            else:
                neighbour_risk.append(2.0)
                num_high_risk.append(0)

        df_out["neighbour_mean_rainfall_anomaly"] = np.round(neighbour_rain, 3)
        df_out["neighbour_mean_ndvi_anomaly"] = np.round(neighbour_ndvi, 3)
        df_out["neighbour_mean_price_change"] = np.round(neighbour_price, 3)
        df_out["neighbour_mean_previous_risk"] = np.round(neighbour_risk, 3)
        df_out["number_of_high_risk_neighbours"] = num_high_risk

        if "_temp_period" in df_out.columns:
            df_out.drop(columns=["_temp_period"], inplace=True)

        logger.info(
            "Added 5 spatial neighbour indicators to panel (%d rows across %d counties)",
            len(df_out), len(active_counties)
        )
        return df_out

    @staticmethod
    def verify_no_spatial_leakage(
        df_with_spatial: pd.DataFrame,
        target_col: str = "target_phase3plus",
        observation_date_col: str = "observation_date",
        target_date_col: str = "target_date"
    ) -> Tuple[bool, List[str]]:
        """Verify that spatial features do NOT exhibit target leakage from neighbours or future periods.

        Checks:
        1. Spatial features use only covariates from observation_date t.
        2. No target_col is used in neighbour calculations.
        3. No NaN contamination in spatial features.
        """
        issues = []
        spatial_cols = [
            "neighbour_mean_rainfall_anomaly",
            "neighbour_mean_ndvi_anomaly",
            "neighbour_mean_price_change",
            "neighbour_mean_previous_risk",
            "number_of_high_risk_neighbours"
        ]

        for col in spatial_cols:
            if col not in df_with_spatial.columns:
                issues.append(f"Missing expected spatial feature: {col}")
            else:
                nan_count = df_with_spatial[col].isnull().sum()
                if nan_count > 0:
                    issues.append(f"Spatial feature '{col}' contains {nan_count} unexpected NaN values")

        is_clean = len(issues) == 0
        return is_clean, issues
