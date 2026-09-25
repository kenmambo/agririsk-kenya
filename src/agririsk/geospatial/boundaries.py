"""Geospatial utilities, county boundary representations, and spatial join validation."""

from pathlib import Path
from typing import Optional, List, Tuple
import json
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, shape
from agririsk.core.constants import KENYA_COUNTIES
from agririsk.core.logging import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
GEOJSON_PATH = PROJECT_ROOT / "data" / "geospatial" / "kenya_counties.geojson"


def load_county_boundaries(target_crs: str = "EPSG:4326") -> gpd.GeoDataFrame:
    """Load official polygon boundary geometries for Kenya's 47 counties.

    If GeoJSON is available at data/geospatial/kenya_counties.geojson, loads polygon shapes;
    otherwise gracefully falls back to Point geometries from constants.

    Args:
        target_crs: Target coordinate reference system (defaults to EPSG:4326).

    Returns:
        GeoDataFrame with columns: county_code, county_name, asal_category, geometry.
    """
    if GEOJSON_PATH.exists():
        try:
            gdf = gpd.read_file(GEOJSON_PATH)
            if gdf.crs is None:
                gdf = gdf.set_crs("EPSG:4326")
            elif gdf.crs.to_string() != target_crs:
                gdf = gdf.to_crs(target_crs)
            return gdf
        except Exception as e:
            logger.warning("Failed to parse %s (%s). Falling back to point geometries.", GEOJSON_PATH, e)

    return get_counties_geodataframe(target_crs=target_crs)


def get_counties_geodataframe(target_crs: str = "EPSG:4326") -> gpd.GeoDataFrame:
    """Return a GeoDataFrame containing all 47 counties of Kenya with centroid points.

    Args:
        target_crs: Target coordinate reference system (defaults to EPSG:4326).

    Returns:
        GeoDataFrame with columns: county_code, county_name, asal_category, geometry (Point).
    """
    records = []
    for c in KENYA_COUNTIES:
        records.append({
            "county_code": c["code"],
            "county_name": c["name"],
            "asal_category": c["asal_category"],
            "latitude": c["lat"],
            "longitude": c["lon"],
            "geometry": Point(c["lon"], c["lat"])
        })

    gdf = gpd.GeoDataFrame(records, crs="EPSG:4326")
    if target_crs != "EPSG:4326":
        gdf = gdf.to_crs(target_crs)

    return gdf


def validate_county_spatial_join(
    model_counties: List[str],
    geo_counties: List[str]
) -> Tuple[bool, List[str]]:
    """Validate that all model counties are present in the geographic boundary layer.

    Args:
        model_counties: List of county names present in the modeling dataset.
        geo_counties: List of county names present in the geospatial layer.

    Returns:
        Tuple of (is_valid: bool, unmatched_counties: List[str]).
    """
    geo_set = {c.strip().lower() for c in geo_counties}
    unmatched = [c for c in model_counties if c.strip().lower() not in geo_set]

    is_valid = len(unmatched) == 0
    if not is_valid:
        logger.warning("Geospatial Join Warning: %d model counties failed to match geographic layer: %s", len(unmatched), unmatched)

    return is_valid, unmatched


def get_county_by_code(code: str) -> Optional[dict]:
    """Look up a single county's geospatial metadata by code."""
    code_normalized = code.zfill(3)
    for c in KENYA_COUNTIES:
        if c["code"] == code_normalized:
            return c
    return None
